import React, { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  TrendingUp, TrendingDown, Minus, ArrowLeft, Scale, Newspaper,
  Activity, Cpu, BarChart3, Check, ChevronRight, Gauge, Play, RotateCcw, FastForward,
} from "lucide-react";

/* ============================================================
   STYLES
   ============================================================ */
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap');

.psai {
  --bg: #0A0D12;
  --panel: #12161F;
  --panel-2: #181D29;
  --border: #232B3A;
  --text: #E7ECF3;
  --text-dim: #8B96A8;
  --text-faint: #5A6577;
  --accent: #4F8CFF;
  --accent-soft: rgba(79,140,255,0.12);
  --bull: #34D399;
  --bull-soft: rgba(52,211,153,0.12);
  --bear: #F25F5C;
  --bear-soft: rgba(242,95,92,0.12);
  --gold: #F2C94C;
  --gold-soft: rgba(242,201,76,0.12);

  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100%;
  width: 100%;
  box-sizing: border-box;
  -webkit-font-smoothing: antialiased;
}
.psai * { box-sizing: border-box; }
.psai h1, .psai h2, .psai h3, .psai .display {
  font-family: 'Space Grotesk', sans-serif;
}
.psai .mono { font-family: 'IBM Plex Mono', monospace; }

.psai button { font-family: inherit; cursor: pointer; }
.psai button:focus-visible, .psai a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* ---------- shell / nav ---------- */
.shell { max-width: 1180px; margin: 0 auto; padding: 0 20px 64px; }
.nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 22px 0 18px; border-bottom: 1px solid var(--border);
  margin-bottom: 28px; flex-wrap: wrap; gap: 14px;
}
.brand { display: flex; align-items: center; gap: 10px; }
.brand-mark {
  width: 30px; height: 30px; border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), var(--bull));
  display: flex; align-items: center; justify-content: center; color: #06080C;
}
.brand-text { font-size: 1.15rem; font-weight: 700; letter-spacing: 0.01em; }
.brand-text span { color: var(--text-dim); font-weight: 500; }
.nav-tabs { display: flex; gap: 6px; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 4px; }
.nav-tab {
  border: none; background: transparent; color: var(--text-dim);
  padding: 8px 16px; border-radius: 8px; font-size: 0.88rem; font-weight: 600;
  transition: background 0.15s, color 0.15s;
}
.nav-tab.active { background: var(--panel-2); color: var(--text); }
.nav-tab:hover:not(.active) { color: var(--text); }

/* ---------- mood banner / pulse header ---------- */
.mood-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
  border: 1px solid var(--border); border-radius: 14px;
  padding: 22px 24px; margin-bottom: 22px;
}
.pulse-svg { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0.35; }
.pulse-path { stroke-dasharray: 6 12; animation: pulse-flow 3.2s linear infinite; }
@keyframes pulse-flow { to { stroke-dashoffset: -180; } }
.mood-row { position: relative; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.mood-label { font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-faint); margin-bottom: 6px; }
.mood-value { font-size: 1.6rem; font-weight: 700; display: flex; align-items: center; gap: 10px; }
.mood-chip { font-size: 0.78rem; padding: 4px 10px; border-radius: 999px; font-weight: 600; }
.mood-meta { color: var(--text-dim); font-size: 0.85rem; }

/* ---------- sector strip ---------- */
.sector-strip-wrap { margin-bottom: 28px; }
.section-eyebrow {
  font-size: 0.74rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--text-faint); margin-bottom: 10px; font-weight: 600;
}
.sector-strip { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
.sector-chip {
  flex: 0 0 auto; display: flex; flex-direction: column; gap: 4px;
  padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--panel); min-width: 132px;
}
.sector-chip .name { font-size: 0.78rem; color: var(--text-dim); white-space: nowrap; }
.sector-chip .val { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.92rem; }

/* ---------- watchlist ---------- */
.watchlist-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 8px; }
.watch-card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
  transition: border-color 0.15s, transform 0.15s;
}
.watch-card:hover { border-color: rgba(79,140,255,0.35); transform: translateY(-2px); }
.watch-head { display: flex; align-items: flex-start; justify-content: space-between; }
.watch-symbol { font-size: 1.05rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }
.watch-name { font-size: 0.74rem; color: var(--text-faint); margin-top: 1px; }
.watch-price { text-align: right; }
.watch-price .px { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 1rem; }
.watch-change { display: flex; align-items: center; justify-content: flex-end; gap: 3px; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; margin-top: 2px; }
.sentiment-badge {
  display: inline-flex; align-items: center; gap: 6px; align-self: flex-start;
  padding: 4px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 600;
}
.sentiment-dot { width: 7px; height: 7px; border-radius: 50%; }
.watch-stats { display: flex; gap: 16px; font-size: 0.78rem; color: var(--text-dim); font-family: 'IBM Plex Mono', monospace; }
.watch-stats b { color: var(--text); font-weight: 600; }
.debate-btn {
  margin-top: 4px; border: 1px solid var(--border); background: var(--panel-2);
  color: var(--text); border-radius: 9px; padding: 9px 12px; font-size: 0.84rem;
  font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: border-color 0.15s, color 0.15s;
}
.debate-btn:hover { border-color: var(--accent); color: var(--accent); }

/* ---------- debate page ---------- */
.back-link {
  display: inline-flex; align-items: center; gap: 6px; color: var(--text-dim);
  background: none; border: none; font-size: 0.86rem; font-weight: 600; padding: 0; margin-bottom: 16px;
}
.back-link:hover { color: var(--text); }
.debate-header {
  display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  margin-bottom: 18px;
}
.debate-title { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.debate-title .sym { font-size: 1.7rem; font-weight: 700; }
.debate-title .nm { color: var(--text-dim); font-size: 0.95rem; }
.debate-price-block { text-align: right; }
.debate-price-block .px { font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; font-weight: 700; }

.debate-layout { display: grid; grid-template-columns: 1.55fr 1fr; gap: 18px; }

.transcript-card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
  max-height: 620px; overflow-y: auto;
}
.transcript-empty { color: var(--text-faint); font-size: 0.9rem; padding: 40px 8px; text-align: center; }

