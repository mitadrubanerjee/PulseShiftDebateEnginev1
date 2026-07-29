# api/dashboard.py
"""
Dashboard data for the FastAPI layer: sector mood/heatmap (reused, real logic
from services/aggregators.py + services/news_fetcher.py, the same functions
Home.py's _load_snapshot() calls) and a per-ticker watchlist (new \u2014 no
per-ticker dashboard logic existed in core/services, so this calls
debate_engine.evidence.get_evidence_packet() per ticker and returns just the
summary fields, skipping the citation-heavy fields meant for debates).
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional, Tuple

from services.news_fetcher import fetch_news
from services.aggregators import build_dashboard_payload
from debate_engine.evidence import get_evidence_packet

from api.config import SECTORS, SECTOR_QUERIES, HOMEPAGE_FRESHNESS_DAYS, DASHBOARD_CACHE_TTL_SECONDS, WATCHLIST

# ---- simple in-memory TTL cache --------------------------------------------
# Mirrors Home.py's @st.cache_data(ttl=900) \u2014 avoids hammering Google News RSS
# on every dashboard load. Single-process only; fine for a pitch demo, not
# meant to survive into a multi-worker production deployment.
_cache: Dict[str, Tuple[float, object]] = {}


def _cached(key: str, ttl: int, compute_fn):
    now = time.time()
    hit = _cache.get(key)
    if hit is not None and (now - hit[0]) < ttl:
        return hit[1]
    value = compute_fn()
    _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    """Equivalent of Home.py's st.cache_data.clear() (wired to a 'refresh' button there)."""
    _cache.clear()


# ---- sector snapshot (reused logic) ----------------------------------------
def _load_sector_snapshot(freshness_days: int = HOMEPAGE_FRESHNESS_DAYS) -> Dict:
    """
    Same computation as Home.py's _load_snapshot(): fetch market-wide +
    per-sector news, compute mood index and sector sentiment table.

    Returns: {"mood": {avg_score, std_score, label, n_articles},
              "by_sector": [{"sector", "avg_score", "std_score", "label", "n_items"}, ...]}
    (by_sector is a list of dicts here, not a DataFrame \u2014 JSON-serializable for the API.)
    """
    market_query = '(markets OR "stock market" OR equities OR earnings OR macro) (stocks OR outlook)'
    market_articles = fetch_news(query=market_query, days=freshness_days, max_results=160)

    sector_articles = {}
    for sector in SECTORS:
        q = SECTOR_QUERIES.get(sector, sector)
        sector_articles[sector] = fetch_news(query=q, days=freshness_days, max_results=80)

    payload = build_dashboard_payload(
        market_articles=market_articles,
        sector_articles=sector_articles,
        engine="vader",  # matches Home.py's hard-locked engine
    )
    return {
        "mood": payload["mood"],
        "by_sector": payload["by_sector"].to_dict(orient="records"),
    }


def get_sector_snapshot(freshness_days: int = HOMEPAGE_FRESHNESS_DAYS) -> Dict:
    key = f"sector_snapshot:{freshness_days}"
    return _cached(key, DASHBOARD_CACHE_TTL_SECONDS, lambda: _load_sector_snapshot(freshness_days))


# ---- per-ticker watchlist (new) ---------------------------------------------
def _load_watchlist_row(ticker: str, company_name: str) -> Dict:
    """
    One row of summary data for a watchlist card, via the same evidence
    pipeline the debate engine uses (so the numbers on the Dashboard match
    what the Debate Arena cites for the same ticker).
    """
    packet = get_evidence_packet(ticker, company_name)
    sent = packet.get("sentiment") or {}
    tech = packet.get("technical") or {}
    return {
        "ticker": ticker,
        "company_name": company_name,
        "sector": packet.get("sector"),
        "sentiment_score": sent.get("avg_score"),
        "sentiment_label": sent.get("label"),
        "rsi": tech.get("rsi"),
        "pct_change": tech.get("pct_change"),
        "close": tech.get("close"),  # latest WEEKLY close from Polygon, not real-time/intraday
        "as_of": tech.get("as_of"),
    }


def get_watchlist(watchlist: Optional[List[Tuple[str, str]]] = None) -> List[Dict]:
    items = watchlist or WATCHLIST
    key = "watchlist:" + ",".join(t for t, _ in items)

    def _fetch_all():
        # Fetch all tickers in parallel using a thread pool \u2014 the sequential
        # list comprehension this replaces caused the last ticker to consistently
        # get empty technical data because cumulative Polygon request time was
        # hitting rate/connection limits by the time it reached the final call.
        # With parallel fetches, all tickers complete in roughly the same
        # wall-clock window (~3-5s instead of ~15-20s sequential).
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(items)) as ex:
            futures = {ex.submit(_load_watchlist_row, t, c): (t, c) for t, c in items}
            results = {}
            for fut in concurrent.futures.as_completed(futures):
                t, c = futures[fut]
                try:
                    results[(t, c)] = fut.result()
                except Exception:
                    # If one ticker completely fails, return a minimal row
                    # rather than breaking the whole watchlist response.
                    results[(t, c)] = {
                        "ticker": t, "company_name": c, "sector": None,
                        "sentiment_score": None, "sentiment_label": None,
                        "rsi": None, "pct_change": None, "close": None, "as_of": None,
                    }
        # Preserve the original watchlist ordering (as_completed gives arbitrary order)
        return [results[(t, c)] for t, c in items]

    return _cached(key, DASHBOARD_CACHE_TTL_SECONDS, _fetch_all)
