/* Gradient glow: soft color clouds that drift on their own and lean toward
 * the cursor (nearer clouds move more), plus a warm halo that follows the
 * pointer and fades out when it leaves the page.
 *
 * Guardrails:
 *  - renders at ~22% resolution on one fixed canvas; CSS upscales it, and
 *    radial gradients stay smooth, so each frame is a handful of fills;
 *  - prefers-reduced-motion: one still frame, no animation loop;
 *  - touch screens (hover: none): ambient drift only, no halo;
 *  - paused while the tab is hidden;
 *  - colors come from the --glow-* tokens (tuned so text keeps 4.5:1
 *    contrast even where clouds overlap under the halo) and refresh on theme
 *    change.
 */
(function () {
  var canvas = document.getElementById("glow");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");
  var SCALE = 0.22;
  var PULL = 0.5;            // a depth-1 cloud travels halfway to the cursor
  var CLOUD_EASE = 0.06;     // per frame
  var HALO_EASE = 0.14;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var noHover = window.matchMedia("(hover: none)");

  // Base position (viewport fractions), radius (fraction of the long side),
  // depth (how strongly it leans toward the cursor), drift speed (rad/ms,
  // 12-21 s per cycle) and phase.
  var CLOUDS = [
    { x: 0.14, y: 0.16, r: 0.46, depth: 0.55, speed: 0.00030, phase: 0.0, token: "--glow-1" },
    { x: 0.86, y: 0.14, r: 0.38, depth: 0.9, speed: 0.00042, phase: 1.7, token: "--glow-2" },
    { x: 0.78, y: 0.82, r: 0.44, depth: 0.4, speed: 0.00034, phase: 3.1, token: "--glow-3" },
    { x: 0.22, y: 0.86, r: 0.36, depth: 1.0, speed: 0.00038, phase: 4.4, token: "--glow-4" },
    { x: 0.5, y: 0.48, r: 0.30, depth: 0.75, speed: 0.00052, phase: 5.2, token: "--glow-5" },
  ];
  var HALO = { r: 0.24, token: "--glow-halo" };

  var W = 2, H = 2, cloudStops = [], haloStops = [], raf = 0, running = false;
  var pointer = { x: 0.5, y: 0.5, active: false };
  var lean = { x: 0.5, y: 0.5 };       // eased cursor position the clouds lean toward
  var halo = { x: 0.5, y: 0.5, alpha: 0 };

  function rgba(p, a) {
    return "rgba(" + p[0] + "," + p[1] + "," + p[2] + "," + a + ")";
  }

  // Fade each glow to the SAME hue at zero alpha (fading to transparent
  // black would leave a grey fringe).
  function stopsFor(cs, token) {
    var m = (cs.getPropertyValue(token) || "").match(/[\d.]+/g) || [0, 0, 0, 0];
    var a = m.length > 3 ? parseFloat(m[3]) : 1;
    return [rgba(m, a), rgba(m, a * 0.42), rgba(m, 0)];
  }

  function readColors() {
    var cs = getComputedStyle(document.documentElement);
    cloudStops = CLOUDS.map(function (c) { return stopsFor(cs, c.token); });
    haloStops = stopsFor(cs, HALO.token);
  }

  function resize() {
    W = Math.max(2, Math.round(window.innerWidth * SCALE));
    H = Math.max(2, Math.round(window.innerHeight * SCALE));
    canvas.width = W;
    canvas.height = H;
  }

  function blob(cx, cy, r, stops, alpha) {
    var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    g.addColorStop(0, stops[0]);
    g.addColorStop(0.55, stops[1]);
    g.addColorStop(1, stops[2]);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = 1;
  }

  function draw(t) {
    ctx.clearRect(0, 0, W, H);
    var big = Math.max(W, H);
    var moving = reduce.matches ? 0 : 1;
    for (var i = 0; i < CLOUDS.length; i++) {
      var c = CLOUDS[i];
      var driftX = 0.07 * Math.sin(t * c.speed + c.phase);
      var driftY = 0.06 * Math.cos(t * c.speed * 0.8 + c.phase);
      var bx = c.x + moving * driftX, by = c.y + moving * driftY;
      // Lean toward the cursor: deeper (nearer) clouds travel further.
      var cx = (bx + (lean.x - bx) * PULL * c.depth * moving) * W;
      var cy = (by + (lean.y - by) * PULL * c.depth * moving) * H;
      var r = c.r * big * (1 + moving * 0.07 * Math.sin(t * c.speed * 1.7 + c.phase));
      blob(cx, cy, r, cloudStops[i], 1);
    }
    if (halo.alpha > 0.01) {
      blob(halo.x * W, halo.y * H, HALO.r * big, haloStops, halo.alpha);
    }
  }

  function frame(t) {
    var tx = pointer.active ? pointer.x : 0.5;
    var ty = pointer.active ? pointer.y : 0.5;
    lean.x += (tx - lean.x) * CLOUD_EASE;
    lean.y += (ty - lean.y) * CLOUD_EASE;
    halo.x += (pointer.x - halo.x) * HALO_EASE;
    halo.y += (pointer.y - halo.y) * HALO_EASE;
    halo.alpha += ((pointer.active ? 1 : 0) - halo.alpha) * 0.08;
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
    // One frame at rest (reduced motion, or while paused): no halo.
    var saved = halo.alpha;
    halo.alpha = 0;
    draw(0);
    halo.alpha = saved;
  }

  function onPointer(e) {
    if (noHover.matches || e.pointerType === "touch") return;
    pointer.x = e.clientX / Math.max(1, window.innerWidth);
    pointer.y = e.clientY / Math.max(1, window.innerHeight);
    if (!pointer.active) {
      // Start the halo where the pointer is instead of sliding in from centre.
      if (halo.alpha < 0.05) { halo.x = pointer.x; halo.y = pointer.y; }
      pointer.active = true;
    }
  }

  function onLeave() {
    pointer.active = false;
  }

  window.addEventListener("pointermove", onPointer, { passive: true });
  window.addEventListener("pointerdown", onPointer, { passive: true });
  document.documentElement.addEventListener("mouseleave", onLeave);
  window.addEventListener("blur", onLeave);
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
