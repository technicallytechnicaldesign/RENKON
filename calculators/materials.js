// Shared material lookup — used by Beam (E, yield) and Cost Estimator (pricePerKg).
// This is the "standards-data lookup" pattern from calculator_specs_flagship5.md,
// cross-linking multiple calculators off one table (TDM-6834-A).
//
// Values are typical textbook figures for the named alloy/temper, not a mill
// certificate — confirm against your actual material cert before using FoS
// outputs for anything load-bearing. pricePerKg is an illustrative market
// price that drifts; edit it to match your actual supplier quote.
var MATERIALS = {
  mild_steel: { label: "Mild steel (A36-ish)", E: 200e9, yield: 250e6, pricePerKg: 1.2 },
  alloy_steel_4140: { label: "Alloy steel (4140, Q&T)", E: 205e9, yield: 655e6, pricePerKg: 2.4 },
  stainless_304: { label: "Stainless 304", E: 193e9, yield: 215e6, pricePerKg: 5.5 },
  aluminum_6061: { label: "Aluminum 6061-T6", E: 69e9, yield: 276e6, pricePerKg: 4.5 },
  brass_c360: { label: "Brass (C360)", E: 97e9, yield: 124e6, pricePerKg: 8.0 },
};

var MATERIAL_ORDER = ["mild_steel", "alloy_steel_4140", "stainless_304", "aluminum_6061", "brass_c360"];
