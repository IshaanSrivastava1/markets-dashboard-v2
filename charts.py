"""Archived chart data for Markets Dashboard V2: read the frozen CSVs and build
theme-neutral Plotly figures plus their HTML side tables.

Adapted from the original dashboard's gold_tracker.py and mu_tracker.py with
every network call removed: V2 only renders what those trackers recorded
before they were archived. Figures use transparent backgrounds and no
template; theme.js colors fonts, grids and series from the CSS tokens.
"""
import csv
import html
import re
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent
GOLD_CSV = BASE_DIR / "data" / "gold_history.csv"
MU_CSV = BASE_DIR / "data" / "mu_history.csv"

GOLD_MARKET_URL = "https://polymarket.com/event/gc-settle-jun-2026"
MU_EMA_PERIODS = (9, 21, 48)

MONO = '"IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace'
# Light-mode starting colors; theme.js swaps in the tokens for the active theme.
SERIES_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK_LIGHT = "#221c12"


def fmt_date(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %-d, %Y")


def fmt_month(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %Y")


def _base_layout(fig, height=400):
    fig.update_layout(
        template="none",
        height=height,
        margin=dict(l=50, r=12, t=12, b=36),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=MONO, size=11, color="#5b5142"),
        hovermode="x unified",
        hoverlabel=dict(font=dict(family=MONO, size=12)),
        legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom",
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11), itemwidth=30),
        xaxis=dict(showgrid=False, showline=True, linewidth=1, ticks="",
                   showspikes=True, spikemode="across", spikethickness=1, spikedash="solid"),
        yaxis=dict(showgrid=True, gridwidth=1, zeroline=False, showline=False, ticks=""),
    )


# ------------------------------------------------------------------- gold

def bracket_sort_key(label):
    nums = [float(n.replace(",", "")) for n in re.findall(r"[\d,]+(?:\.\d+)?", label)]
    if label.startswith("<"):
        return -1
    if label.startswith(">"):
        return 1_000_000
    return nums[0] if nums else 0


def bracket_name(label):
    """'$3,800-$4,200' -> '$3,800–$4,200'; '<$3,800' -> 'Under $3,800'."""
    if label.startswith("<"):
        return "Under " + label[1:]
    if label.startswith(">"):
        return "Over " + label[1:]
    return label.replace("-", "–")


def read_gold():
    with GOLD_CSV.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames
    labels = sorted((c for c in fields if c not in ("date", "volume")), key=bracket_sort_key)
    return rows, labels


def gold_figure(rows, labels):
    dates = [r["date"] for r in rows]
    fig = go.Figure()
    for i, label in enumerate(labels):
        values = [float(r[label]) * 100 if r.get(label) else None for r in rows]
        fig.add_trace(go.Scatter(
            x=dates, y=values, name=bracket_name(label), mode="lines",
            connectgaps=False,
            line=dict(color=SERIES_LIGHT[i], width=2),
            hovertemplate="%{y:.1f}%",
        ))
    _base_layout(fig)
    fig.update_yaxes(range=[0, 100], ticksuffix="%", dtick=25)
    fig.update_xaxes(tickformat="%b %Y")
    return fig


def gold_palette(labels):
    return ["--series-%d" % (i + 1) for i in range(len(labels))]


def gold_summary(rows, labels):
    last = rows[-1]
    odds = [(i, label, float(last[label]) * 100) for i, label in enumerate(labels) if last.get(label)]
    winner = max(odds, key=lambda o: o[2])
    body = "".join(
        "<tr%s><td><span class='swatch s%d'></span>%s</td><td class='num'>%.1f%%</td></tr>"
        % (" class='lead'" if o is winner else "", o[0] + 1, html.escape(bracket_name(o[1])), o[2])
        for o in odds)
    return (
        "<div class='summary'>"
        "<span class='label'>Final recorded odds &middot; %s</span>"
        "<div class='big'>%s</div>"
        "<p class='muted'>The market settled in this bracket at %.0f%%.</p>"
        "<div class='table-wrap'><table class='data'>"
        "<tr><th>Bracket</th><th class='num'>Odds</th></tr>%s</table></div>"
        "<p class='muted'>Source: <a href='%s'>polymarket.com/event/gc-settle-jun-2026</a></p>"
        "</div>"
        % (fmt_date(last["date"]), html.escape(bracket_name(winner[1])), winner[2], body,
           GOLD_MARKET_URL))


