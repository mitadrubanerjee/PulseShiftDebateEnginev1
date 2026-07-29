# debate_engine/smoke_test_orchestrator_offline.py
"""
Offline test for orchestrator.run_debate()'s bookkeeping \u2014 alternation,
round labels, and conviction-trajectory tracking \u2014 using mocked
generate_turn/generate_verdict/get_evidence_packet. No network or API key
needed. This is purely about verifying the LOOP logic is correct; it says
nothing about debate/prompt quality (that's smoke_test_orchestrator.py).

Run from the project root:
    python -m debate_engine.smoke_test_orchestrator_offline
"""

from __future__ import annotations
from unittest.mock import patch

from debate_engine.smoke_test_agents_offline import SAMPLE_EVIDENCE_FULL


def fake_generate_turn(evidence, transcript, speaker, round_label, evidence_brief=None, max_exchanges=10):
    n = len(transcript) + 1
    # Deterministic fake conviction so we can check carry-forward behaviour.
    conviction = (50 + n * 2) if speaker == "bull" else (50 - n)
    conviction = max(0, min(100, conviction))
    return {
        "speaker": speaker,
        "roundLabel": round_label,
        "text": f"(fake {speaker} text, exchange {n}, round {round_label})",
        "citationType": "sentiment",
        "citationLabel": "fake label",
        "citationValue": "fake value",
        "conviction": conviction,
    }


def fake_generate_verdict(evidence, transcript, conviction, evidence_brief=None):
    return {
        "action": "BUY",
        "confidence": 70,
        "sizing": "1.0% of book (fake)",
        "reasoning": ["fake reasoning"],
    }


def main() -> None:
    with patch("debate_engine.orchestrator.get_evidence_packet", return_value=SAMPLE_EVIDENCE_FULL), \
         patch("debate_engine.orchestrator.generate_turn", side_effect=fake_generate_turn), \
         patch("debate_engine.orchestrator.generate_verdict", side_effect=fake_generate_verdict):

        from debate_engine.orchestrator import run_debate
        result = run_debate("NVDA", "NVIDIA Corporation")

    turns = result["turns"]
    conviction = result["conviction"]

    print(f"n turns      : {len(turns)} (expected 10)")
    print(f"n conviction : {len(conviction)} (expected 11)")
    print()

    print("speaker / round / conviction sequence:")
    for t in turns:
        print(f"  {t['speaker']:5s} round {t['roundLabel']}  conviction={t['conviction']}")
    print()

    print("conviction trajectory (checking carry-forward):")
    for c in conviction:
        print(f"  turn {c['turn']:2d}: bull={c['bull']:3d}  bear={c['bear']:3d}")
    print()

    # Sanity checks
    expected_speakers = ["bull", "bear"] * 5
    expected_rounds = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    actual_speakers = [t["speaker"] for t in turns]
    actual_rounds = [t["roundLabel"] for t in turns]

    assert actual_speakers == expected_speakers, f"speaker order wrong: {actual_speakers}"
    assert actual_rounds == expected_rounds, f"round labels wrong: {actual_rounds}"
    assert len(conviction) == len(turns) + 1
    # bull's value should only change on bull turns, bear's only on bear turns
    for i in range(1, len(conviction)):
        prev, cur = conviction[i - 1], conviction[i]
        if turns[i - 1]["speaker"] == "bull":
            assert cur["bear"] == prev["bear"], f"bear changed on a bull turn at index {i}"
        else:
            assert cur["bull"] == prev["bull"], f"bull changed on a bear turn at index {i}"

    print("verdict:", result["verdict"])
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
