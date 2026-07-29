# services/aggregators.py
"""
Aggregations for homepage/dashboard.

Inputs:
- company/sector article lists in the unified article dict shape:
  {"title": str, "description": str, "source": str, "url": str, "published_at": str}

Outputs:
- Market Mood index dict (consistent keys)
- Sector sentiment DataFrame (consistent columns)

This module ONLY depends on the sentiment engines for scoring:
- services.sentiment_finbert (preferred)
- services.sentiment_vader   (fallback)

Each engine must expose:
  score_texts(texts: list[str]) -> list[float]   # scores in [-1, +1]
  label_for_score(score: float) -> str           # one of 5 labels
"""

from __future__ import annotations
from typing import Dict, List, Iterable, Tuple
import numpy as np
import pandas as pd

# ---- choose sentiment engine -------------------------------------------------
# FinBERT first (finance-specific), fallback to VADER if import fails.
try:
    from services.sentiment_finbert import score_texts as _score_texts_finbert
    from services.sentiment_finbert import label_for_score as _label_for_score_finbert
    _HAS_FINBERT = True
except Exception:
    _HAS_FINBERT = False

try:
    from services.sentiment_vader import score_texts as _score_texts_vader
    from services.sentiment_vader import label_for_score as _label_for_score_vader
    _HAS_VADER = True
except Exception:
    _HAS_VADER = False


def _select_engine(engine: str) -> Tuple:
    """
    Returns (score_texts_fn, label_for_score_fn) for the requested engine.
    engine: "finbert" | "vader" | "auto"
    """
    e = (engine or "auto").lower()

    if e == "finbert":
        if not _HAS_FINBERT:
            raise RuntimeError("FinBERT engine requested but not available.")
        return _score_texts_finbert, _label_for_score_finbert

    if e == "vader":
        if not _HAS_VADER:
            raise RuntimeError("VADER engine requested but not available.")
        return _score_texts_vader, _label_for_score_vader

    # auto
    if _HAS_FINBERT:
        return _score_texts_finbert, _label_for_score_finbert
    if _HAS_VADER:
        return _score_texts_vader, _label_for_score_vader
    raise RuntimeError("No sentiment engine available (FinBERT/VADER).")


# ---- helpers ----------------------------------------------------------------
def _to_texts(articles: Iterable[Dict]) -> List[str]:
    """
    Convert article dicts to scoreable strings.
    """
    out: List[str] = []
    for a in articles:
        title = (a.get("title") or "").strip()
        desc  = (a.get("description") or "").strip()
        if title and desc:
            out.append(f"{title} — {desc}")
        elif title:
            out.append(title)
        elif desc:
            out.append(desc)
    return out


# ---- public API --------------------------------------------------------------
def compute_market_mood_index(
    articles: List[Dict],
    *,
    engine: str = "auto",
) -> Dict:
    """
    Aggregate sentiment over a flat list of articles.

    Returns dict with stable keys:
    {
      "avg_score": float,     # mean in [-1, +1]
      "std_score": float,     # std
      "label": str,           # one of 5 labels
      "n_articles": int
    }
    """
    score_fn, label_fn = _select_engine(engine)
    texts = _to_texts(articles)

    if not texts:
        return {"avg_score": 0.0, "std_score": 0.0, "label": "Neutral", "n_articles": 0}

    scores = score_fn(texts)  # list of floats [-1,+1]
    if not scores:
        return {"avg_score": 0.0, "std_score": 0.0, "label": "Neutral", "n_articles": 0}

    arr = np.array(scores, dtype=float)
    avg = float(np.nanmean(arr))
    std = float(np.nanstd(arr))
    label = label_fn(avg)

    return {
        "avg_score": avg,
        "std_score": std,
        "label": label,
        "n_articles": int(len(arr)),
    }


def compute_sector_sentiments(
    sector_articles: Dict[str, List[Dict]],
    *,
    engine: str = "auto",
) -> pd.DataFrame:
    """
    Aggregate sentiment per sector.

    sector_articles: {"Technology": [article,...], "Financials": [...], ...}

    Returns DataFrame with stable columns (one row per sector):
      ["sector", "avg_score", "std_score", "label", "n_items"]
    """
    score_fn, label_fn = _select_engine(engine)

    rows = []
    for sector, articles in (sector_articles or {}).items():
        texts = _to_texts(articles)
        if not texts:
            rows.append({
                "sector": sector,
                "avg_score": 0.0,
                "std_score": 0.0,
                "label": "Neutral",
                "n_items": 0,
            })
            continue

        scores = score_fn(texts)
        if not scores:
            rows.append({
                "sector": sector,
                "avg_score": 0.0,
                "std_score": 0.0,
                "label": "Neutral",
                "n_items": 0,
            })
            continue

        arr = np.array(scores, dtype=float)
        avg = float(np.nanmean(arr))
        std = float(np.nanstd(arr))
        label = label_fn(avg)

        rows.append({
            "sector": sector,
            "avg_score": avg,
            "std_score": std,
            "label": label,
            "n_items": int(len(arr)),
        })

    # consistent schema even if empty
    df = pd.DataFrame(rows, columns=["sector", "avg_score", "std_score", "label", "n_items"])
    return df


def build_dashboard_payload(
    *,
    market_articles: List[Dict],
    sector_articles: Dict[str, List[Dict]],
    engine: str = "auto",
) -> Dict:
    """
    Convenience wrapper that returns *everything the homepage needs* in a single payload.

    Returns:
    {
      "mood":  {avg_score, std_score, label, n_articles},
      "by_sector": DataFrame(sector, avg_score, std_score, label, n_items)
    }
    """
    mood = compute_market_mood_index(market_articles, engine=engine)
    by_sector = compute_sector_sentiments(sector_articles, engine=engine)
    return {"mood": mood, "by_sector": by_sector}
