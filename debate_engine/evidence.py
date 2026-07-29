# debate_engine/evidence.py
"""
Assembles the per-ticker "evidence packet" that the Bull and Bear agents
argue from.

Status:
  - Part 1 (done): news + sentiment evidence for a company, and sentiment
    for its sector. Reuses services.news_fetcher (no Streamlit/secrets
    dependency) plus a small local VADER scorer that mirrors
    services.sentiment_vader's contract without importing core/config.

  - Part 2 (done): ticker -> sector resolution and the RSI/ATR technical
    signal, both via Polygon. Mirrors the logic in
    services/ticker_resolver.py and scoring_script/scoring.py, but reads
    the Polygon key from debate_engine.config (env-based) instead of
    st.secrets, so it runs as a plain script / under FastAPI.

  - Quant model (parked, not in v1): get_quant_signal() works but isn't
    called by get_evidence_packet() — see its docstring for why.

  - get_evidence_packet(ticker, company_name): combines Parts 1 + 2 into
    the single dict the Bull/Bear/Moderator prompts consume. This is the
    only function the rest of the debate engine (agents.py,
    orchestrator.py) needs to call — everything above is an implementation
    detail of this.

NOTE: get_evidence_packet() makes several network calls (news + Polygon).
It should be called ONCE per debate and the resulting dict reused for all
~10 exchanges — not re-fetched per turn.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import re

import numpy as np
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from services.news_fetcher import fetch_company_news, fetch_sector_news
from debate_engine.config import (
    THRESHOLDS,
    SECTOR_QUERIES,
    SECTOR_NORMALIZATION,
    POLYGON_API_KEY,
    FRESHNESS_DAYS,
    MAX_RESULTS_PER_QUERY,
)

_SIA = SentimentIntensityAnalyzer()


# ---- sentiment scoring (mirrors services/sentiment_vader.py) -------------
def _score_texts(texts: List[str]) -> List[float]:
    """Return VADER compound scores in [-1, +1] for each text."""
    out: List[float] = []
    for t in texts or []:
        try:
            out.append(float(_SIA.polarity_scores(t or "")["compound"]))
        except Exception:
            out.append(0.0)
    return out


def _label_for_score(score: float) -> str:
    """Map a continuous score to one of the 5 canonical sentiment labels."""
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


def _articles_to_texts(articles: List[Dict]) -> List[str]:
    """Convert article dicts (title/description) into scoreable strings."""
    out: List[str] = []
    for a in articles:
        title = (a.get("title") or "").strip()
        desc = (a.get("description") or "").strip()
        if title and desc:
            out.append(f"{title} \u2014 {desc}")
        elif title:
            out.append(title)
        elif desc:
            out.append(desc)
    return out


# ---- low-information headline filter --------------------------------------
# MarketBeat / AmericanBankingNews / ETF Daily News etc. publish a high
# volume of templated "institutional investor bought/sold/grew its stake"
# articles whenever 13F filings get processed — these dominate Google News
# results for any large-cap ticker, score artificially high on VADER (words
# like "Acquires"/"Grows"/"Raises" read as positive), and make weak debate
# citations (routine portfolio rebalancing, not company news). Filtering
# these out improves both the aggregate sentiment signal and the headlines
# offered as citations.
_LOW_INFO_PATTERNS = [
    re.compile(r"\bshares\s+(bought|sold|acquired|purchased)\s+by\b", re.I),
    re.compile(r"\b(grows|cuts|trims|raises|lowers|reduces|increases|boosts|takes|buys|sells out of)\b\s+(its\s+|their\s+)?(stock\s+)?(holdings|position|stake)\b", re.I),
    re.compile(r"\bacquires?\s+[\d,]+\s+shares\b", re.I),
    re.compile(r"\bsells?\s+[\d,]+\s+shares\b", re.I),
    re.compile(r"\bSEC\s+13F\b", re.I),
]


def _is_low_information(article: Dict) -> bool:
    title = article.get("title") or ""
    return any(p.search(title) for p in _LOW_INFO_PATTERNS)


def _filter_low_information(articles: List[Dict]) -> List[Dict]:
    """Drop templated institutional-ownership-update articles (see above)."""
    return [a for a in articles if not _is_low_information(a)]


_EMPTY_SENTIMENT = {
    "avg_score": 0.0,
    "std_score": 0.0,
    "label": "Neutral",
    "n_articles": 0,
    "top_headlines": [],
}


# ---- public API ------------------------------------------------------------
def get_company_sentiment(
    company_name: str,
    *,
    days: int = FRESHNESS_DAYS,
    max_results: int = MAX_RESULTS_PER_QUERY,
    top_n_headlines: int = 5,
) -> Dict:
    """
    Fetch recent news for `company_name` and return aggregate sentiment plus
    the most sentiment-salient headlines (for use as debate citations).

    Returns:
    {
      "avg_score": float,      # mean VADER compound score, [-1, +1]
      "std_score": float,      # dispersion across articles
      "label": str,            # one of 5 canonical sentiment labels
      "n_articles": int,
      "top_headlines": [
          {"title": str, "provider": str, "url": str, "score": float}, ...
      ]
    }
    """
    articles = fetch_company_news(company_name, days=days, max_results=max_results)
    articles = _filter_low_information(articles)
    texts = _articles_to_texts(articles)

    if not texts:
        return dict(_EMPTY_SENTIMENT)

    scores = _score_texts(texts)
    arr = np.array(scores, dtype=float)
    avg = float(np.nanmean(arr))
    std = float(np.nanstd(arr))
    label = _label_for_score(avg)

    # Rank headlines by |score| so the most sentiment-salient ones surface
    # first — these make the best debate citations.
    ranked = sorted(zip(articles, scores), key=lambda pair: abs(pair[1]), reverse=True)
    top_headlines = [
        {
            "title": a.get("title", ""),
            "provider": a.get("provider", "Unknown"),
            "url": a.get("url", ""),
            "score": round(float(s), 3),
        }
        for a, s in ranked[:top_n_headlines]
    ]

    return {
        "avg_score": round(avg, 3),
        "std_score": round(std, 3),
        "label": label,
        "n_articles": int(len(arr)),
        "top_headlines": top_headlines,
    }


def get_sector_sentiment(
    sector: str,
    *,
    days: int = FRESHNESS_DAYS,
    max_results: int = MAX_RESULTS_PER_QUERY,
) -> Dict:
    """
    Aggregate sentiment for a whole sector using the pre-built sector query
    strings in debate_engine.config.SECTOR_QUERIES.

    Returns the same shape as get_company_sentiment but without
    `top_headlines` (sector-level evidence cites the aggregate score only).
    Returns the neutral default if `sector` isn't a recognized key.
    """
    query = SECTOR_QUERIES.get(sector)
    if not query:
        out = dict(_EMPTY_SENTIMENT)
        out.pop("top_headlines")
        return out

    articles = fetch_sector_news(query, days=days, max_results=max_results)
    articles = _filter_low_information(articles)
    texts = _articles_to_texts(articles)

    if not texts:
        out = dict(_EMPTY_SENTIMENT)
        out.pop("top_headlines")
        return out

    scores = _score_texts(texts)
    arr = np.array(scores, dtype=float)
    avg = float(np.nanmean(arr))
    std = float(np.nanstd(arr))

    return {
        "avg_score": round(avg, 3),
        "std_score": round(std, 3),
        "label": _label_for_score(avg),
        "n_articles": int(len(arr)),
    }


# ---- ticker -> sector resolution (SIC-code based) -------------------------
# Polygon's /v3/reference/tickers/{ticker} endpoint doesn't reliably populate
# "sector" or "industry" — those come back empty on most plans. What IS
# populated is "sic_code" (Standard Industrial Classification, e.g. NVDA =
# 3674 "Semiconductors & Related Devices"). SIC codes are far more granular
# than our 11-sector taxonomy, so we map *ranges* of codes to sectors.
#
# Ordered (low, high, sector) — narrow carve-outs are listed BEFORE the
# broader ranges that contain them, since the first match wins.
_SIC_RANGES = [
    # --- carve-outs within broader ranges (checked first) ---
    (2833, 2836, "Healthcare"),               # pharmaceutical preparations / biologics
    (2840, 2844, "Consumer Staples"),         # soap, cosmetics, cleaning preparations
    (3570, 3579, "Technology"),               # computer & office equipment (e.g. AAPL)
    (3711, 3711, "Consumer Discretionary"),   # motor vehicles
    (3826, 3851, "Healthcare"),               # lab/medical/surgical instruments
    (4830, 4841, "Communication Services"),   # broadcasting & cable
    (5400, 5499, "Consumer Staples"),         # food stores
    (7370, 7379, "Technology"),               # computer services / software

    # --- broad SIC divisions ---
    (1000, 1099, "Materials"),                # metal mining
    (1200, 1299, "Energy"),                   # coal mining
    (1300, 1399, "Energy"),                   # oil & gas extraction (e.g. XOM)
    (1400, 1499, "Materials"),                # nonmetallic minerals
    (1500, 1799, "Industrials"),              # construction
    (2000, 2199, "Consumer Staples"),         # food, beverages, tobacco
    (2200, 2599, "Consumer Discretionary"),   # textiles, apparel, furniture
    (2600, 2699, "Materials"),                # paper
    (2700, 2799, "Communication Services"),   # printing & publishing
    (2800, 2899, "Materials"),                # chemicals (pharma carved out above)
    (2900, 2999, "Energy"),                   # petroleum refining
    (3000, 3099, "Materials"),                # rubber & plastics
    (3200, 3399, "Materials"),                # stone/clay/glass/concrete, primary metals
    (3400, 3499, "Industrials"),              # fabricated metal products
    (3500, 3599, "Industrials"),              # industrial machinery (computers carved out above)
    (3600, 3699, "Technology"),               # electronics, incl. semiconductors (e.g. NVDA)
    (3700, 3799, "Industrials"),              # transportation equipment (motor vehicles carved out above)
    (3800, 3899, "Industrials"),              # instruments (medical carved out above)
    (3900, 3999, "Consumer Discretionary"),   # misc manufacturing
    (4000, 4299, "Industrials"),              # rail, transit, trucking
    (4400, 4599, "Industrials"),              # water & air transport
    (4700, 4799, "Industrials"),              # transportation services
    (4800, 4899, "Communication Services"),   # communications (broadcasting carved out above)
    (4900, 4999, "Utilities"),                # electric, gas, sanitary services
    (5000, 5199, "Consumer Discretionary"),   # wholesale trade
    (5200, 5999, "Consumer Discretionary"),   # retail trade (food stores carved out above)
    (6000, 6099, "Financials"),               # depository institutions / banks (e.g. JPM)
    (6100, 6299, "Financials"),               # credit institutions, brokers
    (6300, 6499, "Financials"),               # insurance
    (6500, 6599, "Real Estate"),
    (6700, 6799, "Financials"),               # holding / investment offices
    (7000, 7099, "Consumer Discretionary"),   # hotels
    (7200, 7299, "Consumer Discretionary"),   # personal services
    (7300, 7399, "Industrials"),              # business services (software carved out above)
    (7500, 7599, "Consumer Discretionary"),   # auto repair & services
    (7800, 7899, "Communication Services"),   # motion pictures
    (7900, 7999, "Consumer Discretionary"),   # amusement & recreation
    (8000, 8099, "Healthcare"),               # health services
    (8700, 8799, "Industrials"),              # engineering & management services
]


def _sic_code_to_sector(sic_code) -> Optional[str]:
    """Map a Polygon SIC code (str or int) to one of our 11 sector keys."""
    try:
        code = int(sic_code)
    except (TypeError, ValueError):
        return None
    for low, high, sector in _SIC_RANGES:
        if low <= code <= high:
            return sector
    return None


def get_ticker_sector(ticker: str) -> Optional[str]:
    """
    Resolve `ticker`'s sector via Polygon's ticker-details endpoint,
    normalized to one of the canonical SECTOR_QUERIES keys.

    Primary path: map the numeric `sic_code` via _SIC_RANGES (this is what
    Polygon actually populates). Fallback: if `sector` / `industry` /
    `sic_description` happen to be populated and match SECTOR_NORMALIZATION,
    use that instead.

    Returns None if nothing can be resolved/mapped — callers should treat
    sector evidence as optional in that case.
    """
    if not ticker or not POLYGON_API_KEY:
        return None
    try:
        url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
        r = requests.get(url, params={"apiKey": POLYGON_API_KEY}, timeout=15)
        r.raise_for_status()
        result = r.json().get("results", {}) or {}

        sic_mapped = _sic_code_to_sector(result.get("sic_code"))
        if sic_mapped:
            return sic_mapped

        for field in ("sector", "industry", "sic_description"):
            val = result.get(field)
            if val and isinstance(val, str) and val.strip():
                raw = val.strip()
                if raw in SECTOR_NORMALIZATION:
                    return SECTOR_NORMALIZATION[raw]
                lower_map = {k.lower(): v for k, v in SECTOR_NORMALIZATION.items()}
                hit = lower_map.get(raw.lower())
                if hit:
                    return hit
        return None
    except Exception:
        return None


# ---- RSI / ATR technical signal (mirrors scoring_script/scoring.py) ------
_EMPTY_TECHNICAL = {
    "rsi": None,
    "atr": None,
    "atr_pct": None,
    "pct_change": None,
    "close": None,
    "as_of": None,
}


def get_technical_signal(ticker: str, *, lookback_days: int = 30) -> Dict:
    """
    Fetch recent daily OHLCV from Polygon, resample to weekly bars (same
    'W-MON' convention as scoring_script/scoring.py), and compute:
      - RSI(3) on weekly closes
      - ATR(3) on weekly OHLC
      - ATR as a % of the latest close (handy for "X% weekly volatility"
        citations in the debate)
      - the latest week-over-week % price change

    Returns a dict of Nones (same shape) on any failure — missing API key,
    no data returned, not enough history for the rolling windows, etc. —
    so callers can degrade gracefully rather than crash mid-debate.
    """
    if not ticker or not POLYGON_API_KEY:
        return dict(_EMPTY_TECHNICAL)

    try:
        end = datetime.today()
        start = end - timedelta(days=lookback_days)
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
            f"{start:%Y-%m-%d}/{end:%Y-%m-%d}"
        )
        params = {"adjusted": "true", "sort": "asc", "limit": 120, "apiKey": POLYGON_API_KEY}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if not data.get("results"):
            return dict(_EMPTY_TECHNICAL)

        df = pd.DataFrame(data["results"])
        df["Date"] = pd.to_datetime(df["t"], unit="ms")
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].set_index("Date")

        weekly = (
            df.resample("W-MON")
            .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
            .dropna()
            .reset_index()
        )
        if weekly.empty:
            return dict(_EMPTY_TECHNICAL)

        weekly["pct_change"] = weekly["Close"].pct_change() * 100
        weekly["RSI"] = RSIIndicator(close=weekly["Close"], window=3).rsi()
        weekly["ATR"] = AverageTrueRange(
            high=weekly["High"], low=weekly["Low"], close=weekly["Close"], window=3
        ).average_true_range()
        weekly = weekly.dropna()

        if weekly.empty:
            return dict(_EMPTY_TECHNICAL)

        latest = weekly.iloc[-1]
        close = float(latest["Close"])
        atr = float(latest["ATR"])
        atr_pct = (atr / close * 100) if close else None

        return {
            "rsi": round(float(latest["RSI"]), 1),
            "atr": round(atr, 3),
            "atr_pct": round(atr_pct, 2) if atr_pct is not None else None,
            "pct_change": round(float(latest["pct_change"]), 2),
            "close": round(close, 2),
            "as_of": latest["Date"].date().isoformat(),
        }
    except Exception:
        return dict(_EMPTY_TECHNICAL)


# ---- quant model prediction (PARKED for v2 — not used in v1 packet) ------
# Mechanically works (loads + predicts with scikit-learn==1.5.2), but its
# predictive validity is unverified: model/README.md and model.txt contain
# no training/validation info, and the production pipeline in
# scoring_script/scoring.py feeds the model identical values for the
# _lag_1/_lag_2 slots of every feature (no real historical lags), which the
# model likely never saw during training — on top of an unused
# MinMaxScaler(-1,1) in scaler.pkl whose role is unclear. get_quant_signal()
# below is left working and tested, but get_evidence_packet() (next step)
# does NOT call it for v1. Revisit once the model has been retrained with
# real lags and the scaler question is resolved — at that point this slots
# back in as a fourth evidence type with no changes needed elsewhere.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MODEL_PATH = _PROJECT_ROOT / "model" / "model.pkl"

_MODEL = None
_MODEL_LOAD_ERROR: Optional[str] = None

# Exact column order the model expects — must match training.
_FEATURE_ORDER = [
    "Weekly_Sentiment_Score_lag_1",
    "Weekly_Sentiment_Score_lag_2",
    "Sentiment_Volatility_lag_1",
    "Sentiment_Volatility_lag_2",
    "Weekly_Price_Change_%_lag_1",
    "Weekly_Price_Change_%_lag_2",
    "RSI_lag_1",
    "RSI_lag_2",
    "ATR_lag_1",
    "ATR_lag_2",
]


def _load_model():
    """Lazily load and cache model.pkl. Returns None if loading fails."""
    global _MODEL, _MODEL_LOAD_ERROR
    if _MODEL is not None or _MODEL_LOAD_ERROR is not None:
        return _MODEL
    try:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL = pickle.load(f)
    except Exception as exc:
        _MODEL_LOAD_ERROR = str(exc)
    return _MODEL


def model_load_error() -> Optional[str]:
    """Returns the model-loading error message, if loading has been
    attempted and failed (e.g. a scikit-learn version mismatch). Returns
    None if loading succeeded or hasn't been attempted yet."""
    return _MODEL_LOAD_ERROR


