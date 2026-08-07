/* RENKON fluid engine — a self-contained particle fluid sim that renders on a
 * TRANSPARENT canvas and pre-renders a perfectly loopable clip. Built for the
 * overlay use case (Mockup Studio composites the frames as an alpha motion
 * layer), distinct from the standalone Hydroform/Pipeform tools.
 *
 * window.FluidEngine.STYLES            -> [{key,label}, …]
 * window.FluidEngine.preRenderFrames(opts) -> Promise<{frames:[canvas], w, h, durationMs}>
 *   opts: { style, color, seed, frames, w, h, scale, intensity, durationMs }
 *
 * Loop guarantee: emission is a deterministic function of the phase within a
 * fixed period P (the emission RNG is reset at every period boundary and the
 * timestep is fixed), so once the pipeline is warmed up for one period the
 * particle state at step s equals the state at step s+P exactly. We warm up one
 * period, then capture the next — a seamless loop.
 *
 * No build step, no dependencies. Plain global-attaching script.
 */
(function () {
  "use strict";

  var STYLES = [
    { key: "jet",      label: "Jet — arcing stream" },
    { key: "fountain", label: "Fountain — rise & fall" },
    { key: "spray",    label: "Spray — falling mist" },
    { key: "splash",   label: "Splash — pulsing crown" }
  ];
  var STYLE_PERIOD = { jet: 2200, fountain: 2600, spray: 2200, splash: 1800 };

  function makeRng(seed) {
    var a = seed >>> 0;
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function hexToRgb(hex) {
    hex = (hex || "#4FD1D9").replace("#", "");
    if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    var n = parseInt(hex, 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }
  function rgba(c, a) { return "rgba(" + c.r + "," + c.g + "," + c.b + "," + a + ")"; }
  function lighten(c, k) {
    return { r: Math.min(255, Math.round(c.r + (255 - c.r) * k)),
             g: Math.min(255, Math.round(c.g + (255 - c.g) * k)),
             b: Math.min(255, Math.round(c.b + (255 - c.b) * k)) };
  }

  // Per-style emitter. Returns how many particles to spawn this step, and a
  // spawner that produces one particle. `phase` is 0..1 within the period.
  function emitConfig(style, W, H, intensity) {
    var GRAV = 0.9 * H;            // px/s^2, scaled to frame height
    var base = {
      grav: GRAV,
      rate: 0,
      spawn: null
    };
    if (style === "jet") {
      base.rate = 3.2 * intensity;
      base.spawn = function (rng) {
        var speed = (0.46 + rng() * 0.16) * W;
        var ang = (-0.12 + rng() * 0.24);           // small cone, rightward
        return { x: 0.10 * W, y: 0.50 * H,
                 vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed - 0.08 * H,
                 life: 1300 + rng() * 700, size: 1.8 + rng() * 2.6 };
      };
    } else if (style === "fountain") {
      base.rate = 3.6 * intensity;
      base.spawn = function (rng) {
        var speed = (0.62 + rng() * 0.22) * H;
        var ang = -Math.PI / 2 + (rng() - 0.5) * 0.5;  // upward, spread
        return { x: (0.42 + rng() * 0.16) * W, y: 0.94 * H,
                 vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed,
                 life: 1500 + rng() * 900, size: 1.6 + rng() * 2.4 };
      };
    } else if (style === "spray") {
      base.grav = 0.55 * H;
      base.rate = 4.2 * intensity;
      base.spawn = function (rng) {
        var speed = (0.10 + rng() * 0.22) * H;
        var ang = Math.PI / 2 + (rng() - 0.5) * 1.1;   // downward, wide
        return { x: (0.30 + rng() * 0.40) * W, y: 0.08 * H,
                 vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed,
                 life: 1400 + rng() * 800, size: 1.2 + rng() * 2.0 };
      };
    } else { // splash — a burst concentrated near the start of the period
      base.rate = 0; // handled via phase gating below
      base.burst = function (phase, rng) {
        // heavy emission in the first ~14% of the period, tapering off
        if (phase > 0.16) return 0;
        var env = 1 - phase / 0.16;
        return 9 * intensity * env;
      };
      base.spawn = function (rng) {
        var speed = (0.5 + rng() * 0.5) * H;
        var ang = -Math.PI / 2 + (rng() - 0.5) * 1.5;  // crown, up + wide
        return { x: (0.44 + rng() * 0.12) * W, y: 0.82 * H,
                 vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed,
                 life: 1200 + rng() * 500, size: 1.6 + rng() * 3.0 };
      };
    }
    return base;
  }

  async function preRenderFrames(opts) {
    opts = opts || {};
    var style = opts.style || "jet";
    var W = Math.round(opts.w || 640), H = Math.round(opts.h || 360);
    var scale = opts.scale || 1;
    var cw = Math.max(1, Math.round(W * scale)), ch = Math.max(1, Math.round(H * scale));
    var N = opts.frames || 24;
    var P = opts.durationMs || STYLE_PERIOD[style] || 2200;
    var color = hexToRgb(opts.color || "#4FD1D9");
    var core = lighten(color, 0.6);
    var intensity = opts.intensity != null ? opts.intensity : 1;
    var seed = (opts.seed || 1) >>> 0;

    var dt = 1000 / 60;
    var dts = dt / 1000;
    var spp = Math.max(N, Math.round(P / dt));
    var cfg = emitConfig(style, W, H, intensity);

    var particles = [];
    var emitRng = makeRng(seed);
    var carry = 0;

    function emit(phaseStep) {
      var phase = phaseStep / spp;
      var rate = cfg.burst ? cfg.burst(phase, emitRng) : cfg.rate;
      carry += rate;
      while (carry >= 1) {
        carry -= 1;
        if (particles.length > 1400) break;
        var p = cfg.spawn(emitRng);
        p.age = 0; p.px = p.x; p.py = p.y;
        particles.push(p);
      }
    }
    function step(s) {
      if (s % spp === 0) { emitRng = makeRng(seed); carry = 0; }
      emit(s % spp);
      for (var i = particles.length - 1; i >= 0; i--) {
        var p = particles[i];
        p.px = p.x; p.py = p.y;
        p.vy += cfg.grav * dts;
        p.x += p.vx * dts;
        p.y += p.vy * dts;
        p.age += dt;
        if (p.age >= p.life) particles.splice(i, 1);
      }
    }

    function renderFrame() {
      var cvs = document.createElement("canvas");
      cvs.width = cw; cvs.height = ch;
      var ctx = cvs.getContext("2d");
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
      ctx.globalCompositeOperation = "lighter";
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        var a = Math.max(0, 1 - p.age / p.life);
        var fade = a * a * (0.55 + 0.45 * a);
        var r = p.size * (0.7 + 0.5 * a);
        // motion streak
        var g2 = ctx.createLinearGradient(p.px, p.py, p.x, p.y);
        g2.addColorStop(0, rgba(color, 0));
        g2.addColorStop(1, rgba(color, 0.28 * fade));
        ctx.strokeStyle = g2; ctx.lineWidth = r * 1.1; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(p.px, p.py); ctx.lineTo(p.x, p.y); ctx.stroke();
        // glow
        var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 2.6);
        g.addColorStop(0, rgba(color, 0.85 * fade));
        g.addColorStop(0.4, rgba(color, 0.3 * fade));
        g.addColorStop(1, rgba(color, 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(p.x, p.y, r * 2.6, 0, Math.PI * 2); ctx.fill();
        // bright core
        ctx.fillStyle = rgba(core, 0.9 * fade);
        ctx.beginPath(); ctx.arc(p.x, p.y, r * 0.55, 0, Math.PI * 2); ctx.fill();
      }
      return cvs;
    }

    // warm up one full period so the pipeline is steady + periodic
    var s = 0;
    for (; s < spp; s++) step(s);
    // capture the next period as N frames (frame N would equal frame 0)
    var frames = [];
    for (var f = 0; f < N; f++) {
      frames.push(renderFrame());
      var target = spp + Math.round((f + 1) * (spp / N));
      while (s < target) { step(s); s++; }
    }
    return { frames: frames, w: W, h: H, durationMs: P };
  }

  window.FluidEngine = {
    STYLES: STYLES,
    preRenderFrames: preRenderFrames,
    isFluidValue: function (v) { return typeof v === "string" && v.indexOf("fluid:") === 0; },
    styleOf: function (v) { return this.isFluidValue(v) ? v.slice(6) : null; }
  };
})();
