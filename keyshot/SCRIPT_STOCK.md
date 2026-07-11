# Script Stock

Project ID: `ksrp-efbe4961`
Last updated: 2026-07-11 (naming cleanup + 8 backlog items delivered; stage 0 now populated)

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
| 0 | NGS | `0_NGS_MAT_STEEL.py` | ❓ exists elsewhere | Not in this project's files |
| 0 | NGS | `0_NGS_PROC_MATS.py` | ❓ exists elsewhere | Not in this project's files |
| 2b | ANI | `2ANI_SCATTERANIMATION_AQ.py` | ❓ exists elsewhere | Scatter tech — reference for the planned particle script |
| 4* | CHK | `3_NGS_CHECK_REPORT.py` | ❓ exists elsewhere | Recommend re-prefixing `3_`→`4_` next time it's in a session |

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
| P2 | 1 | Studio/camera-rig template library | Not started | — |
| P2 | 0 | STEP-file preflight (units, filename hygiene, material-name hints) | ✅ done — `0_VAL_STEP_PREFLIGHT_AA01.py` | Forum-grounded: STEP unit/scale mismatch is the #1 reported KeyShot import complaint (see RESEARCH_CREO_KEYSHOT.md) |
| P2 | 0 | Trial-import geometry/appearance health check | ✅ done — `0_VAL_IMPORT_HEALTH_AA01.py` | This is the original "pre-import geometry/appearance validator" item, now split out and grounded in specific forum reports (missing assembly components, tessellation gaps, failed imports) |
| P2 | 0 | Orientation / up-axis sanity check | ✅ done — `0_VAL_ORIENTATION_CHECK_AA01.py` | Forum-grounded: KeyShot is always Y-up, source CAD varies, easy to get wrong unattended |
| P2 | 4 | Naming-compliance + render-completeness audit | ✅ done — `4_CHK_AUDIT_AA01.py` | — |
| P3 | — | Archive superseded batch scripts | ✅ done — moved to `scripts/archive/` | — |
| P2 | 2b | Assembly reveal — sub-assembly build (grouped convergence) | Not started | Extension of `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py`; extension point noted in that script's `get_parts()`/`schedule_staggered_windows()` |

See `RESEARCH_CREO_KEYSHOT.md` for the thinking behind the backlog.
