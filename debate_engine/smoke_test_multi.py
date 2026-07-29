# debate_engine/smoke_test_multi.py
"""
Runs run_debate() across multiple tickers and prints a compact comparison
table \u2014 useful for checking whether verdicts/conviction track the
underlying evidence sensibly across different tickers, or whether there's a
systematic bias (e.g. always SELL) independent of the evidence.

This makes ~12 network calls PER TICKER (evidence packet + 10 debate turns
+ 1 moderator call). For 5 tickers, expect several minutes total and a real
OpenAI usage cost. Each full debate is also saved to
debate_engine/last_debate_<TICKER>.json for deeper inspection if any one
result looks worth digging into.

Run from the project root:
    python -m debate_engine.smoke_test_multi
"""

from __future__ import annotations
import json

from debate_engine.orchestrator import run_debate

TICKERS = [
    ("AAPL", "Apple Inc."),
    ("JPM", "JPMorgan Chase & Co."),
    ("XOM", "Exxon Mobil Corp."),
    ("TSLA", "Tesla, Inc."),
    ("PFE", "Pfizer Inc."),
]


def main() -> None:
    results = []
    for ticker, company in TICKERS:
        print(f"Running {ticker} ({company})...")
        result = run_debate(ticker, company)
        results.append((ticker, result))

        out_path = f"debate_engine/last_debate_{ticker}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  done \u2014 saved to {out_path}\n")

    print("\n" + "=" * 92)
    print(f"{'TICKER':6s} {'SENTIMENT':24s} {'RSI':>6s} {'WK CHG':>7s} {'BULL':>5s} {'BEAR':>5s} {'VERDICT':>8s} {'CONF':>5s}")
    print("=" * 92)
    for ticker, result in results:
        ev = result["evidence"]
        sent = ev["sentiment"]
        tech = ev["technical"]
        conv = result["conviction"][-1]
        verdict = result["verdict"]

        sentiment_str = f"{sent['avg_score']:+.2f} {sent['label']}"
        rsi_str = f"{tech['rsi']}" if tech.get("rsi") is not None else "n/a"
        pct_str = f"{tech['pct_change']:+.1f}%" if tech.get("pct_change") is not None else "n/a"

        print(
            f"{ticker:6s} {sentiment_str:24s} {rsi_str:>6s} {pct_str:>7s} "
            f"{conv['bull']:5d} {conv['bear']:5d} {verdict['action']:>8s} {verdict['confidence']:5d}"
        )
    print("=" * 92)
    print("\nSizing per ticker:")
    for ticker, result in results:
        print(f"  {ticker:6s}: {result['verdict']['sizing']}")


if __name__ == "__main__":
    main()
