# -*- coding: utf-8 -*-
# AUTHOR claude-subagent
# REV AB05
# HEADLESS COMPLIANT
# Procedural material *variant* generator, rebuilt as a spec-driven
# sample -> validate -> compile pipeline (design MDD-4B7A9F, Phase 1). A dialog
# (or DEFAULT_OPTIONS in headless) is now a *sampler* that emits a plain-dict
# MaterialSpec; build_material is a *compiler* that reads that spec and wires
# three buses onto the base shader: a colour bus, a roughness bus, and a bump
# bus. Palette now spans MULTIPLE SHADER FAMILIES (opaque metal/plastic/paint +
# anisotropic metal, dielectric glass, thin-film), same feature layers (fine
# noise, scratches, spots, cellular, rounded edges, fractal/occlusion roughness,
# colour gradient), same masking toggles, wear level, seed, and dialog UX as
# AA02. Each build is auto-named MAT-<TYPE>-<WEAR>-<FINISH>-<hex>. Sits in the
# 1_ helper stage as the material-*authoring* member of the MAT family, alongside
# 1_HLP_MAT_PREFLIGHT (coverage QC) and 1_HLP_MAT_LOOKUP (Creo -> KeyShot map).
#
# WHAT'S NEW vs AB04 (AB05 = PART-SIZE-AWARE TEXTURE SCALING. AB04 and earlier
# were NOT part-size aware: no bounding-box query anywhere, and 'Center On'
# (texture_space) was NEVER set -- so KeyShot defaulted to 'Center On: Model' and
# every procedural texture mapped to the whole ~6700-unit MODEL. On a ~40 mm part
# that made feature sizes wildly wrong ("textures loading at 6700, part is 40 mm").
# All texture Scales were hardcoded absolutes in BASE, unrelated to part size. And
# Spots' OWN tiling Scale was never set at all -- add_spots_bump used the list
# ["radius","size","scale"], which matched Radius FIRST (exact-match), so Spots
# Scale stayed at KeyShot's ~6700 default -> giant blobs. AB05 fixes all of this.
# EVERY new API/param access is defensive (getattr/find_param/try-except), logs
# [warn]/[info], and the material ALWAYS builds. CONFIRM-AT-RENDER, see the block
# in the docstring):
#   NEW 1. PART-SIZE RESOLUTION. resolve_part_size(opts, name_filter) returns a
#      characteristic part dimension in mm: (a) the operator-entered `part_size_mm`
#      dialog field if > 0 (most reliable -- they know the part is 40 mm); else
#      (b) measure_part_size(name_filter), which walks the scene geometry (reusing
#      the recursive getChildren() collection) and tries a few UNPROBED lux
#      bounding-box APIs per node (getWorldBounds/getBounds/getBoundingBox), taking
#      the max extent across matched parts; else (c) DEFAULT_PART_SIZE_MM = 50.0
#      with a clear [info]. Captured into spec['scale'] for reproducibility.
#   NEW 2. PART-RELATIVE TEXTURE SCALES. SCALE_FRACTIONS maps each tiling texture's
#      Scale to a FRACTION of part size (scratch 0.12, fine 0.02, fractal 0.15,
#      cellular 0.08, spots 0.06), so a 40 mm part reproduces roughly today's good
#      values (scratch 0.12*40 ~= 4.8 mm, matching the old hardcoded 5) AND it
#      auto-adapts to any part size. Replaces the hardcoded absolutes in BASE
#      (kept only as legacy fallbacks). The placement jitter still multiplies the
#      resolved scale.
#   NEW 3. SCALE SET ON EVERY NODE + CENTER ON: PART. Every tiling texture builder
#      (fine noise, scratches, spots, fractal, cellular) now explicitly sets its
#      Scale to the part-relative value -- including the FIX for the Spots Scale
#      miss (a separate set_display call, not the ["radius","size","scale"] list).
#      set_center_on_part(node) finds ['center on'] / texture_space (a type-2 enum)
#      and sets it to "Part" (string first, then int candidates 1/0, same
#      two-candidate + read-back pattern as set_blend_mode); called on every tiling
#      node right after creation. Non-fatal + logged. CONFIRM-AT-RENDER: the enum
#      value for "Part".
#   NEW 4. SPOTS DISTORTION. add_spots_bump now drives Distortion (~0.4) and
#      Distortion Scale (part-relative) so the spot pattern reads organic, not
#      perfectly round. Defensive.
# Everything else (family schema, buses, masking, placement jitter, spec pipeline,
# and all AB01/AB02/AB03/AB04 fixes) is AB04's logic, extended -- not rewritten.
#
# WHAT'S NEW vs AB03 (AB04 = material FAMILIES -- design AB04_FAMILIES_SPEC,
# DSMI-2F5A-PROCGEN. Four new base-shader FAMILIES added as data, not new
# texture layers. NONE of the new shader constants or family param names are
# probed on the real build -- EVERY one is getattr/find_param-guarded and skips
# with a console [warn]/[info], and the material ALWAYS still builds (opaque
# metal/plastic fallback). CONFIRM-AT-RENDER, see the block in the docstring):
#   NEW 1. SCHEMA `extra`. MATERIALS rows gain an optional 6th element `extra`
#      (a dict; default {} = family "opaque"), carrying `family` + family params
#      (ior/frost, anisotropy/aniso_angle, film_thickness/film_ior). Existing
#      5-element rows are untouched and behave EXACTLY as AB03. `extra` is threaded
#      through sample_spec -> spec['base']['extra'] (a COPY, never the module row)
#      -> validate_spec (numeric family params clamped) -> build_material. A short
#      `meta.family` echo is captured for reproducibility. material_family(extra)
#      returns the family string (default "opaque").
#   NEW 2. FOUR FAMILIES (new MATERIALS rows, getattr-guarded shaders):
#      * metal_aniso  -- "Aluminum (anisotropic brushed)", "Steel (anisotropic)":
#        Metal base + anisotropy + a stable per-build brush angle.
#      * dielectric   -- "Glass (clear)" AND "Glass (frosted)": SHADER_TYPE_DIELECTRIC
#        (fallbacks GLASS -> SOLID_GLASS -> Plastic), ior ~1.51; frosted drives the
#        base roughness (and a refraction-roughness param if present) high.
#      * thinfilm     -- "Thin Film (oil slick)", "Anodised (iridescent)":
#        SHADER_TYPE_THIN_FILM (fallback Metal), film thickness (nm) + film ior.
#   NEW 3. FAMILY-AWARE base setup. apply_family_params(graph, base_node, extra,
#      rng) applies the family shader params defensively AFTER colour+roughness
#      are set. resolve_shader() gained a family-specific fallback chain for the
#      new constants, degrading to Plastic/Metal with a logged note if absent.
#   NEW 4. PER-FAMILY WEAR-LAYER GATING. FAMILY_ALLOWED_LAYERS maps family -> the
#      set of FEATURE_KEYS that make sense on it; build_material intersects the
#      user's chosen features with that set BEFORE building the buses, logging
#      each dropped layer ("<label> skipped -- not applicable to <family>"). This
#      stops nonsense like grime/pitting/cellular-corrosion on clear glass.
# Everything else (spec pipeline, buses, masking, placement jitter, apply, and
# all three AB03 confirmed bugfixes) is AB03's logic, extended -- not rewritten.
#
# WHAT'S NEW vs AB02 (three CONFIRMED BUGFIXES against a real AB02 DEBUG run --
# the ground-truth KeyShot node param names captured there drive all three):
#   FIX 1. ROUGHNESS BUS composite was never built (always 'single-fallback').
#      ROOT CAUSE: _composite_inputs() looked for the Color Composite's two
#      colour inputs with ptype=PT_COLOR, but PT_COLOR resolves to KeyShot type
#      13 (a colour VALUE), while the Composite's Source/Background are type 14
#      (colour/texture CONNECTION inputs). The filter matched nothing -> the
#      chain stopped -> the roughness bus degraded to a single driver every time.
#      FIX: identify Source ('Source') and Background ('Background') by NAME with
#      NO type filter; positional fallback derives the connection type from those
#      params defensively (never hardcodes 14). Now composites N sources ->
#      'composite'. set_blend_mode still tries string-then-int; blend_mode is a
#      type-2 int enum, so the int candidate (7=Lighten) is the one that takes.
#   FIX 2. ANTI-REPETITION placement never applied. ROOT CAUSE: randomize_
#      placement() guessed offset/rotation/translate param names that DO NOT
#      EXIST on these nodes -- every set missed, so nothing varied. Placement is
#      a type-12 'Texture Transform' matrix (transform_obj_to_uv), left UNSET on
#      purpose (writing a raw matrix blind is too risky without a probe). FIX:
#      jitter the REAL, per-node scalar params confirmed in the AB02 dump,
#      node-type-aware, driven by the seeded placement RNG -- scale on all tiling
#      nodes, plus noise_scale/level_scale (Scratches), magnitude (Fine Noise),
#      seed/distortion/radius (Spots), noise_scale/shape_1..3 (Cellular), and
#      bias_x/y/z (Occlusion). placement_seed still captured in spec['meta'].
#   FIX 3. AUTO-APPLY hit 0 parts ('Applied to 0 node(s), skipped 22'). ROOT
#      CAUSE: root.find('') returned only non-geometry nodes (all 22 were
#      cameras, kind=6) -- the geometry was never reached. FIX: traverse the
#      scene tree RECURSIVELY via getChildren() (defensive; falls back to
#      root.find('')), and print a histogram of candidate node KINDS before
#      applying so a future 0-apply is diagnosable. LEAST CERTAIN of the three
#      (no scene to test on) -- marked CONFIRM-AT-RENDER in code + report.
# Everything else (spec pipeline, buses, masking, Finish axis, apply philosophy)
# is AB02's logic, surgically corrected -- not rewritten.
#
# WHAT'S NEW vs AB01 (three targeted changes -- see MDD-4B7A9F / RNK-0054):
#   1. PARAMETER-ROUTING FIX (root-cause). find_param() now prefers an EXACT
#      (case-insensitive) display-name match across ALL params before falling
#      back to the old substring scan. This kills the "noise" vs "Directional
#      Noise" substring collision (AB01 set Directional Noise, then "noise"
#      re-matched it and clobbered it to 0.3 while the real Noise stayed 0). The
#      fix is order-independent and strictly hardens every existing setter
#      (Bump Height, Size, Density, Scale, ...). ptype filtering is unchanged.
#   2. FINISH PRESET AXIS (character), ORTHOGONAL to Wear (amount). Wear governs
#      how MUCH degradation (bump amplitude, density, size, loud-layer count);
#      Finish governs the CHARACTER of the scratch/brush surface (directional
#      noise, chaotic noise, subdivision levels, scratch groove-depth baseline).
#      Pristine/Brushed/Worn/Heavy. A brushed finish is brushed at any wear.
#      Also: an explicit Scratches "Scale" control (tiling scale, KeyShot default
#      ~5mm, never set before) so Density (count) is clearly separate from Scale.
#   3. ANTI-REPETITION: seeded per-material texture PLACEMENT. KeyShot procedural
#      textures are deterministic + world-aligned, so every build tiled
#      IDENTICALLY (reads as fake/too-perfect even with noise). A dedicated,
#      captured placement seed drives a small random offset / rotation / scale-
#      jitter on each procedural texture node (Scratches, Fine Noise, Spots,
#      Fractal Noise, Cellular). Runs for EVERY build; reproducible via
#      spec["meta"]["placement_seed"].
# Everything else (helpers, layer builders, masking, roughness compositing,
# apply) is AB01's logic, re-orchestrated -- not rewritten.
#
# WHAT WAS NEW in AB01 (kept): JSON-serialisable MaterialSpec (sample -> validate
# -> compile), and MULTI-SOURCE ROUGHNESS BLENDING (scratches + fractal +
# occlusion composited into the single roughness input via Color Composite /
# Lighten, degrading to AA02's single-driver behaviour if the chain can't build).
#
# !! KEYSHOT PYTHON CONSTRAINT -- READ BEFORE EDITING !!
# KeyShot's embedded interpreter here predates f-strings (Python < 3.6) and its
# console is ASCII-sensitive. Keep this file f-string-FREE (use "{0}".format())
# and ASCII-ONLY (use -- not an em-dash). An f-string or a stray Unicode char
# makes the whole script fail to load in the Scripting Console. Every sibling
# script that loads cleanly obeys this; the ones that don't (this file's old
# revision, the 2b_ANI_* set) are exactly the ones that wouldn't load.
#
# Confirmed layers (per KeyShot's scripting docs): Fine Noise, Scratches,
# Rounded Edges, Spots, Fractal Noise, Occlusion. Experimental (getattr-
# guarded -- skip with a console [warn] if the lux constant is absent on this
# build): Cellular, Colour Gradient. Masking (targeted wear) maps a Curvature
# (edges) / Occlusion (cavities) mask onto a bump layer's bump-height, so wear
# lands only where the mask is white; param names confirmed against the real
# material-graph dump. Degrades to unmasked (never dropped) if bump-height isn't
# mappable. See MWR-9C4E21 (scripts/research/MASKED_WEAR_RESEARCH.md) and
# MDD-4B7A9F (scripts/research/MATERIAL_DIVERSITY_DESIGN.md).

