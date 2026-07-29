# debate_engine/agents.py
"""
Bull/Bear/Moderator agents for the debate engine.

Built incrementally:
  - Part 1 (this step): format_evidence_for_prompt(evidence) — converts the
    evidence packet from evidence.get_evidence_packet() into a numbered list
    of "evidence items" ([E1], [E2], ...) that the Bull/Bear prompts will be
    told to ground their citations in. Pure string formatting, no API calls
    — testable offline against a sample packet.

  - Part 2 (next): BULL_SYSTEM_PROMPT / BEAR_SYSTEM_PROMPT and
    generate_turn() — the OpenAI call that turns an evidence brief +
    transcript-so-far into one debate turn (text + citation), returned as
    structured JSON matching the shape the frontend mockup already expects.

Citation types used throughout the app (mockup CITATION_ICONS):
  sentiment, technical, sector, headline  -> grounded directly in an [E#]
                                              evidence item (this file)
  synthesis, risk, concession             -> interpretive moves an agent
                                              makes based on the debate so
                                              far, not a single evidence item
                                              (handled in Part 2's prompts)
  model                                   -> PARKED (see evidence.py)
"""

from __future__ import annotations
from typing import Dict, List, Optional


def _fmt_score(v: Optional[float]) -> str:
    """Format a [-1, +1] sentiment-style score with an explicit sign."""
    if v is None:
        return "n/a"
    return f"{'+' if v >= 0 else ''}{v:.2f}"


def _fmt_pct(v: Optional[float], decimals: int = 1) -> str:
    """Format a percentage with an explicit sign."""
    if v is None:
        return "n/a"
    return f"{'+' if v >= 0 else ''}{v:.{decimals}f}%"


def format_evidence_for_prompt(evidence: Dict, max_headlines: int = 5) -> str:
    """
    Convert an evidence packet into a numbered list of citable "evidence
    items" for the Bull/Bear prompts.

    Each item is rendered as:
        [E#] type=<citation_type> | <label>: <value>

    `type` and `label` map directly onto the citationType/citationLabel
    fields the frontend already expects (see CITATION_ICONS in the mockup).
    Items are only included if the underlying data is actually present —
    e.g. if Polygon failed and `technical` is all None, the technical item
    is simply omitted rather than shown as "n/a", so the agents never cite
    evidence that doesn't exist.
    """
    ticker = evidence.get("ticker", "?")
    company = evidence.get("company_name", ticker)
    sector = evidence.get("sector")
    sentiment = evidence.get("sentiment") or {}
    sector_sentiment = evidence.get("sector_sentiment")
    technical = evidence.get("technical") or {}

    items: List[tuple] = []  # (citation_type, label, value)

    # -- aggregate company sentiment + dispersion --
    if sentiment.get("n_articles", 0) > 0:
        items.append((
            "sentiment",
            "News sentiment (VADER)",
            f"{_fmt_score(sentiment.get('avg_score'))} \u00b7 {sentiment.get('label')} "
            f"({sentiment.get('n_articles')} articles, 3d window)",
        ))
        items.append((
            "sentiment",
            "Sentiment dispersion",
            f"std {sentiment.get('std_score', 0):.2f} across {sentiment.get('n_articles')} articles",
        ))
    else:
        items.append((
            "sentiment",
            "News sentiment",
            "No recent company-specific headlines found (Neutral default)",
        ))

    # -- technical signal (only if Polygon data came back) --
    rsi = technical.get("rsi")
    atr_pct = technical.get("atr_pct")
    pct_change = technical.get("pct_change")
    if rsi is not None or atr_pct is not None:
        parts = []
        if rsi is not None:
            parts.append(f"RSI {rsi}")
        if atr_pct is not None:
            parts.append(f"ATR-implied weekly volatility {atr_pct:.1f}%")
        if pct_change is not None:
            parts.append(f"latest weekly change {_fmt_pct(pct_change)}")
        items.append((
            "technical",
            "Technical signal (Polygon, weekly)",
            " \u00b7 ".join(parts),
        ))

    # -- sector sentiment (only if sector was resolved AND had articles) --
    if sector_sentiment and sector_sentiment.get("n_articles", 0) > 0:
        items.append((
            "sector",
            f"Sector mood ({sector})",
            f"{_fmt_score(sector_sentiment.get('avg_score'))} \u00b7 {sector_sentiment.get('label')} "
            f"({sector_sentiment.get('n_articles')} articles)",
        ))

    # -- individual headlines (best citation material) --
    for h in (sentiment.get("top_headlines") or [])[:max_headlines]:
        items.append((
            "headline",
            f"Headline ({h.get('provider', 'Unknown')})",
            f"\"{h.get('title', '')}\" (sentiment {_fmt_score(h.get('score'))})",
        ))

    lines = [f"EVIDENCE FOR {ticker} ({company})" + (f" \u2014 Sector: {sector}" if sector else "")]
    lines.append("")
    for i, (etype, label, value) in enumerate(items, start=1):
        lines.append(f"[E{i}] type={etype} | {label}: {value}")

    return "\n".join(lines)


