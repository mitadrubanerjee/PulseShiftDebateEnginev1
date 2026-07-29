# api/config.py
"""
Standalone config for the FastAPI layer.

Deliberately decoupled from core/config.py, which does `import streamlit as
st` at module level to read st.secrets (see lines ~124-139 of that file).
Importing that module from a non-Streamlit process either errors (if
streamlit isn't installed) or risks touching st.secrets outside of a
running Streamlit app. debate_engine/config.py already made this same call
for the same reason \u2014 this file follows that precedent rather than
patching core/config.py, so the existing Streamlit app is untouched.

SECTOR_QUERIES below is copied from core/config.py (the second, final
definition that overrides the first \u2014 11 sectors). If you add/edit sectors
in core/config.py, mirror the change here.
"""

from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# ---- Sector config (copied from core/config.py) ----------------------------
SECTOR_QUERIES = {
    "Communication Services": '("communication services" OR telecom OR media OR streaming) (earnings OR guidance OR outlook OR subscribers)',
    "Consumer Discretionary": '("consumer discretionary" OR retail OR autos OR apparel) (sales OR earnings OR outlook OR demand)',
    "Consumer Staples":       '("consumer staples" OR beverages OR household OR packaged foods) (sales OR earnings OR inflation OR pricing)',
    "Energy":                 '(energy OR oil OR gas OR LNG OR refinery) (OPEC OR output OR prices OR inventories OR earnings)',
    "Financials":             '(banks OR insurers OR "asset managers" OR brokers) (NIM OR credit OR provisions OR earnings OR guidance)',
    "Healthcare":             '(healthcare OR pharma OR biotech OR medtech) (trial OR FDA OR EMA OR earnings OR guidance)',
    "Industrials":            '(industrials OR machinery OR transport OR aerospace) (orders OR backlog OR capex OR earnings)',
    "Materials":              '(materials OR chemicals OR metals OR mining) (prices OR demand OR China OR earnings)',
    "Real Estate":            '("real estate" OR REIT OR housing) (rents OR occupancy OR mortgage OR "cap rate" OR earnings)',
    "Technology":             '("information technology" OR semiconductors OR software OR hardware) (earnings OR AI OR guidance)',
    "Utilities":              '(utilities OR electricity OR grid OR power) (tariffs OR capacity OR outage OR earnings)',
}
SECTORS = list(SECTOR_QUERIES.keys())

HOMEPAGE_FRESHNESS_DAYS = 3
DASHBOARD_CACHE_TTL_SECONDS = 900  # 15 min, matches Home.py's @st.cache_data(ttl=900)

# Fixed watchlist for the pitch demo (v2: user-configurable via Supabase)
WATCHLIST = [
    ("NVDA", "NVIDIA Corporation"),
    ("AAPL", "Apple Inc."),
    ("JPM", "JPMorgan Chase & Co."),
    ("XOM", "Exxon Mobil Corp."),
    ("MSFT", "Microsoft Corp."),
    ("AMZN", "Amazon.com Inc."),
]


def resolve_ticker_from_company(company_name: str):
    """
    Company name -> (ticker, official_name) via Polygon v3 reference search.
    Returns (None, None) if not found or on any error \u2014 contract matches
    services/ticker_resolver.py's resolve_ticker_from_company(), which this
    is adapted from. Only the ticker-lookup half is needed here (not that
    file's sector-normalization helpers): debate_engine.evidence already
    does its own independent sector lookup via Polygon SIC codes once given
    a ticker, so we don't need a second sector source.

    Decoupled from services/ticker_resolver.py because that module imports
    core.config, which does `import streamlit as st` at module level \u2014
    the same issue api/config.py's SECTOR_QUERIES copy above was written to
    avoid. See that comment for the full explanation.
    """
    import requests
    try:
        url = "https://api.polygon.io/v3/reference/tickers"
        params = {"search": company_name, "active": "true", "apiKey": POLYGON_API_KEY}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            first = data["results"][0]
            return first.get("ticker") or None, first.get("name") or None
        return None, None
    except Exception:
        return None, None
