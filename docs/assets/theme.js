/* Theme toggle + chart theming (shared by index.html and arb.html).
 *
 * The theme lives in data-theme on <html>. With no stored choice the page
 * follows the OS (prefers-color-scheme); clicking the toggle stores an
 * explicit "light" or "dark" in localStorage. A tiny inline script in <head>
 * applies the stored choice before first paint, so there is no flash.
 *
 * Plotly charts are built with transparent backgrounds. applyPlotTheme()
 * reads the CSS tokens and recolors fonts, gridlines, hover labels and (per
 * [data-chart] wrapper) the series palette for the active theme.
 */
(function () {
  var root = document.documentElement;
  var KEY = "theme";
  var mq = window.matchMedia("(prefers-color-scheme: dark)");

  function current() {
    var a = root.getAttribute("data-theme");
    if (a === "light" || a === "dark") return a;
    return mq.matches ? "dark" : "light";
  }

  function token(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // Palette entries are hex colors or CSS custom property names ("--ink").
  function resolveColor(entry) {
    return entry && entry.indexOf("--") === 0 ? token(entry) : entry;
  }

  function applyPlotTheme() {
    if (!window.Plotly) return;
    var ink = token("--ink"), ink2 = token("--ink-2"), muted = token("--muted");
    var grid = token("--chart-grid"), axis = token("--chart-axis"), card = token("--card");
    document.querySelectorAll("[data-chart]").forEach(function (wrap) {
      var gd = wrap.querySelector(".js-plotly-plot");
      if (!gd || !gd.data) return;
      var update = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font.color": ink2,
        "legend.font.color": ink2,
        "legend.bgcolor": "rgba(0,0,0,0)",
        "hoverlabel.bgcolor": card,
        "hoverlabel.bordercolor": axis,
        "hoverlabel.font.color": ink,
      };
      // Every axis, including subplot axes (xaxis2, yaxis2, ...).
      Object.keys(gd._fullLayout || {}).forEach(function (key) {
        if (!/^[xy]axis\d*$/.test(key)) return;
        update[key + ".gridcolor"] = grid;
        update[key + ".linecolor"] = axis;
        update[key + ".zerolinecolor"] = grid;
        update[key + ".tickfont.color"] = muted;
        update[key + ".title.font.color"] = muted;
        update[key + ".spikecolor"] = axis;
      });
      // Subplot titles and other annotations.
      ((gd.layout && gd.layout.annotations) || []).forEach(function (_a, i) {
        update["annotations[" + i + "].font.color"] = ink2;
      });
      Plotly.relayout(gd, update);
      // data-palette lists CSS tokens per trace, e.g. ["--ink", "--series-1"],
      // so series colors come from the same theme tokens as the swatches.
      var palette = JSON.parse(wrap.getAttribute("data-palette") || "[]");
      if (palette.length) {
        var colors = gd.data.map(function (_trace, i) {
          return resolveColor(palette[i % palette.length]);
        });
        Plotly.restyle(gd, { "line.color": colors, "marker.color": colors });
      }
    });
  }
  window.applyPlotTheme = applyPlotTheme;

  function syncToggle() {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    var dark = current() === "dark";
    btn.setAttribute("aria-pressed", String(dark));
    btn.title = dark ? "Switch to light mode" : "Switch to dark mode";
    // SVG elements don't reflect the .hidden property, so toggle the attribute.
    var moon = btn.querySelector(".icon-moon"), sun = btn.querySelector(".icon-sun");
    if (moon) moon.toggleAttribute("hidden", dark);
    if (sun) sun.toggleAttribute("hidden", !dark);
  }

  function announce() {
    syncToggle();
    applyPlotTheme();
    document.dispatchEvent(new CustomEvent("themechange", { detail: { theme: current() } }));
  }

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem(KEY, theme); } catch (_) { /* storage blocked: still switch */ }
  }

  // Any change to data-theme (our toggle, or a host page) re-themes everything.
  new MutationObserver(announce).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
  // With no explicit choice, follow the OS when it switches.
  mq.addEventListener("change", function () {
    if (!root.hasAttribute("data-theme")) announce();
  });

  function init() {
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        setTheme(current() === "dark" ? "light" : "dark");
      });
    }
    syncToggle();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  window.addEventListener("load", function () {
    applyPlotTheme();
    // Web fonts change label widths: let Plotly re-measure once they're in.
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        document.querySelectorAll(".js-plotly-plot").forEach(function (gd) {
          if (window.Plotly) Plotly.Plots.resize(gd);
        });
      });
    }
  });
})();
