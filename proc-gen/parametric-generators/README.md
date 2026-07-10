# Parametric Generators

A single-file, no-build browser tool for the rendering & overlay compositing
pipeline. Two procedural/parametric generators under one shell:

1. **Overlay Asset Customizer** — live gallery of 44 SVG overlays (fluid flow,
   splashes, callouts, arrows, pings, frame chrome). Type → subtype → customize
   drill-down, global palette control, per-asset opacity/thickness/speed/roundness
   sliders, custom text on labeled assets, PNG export. (GIF export is present but
   currently broken — see below.)
2. **Texture & Bump Map Generator** — procedural grayscale texture/height maps
   (noise, grid, scratches, splotches) with a simulated-relief bump preview and
   PNG export. Static output for now; animated maps are the next milestone.

## Run it

Open [`index.html`](index.html) directly in a browser. No build step, no install.
One CDN dependency (`gif.js`, for the not-yet-working GIF export); everything else
is self-contained.

## Files

| Path | What it is |
|---|---|
| `index.html` | The whole app. |
| `CHANGELOG.md` | Version history + iteration notes (replaces the old `toolkit_N.html` scheme). |
| `docs/HANDOFF_BRIEF_v2.md` | Architecture, design-system rationale, known issues, and roadmap. Read this before making changes. |

## Iterating on this tool

- The app file stays named `index.html` — **do not** create `index_8.html` etc.
  Commit changes to git instead; that's the version history now.
- Log notable changes in [`CHANGELOG.md`](CHANGELOG.md) and tag milestones in git
  (`paramgen-vN`).
- Adding a new overlay asset is a single object in the `ASSETS` array — the grids,
  palette wiring, sliders, and export all pick it up from the manifest
  automatically (see handoff brief §4).

## Known issue

**GIF export does not work** in the artifact/sandbox environment (cross-origin
Worker + CSP). PNG export works. The recommended fix is to route around `gif.js`
entirely (`MediaRecorder` + `canvas.captureStream()`, or a PNG frame sequence) —
full diagnosis in [`docs/HANDOFF_BRIEF_v2.md`](docs/HANDOFF_BRIEF_v2.md) §3.