.turn {
  border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px;
  background: var(--panel-2); animation: turn-in 0.45s ease both;
}
@keyframes turn-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.turn.bull { border-left: 3px solid var(--bull); }
.turn.bear { border-left: 3px solid var(--bear); }
.turn.latest { animation: turn-in 0.45s ease both, glow-pulse 1.7s ease-in-out infinite; }
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 0 1px var(--glow), 0 0 12px -6px var(--glow); }
  50% { box-shadow: 0 0 0 1px var(--glow), 0 0 26px -2px var(--glow); }
}
.turn-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.turn-who { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
.turn-who.bull { color: var(--bull); }
.turn-who.bear { color: var(--bear); }
.turn-round { font-size: 0.72rem; color: var(--text-faint); font-family: 'IBM Plex Mono', monospace; }
.turn-text { font-size: 0.9rem; line-height: 1.5; color: var(--text); margin-bottom: 8px; }
.turn-citation {
  display: flex; align-items: center; gap: 8px; font-size: 0.76rem;
  background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  padding: 7px 10px; color: var(--text-dim);
}
.turn-citation b { color: var(--text); font-family: 'IBM Plex Mono', monospace; font-weight: 600; }

.moderator-card {
  border: 1px solid var(--gold); border-radius: 12px; padding: 14px 16px;
  background: var(--gold-soft); animation: turn-in 0.5s ease both;
}
.moderator-head { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: var(--gold); margin-bottom: 8px; }
.moderator-text { font-size: 0.9rem; line-height: 1.55; color: var(--text); margin-bottom: 12px; }

/* ---------- sidebar ---------- */
.sidebar { display: flex; flex-direction: column; gap: 14px; }
.side-card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 16px; }
.side-card h3 { font-size: 0.8rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-faint); margin: 0 0 12px; font-weight: 600; }
.progress-track { height: 8px; border-radius: 999px; background: var(--bg); border: 1px solid var(--border); overflow: hidden; margin-bottom: 8px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--bull)); transition: width 0.5s ease; }
.progress-label { display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-dim); font-family: 'IBM Plex Mono', monospace; }

.meter-row { margin-bottom: 12px; }
.meter-row:last-child { margin-bottom: 0; }
.meter-label { display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px; }
.meter-label .name { font-weight: 600; }
.meter-label .val { font-family: 'IBM Plex Mono', monospace; }
.meter-track { height: 8px; border-radius: 999px; background: var(--bg); border: 1px solid var(--border); overflow: hidden; }
.meter-fill { height: 100%; transition: width 0.6s ease; }
.meter-fill.bull { background: var(--bull); }
.meter-fill.bear { background: var(--bear); }

