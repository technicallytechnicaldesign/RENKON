# Changelog — Hydroform

## 2026-07-22

- Removed the turntable feature entirely (checkbox + speed slider, `T` shortcut, toolbar
  and floating-dock buttons, per-preset flags, and the yaw rotation in `project()`) — judged
  not visually interesting enough to keep.
- Added a movement export: **Record WebM** (toolbar button, floating-dock button, `V`
  shortcut). Uses `canvas.captureStream(60)` + `MediaRecorder` (vp9/vp8/webm, whichever the
  browser supports) — native, zero dependencies, consistent with this repo's
  no-external-JS policy and the "drop GIF, no Worker" call already made for the
  parametric-generators tool (see `proc-gen/parametric-generators/docs/ANIMATED_EXPORT.md`).
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
