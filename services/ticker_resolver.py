# services/ticker_resolver.py
"""
Ticker + sector resolver via Polygon.io.

Public, stable functions:
- resolve_ticker_from_company(company_name) -> (ticker: Optional[str], official_name: Optional[str])
- get_company_sector(ticker) -> Optional[str]   # normalized to your app's sector keys
- normalize_sector(raw_sector) -> Optional[str]

Consistency rules:
- Always return Optional[str] for ticker, official_name, sector.
- Sector is normalized to one of your config.SECTOR_QUERIES keys (or None if unknown).
"""

from __future__ import annotations
from typing import Optional, Tuple
import requests

from core.config import POLYGON_API_KEY, SECTOR_QUERIES  # your canonical sector keys
# 👉 IMPORTANT: In core/config.py, define SECTOR_NORMALIZATION like:
# SECTOR_NORMALIZATION = {
#     "Information Technology": "Technology",
#     "Technology": "Technology",
#     "Financials": "Financials",
#     "Energy": "Energy",
#     "Health Care": "Healthcare",
#     "Healthcare": "Healthcare",
#     "Consumer Discretionary": "Consumer",
#     "Consumer Staples": "Consumer",
#     "Consumer": "Consumer",
#     "Industrials": "Industrials",
#     # Add more mappings as needed
# }
from core.config import SECTOR_NORMALIZATION


# -------- Public API -----------------------------------------------------------

def resolve_ticker_from_company(company_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (ticker, official_name) using Polygon v3 reference search.

    - ticker: e.g., "TSLA"
    - official_name: e.g., "Tesla, Inc."
    - Returns (None, None) if not found or on recoverable errors.

    This function's return shape is stable across the app.
    """
    try:
        url = "https://api.polygon.io/v3/reference/tickers"
        params = {"search": company_name, "active": "true", "apiKey": POLYGON_API_KEY}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if data.get("results"):
            first = data["results"][0]
            ticker = first.get("ticker") or None
            name = first.get("name") or None
            return ticker, name
        return None, None
    except Exception:
        # Do NOT raise: keep the contract stable
        return None, None


def get_company_sector(ticker: str) -> Optional[str]:
    """
    Resolve a company's sector via Polygon, then normalize it
    to one of your app's sector keys (SECTOR_QUERIES keys).

    Returns:
      - normalized sector string (e.g., "Technology", "Financials", ...)
      - None if not found or not mappable

    Contract is stable: Optional[str].
    """
    if not ticker:
        return None

    raw = _fetch_polygon_sector_raw(ticker)
    if not raw:
        return None

    normalized = normalize_sector(raw)
    # Ensure normalized sector actually exists in your configured sectors
    if normalized in SECTOR_QUERIES:
        return normalized
    return None


def normalize_sector(raw_sector: Optional[str]) -> Optional[str]:
    """
    Map provider-specific sector strings into your canonical sector names.

    Uses SECTOR_NORMALIZATION from config. Returns None if no mapping exists.
    """
    if not raw_sector:
        return None
    s = raw_sector.strip()
    # Exact mapping
    if s in SECTOR_NORMALIZATION:
        return SECTOR_NORMALIZATION[s]

    # Fallback: try case-insensitive direct hit on keys
    lower_map = {k.lower(): v for k, v in SECTOR_NORMALIZATION.items()}
    if s.lower() in lower_map:
        return lower_map[s.lower()]

    # Nothing matched
    return None


# -------- Internal helpers -----------------------------------------------------

def _fetch_polygon_sector_raw(ticker: str) -> Optional[str]:
    """
    Hit Polygon ticker details endpoint and try multiple fields that may contain
    sector-ish info. Returns the raw string (un-normalized) or None.
    """
    try:
        url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
        params = {"apiKey": POLYGON_API_KEY}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        result = data.get("results", {}) or {}

        # Different plans/responses may expose different fields; try them in order.
        candidates = [
            result.get("sector"),            # preferred if present
            result.get("industry"),          # sometimes more granular
            result.get("sic_description"),   # broader text; may need normalization
        ]

        for c in candidates:
            if c and isinstance(c, str) and c.strip():
                return c.strip()

        return None
    except Exception:
        return None
