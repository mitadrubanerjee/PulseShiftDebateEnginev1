# services/sentiment.py
"""
Unified sentiment scoring with 5-band labels:
  Positive | Trending Positive | Neutral | Trending Negative | Negative

Default engine: FinBERT (ProsusAI/finbert) — free, local, finance-tuned.
Fallback: VADER (if transformers / model unavailable).

All public functions return the same stable schema so UI/pages remain decoupled.
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional, TypedDict, Literal
import math

# ---- App config: thresholds, etc. -------------------------------------------
from core.config import THRESHOLDS  # must include keys used below

# Expected THRESHOLDS keys:
# THRESHOLDS = {
#     "positive_strong":  0.35,
#     "positive_mild":    0.15,
#     "neutral":          0.0,
#     "negative_mild":   -0.15,
#     "negative_strong": -0.35,
# }

# ---- Optional imports (FinBERT / VADER) -------------------------------------
# We try FinBERT first; if unavailable, we’ll fallback to VADER automatically.
_HAS_FINBERT = False
_HAS_VADER = False

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _HAS_FINBERT = True
except Exception:
    _HAS_FINBERT = False

try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _HAS_VADER = True
except Exception:
    _HAS_VADER = False


# ---- Stable schemas ----------------------------------------------------------
BandLabel = Literal[
    "Positive",
    "Trending Positive",
    "Neutral",
    "Trending Negative",
    "Negative",
]

class SentimentAggregate(TypedDict):
    label: BandLabel                 # final 5-band label on average score
    avg_score: float                 # mean of article scores in [-1, +1]
    std_score: float                 # std dev of article scores
    n_items: int                     # number of scored items
    counts: Dict[str, int]           # {"positive": X, "neutral": Y, "negative": Z}
    band_counts: Dict[BandLabel, int]# per-article 5-band classification counts

class ScoredItem(TypedDict):
    text: str
    score: float                     # [-1, +1] continuous
    finbert_label: str               # "positive" | "neutral" | "negative" (engine native)
    band_label: BandLabel            # mapped into 5-band
    meta: Dict[str, str]             # optional info (e.g., url, provider, title)


# ---- Engine singletons (FinBERT / VADER) ------------------------------------
_FINBERT_TOKENIZER = None
_FINBERT_MODEL = None
_FINBERT_ID2LABEL = {0: "negative", 1: "neutral", 2: "positive"}

def _load_finbert():
    """
    Lazy-load FinBERT once. If anything fails, keep _HAS_FINBERT = False
    so the caller uses fallback automatically.
    """
    global _FINBERT_TOKENIZER, _FINBERT_MODEL, _HAS_FINBERT
    if not _HAS_FINBERT:
        return False
    if _FINBERT_MODEL is not None:
        return True
    try:
        model_name = "ProsusAI/finbert"
        _FINBERT_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        _FINBERT_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name)
        _FINBERT_MODEL.eval()
        return True
    except Exception:
        _HAS_FINBERT = False
        return False

_VADER = None
def _load_vader():
    global _VADER, _HAS_VADER
    if not _HAS_VADER:
        return False
    if _VADER is not None:
        return True
    try:
        # ensure lexicon exists (no-op if already downloaded)
        nltk.download("vader_lexicon", quiet=True)
        _VADER = SentimentIntensityAnalyzer()
        return True
    except Exception:
        _HAS_VADER = False
        return False


# ---- Public helpers: label mapping ------------------------------------------
def classify_band(score: float) -> BandLabel:
    """
    Map a continuous score in [-1, +1] to the 5-band label.
    Uses THRESHOLDS from config.
    """
    if score >= THRESHOLDS["positive_strong"]:
        return "Positive"
    if score >= THRESHOLDS["positive_mild"]:
        return "Trending Positive"
    if score <= THRESHOLDS["negative_strong"]:
        return "Negative"
    if score <= THRESHOLDS["negative_mild"]:
        return "Trending Negative"
    return "Neutral"


# ---- Core FinBERT scoring ----------------------------------------------------
def _finbert_score_texts(texts: List[str], batch_size: int = 16, max_len: int = 128) -> List[Tuple[float, str]]:
    """
    Score texts with FinBERT.
    Returns list of tuples: (score, finbert_label)
      - score ∈ [-1, +1], defined as (p_pos - p_neg), neutral contributes 0.
      - finbert_label ∈ {"positive","neutral","negative"} (argmax)
    """
    assert _FINBERT_MODEL is not None and _FINBERT_TOKENIZER is not None

    scores: List[Tuple[float, str]] = []
    device = "cuda" if hasattr(torch, "cuda") and torch.cuda.is_available() else "cpu"
    _FINBERT_MODEL.to(device)

    # Mini-batching for speed/memory
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        enc = _FINBERT_TOKENIZER(
            chunk,
            padding=True,
            truncation=True,
            max_length=max_len,
            return_tensors="pt",
        )
        enc = {k: v.to(device) for k, v in enc.items()}

        with torch.no_grad():
            logits = _FINBERT_MODEL(**enc).logits  # [B, 3]
            probs = torch.softmax(logits, dim=-1).cpu().numpy()

        for row in probs:
            p_neg, p_neu, p_pos = float(row[0]), float(row[1]), float(row[2])
            score = p_pos - p_neg  # continuous in [-1, +1]
            label_idx = int(row.argmax())
            label = _FINBERT_ID2LABEL[label_idx]
            scores.append((score, label))

    return scores


# ---- VADER fallback scoring --------------------------------------------------
def _vader_score_texts(texts: List[str]) -> List[Tuple[float, str]]:
    """
    VADER: convert compound ∈ [-1,+1] to same continuous score.
    finbert_label here is emulated ("positive"/"neutral"/"negative") for consistency.
    """
    scores: List[Tuple[float, str]] = []
    for t in texts:
        s = _VADER.polarity_scores(t or "")
        comp = float(s.get("compound", 0.0))
        # emulate discrete label from compound for counts
        if comp >= 0.05:
            lbl = "positive"
        elif comp <= -0.05:
            lbl = "negative"
        else:
            lbl = "neutral"
        scores.append((comp, lbl))
    return scores


# ---- Aggregation -------------------------------------------------------------
def _aggregate_scores(scored: List[Tuple[float, str]]) -> Tuple[SentimentAggregate, Dict[BandLabel, int]]:
    """
    Aggregate a list of (score, finbert_label) into SentimentAggregate.
    """
    n = len(scored)
    if n == 0:
        # stable empty aggregate
        agg: SentimentAggregate = {
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
        return agg, agg["band_counts"]

    scores = [s for s, _ in scored]
    avg = sum(scores) / n
    var = sum((s - avg) ** 2 for s in scores) / n
    std = math.sqrt(var)

    # native counts
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    band_counts: Dict[BandLabel, int] = {
        "Positive": 0,
        "Trending Positive": 0,
        "Neutral": 0,
        "Trending Negative": 0,
        "Negative": 0,
    }

    for s, finbert_label in scored:
        counts[finbert_label] += 1
        band = classify_band(s)
        band_counts[band] += 1

    overall_label = classify_band(avg)

    agg: SentimentAggregate = {
        "label": overall_label,
        "avg_score": avg,
        "std_score": std,
        "n_items": n,
        "counts": counts,
        "band_counts": band_counts,
    }
    return agg, band_counts


# ---- Public API: raw texts ---------------------------------------------------
def score_texts(
    texts: List[str],
    engine: Literal["finbert", "auto", "vader"] = "auto",
    batch_size: int = 16,
    max_len: int = 128,
) -> Tuple[SentimentAggregate, List[ScoredItem]]:
    """
    Score a list of raw texts with the selected engine.
    Returns:
      - SentimentAggregate
      - per-item list with score + labels (for tables/exports)
    """
    use_finbert = False
    if engine == "finbert":
        use_finbert = _load_finbert()
    elif engine == "auto":
        use_finbert = _load_finbert()
        if not use_finbert:
            _load_vader()
    elif engine == "vader":
        _load_vader()

    if use_finbert:
        scored_pairs = _finbert_score_texts(texts, batch_size=batch_size, max_len=max_len)
    else:
        if not _VADER:
            # if neither available, return empty neutral aggregate
            return _aggregate_scores([])[0], []
        scored_pairs = _vader_score_texts(texts)

    agg, _ = _aggregate_scores(scored_pairs)

    items: List[ScoredItem] = []
    for t, (score, fin_lbl) in zip(texts, scored_pairs):
        items.append(
            ScoredItem(
                text=t,
                score=score,
                finbert_label=fin_lbl,
                band_label=classify_band(score),
                meta={},  # raw texts have no extra meta
            )
        )

    return agg, items


# ---- Public API: NewsArticle list -------------------------------------------
# Keep this import local to avoid circular imports at module load time
def _article_to_text(a) -> str:
    # a is NewsArticle from services/news_fetcher.py
    # Build a robust snippet for scoring
    title = a.get("title") or ""
    desc = a.get("description") or ""
    # prioritize full sentence; combine succinctly
    return f"{title}. {desc}".strip().strip(" .")

def score_articles(
    articles: List[dict],
    engine: Literal["finbert", "auto", "vader"] = "auto",
    batch_size: int = 16,
    max_len: int = 128,
) -> Tuple[SentimentAggregate, List[ScoredItem]]:
    """
    Score a list of NewsArticle dicts (from news_fetcher).
    Returns:
      - SentimentAggregate (5-band label on average)
      - per-article ScoredItem list with meta (url/provider)
    """
    texts = [_article_to_text(a) for a in articles]
    agg, items = score_texts(texts, engine=engine, batch_size=batch_size, max_len=max_len)

    # enrich with article meta
    enriched: List[ScoredItem] = []
    for a, item in zip(articles, items):
        meta = {
            "url": a.get("url") or "",
            "provider": a.get("provider") or "",
            "title": a.get("title") or "",
            "published_at": a.get("published_at") or "",
        }
        item["meta"] = meta
        enriched.append(item)

    return agg, enriched


# ---- Tiny convenience for direct average-only use ----------------------------
def quick_label_from_texts(
    texts: List[str],
    engine: Literal["finbert", "auto", "vader"] = "auto",
) -> BandLabel:
    agg, _ = score_texts(texts, engine=engine)
    return agg["label"]
