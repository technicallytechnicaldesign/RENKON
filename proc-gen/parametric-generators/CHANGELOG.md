# Changelog — Parametric Generators

All notable changes to this tool. Newest first.

This file replaces the old `toolkit_N.html` filename-versioning scheme: the app
file is now a stable `index.html`, and *iteration is tracked here + in git history*
(commit messages for the detail, this file for the human-readable narrative, git
tags for milestones). Don't create `index_8.html` etc. — commit instead.

Versioning: informal `vN` milestones tagged in git as `paramgen-vN`.

## [Unreleased]

### Fixed — Responsive nav collision + expandable menus (mobile follow-up)
On narrow viewports the `.rk-nav` pill (`assets/menu.js`) — centered and, since
the light/dark pass, three buttons wide (Home/Menu/Theme) — floated directly on
top of the header content on the Texture & Bump Map Generator page, crushing
the breadcrumb text under it. Fixed the collision and used it as the occasion
to declutter the nav generally, per the "use expandable menus/icons to make it
less busy" ask:
- **`assets/menu.js`**: `.rk-nav` moved from centered-floating (`left:50% +
  translateX`) to a fixed top-right corner (`right:16px`, `10px`/`480px`
  breakpoint), so it no longer sits over left-aligned header content at any
  width.
- **`assets/theme.js`**: the theme toggle no longer renders as its own
  persistent third square in the pill. It now folds into menu.js's existing
  expandable `.rk-pop` popover as the first menu item (icon + "Switch to
  light/dark mode" label), so the pill itself stays at two buttons (Home +
  Menu) — literally the same footprint as before light/dark mode shipped.
  Falls back to the old standalone-button behavior if `.rk-pop` isn't present
  for some reason.
