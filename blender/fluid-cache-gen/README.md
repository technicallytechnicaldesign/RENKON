# Fluid Cache Generator

Two Blender (`bpy`) scripts that bake fluid Alembic (`.abc`) caches for import
into KeyShot. Both run **headless inside Blender**, not inside KeyShot — same
adjacent-tool relationship `keyshot/backplate-creator/` has to KeyShot, just
upstream of the render instead of behind the camera. Lives under top-level
`blender/` (not `keyshot/`) because it never runs inside KeyShot itself —
see `../README.md` for why that split exists.

## The two scripts

- **`fluidgen.py`** — real Mantaflow FLIP fluid solver. 4 presets: `jet`
  (nozzle/hose stream), `pipe` (open-pipe flow), `drip` (pinching droplets),
  `splash` (stream-on-plate crown splash). Bakes actual liquid-surface
  dynamics — momentum, collision, pinch-off. Run:
  `blender -b -P fluidgen.py -- <jet|pipe|drip|splash|all> <preview|final>`.
  This is the slow, real-dynamics path — the bake is the expensive part, so
  always validate at `preview` resolution first.
- **`make_fluids.py`** — cheap procedural surfaces, no solver. 4 presets:
  `ocean_swell` (Blender Ocean modifier, keyframed time), `droplet_ripple`
  (Wave modifier, one concentric ring), `flow_turbulence` (Displace modifier
  + scrolling CLOUDS noise driven by a keyframed Empty), `splash_merge` (two
  Wave modifiers summed — two rings crossing). Same CLI shape:
  `blender -b -P make_fluids.py -- <preset|all> <preview|final>`. This is the
  cheap, fast, believable-motion path — animated/displaced mesh, evaluated and
  baked into point positions per frame on export, no solver time at all.

Reach for `fluidgen.py` when the shot needs real impact/pinch-off/crown
dynamics. Reach for `make_fluids.py` when you need liquid-reading motion
behind a product shot fast, and don't need anything to actually react to
anything.

## Requires Blender

Both scripts run in **Blender 4.x, headless**, not in KeyShot:

```
blender -b -P fluidgen.py -- jet preview
blender -b -P make_fluids.py -- ocean_swell preview
```

There is no Blender in this repo's environment or CI, so neither script can
be auto-run or verified here — every run has to happen on a machine with a
real Blender install. Output `.abc` files land in a `fluid_out/` folder
created next to wherever you invoke Blender from. Import the resulting
`.abc` into KeyShot as an animated/deforming mesh (Import → Alembic).

## Status / before real use

**Smoke-tested 2026-07-18 against a real Blender 5.0.1 install.** Both
scripts run correctly on 5.0.1 (a full major version past the 4.x they were
written for) — all `# CHECK`-flagged API names still resolve.

- **`make_fluids.py`** — all 4 presets (`ocean_swell`, `droplet_ripple`,
  `flow_turbulence`, `splash_merge`) ran clean at `preview` res, zero
  `[SKIP]`s, zero `[info] 'x' not settable` guard trips. Every flagged name
  (`Ocean.geometry_mode`, `Ocean.spatial_size`, `Wave.start_position_x/y`,
  `Displace.texture_coords`, the `CLOUDS` texture datablock type,
  `Displace.direction`) is confirmed correct on 5.0.1. Considered working.
- **`fluidgen.py`** — the Mantaflow FLIP bake itself runs clean (no
  exceptions, no `[SKIP]`s) on **all four** presets, but baking without an
  exception is not the same as baking real liquid: reimporting the `.abc`
  output and checking per-frame mesh vertex counts found `jet` and `drip`
  were **silently exporting zero liquid geometry** (an unchanging 8-vert
  domain bounding-box cube every frame, while the file itself was ~4 KB —
  no crash, no `[SKIP]`, just nothing) even though `pipe`/`splash` produced
  real, growing surfaces (10K-125K polys by frame 60). Root causes, found by
  reimport-and-measure rather than assumption:
  - `jet`'s inflow sphere was centered exactly on the domain's boundary edge
    (`x=-1.2` against a domain spanning `x:[-1.2, 1.8]`) — Mantaflow only
    seeds cells strictly inside the domain, so it was seeding almost nothing.
  - `drip`'s inflow radius (0.032 m) was smaller than one preview-resolution
    grid cell (0.046 m) — sub-cell inflow doesn't reliably activate any
    fluid cells.
  **Fixed and reverified** (moved `jet`'s inflow to `x=-1.0`, radius
  0.06→0.12; `drip`'s inflow radius 0.032→0.08): both now produce real
  growing liquid meshes across every checked frame (up to ~39K/~9K polys by
  frame 60). `pipe` and `splash` were unaffected. All four presets in
  `fluidgen.py` are now confirmed producing real liquid mesh at preview res.

**Not yet checked**: `final` resolution tier for either script (only
`preview` was smoke-tested), and neither script's output has been round-
tripped into an actual KeyShot import yet — that's the next real gap before
calling this production-ready. `splash` at preview res alone was **595 MB**
— worth a size/resolution gut-check before committing to `final` tier
routinely.

**GUI run path bug found + fixed (same day)**: the checks above were all run
headless (`blender -b -P ...`). Running either script interactively via the
Text Editor's "Run Script" button instead throws
`AttributeError: 'Context' object has no attribute 'active_object'` inside
`add_domain`/`add_inflow`/`add_collider` (`fluidgen.py`) and `add_grid`/
`build_flow` (`make_fluids.py`) — `bpy.context.active_object` isn't reliably
populated in that interactive execution context, even though it's fine
headless. Fixed by switching all 5 call sites to
`bpy.context.view_layer.objects.active`, which works in both contexts.
Reverified headless (still clean) and interactively (`droplet_ripple` ran
live in the viewport with real propagating ripples). Both run paths now
confirmed working.

## KeyShot note

Both scripts produce liquid-**surface** meshes only — no spray, foam, or
atomized particles come out of either path. Mantaflow's own spray/foam/bubble
particles don't Alembic out as clean mesh; getting atomized droplets needs the
FLIP Fluids addon or a separate particle-meshing pass. Mesh is triangulated on
export (KeyShot 11/2023/2024 choke on n-gons). Object and file names are kept
ASCII. The cryogenic-liquid / other-liquid *look* (IOR, colour, boil-off
vapor) is a KeyShot material choice layered on top in KeyShot — it is not
baked into either cache.

## Files

- `fluidgen.py` — real FLIP solver, 4 presets.
- `make_fluids.py` — procedural no-solver surfaces, 4 presets.
- `README.md` — this file.
- `CHANGELOG.md` — narrative history.

No build step. Both scripts are run directly by Blender's `-P` flag; there is
nothing to install beyond Blender itself.
