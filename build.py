#!/usr/bin/env python3
"""Build docs/index.html for Markets Dashboard V2.

Everything on the page is static: the current project is a link to the live
Equity Charts app, and the archived projects render from the frozen CSVs in
data/ (no network calls). Run after editing copy or styles:

    venv/bin/python3 build.py && open docs/index.html
"""
import csv
import html
import json
import re
from pathlib import Path

import charts

BASE_DIR = Path(__file__).resolve().parent
OUT_FILE = BASE_DIR / "docs" / "index.html"
ARB_LOG = BASE_DIR / "data" / "arb_log.csv"
ARB_SNAPSHOT = BASE_DIR / "source" / "arb_snapshot.html"

PLOTLY_JS = "https://cdn.plot.ly/plotly-4.1.1.min.js"
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800"
             "&family=IBM+Plex+Mono:wght@400;500;600"
             "&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400&display=swap")
EQUITY_CHARTS_URL = "https://equity-charts.onrender.com"
OLD_DASHBOARD_URL = "https://ishaansrivastava1.github.io/markets-dashboard/"

# Applies a stored theme choice before first paint (no light/dark flash).
THEME_BOOT = ('<script>try{var t=localStorage.getItem("theme");'
              'if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}'
              'catch(e){}</script>')

TOGGLE = """<button id="theme-toggle" class="icon-button" type="button" aria-label="Dark mode" aria-pressed="false" title="Switch to dark mode">
          <svg class="icon-moon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="currentColor"/></svg>
          <svg class="icon-sun" viewBox="0 0 24 24" fill="none" aria-hidden="true" hidden><circle cx="12" cy="12" r="4" fill="currentColor"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="light dark">
  <title>Markets Dashboard</title>
  <meta name="description" content="Ishaan Srivastava's market tools: the live Equity Charts app plus archived trackers for gold prediction markets and Micron.">
  {{THEME_BOOT}}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{{FONTS_URL}}">
  <link rel="stylesheet" href="assets/theme.css">
  <script src="{{PLOTLY_JS}}" charset="utf-8"></script>
</head>
<body>
  <canvas id="glow" aria-hidden="true"></canvas>
  <div class="shell">
    <header class="masthead">
      <div class="titles">
        <span class="eyebrow">Ishaan Srivastava &middot; Version 2</span>
        <h1>Markets Dashboard</h1>
        <p class="lede">Tools I built to watch markets: a live charting app that maps support and resistance and scans every US stock and ETF against its 20-day EMA, plus the archived trackers for gold prediction markets and Micron that came before it.</p>
      </div>
      {{TOGGLE}}
    </header>

    <section class="tape" aria-label="Key figures">
      <div><span class="label">Equity Charts</span><span class="value"><span class="dot" aria-hidden="true"></span>Live &middot; ~12,300 symbols</span></div>
      <div><span class="label">Arb tracker &middot; {{ARB_SPAN}}</span><span class="value">{{ARB_SIGHTINGS}} first sightings</span></div>
      <div><span class="label">GC June 2026 settle</span><span class="value">{{GOLD_WINNER}} &middot; {{GOLD_PCT}}</span></div>
      <div><span class="label">MU close &middot; {{MU_LAST_SHORT}}</span><span class="value">${{MU_CLOSE}}</span></div>
    </section>

    <div class="tabs" role="tablist" aria-label="Projects">
      <button class="tab" role="tab" id="tab-current" aria-controls="current" aria-selected="true" type="button">Current projects <span class="count">1</span></button>
      <button class="tab" role="tab" id="tab-archived" aria-controls="archived" aria-selected="false" tabindex="-1" type="button">Archived projects <span class="count">3</span></button>
    </div>

    <main>
      <section id="current" class="panel" role="tabpanel" aria-labelledby="tab-current">
        <article class="card feature" id="equity-charts">
          <div class="card-head">
            <span class="eyebrow">Web app &middot; FastAPI + Lightweight Charts</span>
            <div class="meta"><span class="pill live">Live</span><span class="pill">Updated Oct 2026</span></div>
          </div>
          <h2>Equity Charts</h2>
          <p class="lede">A charting terminal for every US-listed stock and ETF: live prices, indicators and drawing tools, plus written support and resistance analysis that runs entirely in code, with no AI service involved.</p>
          <div class="feature-grid">
            <div><span class="label">Levels</span><p>Shaded support and resistance zones, each explained in writing: how many times price reacted there, when it last did, and what else lines up at that price.</p></div>
            <div><span class="label">Fibonacci</span><p>Drag from a swing low to a swing high to draw retracement levels, or press Auto to place them on the latest major swing.</p></div>
            <div><span class="label">20-day EMA scanner</span><p>After every close it checks about 12,300 stocks and ETFs. Liquid names that close below their 20-day EMA arrive in one Discord digest.</p></div>
            <div><span class="label">Charting</span><p>Streaming prices, EMA, SMA, Bollinger Bands, RSI, MACD, trendlines, and a fundamentals view for individual stocks.</p></div>
          </div>
          <div class="actions">
            <a class="button" href="{{EQUITY_CHARTS_URL}}" target="_blank" rel="noopener noreferrer">Open Equity Charts <span aria-hidden="true">&#8599;</span></a>
            <span class="note">Free hosting: after a quiet spell, the first load takes 30 to 60 seconds.</span>
          </div>
        </article>
      </section>

      <section id="archived" class="panel" role="tabpanel" aria-labelledby="tab-archived" hidden>
        <article class="card" id="arb">
          <div class="card-head">
            <h3>Gold Arbitrage Tracker</h3>
            <div class="meta"><span class="pill gold">V3.9</span><span class="pill">{{ARB_SPAN}}</span></div>
          </div>
          <p>Scanned every open gold-price market on Polymarket and Kalshi, normalized them into one schema, and flagged combinations of contracts that were logically mispriced against each other (net of fees), with an AI agent writing a daily brief on top. The page is its final snapshot and no longer updates.</p>
          <div class="stats">
            <div class="stat"><span class="value">{{ARB_CONTRACTS}}</span><span class="label">Contracts in final scan</span></div>
            <div class="stat"><span class="value">{{ARB_SIGHTINGS}}</span><span class="label">First sightings logged</span></div>
            <div class="stat"><span class="value">2</span><span class="label">Platforms compared</span></div>
          </div>
          <div class="actions"><a class="button quiet" href="arb.html">Open the archived tracker <span aria-hidden="true">&rarr;</span></a></div>
        </article>

        <article class="card" id="gold">
          <div class="card-head">
            <h3>Gold (GC) June 2026 settlement odds</h3>
            <div class="meta"><span class="pill gold">V2</span><span class="pill">{{GOLD_SPAN}}</span></div>
          </div>
          <p>The purpose of this tracker was to find correlations in the movements of prediction market odds to the movements of the underlying asset, and send a summary of these daily changes to myself for evaluation.</p>
          <div class="chart-grid">
            <div class="chart" data-chart data-palette='{{GOLD_PALETTE}}'>{{GOLD_CHART}}</div>
            {{GOLD_SUMMARY}}
          </div>
        </article>

        <article class="card" id="mu">
          <div class="card-head">
            <h3>Micron (MU) EMA trend tracker</h3>
            <div class="meta"><span class="pill gold">V2</span><span class="pill">{{MU_SPAN}}</span></div>
          </div>
          <p>This tracker was created to send automated alerts to myself whenever MU broke below its 9-day or 21-day EMA, since I was using these metrics to trade this ticker at the time.</p>
          <div class="chart-grid">
            <div class="chart" data-chart data-palette='{{MU_PALETTE}}'>{{MU_CHART}}</div>
            {{MU_SUMMARY}}
          </div>
        </article>
      </section>
    </main>

    <footer class="footer">
      <span>Markets Dashboard V2 &middot; Ishaan Srivastava</span>
      <span>Data: Alpaca (Equity Charts) &middot; Polymarket, Kalshi, Yahoo Finance (archived)</span>
      <span>Informational only, not financial advice</span>
      <span>Previous version: <a href="{{OLD_DASHBOARD_URL}}">original dashboard (archived)</a></span>
    </footer>
  </div>
  <script src="assets/theme.js"></script>
  <script src="assets/background.js"></script>
  <script src="assets/tabs.js"></script>
</body>
</html>
"""


