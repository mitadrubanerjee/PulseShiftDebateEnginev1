# services/summarizer.py
"""
OpenAI-powered summaries with strict, consistent outputs.

Exports:
- summarize_from_headlines(headlines, points=4) -> SummaryResult
- summarize_sector_articles(articles, sector_name, points=4) -> SummaryResult
- summarize_company_articles(articles, company_name, ticker="", points=4) -> SummaryResult

All return the same schema:
SummaryResult = {
  "bullets": List[str],   # N bullet points, full sentences
  "text": str,            # single block (bullets joined w/ newlines)
  "model": str,           # model used
  "used_truncation": bool # True if we truncated input to stay within budget
}
"""

from __future__ import annotations
from typing import List, Dict, TypedDict
import re
import os

from openai import OpenAI
from core.config import OPENAI_API_KEY

OPENAI_MODEL_SUMMARIZER = os.getenv("OPENAI_MODEL_SUMMARIZER", "gpt-4o-mini")

# ---- Types -------------------------------------------------------------------
class SummaryResult(TypedDict):
    bullets: List[str]
    text: str
    model: str
    used_truncation: bool

# ---- OpenAI client (lazy) ----------------------------------------------------
_client_obj: OpenAI | None = None
def _client() -> OpenAI:
    global _client_obj
    if _client_obj is None:
        _client_obj = OpenAI(api_key=OPENAI_API_KEY)
    return _client_obj

# ---- Utilities ---------------------------------------------------------------
def _dedupe_keep_order(lines: List[str]) -> List[str]:
    seen, out = set(), []
    for x in lines:
        k = x.strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out

