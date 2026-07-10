# Animated export plan — "blob-URL gallery" (BLOB-URL-GALL)

**Status: priority (1) shipped.** The Texture & Bump Map Generator has an
"Export Frame Sequence (PNG)" control (12/24/48 frames) that opens a numbered
blob-URL gallery in a new tab, per the plan below. Priority (2) (WebM) and
(3) (drop GIF from the Overlay Asset Customizer) are still open — see
`CHANGELOG.md`.

Export for the **animated** maps on the Texture & Bump Map Generator. This is
the plan we settled on; it reuses the static export mechanism already shipped
and deliberately sidesteps the whole `gif.js` / Worker / download-block mess.

## Why this approach

The old export pain (broken GIF, silent download failures) was a **claude.ai
artifact-sandbox** problem, not a code problem — sandboxed iframes block
cross-origin Workers and lack `allow-downloads`. On GitHub Pages the tool is a
normal top-level page, so plain downloads already work there. Regardless, the
robust universal path is:

- `canvas.toBlob()` → `URL.createObjectURL(blob)` → open in a new tab.
- **Use `blob:` URLs, never `data:` URLs** — browsers block top-frame
  navigation to `data:` URLs (phishing/XSS mitigation); `blob:` URLs are
  same-origin to their creator and are allowed.

This is already implemented for the two **static** PNG exports via
`openPngInNewTab(canvas, filename)` in `index.html`. The animated version
generalizes it.

## The plan (priority order)

1. **PNG frame sequence — the primary deliverable (BLOB-URL-GALL).**
   - Render N frames across one loop at `TEXTURE_EXPORT_SIZE` (1024px):
     for `k` in `0..N-1`, set `state.time = k / N`, `computeTextureData(...)`,
     paint to an offscreen canvas, `toBlob()` → object URL.
   - Open **one** new tab that is a numbered gallery: each frame an
     `<img src="blob:…">` with a per-frame **Save** link named
     `noise_<seed>_0001.png … _000N.png` (zero-padded, tied to the timeline).
   - Add a **"Download all"**: either sequential saves, or a single zip via
     **JSZip** (CDN, and crucially **Worker-free** unlike gif.js).
   - This is also *literally what a render engine wants* for an animated bump
     channel — a numbered image sequence, not a GIF/video. So it's the primary
     path, not a fallback.
   - UI: an "Export frames" control + a frame-count input (e.g. 12/24/48).

2. **WebM via `MediaRecorder` + `canvas.captureStream()` — optional.**
   Native, no Worker. Good for a single-file *preview* to share, not for
   feeding KeyShot. Nice-to-have after (1).

3. **GIF — drop it.** Only ever failed in the sandbox, needs a Worker, and
   isn't the right deliverable. Remove the `gif.js` CDN dependency and the
   dead GIF path when convenient.

## Reuse notes

- `openPngInNewTab()` (in `index.html`) is the template for the new-tab host
  page (blob URL + Save link + image). The gallery is the same idea with N
  images and a zip button.
- The generators are already time-parametrized and verified seamless
  (`state.time` 0→1, `state.animate` flag). Frame `k/N` for `k` in `0..N-1`
  gives a clean loop (frame `N` == frame `0`, so don't emit it twice).
- Keep it SVG-first elsewhere — texture/bump maps are the legitimate raster
  exception (they're height data a render engine consumes as raster).
