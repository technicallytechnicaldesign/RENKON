// The two flagship calculators (of five specced in
// 01_RESEARCH/calculator_specs_flagship5.md, UID TDM-6834-A). Each calculator
// is a small self-contained descriptor: an inputs schema the shell renders as
// a form, a pure compute(), and a mount() that draws its own outputs/diagram
// into the panel the shell hands it. Shared machinery (tabs, field/output
// row builders, number formatting) lives in app.js — this file only holds
// calculator-specific content, which is the composition pattern the roadmap
// is trying to prove out.

// ---------------------------------------------------------------------------
// 1. Beam — simply supported (id: beam-simply-supported)
// ---------------------------------------------------------------------------
// Supports a central point load P and/or a full-span UDL w via superposition
// (both peak at midspan, so maxima coincide). Pure Euler-Bernoulli beam theory.

function beamCompute(v) {
  var L = v.L, P = v.P, w = v.w, I = v.I, S = v.S, E = v.E, yieldStress = v.yield;
  var R = P / 2 + (w * L) / 2;
  var Vmax = R;
  var Mmax = (P * L) / 4 + (w * L * L) / 8;
  var dMax = (P * Math.pow(L, 3)) / (48 * E * I) + (5 * w * Math.pow(L, 4)) / (384 * E * I);
  var sigma = S > 0 ? Mmax / S : 0;
  var FoS = sigma > 0 ? yieldStress / sigma : Infinity;
  return { R: R, Vmax: Vmax, Mmax: Mmax, dMax: dMax, sigma: sigma, FoS: FoS };
}

// Shear/moment/deflection as continuous functions of x, for the diagram —
// same superposition, sampled rather than reduced to the four scalars above.
function beamCurve(v, x) {
  var L = v.L, P = v.P, w = v.w, E = v.E, I = v.I;
  var R = P / 2 + (w * L) / 2;
  var half = x <= L / 2;
  var V = R - w * x - (half ? 0 : P);
  var M = half ? (R * x - (w * x * x) / 2) : (R * x - (w * x * x) / 2 - P * (x - L / 2));
  // standard SS-beam deflection tables, superposed: UDL is one closed form
  // across the whole span; point-load-at-midspan mirrors about L/2.
  var yUdl = I > 0 ? (w * x * (Math.pow(L, 3) - 2 * L * x * x + Math.pow(x, 3))) / (24 * E * I) : 0;
  var xp = half ? x : L - x;
  var yPt = I > 0 ? (P * xp * (3 * L * L - 4 * xp * xp)) / (48 * E * I) : 0;
  return { V: V, M: M, y: yUdl + yPt };
}

function beamDiagram(root, v, out) {
  var W = 640, H = 260, pad = { l: 44, r: 16, t: 16, b: 16 };
  var rowH = (H - pad.t - pad.b - 24) / 3;
  var N = 60;
  var pts = [];
  for (var i = 0; i <= N; i++) pts.push(beamCurve(v, (v.L * i) / N));
  var Vmax = Math.max(1e-9, Math.max.apply(null, pts.map(function (p) { return Math.abs(p.V); } )));
  var Mmax = Math.max(1e-9, Math.max.apply(null, pts.map(function (p) { return Math.abs(p.M); } )));
  var Ymax = Math.max(1e-9, Math.max.apply(null, pts.map(function (p) { return Math.abs(p.y); } )));

  function rowY(idx) { return pad.t + idx * (rowH + 12) + rowH / 2; }
  function path(getVal, idx, scale) {
    var y0 = rowY(idx);
    var d = "";
    for (var i = 0; i < pts.length; i++) {
      var x = pad.l + ((W - pad.l - pad.r) * i) / (pts.length - 1);
      var y = y0 - (getVal(pts[i]) / scale) * (rowH / 2 - 4);
      d += (i === 0 ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1) + " ";
    }
    return d;
  }
  var rows = [
    { label: "Shear V(x)", get: function (p) { return p.V; }, scale: Vmax, cls: "" },
    { label: "Moment M(x)", get: function (p) { return p.M; }, scale: Mmax, cls: " b" },
    { label: "Deflection y(x)", get: function (p) { return -p.y; }, scale: Ymax, cls: "" },
  ];
  var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg">';
  rows.forEach(function (row, idx) {
    var y0 = rowY(idx);
    svg += '<line class="zero" x1="' + pad.l + '" y1="' + y0 + '" x2="' + (W - pad.r) + '" y2="' + y0 + '"/>';
    svg += '<path class="trace' + row.cls + '" d="' + path(row.get, idx, row.scale) + '"/>';
    svg += '<text class="lbl" x="' + pad.l + '" y="' + (y0 - rowH / 2 + 2) + '">' + row.label + "</text>";
  });
  svg += "</svg>";
  root.innerHTML = svg;
}

