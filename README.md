# PulseShiftAI — Debate Engine (Phase 0: UI mockup)

This is the working frontend mockup from the Director pitch planning, running
as a real local app. Right now it uses **mock data only** — no backend, no
API keys needed. The goal of this step is just to confirm the UI runs and
looks/feels right on your own machine before we wire it to real data.

## Prerequisites

You need **Node.js** (v18 or newer — this was built and tested with v22).
Check what you have installed:

```
node -v
npm -v
```

If `node -v` fails, install the LTS version from https://nodejs.org and
re-open your terminal.

## Run it

1. Unzip this folder so it sits inside `Desktop/PulseShift_Debate_Engine/`
   (or wherever you'd like — the folder is self-contained).
2. Open a terminal in this folder. In VS Code: `File > Open Folder...`,
   select this folder, then open a terminal with `` Ctrl+` `` (or `Cmd+` `` on Mac).
3. Install dependencies (this downloads everything into a `node_modules`
   folder, which was deliberately NOT included in the zip to keep it small):

   ```
   npm install
   ```

4. Start the dev server:

   ```
   npm run dev
   ```

5. Vite will print a local URL, typically `http://localhost:5173`. Open that
   in your browser.

## What you should see

- **Dashboard**: market mood banner with the animated pulse line, an
  11-sector sentiment strip, and a 6-ticker watchlist with a "Debate this
  stock" button on each card.
- Click **Debate this stock** on NVDA, then **Run debate** in the bottom-right
  card. Watch the transcript reveal one exchange at a time, each one
  highlighted/glowing while it's the "current" turn, with the live conviction
  meters and chart updating alongside.
- After all exchanges complete, a gold **Moderator Verdict** card appears —
  click **View full verdict**.
- On the Verdict page, click **Buy** (or **Sell**, depending on the ticker) to
  add the position to the mock portfolio, then check the **Portfolio** tab in
  the top nav.
- Go back to Dashboard and try a couple of other tickers (XOM is a good one —
  it resolves to a SELL verdict, unlike NVDA's BUY).

## Project structure

- `src/App.jsx` — the entire app (mockup component, mock data, debate
  generator). This is the file we'll progressively rewire to call a real
  backend in later phases.
- `src/index.css` — minimal global reset. All the real styling lives inside
  `App.jsx` in a `<style>` block, scoped under the `.psai` class.
- `src/main.jsx` — standard Vite/React entry point, unchanged from the
  template.

## Useful commands

- `npm run dev` — local dev server with hot reload (use this while working).
- `npm run build` — production build into `dist/` (sanity-check that
  everything compiles; not needed for day-to-day development).

## Next steps (later phases)

This mockup currently generates its own "debate" content from hardcoded mock
data (`WATCHLIST`, `NVDA_DEBATE`, `generateDebate()` near the top of
`App.jsx`). Phase 1+ will build a Python backend that produces real debate
transcripts, and Phase 4 will replace these mock data calls in `App.jsx` with
`fetch()` / `EventSource` calls to that backend — without needing to touch any
of the styling or layout.
