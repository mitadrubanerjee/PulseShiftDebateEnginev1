# debate_engine/smoke_test_packet.py
"""
Live smoke test for the full combined evidence packet — get_evidence_packet().

This is the exact shape agents.py (next step) will consume. Needs network
(news + Polygon), so run this with your real .env in place.

Run from the project root:
    python -m debate_engine.smoke_test_packet [TICKER] [COMPANY NAME]

Examples:
    python -m debate_engine.smoke_test_packet
    python -m debate_engine.smoke_test_packet TSLA "Tesla, Inc."
"""

from __future__ import annotations
import json
import sys

from debate_engine.evidence import get_evidence_packet


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    company_name = sys.argv[2] if len(sys.argv) > 2 else "NVIDIA Corporation"

    print(f"Fetching evidence packet for {ticker} ({company_name})...")
    print("(this makes several live network calls — may take a few seconds)\n")

    packet = get_evidence_packet(ticker, company_name)
    print(json.dumps(packet, indent=2))


if __name__ == "__main__":
    main()
