# Parametric Generators

A single-file, no-build browser tool for the rendering & overlay compositing
pipeline. Two procedural/parametric generators under one shell:

1. **Overlay Asset Customizer** — live gallery of 69 SVG overlays across 8
   categories (fluid flow, splashes, callouts, arrows, pings, frame chrome,
   backgrounds, wildcards). Type → subtype → customize drill-down, global
   palette control (7 roles, including a `caution` red for alarm/status
   assets), per-asset opacity/thickness/speed/roundness sliders, custom text
   on labeled assets, PNG and frame-sequence export. Every asset also carries
   a two-axis `fn`/`vibe` tag (what job it does × how it feels); a FN/VIBE
   chip bar on the landing view filters the whole library across categories
   (OR within an axis, AND across axes — "flow AND dramatic"), with the
   active filter bookmarkable in the URL hash (`#overlay-kit?fn=flow&vibe=dramatic`).
2. **Texture & Bump Map Generator** — procedural grayscale texture/height maps
   (noise, grid, scratches, splotches, plus a "Pro Finish" group) with a
   simulated-relief bump preview. Every pattern has a live, seamless-looping
   animation (Play); export a static PNG, the animated loop as a numbered PNG
   frame sequence (precise, for feeding a render engine), or that same loop as
   a single WebM clip (convenient, lossy — a shareable preview, not
   texture-precision data).

## Run it

Open [`index.html`](index.html) directly in a browser. No build step, no install,
no external JS dependencies — everything is native browser APIs (Canvas,
`blob:` URLs, `MediaRecorder`/`captureStream`).

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
  automatically (see handoff brief §4). Give it a `tags: { fn: [...], vibe: [...] }`
  field too (1–2 tags per axis, 3 max) — the FN/VIBE chip bar and filtered grid
  are generic over `TAG_AXES`/`TAG_ICONS`, so a tagged asset shows up in filter
  results with no other wiring. New tag values need a `TAG_ICONS` entry (16×16,
  stroke-only) and a slot in `TAG_AXES`.

