import React, { useState, useEffect, useRef } from "react";
import { fetchWatchlist, fetchSectorSnapshot, streamDebate, resolveTicker } from "./api";
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

.ticker-search-wrap { margin-top: 28px; }
.ticker-search { display: flex; gap: 10px; }
.ticker-search-input {
  flex: 1; background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 10px 14px; color: var(--text); font-size: 0.88rem; font-family: inherit;
}
.ticker-search-input::placeholder { color: var(--text-faint); }
.ticker-search-input:focus { outline: none; border-color: var(--accent); }
.ticker-search-input:disabled { opacity: 0.6; }
.ticker-search .btn { white-space: nowrap; }
.ticker-search-error { color: var(--bear); font-size: 0.82rem; margin-top: 8px; }
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

.dash-status {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  min-height: 240px; color: var(--text-faint); font-size: 0.92rem; text-align: center; padding: 24px;
}
.dash-status-error { color: var(--bear); flex-direction: column; }
.dash-status-error code {
  font-family: 'IBM Plex Mono', monospace; background: var(--panel-2);
  border: 1px solid var(--border); border-radius: 6px; padding: 2px 6px; font-size: 0.82em;
}

.turn-loading {
  display: flex; align-items: center; gap: 10px; padding: 14px;
  color: var(--text-faint); font-size: 0.85rem; font-style: italic;
}

