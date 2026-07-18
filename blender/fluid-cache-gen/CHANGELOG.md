# Changelog — KeyShot Fluid Cache Generator

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
