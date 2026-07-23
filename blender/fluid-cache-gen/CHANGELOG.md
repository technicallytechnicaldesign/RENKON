# Changelog — KeyShot Fluid Cache Generator

## 2026-07-19 — Async-export bug fixed, fresh full preview-tier bake run

Third bug, found via the same "interactive GUI diverges from headless"
pattern as the `active_object` fix: `bpy.ops.wm.alembic_export` runs as an
async background job when called from the Text Editor's Run Script button,
so the next preset's scene `reset()` was killing in-flight exports before
they finished writing — GUI runs showed correct viewport animation but wrote
zero `.abc` files. Fixed by adding `as_background_job=False` to the `kw`
dict in both scripts' `export()` (forces synchronous export), with a
try/except fallback for older Blender builds.

Then ran a full fresh headless bake of all four `fluidgen.py` presets
(jet/pipe/drip/splash) at `preview` res from `E:\blender\blender.exe`
(5.0.1) — ~114s total wall-clock, verified via the reimport-and-measure
harness (real, non-zero, growing vertex counts on every preset), and
rendered one diagnostic still per preset confirming visually distinct
dynamics (jet arc, pipe fan-out, drip column, splash crown). Total output:
1.36 GB (`fluid_out/` — now gitignored, never commit). Full numbers in
`README.md`'s Status section. Synchronous-export fix confirmed headless;
not yet re-confirmed in the GUI (the case it was written for).

## 2026-07-18 — Smoke-tested against real Blender 5.0.1, jet/drip bug fixed

Ran both scripts for the first time against a real Blender install
(5.0.1, found at `E:\blender\`) instead of guessing from the API docs.
`make_fluids.py`: all 4 presets clean, every `# CHECK`-flagged
modifier/property name confirmed correct. `fluidgen.py`: baking completed
without exceptions on all 4 presets, but reimporting the `.abc` output and
checking per-frame vertex counts (not just trusting "no exception was
thrown") found `jet` and `drip` were silently exporting empty liquid
geometry — `jet`'s inflow sphere sat on the domain boundary edge, `drip`'s
inflow radius was sub-cell at preview resolution. Fixed both (inflow
position/radius tuning) and reverified with the same reimport-and-measure
check — all four presets now produce real, growing liquid meshes. `pipe`
and `splash` were correct from the start. Full detail in `README.md`'s
Status section. Not committed — left for review alongside the fix.

Maker then ran `make_fluids.py` interactively in the Blender GUI (Text
Editor → Run Script) and hit a second, different bug the headless testing
above never exercised: `AttributeError: 'Context' object has no attribute
'active_object'` in `add_grid` — `bpy.context.active_object` isn't reliably
populated when a script runs via the Text Editor's Run Script button, only
when run headless. Fixed all 5 call sites across both scripts
(`bpy.context.active_object` → `bpy.context.view_layer.objects.active`),
reverified both headless and interactively. Maker confirmed `droplet_ripple`
running live in the viewport. Both run paths (headless CLI, interactive GUI)
now confirmed working.

## 2026-07-18 — Established

Established the sub-area from a two-zip inbox drop. Kept the chosen route —
Blender's Mantaflow FLIP solver (`fluidgen.py`, 4 presets: jet/pipe/drip/
splash) — as the real-dynamics generator. The drop's own manifest promised a
second script that the zip never actually contained, so wrote the missing
`make_fluids.py`: 4 procedural, no-solver surface presets (ocean_swell,
droplet_ripple, flow_turbulence, splash_merge) sharing `fluidgen.py`'s export
path and CLI shape, for when believable liquid motion is enough and a real
bake isn't worth the time.

Both scripts are unverified in a real Blender — there is no Blender in this
environment to run one against. `fluidgen.py` was already untested outside
Blender per its own docstring; `make_fluids.py` additionally needs a 4.x
smoke-test before production use, since several of its modifier/property
names are best-effort against the API (flagged `# CHECK` inline).

The un-chosen alternative — a pure-Python, no-Blender fluid-cache generator
aimed at Houdini/Maya rather than KeyShot — was filed as research rather than
developed further; see
`keyshot/scripts/research/FLUID_ALEMBIC_PUREPYTHON_ALT.md`.
