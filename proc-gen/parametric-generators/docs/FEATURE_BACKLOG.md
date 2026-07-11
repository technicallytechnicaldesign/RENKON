# Feature backlog — Texture & Bump Map Generator

Planning docs for whoever (human or subagent) picks these up next, in
priority order. Each is scoped to be buildable independently — pick one, read
its section, go. None of these block each other or `ADVANCED_TEXTURES.md`.

Read `HANDOFF_BRIEF_v2.md` and `ANIMATED_EXPORT.md` first for the existing
architecture (`computeTextureData`, `TEXTURE_GENERATORS`, the blob-URL export
pattern) — every proposal below reuses it rather than inventing a new one.

---

## 1. Seamless XY tiling (P1 — real functional gap)

**Status: shipped** (scope items 1–3). The Tile Preview toggle (3×3 at 1/3
scale, display-only, works while animating, exports untouched) is live next
to Play/Pause. **Noise and Grid tile exactly** in X/Y, static *and* animated
(Noise: toroidal lattice via `buildValueFieldTiling`/`sampleFieldWrap`, cell
size snapped to divide the tile, both animated blend fields tiling; Grid:
shimmer spatial frequency quantized to whole cycles per tile — the static
grid already tiled). **Still documented non-tiling**: Cellular, Wood Grain,
Waves, Scratches, Splotches, Cracks, Machining Marks, Paint Strokes — the
Worley pair (Cellular/Cracks) is the natural next fix per the note below.
Verified headless (seam wrap-delta vs. interior gradient at 320 + 1024,
static + mid-animation; other 8 patterns hash-identical at fixed seed).