# ============================================================================
# Part 2: Bull/Bear prompts + the OpenAI call that produces one debate turn
# ============================================================================
import json
from openai import OpenAI

from debate_engine.config import OPENAI_API_KEY, OPENAI_MODEL_DEBATER

_CITATION_TYPES = ["sentiment", "technical", "sector", "headline", "synthesis", "risk", "concession"]

_RESPONSE_FORMAT_INSTRUCTIONS = """Respond with a single JSON object and nothing else, with exactly these keys:
{
  "text": "<your 2-4 sentence argument>",
  "citation_type": "<one of: sentiment, technical, sector, headline, synthesis, risk, concession>",
  "citation_label": "<short label for the citation, e.g. 'News sentiment (VADER)' or 'Bear concession'>",
  "citation_value": "<the specific number, headline, or phrase you are citing>",
  "conviction": <integer 0-100>
}

The "conviction" field: how confident YOU are right now in your own side's case (BULL: confidence this stock should be bought; BEAR: confidence this stock should be avoided/sold), considering everything said so far including this turn. On your first turn, base this on the evidence alone (typically 50-65). On later turns, adjust it honestly: if your opponent's point has genuinely weakened your case, lower it; if your case has held up or strengthened, raise it. A concession should come with a noticeably lower conviction than your previous turn. Even when your core view hasn't changed, the cumulative weight of the debate should usually nudge this value by a point or two each turn \u2014 an exact repeat of your previous conviction value should be rare.

CONSISTENCY: your conviction number and your text/citation must tell the same story. If you lower your conviction noticeably (more than ~5 points) from your previous turn, your text must reflect why \u2014 acknowledging your opponent's point \u2014 and citation_type should usually be "concession". If your text and citation present a fully confident, undiminished case for your side, your conviction should NOT drop sharply from your previous turn. Do not lower the number while writing text that reads as equally or more confident than before.

Citation rules:
- For "sentiment", "technical", "sector", or "headline": citation_label and citation_value MUST correspond to one of the [E#] evidence items above (light paraphrasing of citation_value is fine, but keep the numbers/headline recognizable).
- For "synthesis": use this when you're weighing multiple evidence items together (e.g. "3 of 3 signals point the same direction"). citation_value should briefly describe that cross-signal observation.
- For "risk": use this for a positioning/timing caveat that isn't a single evidence item (e.g. a crowded trade, entry timing). citation_value should briefly describe the risk.
- For "concession": use this ONLY when conceding a point your opponent made. citation_value should briefly describe what you're conceding.
- Do not repeat a citation_value that you or your opponent have already used earlier in this debate — pick a different angle.
"""

_SHARED_RULES = """Rules for every turn:
- Write 2-4 sentences. Sound like an analyst, not a cheerleader or a doom-monger — you are arguing in good faith for the strongest honest case on your side.
- Every sentence must be traceable either to one of the [E#] evidence items below or to a specific point made earlier in this transcript. Do NOT add generic claims about the company's strategy, competitive position, brand strength, product roadmap, or "future prospects" unless an [E#] item directly supports it — if you don't have evidence for a claim, leave it out.
- Cite exactly ONE piece of evidence per turn (see citation rules below).
- From exchange 2 onward, engage directly with your opponent's most recent point — rebut it, refine your position in light of it, or concede part of it if it has genuine merit. Do not ignore them and simply restate your own case.
- If, by a late exchange, your opponent's pushback has substantially weakened your case and you have no strong counter left, you may concede the overall direction while noting any residual point in your favour. A genuine debate can end in agreement — don't manufacture disagreement for its own sake."""

BULL_SYSTEM_PROMPT = """You are the BULL agent in an AI investment debate about {ticker} ({company}).

Your job is to build the most credible BULLISH case for {ticker}, using ONLY the evidence below and the debate transcript so far.

{shared_rules}

{evidence_brief}

{response_format_instructions}"""

BEAR_SYSTEM_PROMPT = """You are the BEAR agent in an AI investment debate about {ticker} ({company}).

Your job is to build the most credible BEARISH case for {ticker}, using ONLY the evidence below and the debate transcript so far.

{shared_rules}

{evidence_brief}

{response_format_instructions}"""


def format_transcript(transcript: List[Dict]) -> str:
    """Render prior turns for the user-turn prompt. Empty transcript -> opening-turn note."""
    if not transcript:
        return "(no exchanges yet \u2014 this is the opening turn of the debate)"
    lines = []
    for i, turn in enumerate(transcript, start=1):
        speaker = turn.get("speaker", "?").upper()
        lines.append(f"[Exchange {i} \u2014 {speaker}]: {turn.get('text', '')}")
        lines.append(f"  (cited: {turn.get('citationLabel', '')}: {turn.get('citationValue', '')})")
    return "\n".join(lines)


