/* Current / Archived tabs with keyboard support and deep links.
 * A hash like #archived, #arb, #gold or #mu opens whichever tab contains that
 * element and scrolls to it. No hash = Current projects.
 */
(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('[role="tabpanel"]'));
  if (!tabs.length) return;

  function activate(tab, opts) {
    opts = opts || {};
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    });
    panels.forEach(function (p) {
      p.hidden = p.id !== tab.getAttribute("aria-controls");
    });
    if (opts.focus) tab.focus();
    if (opts.push) history.replaceState(null, "", "#" + tab.getAttribute("aria-controls"));
    // Charts inside a panel that was hidden have zero width: re-measure them.
    if (window.Plotly) {
      document.querySelectorAll("#" + tab.getAttribute("aria-controls") + " .js-plotly-plot")
        .forEach(function (gd) { Plotly.Plots.resize(gd); });
    }
  }

  function tabForPanel(id) {
    return tabs.filter(function (t) { return t.getAttribute("aria-controls") === id; })[0];
  }

  function applyHash() {
    var id = (location.hash || "").slice(1);
    if (!id) return;
    var target = document.getElementById(id);
    var panel = target ? target.closest('[role="tabpanel"]') : null;
    if (!panel) return;
    activate(tabForPanel(panel.id));
    if (target !== panel) target.scrollIntoView({ block: "start" });
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { activate(tab, { push: true }); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === "Home") next = tabs[0];
      else if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        activate(next, { focus: true, push: true });
      }
    });
  });

  activate(tabs[0]);
  applyHash();
  window.addEventListener("hashchange", applyHash);
})();
