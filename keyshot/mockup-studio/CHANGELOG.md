# Changelog — KeyShot Mockup Studio

## 2026-07-24 — Scene Randomize + wider animated variation; panel overflow fix

- **Top Randomize button.** Added the shared quick-start bar (generator-ui.css)
  with a one-click **Randomize** that shuffles background, palette, fluid style,
  motif, atmosphere and seed — leaving the user's product placement, finish and
  title untouched. The per-field seed **Roll** stays as the in-panel shuffle.
- **Much wider animated variation.** The animated loops now derive a seeded
  motion **speed** (~0.5–2.4x), a structural **tilt**, and per-seed structural
  picks (orbit ring position/size + ribbon amplitude/offset + particle count;
  reactor core position/size + pipe count + pulse/flow speed; parallax nebula
  position/size + ring geometry + star count + drift; sweep light-sweep speed +
  arc radii + pedestal position). A Randomize now reads genuinely different, not
  a few-pixel shift. All variation is seed-driven and defaults to identity, so
  the Presets tab still renders each concept's original signature look.
- **Layout fix.** On viewports wider than ~1400px the Palette control and the
  Seed+Roll row were overflowing the fixed 300px side column and rendering
  under the preview canvas (invisible / unclickable). field-grid-3 now stacks
  and all grid cells/inputs are min-width:0, so nothing overflows.


## 2026-07-24 — Animated backplates + title + WebM export

The Compositor can now use the four animated loops (previously preview-only in
the Presets tab) as **live backgrounds**: a new **Background** selector switches
between the procedural static scene and Fluid Orbit Loop / Reactor Flow Loop /
Orbital Parallax Hero / Studio Sweep Cinematic. The product, pedestal, shadow
and reflection composite on top of the moving backplate exactly as before.

Added a **Title** section (title + subtitle + top/center/bottom position) that
overlays brand-styled text on the composite, and a **Motion export (WebM)**
block — clip length (4/6/8 s) and video size (720p/1080p) — that records the
animated composite to a downloadable `.webm` via MediaRecorder. Still (PNG/JPG)
export and the static procedural scene are unchanged; the WebM controls only
appear when an animated background is selected. The animated frame renderers
are shared with the Presets tab (one `(ctx,w,h,t)` painter each), so both
surfaces stay in sync.

**Parametric animated backplates + title alignment (same day).** The animated
loops now take an optional `opts` — palette, seed, fluid detail, theme
intensity and light angle — so as a Compositor background they are fully
parametric: the selected palette recolors the whole loop, Roll/seed shifts the
particle and highlight layout, and the atmosphere sliders drive density, glow
and light position. Every factor defaults to identity, so the Presets tab
(which calls the loops with no `opts`) still renders each concept's original
signature look unchanged. The Title overlay also gained a horizontal **Align**
control (left / center / right) alongside the vertical position.

## 2026-07-18 — Motion Lab absorbed as the Presets tab

Mockup Studio is now tabbed: **Compositor** (everything that was already here)
and **Presets** (the four Motion Lab comparison concepts &mdash; Fluid Orbit
Loop, Reactor Flow Loop, Orbital Parallax Hero, Studio Sweep Cinematic &mdash;
carried over functionally unchanged, including the shared pause/reset clock
and fullscreen comparison modal). `keyshot/motion-lab/index.html` now
redirects here (`#presets`) instead of hosting a separate page; the KeyShot
hub tile grid was collapsed from two live tiles to one. See
`keyshot/motion-lab/CHANGELOG.md` for the donor side of this merge.

## 2026-07-18 — Established

Established from the Fluid Forge archive (`fluid_forge_mockup_studio.html`):
reskinned into the RENKON house shell (dark token scale, Space Grotesk/Space
Mono, sharp corners, 1px grid lines) alongside its sibling Backplate Creator.
Every control and the canvas-compositing mechanism — product cutout upload,
drag-to-reposition, placement/scale/rotation, shadow/reflection/pedestal,
scene generator (style/theme/palette/motif/seed + atmosphere sliders), quick
scene variations, and PNG/JPG export — carried over unchanged; only the
visual chrome changed.