"""
KeyShot Procedural Material Generator -- REV AB05 (spec-driven, multi-family,
part-size aware)
============================================================================

Pivoted (AA02) from a fixed recipe into a variant generator, then (AB01)
re-architected into a sample -> validate -> compile pipeline around a first-class
MaterialSpec, then (AB02) hardened the param routing and added a Finish axis +
seeded anti-repetition placement, then (AB03) fixed three CONFIRMED bugs against
a real AB02 DEBUG run (roughness composite input types, placement param names,
and geometry-reaching auto-apply), then (AB04) extended the palette into four
new SHADER FAMILIES -- anisotropic metal, dielectric glass (clear + frosted),
and thin-film -- via an optional per-row `extra` dict, a family-aware base-param
pass, and per-family wear-layer gating (see the WHAT'S NEW vs AB03 block up top):

    options (dialog or DEFAULT_OPTIONS)
        -> sample_spec()     build the MaterialSpec dict (captures finish +
                             placement_seed)
        -> validate_spec()   clamp / sanity-check / derive damping
        -> build_material()  compile the spec: base node + 3 buses + placement
        -> emit_spec()       echo the spec to console (reproducibility)
        -> apply_material_to_parts()

The three buses (design MDD-4B7A9F sec 3.3/4):
  * bump bus       -- N bump-domain layers chained via Bump Add (as AA02).
  * roughness bus  -- N roughness sources composited into ONE roughness input
                       via Color Composite / Lighten. Falls back to AA02's
                       single-driver behaviour if compositing fails.
  * colour bus     -- base colour + optional Colour Gradient driver (as AA02).

Two orthogonal preset axes:
  * Wear   -- how MUCH degradation (amplitude / coverage).
  * Finish -- the CHARACTER of the scratch/brush surface (dir-noise, noise,
              subdivision levels, scratch groove-depth baseline).

Run inside the KeyShot Scripting Console, or via `keyshot -script` headless
(dialog auto-skips headless -> DEFAULT_OPTIONS is used instead).

--------------------------------------------------------------------------
CONFIRMED vs EXPERIMENTAL LAYERS
--------------------------------------------------------------------------
Confirmed against KeyShot's own scripting docs (safe bets):
  Fine Noise, Scratches, Rounded Edges, Spots, Fractal Noise, Occlusion,
  Color Composite (roughness bus mixer)

Experimental (constant name is a reasonable guess, not confirmed to exist
in every KeyShot version) -- these use getattr() and skip cleanly with a
console warning if unavailable, rather than crashing:
  Cellular, Color Gradient

CONFIRM AT RENDER (AB03 -- absence/mismatch is non-fatal, watch the console):
  * FIX 1 landed: expect "Roughness bus: N source(s) -> mode 'composite'" (NOT
    'single-fallback') whenever >= 2 roughness sources are active.
  * FIX 2 landed: placement now jitters CONFIRMED per-node params (scale,
    noise_scale, level_scale, magnitude, seed, distortion, radius, shape_1..3,
    bias_x/y/z). The AB02 "placement: offset/rotation not settable" spam should
    be GONE; any remaining [info] miss names a param whose display name differs
    on this build. The type-12 Texture Transform matrix is intentionally UNSET.
  * FIX 3 (LEAST CERTAIN -- no scene to test): auto-apply now walks getChildren()
    recursively and prints a "candidate kinds: {...}" histogram before applying.
    Confirm geometry kinds appear (not only kind=6 cameras) and material count>0.

CONFIRM AT RENDER (AB04 families -- EVERY shader constant + param name below is
UNPROBED on the real build; all degrade non-fatally to an opaque metal/plastic,
watch the console for [warn]/[info]):
  * SHADER CONSTANTS: SHADER_TYPE_DIELECTRIC (fallbacks GLASS -> SOLID_GLASS ->
    Plastic) for glass; SHADER_TYPE_THIN_FILM (fallback Metal) for thin film. If
    a family fell back, resolve_shader prints "[warn] <constant> unavailable on
    this build -- using <fallback> instead".
  * PARAM DISPLAY NAMES (find_param prefers exact display-name matches -- watch
    for "[warn] no parameter matching '<name>'"): dielectric IOR
    ["index of refraction","ior","refraction index"]; frosted refraction
    roughness ["refraction roughness"]; thin-film thickness
    ["thickness","film thickness"] + IOR ["index of refraction","ior"];
    anisotropy ["anisotropy","aniso"] + brush angle
    ["anisotropy angle","aniso angle","angle"].
  * LOOK CHECKS: clear vs frosted glass visibly differ (clear = smooth/see-
    through, frosted = matte/translucent, driven by the base roughness 0.02 vs
    0.30 plus any refraction-roughness param); glass shows NO grime/pitting
    (gated out); thin film reads iridescent (oil-slick / anodised rainbow).
  * The brush angle is a STABLE per-build value from the placement RNG (the
    Scratches direction_field is a type-2 enum, not degrees, so it is NOT read).

CONFIRM AT RENDER (AB05 -- part-size-aware scaling; all degrade non-fatally):
  * CENTER ON: expect every tiling texture to now read "Center On: Part" in the
    panel, NOT "Model". set_center_on_part tries the string "Part" then int
    candidates (1, then 0). Watch the console for "[info] couldn't confirm
    'Center On' = Part" (the enum value differs on this build) or "[info] no
    'Center On' parameter" (the display name differs). NOTE which int took.
  * TEXTURE SCALE: feature sizes should be part-appropriate (roughly 1-5 mm on a
    40 mm part), NOT the old ~6700 model-scale default. Especially SPOTS -- its
    Scale is now set explicitly (was giant blobs before). If a Scale still reads
    ~6700, the "Scale" display name differs on that node (watch for "[warn] no
    parameter matching 'scale'").
  * PART SIZE SOURCE: the console prints one of "part size {n} mm (entered)",
    "(measured)", or "part size unknown -- using default 50.0 mm". If measured,
    it also prints which bounding-box method worked ("via getWorldBounds()" etc.)
    -- the bbox API is UNPROBED, so if measurement silently falls to default, note
    it and enter a Part size in the dialog instead.
  * SPOTS DISTORTION: the spot pattern should read organic / irregular, not
    perfectly round (Distortion ~0.4, Distortion Scale part-relative). Watch for
    "[warn] no parameter matching 'distortion'" / "'distortion scale'".

Masking / targeted wear (opt-in, off by default):
  Scratches-to-edges (Curvature mask) and Spots-to-cavities (Occlusion mask).
  The mask texture is mapped onto the bump layer's bump-height, so bump strength
  follows the mask -- full on edges/cavities, none on the flats. If bump-height
  isn't mappable the layer is left unmasked (present, never dropped).

If a toggle you enabled doesn't show up in the final material, check the
console for a "[warn] ... not available in this KeyShot version" line, or the
end-of-build wire-audit manifest -- that tells you definitively which wires
landed rather than leaving you guessing.
"""

import lux
import random
import math
import json

# lux's PARAMETER_TYPE_* names vary between KeyShot builds, and a bare
# lux.PARAMETER_TYPE_X reference to a name this build lacks raises AttributeError
# -- which crashes the whole run (there is no PARAMETER_TYPE_SHADERCOLOR, for
# one). Resolve the few we use once, defensively: a missing type becomes None,
# and the helpers below treat None as "no type filter" / "skip this wiring"
# rather than crashing. Colour/texture inputs are PARAMETER_TYPE_COLOR (you
# connect a texture into a colour input); there is no separate shader-colour type.
PT_COLOR = getattr(lux, "PARAMETER_TYPE_COLOR", None)
PT_SHADERBUMP = getattr(lux, "PARAMETER_TYPE_SHADERBUMP", None)

# --------------------------------------------------------------------------
# Debug / diagnostics
# --------------------------------------------------------------------------

DEBUG = True  # prints real parameters for each node as it's created

GENERATOR_REV = "AB05"

# --------------------------------------------------------------------------
# Part-size-aware texture scaling (AB05)
# --------------------------------------------------------------------------
# Fallback when the operator neither entered a part size nor a bounding-box API
# could measure one. 50 mm is a reasonable "small hardware part" default; the
# console prints a clear [info] telling the operator to enter a Part size for
# correct scaling when this is used.
DEFAULT_PART_SIZE_MM = 50.0

# Each tiling texture's "Scale" (a size in scene units / mm) as a FRACTION of the
# resolved part size, so scales auto-adapt to any part instead of being hardcoded
# absolutes. TUNED so a 40 mm part reproduces roughly today's known-good values;
# the human will refine these at render. On a 40 mm part:
#   scratch 0.12 -> 4.8 mm  (matches the old hardcoded scratch_scale 5.0)
#   fine    0.02 -> 0.8 mm  (micro-grain; old absolute was 0.15)
#   fractal 0.15 -> 6.0 mm  (broad roughness band; old absolute was 4.0)
#   cellular 0.08 -> 3.2 mm (old absolute was 2.0)
#   spots   0.06 -> 2.4 mm  (old absolute spots_size 0.05 was the RADIUS, not the
#                            tiling Scale, which was never set at all -> giant blobs)
SCALE_FRACTIONS = {
    "scratch_scale": 0.12,
    "fine_noise":    0.02,
    "fractal":       0.15,
    "cellular":      0.08,
    "spots_scale":   0.06,
}

# --------------------------------------------------------------------------
# Material type presets
# --------------------------------------------------------------------------

# Base materials -- THE PALETTE. Add a new one by adding a single row here:
#   (display name, shader, colour RGB 0-1, roughness, 3-letter code[, extra])
# The shader is a lux.SHADER_TYPE_* attribute *name*, resolved defensively at
# build time (resolve_shader) so an unknown one (e.g. SHADER_TYPE_PAINT on a
# build that lacks it) falls back to Plastic rather than crashing. Metals just
# take a colour tint -- brass/copper/anodised are tinted metals; paints are a
# Paint shader (Plastic fallback). Nothing else needs editing to add a colour.
#
# AB04: rows may carry an OPTIONAL 6th element `extra` -- a dict describing a
# non-opaque shader FAMILY and its params. A missing 6th element == {} == family
# "opaque" (fully backward-compatible: every AB03 5-element row behaves exactly as
# before). See material_extra()/material_family(), apply_family_params(), and
# FAMILY_ALLOWED_LAYERS. All family shader constants + param names are UNPROBED on
# the real build -- getattr/find_param guarded, skip-with-warn, always builds.
MATERIALS = [
    # name,                      shader,                colour RGB,         rough, abbr[, extra]
    ("Aluminum (brushed metal)", "SHADER_TYPE_METAL",   (0.72, 0.73, 0.75), 0.18,  "ALU"),
    ("Steel (metal)",            "SHADER_TYPE_METAL",   (0.55, 0.56, 0.58), 0.25,  "STL"),
    ("Chrome (metal)",           "SHADER_TYPE_METAL",   (0.90, 0.90, 0.92), 0.05,  "CHR"),
    ("Brass (metal)",            "SHADER_TYPE_METAL",   (0.85, 0.70, 0.38), 0.22,  "BRS"),
    ("Copper (metal)",           "SHADER_TYPE_METAL",   (0.95, 0.64, 0.54), 0.20,  "COP"),
    ("Anodised Black (metal)",   "SHADER_TYPE_METAL",   (0.05, 0.05, 0.06), 0.35,  "ANB"),
    ("Anodised Blue (metal)",    "SHADER_TYPE_METAL",   (0.06, 0.15, 0.38), 0.30,  "ANU"),
    ("Anodised Orange (metal)",  "SHADER_TYPE_METAL",   (0.75, 0.30, 0.06), 0.30,  "ANO"),
    ("ABS Plastic",              "SHADER_TYPE_PLASTIC", (0.15, 0.15, 0.16), 0.35,  "ABS"),
    ("Paint - Safety Orange",    "SHADER_TYPE_PAINT",   (0.88, 0.34, 0.05), 0.30,  "POR"),
    ("Paint - Signal Blue",      "SHADER_TYPE_PAINT",   (0.03, 0.15, 0.40), 0.30,  "PBL"),
    ("Paint - White",            "SHADER_TYPE_PAINT",   (0.90, 0.90, 0.88), 0.32,  "PWH"),
    # --- AB04 families (new base shaders; extra carries family + params) --------
    # Anisotropic metal -- Metal base + directional (brushed) highlight. anisotropy
    # in [0,1]; aniso_angle None -> a STABLE per-build angle from the placement RNG
    # (the Scratches direction_field is a type-2 enum, not degrees, so it is NOT
    # read -- see apply_family_params). All layers allowed (it's still a metal).
    ("Aluminum (anisotropic brushed)", "SHADER_TYPE_METAL", (0.72, 0.73, 0.75), 0.18, "ANI",
        {"family": "metal_aniso", "anisotropy": 0.5, "aniso_angle": None}),
    ("Steel (anisotropic)",            "SHADER_TYPE_METAL", (0.55, 0.56, 0.58), 0.22, "ANS",
        {"family": "metal_aniso", "anisotropy": 0.6, "aniso_angle": None}),
    # Dielectric glass -- ships BOTH clear and frosted (user decision). Clear =
    # smooth/see-through (roughness ~0.02); frosted = matte/translucent (roughness
    # ~0.30 + a refraction-roughness param if present). ior ~1.51 (soda-lime glass).
    ("Glass (clear)",                  "SHADER_TYPE_DIELECTRIC", (0.95, 0.97, 0.98), 0.02, "GLC",
        {"family": "dielectric", "ior": 1.51, "transparent": True, "frost": 0.0}),
    ("Glass (frosted)",                "SHADER_TYPE_DIELECTRIC", (0.95, 0.97, 0.98), 0.30, "GLF",
        {"family": "dielectric", "ior": 1.51, "transparent": True, "frost": 0.30}),
    # Thin film -- iridescent coating (oil-slick / anodised rainbow), its own BRDF.
    # film_thickness in nm drives the interference colour; film_ior ~1.4.
    ("Thin Film (oil slick)",          "SHADER_TYPE_THIN_FILM", (0.30, 0.30, 0.32), 0.10, "TFM",
        {"family": "thinfilm", "film_thickness": 420, "film_ior": 1.4}),
    ("Anodised (iridescent)",          "SHADER_TYPE_THIN_FILM", (0.20, 0.22, 0.28), 0.15, "IRI",
        {"family": "thinfilm", "film_thickness": 650, "film_ior": 1.4}),
]
MATERIAL_TYPE_ORDER = [m[0] for m in MATERIALS]
MATERIAL_BY_NAME = {m[0]: m for m in MATERIALS}
TYPE_ABBR = {m[0]: m[4] for m in MATERIALS}


def material_extra(mat):
    """Return a MATERIALS row's optional 6th element (the `extra` family dict), or
    {} when the row is a plain 5-element AB03-style row. Defensive: a non-dict 6th
    element is treated as absent."""
    if len(mat) >= 6 and isinstance(mat[5], dict):
        return mat[5]
    return {}


def material_family(extra):
    """Return the shader-family string carried by an `extra` dict, defaulting to
    'opaque' (the AB03 behaviour) when absent or malformed. Known families:
    'opaque', 'metal_aniso', 'dielectric', 'thinfilm'."""
    if not isinstance(extra, dict):
        return "opaque"
    return extra.get("family", "opaque") or "opaque"

WEAR_PRESETS = {"Pristine": 0.3, "Light Wear": 1.0, "Moderate Wear": 2.5, "Heavy Wear": 5.0}
WEAR_ORDER = list(WEAR_PRESETS.keys())
WEAR_ABBR = {"Pristine": "PRI", "Light Wear": "LGT", "Moderate Wear": "MOD", "Heavy Wear": "HVY"}

# Finish presets -- the CHARACTER of the scratch/brush surface (change 2),
# ORTHOGONAL to Wear. Wear scales amplitude/coverage; Finish sets directional
# noise, chaotic noise, subdivision levels, and the scratch groove-depth
# BASELINE. A brushed finish is brushed at any wear amount, so these values are
# sourced DIRECTLY (not wear-scaled) in add_scratches_bump. The scratch bump
# BASELINE is negative (a groove cut into the surface); build_material still
# multiplies it by the wear/damping amplitude and re-clamps.
#   tuple = (directional_noise, noise, levels, scratch_bump_height baseline)
FINISH_PRESETS = {
    "Pristine": (0.1, 0.0, 1, -0.008),
    "Brushed":  (0.5, 0.1, 2, -0.012),
    "Worn":     (0.8, 0.3, 3, -0.018),
    "Heavy":    (1.0, 0.6, 4, -0.025),
}
FINISH_ORDER = ["Pristine", "Brushed", "Worn", "Heavy"]
# 3-letter codes kept distinct from WEAR_ABBR (Heavy -> HEV, not HVY) so a name
# like MAT-ALU-HVY-HEV-... never reads ambiguously.
FINISH_ABBR = {"Pristine": "PRS", "Brushed": "BRU", "Worn": "WRN", "Heavy": "HEV"}

