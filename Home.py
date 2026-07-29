import streamlit as st
from urllib.parse import quote_plus


st.set_page_config(page_title="PulseShiftAI", page_icon="💹", layout="wide", initial_sidebar_state="expanded")


# Custom CSS (simplified cards, no backgrounds)
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    .block-container { padding-top: 2rem; padding-bottom: 4rem; }

    /* Centered content wrapper for analytic sections */
    .center-wrap { max-width: 980px; margin: 0 auto; }

    /* Section divider (between CTAs and analytics) */
    .section-divider {
        position: relative;
        height: 1px;
        background: linear-gradient(90deg, transparent, #444, transparent);
        margin: 2.25rem auto 1.5rem auto;
        max-width: 980px;
    }
    .section-divider:after {
        content: 'Dashboard';
        position: absolute;
        left: 50%;
        transform: translate(-50%, -60%);
        background: #0e0e0e;
        padding: 0 .6rem;
        color: #cfcfcf;
        font-size: .9rem;
        letter-spacing: .3px;
    }

    .banner {
        background-color: #141414;
        border-left: 5px solid #7FDBFF;
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 3rem;
        font-size: 1.1rem;
        color: #DDDDDD;
    }

    h1 {
        text-align: center;
        font-size: 3em;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    h3 {
        text-align: center;
        font-size: 1.3em;
        font-weight: 400;
        color: #cccccc;
        margin-bottom: 2.5rem;
    }

    .card-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.2rem;
        text-align: center;
    }

    .card-desc {
        color: #aaa;
        font-size: 0.9rem;
        margin-bottom: 1.2rem;
        text-align: center;
    }

    .stButton>button {
        background-color: #333;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        display: block;
        margin: 0 auto;
    }

    .stButton>button:hover {
        background-color: #555;
        box-shadow: 0 0 10px #fff2;
    }

    .info-section {
        background-color: #121212;
        border: 1px dashed #555;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: #cccccc;
        font-size: 0.95rem;
        margin-top: 3rem;
    }

    .info-section h4 {
        margin-top: 0;
        font-size: 1.2rem;
        color: #eeeeee;
    }

    .info-section ul {
        margin: 0;
        padding-left: 1.2rem;
    }

    .info-section ul li {
        margin: 0.4rem 0;
    }
    h2, h3 { text-align: center; }

    /* ----- Movers Cards (single source of truth) ----- */
    .movers-wrap { max-width: 980px; margin: 1rem auto 0; }
    .movers-section-title {
    text-align:center; font-weight:700; color:#d6d6d6; letter-spacing:.2px;
    margin:.5rem 0 .75rem 0;
    }
    .movers-grid {
    display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px;
    }
    @media (max-width: 860px) { .movers-grid { grid-template-columns: repeat(2, minmax(0,1fr)); } }
    @media (max-width: 560px) { .movers-grid { grid-template-columns: 1fr; } }

    a.mover-card {
    display:block; text-decoration:none; color:inherit;
    background:#171717; border:1px solid rgba(255,255,255,.06);
    border-radius:12px; padding:12px 14px;
    box-shadow:0 1px 2px rgba(0,0,0,.24), 0 8px 24px rgba(0,0,0,.14);
    transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }
    a.mover-card:hover { transform:translateY(-2px); box-shadow:0 6px 28px rgba(0,0,0,.22); border-color:rgba(255,255,255,.12); }
    a.mover-card:focus { outline:none; }
    a.mover-card:focus-visible { box-shadow:0 0 0 3px rgba(59,130,246,.45); }

    .mover-card.good { background:linear-gradient(180deg, rgba(16,78,50,.22), rgba(23,23,23,1)); }
    .mover-card.bad  { background:linear-gradient(180deg, rgba(95,23,23,.22),  rgba(23,23,23,1)); }

    .mover-topline { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .mover-name { font-weight:700; font-size:1rem; }
    .mover-score { font-variant-numeric:tabular-nums; font-weight:700; padding:4px 8px; border-radius:8px; background:rgba(255,255,255,.06); }
    .mover-tag { display:inline-flex; align-items:center; gap:6px; margin-top:8px; padding:4px 8px; border-radius:8px; font-size:.85rem; font-weight:600; opacity:.9; }
    .mover-tag.good { color:#30d17c; background:rgba(48,209,124,.12); }
    .mover-tag.bad  { color:#ff7676; background:rgba(255,118,118,.12); }
    .mover-subtle { color:#a7a7a7; font-size:.86rem; margin-top:4px; }
    /* ensure card text is always visible on dark gradient */
    .movers-grid a.mover-card * { color: #eaeaea !important; }
        
        
       

</style>
""", unsafe_allow_html=True)

# 🔹 Title
st.markdown("<h1>PulseShiftAI</h1>", unsafe_allow_html=True)
st.markdown("<h3>Navigate across predictive tools for financial insights, analysis, and forecasts</h3>", unsafe_allow_html=True)

# 🔸 Navigation Cards (no box wrapping)
col1, col2 = st.columns(2)
#, col3 

with col1:
    st.markdown('<div class="card-title">📈 Market Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-desc">Predict weekly stock index movements using sentiment.</div>', unsafe_allow_html=True)
    if st.button("Enter"):
        st.switch_page("pages/Market_Predictor.py")

with col2:
    st.markdown('<div class="card-title">🤖 Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-desc">Ask financial questions and get AI-driven responses in real time.</div>', unsafe_allow_html=True)
    if st.button("Chat"):
        st.switch_page("pages/ChatBot.py")


#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------
# --- visual separation between cards and analytics ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---- Config -----------------------------------------------------------------
from core.config import (
    SECTORS,                    # list of sector display names
    SECTOR_QUERIES,            # dict: sector -> Google News RSS query
    HOMEPAGE_FRESHNESS_DAYS,   # default days window
    #DEFAULT_SENTIMENT_ENGINE,  # "finbert" | "vader" | "auto"
)

freshness = HOMEPAGE_FRESHNESS_DAYS  # e.g., 3; no UI control anymore

# ---- Services ---------------------------------------------------------------
from services.news_fetcher import fetch_news
from services.aggregators import build_dashboard_payload
from services.summarizer import generate_market_wrap

# Open the Google News *web* page (not RSS) for a sector query
GOOGLE_NEWS_WEB = "https://news.google.com/search?q={query}&hl=en-US&gl=US&ceid=US:en"

def _news_url_for_sector(sector: str) -> str:
    q = SECTOR_QUERIES.get(sector, sector)  # fall back to the name if not found
    return GOOGLE_NEWS_WEB.format(query=quote_plus(q))


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
engine = "vader"   # hard-lock to VADER for now
@st.cache_data(ttl=900, show_spinner=False)
def _load_snapshot(freshness_days: int):
    """
    Fetch global + sector news, compute mood and sector table.

    Returns:
      payload: {"mood": {...}, "by_sector": pd.DataFrame}
      sector_articles: Dict[str, List[article]]
      market_articles: List[article]
    """
    # Broad market query (tweak as you like)
    market_query = '(markets OR "stock market" OR equities OR earnings OR macro) (stocks OR outlook)'
    market_articles = fetch_news(
        query=market_query,
        days=freshness_days,
        max_results=160,
    )

    # Per-sector articles using your configured queries
    sector_articles = {}
    for sector in SECTORS:
        q = SECTOR_QUERIES.get(sector, sector)
        sector_articles[sector] = fetch_news(
            query=q,
            days=freshness_days,
            max_results=80,
        )

    payload = build_dashboard_payload(
        market_articles=market_articles,
        sector_articles=sector_articles,
        engine=engine,
    )
    return payload, sector_articles, market_articles


def _render_mood_chip(mood: dict):
    label = mood.get("label", "Neutral")
    idx   = float(mood.get("avg_score", 0.0))
    n     = int(mood.get("n_articles", 0))

    color = {
        "Positive": "#22c55e",
        "Trending Positive": "#86efac",
        "Neutral": "#e5e7eb",
        "Trending Negative": "#fecaca",
        "Negative": "#ef4444",
    }.get(label, "#e5e7eb")

    st.markdown(
        f"""
        <div style="text-align:center; margin-top:0.5rem; margin-bottom:1rem;">
            <span style="
                display:inline-block;
                padding:8px 12px;
                border-radius:10px;
                background:{color};
                color:#111;
                font-weight:600;">
                Market Mood: {label} &nbsp;•&nbsp; Index {idx:+.2f} &nbsp;•&nbsp; {n} articles
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sector_heatmap(df: pd.DataFrame):
    if df.empty:
        st.info("No sector data available.")
        return
    show = df.copy()
    show["Sentiment Index"] = show["avg_score"].round(3)
    show = show[["sector", "Sentiment Index"]].set_index("sector").sort_index()

    fig = px.imshow(
        show[["Sentiment Index"]],
        text_auto=True,
        color_continuous_scale=["#ef4444", "#fca5a5", "#e5e7eb", "#86efac", "#22c55e"],
        aspect="auto",
        origin="lower",
    )
    fig.update_layout(
        margin=dict(l=40, r=20, t=30, b=20),
        coloraxis_colorbar=dict(title="Sentiment Scores Gradient"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_top_movers(df: pd.DataFrame, k: int = 3):
    """Render a centered strip of top and bottom K sectors with clickable chips."""
    if df is None or df.empty or "avg_score" not in df.columns:
        return

    d = df.copy()
    d["avg_score"] = pd.to_numeric(d["avg_score"], errors="coerce")
    d = d.dropna(subset=["avg_score"])
    if d.empty:
        return

    topk = list(d.nlargest(k, "avg_score")[["sector","avg_score"]].itertuples(index=False, name=None))
    botk = list(d.nsmallest(k, "avg_score")[["sector","avg_score"]].itertuples(index=False, name=None))

    def chip(name: str, val: float, klass: str) -> str:
        url = _news_url_for_sector(name)
        # open in new tab, safe attrs
        return (f'<a class="mover-chip {klass}" href="{url}" target="_blank" '
                f'rel="noopener noreferrer" title="Open latest headlines for {name}">'
                f'{name} ({val:+.2f})</a>')

    top_html = " ".join([chip(s, v, "good") for s, v in topk])
    bot_html = " ".join([chip(s, v, "bad") for s, v in botk])

    st.markdown(
        f"""
        <div class="movers-wrap">
            <span class="movers-label">Top movers</span>
            {top_html}
            <span class="movers-label" style="margin-top:.6rem;">Laggards</span>
            {bot_html}
        </div>
        """,
        unsafe_allow_html=True,
    )




# -----------------------------------------------------------------------------
# Controls
# -----------------------------------------------------------------------------
# Controls (centered)
# Action button (centered only)

# Controls (centered)
st.markdown('<div class="center-wrap">', unsafe_allow_html=True)

c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
with c1:
    freshness = st.selectbox(
        "Freshness window",
        options=[1, 3, 7, 14],
        index=[1, 3, 7, 14].index(HOMEPAGE_FRESHNESS_DAYS)
              if HOMEPAGE_FRESHNESS_DAYS in [1, 3, 7, 14] else 2,
        help="Search window for news (in days).",
    )
with c2:
    refresh = st.button("🔄 Refresh snapshot", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)


def _render_top_movers_cards(df: pd.DataFrame, k: int = 3):
    """Centered grid of clickable cards for Top movers and Laggards (no blanks)."""
    if df is None or df.empty or "avg_score" not in df.columns:
        return

    d = df.copy()
    d["avg_score"] = pd.to_numeric(d["avg_score"], errors="coerce")
    d = d.dropna(subset=["avg_score", "sector"])
    d = d[d["sector"].astype(str).str.len() > 0]
    if d.empty:
        return

    # keep k within available size
    k = max(0, min(k, len(d)))

    topk = list(d.nlargest(k, "avg_score")[["sector","avg_score"]].itertuples(index=False, name=None))
    botk = list(d.nsmallest(k, "avg_score")[["sector","avg_score"]].itertuples(index=False, name=None))

    def card_html(name: str, val: float, klass: str, tag: str) -> str:
        # guard against weird/empty names
        if not isinstance(name, str) or not name.strip():
            return ""
        url = _news_url_for_sector(name)
        arrow = "▲" if klass == "good" else "▼"
        # Single-line HTML (avoids Markdown/HTML whitespace edge-cases)
        return (
            f'<a class="mover-card {klass}" href="{url}" target="_blank" rel="noopener noreferrer" '
            f'aria-label="Open latest headlines for {name}">'
            f'<div class="mover-topline"><div class="mover-name">{name}</div>'
            f'<div class="mover-score">{val:+.2f}</div></div>'
            f'<div class="mover-tag {klass}">{arrow} {tag}</div>'
            f'<div class="mover-subtle">Open Google News →</div>'
            f'</a>'
        )

    # Build without newlines to prevent accidental empty nodes
    top_cards = "".join([card_html(s, v, "good", "Top mover") for s, v in topk if isinstance(s, str) and s.strip()])
    bot_cards = "".join([card_html(s, v, "bad",  "Laggard")  for s, v in botk if isinstance(s, str) and s.strip()])

    # If for some reason we generated nothing, bail quietly (prevents empty boxes)
    if not top_cards and not bot_cards:
        return

    st.markdown(
        (
            '<div class="movers-wrap">'
            '<div class="movers-section-title">Top movers</div>'
            f'<div class="movers-grid">{top_cards}</div>'
            '<div class="movers-section-title" style="margin-top:1rem;">Laggards</div>'
            f'<div class="movers-grid">{bot_cards}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )




# -----------------------------------------------------------------------------
# Load + compute
# -----------------------------------------------------------------------------
if refresh:
    st.cache_data.clear()

payload, sector_articles, market_articles = _load_snapshot(freshness)
mood = payload["mood"]
by_sector = payload["by_sector"]

if not by_sector.empty:
    by_sector["avg_score"] = pd.to_numeric(by_sector["avg_score"], errors="coerce")
    by_sector.dropna(subset=["avg_score"], inplace=True)
    by_sector["sector"] = pd.Categorical(by_sector["sector"], categories=SECTORS, ordered=True)
    by_sector.sort_values("sector", inplace=True)


# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------

st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
st.subheader("Market Mood", anchor=None)
st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
_render_mood_chip(mood)
st.markdown('</div>', unsafe_allow_html=True)


st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
st.markdown("### Sector Sentiment Heatmap", unsafe_allow_html=True)
# (heatmap will render inside; see next patch)
_render_sector_heatmap(by_sector)
_render_top_movers_cards(by_sector)

st.markdown('</div>', unsafe_allow_html=True)

# Action buttons
st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
gen_wrap = st.button("📝 Generate Market Wrap", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


if gen_wrap:
    with st.spinner("Compiling market wrap..."):
        wrap = generate_market_wrap(
            mood={**mood, "by_sector": by_sector},
            headlines_by_sector=sector_articles,
            title="Weekly Market Wrap",
            points=4,
        )
    st.markdown("---")
    st.subheader("Market Wrap")
    st.markdown(wrap["markdown"])




#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------

#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------




# 🔻 Bottom Info Section (Reworded and Bulletified)
st.markdown("""
<div class="info-section">
    <h4>🔍 What is PulseShiftAI?</h4>
    <p>PulseShiftAI is your digital ally in navigating volatile financial environments. Whether you're an analyst or a trader, these tools enable:</p>
    <ul>
        <li>📊 Market sentiment integration for weekly forecasts</li>
        <li>🌍 FX and macro intelligence for treasury teams</li>
        <li>💬 Natural language interaction with your own data through the chatbot</li>
    </ul>
    <p><em>We're here to give your decisions context, foresight, and confidence.</em></p>
</div>
""", unsafe_allow_html=True)