var BEAM_CALC = {
  id: "beam-simply-supported",
  chip: "Engineering",
  title: "Beam — Simply Supported",
  why: "The flagship: cross-links Material + Section lookups, and renders shear / moment / deflection diagrams from one set of pure equations.",
  refs: "Euler-Bernoulli beam theory; standard simply-supported beam superposition cases.",
  buildInputs: function (getVals, recompute) {
    var wrap = document.createElement("div");
    var L = fieldNumber(wrap, "Span (L)", "m", 2, 0.05, function () { recompute(); });
    var P = fieldNumber(wrap, "Point load (P), midspan", "N", 0, 0, function () { recompute(); });
    var w = fieldNumber(wrap, "UDL (w)", "N/m", 0, 0, function () { recompute(); });

    var h3 = document.createElement("h3"); h3.textContent = "Section (solid)"; h3.style.marginTop = "22px";
    wrap.appendChild(h3);
    var shapeSel = fieldSelect(wrap, "Shape", [
      ["rect", "Rectangular"], ["circ", "Circular"], ["custom", "Custom I / S"],
    ], "rect", function () { renderShapeFields(); recompute(); });

    var shapeHost = document.createElement("div");
    wrap.appendChild(shapeHost);
    var shapeFields = {};
    function renderShapeFields() {
      shapeHost.innerHTML = "";
      var shape = shapeSel.value;
      if (shape === "rect") {
        shapeFields.b = fieldNumber(shapeHost, "Width (b)", "mm", 20, 0.1, recompute);
        shapeFields.h = fieldNumber(shapeHost, "Height (h)", "mm", 40, 0.1, recompute);
      } else if (shape === "circ") {
        shapeFields.d = fieldNumber(shapeHost, "Diameter (d)", "mm", 30, 0.1, recompute);
      } else {
        shapeFields.Icustom = fieldNumber(shapeHost, "I (2nd moment of area)", "mm⁴", 106667, 0, recompute);
        shapeFields.Scustom = fieldNumber(shapeHost, "S (section modulus)", "mm³", 5333, 0, recompute);
      }
    }
    renderShapeFields();

    var h3b = document.createElement("h3"); h3b.textContent = "Material"; h3b.style.marginTop = "22px";
    wrap.appendChild(h3b);
    var matSel = fieldSelect(wrap, "Material", MATERIAL_ORDER.map(function (k) { return [k, MATERIALS[k].label]; }), "mild_steel", recompute);

    getVals.get = function () {
      var shape = shapeSel.value, I, S;
      if (shape === "rect") {
        var b = shapeFields.b.value / 1000, h = shapeFields.h.value / 1000; // mm -> m
        I = (b * Math.pow(h, 3)) / 12; S = (b * h * h) / 6;
      } else if (shape === "circ") {
        var d = shapeFields.d.value / 1000;
        I = (Math.PI * Math.pow(d, 4)) / 64; S = (Math.PI * Math.pow(d, 3)) / 32;
      } else {
        I = shapeFields.Icustom.value / 1e12; S = shapeFields.Scustom.value / 1e9; // mm^4/mm^3 -> m^4/m^3
      }
      var mat = MATERIALS[matSel.value];
      return { L: L.value, P: P.value, w: w.value, I: I, S: S, E: mat.E, yield: mat.yield };
    };
    return wrap;
  },
  compute: beamCompute,
  buildOutputs: function (root, v, out) {
    root.innerHTML = "";
    var list = document.createElement("div"); list.className = "out-list";
    outRow(list, "Reaction (each)", fmt(out.R / 1000, 3), "kN");
    outRow(list, "Max shear", fmt(out.Vmax / 1000, 3), "kN");
    outRow(list, "Max moment", fmt(out.Mmax / 1000, 3), "kN·m");
    var span = v.L * 1000, defLimit = span / 250;
    outRow(list, "Max deflection", fmt(out.dMax * 1000, 3), "mm",
      out.dMax * 1000 > defLimit ? "exceeds L/250 (" + fmt(defLimit, 1) + " mm) — too flexible for a typical structural limit" : "within L/250 (" + fmt(defLimit, 1) + " mm)",
      out.dMax * 1000 > defLimit ? "warn" : "good");
    outRow(list, "Bending stress", fmt(out.sigma / 1e6, 3), "MPa", null, null, true);
    outRow(list, "Factor of safety", isFinite(out.FoS) ? fmt(out.FoS, 2) : "—", "",
      out.FoS < 1.5 ? "below the 1.5 guideline — review load/section" : "≥ 1.5", out.FoS < 1.5 ? "warn" : "good");
    root.appendChild(list);
    var diagWrap = document.createElement("div"); diagWrap.className = "diagram";
    root.appendChild(diagWrap);
    beamDiagram(diagWrap, v, out);
    var cap = document.createElement("div"); cap.className = "cap";
    cap.textContent = "Shear · moment · deflection, plotted across the span (P = w = 0 renders flat zero lines, no divide errors)";
    root.appendChild(cap);
  },
};

