# api/main.py
"""
FastAPI layer for PulseShiftAI's Debate Arena pitch demo.

Run with:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    GET  /api/watchlist          -> per-ticker summary cards (Dashboard)
    GET  /api/sector-snapshot    -> sector mood/heatmap (Dashboard)
    POST /api/dashboard/refresh  -> clear the 15-min snapshot cache
    GET  /api/debate/{ticker}    -> SSE stream of a full Bull/Bear/Moderator debate

No auth, no DB persistence (mock portfolio etc. is a documented v2 item) \u2014
scoped deliberately narrow to get the live pitch demo working end to end.
"""

from __future__ import annotations
import asyncio
import json
import queue
import threading
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from api.config import WATCHLIST, HOMEPAGE_FRESHNESS_DAYS, resolve_ticker_from_company
from api.dashboard import get_watchlist, get_sector_snapshot, clear_cache
from debate_engine.orchestrator import run_debate_stream

app = FastAPI(title="PulseShiftAI Debate Arena API")

# Vite's default dev server port. Adjust/add origins if your frontend runs
# elsewhere (e.g. add your deployed URL before the Director pitch).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

_TICKER_LOOKUP = {t: c for t, c in WATCHLIST}


# ---- Dashboard ---------------------------------------------------------------
@app.get("/api/watchlist")
def watchlist():
    """Per-ticker summary cards: sentiment, RSI, weekly % change. Cached ~15min."""
    return {"items": get_watchlist()}


@app.get("/api/sector-snapshot")
def sector_snapshot(freshness_days: int = HOMEPAGE_FRESHNESS_DAYS):
    """Sector mood index + heatmap, same computation as the Streamlit dashboard. Cached ~15min."""
    return get_sector_snapshot(freshness_days)


@app.post("/api/dashboard/refresh")
def dashboard_refresh():
    """Clear the snapshot cache (equivalent of Home.py's 'Refresh snapshot' button)."""
    clear_cache()
    return {"status": "ok"}


# ---- Debate Arena (SSE) -----------------------------------------------------
_SENTINEL = object()  # marks "producer thread is done" on the bridge queue


def _run_debate_in_thread(ticker: str, company_name: str, q: "queue.Queue") -> None:
    """
    Runs in a background thread. run_debate_stream() makes blocking OpenAI/
    Polygon/news calls between each yield \u2014 if it were driven directly
    inside an `async def`, those blocking calls would freeze the asyncio
    event loop for their entire duration, which prevents Starlette from
    flushing any SSE bytes to the client until the whole generator finishes
    (this was the original bug: the browser saw nothing until the very end,
    even though the generator was correctly yielding turn by turn).
    Running it here, in a real OS thread, keeps the event loop free so each
    item placed on `q` can be flushed to the client immediately.
    """
    try:
        for event in run_debate_stream(ticker, company_name):
            q.put(event)
    except Exception as exc:  # noqa: BLE001 - surfaced to the client as an SSE error event
        q.put({"type": "error", "message": str(exc)})
    finally:
        q.put(_SENTINEL)


async def _debate_event_stream(ticker: str, company_name: str) -> AsyncIterator[dict]:
    """
    Adapts orchestrator.run_debate_stream()'s synchronous, blocking generator
    to async SSE events without blocking the event loop (see
    _run_debate_in_thread's docstring). Each item becomes one `event: <type>`
    message with the rest of the payload as JSON `data`, e.g.:

        event: turn
        data: {"turn": {...}, "conviction": {...}}

    The frontend should open an EventSource on this endpoint and listen for
    "turn" events to progressively reveal each exchange, then "verdict" for
    the final card. The terminal "done" event carries the full result as a
    fallback for clients that just want to render everything at once.
    """
    q: "queue.Queue" = queue.Queue()
    thread = threading.Thread(target=_run_debate_in_thread, args=(ticker, company_name, q), daemon=True)
    thread.start()

    loop = asyncio.get_event_loop()
    while True:
        # q.get() is itself a blocking call, so it also has to be offloaded
        # to a thread (run_in_executor) rather than called directly here \u2014
        # otherwise we'd reintroduce the exact same event-loop-blocking bug
        # one level up.
        event = await loop.run_in_executor(None, q.get)
        if event is _SENTINEL:
            return
        event_type = event.pop("type")
        yield {"event": event_type, "data": json.dumps(event)}


# ---- Portfolio price feed ---------------------------------------------------
@app.get("/api/price/{ticker}")
def price(ticker: str):
    """
    Latest weekly close price for a single ticker, via Polygon.
    Used by the Portfolio tab to mark positions to market without running
    the full evidence pipeline. Returns {ticker, price, pct_change, as_of}.
    Lightweight — one Polygon OHLCV call, no news fetch, no sentiment.
    """
    from debate_engine.evidence import get_technical_signal
    ticker = ticker.upper()
    tech = get_technical_signal(ticker)
    if tech.get("close") is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price for '{ticker}'. Polygon may not have recent data."
        )
    return {
        "ticker": ticker,
        "price": tech["close"],
        "pct_change": tech["pct_change"],
        "as_of": tech["as_of"],
    }


@app.get("/api/resolve/{query}")
def resolve(query: str):
    """
    Resolve a free-text company name or ticker (e.g. "Microsoft" or "MSFT")
    to a (ticker, official_name) pair, for the custom-ticker input on the
    Dashboard. Checks the fixed WATCHLIST first (no network call) before
    falling back to a live Polygon search.
    """
    q = query.strip().upper()
    if q in _TICKER_LOOKUP:
        return {"ticker": q, "company_name": _TICKER_LOOKUP[q]}

    ticker, official_name = resolve_ticker_from_company(query.strip())
    if ticker is None:
        raise HTTPException(status_code=404, detail=f"Could not resolve '{query}' to a ticker.")
    return {"ticker": ticker, "company_name": official_name or ticker}


@app.get("/api/debate/{ticker}")
async def debate(ticker: str, company_name: str = None):
    """
    SSE stream of a full Bull/Bear/Moderator debate for `ticker`.

    For the fixed WATCHLIST entries, company_name is looked up automatically.
    For any other ticker (a custom lookup via /api/resolve), the frontend
    must pass `company_name` as a query param \u2014 resolution happens once,
    client-side via /api/resolve, rather than repeating it here on every
    debate request.
    """
    ticker = ticker.upper()
    resolved_name = _TICKER_LOOKUP.get(ticker) or company_name
    if resolved_name is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown ticker '{ticker}'. Either use a WATCHLIST ticker or pass ?company_name= "
                   f"(use /api/resolve/{{query}} to look one up first).",
        )
    return EventSourceResponse(_debate_event_stream(ticker, resolved_name))
