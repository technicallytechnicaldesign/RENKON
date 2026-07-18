// Sheet-Metal Bend (id: sheet-metal-bend). A self-contained calculator
// descriptor in the same shape as BEAM_CALC / COST_CALC in calculators.js: an
// inputs schema the shell renders as a form, a pure compute(), and a
// buildOutputs() that draws its own result rows + diagram. This one is the
// counterpoint to the cross-linked flagship — pure geometry, zero cross-links,
// no material/section lookups: it turns bend parameters into the developed flat
// length a fab shop cuts to. Everything here works in mm and degrees directly
// (no SI conversion) — the whole calc is scale-free geometry.

// Pure flat-pattern development. Angle is converted to radians internally.
// A = 0 collapses cleanly to flat = L1 + L2 (BA = OSSB = BD = 0).
function bendCompute(v) {
  var rad = (v.A * Math.PI) / 180;
  var BA = rad * (v.R + v.K * v.T);           // bend allowance (arc of neutral line)
  // Outside setback uses tan(A/2), which is singular at A = 180° (tan 90°): a
  // full hem drives the theoretical mould-line apex — and thus the outside-leg
  // dimensions this method is built on — off to infinity. Flag that case rather
  // than letting the flat length explode into a meaningless huge negative.
  var half = rad / 2;
  var singular = Math.abs(half - Math.PI / 2) < 1e-4;
  var OSSB = singular ? Infinity : (v.R + v.T) * Math.tan(half); // outside setback
  var BD = 2 * OSSB - BA;                      // bend deduction
  var flat = v.L1 + v.L2 - BD;                 // developed flat length
  return { rad: rad, BA: BA, OSSB: OSSB, BD: BD, flat: flat, singular: singular };
}

// Side-view schematic of the bent section: two straight legs meeting at an arc
// of inside radius R swept through angle A, drawn to scale, with the neutral
// line (radius R + K*T) dashed and R / T / A annotated. Built as an SVG string
// like beamDiagram. Everything is sampled to polylines (no SVG arc-flag math)
// and every coordinate is finiteness-guarded; the whole build is wrapped so a
// degenerate input renders a fallback strip instead of throwing.
function bendDiagram(root, v) {
  var W = 640, H = 300, pad = 46;
  var svg;
  try {
    var rad = (v.A * Math.PI) / 180;
    var half = rad / 2;
    var R = Math.max(0, v.R);
    var T = Math.max(0.0001, v.T);
    var K = v.K;
    var L1 = Math.max(0, v.L1);
    var L2 = Math.max(0, v.L2);
    var Rn = R + K * T; // neutral-line radius
    var Ro = R + T;     // outer-surface radius
    var th1 = -Math.PI / 2 - half;
    var th2 = -Math.PI / 2 + half;
    // Leg directions: tangent to the arc at each tangent point, pointing away
    // from the bend (perpendicular to the radius there).
    var dir1 = [Math.sin(th1), -Math.cos(th1)];
    var dir2 = [-Math.sin(th2), Math.cos(th2)];

    function onCirc(r, th) { return [r * Math.cos(th), r * Math.sin(th)]; }
    function addv(p, d, s) { return [p[0] + d[0] * s, p[1] + d[1] * s]; }
    function arcPts(r) {
      var pts = [];
      var n = 28;
      if (Math.abs(th2 - th1) < 1e-9) { pts.push(onCirc(r, th1)); return pts; }
      for (var i = 0; i <= n; i++) pts.push(onCirc(r, th1 + (th2 - th1) * (i / n)));
      return pts;
    }

    var T1in = onCirc(R, th1), T2in = onCirc(R, th2);
    var T1o = onCirc(Ro, th1), T2o = onCirc(Ro, th2);
    var innerPts = [addv(T1in, dir1, L1)].concat(arcPts(R), [addv(T2in, dir2, L2)]);
    var outerPts = [addv(T1o, dir1, L1)].concat(arcPts(Ro), [addv(T2o, dir2, L2)]);
    var neutPts = [addv(onCirc(Rn, th1), dir1, L1)].concat(arcPts(Rn), [addv(onCirc(Rn, th2), dir2, L2)]);
    var capA0 = addv(T1in, dir1, L1), capA1 = addv(T1o, dir1, L1);
    var capB0 = addv(T2in, dir2, L2), capB1 = addv(T2o, dir2, L2);
    var center = [0, 0];
    var arcMidIn = onCirc(R, -Math.PI / 2);
    var arcMidO = onCirc(Ro, -Math.PI / 2);

    // Fit: bounding box over everything drawn (+ center, so the R line shows).
    var all = innerPts.concat(outerPts, neutPts, [center, arcMidO]);
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    all.forEach(function (p) {
      if (!isFinite(p[0]) || !isFinite(p[1])) return;
      if (p[0] < minX) minX = p[0];
      if (p[0] > maxX) maxX = p[0];
      if (p[1] < minY) minY = p[1];
      if (p[1] > maxY) maxY = p[1];
    });
    if (!isFinite(minX)) { minX = -1; maxX = 1; minY = -1; maxY = 1; }
    var bw = maxX - minX, bh = maxY - minY;
    var sx = bw > 1e-9 ? (W - 2 * pad) / bw : Infinity;
    var sy = bh > 1e-9 ? (H - 2 * pad) / bh : Infinity;
    var scale = Math.min(sx, sy);
    if (!isFinite(scale) || scale <= 0) scale = 1;
    var offX = (W - bw * scale) / 2, offY = (H - bh * scale) / 2;
    function DX(p) { return offX + (p[0] - minX) * scale; }
    function DY(p) { return H - (offY + (p[1] - minY) * scale); } // y-flip: math up -> screen down

    function poly(pts, cls) {
      var d = "";
      for (var i = 0; i < pts.length; i++) {
        var x = DX(pts[i]), y = DY(pts[i]);
        if (!isFinite(x) || !isFinite(y)) continue;
        d += (d === "" ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1) + " ";
      }
      return d ? '<path class="' + cls + '" d="' + d + '"/>' : "";
    }
    function seg(a, b, cls) {
      var x1 = DX(a), y1 = DY(a), x2 = DX(b), y2 = DY(b);
      if (!isFinite(x1) || !isFinite(y1) || !isFinite(x2) || !isFinite(y2)) return "";
      return '<line class="' + cls + '" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) +
        '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '"/>';
    }
    function label(p, text, dx, dy) {
      var x = DX(p) + (dx || 0), y = DY(p) + (dy || 0);
      if (!isFinite(x) || !isFinite(y)) return "";
      return '<text class="lbl" x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '">' + text + "</text>";
    }

    svg = '<svg viewBox="0 0 ' + W + " " + H + '" xmlns="http://www.w3.org/2000/svg">';
    svg += seg(center, arcMidIn, "zero");           // radius line (dashed)
    svg += poly(neutPts, "zero");                   // neutral line (dashed)
    svg += poly(outerPts, "trace");                 // outer surface (accent)
    svg += poly(innerPts, "trace b");               // inner surface (teal)
    svg += seg(capA0, capA1, "trace");              // thickness end caps
    svg += seg(capB0, capB1, "trace");
    svg += label(onCirc(R * 0.5, -Math.PI / 2), "R " + fmt(v.R, 3), 4, 0);
    svg += label(capB1, "T " + fmt(v.T, 3), 6, -2);
    svg += label(center, "A " + fmt(v.A, 3) + "°", -10, -6);
    svg += label(neutPts[Math.floor(neutPts.length / 2)], "NEUTRAL R+K·T", 4, -4);
    svg += "</svg>";
  } catch (e) {
    svg = '<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg">' +
      '<line class="zero" x1="40" y1="60" x2="600" y2="60"/>' +
      '<text class="lbl" x="40" y="40">bend preview unavailable</text></svg>';
  }
  root.innerHTML = svg;
}

