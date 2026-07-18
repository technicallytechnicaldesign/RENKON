# KeyShot Mockup Studio

A single-file browser tool for compositing a transparent product cutout onto a
procedurally generated fluid-industrial scene, then art-directing the result live.

- **Scene generator** — the same deterministic Canvas engine as the Backplate
  Creator: 6 fluid styles (Viscous Current, Laminar Stream, Liquid Metal
  Droplets, Ripple Impact, Ink Bloom, Splash Crown) × 4 themes (Pure Fluid,
  Industrial, Space, Industry + Space) × 9 palettes × 11 architecture motifs
  (Mechanical Bay, Orbital Ring, Planet Horizon, Docking Hangar, Pipe Trench,
  Vent Array, Conduit Wall, Reactor Core, Ribbed Bulkhead, Docking Lights,
  Panel Grid), a deterministic seed, and sliders for theme intensity, fluid
  detail, light angle and horizon.
- **Product compositing** — drop or browse a transparent PNG/WebP/JPEG cutout;
  drag it directly on the preview to reposition, or dial in position, scale
  and rotation with sliders. Shadow, reflection and a lit pedestal are each
  independently toggleable and strength-adjustable.
- **Quick scene variations** — a 4-up gallery of alternate theme/palette/motif
  combinations derived from the current seed; preview full-screen or apply one
  to the main stage in a click.
- **Export** — PNG or JPG 95% composite up to 5120×2880, named
  `fluid_mockup_<theme>_<motif>_<style>_<seed>_<w>x<h>.<fmt>`.

## Files

- `index.html` — the tool (self-contained; only external refs are the two
  brand fonts).

No build step. Open `index.html` in a browser, or serve it under the RENKON
Pages base — relative links only.
