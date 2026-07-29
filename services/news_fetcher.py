# services/news_fetcher.py
"""
Google News RSS fetcher that returns a stable NewsArticle schema.

This is the single entry point for fetching company/sector/general news.
Always returns List[NewsArticle] with a consistent shape.
"""

from __future__ import annotations
from typing import List, TypedDict, Optional
from urllib.parse import quote_plus, urlparse
import xml.etree.ElementTree as ET
import html
import requests
from datetime import datetime

# ---- Stable schema used across the app ---------------------------------------
class NewsArticle(TypedDict):
    title: str
    description: str
    url: str
    published_at: Optional[str]   # ISO8601 or ""
    provider: Optional[str]       # e.g., "Reuters", "Bloomberg", or domain


# ---- Constants ---------------------------------------------------------------
_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
_DEFAULT_UA = "Mozilla/5.0 (compatible; MarketSentimentBot/1.0; +https://example.com/bot)"


# ---- Helpers -----------------------------------------------------------------
def _guess_provider_from_title_or_domain(title: str, link: str) -> str:
    """
    Google News often formats titles as: 'Headline - Publisher'.
    If not present, fall back to mapping the domain to a brand or just return the domain.
    """
    parts = (title or "").rsplit(" - ", 1)
    if len(parts) == 2 and 2 <= len(parts[1]) <= 50:
        return parts[1].strip()

    netloc = urlparse(link or "").netloc.lower()
    domain_map = {
        "www.bloomberg.com": "Bloomberg", "bloomberg.com": "Bloomberg",
        "www.reuters.com": "Reuters", "reuters.com": "Reuters",
        "www.cnbc.com": "CNBC", "cnbc.com": "CNBC",
        "www.ft.com": "Financial Times", "ft.com": "Financial Times",
        "www.theguardian.com": "Guardian", "theguardian.com": "Guardian",
        "finance.yahoo.com": "Yahoo Finance", "news.yahoo.com": "Yahoo",
        "www.barrons.com": "Barrons",
        "www.bbc.com": "BBC", "www.bbc.co.uk": "BBC",
        "www.marketwatch.com": "Market Watch",
        "www.economist.com": "Economist",
        "asia.nikkei.com": "Nikkei",
        "www.ecb.europa.eu": "ECB", "www.federalreserve.gov": "Fed",
        "www.fxstreet.com": "FXStreet", "www.forexlive.com": "Forex Live",
        "www.zerohedge.com": "Zero Hedge",
    }
    return domain_map.get(netloc, netloc or "Unknown")


def _parse_pubdate_to_iso(pub: str) -> str:
    """
    Normalize RSS pubDate / dc:date into ISO8601 where possible.
    Returns "" if missing or unparseable.
    """
    if not pub:
        return ""
    fmts = [
        "%a, %d %b %Y %H:%M:%S %Z",  # Mon, 17 Feb 2025 12:34:56 GMT
        "%a, %d %b %Y %H:%M:%S %z",  # with numeric tz
        "%Y-%m-%dT%H:%M:%S%z",       # dc:date ISO format
        "%Y-%m-%dT%H:%M:%S",         # dc:date without tz
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(pub, fmt).isoformat()
        except Exception:
            pass
    return ""


# ---- Public API --------------------------------------------------------------
def fetch_news(
    query: str,
    days: int = 3,
    max_results: int = 80,
    timeout: int = 15,
    user_agent: str = _DEFAULT_UA,
) -> List[NewsArticle]:
    """
    Fetch news articles from Google News RSS for a free, keyless search.

    Args:
        query: Search query. You can pass sector strings or company names.
               Example: '("technology" OR "semiconductors") (stocks OR earnings)'

        days: Freshness filter via Google 'when:Xd' operator (1,3,7,30...).

        max_results: Cap the number of articles returned (typ. RSS yields 20-100).

        timeout: Requests timeout in seconds.

        user_agent: Optional UA string to avoid being blocked.

    Returns:
        List[NewsArticle] with fields:
            - title
            - description
            - url
            - published_at (ISO8601 or "")
            - provider (best-effort guess)
    """
    q = f"{query} when:{days}d"
    url = _GOOGLE_NEWS_RSS.format(q=quote_plus(q))

    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = root.findall(".//item")

    articles: List[NewsArticle] = []
    seen = set()

    for it in items:
        title = html.unescape((it.findtext("title") or "").strip())
        desc = html.unescape((it.findtext("description") or "").strip())
        link = (it.findtext("link") or "").strip()

        # dc:date sometimes present and more ISO-like than pubDate
        dc_date = it.findtext("{http://purl.org/dc/elements/1.1/}date") or ""
        pubdate = dc_date or (it.findtext("pubDate") or "")
        iso_pub = _parse_pubdate_to_iso(pubdate.strip())

        if not link or link in seen:
            continue
        seen.add(link)

        provider = _guess_provider_from_title_or_domain(title, link)

        articles.append(
            NewsArticle(
                title=title,
                description=desc,
                url=link,
                published_at=iso_pub or "",
                provider=provider or "Unknown",
            )
        )

        if len(articles) >= max_results:
            break

    return articles


# Convenience wrappers
def fetch_company_news(company: str, days: int = 7, max_results: int = 120) -> List[NewsArticle]:
    """Company-focused convenience search."""
    return fetch_news(company, days=days, max_results=max_results)


def fetch_sector_news(sector_query: str, days: int = 3, max_results: int = 80) -> List[NewsArticle]:
    """Sector-focused convenience search (expects a prepared sector query string)."""
    return fetch_news(sector_query, days=days, max_results=max_results)
