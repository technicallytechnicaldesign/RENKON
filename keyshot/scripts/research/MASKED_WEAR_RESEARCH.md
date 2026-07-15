# Masked / Targeted Wear — Research

**UID:** MWR-9C4E21
**Rev:** 1
**Date:** 2026-07-15
**Audience:** whoever extends `1_HLP_MAT_GENERATOR_AA02.py` next (TJ + agent).
**Status:** research/design spec — nothing built yet. This is the answer to
"can we make wear land only where it physically would — scratches on edges,
grime in crevices, the odd fingerprint on polished metal — instead of
uniformly over the whole surface?" Short answer: **yes, and it's scriptable**,
with one architectural constraint that decides the whole approach.

---

## 0. The one constraint that shapes everything

KeyShot's own tutorials build targeted wear with a **Label** — a second,
glossier sub-material laid on top, with a Curvature texture driving the
label's *opacity* so it only shows on edges. **That technique is not available
to us:** the `lux` scripting API exposes no label API at all — no `addLabel`,
no label input, nothing on `MaterialGraph` (confirmed against the 11.0 lux
reference). Labels are a GUI-only material feature.

**So we don't mask a label — we mask the *effect itself* inside a single
material graph.** The pattern is:

```
   effect layer  ──┐
                   ├── Color Composite (alpha = mask) ──▶ base input
   mask driver  ───┘        (blend a wear texture against "no wear",
                             gated by a spatial mask on the alpha)
```

Every recipe below is a variation on **mask × effect × composite**. All three
building blocks are confirmed-scriptable node types (next section), so this
slots straight into the generator's existing defensive `try_new_node()` +
Color-Composite plumbing, the same way `add_occlusion_roughness` already works.

---

## 1. Confirmed scriptable node types

Pulled from the KeyShot 11.0 lux scripting reference — exact constant → internal
id:

| Node | `lux` constant | internal id | Role here |
|---|---|---|---|
| Curvature | `SHADER_TYPE_CURVATURE` | `lux_curvature` | **edge/corner mask** — convex → white |
| Occlusion | `SHADER_TYPE_OCCLUSION` | `lux_occlusion_tex` | **cavity/crevice mask** — occluded → dark *(already used in the generator)* |
| Color Composite | `SHADER_TYPE_COLOR_COMPOSITE` | `lux_color_blend` | **the compositor** — blend effect vs. no-effect, alpha = mask |
| Color To Number | `SHADER_TYPE_COLOR_TO_NUMBER` | `convert_rgba_to_float` | map a texture's colour → a scalar (roughness/bump amount), with invert |

Graph API confirmed: `MaterialGraph.newNode(type)`, `.newEdge(source, target,
param)`, `.getRoot()`, `.getMaterialGraph(name)`, plus `.removeNode()` /
`.removeEdge()`. Everything the generator already leans on.

**Not scriptable (design around it):** Labels / Multi-Materials, and there is
**no `NUMBER_TO_COLOR`** constant. Treat the image-texture node id and any
bundled-asset paths as *experimental until probed on the real build* — same
confidence discipline as the rest of the project.

---

## 2. Recipe A — scratches only on edges/corners (fully scriptable)

The headline ask. Curvature is the mask; scratches are the effect.

1. `SHADER_TYPE_CURVATURE` node. Set **Positive Curvature = white**, **Negative
   Curvature = black**, **Zero Curvature = black** (or a mid grey for a softer,
   feathered falloff onto the flats). `Cutoff` + `Radius` tune how far the wear
   creeps off the edge — small radius = a tight rim of wear on the very corner,
   larger = wear bleeds onto the faces.
2. The existing `add_scratches_bump()` node stays as-is — it's the effect.
3. **New composite stage:** feed *scratches* and a *flat black* (no-bump) into a
   `SHADER_TYPE_COLOR_COMPOSITE`, and wire **Curvature → the composite's alpha**.
   Result: scratch bump amplitude is ~full on convex edges, ~zero on flats.
4. Feed the composite's output into the bump chain exactly where the raw
   scratches node goes today.

Net effect: handling wear rings the edges, the broad faces stay clean — the
thing that reads as "real" vs. the current uniform scatter.

---

## 3. Recipe B — grime in crevices (fully scriptable, inverse of A)

