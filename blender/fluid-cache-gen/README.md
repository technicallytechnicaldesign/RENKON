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

**Neither script has been smoke-tested in a real Blender yet.** Both are
written to fail loud one preset at a time (`all` keeps going and reports which
presets skipped, rather than aborting the whole run).

- `fluidgen.py` is untested outside a real Blender — its own docstring says
  so. The Mantaflow API calls are standard 4.x, but nothing here has been
  run against an actual build.
- `make_fluids.py` is newer and needs the same verification pass, plus more:
  several `bpy` modifier/property names inside it are best-effort against the
  4.x API and flagged inline with `# CHECK` comments (`Ocean.geometry_mode`,
  `Wave.start_position_x/y`, `Displace.texture_coords`, the `CLOUDS` texture
  datablock type, and a few others). The first real Blender run **is** the
  verification pass for those names — whichever ones are wrong will surface
  as a `[SKIP <preset>]` traceback rather than a silent wrong result, but they
  haven't been confirmed correct yet. Don't treat `make_fluids.py` as
  working until that run has happened.

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