.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.stat-box { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px; }
.stat-box .lbl { font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
.stat-box .v { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.95rem; }

.controls { display: flex; gap: 8px; flex-wrap: wrap; }
.btn {
  border-radius: 10px; border: 1px solid var(--border); background: var(--panel-2);
  color: var(--text); padding: 10px 16px; font-size: 0.85rem; font-weight: 600;
  display: flex; align-items: center; gap: 6px; transition: border-color 0.15s, background 0.15s, opacity 0.15s;
}
.btn:hover { border-color: var(--accent); }
.btn:disabled { opacity: 0.4; cursor: default; }
.btn-primary { background: linear-gradient(135deg, var(--accent), #6E6BFF); border: none; color: #fff; }
.btn-primary:hover { opacity: 0.92; border: none; }
.btn-buy { background: var(--bull); border: none; color: #06231A; }
.btn-buy:hover { opacity: 0.9; border: none; }
.btn-sell { background: var(--bear); border: none; color: #2A0707; }
.btn-sell:hover { opacity: 0.9; border: none; }
.btn-full { width: 100%; justify-content: center; }

/* ---------- verdict page ---------- */
.verdict-grid { display: grid; grid-template-columns: 1.1fr 1fr; gap: 18px; align-items: start; }
.decision-card {
  border-radius: 16px; padding: 26px; border: 1px solid var(--border);
}
.decision-card.buy { background: linear-gradient(160deg, var(--bull-soft), var(--panel)); border-color: rgba(52,211,153,0.35); }
.decision-card.sell { background: linear-gradient(160deg, var(--bear-soft), var(--panel)); border-color: rgba(242,95,92,0.35); }
.decision-action { font-size: 2.4rem; font-weight: 700; letter-spacing: 0.03em; display: flex; align-items: center; gap: 12px; }
.decision-action.buy { color: var(--bull); }
.decision-action.sell { color: var(--bear); }
.decision-sub { color: var(--text-dim); font-size: 0.9rem; margin: 6px 0 18px; }
.confidence-row { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.confidence-ring { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 700; }
.confidence-track { flex: 1; height: 10px; border-radius: 999px; background: var(--bg); border: 1px solid var(--border); overflow: hidden; }
.confidence-fill { height: 100%; }
.confidence-fill.buy { background: var(--bull); }
.confidence-fill.sell { background: var(--bear); }
.sizing-box {
  background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
  padding: 12px 14px; margin-bottom: 18px; font-size: 0.88rem; color: var(--text-dim);
}
.sizing-box b { color: var(--text); }
.reasoning-list { list-style: none; padding: 0; margin: 0 0 20px; display: flex; flex-direction: column; gap: 10px; }
.reasoning-list li { display: flex; gap: 10px; font-size: 0.88rem; line-height: 1.5; color: var(--text); }
.reasoning-list li svg { flex-shrink: 0; margin-top: 2px; }

.analytics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 8px; }
.analytic-chip { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }
.analytic-chip .lbl { font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.analytic-chip .v { font-family: 'IBM Plex Mono', monospace; font-weight: 700; font-size: 1.05rem; }
.analytic-note { font-size: 0.74rem; color: var(--text-faint); margin-top: 10px; line-height: 1.4; }

/* ---------- portfolio ---------- */
.portfolio-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
.portfolio-table th, .portfolio-table td { text-align: left; padding: 11px 12px; border-bottom: 1px solid var(--border); }
.portfolio-table th { color: var(--text-faint); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.portfolio-table td.num, .portfolio-table th.num { text-align: right; font-family: 'IBM Plex Mono', monospace; }
.portfolio-empty { padding: 36px 16px; text-align: center; color: var(--text-faint); font-size: 0.9rem; }

/* ---------- toast ---------- */
.toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: var(--bull); color: #06231A; padding: 12px 20px; border-radius: 10px;
  font-weight: 600; font-size: 0.88rem; display: flex; align-items: center; gap: 8px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.4); animation: toast-in 0.35s ease both; z-index: 50;
}
@keyframes toast-in { from { opacity: 0; transform: translate(-50%, 12px); } to { opacity: 1; transform: translate(-50%, 0); } }

/* ---------- responsive ---------- */
@media (max-width: 900px) {
  .watchlist-grid { grid-template-columns: repeat(2, 1fr); }
  .debate-layout { grid-template-columns: 1fr; }
  .verdict-grid { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .watchlist-grid { grid-template-columns: 1fr; }
  .nav { flex-direction: column; align-items: flex-start; }
  .analytics-grid { grid-template-columns: 1fr 1fr; }
  .debate-title .sym { font-size: 1.35rem; }
}
`;

/* ============================================================
   MOCK DATA
   ============================================================ */
const SECTOR_MOOD = [
  { sector: "Technology", score: 0.27 },
  { sector: "Financials", score: 0.18 },
  { sector: "Consumer Discretionary", score: 0.15 },
  { sector: "Industrials", score: 0.06 },
  { sector: "Communication Services", score: 0.08 },
  { sector: "Utilities", score: 0.02 },
  { sector: "Healthcare", score: -0.03 },
  { sector: "Consumer Staples", score: -0.05 },
  { sector: "Materials", score: -0.09 },
  { sector: "Real Estate", score: -0.14 },
  { sector: "Energy", score: -0.22 },
];

const WATCHLIST = [
  { symbol: "NVDA", name: "NVIDIA Corporation", price: 128.40, change: 1.24, sentimentScore: 0.31, sentimentLabel: "Trending Positive", rsi: 64, atrPct: 2.9, sector: "Technology", sectorScore: 0.27 },
  { symbol: "AAPL", name: "Apple Inc.", price: 211.05, change: -0.42, sentimentScore: 0.04, sentimentLabel: "Neutral", rsi: 49, atrPct: 1.4, sector: "Technology", sectorScore: 0.27 },
  { symbol: "JPM", name: "JPMorgan Chase & Co.", price: 241.80, change: 0.63, sentimentScore: 0.18, sentimentLabel: "Trending Positive", rsi: 55, atrPct: 1.8, sector: "Financials", sectorScore: 0.18 },
  { symbol: "XOM", name: "Exxon Mobil Corp.", price: 118.22, change: -1.83, sentimentScore: -0.21, sentimentLabel: "Trending Negative", rsi: 71, atrPct: 2.6, sector: "Energy", sectorScore: -0.22 },
  { symbol: "TSLA", name: "Tesla, Inc.", price: 312.55, change: 2.91, sentimentScore: 0.41, sentimentLabel: "Positive", rsi: 68, atrPct: 4.7, sector: "Consumer Discretionary", sectorScore: 0.15 },
  { symbol: "PFE", name: "Pfizer Inc.", price: 27.85, change: -0.18, sentimentScore: -0.02, sentimentLabel: "Neutral", rsi: 44, atrPct: 1.9, sector: "Healthcare", sectorScore: -0.03 },
];

const MARKET_MOOD = { label: "Trending Positive", score: 0.09, articles: 482 };

const fmtScore = (v) => (v >= 0 ? "+" : "") + v.toFixed(2);

/* ---- bespoke, hand-written debate for NVDA (the "wow" demo) ---- */
const NVDA_DEBATE = {
  company: "NVIDIA Corporation",
  symbol: "NVDA",
  price: 128.40,
  change: 1.24,
  turns: [
    { speaker: "bull", roundLabel: 1, text: "Hyperscaler capex commentary this week points to accelerating data-center GPU demand into next quarter, and sentiment across 41 tracked headlines on NVDA sits at +0.31, solidly Trending Positive.", citationType: "sentiment", citationLabel: "FinBERT/VADER sentiment", citationValue: "+0.31 \u00b7 Trending Positive (41 articles, 3d window)" },
    { speaker: "bear", roundLabel: 1, text: "Momentum looks stretched \u2014 RSI is at 64 and the 14-day ATR implies 2.9% weekly volatility, which is elevated relative to NVDA's 6-month average. A pullback risk exists before any further re-rating.", citationType: "technical", citationLabel: "Technical signal (Polygon, 14d)", citationValue: "RSI 64 \u00b7 ATR-implied weekly volatility 2.9%" },
    { speaker: "bull", roundLabel: 2, text: "Even granting the volatility point, the quant model's weekly classifier is leaning upward on the back of a positive lagged price-change and an improving sentiment trend over the past two weeks.", citationType: "model", citationLabel: "Quant signal (GradientBoosting)", citationValue: "Predicted direction: Upward (lag-1 / lag-2 features)" },
    { speaker: "bear", roundLabel: 2, text: "One headline from this week flags a competitor's custom silicon roadmap gaining traction with a major cloud provider \u2014 that's a structural threat narrative the sentiment average may be underweighting.", citationType: "headline", citationLabel: "Headline (2d ago)", citationValue: "\"Cloud provider expands custom AI chip programme, eyes inference workloads\"" },
    { speaker: "bull", roundLabel: 3, text: "That headline is about inference workloads specifically \u2014 NVDA's near-term guidance commentary continues to emphasize training-cluster backlog, which is the segment driving the current earnings cycle. The Technology sector mood is the strongest of all 11 tracked sectors at +0.27.", citationType: "sector", citationLabel: "Sector mood (Technology)", citationValue: "+0.27 \u00b7 strongest of 11 sectors" },
    { speaker: "bear", roundLabel: 3, text: "Strong sector mood can also mean the trade is crowded \u2014 when an entire sector posts the top sentiment reading, positioning risk into any disappointment is higher than usual.", citationType: "risk", citationLabel: "Positioning note", citationValue: "Sector sentiment dispersion: low (crowded long)" },
    { speaker: "bull", roundLabel: 4, text: "Granted \u2014 but the standard deviation of NVDA-specific sentiment across the 41 articles is low at 0.09, meaning the positive read is consistent rather than driven by one or two outlier pieces. That's a more durable signal than a single headline risk.", citationType: "sentiment", citationLabel: "Sentiment dispersion", citationValue: "std 0.09 across 41 articles (low dispersion)" },
    { speaker: "bear", roundLabel: 4, text: "Fair \u2014 I'll soften that objection. My main remaining concern is purely technical: at RSI 64 heading toward 70, the risk/reward on a fresh entry this week is asymmetric versus waiting for a pullback toward the 50-level.", citationType: "technical", citationLabel: "Entry timing", citationValue: "RSI approaching overbought threshold (70)" },
    { speaker: "bull", roundLabel: 5, text: "Acknowledged on timing \u2014 but the question on the table is direction over the next week, not optimal entry price, and on that the weight of evidence (model, sentiment, sector) points the same way.", citationType: "synthesis", citationLabel: "Weight of evidence", citationValue: "3 of 3 independent signals aligned bullish" },
    { speaker: "bear", roundLabel: 5, text: "Agreed \u2014 I don't have a fundamentally bearish case left, only a tactical timing caveat. I'll concede the directional call.", citationType: "concession", citationLabel: "Bear concession", citationValue: "No residual bearish catalyst identified" },
  ],
  conviction: [
    { turn: 0, bull: 50, bear: 50 },
    { turn: 1, bull: 56, bear: 50 },
    { turn: 2, bull: 56, bear: 55 },
    { turn: 3, bull: 61, bear: 55 },
    { turn: 4, bull: 61, bear: 59 },
    { turn: 5, bull: 66, bear: 59 },
    { turn: 6, bull: 66, bear: 62 },
    { turn: 7, bull: 70, bear: 62 },
    { turn: 8, bull: 70, bear: 64 },
    { turn: 9, bull: 73, bear: 64 },
    { turn: 10, bull: 73, bear: 64 },
  ],
  verdict: {
    action: "BUY",
    confidence: 74,
    sizing: "2.0% of book \u2014 staged entry (1.0% now, 1.0% on a pullback toward RSI 50)",
    reasoning: [
      "All three independent signal families \u2014 news sentiment (+0.31, low dispersion), sector momentum (Technology +0.27, strongest of 11), and the quant directional model \u2014 point the same direction.",
      "The Bear case shifted from a structural threat (competitor silicon) to a tactical timing caveat (RSI near 70), and was explicitly conceded by exchange 10.",
      "Elevated short-term volatility (ATR-implied 2.9% weekly) supports a staged entry rather than a single full-size purchase.",
    ],
    metrics: { cts: "0.81", pds: "0.64", entropy: "1.92 bits", bui: "0.58" },
  },
};

/* ---- generic debate generator for the rest of the watchlist ---- */
function generateDebate(t) {
  const tilt = t.sentimentScore;
  const rsiHot = t.rsi > 65 ? 2 : t.rsi < 35 ? -1 : 0;

  const bullDeltas = [6, 5, 5, 4, 3].map((d) => Math.max(1, Math.round(d + tilt * 8)));
  const bearDeltas = [5, 4, 3, 2, 2].map((d) => Math.max(1, Math.round(d - tilt * 8 + rsiHot)));

  const bullTexts = [
    `Recent coverage of ${t.name} skews ${t.sentimentLabel.toLowerCase()}, with an aggregate sentiment score of ${fmtScore(t.sentimentScore)} across tracked headlines this week.`,
    `The quant model's weekly classifier, built on lagged price-change, RSI, and ATR features, is currently leaning toward an upward read for ${t.symbol}.`,
    `${t.sector} sector mood reads ${fmtScore(t.sectorScore)}, which provides a ${t.sectorScore >= 0 ? "supportive" : "mixed"} backdrop for ${t.symbol}.`,
    `The ${t.sentimentLabel.toLowerCase()} sentiment read isn't being driven by a single outlier story \u2014 dispersion across the article set is low to moderate.`,
    `Taken together, none of the independent signal families \u2014 sentiment, sector momentum, or the quant model \u2014 are pointing in a contradictory direction.`,
  ];
  const bearTexts = [
    `RSI for ${t.symbol} sits at ${t.rsi}, with ATR-implied weekly volatility around ${t.atrPct}% \u2014 that's worth weighing against any new-entry conviction.`,
    `${t.sector} sector mood at ${fmtScore(t.sectorScore)} is ${t.sectorScore > 0.15 ? "strong enough that positioning could already be crowded" : "not a decisive tailwind either way"}.`,
    `A ${t.sentimentLabel.toLowerCase()} sentiment score of ${fmtScore(t.sentimentScore)} is close enough to neutral that I wouldn't lean on it heavily in isolation.`,
    `Volatility-adjusted, the entry-timing risk given RSI ${t.rsi} is the main thing keeping me cautious on the size of any near-term move.`,
    `I don't have a strong residual case against ${t.symbol} beyond that timing point \u2014 I'll concede the broader direction.`,
  ];
  const bullCitations = [
    { citationType: "sentiment", citationLabel: "News sentiment (FinBERT/VADER blend)", citationValue: `${fmtScore(t.sentimentScore)} \u00b7 ${t.sentimentLabel}` },
    { citationType: "model", citationLabel: "Quant signal (GradientBoosting)", citationValue: "Predicted direction: Upward-leaning (lag-1 / lag-2 features)" },
    { citationType: "sector", citationLabel: `Sector mood (${t.sector})`, citationValue: fmtScore(t.sectorScore) },
    { citationType: "sentiment", citationLabel: "Sentiment dispersion", citationValue: "Low\u2013moderate across tracked headlines" },
    { citationType: "synthesis", citationLabel: "Cross-signal synthesis", citationValue: "Sentiment, sector, and model signals broadly aligned" },
  ];
  const bearCitations = [
    { citationType: "technical", citationLabel: "Technical signal (Polygon, 14d)", citationValue: `RSI ${t.rsi} \u00b7 ATR-implied weekly volatility ${t.atrPct}%` },
    { citationType: "sector", citationLabel: `Sector mood (${t.sector})`, citationValue: `${fmtScore(t.sectorScore)} \u2014 ${t.sectorScore > 0.15 ? "crowded positioning risk" : "limited tailwind"}` },
    { citationType: "sentiment", citationLabel: "Sentiment strength", citationValue: `${t.sentimentLabel} reading close to neutral band` },
    { citationType: "technical", citationLabel: "Entry timing", citationValue: `RSI ${t.rsi} \u2014 ${t.rsi > 65 ? "approaching overbought" : "no immediate timing edge"}` },
    { citationType: "concession", citationLabel: "Bear concession", citationValue: "No additional bearish catalyst identified" },
  ];

  const turns = [];
  const conviction = [{ turn: 0, bull: 50, bear: 50 }];
  let bull = 50, bear = 50;

  for (let i = 0; i < 5; i++) {
    bull = Math.min(95, bull + bullDeltas[i]);
    turns.push({ speaker: "bull", roundLabel: i + 1, text: bullTexts[i], ...bullCitations[i] });
    conviction.push({ turn: turns.length, bull, bear });

    bear = Math.min(95, Math.max(20, bear + bearDeltas[i]));
    turns.push({ speaker: "bear", roundLabel: i + 1, text: bearTexts[i], ...bearCitations[i] });
    conviction.push({ turn: turns.length, bull, bear });
  }

  const action = bull >= bear ? "BUY" : "SELL";
  const diff = Math.abs(bull - bear);
  const confidence = Math.min(90, Math.max(54, 50 + diff));

  const reasoning =
    action === "BUY"
      ? [
          `Sentiment (${fmtScore(t.sentimentScore)} \u00b7 ${t.sentimentLabel}) and ${t.sector} sector mood (${fmtScore(t.sectorScore)}) are not contradicting the quant model's directional read.`,
          `The Bear case narrowed to a technical entry-timing concern (RSI ${t.rsi}) and was conceded by exchange 10.`,
          `ATR-implied weekly volatility of ${t.atrPct}% supports a measured position size rather than a full-size entry.`,
        ]
      : [
          `${t.sector} sector mood (${fmtScore(t.sectorScore)}) and a ${t.sentimentLabel.toLowerCase()} sentiment read (${fmtScore(t.sentimentScore)}) gave the Bull case little to build on.`,
          `RSI ${t.rsi} with ${t.atrPct}% ATR-implied weekly volatility reinforced the Bear's technical objection through to the end of the debate.`,
          `The Bull case could not assemble three aligned signals \u2014 the weight of evidence favours reducing exposure.`,
        ];

  const sizing =
    action === "BUY"
      ? `${(confidence / 40).toFixed(1)}% of book \u2014 staged entry recommended`
      : `Trim to ${(confidence / 40).toFixed(1)}% under-weight vs. benchmark; avoid new entries`;

  return {
    company: t.name,
    symbol: t.symbol,
    price: t.price,
    change: t.change,
    turns,
    conviction,
    verdict: {
      action,
      confidence,
      sizing,
      reasoning,
      metrics: {
        cts: (confidence / 100).toFixed(2),
        pds: Math.min(1, diff / 40).toFixed(2),
        entropy: (1.4 + (t.rsi % 20) / 20).toFixed(2) + " bits",
        bui: Math.min(0.95, 0.35 + Math.abs(t.sentimentScore)).toFixed(2),
      },
    },
  };
}

function getDebate(symbol) {
  if (symbol === "NVDA") return NVDA_DEBATE;
  const t = WATCHLIST.find((w) => w.symbol === symbol);
  return generateDebate(t);
}

/* ============================================================
   SMALL HELPERS / SHARED COMPONENTS
   ============================================================ */
function sentimentColor(label) {
  if (label === "Positive" || label === "Trending Positive") return "var(--bull)";
  if (label === "Negative" || label === "Trending Negative") return "var(--bear)";
  return "var(--text-dim)";
}

function ChangeArrow({ value }) {
  const color = value > 0 ? "var(--bull)" : value < 0 ? "var(--bear)" : "var(--text-dim)";
  const Icon = value > 0 ? TrendingUp : value < 0 ? TrendingDown : Minus;
  return (
    <span className="watch-change" style={{ color }}>
      <Icon size={13} />
      {value > 0 ? "+" : ""}{value.toFixed(2)}%
    </span>
  );
}

function SentimentBadge({ label, score }) {
  const color = sentimentColor(label);
  return (
    <span className="sentiment-badge" style={{ background: `${color}1a`, color }}>
      <span className="sentiment-dot" style={{ background: color }} />
      {label} {"\u00b7"} {fmtScore(score)}
    </span>
  );
}

const CITATION_ICONS = {
  sentiment: Newspaper,
  headline: Newspaper,
  technical: Activity,
  model: Cpu,
  sector: BarChart3,
  risk: Gauge,
  synthesis: Scale,
  concession: Check,
};

function PulseHeader() {
  return (
    <svg className="pulse-svg" viewBox="0 0 800 80" preserveAspectRatio="none">
      <path
        className="pulse-path"
        d="M0,40 L160,40 L185,12 L210,68 L235,40 L420,40 L445,18 L470,62 L495,40 L800,40"
        stroke="var(--accent)"
        strokeWidth="2"
        fill="none"
      />
    </svg>
  );
}

function NavBar({ page, setPage }) {
  const onDashboard = page === "dashboard" || page === "debate" || page === "verdict";
  return (
    <div className="nav">
      <div className="brand">
        <div className="brand-mark"><Activity size={17} /></div>
        <div className="brand-text">PulseShift<span>AI</span></div>
      </div>
      <div className="nav-tabs">
        <button className={`nav-tab ${onDashboard ? "active" : ""}`} onClick={() => setPage("dashboard")}>Dashboard</button>
        <button className={`nav-tab ${page === "portfolio" ? "active" : ""}`} onClick={() => setPage("portfolio")}>Portfolio</button>
      </div>
    </div>
  );
}

/* ============================================================
   DASHBOARD PAGE
   ============================================================ */
function Dashboard({ onDebate }) {
  return (
    <div>
      <div className="mood-banner">
        <PulseHeader />
        <div className="mood-row">
          <div>
            <div className="mood-label">Market Mood</div>
            <div className="mood-value">
              {MARKET_MOOD.label}
              <span className="mood-chip" style={{ background: "var(--bull-soft)", color: "var(--bull)" }}>
                Index {fmtScore(MARKET_MOOD.score)}
              </span>
            </div>
          </div>
          <div className="mood-meta">{MARKET_MOOD.articles} articles {"\u00b7"} 3-day window</div>
        </div>
      </div>

      <div className="sector-strip-wrap">
        <div className="section-eyebrow">Sector Sentiment</div>
        <div className="sector-strip">
          {SECTOR_MOOD.map((s) => (
            <div className="sector-chip" key={s.sector}>
              <span className="name">{s.sector}</span>
              <span className="val" style={{ color: s.score >= 0 ? "var(--bull)" : "var(--bear)" }}>
                {fmtScore(s.score)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="section-eyebrow">Your Watchlist</div>
      <div className="watchlist-grid">
        {WATCHLIST.map((t) => (
          <div className="watch-card" key={t.symbol}>
            <div className="watch-head">
              <div>
                <div className="watch-symbol">{t.symbol}</div>
                <div className="watch-name">{t.name}</div>
              </div>
              <div className="watch-price">
                <div className="px">${t.price.toFixed(2)}</div>
                <ChangeArrow value={t.change} />
              </div>
            </div>
            <SentimentBadge label={t.sentimentLabel} score={t.sentimentScore} />
            <div className="watch-stats">
              <span>RSI <b>{t.rsi}</b></span>
              <span>Vol <b>{t.atrPct}%</b></span>
              <span>{t.sector}</span>
            </div>
            <button className="debate-btn" onClick={() => onDebate(t.symbol)}>
              <Scale size={15} /> Debate this stock
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================================================
   DEBATE PAGE
   ============================================================ */
function Debate({ symbol, debateState, setDebateState, onBack, onVerdict }) {
  const data = getDebate(symbol);
  const total = data.turns.length;
  const { visibleTurns, running, done } = debateState;
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (!running) return;
    if (visibleTurns >= total) {
      setDebateState((s) => ({ ...s, running: false, done: true }));
      return;
    }
    const id = setTimeout(() => {
      setDebateState((s) => ({ ...s, visibleTurns: s.visibleTurns + 1 }));
    }, 1500);
    return () => clearTimeout(id);
  }, [running, visibleTurns, total, setDebateState]);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [visibleTurns]);

  const chartData = data.conviction.slice(0, visibleTurns + 1);
  const current = data.conviction[visibleTurns];

  const handleRun = () => {
    if (done) {
      setDebateState({ visibleTurns: 0, running: true, done: false });
    } else {
      setDebateState((s) => ({ ...s, running: true }));
    }
  };
  const handleReset = () => setDebateState({ visibleTurns: 0, running: false, done: false });
  const handleSkip = () => setDebateState({ visibleTurns: total, running: false, done: true });

  return (
    <div>
      <button className="back-link" onClick={onBack}><ArrowLeft size={15} /> Back to dashboard</button>

      <div className="debate-header">
        <div className="debate-title">
          <span className="sym">{data.symbol}</span>
          <span className="nm">{data.company}</span>
        </div>
        <div className="debate-price-block">
          <div className="px">${data.price.toFixed(2)}</div>
          <ChangeArrow value={data.change} />
        </div>
      </div>

      <div className="debate-layout">
        <div className="transcript-card" ref={transcriptRef}>
          {visibleTurns === 0 && !running && (
            <div className="transcript-empty">
              Press &ldquo;Run debate&rdquo; to start the Bull / Bear exchange for {data.symbol}.
              <br />Up to {total} exchanges, moderated to a final verdict.
            </div>
          )}
          {data.turns.slice(0, visibleTurns).map((turn, i) => {
            const Icon = CITATION_ICONS[turn.citationType] || Newspaper;
            const isLatest = i === visibleTurns - 1 && (running || !done);
            const glow = turn.speaker === "bull" ? "var(--bull)" : "var(--bear)";
            return (
              <div
                className={`turn ${turn.speaker} ${isLatest ? "latest" : ""}`}
                key={i}
                style={isLatest ? { "--glow": glow } : undefined}
              >
                <div className="turn-head">
                  <span className={`turn-who ${turn.speaker}`}>
                    {turn.speaker === "bull" ? "\ud83d\udc02 Bull" : "\ud83d\udc3b Bear"}
                  </span>
                  <span className="turn-round">Exchange {i + 1} / {total} {"\u00b7"} Round {turn.roundLabel}</span>
                </div>
                <div className="turn-text">{turn.text}</div>
                <div className="turn-citation">
                  <Icon size={14} />
                  {turn.citationLabel}: <b>{turn.citationValue}</b>
                </div>
              </div>
            );
          })}

          {done && (
            <div className="moderator-card">
              <div className="moderator-head"><Scale size={15} /> Moderator Verdict</div>
              <div className="moderator-text">
                Across {total} exchanges, the {data.verdict.action === "BUY" ? "Bull" : "Bear"} case built the more
                consistent multi-signal thesis, while the opposing side narrowed to a tactical caveat and
                ultimately conceded. Net assessment: <b>{data.verdict.action}</b> with{" "}
                {data.verdict.confidence}% confidence.
              </div>
              <button className="btn btn-primary" onClick={onVerdict}>
                View full verdict <ChevronRight size={15} />
              </button>
            </div>
          )}
        </div>

        <div className="sidebar">
          <div className="side-card">
            <h3>Debate Progress</h3>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${(visibleTurns / total) * 100}%` }} />
            </div>
            <div className="progress-label">
              <span>Exchange {visibleTurns} / {total}</span>
              <span>{done ? "Complete" : running ? "In progress\u2026" : "Paused"}</span>
            </div>
          </div>

          <div className="side-card">
            <h3>Live Conviction</h3>
            <div className="meter-row">
              <div className="meter-label"><span className="name" style={{ color: "var(--bull)" }}>Bull</span><span className="val">{current.bull}</span></div>
              <div className="meter-track"><div className="meter-fill bull" style={{ width: `${current.bull}%` }} /></div>
            </div>
            <div className="meter-row">
              <div className="meter-label"><span className="name" style={{ color: "var(--bear)" }}>Bear</span><span className="val">{current.bear}</span></div>
              <div className="meter-track"><div className="meter-fill bear" style={{ width: `${current.bear}%` }} /></div>
            </div>
            <ResponsiveContainer width="100%" height={130}>
              <LineChart data={chartData} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="turn" stroke="var(--text-faint)" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis domain={[20, 95]} stroke="var(--text-faint)" fontSize={10} tickLine={false} axisLine={false} width={28} />
                <Tooltip contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} labelStyle={{ color: "var(--text-dim)" }} />
                <Line type="monotone" dataKey="bull" stroke="var(--bull)" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="bear" stroke="var(--bear)" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="side-card">
            <h3>Reference Signals</h3>
            <div className="stat-grid">
              <div className="stat-box"><div className="lbl">Sentiment</div><div className="v" style={{ color: sentimentColor(WATCHLIST.find(w=>w.symbol===symbol).sentimentLabel) }}>{fmtScore(WATCHLIST.find(w=>w.symbol===symbol).sentimentScore)}</div></div>
              <div className="stat-box"><div className="lbl">RSI (14d)</div><div className="v">{WATCHLIST.find(w=>w.symbol===symbol).rsi}</div></div>
              <div className="stat-box"><div className="lbl">ATR Vol.</div><div className="v">{WATCHLIST.find(w=>w.symbol===symbol).atrPct}%</div></div>
              <div className="stat-box"><div className="lbl">Sector</div><div className="v" style={{ fontSize: "0.78rem" }}>{WATCHLIST.find(w=>w.symbol===symbol).sector}</div></div>
            </div>
          </div>

          <div className="side-card">
            <h3>Controls</h3>
            <div className="controls">
              <button className="btn btn-primary" onClick={handleRun} disabled={running}>
                <Play size={14} /> {done ? "Replay" : visibleTurns > 0 ? "Resume" : "Run debate"}
              </button>
              <button className="btn" onClick={handleSkip} disabled={done}><FastForward size={14} /> Skip</button>
              <button className="btn" onClick={handleReset}><RotateCcw size={14} /> Reset</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   VERDICT PAGE
   ============================================================ */
function Verdict({ symbol, onBack, portfolio, onAdd }) {
  const data = getDebate(symbol);
  const v = data.verdict;
  const isBuy = v.action === "BUY";
  const alreadyHeld = portfolio.some((p) => p.symbol === symbol);

  const handleAdd = () => {
    if (alreadyHeld) return;
    const bookSize = 100000;
    const pct = parseFloat(v.sizing.match(/[\d.]+/)?.[0] || "1") / 100;
    const qty = Math.max(1, Math.round((bookSize * pct) / data.price));
    onAdd({ symbol: data.symbol, name: data.company, qty, entry: data.price, action: v.action });
  };

  return (
    <div>
      <button className="back-link" onClick={onBack}><ArrowLeft size={15} /> Back to debate</button>

      <div className="verdict-grid">
        <div className={`decision-card ${isBuy ? "buy" : "sell"}`}>
          <div className="section-eyebrow">{data.symbol} {"\u00b7"} Moderator Verdict</div>
          <div className={`decision-action ${isBuy ? "buy" : "sell"}`}>
            {isBuy ? <TrendingUp size={32} /> : <TrendingDown size={32} />}
            {v.action}
          </div>
          <div className="decision-sub">
            Based on {data.turns.length} debate exchanges between the Bull and Bear agents, moderated to a single
            recommendation.
          </div>

          <div className="confidence-row">
            <div className="confidence-ring">{v.confidence}%</div>
            <div className="confidence-track">
              <div className={`confidence-fill ${isBuy ? "buy" : "sell"}`} style={{ width: `${v.confidence}%` }} />
            </div>
          </div>

          <div className="sizing-box">
            <b>Suggested action:</b> {v.sizing}
          </div>

          <ul className="reasoning-list">
            {v.reasoning.map((r, i) => (
              <li key={i}>
                <Check size={16} color={isBuy ? "var(--bull)" : "var(--bear)"} />
                <span>{r}</span>
              </li>
            ))}
          </ul>

          <button
            className={`btn btn-full ${isBuy ? "btn-buy" : "btn-sell"}`}
            onClick={handleAdd}
            disabled={alreadyHeld}
          >
            {alreadyHeld ? "Already in portfolio" : isBuy ? "Buy \u2014 add to mock portfolio" : "Sell \u2014 add to mock portfolio"}
          </button>
        </div>

        <div className="side-card">
          <h3>Debate Analytics</h3>
          <div className="analytics-grid">
            <div className="analytic-chip"><div className="lbl">Confidence Trajectory</div><div className="v">{v.metrics.cts}</div></div>
            <div className="analytic-chip"><div className="lbl">Pushback Discrimination</div><div className="v">{v.metrics.pds}</div></div>
            <div className="analytic-chip"><div className="lbl">Argument Entropy</div><div className="v">{v.metrics.entropy}</div></div>
            <div className="analytic-chip"><div className="lbl">Bayesian Updating Index</div><div className="v">{v.metrics.bui}</div></div>
          </div>
          <div className="analytic-note">
            These metrics quantify how the debate evolved {"\u2014"} how decisively conviction moved, how much the
            opposing side's pushback weakened, and how diverse the cited evidence was across the exchange.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   PORTFOLIO PAGE
   ============================================================ */
function Portfolio({ portfolio }) {
  const seed = [
    { symbol: "AAPL", name: "Apple Inc.", qty: 40, entry: 206.10, action: "BUY" },
    { symbol: "JPM", name: "JPMorgan Chase & Co.", qty: 25, entry: 238.40, action: "BUY" },
  ];
  const rows = [...seed, ...portfolio];
  const live = WATCHLIST.reduce((m, w) => ({ ...m, [w.symbol]: w.price }), {});

  return (
    <div>
      <div className="section-eyebrow">Mock Portfolio</div>
      <div className="side-card" style={{ padding: 0 }}>
        {rows.length === 0 ? (
          <div className="portfolio-empty">No positions yet {"\u2014"} run a debate and act on the verdict to add one.</div>
        ) : (
          <table className="portfolio-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Side</th>
                <th className="num">Qty</th>
                <th className="num">Entry</th>
                <th className="num">Current</th>
                <th className="num">P&amp;L</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const cur = live[r.symbol] ?? r.entry;
                const pnl = (cur - r.entry) * r.qty * (r.action === "SELL" ? -1 : 1);
                const pnlColor = pnl > 0 ? "var(--bull)" : pnl < 0 ? "var(--bear)" : "var(--text-dim)";
                return (
                  <tr key={i}>
                    <td className="mono" style={{ fontWeight: 700 }}>{r.symbol}</td>
                    <td>{r.name}</td>
                    <td>
                      <span className="sentiment-badge" style={{
                        background: r.action === "BUY" ? "var(--bull-soft)" : "var(--bear-soft)",
                        color: r.action === "BUY" ? "var(--bull)" : "var(--bear)",
                      }}>{r.action}</span>
                    </td>
                    <td className="num">{r.qty}</td>
                    <td className="num">${r.entry.toFixed(2)}</td>
                    <td className="num">${cur.toFixed(2)}</td>
                    <td className="num" style={{ color: pnlColor }}>
                      {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

/* ============================================================
   APP ROOT
   ============================================================ */
export default function PulseShiftMockup() {
  const [page, setPage] = useState("dashboard");
  const [activeSymbol, setActiveSymbol] = useState(null);
  const [portfolio, setPortfolio] = useState([]);
  const [debateState, setDebateState] = useState({ visibleTurns: 0, running: false, done: false });
  const [toast, setToast] = useState(null);

  const goDebate = (symbol) => {
    setActiveSymbol(symbol);
    setDebateState({ visibleTurns: 0, running: false, done: false });
    setPage("debate");
  };

  const handleAdd = (position) => {
    setPortfolio((p) => [...p, position]);
    setToast(`${position.action === "BUY" ? "Bought" : "Sold"} ${position.qty} ${position.symbol} \u2014 added to mock portfolio`);
    setTimeout(() => setToast(null), 2600);
  };

  const setPageGuarded = (p) => {
    if (p === "dashboard") setActiveSymbol(null);
    setPage(p);
  };

  return (
    <div className="psai">
      <style>{CSS}</style>
      <div className="shell">
        <NavBar page={page} setPage={setPageGuarded} />
        {page === "dashboard" && <Dashboard onDebate={goDebate} />}
        {page === "debate" && activeSymbol && (
          <Debate
            symbol={activeSymbol}
            debateState={debateState}
            setDebateState={setDebateState}
            onBack={() => setPage("dashboard")}
            onVerdict={() => setPage("verdict")}
          />
        )}
        {page === "verdict" && activeSymbol && (
          <Verdict symbol={activeSymbol} onBack={() => setPage("debate")} portfolio={portfolio} onAdd={handleAdd} />
        )}
        {page === "portfolio" && <Portfolio portfolio={portfolio} />}
      </div>
      {toast && <div className="toast"><Check size={16} /> {toast}</div>}
    </div>
  );
}
