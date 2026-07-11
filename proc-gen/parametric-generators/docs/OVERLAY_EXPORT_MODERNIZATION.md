# Overlay Asset Customizer: retire GIF export, ship frame-sequence export

Status: **shipped.** `exportGIF()` and `gif.js` are gone; the Overlay Asset
Customizer's "Export Frames" button now uses the same Worker-free,
dependency-free `blob:` URL frame-sequence gallery as the Texture & Bump Map
Generator — see `CHANGELOG.md`'s "Export Frames (retires `gif.js`)" entry.
Independent of `ADVANCED_TEXTURES.md` and
`FEATURE_BACKLOG.md` (those are both the Texture & Bump Map Generator half of
this file; this plan is the **Overlay Asset Customizer** half — different
tool, same `index.html`). Safe to pick up in parallel with those, but
whoever implements this should still `git pull --rebase` before committing,
same collision-avoidance reason as everything else touching this file.

## Why

The Overlay Asset Customizer's "Export GIF" button (`exportGIF()`, ~line
2400 as of this writing — search for `async function exportGIF`) depends on
`gif.js` loaded from cdnjs, plus a same-origin-Worker workaround
(`getGifWorkerBlobUrl()` re-hosts the CDN worker script as a `blob:` URL
because browsers refuse to construct a `Worker` from a cross-origin script
URL directly). This is the **last external dependency in the entire repo** —
`CLAUDE.md` already calls it out: *"Minimize dependencies (the only current
one is `gif.js` via CDN, and that's the broken path — see the toolkit
brief)."* `docs/ANIMATED_EXPORT.md` §3 recommended dropping it outright when
that plan was written, in favor of exactly the approach that's since shipped
on the Texture & Bump Map Generator: a Worker-free, dependency-free, `blob:`
URL frame-sequence gallery (see `CHANGELOG.md`'s BLOB-URL-GALL entry, and the
`openFrameGalleryInNewTab()` function in `index.html`, which this plan reuses
directly).

Two things now make this worth doing rather than just noting:
1. **`openFrameGalleryInNewTab()` already exists**, built for the texture
   tool. It's generic — takes `(frames, title)` where `frames` is an array of
   `{ url, filename }` blob URLs. Nothing about it is texture-tool-specific.
   The Overlay Customizer's GIF export already has *all* the frame-capture
   logic it needs (`freezeNode()`, `bakeSmilFreeze()`, `bakeCssFreeze()`,
   `resolvedSvgMarkup()`, `svgToImage()`) — it currently feeds captured
   frames into `gif.js`'s encoder instead of into blob URLs + a gallery. That
   swap is small.
2. **The SMIL freeze bug just got fixed** (see `CHANGELOG.md`'s "Fixed —
   Droplet Stream" entry) — `bakeSmilFreeze()` now correctly derives
   `animateMotion` particle positions via `getCTM()` instead of the always-
   `null` `transform.baseVal`, and GIF frame sampling starts after every
   particle's `begin` delay has elapsed so there's no pop-in. That fix
   benefits this new export path for free, since it reuses the same freeze
   functions — good timing to build this now while that context is fresh.

## Scope

Replace `exportGIF()` with `exportFrameSequence()` (name it whatever reads
best, doesn't need to match this exactly) that:

1. Reuses the *existing* frame-capture loop structure from `exportGIF()`
   almost verbatim — the `if (asset.engine === "css") { ... } else if
   (asset.engine === "smil") { ... }` branches, `freezeNode`,
   `resolvedSvgMarkup`, `svgToImage`, the `frameCount = 20` /
   `speed`/`delay` timing math — but instead of `gif.addFrame(ctx, ...)`,
   do what the texture tool's `exportFrameSequence()` already does per
   frame: `canvas.toBlob()` → `URL.createObjectURL()` → push
   `{ url, filename }` onto a `frames` array. Filename convention to match
   the texture tool's: `<asset.id>_0001.png … _00NN.png`.
2. Call `openFrameGalleryInNewTab(frames, asset.id)` when capture finishes —
   same function, no changes needed there.
3. Rename the button from "Export GIF" to something like "Export Frames" and
   drop its `primary` styling distinction if that was only there to make GIF
   the default recommended path (check current CSS — `gifBtn.className =
   "btn primary"` — decide whether PNG or Frames should be `primary` now
   that GIF is gone; PNG being the plain default and Frames being the
   animated-export path both make sense, use judgement).
4. **Remove**: the `<script src="https://cdnjs.cloudflare.com/.../gif.js">`
   tag, `getGifWorkerBlobUrl()`, `gifWorkerBlobUrlPromise`, and the old
   `exportGIF()` function, once the replacement is verified working. Also
   update the footer note in `mountOverlayKit` (search for `"GIF export
   uses gif.js from cdnjs"` — that whole sentence needs rewriting to
   describe the new export instead) and `CLAUDE.md`'s dependency-count
   mention.
5. Static assets (`asset.engine === "static"`) don't get an animated-export
   button at all today (`if (asset.engine !== "static")` gate) — keep that
   gate, nothing changes there.

## What NOT to change

- Don't touch `freezeNode`/`bakeSmilFreeze`/`bakeCssFreeze`/
  `resolvedSvgMarkup`/`svgToImage` — those are correct and shared with PNG
  export; this plan is purely about the *output* path (gif.js encoder vs.
  blob-URL gallery), not the *capture* path.
- Don't touch the Texture & Bump Map Generator's own `exportFrameSequence`/
  `openFrameGalleryInNewTab` beyond calling the latter — if you need to
  extend `openFrameGalleryInNewTab` (e.g. it currently assumes PNG; that's
  already true here too, no change needed), keep it generic, don't fork a
  second copy for this tool.

## Verification

Same headless-Edge approach used to verify the Droplet Stream fix and the
texture-generator frame-sequence export this session (see
`ADVANCED_TEXTURES.md`'s "Build & verification notes" for the exact command
— it applies unchanged here). Specifically:
- Drive the Overlay Asset Customizer to a non-static, `smil`-engine asset
  (e.g. `flow-droplet-stream`, `flow-pulse-wave`) and a `css`-engine asset
  (e.g. `callout-leader-label`), click the new export button on each,
  confirm `window.open` is called exactly once per click (stub it like the
  earlier verification in this session did) and no errors are thrown.
- Confirm the exported frame count and filenames match the intended
  convention, and that a couple of sampled frames' pixel data actually
  differ from each other (i.e. the animation genuinely advanced between
  frames, not stuck on one frame repeated).
- Update `CHANGELOG.md` when done, same as every other entry there.
