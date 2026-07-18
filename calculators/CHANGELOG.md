# Changelog — Calculators

## 2026-07-18 — flagship 5 completed (RNK-0009)

- Built the remaining three of five flagship calculators from
  `calculator_specs_flagship5.md` (TDM-6834-A), each a self-contained
  descriptor in its own file (`calc-bolted.js`, `calc-bend.js`,
  `calc-cutopt.js`) plugged into the existing `app.js` shell — no shell
  changes needed:
  - **Bolted Joint — Torque & Shear**: thread + grade lookup tables
    (`standards.js`, the fastener sibling of `materials.js`) drive tensile
    stress area / proof load / preload / `T = K·F·d` torque, plus optional
    applied-shear stress + FoS. Shear outputs suppress when no shear load is
    entered (no Infinity). ISO 898-1-ish textbook figures, labelled as such.
  - **Sheet-Metal Bend**: pure flat-pattern geometry (BA / BD / OSSB /
    developed flat length), a scaled side-view SVG with the neutral line
    annotated, an `R < T` cracking-risk soft warning, and a guard on the
    180° hem singularity (flagged instead of emitting a ~1e17 mm garbage
    flat length once tan(90°) blows up).
  - **1D Cut Optimiser**: First-Fit-Decreasing bin packing over a dynamic
    add/remove parts list, saw-kerf accounting, waste %, optional material
    cost, and an SVG cut sheet (one row per stock bar, kerf gaps, hatched
    leftover tail). Over-length parts block with a clear validation error;
    stable ties by input order.
- Wired all three into `calculators.js`'s `CALCULATORS` array in spec order
  (Beam, Bolted, Bend, Cut, Cost) and into `index.html`'s script tags;
  emptied `app.js`'s `COMING_SOON` (mechanism kept for future scope). Updated
  the page-head copy and the root `index.html` Calculators tile.
- Verified each new `compute()` against a hand-worked known-good case via a
  Node harness (Bolted M10/8.8/75%/K0.2 → torque 50.5 N·m; Bend default →
  flat 96.524 mm, A=0 → flat=100, A=180 → flagged singular; Cut FFD →
  correct bar counts + waste) and live in the browser (all five tabs mount,
  recompute wiring fires on input change, dynamic parts list add/remove +
  over-length error + cost toggle all work, cut-sheet + bend diagrams render,
  Cost regression clean, zero console errors). New custom UI uses only
  theme-following tokens (`--bg`/`--text`), so light mode stays legible.

## 2026-07-18 — initial build (RNK-0009)

- Built the composition-pattern shell (`app.js`): tabs, field/output row
  builders, `fmt`/`money` number formatting, mount/recompute wiring.
- Built the first two of five flagship calculators from
  `calculator_specs_flagship5.md` (TDM-6834-A):
  - **Beam — Simply Supported**: point load + UDL superposition, real
    rectangular/circular section formulas (or custom I/S entry) instead of a
    hardcoded shape lookup table, shear/moment/deflection SVG diagram.
  - **Cost Estimator**: shop-rate absorption costing, sharing the `MATERIALS`
    table with Beam to prove the cross-calculator composition pattern.
  - Bolted joint / sheet-metal bend / 1D cut optimiser shown as disabled
    "not built yet" tabs — visible roadmap, not hidden scope.
- Added a live "Calculators" tile to the root `index.html`, replacing the
  Slot 03 placeholder.
- Verified by hand-checking beam outputs (2 m span, 5 kN midspan load, 20×40 mm
  rect section, mild steel) against independent calculation — reaction,
  shear, moment, deflection, bending stress, and FoS all matched — and by
  exercising the section-shape switch (rect/circular/custom) and the cost
  breakdown's currency formatting (a scientific-notation bug on lot totals
  over ~$1000 was caught this way and fixed — added a dedicated `money()`
  formatter instead of reusing the sig-fig `fmt()` for currency).
