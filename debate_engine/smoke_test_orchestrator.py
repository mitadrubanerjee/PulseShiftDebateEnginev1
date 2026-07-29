# debate_engine/smoke_test_orchestrator.py
"""
Full end-to-end LIVE test: runs a complete 10-exchange debate for one ticker
and prints the transcript, conviction trajectory, and verdict.

This makes ~12 network calls (news + Polygon for the evidence packet, then
10 Bull/Bear calls + 1 Moderator call) \u2014 expect 30-90+ seconds.
Saves the full result as JSON for inspection (and as a future fallback
transcript for demo day).

Run from the project root:
    python -m debate_engine.smoke_test_orchestrator [TICKER] [COMPANY NAME]

Examples:
    python -m debate_engine.smoke_test_orchestrator
    python -m debate_engine.smoke_test_orchestrator XOM "Exxon Mobil Corp."
"""

from __future__ import annotations
import json
import sys

from debate_engine.orchestrator import run_debate


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    company = sys.argv[2] if len(sys.argv) > 2 else "NVIDIA Corporation"

    print(f"Running full debate for {ticker} ({company})...")
    print("(evidence packet + 10 debate turns + 1 moderator call \u2014 this will take a while)\n")

    result = run_debate(ticker, company)

    for turn in result["turns"]:
        print(f"[{turn['speaker'].upper()} \u2014 exchange round {turn['roundLabel']}, conviction {turn['conviction']}]")
        print(f"  {turn['text']}")
        print(f"  cited ({turn['citationType']}): {turn['citationLabel']} \u2014 {turn['citationValue']}")
        print()

    print("Conviction trajectory:")
    for c in result["conviction"]:
        print(f"  turn {c['turn']:2d}: bull={c['bull']:3d}  bear={c['bear']:3d}")
    print()

    print("Verdict:")
    print(json.dumps(result["verdict"], indent=2))

    out_path = f"debate_engine/last_debate_{ticker}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull result saved to {out_path}")


if __name__ == "__main__":
    main()
