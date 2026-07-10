# Script Stock

Project ID: `ksrp-efbe4961`
Last updated: 2026-07-11

Running at-a-glance inventory + priority backlog. Update this file, don't
replace it, as scripts move status.

## Current inventory

| Stage | Area | Script | Status | Notes |
|---|---|---|---|---|
| 2a | BAT | `2a_BAT_STD_VIEW_AA01.py` | ✅ current | Studios-first multi-view batch |
| 2a | BAT | `2a_BAT_TURNTABLE_AA01.py` | ✅ current | Studios-first turntable batch — kept as-is; "fade between angles" request built as a separate `3_` script instead (see backlog) |
| 2b | ANI | `2b_ANI_HERO_REVEAL_AA01.py` | ✅ current | Zoom+crane reveal; ground-setter & `getAnimationInfo()` shape still unconfirmed on your build |
| 1 | HLP | `batch_material_preflight.py` | ⏳ pending rename | Material-template coverage QC → would become `1_HLP_MAT_PREFLIGHT_AA01.py` |
| 3 | PRC | `contact_sheet.py` | ⏳ pending rename | Standalone HTML viewer, not a lux script → would become `3_PRC_CONTACT_SHEET_AA01.py` |
| 2a | BAT | `batch_turntable.py` | 🗑️ approved for archive | Raw-camera-only predecessor of `2a_BAT_TURNTABLE` |
| 2a | BAT | `batch_import_and_render_all_views.py` | 🗑️ approved for archive | Raw-camera-only predecessor of `2a_BAT_STD_VIEW` |
| 0 | NGS | `0_NGS_MAT_STEEL.py` | ❓ exists elsewhere | Not in this project's files |
| 0 | NGS | `0_NGS_PROC_MATS.py` | ❓ exists elsewhere | Not in this project's files |
| 2b | ANI | `2ANI_SCATTERANIMATION_AQ.py` | ❓ exists elsewhere | Scatter tech — reference for the planned particle script |
| 4* | CHK | `3_NGS_CHECK_REPORT.py` | ❓ exists elsewhere | Recommend re-prefixing `3_`→`4_` next time it's in a session |

## Planned / backlog (priority order)

| Pri | Stage | Idea | Status | Depends on |
|---|---|---|---|---|
| P1 | 2b | Hand-staged one-off reveal (particles, rain) | Design | — |
| P1 | 2b | Assembly reveal — Creo-driven (animate an authored explode state) | Not started | Verify explode data survives plugin import |
| P1 | 2b | Assembly reveal — procedural modes (scatter/settle, staggered/sub-assembly build, spiral converge, ghost fade-in) | Not started | — |
| P1 | 2b | Cutaway / cross-section reveal | Not started | — |
| P1 | 1 | Material-name lookup table (Creo → KeyShot) | Not started | — |
| P2 | 3 | Multi-angle fade reel (crossfade between Studios/cameras) | Not started | Consumes stills from `2a_BAT_TURNTABLE`/`2a_BAT_STD_VIEW` |
| P2 | 3 | BOM-driven manifest (opt-in) | Not started | Research Q3 — BOM access method |
| P2 | 2b | Dynamic BOM callouts on assembly renders | Not started | BOM-driven manifest, above |
| P2 | 1 | Studio/camera-rig template library | Not started | — |
| P2 | 0 | Pre-import geometry/appearance validator | Not started | — |
| P2 | 4 | Naming-compliance + render-completeness audit | Not started | — |
| P3 | — | Archive superseded batch scripts | Approved | — |

See `RESEARCH_CREO_KEYSHOT.md` for the thinking behind the backlog.
