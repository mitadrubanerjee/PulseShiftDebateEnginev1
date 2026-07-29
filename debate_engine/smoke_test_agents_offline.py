# debate_engine/smoke_test_agents_offline.py
"""
Offline smoke test for agents.format_evidence_for_prompt().

Uses a hand-built sample evidence packet (same shape as
evidence.get_evidence_packet(), with realistic NVDA-style numbers) so you
can see exactly what the Bull/Bear agents will be given to read — without
needing live network access or an OpenAI key.

Run from the project root:
    python -m debate_engine.smoke_test_agents_offline
"""

from __future__ import annotations
from debate_engine.agents import format_evidence_for_prompt

SAMPLE_EVIDENCE_FULL = {
    "ticker": "NVDA",
    "company_name": "NVIDIA Corporation",
    "sector": "Technology",
    "sentiment": {
        "avg_score": 0.142,
        "std_score": 0.21,
        "label": "Trending Positive",
        "n_articles": 38,
        "top_headlines": [
            {"title": "Nvidia raises full-year revenue guidance, shares jump in after-hours trading", "provider": "Reuters", "url": "https://example.com/1", "score": 0.612},
            {"title": "Analyst raises Nvidia price target to $200 ahead of earnings", "provider": "Bloomberg", "url": "https://example.com/2", "score": 0.487},
            {"title": "Cloud provider expands custom AI chip programme, eyes inference workloads", "provider": "Financial Times", "url": "https://example.com/3", "score": -0.103},
            {"title": "Nvidia partners with major automakers on next-gen AI platforms", "provider": "CNBC", "url": "https://example.com/4", "score": 0.298},
            {"title": "Chip stocks slip broadly as traders book profits after recent rally", "provider": "MarketWatch", "url": "https://example.com/5", "score": -0.215},
        ],
    },
    "sector_sentiment": {"avg_score": 0.18, "std_score": 0.15, "label": "Trending Positive", "n_articles": 14},
    "technical": {"rsi": 64.0, "atr": 3.72, "atr_pct": 2.9, "pct_change": 1.24, "as_of": "2026-06-08"},
}

# Edge case: Polygon failed (technical all None) and sector couldn't be resolved.
SAMPLE_EVIDENCE_DEGRADED = {
    "ticker": "XYZ",
    "company_name": "Example Corp",
    "sector": None,
    "sentiment": {
        "avg_score": 0.0,
        "std_score": 0.0,
        "label": "Neutral",
        "n_articles": 0,
        "top_headlines": [],
    },
    "sector_sentiment": None,
    "technical": {"rsi": None, "atr": None, "atr_pct": None, "pct_change": None, "as_of": None},
}


def main() -> None:
    print("=" * 70)
    print("FULL PACKET (NVDA-style)")
    print("=" * 70)
    print(format_evidence_for_prompt(SAMPLE_EVIDENCE_FULL))

    print()
    print("=" * 70)
    print("DEGRADED PACKET (no news, no sector, Polygon failed)")
    print("=" * 70)
    print(format_evidence_for_prompt(SAMPLE_EVIDENCE_DEGRADED))


if __name__ == "__main__":
    main()
