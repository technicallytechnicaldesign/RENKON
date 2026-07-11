# Changelog — Parametric Generators

All notable changes to this tool. Newest first.

This file replaces the old `toolkit_N.html` filename-versioning scheme: the app
file is now a stable `index.html`, and *iteration is tracked here + in git history*
(commit messages for the detail, this file for the human-readable narrative, git
tags for milestones). Don't create `index_8.html` etc. — commit instead.

Versioning: informal `vN` milestones tagged in git as `paramgen-vN`.

## [Unreleased]

### Added — seamless XY tiling: Tile Preview toggle; Noise + Grid tile exactly (backlog #1)
- **Tile Preview toggle** next to Play/Pause in the animation row of the
  Texture & Bump Map Generator: a display-only QA view that repeats the
  already-computed map 3×3 at 1/3 scale in both preview panels (Texture /
  Height Map and Bump Preview), making spatial seams visible on every
  pattern — including the ones that remain non-tiling. It re-tiles each
  fresh frame while the animation is playing, and never touches `state`,
  `computeTextureData`, or any export path: exports always produce the
  single un-tiled map (verified — export data hash identical with the
  toggle on vs. off).
- **Noise now tiles exactly in X and Y**, static and animated. Each octave's
  value-noise lattice is snapped to a whole number of cells per tile and
  sampled with toroidal wraparound (`buildValueFieldTiling` /
  `sampleFieldWrap`); both independently-seeded fields the animated path
  blends go through the same tiling build, so every animated frame tiles
  too. Verified: seam wrap-delta (last column/row vs. first) dropped from
  ~25–45× the interior-gradient level to below it, at preview (320) and
  export (1024) sizes, static and mid-animation.
