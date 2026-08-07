# Changelog — Hydroform

## 2026-07-24 — "Surprise me" variations grid

- Added a **Variations** button (toolbar) that opens a modal contact sheet of
  **12 randomized snapshots** (mode + seed + dynamics), each rendered by running
  the sim with that variant's settings, warming it up ~110 steps, and copying
  the main canvas into a thumbnail. **Reroll** for a fresh set; **click a tile to
  adopt** its settings (pushed to the sliders + a live reset). Colours stay as
  the current pick so the grid reads as one palette. The modal backdrop hides
  the brief main-canvas flicker during generation. (Same feature added to the
  sibling Pipeform tool, keyed on pipe network + seed.)

## 2026-07-24

- Added a **Keyable background** control (in the appearance section, also applied
  to the sibling Pipeform tool). WebM records the live canvas and can't hold an
  alpha channel, so the existing "Transparent PNG export" left WebMs with the
  atmospheric gradient baked in. The new control fills a **flat, uniform solid
  colour** behind the fluid instead — swatches for None (scene) · Black · White ·
  Key green · Key blue · Key magenta, plus a custom colour picker.
  - Applies **live** (so the WebM carries it) and to both PNG and WebM, via a
    branch in `render()` that replaces `drawBackground()`'s gradient with a flat
    `fillRect` when a key colour is active. "None" keeps the original scene +
    transparent-PNG behaviour untouched.
  - Note in the control reminds you to switch Surface & ripples off for the
    cleanest key (the surface band is semi-transparent over the fill).

## 2026-07-22

- Removed the turntable feature entirely (checkbox + speed slider, `T` shortcut, toolbar
  and floating-dock buttons, per-preset flags, and the yaw rotation in `project()`) — judged
  not visually interesting enough to keep.
- Added a movement export: **Record WebM** (toolbar button, floating-dock button, `V`
  shortcut). Uses `canvas.captureStream(60)` + `MediaRecorder` (vp9/vp8/webm, whichever the
  browser supports) — native, zero dependencies, consistent with this repo's
  no-external-JS policy and the "drop GIF, no Worker" call already made for the
  parametric-generators tool (see the ANIMATED_EXPORT brief, private lab repo).
  Click to start, click again to stop; the clip downloads as
  `hydroform-<mode>-seed-<seed>.webm`. Unlike the texture generator's deterministic
  frame-sequence export, Hydroform's sim is stateful/live rather than time-parametrized, so
  it records the actual running loop instead of scrubbing a `state.time` value.

## 2026-07-18

- Imported from the Hydroform bundle (studio-turntable superset build) and reskinned into
  the RENKON house shell (Space Grotesk / Space Mono, dark token palette, lotus-root header).
- Kept the entire working engine intact: all four generators (impact splash, pressurized jet,
  vertical fountain, pipe flow), the process-flow playground (tee / manifold / bypass loop,
  centrifugal pump, valves, junction collars, hydraulic readouts), the straight-pipe and
  studio glass-tube modes, the turntable / fullscreen / hide-UI presentation edition,
  keyboard shortcuts (H / T / F / Space / R), presets, and PNG export (incl. transparent).
- Rebuilt only the chrome: replaced the Inter font, the blue accent palette, the rounded
  glass cards, and the radial-glow body background with the RENKON tokens — sticky
  `#app-header` with the lotus-root mark + `RENKON` wordmark, `Parametric Assets / Hydroform`
  crumbs, `FLUID · CANVAS` right-mark, flat `var(--bg)` page, `var(--stage-bg)` canvas
  backdrop, teal flow cues, orange interactive accents, sharp corners, and uppercase
  letter-spaced Space Mono labels. Toggles converted to native accent-coloured checkboxes;
  content moved inside `<main id="app-main">` for `reveal.js`.
- Retuned the two brand-blue defaults to tokens: default water colour → `#4fd1d9`
  (`--c-fluid`), default background → `#060a10` (`--stage-bg`). Canvas diagnostic labels
  (PUMP / pressure tags) now render in Space Mono.
- The three earlier source iterations (`water_splash_jet_generator.html`,
  `water_splash_jet_generator_v1_pipe.html`, `hydroform_process_flow_generator.html`) were
  dropped as superseded; this is the studio-turntable superset build only.