# Subtle base amplitudes at Light Wear (1.0x) -- learned last round that
# these read as much stronger visually than the raw [0,1] numbers suggest.
# AB05: the tiling *_scale absolutes below (fine_noise_scale, fractal_scale,
# scratch_scale, cellular_scale, spots_size) are NO LONGER the source of truth for
# a texture's tiling Scale -- SCALE_FRACTIONS * resolved part size is (see
# build_material). They are kept only as LEGACY FALLBACKS for the placement-jitter
# read-and-multiply path when a live value can't be read. The bump/density/size
# amplitudes are unchanged.
BASE = {
    "fine_noise_scale":    0.15,
    "fine_noise_bump":     0.01,
    "fractal_scale":       4.0,
    "scratch_bump_height": 0.02,
    "scratch_density":     0.12,
    "scratch_size":        0.04,
    # Scratches "Scale" -- the tiling scale of the scratch field (KeyShot default
    # ~5mm). AB01 and earlier never set this, so Density (count) and Scale were
    # conflated. Set explicitly now (change 2) so they are clearly separate axes.
    "scratch_scale":       5.0,
    "scratch_dir_noise":   0.6,   # fallback only -- Finish now supplies dir_noise
    "scratch_noise":       0.3,   # fallback only -- Finish now supplies noise
    "scratch_levels":      2,     # fallback only -- Finish now supplies levels
    "edge_amount":         0.02,
    "spots_bump_height":   0.02,
    "spots_density":       0.08,
    "spots_size":          0.05,
    "cellular_bump_height": 0.015,
    "cellular_scale":      2.0,
}

# "Loud" bump layers actually distort the surface and stack additively when
# combined -- verified against the confirmed research: KeyShot's own manual
# describes Cellular as capable of "cracked surfaces, hammered metal", i.e.
# a strong effect even alone. Rather than let any combination of these pile
# up unbounded, LOUD_BUMP_FEATURES are capped (see randomize_feature_flags
# and the damping factor in build_material) so total surface energy stays
# roughly constant regardless of how many of them are active at once.
# Fine noise is excluded from the cap -- it's deliberately subtle by design.
LOUD_BUMP_FEATURES = ["add_scratches", "add_rounded_edges", "add_spots", "add_cellular"]
MAX_SIMULTANEOUS_LOUD_LAYERS = 2

# Feature keys, dialog labels, and (for randomize mode) inclusion probability.
# NOTE: Thin Film was removed. Research turned up that it's a full KeyShot
# *material type* (its own iridescent BRDF, like Metal or Plastic) -- not a
# texture with a bump/height output. Wiring it into a bump input slot, as
# the previous version of this script did, is a category error with
# undefined behavior -- the leading suspect for "wild" results. Bringing
# Thin Film back properly would mean offering it as an alternate base
# material (a MATERIALS row), not a layer toggle, which is a bigger
# change than this fix (a later phase).
FEATURE_KEYS = [
    "add_fine_noise", "add_scratches", "add_rounded_edges", "add_spots",
    "add_cellular", "add_fractal_roughness", "add_occlusion_roughness",
    "add_color_gradient",
]
FEATURE_LABELS = {
    "add_fine_noise":          "Fine noise (micro-grain bump)",
    "add_scratches":           "Scratches",
    "add_rounded_edges":       "Rounded / worn edges",
    "add_spots":                "Spots / pitting",
    "add_cellular":              "Cellular corrosion (experimental)",
    "add_fractal_roughness":    "Broad roughness variation (fractal noise)",
    "add_occlusion_roughness":  "Crevice grime (occlusion -> roughness)",
    "add_color_gradient":       "Color/tint variation (experimental)",
}
FEATURE_PROBS = {  # used only when "Randomize features" is checked
    "add_fine_noise": 0.85, "add_scratches": 0.55, "add_rounded_edges": 0.35,
    "add_spots": 0.25, "add_cellular": 0.15, "add_fractal_roughness": 0.6,
    "add_occlusion_roughness": 0.25, "add_color_gradient": 0.12,
}

# Per-family wear-layer gating (AB04). Maps a family -> the set of FEATURE_KEYS
# that make physical sense on it. build_material intersects the user's chosen
# features with this set BEFORE building the buses, logging each dropped layer --
# so e.g. clear glass never gets grime/pitting/cellular-corrosion. opaque and
# metal_aniso allow everything (a brushed metal is still a metal). Dielectric and
# thin film drop the "dirt/corrosion" layers (spots, cellular, occlusion grime)
# and the colour-gradient driver (their look comes from the shader, not a tint);
# scratches stay (they read as frosting / fine surface texture), and fractal
# broad-roughness stays for dielectric (mild). A family absent from this map
# falls back to "all allowed" so a future family is never silently crippled.
# (Defined here, AFTER FEATURE_KEYS, because it references it.)
FAMILY_ALLOWED_LAYERS = {
    "opaque":      set(FEATURE_KEYS),
    "metal_aniso": set(FEATURE_KEYS),
    "dielectric":  set(["add_fine_noise", "add_scratches",
                        "add_rounded_edges", "add_fractal_roughness"]),
    "thinfilm":    set(["add_fine_noise", "add_scratches", "add_rounded_edges"]),
}

# Masking modifiers -- separate from FEATURE_KEYS so they never get swept into
# the loud-layer cap or randomize logic. Opt-in, off by default; read straight
# from opts in sample_spec.
MASK_KEYS = ["mask_scratches_to_edges", "mask_spots_to_cavities"]

DEFAULT_OPTIONS = {
    "name_prefix": "MAT",
    "material_type": "Aluminum (brushed metal)",
    "wear_level": "Light Wear",
    # Finish default. "Brushed" is the safe middle. The human may prefer "Worn"
    # as the default (they want more distortion) -- change this ONE word to swap.
    "finish": "Brushed",
    "wear_multiplier": 1.0,
    # AB05: characteristic part size in mm. 0 = auto (measure the scene, else fall
    # back to DEFAULT_PART_SIZE_MM). Entering the real size (e.g. 40) is the most
    # reliable route to correct texture scaling.
    "part_size_mm": 0.0,
    "add_fine_noise": True,
    "add_scratches": True,
    "add_rounded_edges": False,
    "add_spots": False,
    "add_cellular": False,
    "add_fractal_roughness": True,
    "add_occlusion_roughness": False,
    "add_color_gradient": False,
    "mask_scratches_to_edges": False,
    "mask_spots_to_cavities": False,
    "randomize_features": False,
    # NB: KeyShot's getInputDialog rejects an EMPTY string default ("Default
    # value of a string tuple cannot be empty!"), so the "random" sentinel is
    # a non-empty word, not "". _apply_seed treats auto/random/none as no seed.
    "random_seed": "auto",
    "name_filter": "",
}


def clamp01(v):
    return max(0.0, min(1.0, v))


