# Changelog — KeyShot Mockup Studio

## 2026-07-24 — Fluid motion overlays

- The overlay picker gained a **Fluid (particle)** group — **Jet · Fountain ·
  Spray · Splash** — composited as motion layers exactly like the SVG overlays
  (colour / size / position / rotation / speed / opacity, into stills + WebM).
- Powered by a new shared **`assets/fluid-engine.js`**: a self-contained particle
  sim that renders on a **transparent** canvas (so it composites by alpha — no
  keying needed inside the studio) and pre-renders a **perfectly loopable** clip.
  The loop is exact by construction: emission is reset to a deterministic
  function of phase each period and the timestep is fixed, so after a one-period
  warm-up the particle state at `t` equals the state at `t + P`.
- The overlay colour drives the fluid colour. A dedicated **Density** slider
  (shown only for fluid overlays; the SVG "Line weight" slider hides in its
  place) drives the particle emission rate across a wide range — from a tiny
  dribble to a full jet of water (~0.04× to 4× the base rate). `rebuildOverlay`
  branches on a `fluid:<style>` value to the fluid engine; everything downstream
  (draw-time transform, WebM) is shared with the SVG overlay path.

## 2026-07-24 — Copy link + collapsible controls

- **Copy link** (Export section) encodes the scene / overlay / title controls
  into the URL hash; opening the link reproduces the look (the product image is
  a local upload, so it can't ride the link). `history.replaceState` mirrors the
  state in the address bar; clipboard write falls back to a hidden textarea on
  `file://`.
- **Collapsible control groups.** The panel had grown long, so every control
  group is now a `<details>` accordion (`+`/`–` markers, matching the
  generators' `.gen-section` look). Collapsed by default except **Product**,
  **Scene** and **Export**, which stay open so the essentials are always to hand.

## 2026-07-24 — Motion overlays from the shared overlay kit

- **New Overlay layer.** Any of the 69 overlays from the Overlay Asset
  Customizer can now be composited straight onto a mockup — flow indicators,
  callouts, arrows, pings, frames, etc. — so product + procedural scene +
  overlay + title export as a single still or looping WebM. The tools are one
  studio now, not separate exports.
- Powered by a new shared module, **`assets/overlay-engine.js`**: the overlay
  asset library (`window.RENKON_OVERLAYS`, single source of truth, also consumed
  by the customizer) plus `OverlayEngine.preRenderFrames`, which scrubs an
  overlay's loop to cached canvas frames with colours resolved from a supplied
  palette.
- Overlay controls: pick + monochrome **colour**, **size**, **X/Y position**,
  **rotation**, **speed**, **opacity**, **line weight**. Colour / weight bake
  into the cached frames (re-baked on change, with a "building overlay…" note);
  size / position / rotation / speed / opacity apply at draw time so they stay
  live. Frame is chosen by scene time, so the overlay loops in sync with the
  composite and records into the WebM.
- An active overlay now counts as motion: it drives the live preview loop and
  enables WebM export even on a static background, and the top **Randomize**
  rolls the overlay's look (size/position/rotation/speed/opacity/colour) when one
  is selected.

## 2026-07-24 — Procedural animated background; presets stay preset

- **New "Procedural scene (animated)" background.** The full procedural scene —
  every fluid style, theme and motif — now renders as a live, exportable
  animation, not just the four canned presets. Each fluid style has its own
  motion: viscous/laminar ribbons flow and undulate, liquid-metal droplets
  jiggle/drift/shimmer, ripples expand outward and loop, ink blooms breathe and
  drift, splash crowns surge. Plus a slow key-light drift, reactor-core pulse,
  running dock-light twinkle and orbital-ring rotation. All motion is threaded
  through an optional time arg that defaults to 0, so the static scene, the
  quick-scene thumbnails and the preview modal are byte-for-byte unchanged.
- **Presets stay preset.** The four named loops (Orbit/Reactor/Parallax/Sweep)
  no longer receive the fluid-style/theme controls — those now belong to the
  procedural-animated mode. The presets keep their palette recolour + seeded
  variation, but Ink Bloom / Droplets etc. no longer bleed into them. The
  Background dropdown is relabelled: "Procedural (static/animated)" then
  "Preset — …" for the four loops.

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
- **Fluid style + theme now drive the animation too.** The animated backplates
  receive the scene's fluid style and theme: style shapes the motion character
  (viscous = slow, high-amplitude waves; stream = fast, tight; ink = big lazy
  swells; splash = energetic; etc. — mapped to speed, ribbon amplitude/frequency
  and particle count), and theme shapes the environment (space = dense starfield
  + more atmosphere; industry = more structural detail; pure fluid = minimal).
  Both are shuffled by Randomize, so a roll re-composes the motion, not just the
  palette. Neutral defaults keep the Presets tab unchanged.
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
