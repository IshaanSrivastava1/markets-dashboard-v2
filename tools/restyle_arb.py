#!/usr/bin/env python3
"""One-time restyle of the frozen Gold Arbitrage Tracker page for V2.

Reads source/arb_snapshot.html (the final snapshot copied from the original
dashboard) and writes docs/arb.html with:
  - the V2 theme (assets/theme.css, glow background, light/dark toggle),
  - themed CSS for the page's existing class names,
  - the ladder chart wired to the theme's series tokens,
  - em dashes replaced (the dashboard's standing rule).
The page's text and chart data are checked to be otherwise unchanged.

    venv/bin/python3 tools/restyle_arb.py
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (shared head snippets: fonts, theme boot, toggle)

SRC = ROOT / "source" / "arb_snapshot.html"
OUT = ROOT / "docs" / "arb.html"

PAGE_CSS = """
    /* Archived tracker page on the V2 theme (tokens in assets/theme.css). */
    :root { --warn: #8f5f00; }
    @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --warn: #f0b443; } }
    :root[data-theme="dark"] { --warn: #f0b443; }

    body { font-size: 1rem; line-height: 1.55; }
    body > header, body > .stale-banner, body > .tiles, body > main, body > footer { position: relative; z-index: 1; }
    header { max-width: 1100px; margin: 0 auto; padding: 36px clamp(16px, 4vw, 20px) 8px; padding-right: 76px; }
    header h1 { font-size: clamp(2rem, 4.4vw, 2.9rem); margin: 0 0 8px; }
    header h1 .muted { font-family: var(--font-mono); font-size: 0.85rem; font-weight: 500; letter-spacing: 0.04em; vertical-align: middle; color: var(--ink-2); }
    header p { margin: 0; color: var(--ink-2); font-family: var(--font-mono); font-size: 0.8rem; max-width: none; }
    header a { color: var(--ink); }
    #theme-toggle { position: absolute; top: 36px; right: clamp(16px, 4vw, 20px); }
    main { max-width: 1100px; margin: 0 auto; padding: 20px clamp(16px, 4vw, 20px); display: flex; flex-direction: column; gap: 24px; }
    section {
      background: var(--glass); border: 1px solid var(--rule); border-radius: 18px;
      -webkit-backdrop-filter: blur(18px) saturate(1.15); backdrop-filter: blur(18px) saturate(1.15);
      box-shadow: var(--shadow); padding: clamp(18px, 3vw, 26px);
    }
    section h2 { margin: 0 0 10px; font-size: 1.45rem; }
    .explain { color: var(--ink-2); font-size: 0.98rem; max-width: 72ch; margin: 0 0 6px; }
    .tablewrap { overflow-x: auto; }
    table { border-collapse: collapse; margin: 8px 0; font-family: var(--font-mono); font-size: 0.78rem; width: 100%; }
    th, td { text-align: left; padding: 6px 12px 6px 0; vertical-align: top; border-bottom: 1px solid var(--rule); }
    th { color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.7rem; }
    tr.group-head td { background: var(--gold-soft); color: var(--ink); font-weight: 600; padding: 8px 12px; }
    tr.group-head .gh-plat { color: var(--gold-ink); }
    .muted { color: var(--muted); font-size: 0.9rem; }
    .warn { color: var(--warn); }
    .edge { font-size: 1.05rem; font-weight: 700; }
    .num-cell { font-variant-numeric: tabular-nums; }
    .empty { color: var(--muted); padding: 12px 0; margin: 0; }
    footer { max-width: 1100px; margin: 0 auto; padding: 8px clamp(16px, 4vw, 20px) 48px; color: var(--ink-2); font-family: var(--font-mono); font-size: 0.75rem; }
    .tiles {
      max-width: 1100px; margin: 18px auto 0; padding: 0 clamp(16px, 4vw, 20px);
      display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px;
    }
    .tile {
      background: var(--glass); border: 1px solid var(--rule); border-radius: 14px; padding: 12px 16px;
      -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px);
    }
    .tile .num { font-family: var(--font-display); font-size: 1.6rem; font-weight: 750; letter-spacing: -0.02em; color: var(--ink); }
    .tile .lab { font-family: var(--font-mono); color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .stale-banner {
      max-width: calc(1100px - 40px); margin: 18px auto 0; padding: 10px 16px; border-radius: 12px;
      background: var(--gold-soft); border: 1px solid color-mix(in srgb, var(--gold) 55%, transparent);
      color: var(--ink); font-size: 0.92rem;
    }
    @media (max-width: 1140px) { .stale-banner { margin-left: clamp(16px, 4vw, 20px); margin-right: clamp(16px, 4vw, 20px); } }

    /* opportunity + history cards */
    .opp-list, .hist-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
    .opp-card, .hist-card { background: var(--glass-strong); border: 1px solid var(--rule); border-radius: 12px; padding: 14px 16px; }
    .opp-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
    .cap-num { font-family: var(--font-display); font-size: 1.55rem; font-weight: 750; line-height: 1; }
    .cap-lab { display: block; color: var(--muted); font-family: var(--font-mono); font-size: 0.7rem; text-align: right; margin-top: 2px; }
    .opp-legs, .hist-legs { display: flex; flex-direction: column; gap: 8px; margin: 12px 0; }
    .hist-legs { margin: 0; gap: 5px; }
    .leg { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    .side { font-family: var(--font-mono); font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em; padding: 2px 8px; border-radius: 6px; white-space: nowrap; }
    .side-yes { background: color-mix(in srgb, var(--up) 14%, transparent); color: var(--up); }
    .side-no { background: color-mix(in srgb, var(--down) 14%, transparent); color: var(--down); }
    .leg-desc { flex: 1; min-width: 220px; }
    .btn {
      border: 1px solid var(--rule-strong); border-radius: 999px; padding: 4px 12px; font-family: var(--font-mono);
      font-size: 0.75rem; color: var(--ink); background: var(--glass-strong); text-decoration: none; white-space: nowrap;
    }
    .btn:hover { border-color: var(--gold); }
    .opp-stats { display: flex; flex-wrap: wrap; gap: 8px 18px; color: var(--muted); font-size: 0.88rem; border-top: 1px solid var(--rule); padding-top: 10px; }
    .opp-stats b, .hist-stats b { color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }
    .hist-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; color: var(--muted); margin-bottom: 8px; }
    .hist-stats { color: var(--muted); margin-top: 8px; font-size: 0.88rem; }

    /* AI brief */
    .brief h2 { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
    .brief-headline { font-family: var(--font-display); font-size: 1.15rem; font-weight: 650; color: var(--ink); margin: 0 0 12px; max-width: 70ch; }
    .brief-body p { color: var(--ink-2); line-height: 1.65; max-width: 70ch; margin: 0 0 12px; }
    .brief-sources { margin: 14px 0 0; padding-top: 12px; border-top: 1px solid var(--rule); font-size: 0.85rem; color: var(--muted); }
    .brief-meta { font-family: var(--font-mono); font-size: 0.72rem; color: var(--muted); font-weight: 400; }

    /* changelog */
    .changelog { display: flex; flex-direction: column; }
    .change-entry { display: grid; grid-template-columns: 64px 1fr; gap: 18px; padding: 16px 0; }
    .change-entry + .change-entry { border-top: 1px solid var(--rule); }
    .change-version { font-family: var(--font-mono); color: var(--gold-ink); font-weight: 600; font-size: 0.85rem; padding-top: 3px; }
    .change-entry h3 { margin: 0 0 4px; font-size: 1.05rem; }
    .change-date { font-family: var(--font-mono); color: var(--muted); font-weight: 400; font-size: 0.75rem; }
    .change-entry p { margin: 0 0 8px; color: var(--ink-2); font-size: 0.95rem; max-width: 68ch; }
    .change-tags { display: flex; flex-wrap: wrap; gap: 6px; }

    /* ladder chart */
    .chart { border-radius: 12px; background: var(--glass-strong); border: 1px solid var(--rule); padding: 6px 4px 0; margin-top: 10px; }

    /* static guide widget */
    .guide-btn {
      position: fixed; right: 20px; bottom: 20px; z-index: 40; background: var(--ink); color: var(--page);
      border: 0; border-radius: 999px; padding: 10px 18px; font-family: var(--font-display); font-weight: 650;
      font-size: 0.95rem; cursor: pointer; box-shadow: 0 10px 28px -12px rgba(0, 0, 0, 0.6);
    }
    .guide-panel {
      position: fixed; right: 20px; bottom: 74px; z-index: 41; width: min(370px, calc(100vw - 32px));
      background: var(--card); border: 1px solid var(--rule-strong); border-radius: 16px;
      display: flex; flex-direction: column; max-height: min(70vh, 560px); box-shadow: 0 18px 44px -18px rgba(0, 0, 0, 0.55);
    }
    .guide-panel[hidden] { display: none; }
    .g-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--rule); font-family: var(--font-display); font-weight: 700; }
    .g-close { background: none; border: none; color: var(--muted); font-size: 1.2rem; cursor: pointer; padding: 2px 8px; border-radius: 6px; }
    .g-close:hover { color: var(--ink); }
    .g-msgs { overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; flex: 1; min-height: 120px; }
    .g-msg { max-width: 88%; padding: 8px 12px; border-radius: 12px; font-size: 0.9rem; line-height: 1.45; white-space: pre-line; }
    .g-bot { background: var(--gold-soft); color: var(--ink); align-self: flex-start; border-bottom-left-radius: 4px; }
    .g-user { background: var(--ink); color: var(--page); align-self: flex-end; border-bottom-right-radius: 4px; }
    .g-chips { display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 16px 10px; }
    .g-chip { background: var(--glass-strong); border: 1px solid var(--rule-strong); border-radius: 999px; color: var(--ink); padding: 4px 12px; font-size: 0.8rem; cursor: pointer; }
    .g-chip:hover { border-color: var(--gold); }
    .g-input { display: flex; gap: 8px; padding: 10px 16px 14px; border-top: 1px solid var(--rule); }
    .g-input input { flex: 1; min-width: 0; background: var(--page); border: 1px solid var(--rule-strong); border-radius: 8px; color: var(--ink); padding: 8px 12px; font-size: 0.88rem; }
    .g-input button { background: var(--ink); border: 0; border-radius: 8px; color: var(--page); padding: 8px 14px; font-size: 0.88rem; cursor: pointer; }
"""

LADDER_PALETTE = '["--series-1","--series-2","--series-3","--series-4","--series-5","--series-6","--series-7"]'


class _Text(HTMLParser):
    """Visible text of <body>, without scripts and styles."""

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def visible_text(page: str) -> str:
    body = page[page.index("<body"):]
    p = _Text()
    p.feed(body)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def no_em_dashes(text: str) -> str:
    text = text.replace("<div class='num'>&mdash;</div>", "<div class='num'>none</div>")
    text = re.sub(r"\s*(?:—|&mdash;)\s*", " - ", text)
    return text


def plot_payload(page: str) -> str:
    m = re.search(r"Plotly\.newPlot\((.*?)\)\s*};?\s*</script>", page, re.S)
    return m.group(1) if m else ""


def main():
    src = SRC.read_text()
    page = src

    # 1. Head: theme boot, color-scheme, fonts, shared theme, page CSS.
    head_extra = (
        '  <meta name="color-scheme" content="light dark">\n  %s\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link rel="stylesheet" href="%s">\n'
        '  <link rel="stylesheet" href="assets/theme.css">\n'
        "  <style>%s  </style>" % (build.THEME_BOOT, build.FONTS_URL.replace("&", "&amp;"), PAGE_CSS))
    page, n = re.subn(r"<style>.*?</style>", lambda _m: head_extra, page, count=1, flags=re.S)
    assert n == 1, "style block not found"

    # 2. Body: glow canvas first, toggle inside the header.
    page = page.replace("<body>", '<body>\n  <canvas id="glow" aria-hidden="true"></canvas>', 1)
    assert page.count("<header>") == 1
    page = page.replace("<header>", "<header>\n    " + build.TOGGLE, 1)

    # 3. Ladder chart: follow the theme's series colors.
    old = '<div style="height:480px; width:100%;">'
    assert page.count(old) == 1, "ladder chart wrapper not found"
    page = page.replace(old, "<div class=\"chart\" data-chart data-palette='%s' style=\"height:480px; width:100%%;\">"
                        % LADDER_PALETTE, 1)

    # 4. Scripts: theme + glow before </body>.
    page = page.replace("</body>", '  <script src="assets/theme.js"></script>\n'
                                   '  <script src="assets/background.js"></script>\n</body>', 1)

    # 5. The dashboard's rule: no em dashes anywhere.
    page = no_em_dashes(page)
    assert "—" not in page and "&mdash;" not in page

    # Integrity: the dash change is the only text change, and chart data is untouched.
    before = visible_text(no_em_dashes(src))
    after = visible_text(page)
    assert before == after, "visible text changed"
    assert plot_payload(src) == plot_payload(page) != "", "chart data changed"

    OUT.write_text(page)
    print("Wrote %s (%s bytes); text and chart data unchanged" % (OUT, format(len(page), ",")))


if __name__ == "__main__":
    main()