def as_float(v, default):
    """Coerce v to float, returning `default` on None / non-numeric (AB04 family
    params arrive from a plain dict and may be None or malformed)."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def clampf(v, lo, hi):
    """Clamp v into [lo, hi] (used for family params with a non-[0,1] range, e.g.
    IOR ~1.0..3.0 or film thickness in nm)."""
    return max(lo, min(hi, v))


# Material names must stay globally unique even when a run is seeded for a
# reproducible *look* (see _apply_seed), so the ID suffix is drawn from a
# dedicated, never-seeded RNG. This also keeps the createSceneMaterial
# collision-retry loop from regenerating the same name five times in a row.
_name_rng = random.Random()


def random_suffix(n=6):
    return "".join(_name_rng.choice("0123456789ABCDEF") for _ in range(n))


def resolve_filter(value, sentinel="ALL"):
    """Normalize a name-filter dialog field: None, '', or the sentinel all
    mean 'no filter' (match everything)."""
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


def resolve_material_name(prefix, material_type, wear_level, finish_level=None):
    base = (prefix or "MAT").strip().upper().replace(" ", "_") or "MAT"
    type_code = TYPE_ABBR.get(material_type, "GEN")
    wear_code = WEAR_ABBR.get(wear_level, "GEN")
    if finish_level is not None:
        finish_code = FINISH_ABBR.get(finish_level, "GEN")
        return "{0}-{1}-{2}-{3}-{4}".format(base, type_code, wear_code, finish_code, random_suffix())
    return "{0}-{1}-{2}-{3}".format(base, type_code, wear_code, random_suffix())


def randomize_feature_flags():
    """Randomize, but cap how many 'loud' bump layers can stack at once --
    independently rolling each one (the previous approach) could enable
    all four simultaneously, which compounds into chaotic surface noise
    even though each layer alone is tuned to be subtle."""
    flags = {k: False for k in FEATURE_KEYS}
    flags["add_fine_noise"] = random.random() < FEATURE_PROBS["add_fine_noise"]

    loud_candidates = [k for k in LOUD_BUMP_FEATURES if random.random() < FEATURE_PROBS[k]]
    random.shuffle(loud_candidates)
    for k in loud_candidates[:MAX_SIMULTANEOUS_LOUD_LAYERS]:
        flags[k] = True

    flags["add_fractal_roughness"] = random.random() < FEATURE_PROBS["add_fractal_roughness"]
    flags["add_occlusion_roughness"] = random.random() < FEATURE_PROBS["add_occlusion_roughness"]
    flags["add_color_gradient"] = random.random() < FEATURE_PROBS["add_color_gradient"]

    # Don't over-stack the roughness bus in randomize mode: the roughness bus
    # (build_roughness_bus) can now composite fractal + occlusion together, but
    # in randomize mode we keep AA02's de-confliction so seeds stay tame and
    # reproducible (manual mode is free to enable both and exercise the bus).
    if flags["add_fractal_roughness"] and flags["add_occlusion_roughness"]:
        if random.random() < 0.5:
            flags["add_occlusion_roughness"] = False
        else:
            flags["add_fractal_roughness"] = False
    return flags


def _apply_seed(opts):
    """Seed the feature/parameter RNG for reproducible variants. Blank = fully
    random. Only meaningful with 'Randomize features' on -- in manual mode the
    look is fully determined by the checkboxes, so a seed has nothing to vary.
    Material *names* stay unique regardless (see _name_rng). Accepts an int or
    any hashable string. Returns the applied seed (int or str), or None."""
    raw = str(opts.get("random_seed", "") or "").strip()
    if not raw or raw.lower() in ("auto", "random", "none"):
        return None
    try:
        seed = int(raw)
    except ValueError:
        seed = raw
    random.seed(seed)
    return seed


def derive_placement_seed(seed):
    """Pick the per-build texture-placement seed (change 3). If the human gave a
    real feature seed, derive the placement seed deterministically from it (so a
    seeded build tiles identically on replay) but on a DISTINCT stream from the
    feature RNG; otherwise draw a fresh random int. Either way the chosen int is
    captured into spec['meta']['placement_seed'] so ANY build is reproducible
    from the emitted spec. Kept independent of _name_rng (names must vary even
    when the look is seeded).

    Note: seeding a Random with a STRING is stable across runs (Python's
    version-2 seeding hashes str/bytes via sha512); seeding with an arbitrary
    object would fall through to hash() and be process-randomised -- hence the
    explicit "placement|"+str(seed) string key."""
    if seed is not None:
        return random.Random("placement|" + str(seed)).randint(0, 2147483647)
    return random.Random().randint(0, 2147483647)


# --------------------------------------------------------------------------
# Part-size resolution (AB05) -- entered > measured > default
# --------------------------------------------------------------------------
# KeyShot's default "Center On: Model" maps a procedural texture's tiling Scale to
# the whole model's bounding box, so a fixed Scale reads completely differently on
# a 40 mm part vs a 6700-unit model. AB05 resolves a characteristic PART dimension
# (mm) and drives every texture Scale off it (SCALE_FRACTIONS). This is where that
# dimension comes from. The bounding-box APIs below are UNPROBED on the real build
# -- every call is guarded, and a total miss just falls back to the default.

# Candidate lux bounding-box methods, tried in order per geometry node. Only
# getBoundingBox is documented as confirmed elsewhere in the repo (getSceneInfo
# unit-scale + getBoundingBox(world=True)); getWorldBounds/getBounds are plausible
# node-level alternates. All are getattr-guarded -> absence is non-fatal.
BBOX_METHODS = ["getWorldBounds", "getBounds", "getBoundingBox"]


def _vec3(v):
    """Best-effort extract (x, y, z) floats from an unknown vector-like value:
    attribute style (.x/.y/.z), method style (.getX()/.getY()/.getZ()), or an
    indexable ([0]/[1]/[2]). Returns a 3-tuple of floats, or None."""
    if v is None:
        return None
    try:
        return (float(v.x), float(v.y), float(v.z))
    except Exception:
        pass
    try:
        return (float(v.getX()), float(v.getY()), float(v.getZ()))
    except Exception:
        pass
    try:
        return (float(v[0]), float(v[1]), float(v[2]))
    except Exception:
        pass
    return None


def _extent_from_bounds(bounds):
    """Coerce an unknown bounding-box return into a max linear extent
    (max of dx, dy, dz) in mm, or None if the shape isn't understood. Accepts an
    object with .min/.max (or .getMin()/.getMax()), a (min, max) pair, or a flat
    6-sequence [minx, miny, minz, maxx, maxy, maxz]."""
    if bounds is None:
        return None
    mn = None
    mx = None
    try:
        if hasattr(bounds, "min") and hasattr(bounds, "max"):
            mn = _vec3(bounds.min)
            mx = _vec3(bounds.max)
        elif hasattr(bounds, "getMin") and hasattr(bounds, "getMax"):
            mn = _vec3(bounds.getMin())
            mx = _vec3(bounds.getMax())
    except Exception:
        mn = None
        mx = None
    if mn is None or mx is None:
        seq = None
        try:
            seq = list(bounds)
        except Exception:
            seq = None
        if seq is not None:
            if len(seq) == 2:
                mn = _vec3(seq[0])
                mx = _vec3(seq[1])
            elif len(seq) >= 6:
                try:
                    mn = (float(seq[0]), float(seq[1]), float(seq[2]))
                    mx = (float(seq[3]), float(seq[4]), float(seq[5]))
                except Exception:
                    mn = None
                    mx = None
    if mn is None or mx is None:
        return None
    dx = abs(mx[0] - mn[0])
    dy = abs(mx[1] - mn[1])
    dz = abs(mx[2] - mn[2])
    ext = max(dx, dy, dz)
    return ext if ext > 0 else None


def measure_part_size(name_filter):
    """Best-effort: walk the scene geometry (reusing the recursive getChildren()
    collection, _collect_descendants) and compute the max part extent (mm) across
    matched nodes, trying the UNPROBED lux bounding-box APIs per node. Returns a
    float, or None if nothing worked -- non-fatal, the caller falls back. Logs
    which method (if any) succeeded so a future rev can lock the API name."""
    try:
        root = lux.getSceneTree()
    except Exception as e:
        print("  [info] part measure: getSceneTree() unavailable ({0})".format(e))
        return None
    try:
        nodes = _collect_descendants(root)
    except Exception:
        nodes = []
    if name_filter:
        nodes = [n for n in nodes if _name_matches(n, name_filter)]
    if not nodes:
        print("  [info] part measure: no geometry nodes found to measure")
        return None
    best = None
    method_used = None
    for node in nodes:
        for method in BBOX_METHODS:
            fn = getattr(node, method, None)
            if fn is None:
                continue
            bounds = None
            # Try world-space first (getBoundingBox(world=True) is the confirmed
            # form elsewhere in the repo), then a plain no-arg call.
            try:
                bounds = fn(world=True)
            except Exception:
                bounds = None
            if bounds is None:
                try:
                    bounds = fn()
                except Exception:
                    bounds = None
            ext = _extent_from_bounds(bounds)
            if ext is not None:
                if best is None or ext > best:
                    best = ext
                method_used = method
                break  # this method worked on this node -- move to the next node
    if best is None:
        print("  [info] part measure: no bounding-box API returned usable bounds "
              "(tried {0}) -- will fall back".format(", ".join(BBOX_METHODS)))
        return None
    print("  [info] part measure: max extent {0} mm via {1}()".format(best, method_used))
    return best


def resolve_part_size(opts, name_filter):
    """Resolve a characteristic part dimension in mm. Priority:
      1. Operator-entered `part_size_mm` (> 0) -- most reliable (they know it).
      2. Measured via measure_part_size() (UNPROBED bbox APIs, best-effort).
      3. DEFAULT_PART_SIZE_MM fallback, with a clear [info].
    Returns (size_mm float, source str) where source is 'entered'|'measured'|
    'default'. Fully non-fatal -- always returns a usable positive float."""
    entered = as_float(opts.get("part_size_mm"), 0.0)
    if entered and entered > 0.0:
        print("  [info] part size {0} mm (entered)".format(entered))
        return entered, "entered"
    measured = measure_part_size(name_filter)
    if measured is not None and measured > 0.0:
        print("  [info] part size {0} mm (measured)".format(measured))
        return measured, "measured"
    print("  [info] part size unknown -- using default {0} mm; enter a Part size in "
          "the dialog for correct texture scaling".format(DEFAULT_PART_SIZE_MM))
    return DEFAULT_PART_SIZE_MM, "default"


# --------------------------------------------------------------------------
# Options dialog (GUI only -- auto-skipped in headless mode)
# --------------------------------------------------------------------------

def get_options():
    if lux.isHeadless():
        print("Headless session detected -- skipping dialog, using DEFAULT_OPTIONS.")
        return dict(DEFAULT_OPTIONS)

    values = [
        ("name_prefix", lux.DIALOG_TEXT, "Name prefix (blank = 'MAT'):", DEFAULT_OPTIONS["name_prefix"]),
        # DIALOG_ITEM default is an INDEX into the item list, not the label --
        # passing the label string here left KeyShot with no valid default and
        # (combined with the index-typed return value) silently defeated the
        # dropdown. See norm_item below for the matching return-side fix.
        ("material_type", lux.DIALOG_ITEM, "Material type:",
         MATERIAL_TYPE_ORDER.index(DEFAULT_OPTIONS["material_type"]), MATERIAL_TYPE_ORDER),
        ("wear_level", lux.DIALOG_ITEM, "Wear level:",
         WEAR_ORDER.index(DEFAULT_OPTIONS["wear_level"]), WEAR_ORDER),
        # Finish axis (change 2) -- character, orthogonal to Wear. Same
        # index-default + norm_item normalisation as material_type/wear_level.
        ("finish", lux.DIALOG_ITEM, "Finish (surface character):",
         FINISH_ORDER.index(DEFAULT_OPTIONS["finish"]), FINISH_ORDER),
        ("wear_multiplier", lux.DIALOG_DOUBLE, "Wear fine-tune (x):",
         DEFAULT_OPTIONS["wear_multiplier"], (0.0, 3.0)),
        # AB05: part size (mm) drives part-relative texture scaling. 0 = auto
        # (measure, else default). Placed right after the wear/finish rows.
        ("part_size_mm", lux.DIALOG_DOUBLE, "Part size mm (0 = auto-measure):",
         DEFAULT_OPTIONS["part_size_mm"], (0.0, 100000.0)),
        (lux.DIALOG_LABEL, "-- surface detail --"),
    ]
    for key in ["add_fine_noise", "add_scratches", "add_rounded_edges", "add_spots", "add_cellular"]:
        values.append((key, lux.DIALOG_CHECK, FEATURE_LABELS[key], DEFAULT_OPTIONS[key]))
    values.append((lux.DIALOG_LABEL, "-- masking (targeted wear, opt-in) --"))
    values.append(("mask_scratches_to_edges", lux.DIALOG_CHECK,
                    "Scratches only on edges/corners (curvature mask)",
                    DEFAULT_OPTIONS["mask_scratches_to_edges"]))
    values.append(("mask_spots_to_cavities", lux.DIALOG_CHECK,
                    "Spots / grime only in crevices (occlusion mask)",
                    DEFAULT_OPTIONS["mask_spots_to_cavities"]))
    values.append((lux.DIALOG_LABEL, "-- roughness / color drivers --"))
    for key in ["add_fractal_roughness", "add_occlusion_roughness", "add_color_gradient"]:
        values.append((key, lux.DIALOG_CHECK, FEATURE_LABELS[key], DEFAULT_OPTIONS[key]))
    values.append((lux.DIALOG_LABEL, "-- generation --"))
    values.append(("randomize_features", lux.DIALOG_CHECK,
                    "Randomize features instead (ignores checkboxes above)",
                    DEFAULT_OPTIONS["randomize_features"]))
    values.append(("random_seed", lux.DIALOG_TEXT,
                    "Seed ('auto' = random; only affects Randomize):",
                    DEFAULT_OPTIONS["random_seed"]))
    values.append((lux.DIALOG_LABEL, "-- application --"))
    values.append(("name_filter", lux.DIALOG_TEXT, "Apply to parts matching (ALL = every part):",
                    "ALL"))

    opts = lux.getInputDialog(
        title="Procedural Material Generator (AB05)",
        desc="Tick the layers you want, pick a base + wear + finish, and click OK. "
             "(AB05: part-size-aware texture scaling -- enter your Part size in mm "
             "for correct feature sizes, or leave 0 to auto-measure. Textures now "
             "map Center On: Part, not the whole model.)",
        values=values,
        id="procedural_material_generator_dialog",
    )

    if opts is None:
        print("Dialog cancelled.")
        return None

    def norm_item(v, valid):
        # KeyShot's DIALOG_ITEM return type varies by build: usually the
        # selected index (int), sometimes the label (str), occasionally a
        # list. Normalise all three to a valid label and never return
        # something that isn't a real option -- the old code returned the raw
        # value, so an int index bypassed the selection entirely and always
        # fell through to the default material/wear.
        if isinstance(v, bool):
            v = int(v)
        if isinstance(v, int):
            return valid[v] if 0 <= v < len(valid) else valid[0]
        if isinstance(v, (list, tuple)):
            for candidate in reversed(v):
                r = norm_item(candidate, valid)
                if r in valid:
                    return r
            return valid[0]
        if isinstance(v, str) and v in valid:
            return v
        return valid[0]

    opts["material_type"] = norm_item(opts.get("material_type"), MATERIAL_TYPE_ORDER)
    opts["wear_level"] = norm_item(opts.get("wear_level"), WEAR_ORDER)
    opts["finish"] = norm_item(opts.get("finish"), FINISH_ORDER)
    return opts


# --------------------------------------------------------------------------
# Node/parameter helpers (all non-fatal)
# --------------------------------------------------------------------------

def dump_node(node, label=""):
    try:
        node_label = label or node.getType()
    except Exception:
        node_label = label or "?"
    print("--- {0} ---".format(node_label))
    try:
        for p in node.getParameters():
            print("    name={0:<25} display={1:<25} type={2} pure={3}".format(
                repr(p.getName()), repr(p.getDisplayName()), p.getType(), p.isPure()))
    except Exception as e:
        print("    [warn] couldn't list parameters: {0}".format(e))


def new_node(graph, shader_type, label=""):
    node = graph.newNode(shader_type)
    if DEBUG:
        dump_node(node, label or shader_type)
    return node


def try_new_node(graph, attr_name, label):
    """Resolve lux.<attr_name> safely; create the node if it exists."""
    shader_type = getattr(lux, attr_name, None)
    if shader_type is None:
        print("  [warn] lux.{0} not available in this KeyShot version -- skipping {1}".format(attr_name, label))
        return None
    try:
        return new_node(graph, shader_type, label)
    except Exception as e:
        print("  [warn] couldn't create {0} ({1}): {2} -- skipping".format(label, attr_name, e))
        return None


# AB04: family-specific shader fallback chains. NONE of the new constants
# (SHADER_TYPE_DIELECTRIC/GLASS/SOLID_GLASS, SHADER_TYPE_THIN_FILM) are probed on
# the real build -- resolve_shader tries them in order via getattr and drops to a
# working opaque shader (Plastic then Metal) with a logged note if all are absent.
FAMILY_SHADER_FALLBACKS = {
    "dielectric": ["SHADER_TYPE_DIELECTRIC", "SHADER_TYPE_GLASS", "SHADER_TYPE_SOLID_GLASS"],
    "thinfilm":   ["SHADER_TYPE_THIN_FILM"],
}


def resolve_shader(shader_attr, family="opaque"):
    """Resolve a base-material shader by attribute name, falling back through the
    family's alternates (AB04) and then to Plastic/Metal, so an unknown constant
    (e.g. SHADER_TYPE_PAINT, or the new SHADER_TYPE_DIELECTRIC / SHADER_TYPE_THIN_FILM
    on a build that lacks them) degrades to a working material instead of crashing.
    For an opaque row this is identical to AB03 (chain = shader, Plastic, Metal)."""
    chain = [shader_attr]
    for alt in FAMILY_SHADER_FALLBACKS.get(family, []):
        if alt not in chain:
            chain.append(alt)
    # Thin film prefers a Metal fallback (an iridescent coating still reads best on
    # a metal base); everything else prefers Plastic first. Both end at Metal.
    tail = ["SHADER_TYPE_METAL", "SHADER_TYPE_PLASTIC"] if family == "thinfilm" \
        else ["SHADER_TYPE_PLASTIC", "SHADER_TYPE_METAL"]
    for a in tail:
        if a not in chain:
            chain.append(a)
    for attr in chain:
        st = getattr(lux, attr, None)
        if st is not None:
            if attr != shader_attr:
                print("  [warn] {0} unavailable on this build -- using {1} instead".format(shader_attr, attr))
            return st
    return None


def apply_family_params(graph, base_node, extra, rng):
    """Apply the family-specific shader params to the base node (AB04), AFTER its
    colour + roughness are set. EVERY set is best-effort via find_param/set_display
    -- an absent param logs a [warn]/[info] and the build continues (the material
    still works, it just misses that one refinement). All display names are
    UNPROBED guesses; find_param prefers exact display-name matches. Returns the
    family string handled. `rng` is the seeded placement RNG (used only for the
    stable per-build anisotropy angle, so it is reproducible from placement_seed)."""
    family = material_family(extra)
    if family == "metal_aniso":
        # Directional (brushed) highlight strength.
        set_display(base_node, ["anisotropy", "aniso"], clamp01(as_float(extra.get("anisotropy"), 0.5)))
        # Angle: the Scratches direction_field is a type-2 enum (not a degree
        # value), so we deliberately do NOT read it. Pick a STABLE per-build angle
        # from the placement RNG and record it, so the brush highlight has a
        # consistent (reproducible) per-material orientation. CONFIRM AT RENDER:
        # the "anisotropy angle" display name (degrees vs 0-1 is unprobed).
        angle = extra.get("aniso_angle")
        if angle is None:
            angle = rng.uniform(0.0, 180.0)
        extra["aniso_angle_used"] = angle
        set_display(base_node, ["anisotropy angle", "aniso angle", "angle"], angle)
    elif family == "dielectric":
        set_display(base_node, ["index of refraction", "ior", "refraction index"],
                    clampf(as_float(extra.get("ior"), 1.51), 1.0, 3.0))
        frost = clamp01(as_float(extra.get("frost"), 0.0))
        if frost > 0.0:
            # The roughness bus still targets the base roughness input, and the
            # frosted row already sets a high base roughness -- so frosting shows
            # even if the dedicated param below is absent. Also try a refraction-
            # roughness param (some glass BRDFs separate surface vs refraction
            # roughness). CONFIRM AT RENDER: the "refraction roughness" name.
            set_display(base_node, ["refraction roughness"], frost)
        # Absorption / tint is via the base colour input (set in build_material).
    elif family == "thinfilm":
        set_display(base_node, ["thickness", "film thickness"],
                    clampf(as_float(extra.get("film_thickness"), 500.0), 1.0, 2000.0))
        set_display(base_node, ["index of refraction", "ior"],
                    clampf(as_float(extra.get("film_ior"), 1.4), 1.0, 3.0))
    return family


def find_param(node, keywords, ptype=None):
    """Find a parameter by display name. Change 1 (AB02, root-cause fix): prefer
    an EXACT (case-insensitive) display-name match across ALL params FIRST, then
    fall back to the original substring scan. This kills the substring collision
    where a short keyword like "noise" matched "Directional Noise" (and clobbered
    it) before the real "Noise" param was ever reached. The two passes are
    order-independent per keyword, so every existing setter is strictly hardened.
    ptype filtering behaviour is identical to before: a display match whose type
    doesn't pass the filter is skipped (the scan continues), not returned."""
    if isinstance(keywords, str):
        keywords = [keywords]
    try:
        params = node.getParameters()
    except Exception:
        return None
    # Pass 1 -- EXACT display-name match (case-insensitive, whitespace-trimmed).
    for kw in keywords:
        kwx = kw.strip().lower()
        for p in params:
            if p.getDisplayName().strip().lower() == kwx:
                if ptype is None or p.getType() == ptype:
                    return p
    # Pass 2 -- substring fallback (the original AB01 behaviour), so multi-word
    # keyword lists like ["bump height", "height", "amount"] still resolve when
    # no exact match exists on this node.
    for kw in keywords:
        kwx = kw.lower()
        for p in params:
            if kwx in p.getDisplayName().lower():
                if ptype is None or p.getType() == ptype:
                    return p
    return None


def connection_param_names(node, ptype):
    if ptype is None:
        return []
    return [p.getName() for p in node.getParameters() if p.getType() == ptype]


def set_display(node, keywords, value, ptype=None):
    label = keywords if isinstance(keywords, str) else "/".join(keywords)
    p = find_param(node, keywords, ptype)
    if p is None:
        print("  [warn] no parameter matching '{0}' on this node".format(label))
        return False
    if p.isPure():
        print("  [warn] '{0}' is a connection-only (pure) parameter".format(label))
        return False
    try:
        p.setValue(value)
        return True
    except Exception as e:
        print("  [warn] couldn't set '{0}'={1}: {2} (left at default)".format(label, repr(value), e))
        return False


def safe_edge(graph, source, target, param, label=""):
    try:
        graph.newEdge(source=source, target=target, param=param)
        return True
    except Exception as e:
        print("  [warn] couldn't wire {0}: {1}".format(label or param, e))
        return False


