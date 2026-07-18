# keyshot

KeyShot automation for the Creo &rarr; KeyShot pipeline, plus scene/material
binaries as they arrive.

Live pages: [`index.html`](index.html) &mdash; hub tile grid, Scripts is the
first live area; [`scripts.html`](scripts.html) &mdash; script inventory
(filterable, active-only by default), backlog, and conventions;
[`backplate-creator/`](backplate-creator/) &mdash; procedural fluid-backplate
generator + a curated pack of six rendered 16:9 render environments.

## Structure

```
keyshot/
  scripts/            current lux/luxmath scripts (batch render, turntable, animation, helpers)
  scripts/archive/    superseded scripts, kept for reference only — not part of the active pipeline
  backplate-creator/  single-file backplate tool (generator + curated 6-JPG gallery), assets/ holds the renders
  index.html          hub page — tile grid of KeyShot areas
  scripts.html        script inventory page (filters, backlog, conventions)
  SCRIPT_STOCK.md            at-a-glance inventory + prioritized backlog
  RESEARCH_CREO_KEYSHOT.md   research notes behind the backlog
```

`SCRIPT_STOCK.md` is the source of truth for script status — update it,
don't replace it, as scripts move through the pipeline.

## Current scripts (`scripts/`)

| Script | Stage | What it does |
|---|---|---|
| [`0_VAL_STEP_PREFLIGHT_AA01.py`](scripts/0_VAL_STEP_PREFLIGHT_AA01.py) | 0 &middot; VAL | STEP-file preflight — unit/scale, filename hygiene, duplicates, material-name hints |
| [`0_VAL_IMPORT_HEALTH_AA01.py`](scripts/0_VAL_IMPORT_HEALTH_AA01.py) | 0 &middot; VAL | Trial-import geometry/appearance health check before a full batch commit |
| [`0_VAL_ORIENTATION_CHECK_AA01.py`](scripts/0_VAL_ORIENTATION_CHECK_AA01.py) | 0 &middot; VAL | Orientation/up-axis sanity check — flags statistical footprint-ratio outliers |
| [`1_HLP_MAT_PREFLIGHT_AA01.py`](scripts/1_HLP_MAT_PREFLIGHT_AA01.py) | 1 &middot; HLP | Material-template coverage QC, ahead of a full batch render |
| [`1_HLP_MAT_LOOKUP_AA01.py`](scripts/1_HLP_MAT_LOOKUP_AA01.py) | 1 &middot; HLP | Creo &rarr; KeyShot material-name lookup table, applies templates per object |
| [`1_HLP_MAT_GENERATOR_AA02.py`](scripts/1_HLP_MAT_GENERATOR_AA02.py) | 1 &middot; HLP | Procedural material variant generator &mdash; toggleable feature layers onto a metal/plastic base at a wear level |
| [`2a_BAT_STD_VIEW_AA01.py`](scripts/2a_BAT_STD_VIEW_AA01.py) | 2a &middot; BAT | Studios-first multi-view batch render |
| [`2a_BAT_TURNTABLE_AA01.py`](scripts/2a_BAT_TURNTABLE_AA01.py) | 2a &middot; BAT | Studios-first 360&deg; turntable batch |
| [`2b_ANI_HERO_REVEAL_AA01.py`](scripts/2b_ANI_HERO_REVEAL_AA01.py) | 2b &middot; ANI | Zoom+crane hero reveal, synced to Model Set animation |
| [`2b_ANI_CUTAWAY_REVEAL_AA01.py`](scripts/2b_ANI_CUTAWAY_REVEAL_AA01.py) | 2b &middot; ANI | Cutaway / cross-section reveal, sweeps a clip plane through an assembly |
| [`2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py`](scripts/2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py) | 2b &middot; ANI | Procedural assembly reveal — scatter/settle, staggered build, spiral converge, ghost fade |
| [`3_PRC_CONTACT_SHEET_AA01.py`](scripts/3_PRC_CONTACT_SHEET_AA01.py) | 3 &middot; PRC | Standalone HTML contact sheet from a batch's rendered output |
| [`3_PRC_FADE_REEL_AA01.py`](scripts/3_PRC_FADE_REEL_AA01.py) | 3 &middot; PRC | Multi-angle crossfade reel between Studio/camera stills, pure CSS, no dependencies |
| [`4_CHK_AUDIT_AA01.py`](scripts/4_CHK_AUDIT_AA01.py) | 4 &middot; CHK | Naming-compliance + render-completeness audit |

### Archived (`scripts/archive/`)

| Script | Superseded by |
|---|---|
| `batch_turntable.py` | `2a_BAT_TURNTABLE_AA01.py` |
| `batch_import_and_render_all_views.py` | `2a_BAT_STD_VIEW_AA01.py` |

## Naming convention

`{PREFIX}_{AREA}_{NAME}_{REV}.py`

- **PREFIX** — pipeline stage: `0_` pre-checks &middot; `1_` pre-render/cam/material/scene
  helpers &middot; `2a_` batch renders &middot; `2b_` animation &middot; `3_` after-processing &middot;
  `4_` post-checks/other automation
- **AREA** — 3-letter area code: `BAT` batch, `ANI` animation, `HLP` helper, etc.
- **NAME** — short description, 2-4 words
- **REV** — `XX01`: letters step up for a larger/breaking change (`AA` &rarr; `AB`,
  resets number to `01`), number steps up for a routine change (`AA01` &rarr; `AA02`)

Each script's internal KeyShot dialog `id=` (e.g. `id="renderturntables.py.luxion"`)
is left untouched on purpose — it's a persistence key KeyShot uses to remember
last-used dialog field values, not a display name.

## Notes

- KeyShot scripting is Python 3.10+, using the `lux` / `luxmath` modules.
- Headless CLI execution is supported for scripts marked `HEADLESS COMPLIANT`.
  Headless automation still needs a machine with a **licensed KeyShot install**;
  GitHub-hosted Actions runners can't run it.
- Studios (camera + environment + image style, paired) are preferred over raw
  Cameras throughout the batch/animation scripts — raw cameras leave lighting
  as whatever's already active, which is wrong for parts with multiple
  lighting setups.
- Install `git lfs` (`git lfs install`) before committing any binary scene
  files, or the LFS pointers won't be generated.
