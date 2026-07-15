# Script Stock

Project ID: `ksrp-efbe4961`
Last updated: 2026-07-15 (retired the NGS scripts — `1_HLP_MAT_GENERATOR` is now the single source of truth for the material generator; made it KeyShot-load-safe + fixed the empty-dialog-default crash; earlier: filed the generator into stage 1, synthesised the AUTO/PRO launcher research, added masked-wear + launcher backlog)

Running at-a-glance inventory + priority backlog. Update this file, don't
replace it, as scripts move status.

## Current inventory

| Stage | Area | Script | Status | Notes |
|---|---|---|---|---|
| 0 | VAL | `0_VAL_STEP_PREFLIGHT_AA01.py` | ✅ current | STEP-file preflight (not a lux script) — unit/scale declaration check, filename hygiene, duplicate base names, best-effort material-name hints. Forum-grounded: unit/scale mismatch is the #1 reported KeyShot import complaint |
| 0 | VAL | `0_VAL_IMPORT_HEALTH_AA01.py` | ✅ current | Trial-import geometry/appearance health check — bounding-box sanity, object-count sanity, Studio/camera presence, before committing a folder to the full batch pass |
| 0 | VAL | `0_VAL_ORIENTATION_CHECK_AA01.py` | ✅ current | Orientation/up-axis sanity check — flags statistical footprint-ratio outliers across a batch. Explicitly a review-flagging heuristic, not a fixer |
| 1 | HLP | `1_HLP_MAT_PREFLIGHT_AA01.py` | ✅ current | Material-template coverage QC — renamed from `batch_material_preflight.py` |
| 1 | HLP | `1_HLP_MAT_LOOKUP_AA01.py` | ✅ current | Creo → KeyShot material-name lookup table; applies templates per object. Per-object apply method is unconfirmed on your build — probes candidates, reports which worked |
| 1 | HLP | `1_HLP_MAT_GENERATOR_AA02.py` | ✅ current | Procedural material *variant* generator — toggleable feature layers (noise/scratches/spots/cellular/edges/roughness/colour) onto a metal/plastic base at a wear level, auto-named `MAT-<TYPE>-<WEAR>-<hex>`. Loud bump layers capped + `1/√n` damped. Now includes the **masked-wear base** (opt-in scratches→edges via Curvature, spots→cavities via Occlusion, composited through Color Composite; degrades to unmasked on any wiring failure). Made **KeyShot-load-safe** 2026-07-15 (f-string-free + ASCII-only — the old rev wouldn't load). Cellular + Colour Gradient are getattr-guarded experimental layers; mask input-slot names are probe-and-confirm on first real run |
| 2a | BAT | `2a_BAT_STD_VIEW_AA01.py` | ✅ current | Studios-first multi-view batch |
| 2a | BAT | `2a_BAT_TURNTABLE_AA01.py` | ✅ current | Studios-first turntable batch — kept as-is; "fade between angles" request built as a separate `3_` script instead (see backlog) |
| 2b | ANI | `2b_ANI_HERO_REVEAL_AA01.py` | ✅ current | Zoom+crane reveal; ground-setter & `getAnimationInfo()` shape still unconfirmed on your build |
| 2b | ANI | `2b_ANI_CUTAWAY_REVEAL_AA01.py` | ✅ current | Cutaway/cross-section reveal — clip plane sweep through an assembly, camera static. Clipping-plane & bounding-box APIs unconfirmed on your build — probes candidates, degrades to unclipped with a warning |
| 2b | ANI | `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py` | ✅ current | Procedural assembly reveal — 4 modes (scatter_settle, staggered_build, spiral_converge, ghost_fade), camera static, parts converge via relative transform deltas. Per-node transform composition, bounding-box sizing, and opacity control all unconfirmed — probes candidates, degrades gracefully. Sub-assembly build is a follow-on, not implemented |
| 3 | PRC | `3_PRC_CONTACT_SHEET_AA01.py` | ✅ current | Standalone HTML viewer (not a lux script) — renamed from `contact_sheet.py` |
| 3 | PRC | `3_PRC_FADE_REEL_AA01.py` | ✅ current | Multi-angle crossfade reel from batch stills — pure CSS `@keyframes`, no ffmpeg/dependencies |
| 4 | CHK | `4_CHK_AUDIT_AA01.py` | ✅ current | Naming-compliance + render-completeness audit — first script in stage 4 |
| 2a | BAT | `archive/batch_turntable.py` | 🗑️ archived | Raw-camera-only predecessor of `2a_BAT_TURNTABLE_AA01.py` — moved to `scripts/archive/`, out of the active pipeline |
| 2a | BAT | `archive/batch_import_and_render_all_views.py` | 🗑️ archived | Raw-camera-only predecessor of `2a_BAT_STD_VIEW_AA01.py` — moved to `scripts/archive/`, out of the active pipeline |
| 2b | ANI | `2ANI_SCATTERANIMATION_AQ.py` | ❓ exists elsewhere | Scatter tech — reference for the planned particle script |

_NGS scripts retired 2026-07-15: the whole `0_NGS_*` deploy on the KeyShot machine is being dropped. `0_NGS_PROC_MATS.py` (the deployed material generator) is superseded by `1_HLP_MAT_GENERATOR` here, which is now the single source of truth — deploy from this repo, not from the old NGS copies._

## Planned / backlog (priority order)

| Pri | Stage | Idea | Status | Depends on |
|---|---|---|---|---|
| P1 | 2b | Hand-staged one-off reveal (particles, rain) | Design | — |
| P1 | 2b | Assembly reveal — Creo-driven (animate an authored explode state) | Not started | Verify explode data survives plugin import |
| P1 | 2b | Assembly reveal — procedural modes (scatter/settle, staggered build, spiral converge, ghost fade-in) | ✅ done — `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py` (sub-assembly build split out as a follow-on, see below) | — |
| P1 | 2b | Cutaway / cross-section reveal | ✅ done — `2b_ANI_CUTAWAY_REVEAL_AA01.py` | — |
| P1 | 1 | Material-name lookup table (Creo → KeyShot) | ✅ done — `1_HLP_MAT_LOOKUP_AA01.py` | — |
| P2 | 3 | Multi-angle fade reel (crossfade between Studios/cameras) | ✅ done — `3_PRC_FADE_REEL_AA01.py` | Consumes stills from `2a_BAT_TURNTABLE`/`2a_BAT_STD_VIEW` |
| P2 | 3 | BOM-driven manifest (opt-in) | Not started | Research Q3 — BOM access method |
| P2 | 2b | Dynamic BOM callouts on assembly renders | Not started | BOM-driven manifest, above |
| P1 | 1 | Masked / targeted wear in the material generator — edge-only scratches (Curvature mask), cavity grime (Occlusion mask), occasional fingerprints (image + noise-gated roughness) via a per-layer `masked()` Color-Composite stage | Research done | Spec: `scripts/research/MASKED_WEAR_RESEARCH.md` (MWR-9C4E21). Node ids confirmed scriptable; no label API so mask the effect, not a label. Recipe A (edge scratches) is the first build |
| P1 | 2b | **KeyShot-load-safety pass on `2b_ANI_*`** — `2b_ANI_ASSEMBLY_PROCEDURAL`, `2b_ANI_CUTAWAY_REVEAL`, `2b_ANI_HERO_REVEAL` all use f-strings + non-ASCII, the exact combo that stops a script loading in the KS console (Python < 3.6, ASCII-sensitive). Convert to `.format()` + ASCII like the generator + the other siblings | Not started | Same fix that unblocked `1_HLP_MAT_GENERATOR`; these three are the only remaining offenders (`grep` non-ascii/f-string across `scripts/`) |
| P2 | 1 | Studio/camera-rig template library | Not started | — |
| P2 | 0 | STEP-file preflight (units, filename hygiene, material-name hints) | ✅ done — `0_VAL_STEP_PREFLIGHT_AA01.py` | Forum-grounded: STEP unit/scale mismatch is the #1 reported KeyShot import complaint (see RESEARCH_CREO_KEYSHOT.md) |
| P2 | 0 | Trial-import geometry/appearance health check | ✅ done — `0_VAL_IMPORT_HEALTH_AA01.py` | This is the original "pre-import geometry/appearance validator" item, now split out and grounded in specific forum reports (missing assembly components, tessellation gaps, failed imports) |
| P2 | 0 | Orientation / up-axis sanity check | ✅ done — `0_VAL_ORIENTATION_CHECK_AA01.py` | Forum-grounded: KeyShot is always Y-up, source CAD varies, easy to get wrong unattended |
| P2 | 4 | Naming-compliance + render-completeness audit | ✅ done — `4_CHK_AUDIT_AA01.py` | — |
| P3 | — | Archive superseded batch scripts | ✅ done — moved to `scripts/archive/` | — |
| P2 | 2b | Assembly reveal — sub-assembly build (grouped convergence) | Not started | Extension of `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py`; extension point noted in that script's `get_parts()`/`schedule_staggered_windows()` |
| P1 | — | Shared module (L3) — de-duplicate Studio resolution, manifest logging, `centerAndFit`+padding, units/bbox classify out of the ~4 scripts that copy it | Design | The unblocker for both the launcher and the scale classifier; extract before writing either (see synthesis §4) |
| P1 | — | `RUN_ALL.py` launcher (L1) — one spine, two doors (AUTO headless / PRO dialog): import → classify tier → preflight hard-gate → stage router → contact sheet | Design | Shared module (above). AUTO/PRO/EXPERT design in `RENDER_PIPELINE_ARCHITECTURE.md` |
| P2 | — | `watch.py` orchestrator (L0, out-of-KeyShot) — hot-folder watch on `01_FOR_PROCESSING/*`, resolve mode from subfolder, move-on-success lifecycle | Design | `RUN_ALL.py` first |
| P2 | 0 | 5-tier bbox-diagonal scale classification (Micro→Extra-large, ~35,000:1 range) — per-tier overrides dict merged onto base options | Design | Needs a calibration pass over real parts for breakpoints; `getSceneInfo()` unit-scale + `getBoundingBox(world=True)` both confirmed |

See `RESEARCH_CREO_KEYSHOT.md` for the thinking behind the backlog — its
2026-07-15 synthesis section covers the launcher layer, and the two source
docs in `scripts/research/` (RPA-7B2E4D, RPR-3F9C1A) have the full detail.
