# services/sentiment_vader.py
from __future__ import annotations
from typing import List

# Use the standalone package that includes the lexicon (no NLTK download needed)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Lazy singleton
_SIA: SentimentIntensityAnalyzer | None = None

def _sia() -> SentimentIntensityAnalyzer:
    global _SIA
    if _SIA is None:
        _SIA = SentimentIntensityAnalyzer()
    return _SIA

def score_texts(texts: List[str]) -> List[float]:
    """
    Return a list of compound scores in [-1, +1] for each text.
    """
    sia = _sia()
    out: List[float] = []
    for t in texts or []:
        try:
            s = sia.polarity_scores(t or "")
            out.append(float(s.get("compound", 0.0)))
        except Exception:
            out.append(0.0)
    return out

# 5-label mapping using your thresholds
from core.config import THRESHOLDS

def label_for_score(score: float) -> str:
    """
    Map a continuous score to one of:
      'Negative', 'Trending Negative', 'Neutral', 'Trending Positive', 'Positive'
    """
    s = float(score)
    if s >= THRESHOLDS["positive_strong"]:
        return "Positive"
    if s >= THRESHOLDS["positive_mild"]:
        return "Trending Positive"
    if s > THRESHOLDS["negative_mild"]:
        return "Neutral"
    if s > THRESHOLDS["negative_strong"]:
        return "Trending Negative"
    return "Negative"
