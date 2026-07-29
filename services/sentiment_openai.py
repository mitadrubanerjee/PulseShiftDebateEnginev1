# services/sentiment_openai.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional, TypedDict, Literal
import math
import os

from core.config import THRESHOLDS, OPENAI_API_KEY, OPENAI_MODEL_CLASSIFIER

from openai import OpenAI


if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY missing. Set it in .streamlit/secrets.toml under [openai].api_key "
        "or as an environment variable OPENAI_API_KEY."
    )


BandLabel = Literal[
    "Positive",
    "Trending Positive",
    "Neutral",
    "Trending Negative",
    "Negative",
]

class SentimentAggregate(TypedDict):
    label: BandLabel
    avg_score: float
    std_score: float
    n_items: int
    counts: Dict[str, int]         # native: map our band back to +/-/neutral for compatibility
    band_counts: Dict[BandLabel, int]

class ScoredItem(TypedDict):
    text: str
    score: float                  # proxy continuous score from band
    finbert_label: str            # mapped: positive/neutral/negative (for compatibility)
    band_label: BandLabel
    meta: Dict[str, str]

# Map band to a proxy numeric score for averaging/heatmaps
BAND_TO_SCORE: Dict[BandLabel, float] = {
    "Positive": 0.65,
    "Trending Positive": 0.25,
    "Neutral": 0.0,
    "Trending Negative": -0.25,
    "Negative": -0.65,
}

def _band_to_native(b: BandLabel) -> str:
    if b in ("Positive", "Trending Positive"):
        return "positive"
    if b in ("Negative", "Trending Negative"):
        return "negative"
    return "neutral"

_client: Optional[OpenAI] = None
def _client_lazy() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

# Short, strict classifier prompt (one token-efficient line label)
_SYSTEM = (
    "You are a strict sentiment classifier for finance headlines/descriptions. "
    "Return only one label exactly from this set:\n"
    "Positive | Trending Positive | Neutral | Trending Negative | Negative."
)
_USER_FMT = (
    "Classify the overall sentiment of this text for an equity investor. "
    "Return ONLY the label (no punctuation, no explanation):\n\n{snippet}"
)

def _classify_one(snippet: str) -> BandLabel:
    snippet = (snippet or "").strip()
    if not snippet:
        return "Neutral"
    cl = _client_lazy()
    try:
        resp = cl.chat.completions.create(
            model=OPENAI_MODEL_CLASSIFIER,
            temperature=0.0,
            max_tokens=4,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _USER_FMT.format(snippet=snippet[:800])},  # hard cap
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Normalize
        r = raw.lower()
        if "trending positive" in r:
            return "Trending Positive"
        if "trending negative" in r:
            return "Trending Negative"
        if "positive" == r or r.startswith("positive"):
            return "Positive"
        if "negative" == r or r.startswith("negative"):
            return "Negative"
        if "neutral" in r or r == "":
            return "Neutral"
        # Default fallback
        return "Neutral"
    except Exception:
        return "Neutral"

def _aggregate_bands(bands: List[BandLabel]) -> SentimentAggregate:
    n = len(bands)
    if n == 0:
        return {
            "label": "Neutral",
            "avg_score": 0.0,
            "std_score": 0.0,
            "n_items": 0,
            "counts": {"positive": 0, "neutral": 0, "negative": 0},
            "band_counts": {
                "Positive": 0,
                "Trending Positive": 0,
                "Neutral": 0,
                "Trending Negative": 0,
                "Negative": 0,
            },
        }
    scores = [BAND_TO_SCORE[b] for b in bands]
    avg = sum(scores) / n
    var = sum((s - avg) ** 2 for s in scores) / n
    std = math.sqrt(var)

    # native +/-/neutral counts derived from bands
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    band_counts: Dict[BandLabel, int] = {
        "Positive": 0,
        "Trending Positive": 0,
        "Neutral": 0,
        "Trending Negative": 0,
        "Negative": 0,
    }
    for b in bands:
        band_counts[b] += 1
        counts[_band_to_native(b)] += 1

    # Map avg continuous back to band for overall label using your thresholds.
    # (We reuse the same mapping logic by thresholds.)
    def classify_band(score: float) -> BandLabel:
        if score >= THRESHOLDS["positive_strong"]:
            return "Positive"
        if score >= THRESHOLDS["positive_mild"]:
            return "Trending Positive"
        if score <= THRESHOLDS["negative_strong"]:
            return "Negative"
        if score <= THRESHOLDS["negative_mild"]:
            return "Trending Negative"
        return "Neutral"

    overall = classify_band(avg)

    return {
        "label": overall,
        "avg_score": avg,
        "std_score": std,
        "n_items": n,
        "counts": counts,
        "band_counts": band_counts,
    }

def _article_to_text(a) -> str:
    title = a.get("title") or ""
    desc = a.get("description") or ""
    t = f"{title}. {desc}".strip().strip(" .")
    return t[:800]  # keep prompt small + cheap

def score_texts(texts: List[str]) -> Tuple[SentimentAggregate, List[ScoredItem]]:
    bands: List[BandLabel] = []
    items: List[ScoredItem] = []
    for t in texts:
        band = _classify_one(t)
        bands.append(band)
        items.append({
            "text": t,
            "score": BAND_TO_SCORE[band],
            "finbert_label": _band_to_native(band),
            "band_label": band,
            "meta": {},
        })
    agg = _aggregate_bands(bands)
    return agg, items

def score_articles(articles: List[dict]) -> Tuple[SentimentAggregate, List[ScoredItem]]:
    bands: List[BandLabel] = []
    items: List[ScoredItem] = []
    for a in articles:
        t = _article_to_text(a)
        band = _classify_one(t)
        bands.append(band)
        items.append({
            "text": t,
            "score": BAND_TO_SCORE[band],
            "finbert_label": _band_to_native(band),
            "band_label": band,
            "meta": {
                "url": a.get("url") or "",
                "provider": a.get("provider") or "",
                "title": a.get("title") or "",
                "published_at": a.get("published_at") or "",
            },
        })
    agg = _aggregate_bands(bands)
    return agg, items

def quick_label_from_texts(texts: List[str]) -> BandLabel:
    agg, _ = score_texts(texts)
    return agg["label"]
