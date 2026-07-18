// ---------------------------------------------------------------------------
// 1D Cut Optimiser (id: cut-optimiser-1d)
// ---------------------------------------------------------------------------
// Packs a variable bill of cut lengths onto fixed-length stock bars using
// First-Fit-Decreasing (FFD) bin packing: sort every required piece largest
// first, then drop each into the first stock bar it still fits (accounting for
// saw kerf), opening a new bar only when nothing fits. FFD is a heuristic — it
// is near-optimal, not proven optimal — but it is fast, deterministic, and its
// output is a shareable cut sheet a shop can work straight off.
//
// Follows the house descriptor shape (see BEAM_CALC / COST_CALC in
// calculators.js): a buildInputs that renders the form (built ONCE per mount —
// so the dynamic parts list and its own add/remove re-render live here, not in
// buildOutputs), a pure compute(), and a buildOutputs that clears + redraws the
// results panel on every recompute. ES5 only.

function cutCompute(v) {
  // Validation: any single piece longer than a stock bar can never be packed.
  var over = [];
  var i;
  for (i = 0; i < v.parts.length; i++) {
    if (v.parts[i].len > v.stockLen) over.push(v.parts[i].len);
  }
  if (over.length) {
    return {
      error: "Part " + over.join(", ") + " mm exceeds stock length " + v.stockLen + " mm — cannot pack.",
      bars: [],
    };
  }

  // Flatten every part x qty into individual items, then sort largest-first.
  // Ties keep original input order (stable) via the recorded seq index.
  var items = [];
  for (i = 0; i < v.parts.length; i++) {
    for (var q = 0; q < v.parts[i].qty; q++) {
      items.push({ len: v.parts[i].len, seq: items.length });
    }
  }
  items.sort(function (a, b) { return (b.len - a.len) || (a.seq - b.seq); });

  // First-Fit-Decreasing: place each item in the first bar where the running
  // used length + one kerf per existing cut + this item still fits.
  var bars = []; // each bar = { items:[lengths], used:number }
  for (i = 0; i < items.length; i++) {
    var len = items[i].len, placed = false, j;
    for (j = 0; j < bars.length; j++) {
      var b = bars[j];
      if (b.used + v.kerf * b.items.length + len <= v.stockLen) {
        b.items.push(len);
        b.used += len;
        placed = true;
        break;
      }
    }
    if (!placed) bars.push({ items: [len], used: len });
  }

  var itemCount = items.length;
  var barCount = bars.length;
  var used = 0;
  for (i = 0; i < items.length; i++) used += items[i].len;
  var total = barCount * v.stockLen;
  // Kerf consumed = (items - bars): one fewer cut than items in each bar.
  var waste = total - used - v.kerf * (itemCount - barCount);
  var wastePct = total > 0 ? (waste / total) * 100 : 0;
  var cost = total * v.pricePerLen;

  // Per-bar leftover (the untouched tail after the last cut) for labelling.
  for (i = 0; i < bars.length; i++) {
    var cuts = bars[i].items.length - 1;
    if (cuts < 0) cuts = 0;
    bars[i].leftover = v.stockLen - bars[i].used - v.kerf * cuts;
  }

  return {
    error: null,
    bars: bars,
    barCount: barCount,
    used: used,
    total: total,
    waste: waste,
    wastePct: wastePct,
    cost: cost,
    itemCount: itemCount,
  };
}