// ---------------------------------------------------------------------------
// 2. Cost estimator (id: cost-estimator)
// ---------------------------------------------------------------------------
// Composed of other calculators in the roadmap (ingests Mass/Machining-Time
// outputs once those exist) — for now mass/cycle time are direct entries,
// and it already composes on the shared MATERIALS table (pricePerKg).

// Fixed illustrative FX snapshot, not a live rate feed (same "edit before a
// real quote" caveat as MATERIALS.pricePerKg). MATERIALS.pricePerKg is
// USD-denominated, so only the material line gets converted by `rate` —
// machine/labour rates are typed directly in whatever currency is selected.
var CURRENCIES = {
  USD: { symbol: "$", label: "USD — US Dollar", rate: 1 },
  EUR: { symbol: "€", label: "EUR — Euro", rate: 0.92 },
  GBP: { symbol: "£", label: "GBP — British Pound", rate: 0.79 },
  JPY: { symbol: "¥", label: "JPY — Japanese Yen", rate: 156 },
  CAD: { symbol: "CA$", label: "CAD — Canadian Dollar", rate: 1.37 },
  AUD: { symbol: "AU$", label: "AUD — Australian Dollar", rate: 1.52 },
  CHF: { symbol: "CHF", label: "CHF — Swiss Franc", rate: 0.90 },
};
var CURRENCY_ORDER = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"];

function costCompute(i) {
  var material = i.mass * i.pricePerKg * i.currencyRate * (1 + i.scrapPct / 100);
  var machine = (i.setupTime / i.qty + i.cycleTime) * i.machineRate;
  var labour = i.labourTime * i.labourRate;
  var direct = material + machine + labour;
  var overhead = direct * (i.overheadPct / 100);
  var cost = direct + overhead;
  var unit = cost * (1 + i.marginPct / 100);
  return { material: material, machine: machine, labour: labour, overhead: overhead, unit: unit, lot: unit * i.qty };
}

