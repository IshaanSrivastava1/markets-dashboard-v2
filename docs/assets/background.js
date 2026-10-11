/* Gradient glow: five large, soft color fields that drift slowly and lean
 * toward the cursor, each at its own depth (nearer fields move more).
 *
 * Guardrails:
 *  - renders at ~22% resolution on one fixed canvas; CSS upscales it, and
 *    radial gradients stay smooth, so each frame is a handful of fills;
 *  - prefers-reduced-motion: one still frame, no animation loop;
 *  - touch screens (hover: none): slow ambient drift only, no tracking;
 *  - paused while the tab is hidden;
 *  - colors come from the --glow-* tokens and refresh on theme change.
 */
(function () {
  var canvas = document.getElementById("glow");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");
  var SCALE = 0.22;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var noHover = window.matchMedia("(hover: none)");

  // Base position (viewport fractions), radius (fraction of the long side),
  // depth (how far it leans toward the cursor), drift speed and phase.
  var FIELDS = [
    { x: 0.16, y: 0.18, r: 0.62, depth: 0.55, speed: 0.00011, phase: 0.0, token: "--glow-1" },
    { x: 0.86, y: 0.12, r: 0.5, depth: 0.9, speed: 0.00014, phase: 1.7, token: "--glow-2" },
    { x: 0.74, y: 0.8, r: 0.66, depth: 0.35, speed: 0.00009, phase: 3.1, token: "--glow-3" },
    { x: 0.24, y: 0.88, r: 0.5, depth: 1.0, speed: 0.00012, phase: 4.4, token: "--glow-4" },
    { x: 0.5, y: 0.46, r: 0.38, depth: 0.7, speed: 0.00016, phase: 5.2, token: "--glow-5" },
  ];

  var W = 2, H = 2, stops = [], raf = 0, running = false;
  var target = { x: 0.5, y: 0.5 }, eased = { x: 0.5, y: 0.5 };

  function rgba(parts, alpha) {
    return "rgba(" + parts[0] + "," + parts[1] + "," + parts[2] + "," + alpha + ")";
  }

  // Fade each field to the SAME hue at zero alpha (fading to transparent
  // black would leave a grey fringe).
  function readColors() {
    var cs = getComputedStyle(document.documentElement);
    stops = FIELDS.map(function (f) {
      var m = (cs.getPropertyValue(f.token) || "").match(/[\d.]+/g) || [0, 0, 0, 0];
      var a = m.length > 3 ? parseFloat(m[3]) : 1;
      return [rgba(m, a), rgba(m, a * 0.42), rgba(m, 0)];
    });
  }

  function resize() {
    W = Math.max(2, Math.round(window.innerWidth * SCALE));
    H = Math.max(2, Math.round(window.innerHeight * SCALE));
    canvas.width = W;
    canvas.height = H;
  }

  function draw(t) {
    ctx.clearRect(0, 0, W, H);
    var big = Math.max(W, H);
    var drift = reduce.matches ? 0 : 1;
    var px = eased.x - 0.5, py = eased.y - 0.5;
    for (var i = 0; i < FIELDS.length; i++) {
      var f = FIELDS[i];
      var cx = (f.x + drift * 0.06 * Math.sin(t * f.speed + f.phase) + px * 0.3 * f.depth) * W;
      var cy = (f.y + drift * 0.05 * Math.cos(t * f.speed * 0.8 + f.phase) + py * 0.24 * f.depth) * H;
      var r = f.r * big;
      var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
      g.addColorStop(0, stops[i][0]);
      g.addColorStop(0.55, stops[i][1]);
      g.addColorStop(1, stops[i][2]);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }
  }

  function frame(t) {
    eased.x += (target.x - eased.x) * 0.045;
    eased.y += (target.y - eased.y) * 0.045;
    draw(t);
    raf = window.requestAnimationFrame(frame);
  }

  function start() {
    if (running || reduce.matches || document.hidden) return;
    running = true;
    raf = window.requestAnimationFrame(frame);
  }

  function stop() {
    running = false;
    window.cancelAnimationFrame(raf);
  }

  function still() {
    // One frame at rest, centred: used for reduced motion and while paused.
    draw(0);
  }

  function onPointer(e) {
    if (noHover.matches) return;
    target.x = e.clientX / Math.max(1, window.innerWidth);
    target.y = e.clientY / Math.max(1, window.innerHeight);
  }

  function recentre() {
    target.x = 0.5;
    target.y = 0.5;
  }

  window.addEventListener("pointermove", onPointer, { passive: true });
  document.documentElement.addEventListener("mouseleave", recentre);
  window.addEventListener("blur", recentre);
  window.addEventListener("resize", function () {
    resize();
    if (!running) still();
  });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) stop();
    else start();
  });
  reduce.addEventListener("change", function () {
    if (reduce.matches) { stop(); still(); } else start();
  });
  document.addEventListener("themechange", function () {
    readColors();
    if (!running) still();
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    readColors();
    if (!running) still();
  });

  readColors();
  resize();
  still();
  start();
})();