// Horizontal stacked cut sheet — one full-width row per stock bar, each scaled
// so the whole bar width == stockLen. Within a bar: a coloured rect per part
// segment, a muted kerf gap between segments, and a hatched muted tail for the
// leftover/waste. Built as an SVG string then injected (the BEAM_CALC
// beamDiagram pattern). Guards against divide-by-zero / NaN coordinates.
function cutDiagram(root, v, out) {
  var W = 640;
  var pad = { l: 8, r: 8, t: 8, b: 6 };
  var rowH = 30, gap = 8, labelH = 13, barH = 16;
  var bars = out.bars;
  var barW = W - pad.l - pad.r;
  var scale = v.stockLen > 0 ? barW / v.stockLen : 0;
  var H = pad.t + bars.length * (rowH + gap) - (bars.length ? gap : 0) + pad.b;
  if (H < pad.t + pad.b) H = pad.t + pad.b;

  var colors = ["var(--c-fluid)", "var(--c-accent)", "var(--c-good)"];
  var colorIdx = 0;

  function px(n) {
    if (!isFinite(n)) return "0";
    return n.toFixed(1);
  }

  var svg = '<svg viewBox="0 0 ' + W + " " + H + '" xmlns="http://www.w3.org/2000/svg">';
  // Hatch pattern for the leftover tail.
  svg += '<defs><pattern id="cuthatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">';
  svg += '<rect width="6" height="6" fill="var(--panel-bg-raised)"/>';
  svg += '<line x1="0" y1="0" x2="0" y2="6" stroke="var(--muted)" stroke-width="1"/>';
  svg += "</pattern></defs>";

  var i, s;
  for (i = 0; i < bars.length; i++) {
    var bar = bars[i];
    var yTop = pad.t + i * (rowH + gap);
    var yBar = yTop + labelH;

    // Row labels: "Bar N" left, leftover right-aligned, both above the bar.
    svg += '<text class="lbl" x="' + px(pad.l) + '" y="' + px(yTop + 9) + '">Bar ' + (i + 1) + "</text>";
    var leftover = bar.leftover < 0 ? 0 : bar.leftover;
    svg += '<text class="lbl" x="' + px(W - pad.r) + '" y="' + px(yTop + 9) + '" text-anchor="end">' +
      "· " + Math.round(leftover) + " mm left</text>";

    // Full stock outline behind the segments.
    svg += '<rect x="' + px(pad.l) + '" y="' + px(yBar) + '" width="' + px(barW) + '" height="' + barH +
      '" fill="none" stroke="var(--line)" stroke-width="1"/>';

    // Part segments, left to right, with kerf gaps between them.
    var cursor = pad.l;
    for (s = 0; s < bar.items.length; s++) {
      var segLen = bar.items[s] * scale;
      if (segLen < 0) segLen = 0;
      var fill = colors[colorIdx % colors.length];
      colorIdx++;
      svg += '<rect x="' + px(cursor) + '" y="' + px(yBar) + '" width="' + px(segLen) + '" height="' + barH +
        '" fill="' + fill + '"/>';
      // Part length label if the segment is wide enough to hold it.
      if (segLen > 34) {
        svg += '<text class="lbl" x="' + px(cursor + segLen / 2) + '" y="' + px(yBar + barH - 5) +
          '" text-anchor="middle" fill="var(--bg)">' + Math.round(bar.items[s]) + "</text>";
      }
      cursor += segLen;
      // Kerf gap (muted) after every segment except the last.
      if (s < bar.items.length - 1 && v.kerf > 0) {
        var kw = v.kerf * scale;
        svg += '<rect x="' + px(cursor) + '" y="' + px(yBar) + '" width="' + px(kw) + '" height="' + barH +
          '" fill="var(--muted)"/>';
        cursor += kw;
      }
    }

    // Hatched leftover / waste tail filling the rest of the bar.
    var tailW = pad.l + barW - cursor;
    if (tailW > 0.5) {
      svg += '<rect x="' + px(cursor) + '" y="' + px(yBar) + '" width="' + px(tailW) + '" height="' + barH +
        '" fill="url(#cuthatch)"/>';
    }
  }
  svg += "</svg>";
  root.innerHTML = svg;
}

