#!/usr/bin/env python3
"""
pre_warm.py  -  run this ~5 minutes before the Director pitch.

What it does: hits /api/watchlist and /api/sector-snapshot once each, which
fills the 15-minute backend cache. That means when you open the browser in
the room, the Dashboard renders in under a second from cache rather than
making ~7 live network calls cold (which could take 15-25 seconds and look
like it's broken).

Run from the project root while uvicorn is already running:
    python pre_warm.py

Optional: pass a different base URL if uvicorn is on another port:
    python pre_warm.py http://localhost:8001
"""

import sys, time, urllib.request, json

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"

def fetch(label, url):
    t0 = time.time()
    print(f"  {label:<22s} ... ", end="", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = json.loads(r.read())
            elapsed = time.time() - t0
            # Quick sanity: check we actually got data back, not an empty response
            if label == "watchlist":
                n = len(data.get("items", []))
                print(f"OK ({n} tickers, {elapsed:.1f}s)")
            elif label == "sector-snapshot":
                n = len(data.get("by_sector", []))
                print(f"OK ({n} sectors, {elapsed:.1f}s)")
            else:
                print(f"OK ({elapsed:.1f}s)")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAILED after {elapsed:.1f}s: {e}")
        return False
    return True

print(f"\nPulseShiftAI pre-warm  →  {BASE}\n")
ok = all([
    fetch("watchlist",       f"{BASE}/api/watchlist"),
    fetch("sector-snapshot", f"{BASE}/api/sector-snapshot"),
])

if ok:
    print("\nCache is warm. Open the browser now — Dashboard will load instantly.")
    print("Cache TTL: 15 minutes. Re-run this script if uvicorn was restarted.")
else:
    print("\nOne or more requests failed — check that uvicorn is running and try again.")
    sys.exit(1)