def _coerce_full_sentence(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if s.endswith((".", "!", "?")):
        return s
    m = list(re.finditer(r"[.!?]", s))
    if m:
        return s[: m[-1].end()].strip()
    if len(s) <= 240:
        return (s + ".").strip()
    return (s[:240].rstrip(" ,;:-") + ".").strip()

def _postprocess_bullets(raw_text: str, points: int) -> List[str]:
    lines = [ln.strip(" -*\t") for ln in raw_text.splitlines() if ln.strip()]
    if len(lines) <= 1:
        lines = re.split(r"(?<=[.!?])\s+", raw_text.strip())
    lines = [re.sub(r"^\d+[\).\]]\s*", "", ln).strip() for ln in lines if ln.strip()]
    lines = _dedupe_keep_order(lines)

    out = []
    for ln in lines[: points * 2]:
        if len(ln) < 3:
            continue
        out.append(_coerce_full_sentence(ln))

    out = out[:points]
    while len(out) < points:
        out.append("No additional material available.")
    return out

def _summarize_prompt(header: str, items_block: str, points: int) -> List[Dict[str, str]]:
    system = (
        "You are a senior financial editor. Compress multiple headlines into "
        f"exactly {points} crisp bullet points. Each bullet must be a complete sentence "
        "ending with a period. Focus on catalysts and directional cues. No preamble." \
        "Provide a good context as to why you are providing this summary, like your summary needs to be rich" \
        "and needs to provided a good enough understanding for a reader who has a great knowledge of financial markets. "
    )
    user = f"{header}\n\nHeadlines:\n{items_block}\n\nReturn exactly {points} bullets."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

def _call_openai(messages: List[Dict[str, str]], max_tokens: int = 250) -> str:
    resp = _client().chat.completions.create(
        model=OPENAI_MODEL_SUMMARIZER,
        temperature=0.2,
        max_tokens=max_tokens,
        messages=messages,
    )
    return (resp.choices[0].message.content or "").strip()

def _join_for_model(lines: List[str], sep: str = "\n") -> str:
    return sep.join(f"- {h.strip()}" for h in lines if h and h.strip())

from typing import List, Tuple

def _cap_input(headlines: List[str], char_budget: int) -> Tuple[List[str], bool]:
    kept, total = [], 0
    for h in headlines:
        h = re.sub(r"\s+", " ", h).strip()
        if not h:
            continue
        if total + len(h) + 2 > char_budget:
            break
        kept.append(h)
        total += len(h) + 2
    return kept, (len(kept) < len(headlines))

# ---- Public API --------------------------------------------------------------
def summarize_from_headlines(
    headlines: List[str],
    points: int = 4,
    char_budget: int = 5500,
) -> SummaryResult:
    headlines = _dedupe_keep_order([h.strip() for h in headlines if h and h.strip()])
    kept, used_trunc = _cap_input(headlines, char_budget=char_budget)
    if not kept:
        bullets = ["No material available."] * points
        txt = "\n".join(f"- {b}" for b in bullets)
        return {"bullets": bullets, "text": txt, "model": OPENAI_MODEL_SUMMARIZER, "used_truncation": False}

    items_block = _join_for_model(kept)
    messages = _summarize_prompt(
        header="Summarize the following market headlines for an equity/FX audience.",
        items_block=items_block,
        points=points,
    )
    raw = _call_openai(messages)
    bullets = _postprocess_bullets(raw, points=points)
    return {
        "bullets": bullets,
        "text": "\n".join(f"- {b}" for b in bullets),
        "model": OPENAI_MODEL_SUMMARIZER,
        "used_truncation": used_trunc,
    }

def summarize_sector_articles(
    articles: List[dict],
    sector_name: str,
    points: int = 4,
    char_budget: int = 5500,
) -> SummaryResult:
    heads = []
    for a in articles:
        t = (a.get("title") or "").strip()
        d = (a.get("description") or "").strip()
        heads.append(f"{t} — {d}" if t and d else t)
    return summarize_from_headlines(heads, points=points, char_budget=char_budget)

def summarize_company_articles(
    articles: List[dict],
    company_name: str,
    ticker: str = "",
    points: int = 4,
    char_budget: int = 5500,
) -> SummaryResult:
    heads = []
    for a in articles:
        t = (a.get("title") or "").strip()
        d = (a.get("description") or "").strip()
        heads.append(f"{t} — {d}" if t and d else t)

    kept, used_trunc = _cap_input(_dedupe_keep_order(heads), char_budget=char_budget)
    if not kept:
        bullets = ["No material available."] * points
        txt = "\n".join(f"- {b}" for b in bullets)
        return {"bullets": bullets, "text": txt, "model": OPENAI_MODEL_SUMMARIZER, "used_truncation": False}

    items_block = _join_for_model(kept)
    header = (
        f"Summarize headlines about {company_name}"
        + (f" ({ticker})" if ticker else "")
        + f" into exactly {points} bullet points. Each bullet must be a complete sentence."
    )
    messages = _summarize_prompt(header=header, items_block=items_block, points=points)
    raw = _call_openai(messages)
    bullets = _postprocess_bullets(raw, points=points)
    return {
        "bullets": bullets,
        "text": "\n".join(f"- {b}" for b in bullets),
        "model": OPENAI_MODEL_SUMMARIZER,
        "used_truncation": used_trunc,
    }


# --- Market wrap convenience wrapper -----------------------------------------
from typing import Dict, List

def generate_market_wrap(
    mood: Dict,
    headlines_by_sector: Dict[str, List[dict]],
    *,
    title: str = "Weekly Market Wrap",
    points: int = 4,
) -> Dict:
    """
    Assemble a 1-page markdown wrap:
      - Uses summarize_from_headlines() under the hood
      - Includes Market Mood line
      - Lists strongest/weakest sectors if a DataFrame is passed in mood["by_sector"]

    Returns:
      {
        "markdown": str,
        "bullets": List[str],
        "model": str,
        "used_truncation": bool,
      }
    """
    # Collect headlines across sectors
    heads: List[str] = []
    for _, articles in (headlines_by_sector or {}).items():
        for a in articles[:10]:
            t = (a.get("title") or "").strip()
            d = (a.get("description") or "").strip()
            heads.append(f"{t} — {d}" if t and d else t or d)

    # Summarize to N bullets
    summary = summarize_from_headlines(heads, points=points, char_budget=6000)

    # Build markdown
    mood_label = mood.get("label", "Neutral")
    mood_idx   = float(mood.get("avg_score", 0.0))
    n_articles = int(mood.get("n_articles", 0))

    md = []
    md.append(f"# {title}")
    md.append("")
    md.append(f"**Market Mood:** {mood_label} (Index {mood_idx:+.2f}, {n_articles} articles)")
    md.append("")
    for b in summary["bullets"]:
        md.append(f"- {b}")

    # Optional sector table (if DataFrame provided at mood['by_sector'])
    by_sector = mood.get("by_sector")
    if hasattr(by_sector, "sort_values"):
        try:
            strongest = by_sector.sort_values("avg_score", ascending=False).head(5)[["sector","avg_score","label"]]
            weakest   = by_sector.sort_values("avg_score", ascending=True).head(5)[["sector","avg_score","label"]]

            md.append("")
            md.append("**Strongest Sectors**")
            for _, r in strongest.iterrows():
                md.append(f"- {r['sector']}: {r['avg_score']:+.2f} ({r['label']})")

            md.append("")
            md.append("**Weakest Sectors**")
            for _, r in weakest.iterrows():
                md.append(f"- {r['sector']}: {r['avg_score']:+.2f} ({r['label']})")
        except Exception:
            # keep wrap even if sector frame missing columns
            pass

    return {
        "markdown": "\n".join(md),
        "bullets": summary["bullets"],
        "model": summary["model"],
        "used_truncation": summary["used_truncation"],
    }
