import React, { useState, useEffect, useRef, useCallback } from "react";
import { fetchWatchlist, fetchSectorSnapshot, streamDebate, resolveTicker } from "./api";
import { supabase, loadTrades, insertTrade, deleteTrade } from "./supabase";
import { API_BASE_URL } from "./api";
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
.portfolio-summary { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 20px 24px; margin-bottom: 16px; }
.portfolio-summary-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.portfolio-summary-col { display: flex; flex-direction: column; gap: 4px; }
.portfolio-summary-label { font-size: 0.72rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.08em; }
.portfolio-summary-val { font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 700; color: var(--text); }
.portfolio-summary-val.right { text-align: right; }
.portfolio-pnl-row { display: flex; align-items: center; gap: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
.portfolio-pnl-label { font-size: 0.8rem; color: var(--text-faint); min-width: 40px; }
.portfolio-pnl-val { font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; font-weight: 700; }
.portfolio-pnl-badge { font-size: 0.8rem; font-weight: 600; padding: 3px 10px; border-radius: 20px; font-family: 'IBM Plex Mono', monospace; }
.portfolio-cash { font-size: 0.82rem; color: var(--text-dim); margin-top: 8px; }

.portfolio-holdings { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; margin-bottom: 16px; }
.portfolio-holdings-header { padding: 14px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.portfolio-holdings-title { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-faint); font-weight: 600; }

.holding-row { display: grid; grid-template-columns: 1fr 1fr 1fr; padding: 14px 20px; border-bottom: 1px solid var(--border); transition: background 0.15s; }
.holding-row:last-child { border-bottom: none; }
.holding-row:hover { background: var(--panel-2); }
.holding-left { display: flex; flex-direction: column; gap: 3px; }
.holding-ticker { font-weight: 700; font-size: 0.95rem; color: var(--text); }
.holding-company { font-size: 0.75rem; color: var(--text-faint); }
.holding-meta { font-size: 0.75rem; color: var(--text-dim); }
.holding-center { display: flex; flex-direction: column; gap: 3px; align-items: flex-start; }
.holding-right { display: flex; flex-direction: column; gap: 3px; align-items: flex-end; }
.holding-ltp { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; font-weight: 600; color: var(--text); }
.holding-pnl-abs { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; font-weight: 700; }
.holding-pnl-pct { font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; }
.holding-invested { font-size: 0.75rem; color: var(--text-dim); }

.portfolio-days-pnl { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.days-pnl-label { font-size: 0.78rem; color: var(--text-faint); font-weight: 600; }
.days-pnl-val { font-family: 'IBM Plex Mono', monospace; font-size: 0.95rem; font-weight: 700; }

.portfolio-empty { padding: 48px 16px; text-align: center; color: var(--text-faint); font-size: 0.9rem; }
.portfolio-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
.portfolio-table th, .portfolio-table td { text-align: left; padding: 11px 12px; border-bottom: 1px solid var(--border); }
.portfolio-table th { color: var(--text-faint); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.portfolio-table td.num, .portfolio-table th.num { text-align: right; font-family: 'IBM Plex Mono', monospace; }

/* trade modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 28px; width: 420px; max-width: 90vw; }
.modal-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 20px; color: var(--text); }
.modal-field { margin-bottom: 16px; }
.modal-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-faint); margin-bottom: 6px; display: block; }
.modal-input { width: 100%; background: var(--panel-2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; color: var(--text); font-size: 0.9rem; font-family: inherit; box-sizing: border-box; }
.modal-input:focus { outline: none; border-color: var(--accent); }
.modal-toggle { display: flex; gap: 8px; }
.modal-toggle-btn { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--panel-2); color: var(--text-dim); font-size: 0.88rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.modal-toggle-btn.active-buy { background: var(--bull-soft); border-color: var(--bull); color: var(--bull); }
.modal-toggle-btn.active-sell { background: var(--bear-soft); border-color: var(--bear); color: var(--bear); }
.modal-footer { display: flex; gap: 10px; margin-top: 20px; }
.modal-resolved { font-size: 0.78rem; color: var(--bull); margin-top: 4px; }
.modal-error { font-size: 0.78rem; color: var(--bear); margin-top: 4px; }
.add-trade-btn { margin-bottom: 16px; }

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
  const [showQty, setShowQty] = useState(false);
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [priceLoading, setPriceLoading] = useState(false);
  const [logging, setLogging] = useState(false);
  const [logged, setLogged] = useState(false);

  // Fetch price when the inline form opens
  const handleShowQty = async () => {
    setShowQty(true);
    // Try evidence first (instant), then fall back to a live fetch
    const evidencePrice = evidence?.technical?.close;
    if (evidencePrice) {
      setPrice(evidencePrice.toString());
      return;
    }
    setPriceLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/price/${symbol}`);
      if (res.ok) {
        const data = await res.json();
        if (data.price) setPrice(data.price.toString());
      }
    } catch { /* user can fill in manually */ }
    finally { setPriceLoading(false); }
  };

  if (!verdict) {
    return (
      <div>
        <button className="back-link" onClick={onBack}><ArrowLeft size={15} /> Back to debate</button>
        <div className="transcript-empty">No completed verdict for {symbol} yet.</div>
      </div>
    );
  }

  const isBuy = verdict.action === "BUY";

  const handleLogTrade = async () => {
    if (!quantity || !price) return;
    setLogging(true);
    try {
      await onAdd({
        symbol,
        name: evidence?.company_name ?? symbol,
        action: verdict.action,
        sizing: verdict.sizing,
        confidence: verdict.confidence,
        date: new Date().toISOString(),
        quantity: parseFloat(quantity),
        entry_price: parseFloat(price),
        notes: `Debate verdict: ${verdict.action} ${verdict.confidence}% confidence. ${verdict.sizing}`,
      });
      setLogged(true);
      setShowQty(false);
    } finally {
      setLogging(false);
    }
  };

  const totalValue = quantity && price
    ? (parseFloat(quantity) * parseFloat(price)).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : null;

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

          {/* ── Inline trade logger ── */}
          {!logged && !showQty && (
            <button
              className={`btn btn-full ${isBuy ? "btn-buy" : "btn-sell"}`}
              onClick={handleShowQty}
            >
              {isBuy ? "Buy \u2014 log to portfolio" : "Sell \u2014 log to portfolio"}
            </button>
          )}

          {!logged && showQty && (
            <div style={{ marginTop: 16, padding: "16px", background: "var(--panel-2)", borderRadius: 10, border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "0.78rem", color: "var(--text-faint)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Log this trade to portfolio
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", marginBottom: 4 }}>Quantity (shares)</div>
                  <input
                    className="modal-input"
                    type="number"
                    min="0.01"
                    step="0.01"
                    placeholder="e.g. 100"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    autoFocus
                  />
                </div>
                <div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", marginBottom: 4 }}>Price per share ($){priceLoading ? " …" : ""}</div>
                  <input
                    className="modal-input"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder={priceLoading ? "Fetching…" : "e.g. 212.50"}
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                  />
                </div>
              </div>
              {totalValue && (
                <div style={{ fontSize: "0.78rem", color: "var(--text-dim)", marginBottom: 10 }}>
                  Total value: <b style={{ color: "var(--text)" }}>${totalValue}</b>
                </div>
              )}
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn" style={{ flex: 1 }} onClick={() => setShowQty(false)}>Cancel</button>
                <button
                  className={`btn ${isBuy ? "btn-buy" : "btn-sell"}`}
                  style={{ flex: 2 }}
                  onClick={handleLogTrade}
                  disabled={logging || !quantity || !price}
                >
                  {logging ? "Logging\u2026" : `Confirm ${verdict.action}`}
                </button>
              </div>
            </div>
          )}

          {logged && (
            <div style={{ marginTop: 16, padding: "12px 16px", background: "var(--bull-soft)", borderRadius: 10, color: "var(--bull)", fontSize: "0.88rem", fontWeight: 600, textAlign: "center" }}>
              ✓ Trade logged to portfolio
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   PORTFOLIO PAGE
   ============================================================ */
/* ============================================================
   TRADE MODAL
   ============================================================ */
function TradeModal({ onClose, onSave }) {
  const [query, setQuery] = useState("");
  const [resolved, setResolved] = useState(null); // { ticker, company_name }
  const [action, setAction] = useState("BUY");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [tradeDate, setTradeDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [resolving, setResolving] = useState(false);
  const [priceLoading, setPriceLoading] = useState(false);
  const [resolveError, setResolveError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleResolve = async () => {
    if (!query.trim()) return;
    setResolving(true);
    setResolveError(null);
    setResolved(null);
    setPrice("");
    try {
      const res = await resolveTicker(query.trim());
      setResolved(res);
      // Auto-fetch current price
      setPriceLoading(true);
      try {
        const pr = await fetch(`${API_BASE_URL}/api/price/${res.ticker}`);
        if (pr.ok) {
          const pd = await pr.json();
          setPrice(pd.price.toString());
        }
      } catch { /* price auto-fill failed, user can enter manually */ }
      finally { setPriceLoading(false); }
    } catch (err) {
      setResolveError(err.message);
    } finally {
      setResolving(false);
    }
  };

  const handleSave = async () => {
    if (!resolved || !quantity || !price) return;
    setSaving(true);
    try {
      await onSave({
        ticker: resolved.ticker,
        company_name: resolved.company_name,
        action,
        quantity: parseFloat(quantity),
        entry_price: parseFloat(price),
        notes: notes.trim() || null,
        trade_date: tradeDate,
      });
      onClose();
    } catch (err) {
      setResolveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <div className="modal-title">Log a Trade</div>

        <div className="modal-field">
          <label className="modal-label">Company or Ticker</label>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              className="modal-input"
              placeholder="e.g. NVDA or Microsoft"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setResolved(null); }}
              onKeyDown={(e) => e.key === "Enter" && handleResolve()}
              style={{ flex: 1 }}
            />
            <button className="btn btn-primary" onClick={handleResolve} disabled={resolving || !query.trim()}>
              {resolving ? "…" : "Find"}
            </button>
          </div>
          {resolved && <div className="modal-resolved">✓ {resolved.ticker} — {resolved.company_name}</div>}
          {resolveError && <div className="modal-error">{resolveError}</div>}
        </div>

        <div className="modal-field">
          <label className="modal-label">Side</label>
          <div className="modal-toggle">
            <button className={`modal-toggle-btn ${action === "BUY" ? "active-buy" : ""}`} onClick={() => setAction("BUY")}>BUY</button>
            <button className={`modal-toggle-btn ${action === "SELL" ? "active-sell" : ""}`} onClick={() => setAction("SELL")}>SELL</button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="modal-field">
            <label className="modal-label">Quantity (shares)</label>
            <input className="modal-input" type="number" min="0.01" step="0.01" placeholder="e.g. 10" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div className="modal-field">
            <label className="modal-label">Price per share ($){priceLoading ? " …" : ""}</label>
            <input className="modal-input" type="number" min="0" step="0.01" placeholder="Auto-filled" value={price} onChange={(e) => setPrice(e.target.value)} />
          </div>
        </div>

        <div className="modal-field">
          <label className="modal-label">Trade date</label>
          <input className="modal-input" type="date" value={tradeDate} onChange={(e) => setTradeDate(e.target.value)} />
        </div>

        <div className="modal-field">
          <label className="modal-label">Notes (optional)</label>
          <input className="modal-input" placeholder="e.g. Based on NVDA debate — SELL 60% confidence" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        {quantity && price && resolved && (
          <div style={{ fontSize: "0.8rem", color: "var(--text-dim)", marginBottom: 8 }}>
            Total value: <b style={{ color: "var(--text)" }}>${(parseFloat(quantity) * parseFloat(price)).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</b>
          </div>
        )}

        <div className="modal-footer">
          <button className="btn" style={{ flex: 1 }} onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" style={{ flex: 2 }} onClick={handleSave} disabled={saving || !resolved || !quantity || !price}>
            {saving ? "Saving…" : `Log ${action}`}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   PORTFOLIO
   ============================================================ */
const STARTING_CASH = 1_000_000;
const fmt$ = (n) => "$" + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtPct = (n) => (n >= 0 ? "+" : "") + n.toFixed(2) + "%";

function Portfolio() {
  const [trades, setTrades] = useState([]);
  const [prices, setPrices] = useState({}); // { [ticker]: { price, pct_change } }
  const [loading, setLoading] = useState(true);
  const [pricesLoading, setPricesLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Load all trades from Supabase on mount
  const fetchTrades = useCallback(async () => {
    setLoading(true);
    const { data, error: err } = await loadTrades();
    if (err) { setError(err.message); setLoading(false); return; }
    setTrades(data || []);
    setLoading(false);
  }, []);

  useEffect(() => { fetchTrades(); }, [fetchTrades]);

  // Fetch current prices for all unique tickers whenever trades change
  useEffect(() => {
    const tickers = [...new Set(trades.map((t) => t.ticker))];
    if (!tickers.length) return;
    setPricesLoading(true);
    Promise.all(
      tickers.map((tk) =>
        fetch(`${API_BASE_URL}/api/price/${tk}`)
          .then((r) => r.ok ? r.json() : null)
          .catch(() => null)
      )
    ).then((results) => {
      const map = {};
      results.forEach((r) => { if (r) map[r.ticker] = { price: r.price, pct_change: r.pct_change }; });
      setPrices(map);
    }).finally(() => setPricesLoading(false));
  }, [trades]);

  const handleSaveTrade = async (trade) => {
    const { error: err } = await insertTrade(trade);
    if (err) throw new Error(err.message);
    await fetchTrades();
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Remove this trade?")) return;
    await deleteTrade(id);
    await fetchTrades();
  };

  // ── P&L calculation ──────────────────────────────────────────────────────
  // Build positions: group BUY trades into holdings, net off SELLs
  const positions = (() => {
    const map = {};
    // Sort by trade_date ascending so we process oldest first (FIFO weighting)
    const sorted = [...trades].sort((a, b) => new Date(a.trade_date) - new Date(b.trade_date));
    for (const t of sorted) {
      if (!map[t.ticker]) map[t.ticker] = { ticker: t.ticker, company_name: t.company_name, qty: 0, totalCost: 0 };
      if (t.action === "BUY") {
        map[t.ticker].qty += t.quantity;
        map[t.ticker].totalCost += t.quantity * t.entry_price;
      } else {
        // SELL reduces quantity; reduce cost proportionally
        const avgBefore = map[t.ticker].qty > 0 ? map[t.ticker].totalCost / map[t.ticker].qty : 0;
        map[t.ticker].qty = Math.max(0, map[t.ticker].qty - t.quantity);
        map[t.ticker].totalCost = map[t.ticker].qty * avgBefore;
      }
    }
    return Object.values(map).filter((p) => p.qty > 0).map((p) => {
      const avgEntry = p.totalCost / p.qty;
      const currentPrice = prices[p.ticker]?.price ?? avgEntry;
      const invested = p.totalCost;
      const currentValue = currentPrice * p.qty;
      const pnl = currentValue - invested;
      const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;
      const dayChg = prices[p.ticker]?.pct_change ?? 0;
      return { ...p, avgEntry, currentPrice, invested, currentValue, pnl, pnlPct, dayChg };
    });
  })();

  const totalInvested = positions.reduce((s, p) => s + p.invested, 0);
  const totalCurrentValue = positions.reduce((s, p) => s + p.currentValue, 0);
  const totalPnl = totalCurrentValue - totalInvested;
  const totalPnlPct = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;
  const deployedCapital = trades.reduce((s, t) => t.action === "BUY" ? s + t.quantity * t.entry_price : s - t.quantity * t.entry_price, 0);
  const availableCash = STARTING_CASH - deployedCapital;
  const totalPortfolioValue = availableCash + totalCurrentValue;
  const overallPnl = totalPortfolioValue - STARTING_CASH;
  const overallPnlPct = (overallPnl / STARTING_CASH) * 100;
  const daysPnl = positions.reduce((s, p) => s + (p.currentPrice * p.qty * p.dayChg) / 100, 0);

  const pnlColor = (v) => v >= 0 ? "var(--bull)" : "var(--bear)";
  const pnlBg = (v) => v >= 0 ? "var(--bull-soft)" : "var(--bear-soft)";

  if (loading) return <div className="dash-status"><div className="spinner" /> Loading portfolio…</div>;
  if (error) return <div className="dash-status dash-status-error">Failed to load portfolio: {error}</div>;

  return (
    <div>
      {showModal && <TradeModal onClose={() => setShowModal(false)} onSave={handleSaveTrade} />}

      {/* ── Summary card ── */}
      <div className="portfolio-summary">
        <div className="portfolio-summary-row">
          <div className="portfolio-summary-col">
            <span className="portfolio-summary-label">Invested</span>
            <span className="portfolio-summary-val">{fmt$(totalInvested)}</span>
          </div>
          <div className="portfolio-summary-col" style={{ alignItems: "flex-end" }}>
            <span className="portfolio-summary-label">Current</span>
            <span className="portfolio-summary-val right">{fmt$(totalCurrentValue)}{pricesLoading ? " …" : ""}</span>
          </div>
        </div>
        <div className="portfolio-pnl-row">
          <span className="portfolio-pnl-label">P&amp;L</span>
          <span className="portfolio-pnl-val" style={{ color: pnlColor(totalPnl) }}>
            {totalPnl >= 0 ? "+" : ""}{fmt$(totalPnl)}
          </span>
          <span className="portfolio-pnl-badge" style={{ background: pnlBg(totalPnlPct), color: pnlColor(totalPnlPct) }}>
            {fmtPct(totalPnlPct)}
          </span>
        </div>
        <div className="portfolio-cash">
          Available cash: <b style={{ color: "var(--text)", fontFamily: "'IBM Plex Mono', monospace" }}>{fmt$(availableCash)}</b>
          {" · "}Portfolio total: <b style={{ color: "var(--text)", fontFamily: "'IBM Plex Mono', monospace" }}>{fmt$(totalPortfolioValue)}</b>
          {" · "}Overall: <b style={{ color: pnlColor(overallPnl) }}>{overallPnl >= 0 ? "+" : ""}{fmt$(overallPnl)} ({fmtPct(overallPnlPct)})</b>
        </div>
      </div>

      {/* ── Add trade button ── */}
      <button className="btn btn-primary add-trade-btn" onClick={() => setShowModal(true)}>
        + Log a Trade
      </button>

      {/* ── Holdings ── */}
      {positions.length === 0 ? (
        <div className="portfolio-empty">
          No open positions yet — log a trade above to start tracking.
        </div>
      ) : (
        <div className="portfolio-holdings">
          <div className="portfolio-holdings-header">
            <span className="portfolio-holdings-title">Holdings ({positions.length})</span>
            {pricesLoading && <span style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>Updating prices…</span>}
          </div>
          {positions.map((p) => (
            <div className="holding-row" key={p.ticker}>
              <div className="holding-left">
                <span className="holding-ticker">{p.ticker}</span>
                <span className="holding-company">{p.company_name}</span>
                <span className="holding-meta">Qty {p.qty} · Avg {fmt$(p.avgEntry)}</span>
              </div>
              <div className="holding-center">
                <span className="holding-invested">Invested {fmt$(p.invested)}</span>
                <span className="holding-ltp">LTP {fmt$(p.currentPrice)}</span>
                <span style={{ fontSize: "0.75rem", color: pnlColor(p.dayChg) }}>
                  Day {fmtPct(p.dayChg)}
                </span>
              </div>
              <div className="holding-right">
                <span className="holding-pnl-pct" style={{ color: pnlColor(p.pnlPct) }}>{fmtPct(p.pnlPct)}</span>
                <span className="holding-pnl-abs" style={{ color: pnlColor(p.pnl) }}>
                  {p.pnl >= 0 ? "+" : ""}{fmt$(p.pnl)}
                </span>
                <button
                  onClick={() => handleDelete(trades.find(t => t.ticker === p.ticker)?.id)}
                  style={{ fontSize: "0.7rem", color: "var(--text-faint)", background: "none", border: "none", cursor: "pointer", marginTop: 2 }}
                >
                  remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Day's P&L ── */}
      <div className="portfolio-days-pnl">
        <span className="days-pnl-label">Day's P&amp;L</span>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span className="days-pnl-val" style={{ color: pnlColor(daysPnl) }}>
            {daysPnl >= 0 ? "+" : ""}{fmt$(daysPnl)}
          </span>
          <span style={{ fontSize: "0.78rem", color: pnlColor(daysPnl), fontFamily: "'IBM Plex Mono', monospace" }}>
            {totalCurrentValue > 0 ? fmtPct((daysPnl / totalCurrentValue) * 100) : ""}
          </span>
        </div>
      </div>

      {/* ── Trade log ── */}
      <div className="section-eyebrow" style={{ marginTop: 24 }}>Trade Log</div>
      <div className="side-card" style={{ padding: 0 }}>
        {trades.length === 0 ? (
          <div className="portfolio-empty">No trades logged yet.</div>
        ) : (
          <table className="portfolio-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Ticker</th>
                <th>Side</th>
                <th className="num">Qty</th>
                <th className="num">Entry $</th>
                <th className="num">Value</th>
                <th>Notes</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id}>
                  <td style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>{t.trade_date}</td>
                  <td className="mono" style={{ fontWeight: 700 }}>{t.ticker}</td>
                  <td>
                    <span className="sentiment-badge" style={{
                      background: t.action === "BUY" ? "var(--bull-soft)" : "var(--bear-soft)",
                      color: t.action === "BUY" ? "var(--bull)" : "var(--bear)",
                    }}>{t.action}</span>
                  </td>
                  <td className="num">{t.quantity}</td>
                  <td className="num">{fmt$(t.entry_price)}</td>
                  <td className="num">{fmt$(t.quantity * t.entry_price)}</td>
                  <td style={{ fontSize: "0.78rem", color: "var(--text-dim)", maxWidth: 200 }}>{t.notes || "—"}</td>
                  <td>
                    <button onClick={() => handleDelete(t.id)} style={{ fontSize: "0.72rem", color: "var(--text-faint)", background: "none", border: "none", cursor: "pointer" }}>✕</button>
                  </td>
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

  // ---- Debate data, keyed by ticker ----
  const [debates, setDebates] = useState({});
  const closeStreamRef = useRef(null);

  useEffect(() => {
    return () => closeStreamRef.current?.();
  }, []);

  const [customNames, setCustomNames] = useState({});

  const startDebate = (symbol, companyName) => {
    closeStreamRef.current?.();
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

  // Portfolio trades now live in Supabase — no local state needed here.
  // The Portfolio component manages its own Supabase reads/writes.
  // Verdict page still gets a lightweight "add to portfolio" callback
  // that writes directly to Supabase and shows a toast.
  const handleAdd = async (rec) => {
    const { error } = await insertTrade({
      ticker: rec.symbol,
      company_name: rec.name,
      action: rec.action,
      quantity: rec.quantity || 0,
      entry_price: rec.entry_price || 0,
      notes: rec.notes || `${rec.action} — ${rec.confidence}% confidence. ${rec.sizing}`,
      trade_date: new Date().toISOString().slice(0, 10),
    });
    if (!error) {
      setToast(`${rec.action === "BUY" ? "Buy" : "Sell"} ${rec.symbol} — logged to portfolio`);
      setTimeout(() => setToast(null), 2600);
    }
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
          <Verdict symbol={activeSymbol} debate={activeDebate} onBack={() => setPage("debate")} portfolio={[]} onAdd={handleAdd} />
        )}
        {page === "portfolio" && <Portfolio />}
      </div>
      {toast && <div className="toast"><Check size={16} /> {toast}</div>}
    </div>
  );
}