def combine_bump_sources(graph, sources):
    """Chain N bump-domain nodes together pairwise via Bump Add. Non-fatal:
    if a chain link fails, returns the best combination achieved so far."""
    sources = [s for s in sources if s is not None]
    if not sources:
        return None
    if len(sources) == 1:
        return sources[0]
    current = sources[0]
    for nxt in sources[1:]:
        bump_add = try_new_node(graph, "SHADER_TYPE_BUMP_ADD", "Bump Add")
        if bump_add is None:
            print("  [warn] stopping bump combination early -- Bump Add unavailable")
            return current
        slots = connection_param_names(bump_add, PT_SHADERBUMP)
        if len(slots) < 2:
            print("  [warn] Bump Add missing expected 2 inputs (found {0}) -- stopping chain".format(slots))
            return current
        ok1 = safe_edge(graph, source=current, target=bump_add, param=slots[0], label="bump chain a")
        ok2 = safe_edge(graph, source=nxt, target=bump_add, param=slots[1], label="bump chain b")
        current = bump_add if (ok1 and ok2) else current
    return current


def wire_scalar_driver(graph, texture_node, base_node, keywords, label):
    p = find_param(base_node, keywords)
    if p is None:
        print("  [warn] no {0}-like parameter found on base material -- skipping".format(label))
        return False
    ok = safe_edge(graph, source=texture_node, target=base_node, param=p.getName(),
                    label="-> base.{0}".format(label))
    if not ok:
        print("  [info] {0} driver skipped -- static default still applies".format(label))
    return ok


# --------------------------------------------------------------------------
# Anti-repetition: seeded per-material texture placement (FIX 2, AB03)
# --------------------------------------------------------------------------
# KeyShot procedural textures are deterministic and world-aligned, so without
# per-material variety every build tiles IDENTICALLY and reads as fake / too-
# perfect even with noise on.
#
# WHY THIS WAS REWRITTEN (root cause, confirmed): AB02's randomize_placement()
# guessed offset/rotation/translate param names -- but the real AB02 DEBUG dump
# shows those params DO NOT EXIST on any of these nodes. Every set missed, so
# placement never actually varied anything (the console was full of
# "placement: offset/rotation not settable here").
#
# THE ONE real placement lever is the type-12 'Texture Transform' matrix
# (transform_obj_to_uv), present on every tiling node. We DELIBERATELY LEAVE IT
# UNSET: writing a raw 4x4/3x3 texture-transform matrix blind -- with no probe
# of its expected shape/units on this build -- is too risky and could throw a
# feature wildly off-surface. Instead, variety comes from jittering the REAL,
# per-node scalar params that shape each pattern. EVERY name used below is
# confirmed present in the AB02 ground-truth param list, so these are no longer
# "unprobed guesses" -- they are the actual pattern-shaping controls:
#   * ALL tiling nodes : scale        (read-and-multiply x[0.80,1.25])
#   * Scratches        : + noise_scale x[0.7,1.4], level_scale x[0.85,1.2]
#   * Fine Noise       : magnitude    x[0.85,1.15]   (subtle)
#   * Fractal Noise    : scale only (mild -- broad-band roughness, keep gentle)
#   * Spots            : seed <- fresh int (the single best variety lever),
#                        distortion += [0.0,0.15] (capped), radius x[0.85,1.2]
#   * Cellular         : noise_scale x[0.7,1.4], shape_1/2/3 each x[0.9,1.1]
#   * Occlusion (rough): bias_x/y/z <- [-0.5,0.5]   (offsets the AO sampling)
# Driven by the seeded placement RNG, so every build is reproducible from
# spec['meta']['placement_seed']; runs for EVERY build. Fully defensive: every
# miss logs an [info] and the build continues. find_param's exact-match-first
# (change 1) keeps e.g. "Scale" from colliding with "Noise Scale".


def _try_set_placement(param, value, what):
    """Best-effort setValue for a placement param. Non-fatal: any failure logs an
    [info] and returns False -- the build continues with the node's default."""
    try:
        param.setValue(value)
        return True
    except Exception as e:
        print("  [info] placement: {0} not settable here ({1})".format(what, e))
        return False


def _placement_param(node, keywords, what):
    """Resolve a jitter target defensively. Returns the param, or None (logging an
    [info]) when it is missing or connection-only -- so callers stay one-liners."""
    p = find_param(node, keywords)
    if p is None:
        print("  [info] placement: {0} not settable here (no matching param)".format(what))
        return None
    if p.isPure():
        print("  [info] placement: {0} is connection-only here -- skipped".format(what))
        return None
    return p


def _jitter_mult(node, keywords, rng, lo, hi, what, base_default=None):
    """Multiply a scalar param by uniform(lo, hi). Prefers reading the current
    value and multiplying; if it can't be read, falls back to base_default*factor
    when a base is supplied, else logs and leaves the node default. Best-effort."""
    p = _placement_param(node, keywords, what)
    if p is None:
        return False
    factor = rng.uniform(lo, hi)
    cur = None
    try:
        cur = p.getValue()
    except Exception:
        cur = None
    if isinstance(cur, (int, float)) and not isinstance(cur, bool) and cur:
        return _try_set_placement(p, cur * factor, what)
    if base_default is not None:
        return _try_set_placement(p, base_default * factor, what)
    print("  [info] placement: {0} value unreadable and no base -- left at default".format(what))
    return False


def _jitter_add(node, keywords, rng, lo, hi, what, cap=None):
    """Add uniform(lo, hi) to a scalar param (reads current, else treats as 0),
    clamped to [0, cap] when a cap is given. Best-effort."""
    p = _placement_param(node, keywords, what)
    if p is None:
        return False
    add = rng.uniform(lo, hi)
    cur = None
    try:
        cur = p.getValue()
    except Exception:
        cur = None
    if not isinstance(cur, (int, float)) or isinstance(cur, bool):
        cur = 0.0
    val = cur + add
    if cap is not None:
        val = min(cap, val)
    val = max(0.0, val)
    return _try_set_placement(p, val, what)


def _jitter_set(node, keywords, rng, lo, hi, what):
    """Set a scalar param directly to uniform(lo, hi) -- for params that ARE the
    offset (e.g. Occlusion bias_x/y/z), not a value to scale. Best-effort."""
    p = _placement_param(node, keywords, what)
    if p is None:
        return False
    return _try_set_placement(p, rng.uniform(lo, hi), what)


def _set_fresh_seed(node, rng, what="seed"):
    """Set an integer Seed param to a fresh value from the placement RNG. For
    Spots this is the single strongest variety lever (a real 'Seed' param).
    Kept in a moderate range so a build with a narrow seed domain still takes."""
    p = _placement_param(node, [what, "seed"], what)
    if p is None:
        return False
    return _try_set_placement(p, rng.randint(0, 999999), what)


def randomize_placement(node, rng, kind=None, scale_base=None):
    """Apply per-material variety to one procedural texture node by jittering its
    REAL pattern-shaping scalars (see the module note above -- the type-12 Texture
    Transform matrix is intentionally left unset). `kind` selects the node-aware
    jitter table; it is the node label already passed at creation, normalised to a
    short key. `scale_base` (AB05) is the resolved PART-RELATIVE scale for this
    node, used as the read-and-multiply fallback so the jitter stays part-
    appropriate even if the live value can't be read; when None, the BASE absolute
    is used (legacy behaviour). Drawn from `rng` (seeded off placement_seed,
    reproducible), runs for EVERY build, fully defensive -- every miss is a logged
    [info], never fatal."""
    if node is None:
        return
    k = (kind or "").strip().lower()

    # ALL tiling nodes share a 'scale' tiling control. Read-and-multiply; if the
    # value can't be read, fall back to the resolved part-relative scale (AB05),
    # else the node's BASE absolute * factor.
    if scale_base is None:
        scale_base = {
            "fine_noise": BASE["fine_noise_scale"],
            "scratches": BASE["scratch_scale"],
            "fractal": BASE["fractal_scale"],
            "cellular": BASE["cellular_scale"],
        }.get(k)
    if k in ("fine_noise", "scratches", "fractal", "cellular", "spots"):
        _jitter_mult(node, ["scale"], rng, 0.80, 1.25, "scale", scale_base)

    if k == "scratches":
        _jitter_mult(node, ["noise scale", "noise_scale"], rng, 0.7, 1.4, "noise_scale")
        _jitter_mult(node, ["level scale", "level_scale"], rng, 0.85, 1.2, "level_scale")
    elif k == "fine_noise":
        _jitter_mult(node, ["magnitude"], rng, 0.85, 1.15, "magnitude")
    elif k == "fractal":
        # scale (mild) is covered above -- broad-band roughness, keep it gentle.
        pass
    elif k == "spots":
        # Seed is the strongest variety lever on Spots (a real 'Seed' param).
        _set_fresh_seed(node, rng)
        _jitter_add(node, ["distortion"], rng, 0.0, 0.15, "distortion", cap=1.0)
        _jitter_mult(node, ["radius"], rng, 0.85, 1.2, "radius")
    elif k == "cellular":
        _jitter_mult(node, ["noise scale", "noise_scale"], rng, 0.7, 1.4, "noise_scale")
        _jitter_mult(node, ["shape 1", "shape_1"], rng, 0.9, 1.1, "shape_1")
        _jitter_mult(node, ["shape 2", "shape_2"], rng, 0.9, 1.1, "shape_2")
        _jitter_mult(node, ["shape 3", "shape_3"], rng, 0.9, 1.1, "shape_3")
    elif k == "occlusion":
        # bias_x/y/z act as a positional offset of the occlusion sampling -- set
        # directly (they are offsets, not values to scale).
        _jitter_set(node, ["bias x", "bias_x"], rng, -0.5, 0.5, "bias_x")
        _jitter_set(node, ["bias y", "bias_y"], rng, -0.5, 0.5, "bias_y")
        _jitter_set(node, ["bias z", "bias_z"], rng, -0.5, 0.5, "bias_z")
    else:
        print("  [info] placement: unknown node kind {0} -- only scale jittered".format(repr(kind)))


# --------------------------------------------------------------------------
# Color Composite blend-mode setter (defensive) + roughness compositing
# --------------------------------------------------------------------------
# Whether Color Composite's blend_mode sets by int-enum or by string label is
# UNPROBED on the real build (MDD-4B7A9F sec 4.1, probe P8). So the setter tries
# BOTH -- string first (semantically unambiguous; an int index is positional and
# could silently select the wrong mode if the enum order differs on this build),
# then int -- and verifies via getValue() when the build allows a read-back. If
# it can't be set/confirmed, the composite keeps the node's default blend and we
# log it; the roughness bus itself degrades to single-driver if the whole chain
# can't be built.

# Lighten's position in KeyShot's documented blend list
# (Normal, Multiply, Screen, Overlay, Soft Light, Hard Light, Darken, Lighten,
#  Burn, Difference, Sum) -- index 7. Only used as the int candidate.
BLEND_LIGHTEN_NAME = "Lighten"
BLEND_LIGHTEN_INT = 7


def _blend_matches(got, name, ival):
    if got == ival:
        return True
    if isinstance(got, str) and got.strip().lower() == name.lower():
        return True
    return False


def set_blend_mode(node, mode_name, mode_int):
    """Set a Color Composite blend mode defensively. Returns True if the mode was
    set (or plausibly set, when read-back isn't supported), False if it couldn't
    be applied -- the caller keeps the composite either way (degrade-never-break;
    a failed blend just means the node's default blend is used)."""
    p = find_param(node, ["blend mode", "blend"])
    if p is None:
        print("  [warn] no blend-mode parameter on Color Composite -- using node default blend")
        return False
    if p.isPure():
        print("  [warn] blend-mode is connection-only (pure) -- can't set, using default blend")
        return False
    can_read = True
    try:
        p.getValue()
    except Exception:
        can_read = False
    # blend_mode is a TYPE-2 int enum in the real AB02 dump, so the int candidate
    # (mode_int = 7 = Lighten) is the one most likely to take. We still try the
    # string label first (unambiguous), then fall through to the int -- keeping
    # both candidates as before, but the int IS always attempted second.
    for val in (mode_name, mode_int, mode_name.lower(), mode_name.upper()):
        try:
            p.setValue(val)
        except Exception:
            continue
        if not can_read:
            # setValue didn't raise and we can't read back to confirm -- accept
            # optimistically (best-effort). Prefer the string candidate, which
            # is why mode_name is tried first.
            return True
        try:
            got = p.getValue()
        except Exception:
            return True
        if _blend_matches(got, mode_name, mode_int):
            return True
    print("  [warn] couldn't confirm blend mode '{0}' -- left at node default".format(mode_name))
    return False


# --------------------------------------------------------------------------
# Center On: Part (texture_space enum) setter (AB05, defensive)
# --------------------------------------------------------------------------
# Every tiling texture node has a 'Center On' control (param texture_space, a
# type-2 enum -- Model vs Part). KeyShot defaults to "Center On: Model", which
# maps the texture's Scale to the WHOLE model's bounding box; on a small part in a
# big model this is the root cause of "textures loading at 6700, part is 40 mm".
# Setting it to "Part" maps the texture to the part's own bounds so a mm-scale
# Scale reads correctly. Which int is "Part" is UNPROBED -- try the string "Part"
# first (unambiguous), then int candidates (1 = Part in the panel order
# Model/Part, else 0), using the same two-candidate + read-back pattern as
# set_blend_mode. CONFIRM-AT-RENDER: the enum value that took.
CENTER_ON_PART_NAME = "Part"
CENTER_ON_PART_INTS = (1, 0)


def set_center_on_part(node):
    """Set a tiling texture's 'Center On' (texture_space) enum to Part so the
    texture maps to the PART's bounding box rather than the whole MODEL. Best-
    effort + logged: the material still builds if the param is absent or the enum
    value can't be confirmed (it just stays at KeyShot's default, Center On:
    Model). Returns True if it was set (or plausibly set when read-back isn't
    supported), else False. Tries the string "Part" first (unambiguous), then the
    int candidates (1 = Part in the panel order Model/Part, else 0); the read-back
    is matched against the SPECIFIC value just set, so an ignored set that leaves
    the node at a Model default (which might equal one of the int candidates)
    doesn't read as a false success."""
    if node is None:
        return False
    p = find_param(node, ["center on", "texture space", "texture_space"])
    if p is None:
        print("  [info] no 'Center On' parameter on this node -- left at default (Model)")
        return False
    if p.isPure():
        print("  [info] 'Center On' is connection-only here -- left at default")
        return False
    can_read = True
    try:
        p.getValue()
    except Exception:
        can_read = False
    candidates = [CENTER_ON_PART_NAME]
    candidates.extend(CENTER_ON_PART_INTS)
    for val in candidates:
        try:
            p.setValue(val)
        except Exception:
            continue
        if not can_read:
            # setValue didn't raise and we can't read back -- accept optimistically
            # (the string "Part" is tried first, so this prefers the unambiguous one).
            return True
        try:
            got = p.getValue()
        except Exception:
            return True
        if isinstance(val, str):
            if isinstance(got, str) and got.strip().lower() == val.lower():
                return True
        else:
            if got == val:
                return True
    print("  [info] couldn't confirm 'Center On' = Part -- left at node default")
    return False