def get_quant_signal(
    *,
    sentiment_score: Optional[float],
    sentiment_volatility: Optional[float],
    pct_change: Optional[float],
    rsi: Optional[float],
    atr: Optional[float],
) -> Optional[str]:
    """
    Returns "upward" or "downward" from the existing GradientBoosting model,
    or None if the model can't be loaded or any required input is missing
    (so callers can omit this citation rather than crash the debate).

    Mirrors scoring_script/scoring.py's prepare_scoring_data(): the same
    "current" sentiment/RSI/ATR/price-change values are duplicated into both
    the lag_1 and lag_2 slots, since the original pipeline doesn't have true
    historical lags either.
    """
    if any(v is None for v in (sentiment_score, sentiment_volatility, pct_change, rsi, atr)):
        return None

    model = _load_model()
    if model is None:
        return None

    row = {
        "Weekly_Sentiment_Score_lag_1": sentiment_score,
        "Weekly_Sentiment_Score_lag_2": sentiment_score,
        "Sentiment_Volatility_lag_1": sentiment_volatility,
        "Sentiment_Volatility_lag_2": sentiment_volatility,
        "Weekly_Price_Change_%_lag_1": pct_change,
        "Weekly_Price_Change_%_lag_2": pct_change,
        "RSI_lag_1": rsi,
        "RSI_lag_2": rsi,
        "ATR_lag_1": atr,
        "ATR_lag_2": atr,
    }
    try:
        X = pd.DataFrame([row])[_FEATURE_ORDER].to_numpy()
        pred = model.predict(X)[0]
        return "upward" if int(pred) == 1 else "downward"
    except Exception:
        return None


