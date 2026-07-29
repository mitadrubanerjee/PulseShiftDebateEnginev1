// src/api.js
/*
 * Thin client for the FastAPI backend (api/main.py). Three real backend
 * calls, matching the three endpoints that exist:
 *   GET  /api/watchlist
 *   GET  /api/sector-snapshot
 *   GET  /api/debate/{ticker}   (Server-Sent Events)
 *
 * Base URL is read from VITE_API_BASE_URL if set (e.g. for a deployed
 * backend), otherwise defaults to localhost:8000 for local dev. Set this
 * in a .env file at the pulseshift-app root if you ever run the API
 * somewhere other than localhost:8000 (see Vite's env docs \u2014 the var
 * MUST be prefixed VITE_ to be exposed to client code).
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * GET /api/watchlist
 * Returns: { items: [{ ticker, company_name, sector, sentiment_score,
 *                       sentiment_label, rsi, pct_change }, ...] }
 */
export async function fetchWatchlist() {
  const res = await fetch(`${API_BASE_URL}/api/watchlist`);
  if (!res.ok) throw new Error(`fetchWatchlist failed: ${res.status}`);
  const data = await res.json();
  return data.items;
}

/**
 * GET /api/sector-snapshot
 * Returns: { mood: {avg_score, std_score, label, n_articles},
 *            by_sector: [{sector, avg_score, std_score, label, n_items}, ...] }
 */
export async function fetchSectorSnapshot() {
  const res = await fetch(`${API_BASE_URL}/api/sector-snapshot`);
  if (!res.ok) throw new Error(`fetchSectorSnapshot failed: ${res.status}`);
  return res.json();
}

/**
 * POST /api/dashboard/refresh \u2014 clears the backend's 15-min snapshot cache.
 */
export async function refreshDashboard() {
  const res = await fetch(`${API_BASE_URL}/api/dashboard/refresh`, { method: "POST" });
  if (!res.ok) throw new Error(`refreshDashboard failed: ${res.status}`);
  return res.json();
}

/**
 * GET /api/resolve/{query} \u2014 resolves a free-text company name or ticker
 * (e.g. "Microsoft" or "MSFT") to {ticker, company_name}. Checks the fixed
 * watchlist first (instant, no network), falls back to a live Polygon
 * search otherwise. Throws if nothing could be resolved.
 */
export async function resolveTicker(query) {
  const res = await fetch(`${API_BASE_URL}/api/resolve/${encodeURIComponent(query)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Couldn't find a match for "${query}"`);
  }
  return res.json(); // { ticker, company_name }
}

/**
 * Opens an SSE connection to GET /api/debate/{ticker} and streams events
 * back through the provided callbacks as they arrive in real time (this is
 * the actual fix for the "everything appears at once" bug \u2014 the backend
 * now genuinely flushes each event as soon as it's produced; this function
 * is just the client-side listener for that).
 *
 * Event types emitted by the backend, in order: "evidence", "turn" (\u00d7
 * max_exchanges), "verdict", "done". An "error" event is also possible if
 * something fails server-side mid-debate.
 *
 * callbacks: {
 *   onEvidence(evidence),
 *   onTurn(turn, conviction),   // conviction is the running {turn, bull, bear} point
 *   onVerdict(verdict),
 *   onDone(result),             // full {evidence, turns, conviction, verdict}
 *   onError(message),
 * }
 *
 * Returns a close() function \u2014 call it to abort the stream early (e.g. if
 * the user navigates away mid-debate), since EventSource otherwise keeps
 * the connection open indefinitely.
 */
export function streamDebate(ticker, companyName, callbacks) {
  const url = companyName
    ? `${API_BASE_URL}/api/debate/${ticker}?company_name=${encodeURIComponent(companyName)}`
    : `${API_BASE_URL}/api/debate/${ticker}`;
  const es = new EventSource(url);

  es.addEventListener("evidence", (e) => {
    const data = JSON.parse(e.data);
    callbacks.onEvidence?.(data.evidence);
  });

  es.addEventListener("turn", (e) => {
    const data = JSON.parse(e.data);
    callbacks.onTurn?.(data.turn, data.conviction);
  });

  es.addEventListener("verdict", (e) => {
    const data = JSON.parse(e.data);
    callbacks.onVerdict?.(data.verdict);
  });

  es.addEventListener("done", (e) => {
    const data = JSON.parse(e.data);
    callbacks.onDone?.(data.result);
    es.close(); // server is finished; no need to keep the connection open
  });

  es.addEventListener("error", (e) => {
    // Two distinct cases share this listener: (1) the backend explicitly
    // sent an `event: error` (e.data is set, parseable), or (2) the
    // underlying connection itself dropped/failed (e.data is undefined).
    let message = "Connection to debate stream lost.";
    if (e.data) {
      try {
        message = JSON.parse(e.data).message || message;
      } catch {
        /* not JSON, fall through to default message */
      }
    }
    callbacks.onError?.(message);
    es.close();
  });

  return () => es.close();
}