def _composite_inputs(comp):
    """Return (source_param_name, background_param_name) for a Color Composite,
    or (None, None) if two inputs can't be identified.

    FIX 1 (AB03, root-cause): the Composite's Source/Background are colour/texture
    CONNECTION inputs -- KeyShot param TYPE 14 in the real AB02 dump -- NOT the
    plain colour-VALUE type (13 = PT_COLOR). AB02 searched for them with
    ptype=PT_COLOR, matched NOTHING, and stopped the roughness chain, forcing
    single-fallback every run. Identify them by NAME with NO type filter
    ('Source' / 'Background' in the dump); the positional fallback derives the
    connection type from those params defensively rather than hardcoding 14."""
    # Primary: by display name, no type filter (they are connection inputs).
    src = find_param(comp, ["source", "foreground", "top"])
    bg = find_param(comp, ["background", "base", "bottom"])
    if src is not None and bg is not None and src.getName() != bg.getName():
        return src.getName(), bg.getName()

    try:
        params = comp.getParameters()
    except Exception:
        params = []

    # Derive the connection-colour type from whichever named input we DID find,
    # so we never blindly hardcode 14 as a lux constant.
    conn_type = None
    for cand in (src, bg):
        if cand is not None and conn_type is None:
            try:
                conn_type = cand.getType()
            except Exception:
                conn_type = None

    names = []
    if conn_type is not None:
        # The connection inputs are the non-pure params of that type
        # (clipping_mask is type 14 too but pure, so it's excluded).
        for p in params:
            try:
                if p.getType() == conn_type and not p.isPure():
                    names.append(p.getName())
            except Exception:
                continue
    else:
        # No named input found on this build -- exclude the KNOWN non-inputs by
        # display name (blend_mode/mask_mode are int enums; alpha/background_alpha/
        # source_alpha are floats; clip_using_source/invert_mask are bools;
        # clipping_mask is pure) and take the first two remaining non-pure params.
        _NON_INPUTS = ("blend mode", "blend", "mask mode", "alpha", "source alpha",
                       "background alpha", "clip using source", "invert mask",
                       "clipping mask")
        for p in params:
            try:
                if p.isPure():
                    continue
                dn = p.getDisplayName().strip().lower()
                if dn in _NON_INPUTS:
                    continue
                names.append(p.getName())
            except Exception:
                continue
    if len(names) >= 2:
        return names[0], names[1]
    return None, None


def combine_roughness_composite(graph, sources):
    """Composite N roughness-source nodes into a single output node via a chain
    of Color Composite nodes, blend mode Lighten (per-pixel max). Non-fatal:
    returns the best node achieved so far -- if no composite can be built it
    returns sources[0] (highest-priority source), which the bus then wires as a
    single driver (AA02 behaviour). sources[0] is kept on the SOURCE side of
    every composite, so if a blend mode silently defaults to Normal the highest-
    priority source (scratches) still shows through rather than being replaced."""
    sources = [s for s in sources if s is not None]
    if not sources:
        return None
    if len(sources) == 1:
        return sources[0]
    current = sources[0]
    for nxt in sources[1:]:
        comp = try_new_node(graph, "SHADER_TYPE_COLOR_COMPOSITE", "Color Composite (roughness Lighten)")
        if comp is None:
            print("  [warn] Color Composite unavailable -- stopping roughness composite early")
            return current
        src_name, bg_name = _composite_inputs(comp)
        if not src_name or not bg_name:
            print("  [warn] Color Composite missing 2 colour inputs -- stopping roughness chain")
            try:
                graph.removeNode(comp)
            except Exception:
                pass
            return current
        ok1 = safe_edge(graph, source=current, target=comp, param=src_name, label="rough composite source")
        ok2 = safe_edge(graph, source=nxt, target=comp, param=bg_name, label="rough composite background")
        if not (ok1 and ok2):
            print("  [warn] couldn't wire a roughness composite input -- stopping chain")
            try:
                graph.removeNode(comp)
            except Exception:
                pass
            return current
        set_blend_mode(comp, BLEND_LIGHTEN_NAME, BLEND_LIGHTEN_INT)
        current = comp
    return current


def build_roughness_bus(graph, base_node, sources):
    """The roughness bus. `sources` is the list of roughness-source nodes in
    priority order (scratches first, then fractal, then occlusion). Returns a
    short string describing what landed, for the console/manifest:
      'value'           -- no sources; base roughness value stands
      'single'          -- one source wired straight in (AA02 behaviour)
      'composite'       -- multiple sources composited via Lighten (NEW)
      'single-fallback' -- compositing failed; degraded to one driver
    Degrade-never-break: any failure leaves the base's static roughness value
    (already set on the base node) as the ultimate fallback."""
    sources = [s for s in sources if s is not None]
    if not sources:
        return "value"
    if len(sources) == 1:
        ok = wire_scalar_driver(graph, sources[0], base_node, ["roughness"], "roughness")
        return "single" if ok else "value"

    combined = combine_roughness_composite(graph, sources)
    if combined is None:
        combined = sources[0]
    composited = combined is not sources[0]
    ok = wire_scalar_driver(graph, combined, base_node, ["roughness"],
                            "roughness (composite)" if composited else "roughness (fallback)")
    if ok:
        return "composite" if composited else "single-fallback"
    # Wiring the composite output into base.roughness failed -- last-ditch:
    # try the highest-priority source alone.
    if composited:
        ok2 = wire_scalar_driver(graph, sources[0], base_node, ["roughness"], "roughness (fallback)")
        return "single-fallback" if ok2 else "value"
    return "value"


# --------------------------------------------------------------------------
# Masking (targeted wear) -- Curvature/Occlusion mask onto a bump layer's
# bump-height. Node ids confirmed (11.0 lux ref); input-slot names discovered
# at run time; any wiring failure degrades to the unmasked effect so masking
# can never break the base material. See MWR-9C4E21. (Unchanged from AB01.)
# --------------------------------------------------------------------------

