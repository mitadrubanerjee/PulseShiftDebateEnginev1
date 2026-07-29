# debate_engine/smoke_test_agents_live.py
"""
Live smoke test for agents.generate_turn() — needs OPENAI_API_KEY in .env.

Generates the opening Bull turn, then the Bear's response to it (using the
sample evidence packet from smoke_test_agents_offline.py, so this doesn't
also depend on live news/Polygon calls). Prints both turns in full so you
can judge: do these citations look genuinely grounded? Does the Bear
actually engage with the Bull's point?

Run from the project root:
    python -m debate_engine.smoke_test_agents_live
"""

from __future__ import annotations
import json

from debate_engine.agents import generate_turn, format_evidence_for_prompt
from debate_engine.smoke_test_agents_offline import SAMPLE_EVIDENCE_FULL


def print_turn(turn: dict) -> None:
    print(f"[{turn['speaker'].upper()} \u2014 round {turn['roundLabel']}]")
    print(f"  text: {turn['text']}")
    print(f"  citation_type : {turn['citationType']}")
    print(f"  citation_label: {turn['citationLabel']}")
    print(f"  citation_value: {turn['citationValue']}")
    print()


def main() -> None:
    evidence = SAMPLE_EVIDENCE_FULL
    brief = format_evidence_for_prompt(evidence)

    print("Generating Bull, exchange 1 (round 1)...")
    bull_1 = generate_turn(evidence, transcript=[], speaker="bull", round_label=1, evidence_brief=brief)
    print_turn(bull_1)

    print("Generating Bear, exchange 2 (round 1, responding to Bull)...")
    bear_1 = generate_turn(evidence, transcript=[bull_1], speaker="bear", round_label=1, evidence_brief=brief)
    print_turn(bear_1)


if __name__ == "__main__":
    main()