def arb_facts():
    with ARB_LOG.open() as f:
        rows = list(csv.DictReader(f))
    snapshot = ARB_SNAPSHOT.read_text()
    m = re.search(r"<div class='num'>(\d+)</div><div class='lab'>contracts scanned", snapshot)
    return {
        "sightings": len(rows),
        "first": rows[0]["seen_at"][:10],
        "last": rows[-1]["seen_at"][:10],
        "contracts": m.group(1) if m else "90",
    }


def span(first, last):
    """'Jul–Oct 2026' within one year, 'Dec 2025–Jul 2026' across years."""
    a, b = charts.fmt_month(first), charts.fmt_month(last)
    if a[-4:] == b[-4:]:
        return "%s–%s" % (a[:3], b)
    return "%s–%s" % (a, b)


def chart_html(fig, div_id):
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id,
                       config={"displayModeBar": False, "responsive": True})


def main():
    gold_rows, gold_labels = charts.read_gold()
    mu_rows = charts.read_mu()
    mu_emas = charts.compute_emas(mu_rows)
    gold = charts.gold_facts(gold_rows, gold_labels)
    mu = charts.mu_facts(mu_rows)
    arb = arb_facts()

    values = {
        "THEME_BOOT": THEME_BOOT,
        "FONTS_URL": html.escape(FONTS_URL),
        "PLOTLY_JS": PLOTLY_JS,
        "TOGGLE": TOGGLE,
        "EQUITY_CHARTS_URL": EQUITY_CHARTS_URL,
        "OLD_DASHBOARD_URL": OLD_DASHBOARD_URL,
        "ARB_SPAN": span(arb["first"], arb["last"]),
        "ARB_SIGHTINGS": "{:,}".format(arb["sightings"]),
        "ARB_CONTRACTS": arb["contracts"],
        "GOLD_WINNER": html.escape(gold["winner"]),
        "GOLD_PCT": "%.0f%%" % gold["winner_pct"],
        "GOLD_SPAN": span(gold["first"], gold["last"]),
        "GOLD_PALETTE": json.dumps(charts.gold_palette(gold_labels)),
        "GOLD_CHART": chart_html(charts.gold_figure(gold_rows, gold_labels), "gold-chart"),
        "GOLD_SUMMARY": charts.gold_summary(gold_rows, gold_labels),
        "MU_SPAN": span(mu["first"], mu["last"]),
        "MU_LAST_SHORT": charts.fmt_date(mu["last"]).rsplit(",", 1)[0],
        "MU_CLOSE": format(mu["close"], ",.2f"),
        "MU_PALETTE": json.dumps(charts.MU_PALETTE),
        "MU_CHART": chart_html(charts.mu_figure(mu_rows, mu_emas), "mu-chart"),
        "MU_SUMMARY": charts.mu_summary(mu_rows, mu_emas),
    }
    page = PAGE
    for key, value in values.items():
        page = page.replace("{{%s}}" % key, value)

    leftover = re.findall(r"\{\{[A-Z_]+\}\}", page)
    assert not leftover, "unfilled placeholders: %s" % leftover
    # The dashboard's standing rule: no em dashes anywhere on the page.
    assert "—" not in page and "&mdash;" not in page, "em dash found in output"

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page)
    print("Wrote %s (%s bytes)" % (OUT_FILE, format(len(page), ",")))


if __name__ == "__main__":
    main()