var CUTOPT_CALC = {
  id: "cut-optimiser-1d",
  chip: "Production",
  title: "1D Cut Optimiser",
  why: "Packs a variable parts list onto fixed stock bars with First-Fit-Decreasing bin-packing (near-optimal, not proven optimal); its output is a shareable SVG cut sheet a shop can work straight off.",
  refs: "First-Fit-Decreasing bin packing (heuristic — near-optimal, not proven optimal).",
  buildInputs: function (getVals, recompute) {
    var wrap = document.createElement("div");
    var stockLen = fieldNumber(wrap, "Stock length", "mm", 6000, 1, recompute);
    var kerf = fieldNumber(wrap, "Saw kerf", "mm", 3, 0, recompute);

    // --- Dynamic parts list -------------------------------------------------
    var h3 = document.createElement("h3");
    h3.textContent = "Parts";
    h3.style.marginTop = "22px";
    wrap.appendChild(h3);

    // parts is the source of truth for structure + last-known values; each row's
    // live inputs write back into it on every keystroke so add/remove rebuilds
    // preserve what the user typed. get() reads the live inputs directly.
    var parts = [
      { len: 2400, qty: 3 },
      { len: 1500, qty: 4 },
      { len: 800, qty: 5 },
    ];

    var rowsHost = document.createElement("div");
    wrap.appendChild(rowsHost);
    var partInputs = []; // parallel to parts: { lenEl, qtyEl }

    function styleInput(input) {
      input.style.width = "100%";
      input.style.background = "var(--bg)";
      input.style.border = "1px solid var(--line)";
      input.style.color = "var(--text)";
      input.style.fontFamily = "var(--font-mono)";
      input.style.fontSize = "13px";
      input.style.padding = "7px 8px";
      input.style.boxSizing = "border-box";
    }

    function renderRows() {
      rowsHost.innerHTML = "";
      partInputs = [];
      parts.forEach(function (part, idx) {
        var row = document.createElement("div");
        row.style.display = "grid";
        row.style.gridTemplateColumns = "1fr 1fr auto";
        row.style.gap = "8px";
        row.style.alignItems = "center";
        row.style.border = "1px solid var(--line)";
        row.style.padding = "8px";
        row.style.marginBottom = "8px";

        var lenIn = document.createElement("input");
        lenIn.type = "number"; lenIn.min = "1"; lenIn.step = "any"; lenIn.value = part.len;
        lenIn.setAttribute("aria-label", "Part length (mm)");
        styleInput(lenIn);
        lenIn.addEventListener("input", function () {
          part.len = parseFloat(lenIn.value) || 0;
          recompute();
        });

        var qtyIn = document.createElement("input");
        qtyIn.type = "number"; qtyIn.min = "1"; qtyIn.step = "1"; qtyIn.value = part.qty;
        qtyIn.setAttribute("aria-label", "Quantity");
        styleInput(qtyIn);
        qtyIn.addEventListener("input", function () {
          part.qty = Math.floor(parseFloat(qtyIn.value) || 0);
          recompute();
        });

        var rm = document.createElement("button");
        rm.type = "button";
        rm.textContent = "✕";
        rm.setAttribute("aria-label", "Remove part");
        rm.style.background = "var(--panel-bg-raised)";
        rm.style.border = "1px solid var(--line)";
        rm.style.color = "var(--muted)";
        rm.style.fontFamily = "var(--font-mono)";
        rm.style.fontSize = "13px";
        rm.style.lineHeight = "1";
        rm.style.padding = "7px 10px";
        rm.style.cursor = "pointer";
        rm.addEventListener("click", function () {
          parts.splice(idx, 1);
          renderRows();
          recompute();
        });

        row.appendChild(lenIn);
        row.appendChild(qtyIn);
        row.appendChild(rm);
        rowsHost.appendChild(row);
        partInputs.push({ lenEl: lenIn, qtyEl: qtyIn });
      });
    }
    renderRows();

    // Column caption + add-row control.
    var partsCap = document.createElement("div");
    partsCap.className = "field-note";
    partsCap.style.marginTop = "0";
    partsCap.textContent = "Length (mm) · Qty";
    rowsHost.insertBefore(partsCap, rowsHost.firstChild);

    var addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "+ Add part";
    addBtn.style.background = "var(--panel-bg-raised)";
    addBtn.style.border = "1px solid var(--line)";
    addBtn.style.color = "var(--text)";
    addBtn.style.fontFamily = "var(--font-mono)";
    addBtn.style.fontSize = "11px";
    addBtn.style.textTransform = "uppercase";
    addBtn.style.letterSpacing = "0.05em";
    addBtn.style.padding = "8px 12px";
    addBtn.style.cursor = "pointer";
    addBtn.style.marginBottom = "14px";
    addBtn.addEventListener("click", function () {
      parts.push({ len: 1000, qty: 1 });
      renderRows();
      recompute();
    });
    wrap.appendChild(addBtn);

    // --- Optional pricing ---------------------------------------------------
    var pricePerLen = fieldNumber(wrap, "Price per length", "$/mm", 0, 0, recompute);
    var priceNote = document.createElement("div");
    priceNote.className = "field-note";
    priceNote.textContent = "Price is optional — leave 0 to hide cost.";
    wrap.appendChild(priceNote);

    getVals.get = function () {
      var out = [];
      for (var i = 0; i < partInputs.length; i++) {
        var len = parseFloat(partInputs[i].lenEl.value) || 0;
        var qty = Math.floor(parseFloat(partInputs[i].qtyEl.value) || 0);
        if (len <= 0 || qty <= 0) continue;
        out.push({ len: len, qty: qty });
      }
      return {
        stockLen: stockLen.value,
        kerf: kerf.value,
        parts: out,
        pricePerLen: pricePerLen.value,
      };
    };
    return wrap;
  },
  compute: cutCompute,
  buildOutputs: function (root, v, out) {
    root.innerHTML = "";
    var list = document.createElement("div");
    list.className = "out-list";

    if (out.error) {
      outRow(list, "Cannot pack", "—", "", out.error, "warn");
      root.appendChild(list);
      return;
    }

    outRow(list, "Stock bars", String(out.barCount), "",
      out.itemCount + " parts packed", "good");
    outRow(list, "Waste", fmt(out.wastePct, 1), "%", null, null, true);
    if (v.pricePerLen > 0) {
      outRow(list, "Material cost", "$" + money(out.cost), "");
    }
    root.appendChild(list);

    var diagWrap = document.createElement("div");
    diagWrap.className = "diagram";
    root.appendChild(diagWrap);
    cutDiagram(diagWrap, v, out);

    var cap = document.createElement("div");
    cap.className = "cap";
    cap.style.fontFamily = "var(--font-mono)";
    cap.style.fontSize = "9.5px";
    cap.style.color = "var(--muted)";
    cap.style.textTransform = "uppercase";
    cap.style.letterSpacing = "0.06em";
    cap.style.marginTop = "8px";
    cap.textContent = "Cut sheet — one row per stock bar; gaps = kerf; muted tail = leftover/waste. FFD heuristic (near-optimal).";
    root.appendChild(cap);
  },
};
