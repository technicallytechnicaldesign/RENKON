# Creo → KeyShot Workflow: Research Notes

Project ID: `ksrp-efbe4961`
Date: 2026-07-11

## Assignment
Scripts that make the Creo→KeyShot workflow easier, more professional, more
consistent, and — sometimes — more exciting. Covers both single parts and
assemblies.

## The bridge, and what depends on it
Both paths are available and in active use:
1. **KeyShot's Creo plugin (live link)** — preserves assembly tree, instance
   names, appearances, configs/simplified reps. Available, underused so far.
2. **Neutral export (STEP) → `lux.importFile()`** — geometry only; the
   current default for most work.

Decision: default to STEP for anything that doesn't need hierarchy/config
data to survive (most single-part work). Use the live plugin where that
data is the point — assembly structure, explode state, configs — starting
with the exploded-view work below. Worth experimenting per-script rather
than picking one bridge pipeline-wide.

## Where the pipeline has gaps (by stage)
Everything built so far lives in `2a_` (batch render) and `2b_` (animation),
plus one `3_` (contact sheet) and one `1_` (material preflight). `0_` and
`4_` are empty.

| Stage | Gap | Why it matters |
|---|---|---|
| `0_` pre-check | Nothing validates geometry/appearances before they hit KeyShot | Non-manifold geo, missing materials, wrong scale get caught mid-render instead of before |
| `1_` helper | No Studio/camera-rig library — each part's Studios are set up ad hoc | Family consistency (e.g. all steel brackets shot the same way) isn't enforced anywhere |
| `4_` post-check | Nothing audits a finished batch | No automatic check that every part got every expected view, or that filenames match the new convention |

## Parts vs. assemblies
Parts are mostly solved (batch views, turntables, hero reveal). Assemblies
open a different set of opportunities.

### Exploded / build reveals — two source modes
- **Creo-driven** — the explode state is authored in Creo, brought in via
  the live plugin, and the script animates into/out of that existing state
  (closest to how the hero reveal script already treats a fixed hero
  framing).
- **Procedural** — the script generates the motion itself, no Creo explode
  needed. Worth building as selectable modes on one script rather than
  separate scripts:

  | Style | Idea |
  |---|---|
  | Scatter & settle | Parts scatter to random positions/orientations at open, reveal is watching them settle |
  | Reassemble, no crossing | Parts converge to final position without visually crossing paths — likely solved with per-part timing/route offsets rather than true collision detection |
  | Staggered build | Parts arrive one at a time in assembly order, stop-motion style |
  | Sub-assembly build | Sub-assemblies converge first as groups, then those groups converge into the final assembly — mirrors how the thing is actually built |
  | Spiral converge | Parts arrive on curved/helical paths instead of straight lines |
  | Ghost fade-in | Parts fade from transparent to full opacity as they arrive, rather than moving |

  **Open / needs verification:** does an active Creo explode state come
  through the live plugin import automatically as a readable per-part
  offset, or does it need to be brought in as a separate export/data file?
  Same confirmed-vs-inferred treatment as the rest of this pipeline — a
  `dump_node()` check on a plugin-imported exploded assembly should answer
  it directly.

### Other assembly ideas
- **Cutaway/cross-section shots** — assemblies benefit far more than single
  parts from a section-plane reveal.
- **Per-instance material variants** — same assembly, different finish or
  colorway, batch-rendered.
- **Dynamic BOM callouts** — part number/name labels that place themselves
  next to each component during an exploded reveal, driven by the same BOM
  data as the manifest (see below).

## "Professional & consistent" ideas
- **Material-name lookup table** (Creo appearance → KeyShot template) —
  confirmed priority. `batch_material_preflight.py` catches the symptom; a
  mapping file prevents it.
- **BOM-driven manifest** — opt-in flag, not a hard requirement (BOM access
  method still TBD, see Q3). Feeds both the CSV manifest and the dynamic
  callout idea above.
- Naming-compliance audit (`4_`) — now that we have the `AA01` convention,
  scan a folder and flag anything that doesn't match it.

## "Exciting" ideas
- Assembly reveal (exploded/build), as above.
- Cutaway/cross-section reveal (also above) — assemblies particularly.
- **Multi-angle fade reel** — instead of a continuous 360 spin, crossfade
  between N fixed Studios/cameras into one video ("turntable fade").
  Crossfading is 2D compositing, not a render step — cleanest as a new `3_`
  post-process script that consumes stills already produced by
  `2a_BAT_TURNTABLE`/`2a_BAT_STD_VIEW`, rather than a change to either of
  them. Keeps the existing continuous-spin turntable script untouched.
- Short-form output presets (square/vertical crop, GIF export) for
  social/marketing use straight out of the same render pass.
- A small "hero shot" preset library (dramatic rim-light Studio, etc.)
  selectable per part family.

## Open questions — status (2026-07-11)
1. ✅ Both available; STEP is the current default, plugin available and
   worth using per-script where hierarchy/config/explode data matters.
2. ⏳ Partially open — want both Creo-driven and procedural modes (styles
   table above). Still need to verify whether explode data survives the
   plugin import automatically.
3. ⏳ Open — BOM access method not yet confirmed.
4. ✅ Cutaway/cross-section and the material lookup table are confirmed
   near-term priorities; BOM manifest is in as an optional feature — see
   updated priority order in `SCRIPT_STOCK.md`.
