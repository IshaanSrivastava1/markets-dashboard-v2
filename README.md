# Markets Dashboard V2

A redesigned home for my market-tracking projects: a light ivory-and-gold
theme with a cursor-following glow, plus a dark mode. The original dashboard
stays online, untouched, as an archive:
<https://ishaansrivastava1.github.io/markets-dashboard/>.

- **Current projects:** Equity Charts, the live charting app
  (<https://equity-charts.onrender.com>).
- **Archived projects:** the Gold Arbitrage Tracker (final snapshot,
  restyled), the Gold (GC) June 2026 settlement odds, and the Micron (MU)
  EMA tracker. All three are frozen; nothing here fetches new data.

## How it's built

Everything is static and served by GitHub Pages from `docs/`.

- `build.py` writes `docs/index.html` from the frozen CSVs in `data/`
  (charts via `charts.py`, Plotly).
- `tools/restyle_arb.py` turned the frozen tracker snapshot
  (`source/arb_snapshot.html`) into `docs/arb.html` on the new theme, and
  checks that its text and chart data are unchanged.
- `docs/assets/`: `theme.css` (colors, type, layout for light and dark),
  `theme.js` (toggle and chart colors), `background.js` (the glow, still for
  people who turn off animations), `tabs.js` (Current / Archived tabs and
  `#arb` / `#gold` / `#mu` links).

No page on this site may contain an em dash; both build scripts check.

## Rebuild after editing

Type these in the Terminal app:

```
cd "/Users/ish1/Desktop/Code Projects/Markets Dashboard V2"
venv/bin/python3 build.py
venv/bin/python3 tools/restyle_arb.py
open docs/index.html
```

Then `git add -A && git commit -m "..." && git push` to publish.