Occlusion is already wired into the generator for roughness; here it's a mask
instead. `SHADER_TYPE_OCCLUSION` outputs dark where surfaces are close
(parting lines, folds, inside corners). Use it as the Color-Composite alpha for
a darkening/roughening layer → dirt collects *in* the cavities, opposite to
where scratches (edges) land. A + B together read as a coherently aged part.

---

## 4. Recipe C — the occasional fingerprint on polished metal (part-scriptable)

Fingerprints are a **roughness** effect, not colour or bump: a smudge is a
patch that's locally *less* reflective on an otherwise mirror surface. Standard
KeyShot recipe:

1. **Fingerprint image texture** (KeyShot ships one under Library → Textures).
   This is the experimental bit for us — it needs an image-map node (confirm
   the `lux` constant) and a path to the asset. The repo is SVG-first, but a
   fingerprint is a genuine raster case, like the render/texture maps we
   already allow.
2. `SHADER_TYPE_COLOR_TO_NUMBER`, **inverted** (`Output From`/`Output To`
   swapped, `Input To` pulled down) so the print reads darker than its
   background — because roughness treats white = smooth, black = rough, so the
   smudge must be the darker value.
3. Wire that scalar into the base metal's **Roughness** (base roughness ~0 for a
   polish; the print raises it locally).
4. **"Occasional"** = don't tile it everywhere. Gate the fingerprint's
   contribution through a second Color Composite whose alpha is a
   **low-frequency noise thresholded hard** (a few sparse blobs), so prints
   show in a handful of spots instead of wallpapering the part. This keeps it
   scriptable without needing per-decal placement (which would want the
   label/positioning API we don't have).

Realism note: real fingerprints also nudge clear-coat / reflection, not just
roughness — roughness alone gets ~80% of the read and is the pragmatic target.

---

## 5. How this lands in the generator

The generator already combines bump layers and drives roughness. Masking adds a
**per-layer mask stage** rather than new top-level architecture:

- A helper like `masked(graph, effect_node, mask_node, param)` → returns a
  Color-Composite node = effect gated by mask. Every loud bump layer can opt
  into a mask.
- New feature toggles, in the same dialog idiom: `mask_scratches_to_edges`
  (Curvature), `mask_spots_to_cavities` (Occlusion), `add_fingerprints`
  (image + noise gate). Default off → current behaviour is unchanged, masking
  is opt-in.
- The `1/√n` loud-layer damping still applies; masking is orthogonal to it (it
  changes *where*, not *how strong*).

---

## 6. Confirmed vs experimental

| Element | Confidence |
|---|---|
| Curvature / Occlusion / Color Composite / Color-To-Number node ids | **Confirmed** (11.0 lux ref) |
| Curvature-alpha edge masking; Occlusion-alpha cavity masking | **Confident** — standard, all-scriptable |
| Fingerprint via inverted Color-To-Number → roughness | **Confident** on the wiring |
| Image-texture node id + bundled fingerprint asset path | **Experimental** — probe on the real build |
| Noise-threshold "occasional" gating | **Confident** — reuses existing noise node |
| Label-based approach from KeyShot's own tutorials | **Ruled out** — no label API in `lux` |

---

## 7. Open questions (→ DECISIONS.md)

1. **Fingerprint source** — ship/point at a bundled raster fingerprint map
   (breaks SVG-first, but it's a legit raster case), or skip prints for v1 and
   do edge/cavity masking only? Rec: masking (A+B) first, fingerprints as a
   follow-on once the image-node id is confirmed.
2. **Masking: global toggle or per-layer?** Rec: per-layer opt-in toggles, off
   by default, so existing output is untouched.
3. **Curvature falloff defaults** — tight rim vs. feathered. Needs a real render
   to taste; ship a middle default + expose Cutoff/Radius via wear level.

## 8. Build order

1. `masked()` composite helper + confirm Curvature/Color-Composite create &
   wire on the real build (one throwaway material, DEBUG on).
2. Recipe A (edge scratches) behind a toggle — the highest-value, lowest-risk win.
3. Recipe B (cavity grime) — near-free once A's helper exists.
4. Recipe C (fingerprints) — after the image-node id + asset path are confirmed.
