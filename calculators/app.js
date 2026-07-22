// Shared shell — tabs + field/output builders. Everything calculator-specific
// lives in calculators.js; this file only knows how to mount whatever
// descriptor it's handed. New calculators (bolted joint, sheet-metal bend,
// 1D cut optimiser) plug in by adding to the CALCULATORS array — nothing
// here should need to change for that.

function fmt(n, sig) {
  if (!isFinite(n)) return "—";
  if (n === 0) return "0";
  var s = n.toPrecision(sig);
  if (s.indexOf("e") !== -1) {
    // toPrecision falls back to exponential notation once the magnitude
    // outgrows `sig` integer digits (e.g. 1493 at 2 sig figs) — render
    // fixed-point instead so engineering-scale numbers never show as "1.5e+3".
    var digits = Math.max(0, sig - Math.ceil(Math.log10(Math.abs(n))));
    s = n.toFixed(digits);
  }
  if (s.indexOf(".") !== -1) s = s.replace(/0+$/, "").replace(/\.$/, "");
  return s;
}

function money(n) { return isFinite(n) ? n.toFixed(2) : "—"; }

function xlsEscape(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Zero-dependency ".xls" export: SpreadsheetML (Excel 2003 XML) is a plain-text
// format Excel opens natively as a real worksheet — no zip/OOXML generation and
// no CDN library needed, same "native browser APIs only" policy as the rest of
// the site. `rows` is an array of [label, value] pairs; the first row is styled
// as a bold header.
function downloadXLS(filename, sheetName, rows) {
  var body = rows.map(function (r, i) {
    var style = i === 0 ? ' ss:StyleID="Header"' : "";
    return "<Row>" +
      '<Cell' + style + '><Data ss:Type="String">' + xlsEscape(r[0]) + "</Data></Cell>" +
      '<Cell' + style + '><Data ss:Type="String">' + xlsEscape(r[1]) + "</Data></Cell>" +
      "</Row>";
  }).join("");
  var xml = '<?xml version="1.0"?>' +
    '<?mso-application progid="Excel.Sheet"?>' +
    '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" ' +
    'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">' +
    '<Styles><Style ss:ID="Header"><Font ss:Bold="1"/></Style></Styles>' +
    '<Worksheet ss:Name="' + xlsEscape(sheetName).slice(0, 31) + '">' +
    "<Table>" + body + "</Table>" +
    "</Worksheet></Workbook>";
  var blob = new Blob([xml], { type: "application/vnd.ms-excel" });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url; a.download = filename;
  a.click();
  setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
}

function fieldNumber(root, label, unit, def, min, onChange) {
  var f = document.createElement("div"); f.className = "field";
  var l = document.createElement("label");
  var span = document.createElement("span"); span.textContent = label;
  var u = document.createElement("span"); u.className = "unit"; u.textContent = unit;
  l.appendChild(span); l.appendChild(u);
  var input = document.createElement("input");
  input.type = "number"; input.value = def; if (min !== null && min !== undefined) input.min = min;
  input.step = "any";
  f.appendChild(l); f.appendChild(input);
  root.appendChild(f);
  input.addEventListener("input", onChange);
  // calculators.js reads `.value` expecting a number — wrap the element
  // rather than shadow its native (string) value property. unitEl is exposed
  // so a calculator can relabel the unit later (e.g. cost estimator swapping
  // "$/h" for "€/h" when the currency changes).
  return { el: input, unitEl: u, get value() { return parseFloat(input.value) || 0; } };
}

function fieldSelect(root, label, options, def, onChange) {
  var f = document.createElement("div"); f.className = "field";
  var l = document.createElement("label"); l.textContent = label;
  var sel = document.createElement("select");
  options.forEach(function (o) {
    var opt = document.createElement("option"); opt.value = o[0]; opt.textContent = o[1];
    if (o[0] === def) opt.selected = true;
    sel.appendChild(opt);
  });
  f.appendChild(l); f.appendChild(sel);
  root.appendChild(f);
  sel.addEventListener("change", onChange);
  return sel;
}

function outRow(root, label, value, unit, note, level, headline) {
  var row = document.createElement("div");
  row.className = "out-row" + (level ? " " + level : "") + (headline ? " headline" : "");
  var k = document.createElement("span"); k.className = "k"; k.textContent = label;
  var v = document.createElement("span"); v.className = "v"; v.textContent = value + (unit ? " " + unit : "");
  row.appendChild(k); row.appendChild(v);
  if (note) {
    var n = document.createElement("div"); n.className = "note"; n.textContent = note;
    row.appendChild(n);
  }
  root.appendChild(row);
  return row;
}

(function () {
  var tabsHost = document.getElementById("calc-tabs");
  var whyHost = document.getElementById("calc-why");
  var layout = document.getElementById("calc-layout");
  var active = CALCULATORS[0].id;

  // All five flagship calculators are built — nothing pending. The roadmap
  // placeholder mechanism below is kept (harmless on an empty list) so a future
  // calculator can be shown as a "not built yet" tab again without re-adding it.
  var COMING_SOON = [];

  function renderTabs() {
    tabsHost.innerHTML = "";
    CALCULATORS.forEach(function (calc) {
      var b = document.createElement("button");
      b.className = "calc-tab" + (calc.id === active ? " on" : "");
      b.setAttribute("role", "tab");
      b.innerHTML = '<span>' + calc.chip + '</span><span class="n">' + calc.title + "</span>";
      b.addEventListener("click", function () { active = calc.id; renderTabs(); mount(calc); });
      tabsHost.appendChild(b);
    });
    COMING_SOON.forEach(function (name) {
      var b = document.createElement("button");
      b.className = "calc-tab soon";
      b.innerHTML = '<span>Not built yet</span><span class="n">' + name + "</span>";
      tabsHost.appendChild(b);
    });
  }

  function mount(calc) {
    whyHost.innerHTML = "<b>" + calc.title + ".</b> " + calc.why + " <i>Refs: " + calc.refs + "</i>";
    layout.innerHTML = "";
    var formPanel = document.createElement("div"); formPanel.className = "panel";
    var h3 = document.createElement("h3"); h3.textContent = "Inputs"; formPanel.appendChild(h3);
    var outPanel = document.createElement("div"); outPanel.className = "panel";
    var h3b = document.createElement("h3"); h3b.textContent = "Results"; outPanel.appendChild(h3b);
    var outBody = document.createElement("div");
    outPanel.appendChild(outBody);

    var getVals = {};
    function recompute() {
      var v = getVals.get();
      var out = calc.compute(v);
      calc.buildOutputs(outBody, v, out);
    }
    var formBody = calc.buildInputs(getVals, recompute);
    formPanel.appendChild(formBody);
    layout.appendChild(formPanel); layout.appendChild(outPanel);
    recompute();
  }

  renderTabs();
  mount(CALCULATORS[0]);
})();