- **Header CSS, all four pages**: `header`/`#app-header` now reserve
  `padding-right` for the pill's footprint and allow wrapping
  (`flex-wrap: wrap` on root/keyshot, ellipsis-truncation via `min-width: 0` +
  `text-overflow: ellipsis` on proc-gen's `.crumbs`, since that header is
  `position: sticky` and shouldn't grow tall). Verified headless at 360–430px:
  no rect overlap between `.rk-nav` and any header text on any of the four
  pages.
- **Texture & Bump Map Generator control panel**: the remaining flat sections
  (Preset, Pattern, Shape, Preview & Animation) are now `<details open>` with
  the same chevron affordance Surface & Tone already had, so the whole panel
  is uniformly collapsible — expanded by default (nothing hidden), collapsible
  per-section on a small screen instead of one long scroll. The primary
  "Static maps" export actions stay a plain, always-visible, non-collapsible
  section — that's the main call to action and shouldn't cost a tap to reach.
- Verified headless (Edge, mobile viewport 390–430px + a functional regression
  pass at desktop width): zero nav/header overlap on all four pages; popover
  opens with the theme item first and 6 items total; theme flips dark→light
  through the new popover item; all 5 `details.control-section` elements
  present and open by default on first load; 17 pattern-related buttons, the
  6-option preset dropdown, Randomize, and all 4 export buttons (with their
  tooltips) present and clickable with zero JS console errors after the reorg.

### Changed — Site-wide design review: readability, cohesion, light/dark mode, generator usability
Implements `docs/DESIGN_REVIEW.md` (all four lenses) across all four live pages
(root `index.html`, this tool, `keyshot/index.html`, `keyshot/scripts.html`).
Reorg/labels/tooltips only — no generator or export logic changed.

- **Light/dark mode (new)**: added `assets/theme.js`, a single dependency-free
  script (same philosophy as `assets/menu.js`) loaded synchronously as the
  *first* `<script>` in every page's `<head>` — sets `documentElement`'s
  `data-theme` and injects the light-theme variable overrides before first
  paint (no flash), resolves from `localStorage('renkon-theme')` else
  `prefers-color-scheme`, and injects a sun/moon toggle button into the
  `.rk-nav` pill `menu.js` builds (pill becomes Home + Menu + Theme). Light
  palette keeps all three brand roles recognizable (`--c-structural` blue
  unchanged, `--c-fluid` teal deepened slightly, `--c-accent` orange deepened)
  while passing AA contrast on the light backgrounds. Preview/relief
  viewports (`--stage-bg`) intentionally stay dark in both themes — a
  texture/normal-map preview reads best on a dark stage. Fixed the
  chrome colors that were previously theme-blind: `.mini-stage`,
  `.canvas-panel canvas`, `.large-stage` now use `var(--stage-bg)`;
  `.text-field-wrap input` uses `var(--panel-bg)`; `.btn.primary:hover`'s
  hard-coded `color:#001A33` is now `var(--bg)`. New-tab export pages (PNG
  viewer, frame gallery — separate `document`s with no RENKON chrome) stay
  hard-coded dark by design, not wired to theme.
- **Readability**: smallest label/chip tier 9px → 10px; body/help copy
  (`.tile p`/`.card p`, `.param-hint`, `.status-line`, footers) 11px → 12px;
  tracking on the two 10px uppercase section-labels (`.pattern-group-label`,
  `.section-label`) tightened 0.1em → 0.06em; `--muted` lightened
  `#7a7f83` → `#93999e` (≈6.4:1 on `--panel-bg`, was ≈4.0:1); `footer.note`
  capped at `max-width:74ch`. Same token bumps applied to root and both
  keyshot pages.
- **Cohesion**: this tool now loads `reveal.js` (previously the only one of
  the four pages without it) — content fades in on first paint; hash-router
  navigations do **not** re-trigger it (`reveal.js`'s `run()` is single-shot
  by design, guarding the root landing page's splash handoff — re-arming it
  safely for a second run was out of scope for this pass, so proc-gen
  intentionally only gets the first-paint reveal, never a blank page).
  `.page-head h1` now 17px and focus-outline offset 3px, matching the other
  three pages. Added the RENKON wordmark to `#app-header` (links to
  `../../index.html`), kept sticky. Back-nav now reads "← Back to {label}"
  (was "↑ Up to {label}"), matching keyshot's metaphor. `.card h2` aligned to
  13px/weight 500 to match `.tile h2` on the other pages (layout/class
  untouched — `.card` was deliberately *not* re-plumbed into `.tile`).
- **Generator usability (Texture & Bump Map Generator)**: the flat
  `.texture-controls` wall is now six ordered, labeled sections — **Preset**
  (moved up front, split out of the old combined Seed row), **Pattern**
  (pattern buttons + Seed/Randomize), **Shape** (Scale/Octaves/Count + a
  "Pattern Options" sub-label over the per-pattern custom rows), **Surface &
  Tone** (Roughness/Contrast/Levels/Invert, in a `<details open>`), **Preview
  & Animation** (Bump Strength/Light Angle + Animate/Tile Preview, renamed
  "Tile Preview (QA)"). Preview canvases got one-line captions ("This is the
  exportable data." / "Lighting preview only…"). Export is now a labeled
  section split into **Static maps** (Height/Bump, Preview Render, Normal
  Map) and an **Animated** `<details open>` group (frame count + Export Frame
  Sequence), each button carrying a `title` tooltip; the footer paragraph
  stays as the long-form backup. This is DOM reorder + label/caption/
  `<details>` nodes only — `state`, `computeTextureData`, `syncPatternUI`,
  `regenerate()`, every export handler, and the preset engine are
  byte-identical in behavior. Verified via headless Edge: all 13 patterns
  still produce non-degenerate, NaN-free output after the reorg; all 5
  built-in presets, Randomize, Tile Preview, Play/loop, and all 4 export
  buttons + frame-count select remain present and functional; both
  `<details open>` blocks default open.
- **Generator usability (Overlay Asset Customizer)**: the 6-swatch palette
  panel — which used to render fully expanded on every asset's customize
  screen — is now a `<details>` collapsed by default ("Palette (advanced) —
  recolor all assets"); this is the one intentionally collapsed-by-default
  disclosure in the whole pass, everything else defaults open. Fixed the
  dead **Save Palette** button: it called `window.storage`, an
  environment-injected API that doesn't exist in a plain browser (same root
  cause the texture-preset `localStorage` wrapper below already documents
  and works around) — Save/Load Palette now use `localStorage` directly
  under `palette:default`, and a saved palette is reloaded automatically on
  mount. Added `title` tooltips to Opacity/Thickness/Speed/Roundness.
- **Verified headless** (Edge, `--headless=new --allow-file-access-from-files
  --dump-dom`, driven through the live UI, per `ADVANCED_TEXTURES.md`'s
  verification pattern): theme resolves correctly pre-paint with no flash on
  all 4 pages, toggle flips + persists across reload on all 4 pages,
  `--muted`/`--text` contrast ≈5.9–16.5:1 in both themes on `--panel-bg`
  (`--c-accent` on `--panel-bg` in light mode measures ≈4.3:1 — a hair under
  strict AA for small text; this is the doc-specified, unmodified palette
  value, used mostly for borders/interactive elements rather than body text —
  flagged, not changed, since the palette was pre-approved in the review
  doc); Overlay Customizer palette panel confirmed collapsed by default with
  all 6 swatches reachable, Save Palette confirmed writing to and surviving
  in `localStorage` across reload; no JS console errors across the full
  interaction sweep (39 pattern-button clicks, preset load, theme toggles,
  export clicks).

### Added — Pro Finish P2: Knurling, Orange Peel, Anodize Swirl
- Three more art-directed patterns join the **Pro Finish** group (now
  `machining`, `paint`, `knurl`, `peel`, `anodize`), per
  `docs/ADVANCED_TEXTURES.md`'s "P2 — stretch goals, fleshed out" spec. All
  three ship through the existing generic plumbing with zero changes to
  preset/tiling/export code — `PATTERN_GROUPS`, `PATTERN_META`,
  `TEXTURE_GENERATORS`, and the custom-param mechanism (`state.custom[kind]`)
  already covered them; only additive entries were needed.
- **Knurling**: two directional cosine-groove bands (same profile Machining
  Marks established) crossed at a user-controlled `angle` and `angle + 90°` —
  derived, not hardcoded to ±45, so any crossing (not just a symmetric
  diamond) is reachable. Custom params: `angle` (0–90°, default 30),
  `pitch` (2–40, preview-size-normalized like Machining's), and `mode` — a
  2-option `select` (`cross`/`straight`) standing in for a boolean, since the
  shipped custom-param mechanism has no checkbox type. `cross` multiplies the
  two bands (`bandA * bandB`) for a diamond knurl; `straight` uses `bandA`
  alone. Reuses shared `roughness` for groove-edge depth, same role as
  Machining Marks. Animate: both bands' phase advances together (tool still
  cutting) — seamless loop, static (animate off) matches the `time=0` frame,
  same convention as Machining Marks/Wood Grain/Waves.
- **Orange Peel**: fine Worley dimpling blended with low-frequency noise for
  irregularity — `data[i] = worleyValue*(1-blend) + noiseValue*blend`. Cell
  size is `w/(count*3)`, noticeably finer than Cellular's own `w/count`, so
  it reads as dimpling rather than blobs even at `blend = 0`. Custom param:
  `blend` (0–0.6, default 0.25); reuses shared `count` (cell density) and
  `roughness` (Worley falloff softness, same role as in Cellular). Animate:
  reuses Cellular's wiggle-the-feature-points trick verbatim rather than
  inventing new motion — this is a finish variant of Cellular, not a new
  animation personality, so it also inherits Cellular's existing convention
  where the un-animated static frame (no wiggle) is not pixel-identical to
  the animated frame at `time=0` (wiggle evaluated at each point's own
  phase) — that's Cellular's own established, already-shipped behavior, not
  a regression or a new quirk introduced here.
- **Anodize Swirl**: a radial variant of Paint Strokes — same accumulation
  loop (seed points, step-and-deposit-a-dab, `Math.min(1, existing + dab)`),
  but the base stroke direction is recomputed every step as
  `atan2(y - cy, x - cx) + PI/2` (tangential to the radius from canvas
  center) instead of one fixed straight angle, still perturbed by the same
  turbulence-scaled flow-field bend Paint Strokes uses. Seed points are
  ring-biased (`r = maxRadius * sqrt(rng())`, uniform-area over the disc)
  rather than uniform-random, since radial brushing reads denser away from
  dead-center. Custom params: `strokeLength`/`turbulence`, same names and
  preview-size normalization as Paint Strokes (safe to reuse — the mechanism
  namespaces by pattern kind). Animate: same progressive-reveal trick and the
  same documented one-frame loop-boundary snap as Paint Strokes; static
  (animate off) renders fully-grown strokes, matching Paint Strokes'
  convention.
- **Verified headless** (Edge, driven through the live UI via a scratch
  `window.__TEST__` hook exposing `state`/`regenerate` — not by calling
  internal functions directly, and not present in the shipped file): no
  `NaN` and non-degenerate min/max spread for all 3 new patterns at both
  320px preview and 1024px export size; custom controls render with correct
  labels/types (`select` for Knurling's Mode, `range` for Angle/Pitch/Blend/
  Stroke Length/Turbulence) and are hidden for all other 12 patterns (10
  pre-existing + the other 2 new ones) — confirmed by inspecting every
  pattern's custom-wrap visibility across all 13 kinds; changing each custom
  param changes the output hash; Knurling's `cross` vs `straight` modes
  produce different hashes and changing `angle`/`pitch` changes structure;
  Orange Peel's `blend` changes output and, even at `blend = 0`, differs from
  plain Cellular in both hash and pixel-level structure (finer cell
  frequency from the `w/(count*3)` cell size) — confirming it doesn't
  collapse to a re-parameterized Cellular; Anodize Swirl's direction verified
  genuinely tangential by re-deriving the exact `baseAngle` formula at two
  canvas points 90° apart — dot product with each point's own radius vector
  is 0 (perpendicular to radius, ruling out radial-outward) and the two
  points' direction vectors have a nonzero cross product / zero dot product
  with each other (not parallel, ruling out one fixed straight angle); 4
  distinct `time` values produce 4 distinct frame hashes for all 3 new
  patterns; static-vs-animated-`time=0` matches each pattern's documented
  convention (Knurling: static == t=0, seamless-loop family; Orange Peel:
  static != t=0, inherited from Cellular's own established behavior; Anodize
  Swirl: static == fully-grown != t=0, same accepted snap as Paint Strokes).
  **Regression**: all 10 pre-existing patterns' static output AND 4 sampled
  animated frames each are byte-identical (same FNV-1a-style pixel hash)
  between the pre-edit baseline and the post-edit file, at a fixed seed —
  zero drift from adding the 3 new patterns. Round-trip: set distinctive
  custom values on all 5 Pro Finish kinds, hopped through all 13 patterns,
  confirmed every kind's values survived unchanged (no cross-contamination
  via the shared `state.custom[kind]` namespacing).

### Added — Overlay Asset Customizer: Export Frames (retires `gif.js`)
- **Export Frames** on the Overlay Asset Customizer replaces the old
  **Export GIF** button. `exportFrameSequence()` reuses the existing
  frame-capture loop from the old `exportGIF()` almost verbatim — the
  `asset.engine === "css"` / `"smil"` branches, `bakeCssFreeze`/
  `bakeSmilFreeze`, `resolvedSvgMarkup`, `svgToImage`, the 20-frame /
  speed-adjusted timing math — but instead of feeding frames to `gif.js`'s
  encoder, each frame goes `canvas.toBlob()` → `URL.createObjectURL()` →
  `{ url, filename }`, matching the Texture & Bump Map Generator's own
  frame-sequence export. Filenames follow the same convention:
  `<asset.id>_0001.png … _0020.png`. On completion it calls the existing,
  unmodified `openFrameGalleryInNewTab(frames, asset.id)` — same numbered
  gallery + "Download All" UX the texture tool already ships. Static-engine
  assets are unaffected — they still get no animated-export button at all.
- PNG export now carries the `primary` button styling (previously reserved
  for GIF, the "recommended" export); Export Frames is a plain `btn` — PNG is
  the simple default, Frames is the animated-export path for assets that
  loop or play once.

### Removed — `gif.js` (last external dependency in the repo)
- Deleted the `<script src="https://cdnjs.cloudflare.com/…/gif.js">` tag,
  `getGifWorkerBlobUrl()`/`gifWorkerBlobUrlPromise` (the same-origin Worker
  re-hosting workaround gif.js needed), and the old `exportGIF()` function.
  This was the last external dependency anywhere in the repo — everything is
  now native browser APIs (Canvas, `blob:` URLs, Web Animations API, native
  SVG time control), no CDN, no Worker, no build step. Updated the footer
  note in `mountOverlayKit` and root `CLAUDE.md`'s dependency callout to
  match.

### Added — preset library (backlog #3)
- **Save Preset / preset dropdown** next to Randomize on the Texture & Bump
  Map Generator. Save Preset `prompt()`s for a name (same UX level as the
  Overlay Customizer's palette Save/Load — this file doesn't avoid `prompt()`
  for this kind of thing) and serializes the current look — `pattern`,
  `scale`, `octaves`, `count`, `roughness`, `contrast`, `levelsBlack`,
  `levelsWhite`, `levelsGamma`, `bumpStrength`, `lightAngle`, `invert`, and
  the *full* `state.custom` object (every pattern kind's custom params, not
  just the active one) — to storage. The dropdown lists built-ins first, then
  user-saved presets, and applies every field to `state` on selection.
- **Storage: `localStorage`, not `window.storage`.** The spec pointed at
  `window.storage` (the API the Overlay Customizer's palette Save/Load already
  uses — see `buildPalettePanel`), but that global is never defined anywhere
  in this file; it's only ever referenced behind an `if (window.storage)`
  guard that falls through to "Storage unavailable" otherwise. It's an
  environment-injected API present in whatever sandboxed host supplies it —
  not in a plain browser tab. Since this app is also opened as a plain local
  file and served static on GitHub Pages (see root `CLAUDE.md`), building the
  preset library on `window.storage` would ship a feature that silently does
  nothing in this app's primary deployment targets. Presets use `localStorage`
  directly instead, under the exact key-naming scheme the spec specifies:
  `texturepreset:<name>` per preset, `texturepreset:index` (a JSON array of
  user-saved names — built-ins are never added to this index) for
  enumeration. Verified this actually persists (not just an in-memory
  variable) via a genuine iframe reload, not just re-selecting in the same
  session.
- **Seed is deliberately excluded** from both save and load, per spec — a
  preset is a *look* ("Steel — Brushed"), not a specific instance, and should
  render that look on whatever seed is currently active. Verified: saving at
  one seed, randomizing to a different seed, changing several other fields,
  then reloading the preset restores every field except seed, and seed keeps
  the randomized value rather than reverting.
- **`time`/`animate` are also excluded** (a judgment call beyond the literal
  spec text, which only calls out excluding seed): these are transient
  playback state, not parameters of a look, and naively restoring `animate`
  would desync the Play/Pause button and rAF loop from `state.animate` —
  those two are only ever meant to change together via the existing
  `setAnimate()` function, which a raw state write bypasses.
- **UI resync on load**: applying a preset updates every control that could
  otherwise go stale — shared sliders (position + numeric readout), the
  active pattern button, `scaleRow`/`octaveRow`/`countRow` visibility, every
  pattern's custom-param rows (both `range` and `select` types), and the
  Invert checkbox — reusing the exact same row-visibility/custom-wrap resync
  the pattern-button click handler already did (factored out into
  `syncPatternUI`, called from both places) rather than duplicating it.
- **5 built-in presets**, hardcoded in `index.html` (never touch storage),
  spanning all 4 pattern groups: **Steel — Brushed** (Machining Marks,
  linear, tight pitch) and **Weathered Paint** (Paint Strokes, high
  turbulence) for Pro Finish per the backlog's own example pairing; **Rubber
  — Pebbled** (Splotches, high count/contrast, inverted) for Weathering;
  **Wood — Oak** (Wood Grain) for Organic; **Waves — Ripples** for Geometric.
  Available in the dropdown with no prior save action (marked with a ★ to
  distinguish them from user saves).
- **Name-collision handling**: saving under a name that matches a built-in is
  rejected outright (status line reads "Name reserved by a built-in — pick
  another") rather than silently overwriting the built-in's stored value or
  silently renaming the user's save — keeps the shipped reference presets
  always exactly what's documented above.
- Verified headless (Edge, driven through the live UI via `contentDocument`/
  `contentWindow`, not by calling internal functions directly): fresh load
  with empty storage lists all 5 built-ins spanning Pro Finish + the other 3
  groups; save-then-reload at a fixed seed reproduces a byte-identical canvas
  hash; the full round trip (save → randomize seed → change pattern/scale/
  invert/contrast → reload preset) restores every non-seed field exactly
  (pattern, all 10 shared sliders incl. Invert, and Machining Marks' Direction/
  Pitch/Waviness) while seed keeps the randomized value; UI resync confirmed
  via the actual DOM (active pattern button, Scale/Octaves/Count rows hidden
  for Machining Marks, custom rows populated); a genuine iframe reload (not
  just re-selecting) still lists and correctly loads the saved preset,
  confirming real persistence; smoke-checked all 10 patterns for non-degenerate
  canvas stats (no NaN, sensible min/max spread) and all 3 static exports
  (Height/Bump, Preview Render, Normal Map) still fire `window.open` with no
  thrown errors after these changes.

### Added — normal map export (backlog #2)
- **Export Normal Map PNG** button on the Texture & Bump Map Generator, next
  to Export Height/Bump Map PNG and Export Preview Render PNG. Produces a
  tangent-space RGB normal map — the material channel a render engine
  typically wants over a raw height map — via a Sobel filter (`heightToNormalMap`)
  applied to the same `data` array `computeTextureData` already produces at
  `TEXTURE_EXPORT_SIZE` (1024). Pattern-agnostic: works unmodified across all
  10 patterns (the 8 base patterns plus Machining Marks/Paint Strokes from
  Advanced Textures) since it operates purely on the generic height field, not
  any pattern-specific state.
- **Reuses `state.bumpStrength`** as the Sobel strength input — no new
  slider — so the normal map's apparent intensity matches what the Bump
  Preview panel is already showing for the same setting.
- The Sobel `at(x, y)` sampler wraps toroidally (`(x + w) % w`) independent of
  whether the source pattern actually tiles (see `docs/FEATURE_BACKLOG.md`
  item #1/#2) — a deliberate one-pixel-wide inaccuracy at the border for
  non-tiling patterns, in exchange for not needing edge-clamp special-casing.
  Separate from, and doesn't reuse, the tiling-QA `buildValueFieldTiling`/
  `sampleFieldWrap` helpers added for Noise/Grid generation — those wrap the
  noise lattice at generation time; this wraps the already-rendered pixel
  grid at export time.
- Output is a real 4-channel `Uint8ClampedArray` (`paintNormalMap`, mirroring
  `paintHeightMap`/`paintBumpPreview`'s `ctx.createImageData` +
  `putImageData` pattern) and exports via the same `openPngInNewTab` blob-URL
  pattern as the other two static exports. Filename: `normal_<pattern>_<seed>.png`.
- Verified headless (driver clicks the real button through the live UI,
  stubs `window.open` to capture the blob URL, and reloads that exact blob
  as an `<img>` to read back pixels — not just the underlying function in
  isolation): output is 1024×1024, alpha is 255 across every pixel of the
  actual exported image, filename matches convention. Also verified directly
  on `heightToNormalMap`'s output: no NaN on Grid/Noise/Machining Marks; B
  channel reads 255 (straight-up) on a near-flat region (Noise at
  `bumpStrength` 0.05) and 205–255 across Grid at `bumpStrength` 1 (edges
  pull it down from full flat, as expected); Grid's R and G channels both
  swing the full 41–214 range (edges run both axes on a 2D grid), Machining
  Marks swings R 86–164 / G 67–188 (anisotropic, as expected for directional
  grooves); raising `bumpStrength` 0.1 → 3.0 raises the max R-channel
  deviation from 128 (flat) from 12 to 120, confirming strength drives
  intensity. The two existing static exports and frame-sequence export are
  untouched code (diff is additive-only — no edits inside `paintHeightMap`,
  `paintBumpPreview`, `computeTextureData`, or the two existing export
  handlers) and reproduce identical hashes at a fixed seed/pattern.

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