.spinner {
  width: 16px; height: 16px; border-radius: 50%;
  border: 2px solid var(--border); border-top-color: var(--accent);
  animation: spin 0.8s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.controls-note { font-size: 0.74rem; color: var(--text-faint); margin-top: 8px; line-height: 1.4; }

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
const fmtScore = (v) => (v == null ? "\u2014" : (v >= 0 ? "+" : "") + v.toFixed(2));

/* ============================================================
   SMALL HELPERS / SHARED COMPONENTS
   ============================================================ */
function sentimentColor(label) {
  if (label === "Positive" || label === "Trending Positive") return "var(--bull)";
  if (label === "Negative" || label === "Trending Negative") return "var(--bear)";
  return "var(--text-dim)";
}

function ChangeArrow({ value, suffix }) {
  if (value == null) {
    return <span className="watch-change" style={{ color: "var(--text-dim)" }}>&mdash;</span>;
  }
  const color = value > 0 ? "var(--bull)" : value < 0 ? "var(--bear)" : "var(--text-dim)";
  const Icon = value > 0 ? TrendingUp : value < 0 ? TrendingDown : Minus;
  return (
    <span className="watch-change" style={{ color }}>
      <Icon size={13} />
      {value > 0 ? "+" : ""}{value.toFixed(2)}%{suffix ? ` ${suffix}` : ""}
    </span>
  );
}

function SentimentBadge({ label, score }) {
  const color = sentimentColor(label);
  return (
    <span className="sentiment-badge" style={{ background: `${color}1a`, color }}>
      <span className="sentiment-dot" style={{ background: color }} />
      {label ?? "No data"} {"\u00b7"} {fmtScore(score)}
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
function TickerSearch({ onDebate }) {
  const [query, setQuery] = useState("");
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (!q || resolving) return;
    setResolving(true);
    setError(null);
    try {
      const { ticker, company_name } = await resolveTicker(q);
      setQuery("");
      onDebate(ticker, company_name);
    } catch (err) {
      setError(err.message);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="ticker-search-wrap">
      <div className="section-eyebrow">Debate Any Stock</div>
      <form className="ticker-search" onSubmit={handleSubmit}>
        <input
          type="text"
          className="ticker-search-input"
          placeholder="Type a company name or ticker (e.g. Microsoft, MSFT)\u2026"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={resolving}
        />
        <button type="submit" className="btn btn-primary" disabled={resolving || !query.trim()}>
          {resolving ? <span className="spinner" /> : <Scale size={15} />}
          {resolving ? "Looking up\u2026" : "Debate this stock"}
        </button>
      </form>
      {error && <div className="ticker-search-error">{error}</div>}
    </div>
  );
}

function Dashboard({ onDebate, watchlist, sectorSnapshot, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="dash-status">
        <div className="spinner" />
        Loading live market data\u2026 (first load can take a little while \u2014 it's a real news fetch, not cached)
      </div>
    );
  }
  if (error) {
    return (
      <div className="dash-status dash-status-error">
        Couldn't reach the PulseShiftAI backend ({error}).
        <br />Make sure <code>uvicorn api.main:app --port 8000</code> is running.
        <button className="btn" onClick={onRetry} style={{ marginTop: 12 }}>Retry</button>
      </div>
    );
  }

  const mood = sectorSnapshot?.mood;
  const bySector = sectorSnapshot?.by_sector || [];

  return (
    <div>
      <div className="mood-banner">
        <PulseHeader />
        <div className="mood-row">
          <div>
            <div className="mood-label">Market Mood</div>
            <div className="mood-value">
              {mood?.label ?? "\u2014"}
              <span className="mood-chip" style={{ background: "var(--bull-soft)", color: "var(--bull)" }}>
                Index {fmtScore(mood?.avg_score)}
              </span>
            </div>
          </div>
          <div className="mood-meta">{mood?.n_articles ?? 0} articles {"\u00b7"} 3-day window</div>
        </div>
      </div>

      <div className="sector-strip-wrap">
        <div className="section-eyebrow">Sector Sentiment</div>
        <div className="sector-strip">
          {bySector.map((s) => (
            <div className="sector-chip" key={s.sector}>
              <span className="name">{s.sector}</span>
              <span className="val" style={{ color: s.avg_score >= 0 ? "var(--bull)" : "var(--bear)" }}>
                {fmtScore(s.avg_score)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="section-eyebrow">Your Watchlist</div>
      <div className="watchlist-grid">
        {watchlist.map((t) => (
          <div className="watch-card" key={t.ticker}>
            <div className="watch-head">
              <div>
                <div className="watch-symbol">{t.ticker}</div>
                <div className="watch-name">{t.company_name}</div>
              </div>
              <div className="watch-price">
                {t.close != null && <div className="px">${t.close.toFixed(2)}</div>}
                <ChangeArrow value={t.pct_change} suffix="wk" />
              </div>
            </div>
            <SentimentBadge label={t.sentiment_label} score={t.sentiment_score} />
            <div className="watch-stats">
              <span>RSI <b>{t.rsi != null ? t.rsi : "\u2014"}</b></span>
              <span>{t.sector}</span>
            </div>
            <button className="debate-btn" onClick={() => onDebate(t.ticker)}>
              <Scale size={15} /> Debate this stock
            </button>
          </div>
        ))}
      </div>

      <TickerSearch onDebate={onDebate} />
    </div>
  );
}

/* ============================================================
   DEBATE PAGE
   ============================================================ */
function Debate({ symbol, debate, onStart, onBack, onVerdict }) {
  const { evidence, turns, conviction, verdict, streaming, error } = debate;
  const total = turns.length;
  const done = !!verdict;
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [turns.length]);

  const current = conviction.length ? conviction[conviction.length - 1] : { bull: 50, bear: 50 };
  const chartData = conviction.length ? conviction : [{ turn: 0, bull: 50, bear: 50 }];

  const handleRun = () => onStart(symbol, evidence?.company_name);

  return (
    <div>
      <button className="back-link" onClick={onBack}><ArrowLeft size={15} /> Back to dashboard</button>

      <div className="debate-header">
        <div className="debate-title">
          <span className="sym">{symbol}</span>
          <span className="nm">{evidence?.company_name ?? ""}</span>
        </div>
        {evidence?.technical && (
          <div className="debate-price-block">
            {evidence.technical.close != null && <div className="px">${evidence.technical.close.toFixed(2)}</div>}
            <ChangeArrow value={evidence.technical.pct_change} suffix="this wk" />
          </div>
        )}
      </div>

      <div className="debate-layout">
        <div className="transcript-card" ref={transcriptRef}>
          {turns.length === 0 && !streaming && !error && (
            <div className="transcript-empty">
              Press &ldquo;Run debate&rdquo; to start a live Bull / Bear exchange for {symbol}.
              <br />Up to 10 exchanges, moderated to a final verdict \u2014 this calls the real
              backend and typically takes 60\u201390 seconds.
            </div>
          )}

          {error && (
            <div className="transcript-empty" style={{ color: "var(--bear)" }}>
              {error}
              <br /><button className="btn" style={{ marginTop: 10 }} onClick={handleRun}>Try again</button>
            </div>
          )}

          {turns.map((turn, i) => {
            const Icon = CITATION_ICONS[turn.citationType] || Newspaper;
            const isLatest = i === turns.length - 1 && !done;
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
                  <span className="turn-round">Exchange {i + 1} / 10 {"\u00b7"} Round {turn.roundLabel}</span>
                </div>
                <div className="turn-text">{turn.text}</div>
                <div className="turn-citation">
                  <Icon size={14} />
                  {turn.citationLabel}: <b>{turn.citationValue}</b>
                </div>
              </div>
            );
          })}

          {streaming && !done && turns.length < 10 && (
            <div className="turn-loading">
              <div className="spinner" /> {turns.length === 0 ? "Fetching live evidence\u2026" : "Next exchange generating\u2026"}
            </div>
          )}

          {done && (
            <div className="moderator-card">
              <div className="moderator-head"><Scale size={15} /> Moderator Verdict</div>
              <div className="moderator-text">
                Across {total} exchanges, the {verdict.action === "BUY" ? "Bull" : "Bear"} case built the more
                consistent multi-signal thesis. Net assessment: <b>{verdict.action}</b> with{" "}
                {verdict.confidence}% confidence.
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
              <div className="progress-fill" style={{ width: `${(turns.length / 10) * 100}%` }} />
            </div>
            <div className="progress-label">
              <span>Exchange {turns.length} / 10</span>
              <span>{done ? "Complete" : streaming ? "Live\u2026" : error ? "Failed" : "Not started"}</span>
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
              <div className="stat-box"><div className="lbl">Sentiment</div><div className="v" style={{ color: sentimentColor(evidence?.sentiment?.label) }}>{fmtScore(evidence?.sentiment?.avg_score)}</div></div>
              <div className="stat-box"><div className="lbl">RSI (wk)</div><div className="v">{evidence?.technical?.rsi ?? "\u2014"}</div></div>
              <div className="stat-box"><div className="lbl">ATR Vol.</div><div className="v">{evidence?.technical?.atr_pct != null ? `${evidence.technical.atr_pct}%` : "\u2014"}</div></div>
              <div className="stat-box"><div className="lbl">Sector</div><div className="v" style={{ fontSize: "0.78rem" }}>{evidence?.sector ?? "\u2014"}</div></div>
            </div>
          </div>

          <div className="side-card">
            <h3>Controls</h3>
            <div className="controls">
              <button className="btn btn-primary" onClick={handleRun} disabled={streaming}>
                <Play size={14} /> {done ? "Run again (new live debate)" : streaming ? "Running\u2026" : "Run debate"}
              </button>
            </div>
            {done && (
              <div className="controls-note">
                Re-running calls the live model again and can produce a different transcript and verdict.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   VERDICT PAGE
   ============================================================ */
function Verdict({ symbol, debate, onBack, portfolio, onAdd }) {
  const { evidence, turns, verdict } = debate;
  if (!verdict) {
    // Guards against navigating to /verdict directly before a debate has
    // actually completed (e.g. a stale link or a fast double-click) \u2014
    // there's nothing real to show yet.
    return (
      <div>
        <button className="back-link" onClick={onBack}><ArrowLeft size={15} /> Back to debate</button>
        <div className="transcript-empty">No completed verdict for {symbol} yet.</div>
      </div>
    );
  }

  const isBuy = verdict.action === "BUY";
  const alreadyHeld = portfolio.some((p) => p.symbol === symbol);

  const handleAdd = () => {
    if (alreadyHeld) return;
    onAdd({
      symbol,
      name: evidence?.company_name ?? symbol,
      action: verdict.action,
      sizing: verdict.sizing,
      confidence: verdict.confidence,
      date: new Date().toISOString(),
    });
  };

  return (
    <div>
      <button className="back-link" onClick={onBack}><ArrowLeft size={15} /> Back to debate</button>

      <div className="verdict-grid">
        <div className={`decision-card ${isBuy ? "buy" : "sell"}`}>
          <div className="section-eyebrow">{symbol} {"\u00b7"} Moderator Verdict</div>
          <div className={`decision-action ${isBuy ? "buy" : "sell"}`}>
            {isBuy ? <TrendingUp size={32} /> : <TrendingDown size={32} />}
            {verdict.action}
          </div>
          <div className="decision-sub">
            Based on {turns.length} debate exchanges between the Bull and Bear agents, moderated to a single
            recommendation.
          </div>

          <div className="confidence-row">
            <div className="confidence-ring">{verdict.confidence}%</div>
            <div className="confidence-track">
              <div className={`confidence-fill ${isBuy ? "buy" : "sell"}`} style={{ width: `${verdict.confidence}%` }} />
            </div>
          </div>

          <div className="sizing-box">
            <b>Suggested action:</b> {verdict.sizing}
          </div>

          <ul className="reasoning-list">
            {verdict.reasoning.map((r, i) => (
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
      </div>
    </div>
  );
}

/* ============================================================
   PORTFOLIO PAGE
   ============================================================ */
function Portfolio({ portfolio }) {
  const fmtDate = (iso) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch {
      return iso;
    }
  };

  return (
    <div>
      <div className="section-eyebrow">Recommendation Log</div>
      <div className="side-card" style={{ padding: 0 }}>
        {portfolio.length === 0 ? (
          <div className="portfolio-empty">No recommendations yet {"\u2014"} run a debate and act on the verdict to add one.</div>
        ) : (
          <table className="portfolio-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Side</th>
                <th>Suggested sizing</th>
                <th className="num">Confidence</th>
                <th>Logged</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((r, i) => (
                <tr key={i}>
                  <td className="mono" style={{ fontWeight: 700 }}>{r.symbol}</td>
                  <td>{r.name}</td>
                  <td>
                    <span className="sentiment-badge" style={{
                      background: r.action === "BUY" ? "var(--bull-soft)" : "var(--bear-soft)",
                      color: r.action === "BUY" ? "var(--bull)" : "var(--bear)",
                    }}>{r.action}</span>
                  </td>
                  <td>{r.sizing}</td>
                  <td className="num">{r.confidence}%</td>
                  <td>{fmtDate(r.date)}</td>
                </tr>
              ))}
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
const EMPTY_DEBATE = { evidence: null, turns: [], conviction: [], verdict: null, streaming: false, error: null };

export default function PulseShiftMockup() {
  const [page, setPage] = useState("dashboard");
  const [activeSymbol, setActiveSymbol] = useState(null);
  const [portfolio, setPortfolio] = useState([]);
  const [toast, setToast] = useState(null);

  // ---- Dashboard data (real fetch on mount) ----
  const [watchlist, setWatchlist] = useState([]);
  const [sectorSnapshot, setSectorSnapshot] = useState(null);
  const [dashLoading, setDashLoading] = useState(true);
  const [dashError, setDashError] = useState(null);

  const loadDashboard = () => {
    setDashLoading(true);
    setDashError(null);
    Promise.all([fetchWatchlist(), fetchSectorSnapshot()])
      .then(([items, snapshot]) => {
        setWatchlist(items);
        setSectorSnapshot(snapshot);
      })
      .catch((err) => setDashError(err.message))
      .finally(() => setDashLoading(false));
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // ---- Debate data, keyed by ticker so navigating dashboard <-> debate <->
  // verdict and back doesn't lose progress or re-trigger a new live debate.
  const [debates, setDebates] = useState({}); // { [symbol]: { evidence, turns, conviction, verdict, streaming, error } }
  const closeStreamRef = useRef(null); // close() fn for whichever SSE connection is currently open, if any

  useEffect(() => {
    // Safety net: if the component unmounts (e.g. hot-reload during dev)
    // while a debate is mid-stream, close the connection rather than
    // leaking it.
    return () => closeStreamRef.current?.();
  }, []);

  // Company names for tickers resolved via the custom-ticker input (not in
  // the fixed WATCHLIST) \u2014 streamDebate needs this to pass ?company_name=
  // on every request for such tickers, since the backend only knows
  // WATCHLIST names automatically.
  const [customNames, setCustomNames] = useState({}); // { [symbol]: companyName }

  const startDebate = (symbol, companyName) => {
    closeStreamRef.current?.(); // only one debate streams at a time
    setDebates((d) => ({ ...d, [symbol]: { ...EMPTY_DEBATE, streaming: true } }));

    closeStreamRef.current = streamDebate(symbol, companyName, {
      onEvidence: (evidence) => {
        setDebates((d) => ({ ...d, [symbol]: { ...d[symbol], evidence } }));
      },
      onTurn: (turn, conviction) => {
        setDebates((d) => {
          const cur = d[symbol];
          const baseConviction = cur.conviction.length ? cur.conviction : [{ turn: 0, bull: 50, bear: 50 }];
          return { ...d, [symbol]: { ...cur, turns: [...cur.turns, turn], conviction: [...baseConviction, conviction] } };
        });
      },
      onVerdict: (verdict) => {
        setDebates((d) => ({ ...d, [symbol]: { ...d[symbol], verdict, streaming: false } }));
      },
      onDone: () => {
        // turns/conviction/verdict already accumulated via the events
        // above; this just confirms the stream finished cleanly.
        setDebates((d) => ({ ...d, [symbol]: { ...d[symbol], streaming: false } }));
      },
      onError: (message) => {
        setDebates((d) => ({ ...d, [symbol]: { ...d[symbol], streaming: false, error: message } }));
      },
    });
  };

  const goDebate = (symbol, companyName) => {
    setActiveSymbol(symbol);
    if (companyName) setCustomNames((n) => ({ ...n, [symbol]: companyName }));
    if (!debates[symbol]) {
      startDebate(symbol, companyName || customNames[symbol]);
    }
    setPage("debate");
  };

  const handleAdd = (rec) => {
    setPortfolio((p) => [...p, rec]);
    setToast(`${rec.action === "BUY" ? "Buy" : "Sell"} ${rec.symbol} \u2014 added to recommendation log`);
    setTimeout(() => setToast(null), 2600);
  };

  const setPageGuarded = (p) => {
    if (p === "dashboard") setActiveSymbol(null);
    setPage(p);
  };

  const activeDebate = activeSymbol ? (debates[activeSymbol] || EMPTY_DEBATE) : EMPTY_DEBATE;

  return (
    <div className="psai">
      <style>{CSS}</style>
      <div className="shell">
        <NavBar page={page} setPage={setPageGuarded} />
        {page === "dashboard" && (
          <Dashboard
            onDebate={goDebate}
            watchlist={watchlist}
            sectorSnapshot={sectorSnapshot}
            loading={dashLoading}
            error={dashError}
            onRetry={loadDashboard}
          />
        )}
        {page === "debate" && activeSymbol && (
          <Debate
            symbol={activeSymbol}
            debate={activeDebate}
            onStart={startDebate}
            onBack={() => setPage("dashboard")}
            onVerdict={() => setPage("verdict")}
          />
        )}
        {page === "verdict" && activeSymbol && (
          <Verdict symbol={activeSymbol} debate={activeDebate} onBack={() => setPage("debate")} portfolio={portfolio} onAdd={handleAdd} />
        )}
        {page === "portfolio" && <Portfolio portfolio={portfolio} />}
      </div>
      {toast && <div className="toast"><Check size={16} /> {toast}</div>}
    </div>
  );
}
