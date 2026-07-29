# debate_engine/config.py
"""
Standalone configuration for the debate engine.

Deliberately decoupled from core/config.py, which loads secrets via
st.secrets and therefore expects to run inside a Streamlit process. The
debate engine needs to run as a plain Python script (for development/testing)
and later inside FastAPI — neither of which is a Streamlit runtime — so it
reads API keys from environment variables / a local .env file instead.

To use locally:
  1. `pip install python-dotenv` (already added to requirements.txt)
  2. Create a `.env` file in the project root (same folder as Home.py) with:
       OPENAI_API_KEY=sk-...
       POLYGON_API_KEY=...
     (.env should be in .gitignore — never commit real keys)

NOTE: SECTOR_QUERIES, SECTOR_NORMALIZATION and THRESHOLDS are intentionally
duplicated (in trimmed form) from core/config.py rather than imported, so
that importing this module never triggers `import streamlit`. If
core/config.py's sector queries or thresholds change, mirror the change here.
This duplication is a known piece of tech debt to clean up once the whole
app moves off Streamlit.
"""

from __future__ import annotations
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed yet — env vars set another way still work
    pass

# ---- API keys -----------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

OPENAI_MODEL_DEBATER = os.getenv("OPENAI_MODEL_DEBATER", "gpt-4o-mini")
OPENAI_MODEL_MODERATOR = os.getenv("OPENAI_MODEL_MODERATOR", "gpt-4o-mini")

# ---- News freshness / limits --------------------------------------------
FRESHNESS_DAYS = 3
MAX_RESULTS_PER_QUERY = 60

# ---- Sentiment thresholds (mirrors core/config.py THRESHOLDS) -----------
THRESHOLDS = {
    "positive_strong": 0.35,
    "positive_mild": 0.15,
    "neutral": 0.0,
    "negative_mild": -0.15,
    "negative_strong": -0.35,
}

SENTIMENT_LABELS = [
    "Negative",
    "Trending Negative",
    "Neutral",
    "Trending Positive",
    "Positive",
]

# ---- Sector news queries (mirrors core/config.py SECTOR_QUERIES) --------
SECTOR_QUERIES = {
    "Communication Services": '("communication services" OR telecom OR media OR streaming) (earnings OR guidance OR outlook OR subscribers)',
    "Consumer Discretionary": '("consumer discretionary" OR retail OR autos OR apparel) (sales OR earnings OR outlook OR demand)',
    "Consumer Staples": '("consumer staples" OR beverages OR household OR packaged foods) (sales OR earnings OR inflation OR pricing)',
    "Energy": '(energy OR oil OR gas OR LNG OR refinery) (OPEC OR output OR prices OR inventories OR earnings)',
    "Financials": '(banks OR insurers OR "asset managers" OR brokers) (NIM OR credit OR provisions OR earnings OR guidance)',
    "Healthcare": '(healthcare OR pharma OR biotech OR medtech) (trial OR FDA OR EMA OR earnings OR guidance)',
    "Industrials": '(industrials OR machinery OR transport OR aerospace) (orders OR backlog OR capex OR earnings)',
    "Materials": '(materials OR chemicals OR metals OR mining) (prices OR demand OR China OR earnings)',
    "Real Estate": '("real estate" OR REIT OR housing) (rents OR occupancy OR mortgage OR "cap rate" OR earnings)',
    "Technology": '("information technology" OR semiconductors OR software OR hardware) (earnings OR AI OR guidance)',
    "Utilities": '(utilities OR electricity OR grid OR power) (tariffs OR capacity OR outage OR earnings)',
}

# ---- Sector normalization (mirrors core/config.py SECTOR_NORMALIZATION) -
# Maps raw sector/industry strings from Polygon into the canonical keys
# used by SECTOR_QUERIES above.
SECTOR_NORMALIZATION = {
    "Information Technology": "Technology",
    "Technology": "Technology",
    "Tech": "Technology",

    "Financials": "Financials",
    "Banks": "Financials",
    "Insurance": "Financials",

    "Health Care": "Healthcare",
    "Healthcare": "Healthcare",
    "Biotechnology": "Healthcare",
    "Pharmaceuticals": "Healthcare",

    "Energy": "Energy",
    "Oil & Gas": "Energy",
    "Renewables": "Energy",

    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Retail": "Consumer Discretionary",
    "Ecommerce": "Consumer Discretionary",
    "Apparel": "Consumer Discretionary",
    "Autos": "Consumer Discretionary",
    "Food": "Consumer Staples",
    "Beverages": "Consumer Staples",
    "Household": "Consumer Staples",
    "Consumer": "Consumer Discretionary",

    "Industrials": "Industrials",
    "Manufacturing": "Industrials",
    "Aerospace": "Industrials",

    "Utilities": "Utilities",
    "Power": "Utilities",
    "Electric": "Utilities",

    "Materials": "Materials",
    "Chemicals": "Materials",
    "Metals": "Materials",
    "Mining": "Materials",

    "Real Estate": "Real Estate",
    "REIT": "Real Estate",
    "Property": "Real Estate",

    "Telecommunications": "Communication Services",
    "Telecom": "Communication Services",
    "Media": "Communication Services",
    "5G": "Communication Services",
}
