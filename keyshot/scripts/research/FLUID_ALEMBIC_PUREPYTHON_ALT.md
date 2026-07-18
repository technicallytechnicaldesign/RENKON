# Fluid Alembic — Pure-Python Alternative (un-chosen)

**UID:** FAPA-7C41A0
**Rev:** 1
**Date:** 2026-07-18
**Type:** research note (reference only — not developed further)
**Audience:** whoever next touches `keyshot/fluid-cache-gen/` or wants to add
a spray/foam pass to it.

---

## What it was

A competing approach to the same problem `fluid-cache-gen/` now solves: how
to get a fluid Alembic (`.abc`) cache into a DCC/render pipeline. Where
`fluidgen.py` and `make_fluids.py` run inside Blender, this alternative was
**pure Python, no Blender dependency at all** — an optional PyAlembic write
path with a JSON-meta + raw-binary fallback when PyAlembic isn't installed.
It targeted **Houdini/Maya import**, not KeyShot directly — no triangulation
pass, no KeyShot n-gon handling, no ASCII-name discipline; it assumed a
downstream DCC would receive and shade the cache before anything reached a
renderer.

It generated three procedural presets, each yielding per-vertex geometry plus
**velocity and density attributes** meant for whitewater/motion-blur shading
downstream:

- `splash_jets` — multiple outlet streams (wobbling tessellated-sphere
  clusters per stream, 3 or 5 streams).
- `spray_mist` — an airborne particle cloud (point cloud, no faces) that
  drifts and disperses over time.
- `surface_turbulence` — a wavy liquid surface built from summed sine
  harmonics over a grid, with a density mask standing in for foam regions.

Like `make_fluids.py`, none of this is a real solve — it's closed-form math
(sin/cos waves, radial falloff) evaluated per frame, not a fluid solver. Frame
data is a hand-rolled `FluidFrame` dataclass (frame, time, vertices, faces,
velocities, density) rather than anything solver-derived.

## Why it was NOT chosen

The Blender FLIP route (`fluidgen.py`) won instead: a real Mantaflow solver
producing actual liquid-surface dynamics (momentum, collision, pinch-off)
beats a no-solver procedural generator, and `fluidgen.py`'s export path is
built KeyShot-first (triangulated, ASCII, direct `.abc` write via Blender's
own Alembic exporter) rather than aimed at a different DCC that would need
its own import/shading step before reaching KeyShot at all. For this
pipeline's actual destination — KeyShot import — the Blender path is the
more direct one.

## Where the source lives now

Preserved as reference, not developed further:
`PROJECTS/RENKON/01_RESEARCH/alembic_purepython_alt/` (workspace path,
outside this git repo — same cross-reference style `keyshot/PICKUP.md` uses
for its `PROJECTS/RENKON/...` pointers). Contents: `README.md`,
`GENERATOR_STRATEGY.md`, `PROJECT_MANIFEST.md`, `alembic_research.md` (the
Alembic-format/physics background), `abc_fluid_generator.py` (the generator
+ PyAlembic/JSON-fallback writer), `example_usage.py` (a custom-viscosity
splash variant).

## Reusable ideas worth remembering

Even though the approach itself wasn't taken forward, a few pieces are worth
keeping in mind if `fluid-cache-gen/` ever grows a spray/foam pass:

- **The JSON-meta + raw-binary fallback pattern.** When no Alembic library
  is available, `abc_fluid_generator.py` still writes a `.json` (frame
  count, fps, per-frame vertex/face counts) plus a `.bin` of packed
  float-triplet vertex/velocity data — a format any downstream tool can read
  without an Alembic dependency at all. Worth remembering as a fallback
  shape if a future export target doesn't have Alembic support either.
- **The procedural particle splash/spray/turbulence approach itself** —
  useful groundwork if `make_fluids.py` ever needs an actual point-cloud
  spray/foam preset (its current honest limit is that it's surface-only,
  no droplets separating from the sheet).
- **Per-point velocity + density attributes.** Baking velocity into the
  cache (for motion blur / whitewater-style shading) and density (as an
  alpha/thickness proxy) are both directly reusable ideas for extending
  either Blender script, independent of whether the geometry comes from a
  real solve or a procedural surface.
