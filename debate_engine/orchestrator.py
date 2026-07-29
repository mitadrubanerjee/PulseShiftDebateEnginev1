# debate_engine/orchestrator.py
"""
Runs a complete Bull/Bear/Moderator debate for one ticker.

This is the top-level entry point for the whole debate engine: everything
in evidence.py and agents.py exists to support run_debate().
"""

from __future__ import annotations
from typing import Dict, Iterator, List

from debate_engine.evidence import get_evidence_packet
from debate_engine.agents import generate_turn, generate_verdict, format_evidence_for_prompt

MAX_EXCHANGES = 10


def run_debate_stream(ticker: str, company_name: str, max_exchanges: int = MAX_EXCHANGES) -> Iterator[Dict]:
    """
    Generator version of run_debate() \u2014 yields one event dict at a time as
    the debate is generated, instead of returning everything at once. This
    is the single real implementation of the debate loop; run_debate() below
    just drains this generator and returns the final state, so there's only
    one place the alternation/conviction-tracking logic lives.

    Yields, in order:
      {"type": "evidence", "evidence": {...}}
      {"type": "turn", "turn": {...}, "conviction": {...}}        \u00d7 max_exchanges
      {"type": "verdict", "verdict": {...}}
      {"type": "done", "result": {...}}   # same shape run_debate() returns

    Intended consumer: api/debates.py wraps each yielded event as one SSE
    message, so the frontend's progressive-reveal animation has real data to
    drive it turn by turn rather than a fixed client-side timer.
    """
    evidence = get_evidence_packet(ticker, company_name)
    brief = format_evidence_for_prompt(evidence)
    yield {"type": "evidence", "evidence": evidence}

    transcript: List[Dict] = []
    conviction: List[Dict] = [{"turn": 0, "bull": 50, "bear": 50}]
    bull_conv, bear_conv = 50, 50

    for i in range(max_exchanges):
        speaker = "bull" if i % 2 == 0 else "bear"
        round_label = i // 2 + 1

        turn = generate_turn(
            evidence, transcript, speaker, round_label,
            evidence_brief=brief, max_exchanges=max_exchanges,
        )

        if speaker == "bull":
            bull_conv = turn["conviction"]
        else:
            bear_conv = turn["conviction"]

        transcript.append(turn)
        conv_point = {"turn": i + 1, "bull": bull_conv, "bear": bear_conv}
        conviction.append(conv_point)

        yield {"type": "turn", "turn": turn, "conviction": conv_point}

    verdict = generate_verdict(evidence, transcript, conviction, evidence_brief=brief)
    yield {"type": "verdict", "verdict": verdict}

    result = {
        "evidence": evidence,
        "turns": transcript,
        "conviction": conviction,
        "verdict": verdict,
    }
    yield {"type": "done", "result": result}


def run_debate(ticker: str, company_name: str, max_exchanges: int = MAX_EXCHANGES) -> Dict:
    """
    Run a full debate for `ticker` / `company_name` and return the complete
    result at once (drains run_debate_stream() internally). See that
    function's docstring for the event sequence; this just keeps the last
    "done" event's result.

    Returns:
    {
      "evidence": <full evidence packet from evidence.get_evidence_packet>,
      "turns": [
          {speaker, roundLabel, text, citationType, citationLabel,
           citationValue, conviction}, ...
      ],  # length == max_exchanges
      "conviction": [
          {"turn": 0, "bull": 50, "bear": 50}, ...
      ],  # length == max_exchanges + 1 (turn 0 = baseline before any exchanges)
      "verdict": {action, confidence, sizing, reasoning},
    }
    """
    result = None
    for event in run_debate_stream(ticker, company_name, max_exchanges=max_exchanges):
        if event["type"] == "done":
            result = event["result"]
    return result
