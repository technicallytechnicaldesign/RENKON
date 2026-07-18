// Bolted Joint — Torque & Shear (id: bolted-joint)
// ---------------------------------------------------------------------------
// The third flagship calculator, and the clearest demonstration of the
// standards-data lookup pattern: a thread-dimension table and a bolt-grade
// table (standards.js) drive the whole computation, exactly the shape
// materials.js has for Beam/Cost. Pick a size and a grade, and the tables
// supply d, p, Sproof and Suts; the math is pure ISO 898-1 relations from
// there.
//
// Torque comes from the classic T = K·F·d preload relation (K is the nut
// factor / friction coefficient); preload is set as a fraction of the proof
// load At·Sproof. Optional applied shear per bolt yields a shear stress and a
// factor of safety against 0.6·Suts (a standard shear-yield approximation).
//
// Refs: ISO 898-1 (mechanical properties of fasteners); T = K·F·d torque–
// preload relation. Textbook figures — not a fastener spec sheet.

function boltedCompute(v) {
  var At = 0.7854 * Math.pow(v.d - 0.9382 * v.p, 2);   // tensile stress area, m^2
  var proofLoad = At * v.Sproof;                        // N
  var Fpreload = (v.preloadPct / 100) * proofLoad;      // N
  var torque = v.K * Fpreload * v.d;                    // N·m
  var As = v.threadsInShear ? At : 0.7854 * v.d * v.d;  // shear area, m^2
  var hasShear = v.Vapplied > 0;
  var tau = hasShear ? v.Vapplied / As : 0;             // Pa
  var FoSshear = hasShear ? (0.6 * v.Suts) / tau : Infinity;
  return { At: At, proofLoad: proofLoad, Fpreload: Fpreload, torque: torque, As: As, tau: tau, FoSshear: FoSshear, hasShear: hasShear };
}

var BOLTED_CALC = {
  id: "bolted-joint",
  chip: "Engineering",
  title: "Bolted Joint — Torque & Shear",
  why: "The standards-data lookup pattern at its plainest — a thread table and a grade table (like materials.js) supply every geometry and strength figure, and the pure T = K·F·d math falls out of the lookup.",
  refs: "ISO 898-1 (mechanical properties of fasteners); T = K·F·d torque–preload relation.",
  buildInputs: function (getVals, recompute) {
    var wrap = document.createElement("div");
    var sizeSel = fieldSelect(wrap, "Thread size", THREAD_ORDER.map(function (k) { return [k, k]; }), "M10", recompute);
    var gradeSel = fieldSelect(wrap, "Grade (class)", GRADE_ORDER.map(function (k) { return [k, k]; }), "8.8", recompute);

    var h3 = document.createElement("h3"); h3.textContent = "Preload"; h3.style.marginTop = "22px";
    wrap.appendChild(h3);
    var preloadPct = fieldNumber(wrap, "Preload (% of proof)", "%", 75, 0, recompute);
    preloadPct.el.max = 90;
    var K = fieldNumber(wrap, "Nut factor (K)", "—", 0.2, 0.08, recompute);
    K.el.max = 0.35;
    var note = document.createElement("div"); note.className = "field-note";
    note.textContent = "Nut factor K is approximate — ~0.2 dry, ~0.16 lubed. Preload above ~90% of proof is discouraged.";
    wrap.appendChild(note);

    var h3b = document.createElement("h3"); h3b.textContent = "Shear (optional)"; h3b.style.marginTop = "22px";
    wrap.appendChild(h3b);
    var Vapplied = fieldNumber(wrap, "Applied shear (per bolt)", "N", 0, 0, recompute);
    var threadsSel = fieldSelect(wrap, "Shear plane", [
      ["yes", "Threads in shear plane"], ["no", "Shank in shear plane"],
    ], "yes", recompute);

    getVals.get = function () {
      var dim = THREAD_DIMS[sizeSel.value];
      var g = BOLT_GRADES[gradeSel.value];
      var pct = preloadPct.value;
      if (pct < 0) pct = 0; else if (pct > 90) pct = 90;   // clamp 0..90
      return {
        d: dim.d / 1000, p: dim.p / 1000,             // mm -> m
        Sproof: g.Sproof * 1e6, Suts: g.Suts * 1e6,   // MPa -> Pa
        preloadPct: pct, K: K.value, Vapplied: Vapplied.value,
        threadsInShear: (threadsSel.value === "yes"),
      };
    };
    return wrap;
  },
  compute: boltedCompute,
  buildOutputs: function (root, v, out) {
    root.innerHTML = "";
    var list = document.createElement("div"); list.className = "out-list";
    outRow(list, "Tensile stress area (At)", fmt(out.At * 1e6, 3), "mm²");
    outRow(list, "Proof load", fmt(out.proofLoad / 1000, 3), "kN");
    outRow(list, "Preload target", fmt(out.Fpreload / 1000, 3), "kN");
    outRow(list, "Tightening torque", fmt(out.torque, 3), "N·m", "the number the shop actually needs", null, true);
    if (out.hasShear) {
      outRow(list, "Shear stress", fmt(out.tau / 1e6, 3), "MPa");
      outRow(list, "Shear factor of safety", fmt(out.FoSshear, 2), "",
        out.FoSshear < 1.5 ? "below the 1.5 guideline — review bolt size/count" : "≥ 1.5",
        out.FoSshear < 1.5 ? "warn" : "good");
    } else {
      var hint = document.createElement("div"); hint.className = "out-row";
      var hk = document.createElement("span"); hk.className = "k";
      hk.textContent = "Enter an applied shear load to see shear stress + FoS.";
      hint.appendChild(hk);
      list.appendChild(hint);
    }
    root.appendChild(list);
  },
};
