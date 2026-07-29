# debate_engine/debug_sector_lookup.py
"""
Diagnostic: print the raw fields Polygon's /v3/reference/tickers/{ticker}
endpoint returns for sector/industry classification, so we can see exactly
what get_ticker_sector() has to work with.

Run from the project root:
    python -m debate_engine.debug_sector_lookup
"""

from __future__ import annotations
import json
import requests

from debate_engine.config import POLYGON_API_KEY, SECTOR_NORMALIZATION

TICKERS = ["NVDA", "XOM", "AAPL", "JPM"]

FIELDS_OF_INTEREST = [
    "sector",
    "industry",
    "sic_code",
    "sic_description",
    "type",
    "market",
]


def main() -> None:
    if not POLYGON_API_KEY:
        print("POLYGON_API_KEY is not set — check your .env file.")
        return

    for ticker in TICKERS:
        print(f"=== {ticker} ===")
        url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
        r = requests.get(url, params={"apiKey": POLYGON_API_KEY}, timeout=15)

        if r.status_code != 200:
            print(f"  HTTP {r.status_code}: {r.text[:300]}")
            print()
            continue

        result = r.json().get("results", {}) or {}

        for field in FIELDS_OF_INTEREST:
            val = result.get(field)
            print(f"  {field:16s}: {val!r}")

        # Show what our current normalization would do with sic_description
        sic_desc = result.get("sic_description")
        if sic_desc:
            normalized = SECTOR_NORMALIZATION.get(sic_desc) or SECTOR_NORMALIZATION.get(sic_desc.lower())
            print(f"  -> normalized   : {normalized}")

        print()


if __name__ == "__main__":
    main()