var COST_CALC = {
  id: "cost-estimator",
  chip: "Production",
  title: "Cost Estimator",
  why: "Composed of other calculators — pulls material price from the same MATERIALS table Beam uses, and (once built) will ingest Mass-from-geometry + Machining-Time outputs directly.",
  refs: "Standard shop-rate / absorption costing model.",
  buildInputs: function (getVals, recompute) {
    var wrap = document.createElement("div");
    var currencySel = fieldSelect(wrap, "Currency", CURRENCY_ORDER.map(function (k) { return [k, CURRENCIES[k].label]; }), "USD", function () {
      var sym = CURRENCIES[currencySel.value].symbol;
      machineRate.unitEl.textContent = sym + "/h";
      labourRate.unitEl.textContent = sym + "/h";
      recompute();
    });
    var mass = fieldNumber(wrap, "Mass", "kg", 1.2, 0.001, recompute);
    var matSel = fieldSelect(wrap, "Material", MATERIAL_ORDER.map(function (k) { return [k, MATERIALS[k].label]; }), "mild_steel", recompute);
    var scrapPct = fieldNumber(wrap, "Scrap", "%", 15, 0, recompute);
    var qty = fieldNumber(wrap, "Lot size", "parts", 100, 1, recompute);

    var h3 = document.createElement("h3"); h3.textContent = "Machine + labour"; h3.style.marginTop = "22px";
    wrap.appendChild(h3);
    var setupTime = fieldNumber(wrap, "Setup time (per lot)", "h", 0.5, 0, recompute);
    var cycleTime = fieldNumber(wrap, "Cycle time", "h/part", 0.1, 0, recompute);
    var machineRate = fieldNumber(wrap, "Machine rate", "$/h", 60, 0, recompute);
    var labourTime = fieldNumber(wrap, "Labour time", "h/part", 0.05, 0, recompute);
    var labourRate = fieldNumber(wrap, "Labour rate", "$/h", 40, 0, recompute);

    var h3b = document.createElement("h3"); h3b.textContent = "Overhead + margin"; h3b.style.marginTop = "22px";
    wrap.appendChild(h3b);
    var overheadPct = fieldNumber(wrap, "Overhead", "%", 20, 0, recompute);
    var marginPct = fieldNumber(wrap, "Margin", "%", 25, 0, recompute);

    getVals.get = function () {
      var currency = CURRENCIES[currencySel.value];
      return {
        currencyCode: currencySel.value, currencySymbol: currency.symbol, currencyRate: currency.rate,
        mass: mass.value, pricePerKg: MATERIALS[matSel.value].pricePerKg, scrapPct: scrapPct.value,
        setupTime: setupTime.value, cycleTime: cycleTime.value, machineRate: machineRate.value,
        labourTime: labourTime.value, labourRate: labourRate.value,
        overheadPct: overheadPct.value, marginPct: marginPct.value, qty: qty.value,
      };
    };
    return wrap;
  },
  compute: costCompute,
  buildOutputs: function (root, v, out) {
    root.innerHTML = "";
    var sym = v.currencySymbol;
    var list = document.createElement("div"); list.className = "out-list";
    outRow(list, "Unit price", sym + money(out.unit), "", null, null, true);
    outRow(list, "Lot price (×" + v.qty + ")", sym + money(out.lot), "");
    root.appendChild(list);

    var segs = [
      { key: "Material", val: out.material, color: "var(--c-fluid)" },
      { key: "Machine", val: out.machine, color: "var(--c-accent)" },
      { key: "Labour", val: out.labour, color: "var(--c-good)" },
      { key: "Overhead", val: out.overhead, color: "var(--muted)" },
    ];
    var total = segs.reduce(function (s, x) { return s + x.val; }, 0) || 1;
    var bar = document.createElement("div"); bar.className = "stackbar";
    var legend = document.createElement("div"); legend.className = "stackbar-legend";
    segs.forEach(function (s) {
      var pct = (s.val / total) * 100;
      var seg = document.createElement("div"); seg.className = "seg";
      seg.style.width = pct + "%"; seg.style.background = s.color;
      seg.textContent = pct > 8 ? pct.toFixed(0) + "%" : "";
      bar.appendChild(seg);
      var li = document.createElement("div"); li.className = "li";
      var sw = document.createElement("span"); sw.className = "sw"; sw.style.background = s.color;
      li.appendChild(sw);
      li.appendChild(document.createTextNode(s.key + " " + sym + money(s.val)));
      legend.appendChild(li);
    });
    root.appendChild(bar); root.appendChild(legend);
    var cap = document.createElement("div"); cap.className = "cap"; cap.style.marginTop = "10px";
    cap.textContent = "Per-part direct-cost breakdown, before overhead + margin";
    root.appendChild(cap);

    var exportBtn = document.createElement("button");
    exportBtn.type = "button";
    exportBtn.textContent = "↓ Export .xls";
    exportBtn.style.background = "var(--panel-bg-raised)";
    exportBtn.style.border = "1px solid var(--line)";
    exportBtn.style.color = "var(--text)";
    exportBtn.style.fontFamily = "var(--font-mono)";
    exportBtn.style.fontSize = "11px";
    exportBtn.style.textTransform = "uppercase";
    exportBtn.style.letterSpacing = "0.05em";
    exportBtn.style.padding = "8px 12px";
    exportBtn.style.cursor = "pointer";
    exportBtn.style.marginTop = "16px";
    exportBtn.addEventListener("click", function () {
      downloadXLS("cost-estimate-" + v.currencyCode + ".xls", "Cost Estimate", [
        ["Field", "Value"],
        ["Currency", v.currencyCode],
        ["Mass (kg)", v.mass],
        ["Material price/kg (" + v.currencyCode + ")", money(v.pricePerKg * v.currencyRate)],
        ["Scrap (%)", v.scrapPct],
        ["Lot size (parts)", v.qty],
        ["Setup time (h/lot)", v.setupTime],
        ["Cycle time (h/part)", v.cycleTime],
        ["Machine rate (" + sym + "/h)", v.machineRate],
        ["Labour time (h/part)", v.labourTime],
        ["Labour rate (" + sym + "/h)", v.labourRate],
        ["Overhead (%)", v.overheadPct],
        ["Margin (%)", v.marginPct],
        ["Material cost", sym + money(out.material)],
        ["Machine cost", sym + money(out.machine)],
        ["Labour cost", sym + money(out.labour)],
        ["Overhead cost", sym + money(out.overhead)],
        ["Unit price", sym + money(out.unit)],
        ["Lot price (×" + v.qty + ")", sym + money(out.lot)],
      ]);
    });
    root.appendChild(exportBtn);
  },
};

var CALCULATORS = [BEAM_CALC, BOLTED_CALC, BEND_CALC, CUTOPT_CALC, COST_CALC];