var BEND_CALC = {
  id: "sheet-metal-bend",
  chip: "CAD / geometry",
  title: "Sheet-Metal Bend",
  why: "The counterpoint to the flagship: pure geometry, zero cross-links, no material/section lookups — it develops the flat length a fab shop cuts to from thickness, radius, angle and K-factor.",
  refs: "Standard bend-allowance / K-factor flat-pattern development.",
  buildInputs: function (getVals, recompute) {
    var wrap = document.createElement("div");
    var T = fieldNumber(wrap, "Thickness (T)", "mm", 2, 0.001, recompute);
    var R = fieldNumber(wrap, "Inside radius (R)", "mm", 2, 0, recompute);
    var A = fieldNumber(wrap, "Bend angle (A), swept", "°", 90, 0, recompute); A.el.max = 180;
    var K = fieldNumber(wrap, "K-factor", "—", 0.44, 0, recompute); K.el.max = 0.5;
    var L1 = fieldNumber(wrap, "Outside leg 1 (L1)", "mm", 50, 0, recompute);
    var L2 = fieldNumber(wrap, "Outside leg 2 (L2)", "mm", 50, 0, recompute);

    getVals.get = function () {
      return { T: T.value, R: R.value, A: A.value, K: K.value, L1: L1.value, L2: L2.value };
    };
    return wrap;
  },
  compute: bendCompute,
  buildOutputs: function (root, v, out) {
    root.innerHTML = "";
    var list = document.createElement("div"); list.className = "out-list";
    outRow(list, "Developed flat length", fmt(out.flat, 3), "mm",
      out.singular ? "A → 180° (full hem): the outside-setback method is singular here — use a dedicated hem allowance." : null,
      out.singular ? "warn" : null, true);
    outRow(list, "Bend allowance (BA)", fmt(out.BA, 3), "mm");
    outRow(list, "Bend deduction (BD)", fmt(out.BD, 3), "mm");
    outRow(list, "Outside setback (OSSB)", fmt(out.OSSB, 3), "mm");
    if (v.R < v.T) {
      outRow(list, "Radius check", "R < T", "",
        "Inside radius R < thickness T — risk of cracking on brittle/hard tempers (common shop rule: R ≥ T).",
        "warn");
    }
    root.appendChild(list);

    var diagWrap = document.createElement("div"); diagWrap.className = "diagram";
    root.appendChild(diagWrap);
    bendDiagram(diagWrap, v);
    var cap = document.createElement("div"); cap.className = "cap";
    cap.textContent = "Side view — outside legs, inside radius R, angle A; dashed = neutral line at R + K·T";
    root.appendChild(cap);
  },
};
