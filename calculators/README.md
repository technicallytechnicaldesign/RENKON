# Calculators

Engineering + shop-math tools, built on one small composition pattern:
a typed input schema, a pure `compute()`, and shared lookup tables.
No build step — `index.html` + plain-JS files, opens directly in a browser.
All five flagship calculators are live.

Specs for all five flagship calculators (this + three more): RENKON's
`01_RESEARCH/calculator_specs_flagship5.md` (UID `TDM-6834-A`).

## Files

| File | What |
|---|---|
| `index.html` | Page chrome + the tab shell markup. |
| `app.js` | Shared shell: tabs, `fieldNumber`/`fieldSelect`/`outRow` builders, `fmt`/`money` formatters, `downloadXLS()` (SpreadsheetML export), mount/recompute wiring. Calculator-agnostic — new calculators shouldn't need to touch this. |
| `calculators.js` | The Beam + Cost descriptors (`BEAM_CALC`, `COST_CALC`) and the `CALCULATORS` array that assembles all five in tab order. |
| `calc-bolted.js` | `BOLTED_CALC` — torque & shear descriptor. |
| `calc-bend.js` | `BEND_CALC` — sheet-metal bend descriptor (with a side-view SVG). |
| `calc-cutopt.js` | `CUTOPT_CALC` — 1D cut optimiser (dynamic parts list + FFD packing + SVG cut sheet). |
| `materials.js` | Shared `MATERIALS` table (E, yield, pricePerKg per alloy) — Beam + Cost pull from it. |
| `standards.js` | Shared fastener tables (`THREAD_DIMS`, `BOLT_GRADES`) driving the Bolted Joint math — the same data-lookup shape as `materials.js`. |

Script load order matters: the per-calculator files and the two data
tables load *before* `calculators.js` (whose `CALCULATORS` array references
every descriptor), and `app.js` loads last.

## Live

- **Beam — Simply Supported** (`beam-simply-supported`): point load + UDL via
  superposition, Euler-Bernoulli theory. Section is derived from real solid
  geometry (rectangular/circular formulas, or direct custom I/S entry) rather
  than a hardcoded named-shape lookup table, to avoid stating standard-shape
  values from memory that could be subtly wrong. Renders shear/moment/
  deflection as a 3-row SVG plot.
- **Bolted Joint — Torque & Shear** (`bolted-joint`): thread + grade tables
  (`standards.js`) drive tensile-stress-area / proof-load / preload / torque
  (`T = K·F·d`), plus an optional applied-shear stress + FoS. The
  standards-data-lookup pattern at its plainest; shear outputs suppress
  cleanly when no shear load is entered.
- **Sheet-Metal Bend** (`sheet-metal-bend`): pure flat-pattern geometry —
  bend allowance / deduction / setback / developed flat length from T, R,
  angle and K-factor. Zero cross-links. Renders a scaled side-view SVG with
  the neutral line annotated; soft-warns when `R < T`; flags the 180° hem
  singularity rather than emitting a garbage flat length.
- **1D Cut Optimiser** (`cut-optimiser-1d`): First-Fit-Decreasing bin
  packing over a dynamic parts list, with saw-kerf accounting, waste %,
  optional material cost, and an SVG cut sheet (one row per stock bar, kerf
  gaps, hatched leftover tail). Over-length parts block with a clear error.
  Labelled near-optimal, not proven optimal.
- **Cost Estimator** (`cost-estimator`): shop-rate absorption costing,
  composes on the same `MATERIALS` table Beam uses (proving the cross-
  calculator composition pattern the roadmap cares about). Renders a
  material/machine/labour/overhead stacked-bar breakdown. A currency picker
  (`CURRENCIES` in `calculators.js`) converts the `MATERIALS.pricePerKg`
  line by a fixed FX snapshot and relabels the machine/labour rate units;
  those two rates are typed directly in whatever currency is selected, not
  converted. An "Export .xls" button (`downloadXLS()` in `app.js`) writes
  the full input + output breakdown as a SpreadsheetML (Excel 2003 XML)
  file — plain text, no zip/OOXML generation, opens natively in Excel.

## Adding another calculator

A new descriptor object (`{ id, chip, title, why, refs, buildInputs,
compute, buildOutputs }`) in its own `calc-*.js` file, added to the
`CALCULATORS` array in `calculators.js` and to the script tags in
`index.html`. Nothing in `app.js` should need to change. `app.js` still
carries a `COMING_SOON` array (now empty) that renders any listed name as a
disabled "not built yet" tab — a visible roadmap marker for future scope.

## Values that need a human's judgment before real use

`MATERIALS`' `E`/`yield` are typical textbook figures for the named alloy/
temper, not a mill certificate — confirm against the actual material cert
before trusting an FoS output for anything load-bearing. `pricePerKg` is
illustrative and drifts with the market; edit it to match your supplier.
Same caveat for `CURRENCIES`' `rate` values (Cost Estimator) — a fixed
snapshot, not a live feed; edit before using for a real quote.