def gold_facts(rows, labels):
    last = rows[-1]
    winner = max(labels, key=lambda l: float(last[l] or 0))
    return {
        "first": rows[0]["date"],
        "last": last["date"],
        "winner": bracket_name(winner),
        "winner_pct": float(last[winner]) * 100,
    }


# --------------------------------------------------------------------- MU

def read_mu():
    with MU_CSV.open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("open", "high", "low", "close"):
            r[k] = float(r[k])
        r["volume"] = int(float(r["volume"]))
    return rows


def compute_ema(closes, period):
    """Standard 2/(N+1) EMA, seeded with the SMA of the first `period` closes
    (the same method the original tracker used)."""
    ema = [None] * len(closes)
    if len(closes) < period:
        return ema
    ema[period - 1] = sum(closes[:period]) / period
    k = 2 / (period + 1)
    for i in range(period, len(closes)):
        ema[i] = (closes[i] - ema[i - 1]) * k + ema[i - 1]
    return ema


def compute_emas(rows):
    closes = [r["close"] for r in rows]
    return {p: compute_ema(closes, p) for p in MU_EMA_PERIODS}


def mu_figure(rows, emas):
    dates = [r["date"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=[r["close"] for r in rows], name="Close", mode="lines",
        line=dict(color=INK_LIGHT, width=2), hovertemplate="$%{y:,.2f}"))
    for i, p in enumerate(MU_EMA_PERIODS):
        fig.add_trace(go.Scatter(
            x=dates, y=emas[p], name="EMA %d" % p, mode="lines", connectgaps=False,
            line=dict(color=SERIES_LIGHT[i], width=2), hovertemplate="$%{y:,.2f}"))
    _base_layout(fig)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_xaxes(tickformat="%b %Y")
    return fig


MU_PALETTE = ["--ink", "--series-1", "--series-2", "--series-3"]


def mu_summary(rows, emas):
    today, prev = rows[-1], rows[-2]
    change = today["close"] - prev["close"]
    pct = change / prev["close"] * 100
    cls = "up" if change >= 0 else "down"
    sign = "+" if change >= 0 else "−"

    signals = []
    for fast, slow in ((9, 21), (21, 48)):
        pf, ps, tf, ts = emas[fast][-2], emas[slow][-2], emas[fast][-1], emas[slow][-1]
        if None in (pf, ps, tf, ts):
            continue
        if pf <= ps and tf > ts:
            signals.append("Bullish crossover: %d-day EMA crossed above the %d-day" % (fast, slow))
        elif pf >= ps and tf < ts:
            signals.append("Bearish crossover: %d-day EMA crossed below the %d-day" % (fast, slow))

    rows_html = ""
    for i, p in enumerate(MU_EMA_PERIODS):
        val = emas[p][-1]
        dist = (today["close"] - val) / val * 100
        rows_html += (
            "<tr><td><span class='swatch s%d'></span>EMA %d</td><td class='num'>$%s</td>"
            "<td class='num %s'>%s%.1f%%</td></tr>"
            % (i + 1, p, format(val, ",.2f"), "up" if dist >= 0 else "down",
               "+" if dist >= 0 else "−", abs(dist)))

    return (
        "<div class='summary'>"
        "<span class='label'>Last recorded close &middot; %s</span>"
        "<div class='big'>$%s</div>"
        "<p class='%s num'>%s$%s (%s%.2f%%) on the day</p>%s"
        "<div class='table-wrap'><table class='data'>"
        "<tr><th>Average</th><th class='num'>Value</th><th class='num'>Close vs</th></tr>%s</table></div>"
        "<p class='muted num'>Volume %s shares &middot; data: Yahoo Finance</p>"
        "</div>"
        % (fmt_date(today["date"]), format(today["close"], ",.2f"), cls, sign,
           format(abs(change), ",.2f"), sign, abs(pct),
           "".join("<p class='signal'>%s</p>" % s for s in signals), rows_html,
           format(today["volume"], ",")))


def mu_facts(rows):
    return {"first": rows[0]["date"], "last": rows[-1]["date"], "close": rows[-1]["close"]}