**The gap:** every pattern's *time* animation is seamless-looping (documented
and verified per-pattern), but nothing guarantees **spatial** seamlessness —
whether the texture tiles cleanly when repeated across a surface in X/Y. For
Noise this happens to mostly work by luck at the field's boundary only if
`w`/`cellSize` divides evenly; for Cellular/Cracks/Wood Grain/Waves it
does **not** tile at all (Wood Grain and Waves are anchored to a fixed
point/angle, Cellular's edge cells are unrelated to the opposite edge).
This matters because texture/bump maps are applied as tiling surface
material channels in KeyShot — a map that visibly seams when repeated is a
real defect, not a nice-to-have.

**Scope for this pass:**
1. Add a **"Tile Preview"** toggle next to Play/Pause in the animation row.
   When on, render the *current* preview canvas content tiled 3x3 into a
   larger preview (reuse the canvas the pattern already computed — just
   `drawImage` it 9 times at 1/3 scale each, no need to regenerate at a
   different size). This alone is valuable as a QA tool even before any
   generator is fixed — it makes the current seams visible, which is
   probably the actual next step (see them before deciding which patterns
   are worth the fix effort).
2. Fix **Noise** and **Grid** to tile exactly (both are already
   grid/lattice-based — this is the cheapest win): generate over a domain
   that wraps, i.e. sample coordinates modulo the export size, or build the
   underlying value field with `cols`/`rows` sized to divide the tile exactly
   and sample with wraparound in `sampleField` (`(x0+1) % cols` instead of
   `x0+1`). This is the standard toroidal-domain trick for value noise.
3. Leave Cellular/Cracks/Wood Grain/Waves/Scratches/Splotches as **documented
   non-tiling** for this pass (note it in `CHANGELOG.md`) unless there's
   time — Cellular/Cracks tiling requires wrapping the Worley neighbor search
   toroidally (doable, same trick as #2 but in `sampleWorley`'s 3x3 loop);
   Wood Grain/Waves tiling is harder (they're not lattice-based) and lower
   priority since they're meant to look organic/directional, not tile-critical,
   in most real placements.

**Verification:** headless-driven canvas stats before/after on the *seam
row* specifically — sample the last column of pixels and the first column,
confirm they're continuous (small delta) after the fix, for both a static
frame and mid-animation.

---

## 2. Normal map export (P1 — natural extension, real KeyShot value)

**Status: shipped.** `Export Normal Map PNG` is live in `index.html`, built
per this spec's `heightToNormalMap()` reference almost verbatim (the `at()`
wraparound sampler kept as specced). Reuses `state.bumpStrength`, works
unmodified across all 10 patterns, exports via the same `openPngInNewTab`
blob-URL pattern as the other two static exports. See `CHANGELOG.md` for
verification detail.

**What:** alongside the existing Height/Bump Map PNG export, add an **Export
Normal Map PNG** button. A normal map (tangent-space, RGB) is the standard
material channel a render engine actually wants for surface detail — more
so than the height map in many pipelines — and this tool already computes
exactly the height field a normal map derives from.

**Implementation:** a Sobel-filter height-to-normal conversion, applied to
the same `data` array `computeTextureData` already produces at export size:

```js
function heightToNormalMap(data, w, h, strength) {
  const out = new Uint8ClampedArray(w * h * 4);
  const at = (x, y) => data[((y + h) % h) * w + ((x + w) % w)]; // wraps — see tiling note below
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const l = at(x - 1, y), r = at(x + 1, y), u = at(x, y - 1), d = at(x, y + 1);
      const dx = (l - r) * strength, dy = (u - d) * strength;
      const len = Math.sqrt(dx * dx + dy * dy + 1);
      const idx = (y * w + x) * 4;
      out[idx]     = Math.round((dx / len * 0.5 + 0.5) * 255); // R
      out[idx + 1] = Math.round((dy / len * 0.5 + 0.5) * 255); // G
      out[idx + 2] = Math.round((1 / len * 0.5 + 0.5) * 255);  // B
      out[idx + 3] = 255;
    }
  }
  return out;
}
```

Wire a third export button (`Export Normal Map PNG`) next to the existing
two, following the exact same `openPngInNewTab` pattern already used for
Height/Bump and Preview Render. Reuse `state.bumpStrength` as the Sobel
`strength` input so the normal map's intensity matches what the bump preview
is already showing — no new slider needed.

Note the `at()` helper above wraps toroidally regardless of whether the
underlying pattern actually tiles (item #1) — for non-tiling patterns this
just means the normal map's edge pixels reference the opposite edge's height,
which is harmless (a one-pixel-wide inaccuracy at the border) and avoids
needing edge-clamping special-casing.

**Verification:** headless-driven — confirm output is 4-channel RGBA, B
channel is consistently high (mostly-flat surfaces should read close to
straight-up blue, ~128-255), and R/G channels vary sensibly across a
patterned region (e.g. Grid's straight edges should produce strong, sharply
alternating R or G depending on edge orientation).

---

## 3. Preset library (P2 — nice-to-have, uses existing infra)

**What:** save/recall named parameter presets per pattern (e.g. "Steel —
brushed", "Rubber — pebbled") instead of re-dialing sliders from scratch
each session. The palette section of the Overlay Asset Customizer already
does exactly this shape of thing via `window.storage.set("palette:default",
JSON.stringify(palette), false)` — reuse that same `window.storage` API,
don't invent a second persistence mechanism.

**Scope:**
1. A "Save Preset" button prompts for a name, serializes the full `state`
   object (pattern + all shared/custom params, *not* seed — presets should
   be seed-independent so "Steel — brushed" looks like steel on any seed) to
   `window.storage.set("texturepreset:" + name, JSON.stringify(state), false)`.
2. Maintain an index list (`window.storage.set("texturepreset:index", ...)`
   — array of names) so presets can be enumerated for a dropdown, same
   pattern you'd use for any small key-value store without a "list keys"
   primitive.
3. A preset dropdown next to Randomize; selecting one applies all its fields
   to `state` and calls `regenerate()`.
4. Ship 4-5 built-in presets (not user-saved, just hardcoded defaults
   shipped in the file) covering genuinely different looks across the 8
   base patterns + whatever's landed from `ADVANCED_TEXTURES.md` by the
   time this is built, so the dropdown isn't empty on first use.

**Verification:** save a preset, randomize the seed and change several
sliders, reload the preset, confirm every field (except seed) matches the
saved values and the regenerated canvas is visually the "same" texture
(same pattern + params) just on whatever seed was active.

---

## Not scoped yet (ideas only, don't build without fleshing out first)

- **KeyShot material-template bridge**: pair a texture/bump/normal export
  triple with a small manifest noting suggested KeyShot material-channel
  hookup — natural cross-link to the `keyshot/` pipeline in this repo, but
  needs someone who actually knows the target KeyShot material graph shape
  to spec correctly. Don't guess at this one.
- **Seed-variation gallery**: a "generate N variations" grid (thumbnails,
  different seeds, same pattern/params) for fast visual picking — same
  blob-URL-gallery UI shape as `ANIMATED_EXPORT.md`'s frame sequence, just
  varying seed instead of time. Low effort if you're already touching the
  gallery code from that doc.
