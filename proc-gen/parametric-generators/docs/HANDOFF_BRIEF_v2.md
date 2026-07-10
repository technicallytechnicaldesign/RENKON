# HANDOFF BRIEF v2 — Overlay Toolkit + Texture/Bump Generator

## 1. Purpose & context

This supersedes the original `HANDOFF_BRIEF.md` (still worth reading for
the original design-system rationale — palette sourcing, KeyShot
compositing workflow, etc.). That brief covered a static 17-file SVG
library and a plan for an interactive customizer. That customizer has
since been built and grown into a two-tool **Toolkit**:

1. **Overlay Asset Customizer** — live gallery of 44 SVG overlays
   (fluid flow, splashes, callouts, arrows, pings, frame chrome),
   organized as a type → subtype → customize drill-down, with global
   palette control, per-asset opacity/thickness/speed/roundness
   sliders, custom text on labeled assets, and PNG/GIF export.
2. **Texture & Bump Map Generator** — procedural grayscale
   texture/height-map generator (noise, grid, scratches, splotches)
   with a simulated-relief bump preview and PNG export. Early
   infrastructure, static output only for now.

Everything lives in **one file**: `toolkit.html`. No build step, no
dependencies beyond one CDN script (`gif.js`, for GIF export — see
§3 below).

## 2. What's in this handoff

| File | What it is |
|---|---|
| `toolkit.html` | The whole app. Open it directly in a browser. |
| `HANDOFF_BRIEF_v2.md` | This document. |
| `HANDOFF_BRIEF.md` | Original brief (v1), still relevant for design-system background. |

## 3. ⚠️ Known issue: GIF export is not working

**Status: broken, unresolved.** This needs real debugging in an actual
browser with devtools open — something that can't be done from inside
this environment, so what follows is diagnosis-in-writing, not a fix.

**What it does:** exports a looping GIF of any non-static overlay
asset, by scrubbing the live animation frame-by-frame (via the Web
Animations API for CSS assets, via `SVGSVGElement.pauseAnimations()` /
`setCurrentTime()` for SMIL assets), rasterizing each frame to a
canvas, and encoding with `gif.js`.

**What's been tried:**

- **v1**: pointed `gif.js`'s `workerScript` option straight at the
  cdnjs URL. Failed — browsers refuse to construct a `Worker` from a
  cross-origin script URL at all, silently, with no catchable error on
  our side.
- **v2 (current code)**: `fetch()` the worker script text, wrap it in
  a `Blob`, create an object URL from that, and pass *that* blob URL
  as `workerScript` — since a `blob:` URL is same-origin to the page
  that created it, this is the standard workaround for the v1
  problem. Also added a `gif.on("error", …)` handler so failures
  inside `gif.js` itself would surface in the UI instead of hanging
  silently.
- **Reported result**: still not working, even with the v2 fix in
  place.

**Leading hypotheses, roughly in order of likelihood** (untested —
whoever picks this up should open devtools, trigger an export, and
just read the console; it will point straight at which of these it
is):

1. **CSP blocks the `fetch()` itself.** `script-src` (which permits
   the `<script src="…cdnjs…">` tag that loads `gif.js` in the first
   place) and `connect-src` (which governs `fetch`/`XHR` targets) are
   separate CSP directives. The artifact sandbox may allow the former
   without allowing the latter, in which case the
   `fetch("https://cdnjs.cloudflare.com/.../gif.worker.js")` call in
   `getGifWorkerBlobUrl()` fails before a blob URL is ever produced.
   This would throw inside the existing `try/catch` and should already
   surface as "GIF export failed" in the status line — worth
   confirming that's actually what's shown.
2. **The sandbox blocks `new Worker()` outright**, including from
   `blob:` URLs, as a general containment policy for iframe-embedded
   artifacts — independent of where the script came from. If so, no
   amount of URL-hosting cleverness fixes it; `gif.js` is a dead end
   in this environment specifically (it might work fine if the same
   file is opened outside claude.ai, e.g. saved locally and opened in
   a normal browser tab — worth testing as a data point).
3. Less likely: a timing issue where `gif.render()` spins up workers
   asynchronously and a failure inside that path doesn't reach the
   `gif.on("error", …)` handler because it happens before `gif.js`'s
   own event system is attached.

**Recommended path forward — stop trying to make `gif.js` work, route
around it:**

- **Best option: `MediaRecorder` + `canvas.captureStream()`.** Both
  are native browser APIs, need no external library and no Worker at
  all. Feed the same per-frame canvas rendering loop already built
  for GIF capture into a `MediaRecorder` recording a
  `canvas.captureStream()`, and export WebM instead of GIF. This is
  very likely to work where `gif.js` doesn't, since it sidesteps the
  whole cross-origin-Worker problem by not using workers.
