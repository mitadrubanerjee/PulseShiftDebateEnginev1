# debate_engine/smoke_test_live.py
"""
Live smoke test for evidence.py Part 2 — ticker -> sector resolution and
the RSI/ATR technical signal, both via Polygon.

This DOES hit the network (Polygon's API), so it needs:
  - POLYGON_API_KEY set in your .env file (or environment), and
  - your machine to have internet access.

Run from the project root:
    python -m debate_engine.smoke_test_live
"""

from __future__ import annotations

from debate_engine.config import POLYGON_API_KEY
from debate_engine.evidence import get_ticker_sector, get_technical_signal

TICKERS = ["NVDA", "XOM"]


def main() -> None:
    if not POLYGON_API_KEY:
        print(
            "POLYGON_API_KEY is not set. Create a .env file in the project "
            "root with a line like:\n  POLYGON_API_KEY=your_key_here\n"
            "(see debate_engine/config.py for details)."
        )
        return

    for ticker in TICKERS:
        print(f"=== {ticker} ===")

        sector = get_ticker_sector(ticker)
        print(f"sector       : {sector}")

        tech = get_technical_signal(ticker)
        print(f"rsi          : {tech['rsi']}")
        print(f"atr          : {tech['atr']}")
        print(f"atr_pct      : {tech['atr_pct']}")
        print(f"pct_change   : {tech['pct_change']}")
        print(f"as_of        : {tech['as_of']}")
        print()


if __name__ == "__main__":
    main()
