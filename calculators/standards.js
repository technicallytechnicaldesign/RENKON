// Shared fastener standards lookup — used by the Bolted Joint calculator
// (thread geometry + grade strengths drive torque/preload/shear). This is the
// same "standards-data lookup" pattern materials.js uses: a couple of small
// tables plus an ordered key array so the selects render in a sensible order,
// cross-linking one calculator's math off shared reference data (TDM-6834-A).
//
// Values are typical ISO 898-1 / ISO metric-coarse textbook figures for the
// named size/grade, not a substitute for a real fastener spec sheet — confirm
// against the actual bolt's data before using torque or FoS outputs for
// anything that matters. Dimensions are mm, strengths MPa; the calculator
// converts to m and Pa at the point of use.

// Thread geometry: nominal diameter d (mm) and coarse pitch p (mm).
var THREAD_DIMS = {
  M6: { d: 6, p: 1.0 },
  M8: { d: 8, p: 1.25 },
  M10: { d: 10, p: 1.5 },
  M12: { d: 12, p: 1.75 },
  M16: { d: 16, p: 2.0 },
  M20: { d: 20, p: 2.5 },
};

var THREAD_ORDER = ["M6", "M8", "M10", "M12", "M16", "M20"];

// Property classes: proof strength Sproof (MPa) and tensile strength Suts (MPa).
var BOLT_GRADES = {
  "4.6": { Sproof: 225, Suts: 400 },
  "8.8": { Sproof: 580, Suts: 800 },
  "10.9": { Sproof: 830, Suts: 1040 },
  "12.9": { Sproof: 970, Suts: 1220 },
};

var GRADE_ORDER = ["4.6", "8.8", "10.9", "12.9"];