- **Zero-dependency fallback: PNG frame sequence.** Capture the same
  N frames already being generated for GIF export, but instead of
  encoding them, offer them as individual PNG downloads (or zip them
  client-side with a small library like JSZip from cdnjs). Not as
  convenient as one file, but it cannot fail the way a worker-based
  encoder can.
- Only worth returning to `gif.js` itself if hypothesis 1 above turns
  out to be the cause and there's a CSP allowance to fix it from the
  Anthropic side — not something fixable purely from the artifact.

## 4. Architecture overview (Overlay Asset Customizer)

- **Shell**: a tiny hash router. `""` → Toolkit home (tool registry
  cards). `#<toolId>/<subpath...>` → that tool's `mount(main,
  subpath)`. Overlay kit's own subpath is
  `[categorySlug]/[assetId]`, giving three real, bookmarkable,
  back-button-friendly levels: type grid → subtype grid → customize.
- **Palette**: six semantic roles (`structural`, `fluid`, `accent`,
  `leader`, `panel`, `label`) held in one JS object, mirrored onto
  `:root` as CSS custom properties (`--c-structural` etc.). Every
  asset's inline `<style>` block reads colors via `var(--c-*)`
  instead of hardcoded hex, so one palette edit repaints all 44 assets
  instantly with no re-render. `Save Palette` / `Load Palette` persist
  via the artifact's `window.storage` API (personal scope).
- **Live params (opacity / thickness / speed / roundness)**: same
  trick, one level down — each *individual asset's* `<svg>` root gets
  its own inline `--t-mult` / `--s-mult` / `--r-mult` custom
  properties plus a plain `opacity` style, and every stroke-width /
  animation-duration / corner-radius in that asset's CSS reads through
  `calc(BASE * var(--t-mult,1))` etc. Dragging a slider is a single
  `style.setProperty()` call — no re-render, no animation restart.
  The one exception: the two-then-three SMIL assets
  (`flow-straight`, `flow-pulse-wave`, `flow-droplet-stream`) have no
  CSS-accessible equivalent for their native `dur="…"` attribute, so
  Speed on those re-renders the markup on slider *release* rather than
  live-dragging.
- **Asset manifest**: `ASSETS` is a flat array of
  `{ id, name, file, category, engine: 'css'|'smil'|'static', loop,
  durationMs, roundable?, hasText?, textDefault?, textHint?,
  svg(rid, speedMult?) }`. Adding a new asset is one object in this
  array — the type grid, subtype grid, palette wiring, params
  sliders, text field, and export buttons all pick it up
  automatically from the manifest, nothing else to touch.
- **Per-asset scoping convention**: every class name and `@keyframes`
  name inside an asset's `<style>` block is prefixed with a short
  per-asset code (`fsv_`, `acf_`, `ctb_`, …). This exists because
  many asset instances can be live in the DOM at once (gallery,
  mini-previews) and plain CSS class/keyframe names are global — two
  assets both naming a class `.shaft` would silently collide, with
  whichever `<style>` block rendered last winning for *all* of them.
- **SMIL freeze convention**: SMIL elements driven by
  `animateMotion` are marked `data-role="motion-target"`; `<pattern>`
  elements driven by `animateTransform` need no marking (there's only
  ever one per asset). `bakeSmilFreeze()` walks *all* matches of both
  generically — it doesn't special-case asset IDs — so it already
  handles `flow-droplet-stream`'s three particles the same way it
  handles `flow-pulse-wave`'s one glow, and will handle any future
  SMIL asset the same way with zero changes.
- **Export pipeline**: `freezeNode()` clones the live `<svg>` and
  bakes its *current* animated state into static attributes (reading
  `getComputedStyle()` for CSS assets, reading
  `getCTM()`/`transform.baseVal.consolidate()` matrices for SMIL
  assets) — necessary because re-parsing the cloned markup as a fresh
  image would otherwise restart every animation from frame zero.
  `resolvedSvgMarkup()` then resolves `var(--c-*)` color references to
  literal hex (so exported files are portable, standalone SVG/PNG,
  not dependent on this page's stylesheet). PNG export works. GIF
  export does not — see §3.

## 5. Texture & Bump Map Generator — current state

Single flat screen (no drill-down yet). State object holds
`pattern, scale, octaves, count, roughness, contrast, bumpStrength,
lightAngle, invert, seed`. Four generators
(`TEXTURE_GENERATORS = { noise, grid, scratches, splotches }`), all
seeded via a small `mulberry32` PRNG for determinism. `Octaves` only
applies to (and is only shown for) Noise; `Count` only applies to (and
is only shown for) Grid/Scratches/Splotches. Two live canvases: the
raw grayscale height data, and a simulated-relief shading of that same
data (finite-difference gradient + a directional light dot product) so
you can judge depth before exporting. Two PNG export buttons at
`TEXTURE_EXPORT_SIZE` (1024px) — the height map (the actual usable
texture) and the shaded preview (explicitly labeled as preview-only,
not a texture).

Everything here is static — one frame, no time dimension. That's the
next piece.

## 6. Plan: animated bump / texture maps

The generation math is already frame-independent and cheap (a 320px
preview regenerates comfortably inside a slider's `input` event), so
animating it is mostly about adding a **time** parameter to each
generator and a **playback/export** layer on top — not a rewrite.

### 6.1 Time-parametrized generators

Add `time` (0–1, one loop cycle) to the params object each generator
receives, and give each pattern its own idea of what "animated" means
— these should feel like different motions, the same way the SVG
assets ended up with different vibes rather than one shared wiggle:

- **Noise** — the most natural fit for something like flowing water
  or shimmering heat. Two options, worth prototyping both: (a) blend
  between two independently-seeded static noise fields with
  `lerp(fieldA, fieldB, smoothstep(time))` for a guaranteed-seamless
  loop, or (b) scroll the sampling coordinates through a larger
  pre-generated field with wraparound ("domain warping") for a more
  convincing flowing/drifting look. (b) reads better but is more
  work; (a) is a good first cut.
- **Grid** — sinusoidally offset each line's position over time
  (`x + amplitude * sin(2π·time + phase)`), phase-staggered per line.
  Reads as a heat-shimmer / vibration effect, which is a genuinely
  useful bump animation for a pump-parts renderer (e.g. implying
  vibration on a housing).
- **Scratches** — give each streak its own random lifespan window
  within the loop (fade in, hold, fade out, staggered start times)
  instead of all streaks being static and permanent. Reads as
  film-grain / static noise.
- **Splotches** — blobs individually pulse size and strength on their
  own phase-offset cycles, or spawn-and-fade entirely rather than
  holding static. Reads as a "boiling surface" / bubbling effect.

### 6.2 Live animated preview (no export dependency at all)

Before touching export, wire a `requestAnimationFrame` loop into
`regenerate()`: `time = (performance.now() / durationMs) % 1`,
re-run both canvas paints every frame. This alone makes the tool
dramatically more useful — you can judge whether an animated pattern
actually looks good before spending any effort on export — and ships
with zero new dependencies or failure modes.

### 6.3 Export paths, in priority order

Given §3, **don't make animated export depend on `gif.js` /
Workers** as the primary path:

1. **PNG frame sequence** (do this first). Render N frames across one
   loop at export resolution, offer them as sequential downloads or a
   client-side zip (JSZip from cdnjs is a reasonable, Worker-free
   dependency). This is also very likely the *actually correct*
   deliverable for KeyShot itself — render engines generally consume
   animated texture maps as a numbered image sequence tied to the
   render timeline, not as a GIF or video file, so this path may end
   up being the primary export rather than a fallback.
2. **WebM via `MediaRecorder` + `canvas.captureStream()`**. Native,
   Worker-free, good for a quick single-file preview/reference to
   share, but not something KeyShot can plug into a bump channel
   directly.
3. **GIF**, only after §3 is actually root-caused. Treat as a nice-to-have
   preview format, not the primary deliverable, given how this
   environment has treated it so far.

### 6.4 Suggested build order

1. Add `time` to the four generators (§6.1) — pure math, no UI yet.
2. Wire the rAF live-preview loop (§6.2) — immediately visible payoff,
   validates the generator changes look right before building export.
3. PNG sequence export (§6.3.1) — no fragile dependencies, and likely
   the real-world useful deliverable regardless of what happens with
   GIF/WebM.
4. WebM export (§6.3.2) as a nice-to-have single-file option.
5. Revisit GIF (§6.3.3 / §3) last, if at all.

## 7. Open questions for the person picking this up

- Confirm the actual devtools error behind §3 before doing anything
  else with GIF — it changes which of the §3 fallback options is
  worth building first.
- For animated maps: how many loop frames does KeyShot's material
  system actually expect/accept for an animated bump channel, and
  what's the expected file-naming convention for a frame sequence?
  That should drive the exact export format in §6.3.1 rather than
  guessing.
- Still open from v1 and still unaddressed: a confirmed accent color
  for anything beyond the current six palette roles, if a seventh
  semantic role is ever wanted (e.g. a dedicated "warning/error" red,
  distinct from the orange accent).