def add_curvature_mask(graph):
    """Convex-edge mask: white on positive curvature (edges/corners), black on
    the flats -- param names confirmed from the material-graph dump. Feeds a
    bump layer's bump-height so wear lands only on the edges."""
    n = try_new_node(graph, "SHADER_TYPE_CURVATURE", "Curvature (edge mask)")
    if n is None:
        return None
    set_display(n, ["positive curvature"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
    set_display(n, ["zero curvature"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
    set_display(n, ["negative curvature"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
    return n


def add_occlusion_mask(graph):
    """Cavity mask: white in occluded crevices, black on exposed faces -- the
    inverse of the edge mask, so grime composited through it collects in the
    cavities. Occluded/unoccluded colour param names vary by build; best-effort
    (masking degrades gracefully if they aren't found)."""
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (cavity mask)")
    if n is None:
        return None
    set_display(n, ["occluded"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
    set_display(n, ["unoccluded", "bright", "far", "exposed"], (0.0, 0.0, 0.0),
                ptype=PT_COLOR)
    return n


def mask_bump_layer(graph, effect_node, mask_node, label):
    """Spatially gate a bump layer by mapping the mask texture into the effect's
    bump-height input, so bump strength follows the mask (white = full on the
    edges/cavities, black = none on the flats). The effect stays a plain texture,
    so it still chains into Bump Add normally -- and if bump-height isn't
    mappable on this build the layer is left unmasked (present, not dropped).

    Supersedes the earlier Color Composite approach: a Composite outputs a
    colour, which KeyShot will not accept into a bump input -- the graph dump
    showed 'Could not create requested edge', so the whole layer got silently
    dropped. Mapping the mask onto bump-height keeps everything in the bump
    domain."""
    if effect_node is None or mask_node is None:
        return effect_node
    p = find_param(effect_node, ["bump height", "height", "amount"])
    if p is None:
        print("  [warn] {0}: no bump-height input to mask on -- left unmasked".format(label))
        return effect_node
    ok = safe_edge(graph, source=mask_node, target=effect_node, param=p.getName(),
                   label="{0}: mask -> bump height".format(label))
    if not ok:
        print("  [info] {0}: bump-height not mappable here -- left unmasked".format(label))
        try:
            graph.removeNode(mask_node)  # don't leave the mask node orphaned in the graph
        except Exception:
            pass
    return effect_node


# --------------------------------------------------------------------------
# Layer builders -- each returns a node (bump-domain / roughness-source) or
# bool (colour driver). Reused from AB01; the fractal/occlusion roughness
# builders are split into node factories so the roughness bus can composite
# them rather than wiring a single driver.
# --------------------------------------------------------------------------

def add_fine_noise_bump(graph, scale=None):
    n = try_new_node(graph, "SHADER_TYPE_NOISE_TEXTURE", "Fine Noise")
    if n:
        # AB05: part-relative tiling Scale (SCALE_FRACTIONS['fine_noise'] * part
        # size); BASE absolute is the legacy fallback only.
        set_display(n, ["scale"], scale if scale is not None else BASE["fine_noise_scale"])
        # Give it an actual (small) bump amplitude -- without this the micro-grain
        # is dormant and surfaces read as flat CAD.
        set_display(n, ["bump height"], BASE["fine_noise_bump"])
        # AB05: map to the PART, not the whole model.
        set_center_on_part(n)
    return n


def add_scratches_bump(graph, wear_mult, base_roughness, finish, damping=1.0, scale=None):
    """Scratches layer. Change 2: the CHARACTER params (directional noise, noise,
    levels) and the scratch groove-depth BASELINE come DIRECTLY from the Finish
    tuple (NOT wear-scaled -- a brushed finish is brushed at any wear). The wear
    amount still scales the groove AMPLITUDE (and density/size coverage). Change 2
    also sets an explicit Scratches "Scale" (tiling scale) so Density is clearly
    separate from Scale. `finish` is the validated spec['finish'] dict."""
    n = try_new_node(graph, "SHADER_TYPE_SCRATCHES", "Scratches")
    if n:
        dir_noise = finish.get("dir_noise", BASE["scratch_dir_noise"])
        noise = finish.get("noise", BASE["scratch_noise"])
        levels = finish.get("levels", BASE["scratch_levels"])
        finish_bump = finish.get("scratch_bump_height", -BASE["scratch_bump_height"])
        # Effective scratch bump = groove BASELINE (from Finish) scaled by the
        # wear/damping AMPLITUDE, kept NEGATIVE (cuts into the surface) and
        # magnitude-clamped to [0,1] -- the AB01 negative-bump/clamp convention.
        eff_bump = -clamp01(abs(finish_bump) * wear_mult * damping)
        set_display(n, ["bump height"], eff_bump)
        # Coverage stays WEAR-driven.
        set_display(n, ["density"], clamp01(BASE["scratch_density"] * wear_mult))
        set_display(n, ["size"], clamp01(BASE["scratch_size"] * wear_mult))
        # Character stays FINISH-driven (not wear-scaled). Now that find_param
        # prefers exact matches (change 1), ["directional noise"] and ["noise"]
        # resolve to distinct params independently.
        set_display(n, ["directional noise"], clamp01(dir_noise))
        set_display(n, ["noise"], clamp01(noise))
        set_display(n, ["levels"], levels)
        # Scratches "Scale" -- the tiling scale, SEPARATE from Density (count) and
        # Size (per-scratch). AB05: part-relative (SCALE_FRACTIONS['scratch_scale']
        # * part size -> ~4.8 mm on a 40 mm part, matching the old absolute 5.0);
        # BASE absolute is the legacy fallback only. Defensive: skip-with-warn via
        # set_display if the param is absent. CONFIRM AT RENDER: display name "Scale".
        set_display(n, ["scale"], scale if scale is not None else BASE["scratch_scale"])
        # Colours drive ROUGHNESS. KeyShot's convention (confirmed from the v2
        # render, where a bright background flattened everything): brighter
        # texture = ROUGHER. So the scratch line is light -> a matte streak that
        # reads on gloss, and the Background is set to the base material's OWN
        # roughness so the surrounding metal keeps its finish and its metallic
        # sheen instead of going uniformly matte. This is what makes scratches a
        # roughness-bus source, not just a bump layer.
        set_display(n, ["color"], (0.75, 0.75, 0.75), ptype=PT_COLOR)
        bg = clamp01(base_roughness)
        set_display(n, ["background"], (bg, bg, bg), ptype=PT_COLOR)
        # AB05: map to the PART, not the whole model.
        set_center_on_part(n)
    return n


def add_rounded_edges_bump(graph, wear_mult, damping=1.0):
    n = try_new_node(graph, "SHADER_TYPE_ROUNDED_EDGES", "Rounded Edges")
    if n:
        set_display(n, ["radius", "bump height", "amount"],
                    clamp01(BASE["edge_amount"] * wear_mult * damping))
    return n


def add_spots_bump(graph, wear_mult, damping=1.0, scale=None):
    n = try_new_node(graph, "SHADER_TYPE_SPOTS", "Spots / Pitting")
    if n:
        set_display(n, ["bump height", "height"], clamp01(BASE["spots_bump_height"] * wear_mult * damping))
        set_display(n, ["density"], clamp01(BASE["spots_density"] * wear_mult))
        # 'Radius' is the per-spot size. Set it on its OWN exact-match key.
        set_display(n, ["radius"], clamp01(BASE["spots_size"] * wear_mult))
        # AB05 FIX (the giant-blobs bug): Spots' OWN tiling "Scale" was NEVER set.
        # The old ["radius","size","scale"] list matched Radius FIRST (exact match),
        # so Scale stayed at KeyShot's ~6700 model-scale default -> giant blobs.
        # Set Scale EXPLICITLY (a separate call from radius), part-relative
        # (SCALE_FRACTIONS['spots_scale'] * part size -> ~2.4 mm on a 40 mm part).
        # CONFIRM AT RENDER: the display name "Scale" on Spots.
        if scale is not None:
            set_display(n, ["scale"], scale)
        # AB05 distortion: drive the pattern organic (not perfectly round). A modest
        # Distortion with a part-relative Distortion Scale reads as irregular pits.
        # Defensive -- both skip-with-warn if absent on this build.
        set_display(n, ["distortion"], 0.4)
        if scale is not None:
            set_display(n, ["distortion scale", "distortion_scale"], scale)
        # AB05: map to the PART, not the whole model.
        set_center_on_part(n)
    return n


def add_cellular_bump(graph, wear_mult, damping=1.0, scale=None):
    # KeyShot's own manual describes this as capable of "cracked surfaces,
    # hammered metal" -- a strong effect even alone, hence the extra 0.6x.
    n = try_new_node(graph, "SHADER_TYPE_CELLULAR", "Cellular (experimental)")
    if n:
        # AB05: part-relative tiling Scale; BASE absolute is the legacy fallback.
        set_display(n, ["scale"], scale if scale is not None else BASE["cellular_scale"])
        set_display(n, ["bump height", "height"],
                    clamp01(BASE["cellular_bump_height"] * wear_mult * damping * 0.6))
        # AB05: map to the PART, not the whole model.
        set_center_on_part(n)
    return n


def make_fractal_roughness_node(graph, base_roughness, scale=None):
    """Create + configure a Fractal Noise node as a ROUGHNESS-bus source (broad
    variation). Returns the node (not wired) so the bus can composite it; None
    if the node type is unavailable."""
    n = try_new_node(graph, "SHADER_TYPE_NOISE_FRACTAL", "Fractal Noise (roughness source)")
    if n is not None:
        # AB05: part-relative tiling Scale; BASE absolute is the legacy fallback.
        set_display(n, ["scale"], scale if scale is not None else BASE["fractal_scale"])
        # Constrain the noise to a TIGHT band around the base roughness. Left raw,
        # its 0-1 output would Lighten-max the whole surface toward matte and
        # flatten a glossy metal (the v2 blowout, in bus form). The Color 1 /
        # Color 2 stops become the roughness min/max: base-0.06 .. base+0.08, i.e.
        # subtle broad variation only. (Band widens in a later phase, MDD sec 4.2.)
        lo = clamp01(base_roughness - 0.06)
        hi = clamp01(base_roughness + 0.08)
        set_display(n, ["color 1", "color1", "color a"], (lo, lo, lo), ptype=PT_COLOR)
        set_display(n, ["color 2", "color2", "color b"], (hi, hi, hi), ptype=PT_COLOR)
        # AB05: map to the PART, not the whole model.
        set_center_on_part(n)
    return n


def make_occlusion_roughness_node(graph, base_roughness):
    """Create an Occlusion node as a ROUGHNESS-bus source (crevice grime -> rougher
    in cavities, base roughness on exposed faces). Returns the node (not wired);
    None if unavailable. Occluded/unoccluded colour param names vary by build;
    best-effort -- if they aren't set it degrades to the node's defaults."""
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (roughness/grime source)")
    if n is not None:
        # Grime roughens the cavities; exposed faces keep the base roughness so
        # the metal doesn't go uniformly matte (Lighten-max keeps the higher one).
        grimy = clamp01(base_roughness + 0.35)
        exposed = clamp01(base_roughness)
        set_display(n, ["occluded"], (grimy, grimy, grimy), ptype=PT_COLOR)
        set_display(n, ["unoccluded", "bright", "far", "exposed"],
                    (exposed, exposed, exposed), ptype=PT_COLOR)
    return n


def add_color_gradient(graph, base_node, base_color):
    """Colour bus (single driver, as AA02). Best-effort: if the gradient's stops
    aren't script-settable it is removed rather than left to drive a garbage
    (default magenta->cyan) colour into the base."""
    n = try_new_node(graph, "SHADER_TYPE_COLOR_GRADIENT", "Color Gradient (experimental)")
    if n is None:
        return False
    # Nudge toward tasteful, near-neutral tones close to the base material
    # color rather than leaving KeyShot's own default gradient stops (unknown,
    # possibly high-contrast) in place -- this was the leading suspect for
    # "wild" output. Best-effort: this node's UI is a draggable color bar,
    # which may not expose simple named color parameters the way other
    # nodes do. If no match is found, that's reported rather than assumed.
    light = tuple(clamp01(c * 1.25 + 0.05) for c in base_color)
    dark = tuple(clamp01(c * 0.6) for c in base_color)
    ok1 = set_display(n, ["color 1", "start color", "color a"], light, ptype=PT_COLOR)
    ok2 = set_display(n, ["color 2", "end color", "color b"], dark, ptype=PT_COLOR)
    if not (ok1 or ok2):
        # KeyShot's Color Gradient is a draggable colour bar with no named
        # colour-stop params, so we can't set it from script -- it keeps its
        # default (magenta->cyan) stops. Do NOT wire that into the base colour:
        # that is the bright-magenta node seen driving the metal in the graph
        # dump, i.e. the "wild colour" bug. Leave the node unwired (harmless)
        # and keep the base colour intact.
        print("  [warn] Color Gradient stops aren't script-settable on this build -- "
              "removing it so it can't drive a garbage (magenta) colour or clutter the graph")
        try:
            graph.removeNode(n)
        except Exception:
            pass
        return False
    return wire_scalar_driver(graph, n, base_node,
                              ["color", "diffuse", "tint", "reflectance"], "color")


# --------------------------------------------------------------------------
# Post-build wire audit (MDD-4B7A9F sec 7) -- optional/defensive
# --------------------------------------------------------------------------

def wire_audit(base_node, label="base"):
    """Walk the base node's inputs after building and print a one-line manifest
    of which wires actually landed, so silent edge failures (the historical
    bump_height bug) are visible. Fully defensive: if the getInputEdge API
    isn't available on this build it just says so and returns."""
    print("--- wire audit ({0} inputs) ---".format(label))
    try:
        params = base_node.getParameters()
    except Exception as e:
        print("  [info] wire audit unavailable ({0})".format(e))
        return
    landed = []
    saw_api = False
    for p in params:
        try:
            edge = base_node.getInputEdge(p.getName())
            saw_api = True
        except Exception:
            edge = None
        if edge:
            landed.append(p.getDisplayName())
    if not saw_api:
        print("  [info] getInputEdge not supported here -- skipping manifest")
        return
    if landed:
        print("  wired inputs: {0}".format(", ".join(landed)))
    else:
        print("  [info] no wired inputs detected on base node")


# --------------------------------------------------------------------------
# Sample -> validate -> compile pipeline (MDD-4B7A9F sec 3)
# --------------------------------------------------------------------------

def sample_spec(opts):
    """Sampler: turn a flat options dict (from the dialog or DEFAULT_OPTIONS)
    into a MaterialSpec dict. Applies the seed and randomize logic here so the
    spec captures the concrete feature set that will be built. Also resolves the
    Finish preset (change 2) and draws the per-build placement seed (change 3)
    into the spec. JSON-serialisable (plain dict/list/str/float/bool/None -- no
    dataclasses)."""
    material_type = opts.get("material_type", DEFAULT_OPTIONS["material_type"])
    wear_level = opts.get("wear_level", DEFAULT_OPTIONS["wear_level"])
    finish_name = opts.get("finish", DEFAULT_OPTIONS["finish"])
    wear_multiplier = float(opts.get("wear_multiplier", 1.0))

    seed = _apply_seed(opts)
    # Placement seed (change 3): derived from the feature seed when one was given
    # (reproducible), else a fresh random int -- captured below so ANY build can
    # be reproduced from the emitted spec.
    placement_seed = derive_placement_seed(seed)

    features = {k: bool(opts.get(k, False)) for k in FEATURE_KEYS}
    randomized = bool(opts.get("randomize_features"))
    if randomized:
        features = randomize_feature_flags()

    masks = {k: bool(opts.get(k, False)) for k in MASK_KEYS}

    mat = MATERIAL_BY_NAME.get(material_type, MATERIAL_BY_NAME[DEFAULT_OPTIONS["material_type"]])
    # Index-based unpack (AB04): rows are now 5- OR 6-element. Never destructure a
    # fixed arity. `extra` is COPIED so validate/build mutating it (e.g. recording
    # the chosen anisotropy angle) can NEVER mutate the module-level MATERIALS row.
    shader_attr = mat[1]
    base_color = mat[2]
    base_roughness = mat[3]
    extra = dict(material_extra(mat))
    family = material_family(extra)

    fp = FINISH_PRESETS.get(finish_name, FINISH_PRESETS[DEFAULT_OPTIONS["finish"]])

    # AB05: resolve the name filter once (needed to scope part measurement) and the
    # characteristic part size (entered > measured > default). part_size drives all
    # part-relative texture scales; captured into spec['scale'] for reproducibility.
    name_filter = resolve_filter(opts.get("name_filter"))
    part_size, size_source = resolve_part_size(opts, name_filter)

    name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level, finish_name)

    spec = {
        "meta": {
            "name": name,
            "name_prefix": opts.get("name_prefix", ""),
            "generator_rev": GENERATOR_REV,
            "seed": seed,
            "placement_seed": placement_seed,
            "randomized": randomized,
            "material_type": material_type,
            "wear_level": wear_level,
            "finish": finish_name,
            # Short family echo for reproducibility / at-a-glance in the emitted spec.
            "family": family,
        },
        "base": {
            "shader": shader_attr,
            "color": [base_color[0], base_color[1], base_color[2]],
            "roughness": base_roughness,
            # AB04: family + family shader params (opaque rows carry {}).
            "extra": extra,
        },
        "wear": {
            "level": wear_level,
            "multiplier": wear_multiplier,
            "effective": WEAR_PRESETS.get(wear_level, 1.0) * wear_multiplier,
        },
        "finish": {
            "name": finish_name,
            "dir_noise": fp[0],
            "noise": fp[1],
            "levels": fp[2],
            "scratch_bump_height": fp[3],
        },
        "features": features,
        "masks": masks,
        # AB05: part-size + the resolved part-relative texture scales. `resolved`
        # values are part_size * SCALE_FRACTIONS, in mm -- captured so the emitted
        # spec fully reproduces the scaling. build_material recomputes from
        # part_size_mm (robust if this block is edited) but honours these too.
        "scale": {
            "part_size_mm": part_size,
            "source": size_source,
            "fractions": dict(SCALE_FRACTIONS),
            "resolved": {
                "fine_noise": part_size * SCALE_FRACTIONS["fine_noise"],
                "scratches": part_size * SCALE_FRACTIONS["scratch_scale"],
                "fractal": part_size * SCALE_FRACTIONS["fractal"],
                "cellular": part_size * SCALE_FRACTIONS["cellular"],
                "spots": part_size * SCALE_FRACTIONS["spots_scale"],
            },
        },
        "application": {
            "name_filter": name_filter,
        },
    }
    return spec


def validate_family_extra(extra):
    """Clamp/sanity-check the numeric family params in an `extra` dict, in place
    (AB04). Every param is optional and defensively coerced; an opaque row ({}) or
    an unknown family passes through untouched. Ranges: anisotropy [0,1], brush
    angle wrapped into [0,360) (None left as-is -- chosen per-build later), IOR
    ~[1.0,3.0], frost [0,1], film thickness [1,2000] nm, film IOR ~[1.0,3.0]."""
    if not isinstance(extra, dict):
        return {}
    family = material_family(extra)
    if family == "metal_aniso":
        extra["anisotropy"] = clamp01(as_float(extra.get("anisotropy"), 0.5))
        ang = extra.get("aniso_angle")
        if ang is not None:
            extra["aniso_angle"] = as_float(ang, 0.0) % 360.0
    elif family == "dielectric":
        extra["ior"] = clampf(as_float(extra.get("ior"), 1.51), 1.0, 3.0)
        extra["frost"] = clamp01(as_float(extra.get("frost"), 0.0))
    elif family == "thinfilm":
        extra["film_thickness"] = clampf(as_float(extra.get("film_thickness"), 500.0), 1.0, 2000.0)
        extra["film_ior"] = clampf(as_float(extra.get("film_ior"), 1.4), 1.0, 3.0)
    return extra


def validate_spec(spec):
    """Validator: sanity-check + clamp the spec and derive the loud-layer
    damping context. Deliberately does NOT cap loud layers in manual mode --
    AA02 only caps in randomize mode; manual mode may enable all four and relies
    on the 1/sqrt(n) damping (computed here) to keep total surface energy bounded
    (MDD-4B7A9F sec 5.5 generalises this to per-bus budgets; kept as-is for
    Phase 1 to avoid regression)."""
    features = spec.setdefault("features", {})
    for k in FEATURE_KEYS:
        features.setdefault(k, False)

    masks = spec.setdefault("masks", {})
    for k in MASK_KEYS:
        masks.setdefault(k, False)

    base = spec.setdefault("base", {})
    color = base.get("color", [0.5, 0.5, 0.5])
    base["color"] = [clamp01(color[0]), clamp01(color[1]), clamp01(color[2])]
    base["roughness"] = clamp01(base.get("roughness", 0.3))
    # AB04: clamp any numeric family params in `extra` (defensive -- optional +
    # coerced; unknown families pass through untouched). Kept on the spec so the
    # emitted spec is reproducible.
    base["extra"] = validate_family_extra(base.get("extra", {}))

    # AB05: sanity-check the scale block so a bad/absent part size can never break
    # the build (coerced to a positive float; non-positive -> default). Kept on the
    # spec so the emitted spec stays honest.
    scale = spec.setdefault("scale", {})
    psize = as_float(scale.get("part_size_mm"), DEFAULT_PART_SIZE_MM)
    if psize <= 0.0:
        psize = DEFAULT_PART_SIZE_MM
    scale["part_size_mm"] = psize
    scale.setdefault("source", "default")

    # Finish (change 2): clamp dir/noise to [0,1], levels to an int in [1,5],
    # and the scratch bump BASELINE to a valid negative groove (magnitude [0,1]).
    finish = spec.setdefault("finish", {})
    finish["dir_noise"] = clamp01(finish.get("dir_noise", 0.5))
    finish["noise"] = clamp01(finish.get("noise", 0.1))
    try:
        levels = int(finish.get("levels", 2))
    except (ValueError, TypeError):
        levels = 2
    finish["levels"] = max(1, min(5, levels))
    try:
        sbh = float(finish.get("scratch_bump_height", -0.012))
    except (ValueError, TypeError):
        sbh = -0.012
    finish["scratch_bump_height"] = -clamp01(abs(sbh))

    active_loud = sum(1 for k in LOUD_BUMP_FEATURES if features.get(k))
    spec["derived"] = {
        "active_loud_count": active_loud,
        "damping": 1.0 / math.sqrt(max(1, active_loud)),
    }
    return spec


def emit_spec(spec):
    """Echo the spec to the console for reproducibility (MDD-4B7A9F sec 3.2):
    any future rev can rebuild the exact material from this dict. Prefer JSON
    (ASCII, re-loadable); fall back to repr if json is unavailable."""
    try:
        print("SPEC {0}".format(json.dumps(spec, sort_keys=True)))
    except Exception:
        print("SPEC {0}".format(repr(spec)))


# --------------------------------------------------------------------------
# Compiler: build_material(spec)
# --------------------------------------------------------------------------

def build_material(spec):
    """Compiler: read a MaterialSpec and wire the base shader + three buses.
    Mutates spec['meta']['name'] if a name collision forces a retry, so the
    emitted spec reflects the material that was actually created."""
    meta = spec["meta"]
    base = spec["base"]
    wear = spec["wear"]
    finish = spec.get("finish", {})
    features = spec["features"]
    masks = spec["masks"]
    derived = spec.get("derived", {})

    material_type = meta["material_type"]
    wear_level = meta["wear_level"]
    finish_name = meta.get("finish", DEFAULT_OPTIONS["finish"])
    wear_mult = wear["effective"]
    base_color = (base["color"][0], base["color"][1], base["color"][2])
    base_roughness = base["roughness"]

    # AB05: resolve the part-relative texture scales (mm). Recomputed here from the
    # spec's part_size_mm + SCALE_FRACTIONS so it is robust even if spec['scale']
    # was hand-edited; defaults are used if the block is missing entirely.
    scale_info = spec.get("scale", {})
    part_size = as_float(scale_info.get("part_size_mm"), DEFAULT_PART_SIZE_MM)
    if part_size <= 0.0:
        part_size = DEFAULT_PART_SIZE_MM
    size_source = scale_info.get("source", "default")
    tex_scales = {
        "fine_noise": part_size * SCALE_FRACTIONS["fine_noise"],
        "scratches": part_size * SCALE_FRACTIONS["scratch_scale"],
        "fractal": part_size * SCALE_FRACTIONS["fractal"],
        "cellular": part_size * SCALE_FRACTIONS["cellular"],
        "spots": part_size * SCALE_FRACTIONS["spots_scale"],
    }

    # AB04: family + its shader params (opaque rows carry {} -> family "opaque").
    extra = base.get("extra", {}) or {}
    family = material_family(extra)

    shader_type = resolve_shader(base["shader"], family)
    if shader_type is None:
        raise RuntimeError("No usable base shader for '{0}'".format(material_type))

    seed = meta.get("seed")
    if seed is not None:
        print("  Seeded feature RNG with {0} (reproducible in randomize mode)".format(repr(seed)))

    # Placement RNG (change 3): a dedicated Random seeded off the captured
    # placement_seed, so per-material texture placement is reproducible. If the
    # spec somehow lacks one, draw + capture it now so the emitted spec stays
    # honest and the build is still reproducible.
    placement_seed = meta.get("placement_seed")
    if placement_seed is None:
        placement_seed = random.Random().randint(0, 2147483647)
        meta["placement_seed"] = placement_seed
    placement_rng = random.Random(placement_seed)

    name = meta["name"]

    print("lux.isHeadless() = {0}".format(lux.isHeadless()))
    print("Building '{0}' | type={1} | wear={2} (x{3:.2f}) | finish={4}".format(
        name, material_type, wear_level, wear_mult, finish_name))
    print("  Finish: {0} -- dir_noise={1}, noise={2}, levels={3}, scratch-bump baseline={4}".format(
        finish_name, finish.get("dir_noise"), finish.get("noise"),
        finish.get("levels"), finish.get("scratch_bump_height")))
    print("  Placement seed: {0} (per-build texture placement, reproducible)".format(placement_seed))
    print("  Family: {0}".format(family))
    print("  Scale: part {0} mm ({1}) -> scratches {2}, fine {3}, fractal {4}, "
          "cellular {5}, spots {6} mm (Center On: Part)".format(
              part_size, size_source, tex_scales["scratches"], tex_scales["fine_noise"],
              tex_scales["fractal"], tex_scales["cellular"], tex_scales["spots"]))

    # --- PER-FAMILY WEAR-LAYER GATING (AB04) --------------------------------
    # Intersect the user's chosen features with the family's allowed set BEFORE
    # building any bus, so a family never gets a nonsensical layer (grime/pitting/
    # cellular-corrosion on clear glass, etc.). opaque/metal_aniso allow all, so
    # this is a no-op for them. Each dropped layer is logged. `features` is a
    # reference into the spec, so the emitted spec reflects what was actually
    # built; the sampled intent is still visible in meta/randomized.
    allowed = FAMILY_ALLOWED_LAYERS.get(family, set(FEATURE_KEYS))
    if family != "opaque":
        for k in FEATURE_KEYS:
            if features.get(k) and k not in allowed:
                print("  [info] {0} skipped -- not applicable to {1}".format(FEATURE_LABELS[k], family))
                features[k] = False

    active = [FEATURE_LABELS[k] for k, v in features.items() if v]
    active_str = ", ".join(active) if active else "(none)"
    print("Features: {0}".format(active_str))
    masks_on = [m for m, on in [("scratches->edges", masks.get("mask_scratches_to_edges")),
                                ("spots->cavities", masks.get("mask_spots_to_cavities"))] if on]
    if masks_on:
        print("Masking: {0}".format(", ".join(masks_on)))

    # Damp each loud bump layer's amplitude by how many are stacked, so total
    # surface energy stays roughly bounded regardless of how many ended up
    # active -- this is what actually stops combinations from compounding into
    # chaotic noise. RECOMPUTED here (AB04) from the POST-GATE features, so a
    # family that dropped loud layers (e.g. glass loses spots/cellular) isn't
    # over-damped by validate_spec's pre-gate count. spec['derived'] is updated
    # to keep the emitted spec honest.
    active_loud_count = sum(1 for k in LOUD_BUMP_FEATURES if features.get(k))
    damping = 1.0 / math.sqrt(max(1, active_loud_count))
    derived["active_loud_count"] = active_loud_count
    derived["damping"] = damping
    spec["derived"] = derived
    if active_loud_count > 1:
        print("  {0} loud bump layers active -- damping each by {1:.2f}x".format(active_loud_count, damping))

    for attempt in range(5):
        try:
            lux.createSceneMaterial(name)
            break
        except Exception as e:
            print("  [warn] couldn't create material '{0}': {1} -- trying a new random name".format(name, e))
            name = resolve_material_name(meta.get("name_prefix", ""), material_type, wear_level, finish_name)
    else:
        raise RuntimeError("Couldn't create a scene material after 5 attempts")
    meta["name"] = name  # keep the emitted spec honest about the final name

    graph = lux.getMaterialGraph(name)
    root = graph.getRoot()
    if DEBUG:
        dump_node(root, "Root")

    base_node = new_node(graph, shader_type, material_type)
    safe_edge(graph, source=base_node, target=root, param="surface", label="base -> root.surface")
    # "diffuse" is essential: KeyShot's Plastic material names its colour
    # channel "Diffuse", not "Color" -- without it, plastic bases silently kept
    # KeyShot's default colour instead of the one picked here. Metal uses
    # "Color"; both are covered by the keyword list.
    # Match by name only: the base Color is PARAMETER_TYPE 14 (a texture-able
    # colour input), not PT_COLOR (13, the plain colour-value type) -- filtering
    # by PT_COLOR missed it and the colour never applied. Names cover metal
    # ("Color") and plastic ("Diffuse").
    set_display(base_node, ["color", "diffuse", "tint", "reflectance", "base color"],
                base_color)
    # Static roughness value is the ultimate fallback for the roughness bus:
    # if every roughness wire fails, this value still applies. For frosted glass
    # this base roughness is deliberately high (~0.30) so it reads matte even if
    # the refraction-roughness param below is absent.
    set_display(base_node, ["roughness"], base_roughness)

    # --- FAMILY BASE PARAMS (AB04) ------------------------------------------
    # Apply the non-opaque family's shader params (IOR/frost, anisotropy+angle,
    # film thickness/IOR) defensively AFTER colour+roughness. No-op for opaque.
    # Every set is best-effort; a missing param logs and the material still works.
    if family != "opaque":
        apply_family_params(graph, base_node, extra, placement_rng)

    # --- BUMP BUS: bump-domain layers combined into one bump input ----------
    # Masking is applied per-layer here: a masked layer gets a Curvature/
    # Occlusion mask mapped onto its bump-height before it joins the bump chain.
    # Placement randomisation (change 3) runs on each procedural texture node
    # right after it is configured -- for EVERY build, driven by placement_rng.
    bump_sources = []
    scratches_node = None  # captured so scratches can also drive the roughness bus
    if features["add_fine_noise"]:
        fine_node = add_fine_noise_bump(graph, tex_scales["fine_noise"])
        randomize_placement(fine_node, placement_rng, "fine_noise", tex_scales["fine_noise"])
        bump_sources.append(fine_node)
    if features["add_scratches"]:
        scratches_node = add_scratches_bump(graph, wear_mult, base_roughness, finish, damping,
                                            tex_scales["scratches"])
        randomize_placement(scratches_node, placement_rng, "scratches", tex_scales["scratches"])
        if masks.get("mask_scratches_to_edges"):
            mask_bump_layer(graph, scratches_node, add_curvature_mask(graph), "scratches->edges")
        bump_sources.append(scratches_node)
    if features["add_rounded_edges"]:
        # Rounded Edges is a geometry-based bump, not a tiling texture -- no
        # placement randomisation (nothing to de-repeat) and no Center On / Scale.
        bump_sources.append(add_rounded_edges_bump(graph, wear_mult, damping))
    if features["add_spots"]:
        sp = add_spots_bump(graph, wear_mult, damping, tex_scales["spots"])
        randomize_placement(sp, placement_rng, "spots", tex_scales["spots"])
        if masks.get("mask_spots_to_cavities"):
            sp = mask_bump_layer(graph, sp, add_occlusion_mask(graph), "spots->cavities")
        bump_sources.append(sp)
    if features["add_cellular"]:
        cell_node = add_cellular_bump(graph, wear_mult, damping, tex_scales["cellular"])
        randomize_placement(cell_node, placement_rng, "cellular", tex_scales["cellular"])
        bump_sources.append(cell_node)

    combined_bump = combine_bump_sources(graph, bump_sources)
    if combined_bump is not None:
        base_bump_slots = connection_param_names(base_node, PT_SHADERBUMP)
        if base_bump_slots:
            safe_edge(graph, source=combined_bump, target=base_node, param=base_bump_slots[0],
                      label="combined bump -> base.bump")
        else:
            print("  [warn] base material has no bump input")

    # --- ROUGHNESS BUS: multi-source, composited via Lighten ----------------
    # AA02 wired a single roughness driver ("first wins"): scratches took
    # priority (matte streaks are what make them read on glossy metal), else
    # fractal, else occlusion. The bus now composites ALL active sources into
    # the one roughness input via Color Composite / Lighten (per-pixel max --
    # the physically-right combiner for "wear only ever roughens"), and falls
    # back to the AA02 single-driver behaviour if the composite chain can't be
    # built. Scratches stay first in the list, so both the fallback and the
    # source-side-of-composite priority match AA02.
    rough_sources = []
    if scratches_node is not None:
        rough_sources.append(scratches_node)
    if features["add_fractal_roughness"]:
        fr = make_fractal_roughness_node(graph, base_roughness, tex_scales["fractal"])
        if fr is not None:
            # Fractal Noise is a tiling texture -- part-relative scale + Center On: Part.
            randomize_placement(fr, placement_rng, "fractal", tex_scales["fractal"])
            rough_sources.append(fr)
    if features["add_occlusion_roughness"]:
        oc = make_occlusion_roughness_node(graph, base_roughness)
        if oc is not None:
            # Occlusion has no tiling scale, but its bias_x/y/z DO offset the AO
            # sampling (confirmed in the AB02 dump) -- FIX 2 jitters those so even
            # the crevice-grime source varies per material instead of being global.
            randomize_placement(oc, placement_rng, "occlusion")
            rough_sources.append(oc)
    rough_mode = build_roughness_bus(graph, base_node, rough_sources)
    print("  Roughness bus: {0} source(s) -> mode '{1}'".format(len(rough_sources), rough_mode))

    # --- COLOUR BUS: base colour + optional gradient driver (single) --------
    if features["add_color_gradient"]:
        add_color_gradient(graph, base_node, base_color)

    # --- post-build wire audit (silent-edge-failure guard) ------------------
    wire_audit(base_node, "base")

    print("Built material graph: {0}".format(name))
    return graph, name


def _collect_descendants(root):
    """FIX 3 (AB03): recursively collect all descendant nodes of `root` via
    getChildren(). AB02 used root.find(''), which on the operator's scene
    returned ONLY non-geometry nodes (all 22 were cameras, kind=6) and never
    reached the geometry -- so 0 parts got the material. Walk the tree by hand
    instead. Fully defensive: any getChildren() failure just prunes that branch,
    and the caller falls back to root.find('') if getChildren isn't available at
    all. A visited-set (by id) guards against a pathological cyclic tree."""
    collected = []
    visited = set()
    stack = []
    try:
        first = root.getChildren()
    except Exception:
        first = None
    if first:
        stack.extend(first)
    while stack:
        node = stack.pop()
        marker = id(node)
        if marker in visited:
            continue
        visited.add(marker)
        collected.append(node)
        try:
            children = node.getChildren()
        except Exception:
            children = None
        if children:
            stack.extend(children)
    return collected


def _name_matches(node, name_filter):
    """Best-effort substring name match, so name filtering still works on the
    recursively-collected node list (the find() fallback filters on its own)."""
    try:
        nm = node.getName()
    except Exception:
        return False
    if not nm:
        return False
    return name_filter.lower() in nm.lower()


def apply_material_to_parts(name, name_filter=None):
    """Apply `name` across the scene. Deliberately does NOT pre-filter to
    isObject() -- KeyShot's own docs confirm Group nodes accept setMaterial()
    and cascade it to their children, so excluding Groups (as an earlier
    version of this function did) silently skipped entire assemblies. Instead
    every node is tried; only genuine failures (cameras, lights, etc.) are
    skipped, based on what setMaterial() itself reports.

    FIX 3 (AB03, CONFIRM-AT-RENDER -- LEAST CERTAIN of the three fixes, no scene
    to test on): reach geometry by walking the tree RECURSIVELY via getChildren()
    rather than root.find(''), which returned only cameras on the operator's
    scene. Prints a histogram of candidate node KINDS discovered BEFORE applying,
    so if 0 still apply the operator can see exactly what kinds exist."""
    root = lux.getSceneTree()

    # Prefer a recursive getChildren() walk; fall back to root.find('') if the
    # API isn't available on this build.
    try:
        can_walk = root.getChildren() is not None
    except Exception:
        can_walk = False

    if can_walk:
        candidates = _collect_descendants(root)
        used_recursive = True
        if name_filter:
            candidates = [n for n in candidates if _name_matches(n, name_filter)]
    else:
        print("  [info] getChildren() unavailable -- falling back to root.find('')")
        candidates = root.find(name=name_filter) if name_filter else root.find("")
        used_recursive = False

    # DEBUG: histogram of candidate KINDS BEFORE applying -- if 0 apply, this
    # tells us what kinds exist (e.g. {6: 17, <geo-kind>: N, ...}).
    if DEBUG:
        discovered = {}
        for node in candidates:
            try:
                kd = node.getKind()
            except Exception:
                kd = "?"
            discovered[kd] = discovered.get(kd, 0) + 1
        print("  candidate kinds: {0} ({1} node(s) via {2})".format(
            discovered, len(candidates),
            "recursive getChildren" if used_recursive else "root.find fallback"))

    applied, skipped = 0, 0
    kind_counts = {}
    for node in candidates:
        kind = None
        if DEBUG:
            try:
                kind = node.getKind()
            except Exception:
                kind = "?"
        try:
            ok = bool(node.setMaterial(name))
        except Exception as e:
            ok = False
            if DEBUG:
                print("  [warn] setMaterial failed (kind={0}): {1}".format(kind, e))
        if ok:
            applied += 1
            if DEBUG:
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
        else:
            skipped += 1
    suffix = " matching {0}".format(repr(name_filter)) if name_filter else ""
    print("Applied '{0}' to {1} node(s){2}, skipped {3}".format(name, applied, suffix, skipped))
    if DEBUG and applied:
        print("  applied to node kinds: {0}".format(kind_counts))
    if applied == 0 and DEBUG:
        print("  [info] nothing matched -- see the 'candidate kinds' histogram above; "
              "if it's all kind=6 (cameras) the geometry wasn't reached, so confirm a "
              "model is actually loaded in the scene")
    return applied


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled -- nothing built.")
    else:
        spec = validate_spec(sample_spec(options))
        graph, material_name = build_material(spec)
        emit_spec(spec)  # emitted after build so meta.name reflects the final name
        apply_material_to_parts(material_name, name_filter=spec["application"]["name_filter"])