- **Grid now tiles exactly when animated.** The static grid already tiled
  (spacing divides the tile exactly; per-pixel jitter is structureless);
  what seamed was the animated shimmer's fixed spatial frequency
  (0.06 rad/px doesn't complete whole cycles per tile). That frequency is
  now quantized to the nearest whole number of cycles per tile (~3 at
  320px) — same visual character, exact wrap at any size.
- **Expected small output change** (fixed seed) for Noise (snapped lattice
  cell size + wraparound sampling) and animated Grid (quantized shimmer
  frequency, ~2% at 320px). Static Grid is byte-identical. The other 8
  patterns (Cellular, Wood Grain, Waves, Scratches, Splotches, Cracks,
  Machining Marks, Paint Strokes) are byte-identical before vs. after
  (per-pattern FNV hash at a fixed seed, static + animated) — the tiling
  field builders are a parallel pair, and the non-tiling
  `buildValueField`/`sampleField` warp/flow paths those patterns use are
  untouched.
- **Documented non-tiling for this pass**: Cellular, Wood Grain, Waves,
  Scratches, Splotches, Cracks, Machining Marks, Paint Strokes. Use the
  Tile Preview toggle to judge whether a given seed/placement seams badly
  enough to matter; Cellular/Cracks are the natural next fix (toroidal
  Worley neighbor search — see `docs/FEATURE_BACKLOG.md` item #1).

### Added — Pro Finish patterns + per-pattern custom params (Advanced Textures P1)
- **New pattern group "Pro Finish"** on the Texture & Bump Map Generator, with
  two art-directed patterns modeled on real finishing processes (10 patterns
  total). Both are seeded/deterministic and reuse the whole existing pipeline
  (Contrast, Levels, Invert, bump preview, static + frame-sequence export)
  unmodified:
  - **Machining Marks** — regular tool-mark grooves with a cosine profile
    (rounded in the bump preview, not razor edges). *Linear* mode is a
    mill/planing pass (parallel grooves at a fixed pitch with low-frequency
    toolpath waviness); *Radial* is a lathe/turning pass (concentric grooves
    around the canvas center — deliberately centered, unlike Wood Grain's
    seeded pith, so the map stays placeable). Custom params: Direction
    (Linear/Radial), Pitch, Waviness; the shared Roughness slider controls
    groove-edge sharpness. Animated: the toolpath advances (phase-shift,
    seamless loop, same trick as Wood Grain/Waves).
  - **Paint Strokes** — hand-brushed streaks that follow a low-frequency flow
    field (`buildValueField`), so strokes share a smoothly-varying regional
    direction instead of one printed angle or Scratches' unrelated segments.
    Each stroke deposits soft round brush dabs (Splotches-style accumulation)
    with width tapering at both ends. Custom params: Stroke Length,
    Turbulence; shared Count = number of strokes, Roughness = dab edge
    softness. Animated: strokes *grow* progressively along their length each
    loop — a directional reveal, deliberately accepting a one-frame snap at
    the loop boundary instead of a seamless in-place loop (documented in-file;
    not a bug). Static output renders the fully grown strokes.
- **Per-pattern custom-param mechanism**: a `PATTERN_META[kind].custom` array
  declares extra controls (`type: "range"` slider rows or `type: "select"`
  button groups) beyond the shared slider set. Rows are built once at mount
  into a per-pattern container (shown only while that pattern is selected),
  and values live in `state.custom[kind][key]` so they persist across pattern
  switches and never collide. Because every export path passes `state`
  straight into `computeTextureData`, custom params flow into static and
  frame-sequence exports with zero export-code changes. Custom *length*
  params (Pitch, Stroke Length) are defined in px at preview size and
  normalized by `w / TEXTURE_PREVIEW_SIZE` inside the generators, so the
  320px preview and 1024px export show the same texture. The 8 existing
  patterns declare no custom params and are unaffected — verified
  pixel-identical (per-pattern FNV hash over the rendered canvas) before vs.
  after at a fixed seed.

### Added — four new texture patterns, grouped selector, Levels
- **New patterns**: Cellular, Wood Grain, Waves, Cracks — alongside the
  existing Noise, Grid, Scratches, Splotches (8 total). Cellular and Cracks
  share a new Worley (cellular-noise) helper (`buildWorleyField` /
  `sampleWorley`, jittered-grid nearest-point search) — Cellular fills each
  cell from its distance to the nearest feature point, Cracks thresholds the
  gap between nearest and second-nearest into thin boundary lines. Wood Grain
  is warped concentric rings from a seeded pith point; Waves is a warped
  directional sine band. All four are animated (seamless loop) using the same
  conventions as the original four.
- **Grouped pattern selector**: patterns are organized into Organic (Noise,
  Cellular, Wood Grain), Geometric (Grid, Waves), and Weathering (Scratches,
  Splotches, Cracks), each its own labeled row instead of one flat button
  list. Which of Scale/Octaves/Count show per pattern is now a lookup table
  (`PATTERN_META`) instead of a two-branch ternary.
- **Levels**: Black Point / White Point / Gamma sliders, Photoshop-style —
  remaps to the [black, white] range then applies a gamma curve. Runs after
  Contrast, before Invert, in `computeTextureData`.

### Added — animated frame-sequence export (BLOB-URL-GALL)
- **Export Frame Sequence (PNG)** on the Texture & Bump Map Generator. Renders
  N frames (12/24/48, selectable) across one `state.time` loop at
  `TEXTURE_EXPORT_SIZE`, each painted to a `blob:` URL PNG, and opens one new
  tab hosting a numbered gallery — a `<img>` + per-frame Save link for each
  frame (`<pattern>_<seed>_0001.png … _000N.png`), plus a "Download All" that
  sequentially triggers each frame's own download link. No zip dependency —
  stays consistent with the Worker-free, dependency-minimal export path.
  This is priority (1) from `docs/ANIMATED_EXPORT.md` and the actual
  deliverable a render engine wants for an animated bump channel (a numbered
  image sequence, not a GIF/video).

### Fixed — Droplet Stream (and other multi-particle `animateMotion`) GIF export
- `bakeSmilFreeze()` was reading `liveEl.transform.baseVal` to capture each
  `animateMotion`-driven particle's position when freezing a frame for GIF
  capture. `animateMotion`'s supplemental transform is never reflected in
  `baseVal` (the static, non-animated attribute) — verified empirically it's
  not in `animVal` either — so the freeze silently produced no transform at
  all, leaving the particle at its untransformed local origin. For Droplet
  Stream's three particles (staggered `begin` at 0, dur/3, 2dur/3) this meant
  particles popped in from the top-left corner of the viewBox instead of
  riding the guide path; single always-on particles (e.g. Traveling Pulse)
  were silently frozen at the wrong spot every frame instead.
- Fix: derive the frozen matrix from `getCTM()` (element relative to the SVG
  root) instead of `baseVal` — the only DOM read that actually reflects a live
  `animateMotion` transform.
- Also fixed the GIF frame-sampling window: it previously scrubbed
  `time ∈ [0, dur)`, which for staggered-begin particles includes a stretch
  before their own `begin` has elapsed (SMIL semantics: no motion applied
  yet). Now sampling starts at `max(begin)` across the asset's
  `animateMotion` elements — the system is periodic with period `dur` from
  that point on, so this captures one clean, pop-in-free loop.

### Added — animated texture/bump preview (handoff §6.1 + §6.2)
- **Time-parametrized generators.** Each of the four generators takes an
  `animate` flag + `time` (0–1, one loop) and has its own seamless-looping
  motion: noise *breathes* (cyclic blend to a second field and back), grid
  *shimmers* (phase-shifted sinusoidal coord displacement), scratches *flicker*
  (per-streak fade in/out on staggered phase), splotches *boil* (per-blob
  size/strength pulse). Loops are seamless (`time 0` frame == `time 1` frame)
  and verified to have no boundary seam.
- **Live rAF preview.** Play/Pause button + loop-duration slider (0.5–8s) drive
  a `requestAnimationFrame` loop that cycles `time` and repaints both canvases.
  Self-cleans when you navigate away from the tool.
- **No regression.** With animation off, generator output is byte-identical to
  before — all motion is gated behind the `animate` flag. Pause returns to the
  canonical static frame.

### Changed — PNG export opens in a new tab
- Both texture exports now render to a `blob:` URL and open a small host page in
  a new tab (image + a working "Save PNG" link), instead of triggering a direct
  download. This sidesteps download restrictions (sandboxed iframes, etc.) and
  the `data:`-URL top-frame-navigation block, and works on Pages/local/sandbox.
  Falls back to a direct download if the popup is blocked.

### Still to do (next)
- Optional WebM export via `MediaRecorder` + `canvas.captureStream()` (§6.3
  priority 2) — nice-to-have single-file preview, not needed for the
  KeyShot-facing deliverable which the frame sequence above now covers. See
  [`docs/ANIMATED_EXPORT.md`](docs/ANIMATED_EXPORT.md).
- Remove the dead `gif.js` CDN dependency and GIF-export code path from the
  Overlay Asset Customizer per the plan's §3 recommendation ("GIF — drop it")
  — the Droplet Stream freeze bug is fixed, but the underlying Worker/CSP
  fragility this plan flagged is still the right reason to eventually retire
  it in favor of a frame-sequence gallery there too.

## [v7] — 2026-07-10

Baseline import into the RENKON repo. This is the `toolkit_7.html` snapshot,
brought in as-is and renamed:

- Renamed `toolkit_7.html` → `index.html`; retitled "Overlay Toolkit" →
  "Parametric Generators" (the app houses two tools, not just overlays).
- Two tools present:
  - **Overlay Asset Customizer** — 44 SVG overlays, type→subtype→customize
    drill-down, global palette + per-asset param sliders, custom text, PNG export.
  - **Texture & Bump Map Generator** — procedural grayscale height/bump maps
    (noise, grid, scratches, splotches), simulated-relief preview, PNG export.
    Static output only for now.
- Known issue carried over: **GIF export is broken** (cross-origin Worker /
  CSP problem — see handoff brief §3). PNG export works.

### Pre-import history (manual `toolkit_1..7.html` saves)
Not reconstructed commit-by-commit — the v1→v7 evolution predates version
control. `docs/HANDOFF_BRIEF_v2.md` covers the design-system rationale and
architecture as of this baseline.
