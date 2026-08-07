# Hydroform

A self-contained, single-file browser app: a deterministic, real-time **Canvas 2D
procedural water / fluid generator** with pipe and process-flow networks and a
studio glass-tube presentation mode. No build step, no framework, no external JS —
only the two RENKON brand fonts load from Google Fonts. Open `index.html` directly.

Every seed produces a repeatable variation.

## Modes

- **Impact splash** — crown-sheet breakup, central impact plume, secondary droplets, surface ripples.
- **Pressurized side jet** — a continuous stream that breaks up, arcs under gravity, and splashes on contact.
- **Vertical fountain** — a nozzle with adjustable cone spread, droplet breakup, drift, and mist.
- **Pipe flow** — seeded pipe routing with animated internal flow streaks, bubbles/air entrainment, and outlet flow. Networks:
  - **Straight pipe** — minimal single straight run, no pump/valves/branches.
  - **Single run / Tee branch / Manifold / Bypass loop** — a miniature process system with a centrifugal pump, animated impeller, junction collars, and valves (count + opening).
  - Pipe materials: industrial metal, transparent glass, frosted glass, clear acrylic, polished chrome, smoked glass, technical cutaway.
  - Illustrative live hydraulic readouts (inlet / outlet pressure, pressure loss, estimated flow). This is a visual model, **not** an engineering-certified hydraulic solver.
- **Studio glass-tube presentation** — bright studio backdrop, soft floor reflection, hidden clutter, for KeyShot-style clean renders. Pairs with fullscreen.

## Controls

Flow (pressure, spread, angle, nozzle, density), fluid behavior (gravity, drag, surface
tension, turbulence, wind, droplet scale), and look development (water/background colour,
opacity, highlight, motion streak, depth/perspective, surface & ripples, specular sparkle).
Presets: Clean studio, Violent impact, Silky jet, Fine mist, Process line, Simple straight
pipe, Studio glass tube. Randomize re-rolls the seed and settings. Export writes a PNG
(with optional transparent background); Record writes a WebM clip of the live sim via
`canvas.captureStream()` + `MediaRecorder` — native, no dependency, no fixed duration
(click to start, click again to stop and download).

## Keyboard shortcuts

- **H** — hide / show UI
- **V** — start / stop recording a WebM clip
- **F** — fullscreen
- **Space** — pause / resume
- **R** — replay

## House style

Reskinned into the RENKON dark shell (Space Grotesk / Space Mono, dark token palette,
lotus-root header, sharp corners, 1px grid lines). Flow/preview cues use the fluid teal
(`--c-fluid`); orange (`--c-accent`) is reserved for interactive controls and active states.
Relative links only — works both as a local file and served under the `/RENKON/` Pages base.