# ---- combined evidence packet ---------------------------------------------
def get_evidence_packet(ticker: str, company_name: str) -> Dict:
    """
    Assemble the full evidence packet for one ticker — the single object
    the Bull/Bear/Moderator prompts are built from.

    Makes several network calls (news fetches + Polygon). Call this ONCE
    per debate and reuse the returned dict for all ~10 exchanges, rather
    than re-fetching per turn.

    Returns:
    {
      "ticker": str,
      "company_name": str,
      "sector": str | None,
      "sentiment": {
          "avg_score": float, "std_score": float, "label": str,
          "n_articles": int,
          "top_headlines": [{"title", "provider", "url", "score"}, ...]
      },
      "sector_sentiment": {
          "avg_score": float, "std_score": float, "label": str, "n_articles": int
      } | None,
      "technical": {
          "rsi": float | None, "atr": float | None, "atr_pct": float | None,
          "pct_change": float | None, "as_of": str | None
      },
    }

    `sector_sentiment` is None if `sector` couldn't be resolved — a "Neutral,
    0 articles" placeholder would be misleading, so callers should simply
    treat sector evidence as optional/absent in that case.
    """
    sentiment = get_company_sentiment(company_name)
    sector = get_ticker_sector(ticker)
    sector_sentiment = get_sector_sentiment(sector) if sector else None
    technical = get_technical_signal(ticker)

    return {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "sentiment": sentiment,
        "sector_sentiment": sector_sentiment,
        "technical": technical,
    }