_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set \u2014 add it to your .env file.")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _used_citations(transcript: List[Dict]) -> List[str]:
    """Citation values already used by either side, for the 'don't repeat' check."""
    return [t.get("citationValue", "") for t in transcript if t.get("citationValue")]


def generate_turn(
    evidence: Dict,
    transcript: List[Dict],
    speaker: str,
    round_label: int,
    evidence_brief: Optional[str] = None,
    max_exchanges: int = 10,
) -> Dict:
    """
    Generate one debate turn for `speaker` ("bull" or "bear"), given the
    evidence packet and the transcript of prior turns.

    Returns a dict in the exact shape the frontend mockup expects:
        {speaker, roundLabel, text, citationType, citationLabel, citationValue, conviction}

    `evidence_brief` can be precomputed once via format_evidence_for_prompt()
    and passed in for all ~10 calls in a debate, to avoid reformatting it
    every turn (it doesn't change during a debate).
    """
    if speaker not in ("bull", "bear"):
        raise ValueError(f"speaker must be 'bull' or 'bear', got {speaker!r}")

    if evidence_brief is None:
        evidence_brief = format_evidence_for_prompt(evidence)

    template = BULL_SYSTEM_PROMPT if speaker == "bull" else BEAR_SYSTEM_PROMPT
    system_prompt = template.format(
        ticker=evidence.get("ticker", "?"),
        company=evidence.get("company_name", "?"),
        shared_rules=_SHARED_RULES,
        evidence_brief=evidence_brief,
        response_format_instructions=_RESPONSE_FORMAT_INSTRUCTIONS,
    )

    exchange_num = len(transcript) + 1
    used = _used_citations(transcript)
    used_block = "\n".join(f"  - {c}" for c in used) if used else "  (none yet \u2014 this is the opening turn)"

    late_note = ""
    if exchange_num >= max_exchanges - 2:
        late_note = (
            f"\nThis is one of the final exchanges ({exchange_num} of {max_exchanges}). "
            f"If you've already made your strongest distinct points and don't have a "
            f"genuinely new angle, this is a natural point to concede ground on the "
            f"overall direction (citation_type=\"concession\") while noting any residual "
            f"caveat \u2014 a debate can end in agreement rather than two sides repeating themselves."
        )

    user_prompt = (
        f"Debate transcript so far:\n{format_transcript(transcript)}\n\n"
        f"Citations already used by either side (do NOT reuse any of these \u2014 pick a "
        f"different [E#] item, or switch to synthesis/risk/concession):\n{used_block}\n"
        f"{late_note}\n\n"
        f"This is exchange {exchange_num} of {max_exchanges} (round {round_label}). "
        f"Respond now as the {speaker.upper()}, in the required JSON format."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL_DEBATER,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(f"Model did not return valid JSON: {content!r}") from exc

    citation_type = data.get("citation_type")
    if citation_type not in _CITATION_TYPES:
        citation_type = "synthesis"

    try:
        conviction_val = int(data.get("conviction", 50))
    except (TypeError, ValueError):
        conviction_val = 50
    conviction_val = max(0, min(100, conviction_val))

    return {
        "speaker": speaker,
        "roundLabel": round_label,
        "text": (data.get("text") or "").strip(),
        "citationType": citation_type,
        "citationLabel": data.get("citation_label", ""),
        "citationValue": data.get("citation_value", ""),
        "conviction": conviction_val,
    }


# ============================================================================
# Moderator: synthesizes the full debate into a final BUY/SELL verdict
# ============================================================================
from debate_engine.config import OPENAI_MODEL_MODERATOR

MODERATOR_SYSTEM_PROMPT = """You are the MODERATOR in an AI investment debate about {ticker} ({company}).

You have observed a full debate between a BULL agent (arguing the stock should be bought) and a BEAR agent (arguing it should be avoided or sold), both grounded in the evidence below.

{evidence_brief}

Full debate transcript:
{transcript}

Conviction trajectory \u2014 each agent's self-reported confidence (0-100) in their own side after each of their turns:
{conviction_summary}

Your job is to synthesize this into a final recommendation. Respond with a single JSON object and nothing else, with exactly these keys:
{{
  "action": "BUY or SELL",
  "confidence": <integer 0-100>,
  "sizing": "<one short original sentence with a position-sizing suggestion>",
  "reasoning": ["2-3 short one-sentence bullet points explaining WHY, referencing specific evidence and/or how the debate evolved (e.g. concessions, conviction trends)"]
}}

CONFIDENCE: do not default to a routine or "typical" number. Derive it from THIS debate specifically:
- How one-sided was the final exchange of evidence? A debate where one side's case fell apart under pushback warrants higher confidence (80-95) than one where both sides held up reasonably well under scrutiny (55-65).
- How much hard, specific evidence (numbers, named headlines) backed the winning side vs. soft or repeated claims?
- Did the losing side explicitly concede, or keep contesting to the end?
A confidence of exactly 65 or 70 should not appear by default \u2014 only if the specific reasoning below genuinely lands there. Vary your number meaningfully between different debates; identical confidence values across unrelated tickers signal you are not actually differentiating.

SIZING: write an ORIGINAL sentence, not a stock phrase. Pick a concrete percentage and framing that reflects how strong THIS verdict is (e.g. a high-confidence SELL on deteriorating fundamentals reads differently from a marginal SELL where the Bull case nearly held). Do not reuse the same sizing sentence you have used in other debates \u2014 vary the wording and the number to match this specific case.

Base your verdict on the full debate: which side built the more consistent, evidence-grounded case, where (if anywhere) one side conceded ground, and what the conviction trajectory shows. Be decisive \u2014 choose BUY or SELL, not a middle-ground "hold".

IMPORTANT: if your verdict does NOT match what a simple comparison of the final bull vs. bear conviction numbers above would suggest (e.g. you recommend SELL even though bull's final conviction is higher than bear's), say so explicitly in your reasoning \u2014 name the specific point(s) that make the substance of one side's case more decisive than the raw conviction numbers imply. Weighing argument quality over self-reported confidence is a deliberate feature of this system, not an error, but it should be explained, not left for the reader to puzzle over."""


def generate_verdict(
    evidence: Dict,
    transcript: List[Dict],
    conviction: List[Dict],
    evidence_brief: Optional[str] = None,
) -> Dict:
    """
    Synthesize a completed debate into a final verdict.

    `conviction` is the full trajectory, e.g.:
        [{"turn": 0, "bull": 50, "bear": 50}, {"turn": 1, "bull": 58, "bear": 50}, ...]

    Returns: {"action": "BUY"|"SELL", "confidence": int, "sizing": str, "reasoning": [str, ...]}
    """
    if evidence_brief is None:
        evidence_brief = format_evidence_for_prompt(evidence)

    # Compute confidence from the conviction trajectory BEFORE the API call,
    # so the Moderator can't anchor on 70%. The LLM still picks BUY/SELL and
    # writes the sizing/reasoning — we just take the number out of its hands.
    #
    # Logic: base confidence = 50 + abs(conviction_gap) * 1.2
    #   - gap 0  (total draw)     → 50  → clamped to 55%
    #   - gap 10 (moderate lean)  → 62%
    #   - gap 20 (clear winner)   → 74%
    #   - gap 30 (dominant side)  → 86%
    # Contrarian penalty: if the verdict contradicts who ended with higher
    # conviction (e.g. Bull ends higher but Moderator picks SELL), that's an
    # inherently less certain call — subtract 8 points.
    # Final clamp: 55-88 to avoid false certainty or false helplessness.
    final_conv = conviction[-1] if conviction else {"bull": 50, "bear": 50}
    bull_final = final_conv.get("bull", 50)
    bear_final = final_conv.get("bear", 50)
    gap = abs(bull_final - bear_final)
    base_confidence = 50 + gap * 1.2

    conviction_summary = "\n".join(
        f"  after exchange {c['turn']}: bull={c['bull']}, bear={c['bear']}" for c in conviction
    )

    system_prompt = MODERATOR_SYSTEM_PROMPT.format(
        ticker=evidence.get("ticker", "?"),
        company=evidence.get("company_name", "?"),
        evidence_brief=evidence_brief,
        transcript=format_transcript(transcript),
        conviction_summary=conviction_summary,
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL_MODERATOR,
        messages=[{"role": "system", "content": system_prompt}],
        response_format={"type": "json_object"},
        temperature=0.6,
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(f"Moderator did not return valid JSON: {content!r}") from exc

    action = str(data.get("action", "BUY")).upper()
    if action not in ("BUY", "SELL"):
        action = "BUY"

    # Apply contrarian penalty if verdict contradicts conviction numbers,
    # then clamp to the 55-88 range.
    bull_won_numerically = bull_final > bear_final
    verdict_is_buy = action == "BUY"
    contrarian = (bull_won_numerically and not verdict_is_buy) or \
                 (not bull_won_numerically and verdict_is_buy)
    if contrarian:
        base_confidence -= 8

    confidence = max(55, min(88, round(base_confidence)))

    reasoning = data.get("reasoning") or []
    if not isinstance(reasoning, list):
        reasoning = [str(reasoning)]

    return {
        "action": action,
        "confidence": confidence,
        "sizing": str(data.get("sizing", "")),
        "reasoning": [str(r) for r in reasoning],
    }
