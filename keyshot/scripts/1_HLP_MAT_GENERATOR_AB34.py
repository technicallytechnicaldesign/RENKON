# -*- coding: utf-8 -*-
# AUTHOR claude-subagent
# REV AB34
#
# Procedural KeyShot material generator: finish presets, wear masks,
# label channels, scripted via lux API.
#
# CONSTRAINTS: ASCII only, no f-strings, no walrus operators.
# Single-file delivery via raw GitHub URL (no imports from local modules).
# Changelog: git log; process notes live in the private RENKON_LAB repo.

import lux
import random


# ===== CORE BLOCK v1 -- BYTE-IDENTICAL IN EVERY GENERATOR =====================
# Shared plumbing for every KeyShot generator in this repo: part measurement and
# scene-unit scaling, Center On, placement jitter, the bump and roughness buses,
# the curvature/occlusion masks, node and parameter helpers, and apply-to-
# geometry with read-back. Most of it is knowledge that cost a render session to
# learn, and all of it is generator-agnostic.
#
# The KeyShot machine has no git and downloads ONE file per run, so a shared
# module would mean hand-carrying two files and keeping them in sync by eye.
# Instead this block is DUPLICATED verbatim into each generator, and
# 0_VAL_LOAD_SAFETY compares the copies and FAILS if they differ. Drift is a
# build failure, not a thing to remember.
#
# EDIT IT IN ONE FILE, THEN COPY THE WHOLE BLOCK INTO THE OTHERS. Do not
# hand-merge, and do not let a generator 'improve' its own copy locally.
# ==============================================================================

# lux's PARAMETER_TYPE_* names vary between KeyShot builds, and a bare
# lux.PARAMETER_TYPE_X reference to a name this build lacks raises AttributeError
# -- which crashes the whole run (there is no PARAMETER_TYPE_SHADERCOLOR, for
# one). Resolve the few we use once, defensively: a missing type becomes None,
# and the helpers below treat None as "no type filter" / "skip this wiring"
# rather than crashing. Colour/texture inputs are PARAMETER_TYPE_COLOR (you
# connect a texture into a colour input); there is no separate shader-colour type.
PT_COLOR = getattr(lux, "PARAMETER_TYPE_COLOR", None)


PT_SHADERBUMP = getattr(lux, "PARAMETER_TYPE_SHADERBUMP", None)


DEBUG = True  # prints real parameters for each node as it's created


# --------------------------------------------------------------------------
# Image-label (emulated) constants (AB06)
# --------------------------------------------------------------------------
# True KeyShot Labels are NOT exposed to scripting, so the "label" here is an
# image-map texture node wired into the base material's own channels (bump, spec/
# roughness, and a masked colour overlay), surface/UV-mapped via Center On: Part +
# Scale. The image/texture-map node's lux SHADER_TYPE_* constant is UNPROBED on this
# build -- make_image_map resolves the FIRST that exists over this candidate list
# and DEBUG-dumps the created node so the render log reveals the real API. If NONE
# exist, labels are skipped and the plain material still builds.
# PARAMETER_TYPE_STRING -- the image/file-path parameter type. Named here rather
# than inlined so the intent is legible at the call site.
PTYPE_STRING = 9


# PROBED 2026-07-28: of the five candidates AB06 carried, only TEXTURE_MAP exists
# on this build (the other four are absent). The list stays a list so a different
# KeyShot version still has somewhere to fall through to, but the order now leads
# with the one that is actually real.
IMAGE_MAP_CANDIDATES = [
    "SHADER_TYPE_TEXTURE_MAP", "SHADER_TYPE_IMAGE_MAP", "SHADER_TYPE_IMAGE",
    "SHADER_TYPE_BITMAP", "SHADER_TYPE_TEXTURE",
]


# Candidate lux constants for a plain colour node (the composite's Background side
# in the colour overlay). UNPROBED -> tried in order; if none exist the overlay
# falls back to setting the Composite's Background colour VALUE directly.
COLOR_NODE_CANDIDATES = [
    "SHADER_TYPE_COLOR", "SHADER_TYPE_SOLID_COLOR", "SHADER_TYPE_COLOR_MAP",
    "SHADER_TYPE_COLORMAP", "SHADER_TYPE_CONSTANT_COLOR",
]


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
# Legacy absolute tiling scales, kept ONLY as the fallback inside
# randomize_placement when a caller passes no part-relative scale. Since AB05
# every caller does, so this is a safety net rather than a code path. Values are
# the originals from BASE, unchanged; they live here so the shared core does not
# reach into a material-specific table.
LEGACY_SCALE_BASE = {
    "fine_noise": 0.15,
    "scratches":  5.0,
    "fractal":    4.0,
    "cellular":   2.0,
}


# Part-relative tiling scales. Panel mm = extent * fraction, so 0.12 on a 270 mm
# part is a 32 mm scratch field and on a 10 mm cube a 1.2 mm one.
#
# TWO GROUPS, MEASURED SEPARATELY 2026-07-31, and the split is the point:
#   READ DIRECTLY (fine_noise, fractal, cellular) -- the bench range is 0.1 to
#     1 mm of panel on a 10 mm part, and these were already inside it.
#   MASKED THROUGH A CURVATURE (scratch_scale, spots_scale) -- the range is ten
#     times finer, 0.01 to 0.05 mm, because what reaches the composite is the
#     INTERSECTION of the pattern and the edge band. A pattern coarse enough to
#     miss the edges hands the composite pure black, which is what 0.12 and 0.06
#     were doing on every masked build since AB13.
SCALE_FRACTIONS = {
    "scratch_scale": 0.004,
    "fine_noise":    0.02,
    "fractal":       0.15,
    "cellular":      0.08,
    "spots_scale":   0.004,
}


# AB08: the sentinel that means "no image for this channel". The dialog cannot be
# handed an empty default string (AB07 raised inside getInputDialog when it was),
# so an unused label channel carries this word and normalise_label_path() maps it
# back to "" before anything reads it.
NO_LABEL = "none"


def normalise_label_path(value):
    """Map the no-image sentinel, a dash, or blank input to "" (channel skipped).
    Anything else is returned stripped, so a pasted path with stray whitespace
    still resolves."""
    if value is None:
        return ""
    text = str(value).strip()
    # AB09: Windows "Copy as path" wraps the path in double quotes and they came
    # through verbatim, so KeyShot was handed >"C:/x.png"< and could not open it.
    # Strip matching quotes from both ends (repeatedly -- a path can arrive quoted
    # twice via a round trip through a dialog field).
    while len(text) >= 2 and text[0] == text[-1] and text[0] in ("\"", "'"):
        text = text[1:-1].strip()
    if text.lower() in (NO_LABEL, "-", ""):
        return ""
    return text


# Texture Scale panel: MILLIMETRES. API takes metres, panel shows mm.
# MEASURED 2026-07-31: wrote 1.0, panel read 1000. Factor = 1000.0.
# Same value as RADIUS_DISPLAY_FACTOR (MEASURED 2026-08-03).
# Two constants kept separate: each is one observation, not a law.
# Use mm_to_texture_scale(), not raw multiplication.
TEXTURE_DISPLAY_FACTOR = 1000.0
TEXTURE_DISPLAY_FACTOR_LIVE = [TEXTURE_DISPLAY_FACTOR]

# Kept as the reciprocal for the scale_factor dialog field, whose meaning has not
# changed: written = extent * fraction * TEXTURE_SCALE_FACTOR.
TEXTURE_SCALE_FACTOR = 1.0 / TEXTURE_DISPLAY_FACTOR

# The smallest scale_factor the dialog itself declares legal. THE DIALOG DOES NOT
# ENFORCE IT. On 2026-08-04 both mode 7 runs were handed back 0.0 for this field,
# so `scale = extent * fraction * 0.0` gave the grunge Scratches node a Scale of
# exactly ZERO in every frame judged that day. Nothing warned: the log printed
# `texture scale 0.0 (panel should read 0.0)` as an ordinary number, and the
# panel-should-read arithmetic divides by the same factor, so it degenerated too
# and agreed with itself. A range the tool declares and does not enforce is a
# range this code has to enforce.
TEXTURE_SCALE_MIN = 0.0000001


def resolve_scale_factor(raw, label="scale_factor"):
    """Coerce a dialog scale_factor into something that can produce a texture.

    Returns the factor to use. Loud whenever it had to change the number: the
    value substituted here is what the run's entire scale arithmetic is built on,
    so it must not arrive as a surprise in a frame hours later."""
    factor = as_float(raw, TEXTURE_SCALE_FACTOR)
    if factor >= TEXTURE_SCALE_MIN:
        return factor
    print("  [warn] {0} came back as {1}, below the dialog's own declared "
          "minimum of {2}. The dialog does not enforce its range, and a factor "
          "of zero gives every texture a Scale of zero while printing like a "
          "normal number. This is what confounded both mode 7 frames on "
          "2026-08-04. USING {3} instead.".format(
              label, factor, TEXTURE_SCALE_MIN, TEXTURE_SCALE_FACTOR))
    return TEXTURE_SCALE_FACTOR


def texture_scale_or_refuse(extent, fraction, factor, label):
    """The texture Scale to write, or None meaning DO NOT BUILD THIS NODE.

    The factor is guarded by `resolve_scale_factor` before it gets here, so this
    catches the other two routes to zero: an unmeasured part (extent 0) and a
    zeroed fraction. A texture at Scale 0 is not a subtle texture, it is an
    absent one, and it renders as a plausible frame that means nothing. Refusing
    to build the node is the point: a missing node is visible in the log and in
    the graph, a Scale of zero is visible in neither."""
    scale = (as_float(extent, 0.0) * as_float(fraction, 0.0)
             * as_float(factor, 0.0))
    if scale > 0.0:
        return scale
    print("  [REFUSED] {0}: computed texture Scale is {1} (extent {2} x fraction "
          "{3} x factor {4}). A Scale of zero or less is not a texture, so this "
          "node is NOT being built rather than being built blind. Fix whichever "
          "of the three is zero.".format(label, scale, extent, fraction, factor))
    return None


def mm_to_texture_scale(mm):
    """Millimetres a texture feature should measure -> the value to write.

    The panel reads millimetres; the parameter takes mm / 1000. Bench-measured
    good ranges on a 10 mm cube, which are what the wear fractions now target:
      raw pattern, read directly     0.1 -- 1 mm   (gone by about 5 mm)
      masked through a curvature     0.01 -- 0.05 mm
    The masked route needs a finer pattern because its coverage is the
    INTERSECTION of the scratch lines and the edge band, so a coarse pattern
    simply misses the edges and the mask comes back black."""
    factor = TEXTURE_DISPLAY_FACTOR_LIVE[0] or TEXTURE_DISPLAY_FACTOR
    return float(mm) / factor


def texture_scale_to_mm(value):
    """The inverse, for printing what the panel should read."""
    factor = TEXTURE_DISPLAY_FACTOR_LIVE[0] or TEXTURE_DISPLAY_FACTOR
    return float(value) * factor


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


# Candidate lux bounding-box methods, tried in order per geometry node. Only
# getBoundingBox is documented as confirmed elsewhere in the repo (getSceneInfo
# unit-scale + getBoundingBox(world=True)); getWorldBounds/getBounds are plausible
# node-level alternates. All are getattr-guarded -> absence is non-fatal.
# PROBED 2026-07-28: only getBoundingBox() exists on SceneNode. The other two
# were guesses and never resolved. Kept in the list purely so a different build
# still has somewhere to fall through to.
BBOX_METHODS = ["getBoundingBox", "getWorldBounds", "getBounds"]


# getBoundingBox() returns luxmath.Vectors in SCENE units, and the scene unit is
# NOT mm. AB06 labelled the raw number "mm" and fed it straight into the scale
# fractions. AB10: there is no scene-unit constant to have, so there is none
# here. Any apparent mm-per-unit figure for a scene is an import-scale artefact,
# not a unit of length, and no constant can know it (RNK-0255 struck the old 74.6). Texture Scale
# is in SCENE units, so the fractions below are applied straight to the MEASURED
# extent and nothing is converted, which is correct at any import scale. AB05
# through AB09 multiplied a millimetre figure into a scene-unit parameter, which
# is why every render so far showed textures far larger than the part.
#
# DEFAULT_PART_EXTENT is only reached when no bounding box can be read at all, in
# which case the scale is a guess and the console says so.
DEFAULT_PART_EXTENT = 1.0


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
    which method (if any) succeeded so a future rev can lock the API name.

    REFUSES to measure with no name_filter (RNK-0298). The dialog's own default
    is the ALL sentinel, which resolve_filter turns into None, and an unfiltered
    walk includes every Group/assembly node the scene has; taking max() extent
    across all of them measured 301,814,039 scene units for a part entered as
    220 mm, a factor of 1976 off -- the walk was finding the top of the tree,
    not the part. Refusing routes the caller to the entered-mm fallback instead,
    which is the existing, already-warned path."""
    if not name_filter:
        print("  [warn] part measure: no name filter set -- an unfiltered walk "
              "measures the largest node in the scene, almost always a "
              "Group/assembly and not the part (RNK-0298). Refusing to guess; "
              "type the part's name into 'Apply to parts matching' to measure "
              "it.")
        return None
    try:
        root = lux.getSceneTree()
    except Exception as e:
        print("  [info] part measure: getSceneTree() unavailable ({0})".format(e))
        return None
    try:
        nodes = _collect_descendants(root)
    except Exception:
        nodes = []
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
    print("  [info] part measure: max extent {0} scene units via {1}()".format(
        best, method_used))
    return best


def check_performance_mode():
    """Refuse to let a run be judged while Performance Mode is on.

    MEASURED 2026-08-03, the expensive way. Mode 1 of the mask viewer came back
    BLACK on the 220 mm discharge body at 1.5 mm -- the exact scene and radius
    that had rendered a crisp mask on every edge four days earlier. Two separate
    diagnoses were built on that black frame (the Cutoff default, then the
    radius) before the operator noticed that PERFORMANCE MODE had been toggled
    on. Turning it off brought the edges straight back.

    Performance Mode drops most of the material graph, including exactly the
    procedural nodes every mask in this repo is built from. So a curvature mask
    reads black, an occlusion mask reads black, and the console reports a
    perfectly healthy build the whole time -- every edge ACCEPTED, every write
    read back, nothing to warn about. It is the ideal shape for a wrong
    diagnosis: the failure looks exactly like the failures this workstream has
    genuinely had, and none of the instruments can see it.

    Hence a check rather than a note. `lux.isPerformanceModeEnabled` is on the
    real API surface. This does NOT turn it off: that is the operator's viewport
    and their call. It makes the state impossible to miss instead, at the top of
    the run and again at the end, because the log is what gets pasted back and
    read hours later.

    Returns True if performance mode is ON (i.e. the run is not judgeable)."""
    probe = getattr(lux, "isPerformanceModeEnabled", None)
    if probe is None:
        print("[info] this build has no isPerformanceModeEnabled -- cannot "
              "check Performance Mode. If a mask reads black on geometry that "
              "obviously has edges, check the toggle by hand FIRST.")
        return False
    try:
        on = bool(probe())
    except Exception as e:
        print("[info] could not read Performance Mode ({0})".format(e))
        return False
    if not on:
        return False
    print("")
    print("!" * 68)
    print("!!  PERFORMANCE MODE IS ON. NOTHING BELOW CAN BE JUDGED.")
    print("!!")
    print("!!  It drops most of the material graph, including the procedural")
    print("!!  nodes every mask here is built from. Curvature and occlusion")
    print("!!  will read BLACK on geometry that is full of edges, and every")
    print("!!  console line will look healthy: edges ACCEPTED, writes read")
    print("!!  back, no warnings. It cost two wrong diagnoses on 2026-08-03.")
    print("!!")
    print("!!  Turn it off in the viewport toolbar and run this again. Or, in")
    print("!!  this console:  import lux; lux.enablePerformanceMode(False)")
    print("!" * 68)
    print("")
    return True


def resolve_part_size(opts, name_filter):
    """Resolve the characteristic part extent IN SCENE UNITS, which is the space
    texture Scale parameters live in. Priority:
      1. Measured bounding box (getBoundingBox, confirmed working on 13.2).
      2. The entered Part size, read as a scene-unit figure, if nothing measures.
      3. DEFAULT_PART_EXTENT, loudly.
    When a measurement exists the entered mm value is REPORTING ONLY: it names
    this scene's unit in the log and never scales anything.
    Returns (extent_scene float, source str, units_to_mm float or None)."""
    entered_mm = as_float(opts.get("part_size_mm"), 0.0)
    measured = measure_part_size(name_filter)

    if measured is not None and measured > 0.0:
        units_to_mm = None
        if entered_mm and entered_mm > 0.0:
            units_to_mm = entered_mm / measured
            print("  [info] part extent {0} scene units (measured) = {1} mm as "
                  "entered, so this scene's unit is {2} mm. The mm figure is for "
                  "the log only -- texture scale uses the scene units.".format(
                      measured, entered_mm, "{0:.4g}".format(units_to_mm)))
        else:
            print("  [info] part extent {0} scene units (measured). Real size "
                  "unknown -- enter the Part size in mm and the log will name "
                  "this scene's unit; it does not change texture scale.".format(
                      measured))
        return measured, "measured", units_to_mm

    if entered_mm and entered_mm > 0.0:
        print("  [warn] no bounding box could be read, so the entered Part size "
              "{0} is being used AS A SCENE-UNIT figure, not as millimetres. If "
              "the scene panel reports a different extent, enter that "
              "number.".format(entered_mm))
        return entered_mm, "entered-as-scene-units", None

    print("  [warn] part extent unknown -- nothing measured and nothing entered. "
          "Falling back to {0} scene unit(s); texture scale will almost certainly "
          "be wrong. Enter the extent the scene panel reports.".format(
              DEFAULT_PART_EXTENT))
    return DEFAULT_PART_EXTENT, "default", None


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
    # Pass 3 (AA07/AB17, 2026-07-31) -- THE TYPE FILTER IS A HINT, NOT A GATE.
    # The label probe asked for a BRDF's colour with ptype=PARAMETER_TYPE_COLOR
    # and got nothing, because a BRDF's `color` is type 14 while the constant is
    # 13: colour on a texture node and colour on a shader are different types.
    # The caller was told "no parameter matching 'color'" about a node whose dump
    # plainly listed one, and the write silently did not happen. So a filtered
    # miss now retries unfiltered and SAYS the type it actually found, which
    # turns a silent no-op into a line naming the real type.
    if ptype is not None:
        p = find_param(node, keywords, None)
        if p is not None:
            label = keywords if isinstance(keywords, str) else "/".join(keywords)
            try:
                print("  [info] '{0}' has type {1}, not the {2} asked for -- using "
                      "it anyway".format(label, p.getType(), ptype))
            except Exception:
                pass
            return p
    return None


def connection_param_names(node, ptype):
    if ptype is None:
        return []
    return [p.getName() for p in node.getParameters() if p.getType() == ptype]


def values_agree(got, want, tol=1e-6):
    """Did a read-back land on what we asked for? Tolerant about the shapes this
    API hands back: floats that round-trip imprecisely, colours as tuples or
    lists, ints that arrive as floats, bools as ints."""
    if got is None:
        return False
    if isinstance(want, bool) or isinstance(got, bool):
        try:
            return bool(got) == bool(want)
        except Exception:
            return False
    if isinstance(want, (tuple, list)):
        # A COLOUR COMES BACK WITH AN ALPHA. Measured 2026-08-03 at the bench:
        # every colour write in the label probe was reported DID NOT TAKE while
        # holding exactly the value asked for -- (0.85, 0.06, 0.06) read back as
        # (0.8500000238418579, 0.0599999986588954, 0.059999998658895, 1.0). The
        # values were right to float32; the LENGTH was different, because the API
        # returns RGBA for an RGB write, and this function required equal length.
        # So it cried wolf on the one channel the probe existed to judge, which
        # is the same class of error as setMaterial returning None and scoring
        # every success as a failure -- inverted, and therefore worse: it teaches
        # the operator to discount a warning that will one day be real.
        # A longer read-back is accepted only when the extra tail is opaque
        # alpha; anything else is still a genuine mismatch.
        try:
            n_got, n_want = len(got), len(want)
        except TypeError:
            return False
        if n_got < n_want:
            return False
        if n_got > n_want:
            for extra in list(got)[n_want:]:
                if not values_agree(extra, 1.0, tol):
                    return False
        for a, b in zip(got, want):
            if not values_agree(a, b, tol):
                return False
        return True
    try:
        a = float(got)
        b = float(want)
    except (TypeError, ValueError):
        return got == want
    return abs(a - b) <= max(tol, abs(b) * 1e-4)


def set_display(node, keywords, value, ptype=None):
    """Write a parameter AND CONFIRM IT LANDED.

    AA07/AB17: a setValue that does not raise is not a value that was accepted.
    KeyShot refuses an out-of-range value silently -- `thinness` is [1, 100] and
    was fed 0.55 and 0.15 for three revs, leaving both wear channels at the
    default while the console reported success. Same class as `setMaterial`
    returning None and every success being scored as a failure. So every write is
    read back, and a value that did not stick says so loudly with what the
    parameter actually holds. Silence here now means the write is real."""
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
    except Exception as e:
        print("  [warn] couldn't set '{0}'={1}: {2} (left at default)".format(label, repr(value), e))
        return False
    try:
        got = p.getValue()
    except Exception as e:
        print("  [warn] '{0}' set to {1} but could not be read back ({2}) -- "
              "UNVERIFIED".format(label, repr(value), e))
        return True
    if not values_agree(got, value):
        print("  [warn] '{0}' DID NOT TAKE: asked for {1}, parameter holds {2}. "
              "Out of range, or the wrong parameter.".format(
                  label, repr(value), repr(got)))
        return False
    return True


# --------------------------------------------------------------------------
# RNK-0257 -- safe_edge reporting
# --------------------------------------------------------------------------
# Prints param type + target node shader type by name, reads back edge where
# API allows, says "CALL OK, UNVERIFIED" where it cannot. Return contract
# unchanged: True = call did not raise (not "connection exists").
# Type-4 on BRDF works (probe M5 PASSED: curvature->metal.roughness verified).
# Type-4 on TEXTURE node does not (bump_height). Discriminator is target NODE,
# not param type.


def _build_param_type_names():
    """Reverse-map lux's PARAMETER_TYPE_* ints to their names. Built from
    whatever this build actually carries, so a KeyShot version with a different
    set of constants still prints the truth rather than a guessed table."""
    names = {}
    for attr in dir(lux):
        if not attr.startswith("PARAMETER_TYPE_"):
            continue
        try:
            value = getattr(lux, attr)
        except Exception:
            continue
        if isinstance(value, int):
            names.setdefault(value, attr[len("PARAMETER_TYPE_"):])
    return names


PARAM_TYPE_NAMES = _build_param_type_names()


# MEASURED ON THE REAL BUILD, 2026-08-04, off the mask viewer's own node dumps.
# Recorded because this repo has twice reasoned about a type from its number and
# been wrong. These are read, not derived:
#
#     1      BOOLEAN-ish   Radius In Pixels, Sync, Sample Same Material Only
#     2      INTEGER-ish   Samples, Opacity Map Mode
#     4      FLOAT         Radius, Cutoff, Roughness, Radius Map (pure)
#     13     COLOR         Positive/Zero/Negative Curvature -- a colour VALUE
#     14     COLORALPHA    Color, Opacity -- what a TEXTURE connects into
#     65537  SHADERSURFACE root.surface (pure)
#     65539  SHADERBUMP    Bump (pure)
#
# The high-bit types (65537, 65539) are the shader-domain connections; the low
# numbers are values. `pure` is orthogonal and marks a param that is not a
# freely writable input.
OBSERVED_PARAM_TYPES = "see the table above -- measured 2026-08-04, do not guess"


def _build_shader_type_names():
    """Same reverse map for SHADER_TYPE_*, so the target NODE can be named. M5
    settled that a type-4 parameter is drivable on a BRDF and not on a texture
    node, which makes the node the half of the question that decides it."""
    names = {}
    for attr in dir(lux):
        if not attr.startswith("SHADER_TYPE_"):
            continue
        try:
            value = getattr(lux, attr)
        except Exception:
            continue
        if isinstance(value, int):
            names.setdefault(value, attr[len("SHADER_TYPE_"):])
    return names


SHADER_TYPE_NAMES = _build_shader_type_names()


def lookup_type_name(table, key):
    """`table.get(key)`, but survive a key that cannot be hashed.

    MEASURED AT THE BENCH 2026-08-04, and it took the mask viewer down at load:
    `node.getType()` returns a **dict** on this build, not an int. `dict.get`
    raises `TypeError: unhashable type: 'dict'`, which is not caught by an
    `except Exception` around the *call* -- it happens after. AA17 assumed a
    node's type was an int because a PARAMETER's type is one (the dumps show 4,
    13, 14). Parameters and nodes do not answer `getType()` in the same shape,
    and assuming they did is the same class of mistake as applying one radius
    rule to two node types. Returns None when the key cannot be looked up."""
    try:
        return table.get(key)
    except TypeError:
        return None


# Keys worth trying inside a dict-shaped type. We know from the 2026-08-04
# crash that this build answers `getType()` with a dict; we do NOT know what is
# in it, and nobody has dumped one yet. So: USE a name key if there is one, and
# otherwise print the keys there actually are, which is how the next run finds
# out. Never assume a key exists -- that assumption is what produced the crash.
TYPE_NAME_KEYS = ("name", "type", "displayName", "display_name", "label", "title")


def describe_opaque(value):
    """A short, safe rendering of a type reported in a shape we have no constant
    for. Prints the SHAPE rather than swallowing it, so the next session
    inherits the real thing instead of another guess."""
    if isinstance(value, dict):
        for key in TYPE_NAME_KEYS:
            try:
                found = value.get(key)
            except Exception:
                found = None
            if isinstance(found, str) and found.strip():
                return found.strip()
        try:
            keys = sorted([str(k) for k in value.keys()])
        except Exception:
            keys = []
        return "dict keys {0}".format(keys) if keys else "dict"
    return "{0} ({1})".format(value, type(value).__name__)


def shader_type_name(node):
    """`PAINT` / `TEXTURE_MAP` / a description of whatever shape this build
    reports / `unknown`. Never raises: this is a diagnostic, and a diagnostic
    that can take the run down is worse than no diagnostic at all."""
    try:
        stype = node.getType()
    except Exception:
        return "unknown"
    if isinstance(stype, str):
        return stype
    name = lookup_type_name(SHADER_TYPE_NAMES, stype)
    if name is None:
        return describe_opaque(stype)
    return name


# The named types that hold a VALUE rather than accept a connection. Listed by
# NAME, never by int: the ints are not stable across builds, and this repo has
# already been burnt by a hardcoded one (a BRDF's colour reads 14 while
# PARAMETER_TYPE_COLOR is 13). A type absent from this build simply never
# resolves, so the set is always a subset of what really exists here.
#
# NOTE: this is NOT a "cannot be connected" list. M5 proved a type-4 target on a
# BRDF accepts an edge. It is the list of types worth SAYING OUT LOUD, because
# they are the ones where the answer depends on the node.
SCALAR_VALUE_TYPE_NAMES = (
    "BOOLEAN", "DOUBLE", "DOUBLE3", "FLOAT", "FLOAT2", "FLOAT3", "FLOATARRAY",
    "INTEGER", "INTEGERLIST", "STRING", "STRINGLIST",
)


def param_type_name(ptype):
    """`4 (FLOAT)`, or a description of whatever shape this build reports. An
    unnamed type is NOT a complaint: the real connection inputs on this build
    read as a type lux has no PARAMETER_TYPE_* constant for.

    Guarded the same way as the node lookup after the 2026-08-04 crash. A
    parameter type has always read as an int here, but "has always" is exactly
    what was said about node types the day before they turned out to be dicts."""
    if ptype is None:
        return "unknown"
    name = lookup_type_name(PARAM_TYPE_NAMES, ptype)
    if name is None:
        if isinstance(ptype, int):
            return "{0} (unnamed on this build)".format(ptype)
        return describe_opaque(ptype)
    return "{0} ({1})".format(ptype, name)


def is_scalar_value_type(ptype):
    """True only when this build NAMES the type and the name is a value type."""
    return lookup_type_name(PARAM_TYPE_NAMES, ptype) in SCALAR_VALUE_TYPE_NAMES


def describe_target_param(node, param_name):
    """(type int, is-pure, printable) for a named parameter on a node. Every
    lookup is defensive: a node that cannot be asked reports as unknown rather
    than taking the build down over a diagnostic."""
    ptype = None
    pure = None
    try:
        for p in node.getParameters():
            if p.getName() == param_name:
                ptype = p.getType()
                try:
                    pure = p.isPure()
                except Exception:
                    pure = None
                break
    except Exception:
        pass
    text = "{0}.{1}, param type {2}".format(
        shader_type_name(node), param_name, param_type_name(ptype))
    if pure:
        text = text + ", PURE"
    return ptype, pure, text


# None = not probed yet, False = this build exposes nothing, str = method name.
_EDGE_READBACK_API = [None]


def graph_edges(graph):
    """This build's edge list, or None when it exposes no way to ask. Probed
    ONCE and remembered, so a build without the API costs one lookup and then
    says UNVERIFIED for the rest of the run instead of inventing an answer."""
    probe = _EDGE_READBACK_API[0]
    if probe is False:
        return None
    if probe is None:
        for name in ("getEdges", "edges", "getConnections", "getAllEdges"):
            fn = getattr(graph, name, None)
            if fn is None:
                continue
            try:
                result = fn()
            except Exception:
                continue
            if result is None:
                continue
            try:
                result = list(result)
            except Exception:
                continue
            _EDGE_READBACK_API[0] = name
            print("[info] edge read-back IS available on this build: "
                  "graph.{0}() -- every wire below is checked, not assumed".format(name))
            return result
        _EDGE_READBACK_API[0] = False
        print("[info] no LIST-ALL-EDGES API on this build (tried getEdges, "
              "edges, getConnections, getAllEdges -- none exist, confirmed "
              "2026-08-04). Per-edge verification uses the getID round-trip "
              "instead (RNK-0299).")
        # MEASURED, NOT GUESSED. Four guessed names found nothing, and guessing a
        # fifth is how this repo lost four days to a radius. So the run now DUMPS
        # what the graph actually offers: the next bench log hands over the real
        # name, or proves there is none, and either way nobody has to guess again.
        try:
            offered = [n for n in dir(graph) if not n.startswith("_")]
        except Exception as e:
            offered = []
            print("       (could not list the graph's methods: {0})".format(e))
        if offered:
            print("       the graph object OFFERS: {0}".format(", ".join(sorted(offered))))
            print("       ^ for reference. The list-edges route is closed; "
                  "per-edge verification via getID is now the primary path.")
        return None
    try:
        return list(getattr(graph, probe)())
    except Exception:
        return None


def _node_identity(node):
    """Something that identifies THIS node, or None when nothing here does.

    AA17 fell back to `getType()`, which was wrong on its own terms: a type is
    shared by every node of that type, so two Curvature nodes compared EQUAL and
    `edge_readback` could have reported WIRED against the wrong one. A false
    WIRED is the exact failure this whole rev exists to remove, so the fallback
    is gone. `getType()` also turned out to return a dict at the bench, which
    would have made that false match even easier to hit.

    Returns None rather than guessing. The caller treats None as UNVERIFIED, so
    a build that cannot identify its nodes says so instead of inventing an
    answer."""
    fn = getattr(node, "getName", None)
    if fn is not None:
        try:
            value = fn()
        except Exception:
            value = None
        if isinstance(value, str) and value.strip():
            return ("name", value)
    # `id()` is only meaningful when both sides are the SAME wrapper object. It
    # is correct when it matches and merely unverified when it does not, which
    # is the safe direction.
    return ("object", id(node))


def _edge_target_of(edge):
    """(target node, param name) off an edge object whose shape is unprobed."""
    node = None
    for attr in ("getTarget", "target", "getDestination", "destination", "getTo", "to"):
        value = getattr(edge, attr, None)
        if value is None:
            continue
        try:
            node = value() if callable(value) else value
        except Exception:
            node = None
        if node is not None:
            break
    name = None
    for attr in ("getParam", "param", "getParameter", "parameter", "getParamName"):
        value = getattr(edge, attr, None)
        if value is None:
            continue
        try:
            resolved = value() if callable(value) else value
        except Exception:
            continue
        if resolved is None:
            continue
        if isinstance(resolved, str):
            name = resolved
        else:
            getter = getattr(resolved, "getName", None)
            try:
                name = getter() if getter is not None else None
            except Exception:
                name = None
        if name is not None:
            break
    return node, name


def edge_readback(graph, target, param):
    """True = an edge reads back on target.param. False = the graph was read and
    none does. None = this build (or this edge shape) cannot be asked.

    A shape we cannot parse returns None, NOT False. A false "nothing is wired"
    is a wrong diagnosis, and this workstream has spent whole sessions on those.
    """
    edges = graph_edges(graph)
    if edges is None:
        return None
    # An EMPTY edge list is a definitive read, not a parse failure: the graph
    # was asked and it holds nothing. Only a list whose entries we cannot read
    # is unanswerable. Collapsing those two was a bug the harness caught.
    if not edges:
        return False
    target_id = _node_identity(target)
    parsed_any = False
    for edge in edges:
        node, name = _edge_target_of(edge)
        if node is None or name is None:
            continue
        parsed_any = True
        if name == param and _node_identity(node) == target_id:
            return True
    if not parsed_any:
        return None
    return False


# One-shot: the first successful newEdge of the run reports what it handed back.
_NEW_EDGE_PROBED = [False]

# Whether the getID round-trip has reported its result yet this run.
_EDGE_ID_TRIP_REPORTED = [False]


def probe_new_edge_return(graph, handed_back):
    """ONE probe, ONE question: does `newEdge` hand back anything that identifies
    the edge it just made?

    The predictions, written before the run as the rules require:
      PASS  the return value is not None, and either it exposes an id-ish
            attribute or `getEdgeFromID` accepts it and returns something. Then
            there is a route to verifying a wire that this repo has not tried.
      FAIL  it returns None, or a bare bool, or nothing `getEdgeFromID` accepts.
            Then this route is closed and nobody spends another session on it.
      Anything else is "I do not know" and gets copied back, not interpreted.

    It reports ONLY what it just called. Whether the build has edge read-back is
    `graph_edges`'s question and it prints its own answer after probing for it;
    this probe saying so too would be a second voice on a question it did not
    ask, which is how a confident wrong line got under a correct one in the
    2026-08-04 log.

    Why it is worth one probe: the 2026-08-04 bench dump showed this build has no
    method that LISTS edges, which is why four guessed names all missed, but it
    DOES have `getEdgeFromID`, and `safe_edge` was throwing `newEdge`'s return
    value away without ever looking at it. Untried, not ruled out.

    Prints and returns nothing. It must not change what any caller does."""
    if _NEW_EDGE_PROBED[0]:
        return
    _NEW_EDGE_PROBED[0] = True
    print("[probe] newEdge returned: type {0}, value {1!r}".format(
        type(handed_back).__name__, handed_back))
    if handed_back is None:
        print("        FAIL as predicted: nothing came back, so this route to "
              "checking a wire is closed. Do not probe it again.")
        return
    try:
        offered = [n for n in dir(handed_back) if not n.startswith("_")]
    except Exception as e:
        offered = []
        print("        (could not list what it offers: {0})".format(e))
    if offered:
        print("        it OFFERS: {0}".format(", ".join(sorted(offered))))
    getter = getattr(graph, "getEdgeFromID", None)
    if getter is None:
        print("        graph has no getEdgeFromID on this build, so a returned "
              "handle has nothing to be looked up with.")
        return
    try:
        found = getter(handed_back)
    except Exception as e:
        print("        getEdgeFromID(<that value>) raised: {0}. If the value is "
              "an object rather than an id, the id is probably one of the names "
              "listed above; that is the next probe, not a guess to make "
              "now.".format(e))
        return
    print("        getEdgeFromID(<that value>) returned: type {0}, value "
          "{1!r}".format(type(found).__name__, found))
    print("        ^ COPY THE THREE [probe] LINES BACK. If a returned handle "
          "round-trips through getEdgeFromID, edge_readback gets a real "
          "implementation and every wire in every script starts self-checking.")


def _verify_edge_by_id(graph, edge_handle):
    """Verify a just-made edge by round-tripping its ID through getEdgeFromID.

    True = the edge reads back. False = the graph was asked and the edge is not
    there. None = cannot be asked (handle is None, no getID, no getEdgeFromID).

    MEASURED 2026-08-05 at R0: newEdge returns a lux.ShaderEdge offering getID,
    getSourceNode, getTargetNode, isEnabled. getEdgeFromID refused the object
    itself ('cannot be interpreted as an integer') and named the route: pass
    edge.getID(). This function builds that route.

    Report-only for the first run (RNK-0299): the return contract of safe_edge
    is unchanged (True = call did not raise). Whether a NOT-WIRED edge should
    fall back is RNK-0289's decision, not this function's."""
    if edge_handle is None:
        return None
    get_id = getattr(edge_handle, "getID", None)
    if get_id is None:
        return None
    try:
        edge_id = get_id()
    except Exception:
        return None
    if edge_id is None:
        return None
    getter = getattr(graph, "getEdgeFromID", None)
    if getter is None:
        return None
    try:
        found = getter(edge_id)
    except Exception as e:
        if not _EDGE_ID_TRIP_REPORTED[0]:
            _EDGE_ID_TRIP_REPORTED[0] = True
            print("    [info] getEdgeFromID({0}) raised: {1}. The route may need "
                  "a different argument shape.".format(edge_id, e))
        return None
    if found is None:
        return False
    if not _EDGE_ID_TRIP_REPORTED[0]:
        _EDGE_ID_TRIP_REPORTED[0] = True
        print("    [info] EDGE READ-BACK IS LIVE via getID round-trip. "
              "getEdgeFromID({0}) returned a valid edge. Every wire below "
              "is checked, not assumed.".format(edge_id))
    return True


def safe_edge(graph, source, target, param, label=""):
    """Wire an edge, then say what actually happened. The return value keeps its
    old meaning (True = the call did not raise) so every existing caller behaves
    exactly as before; the CONSOLE carries the honesty."""
    what = label or param
    ptype, pure, type_text = describe_target_param(target, param)
    try:
        handed_back = graph.newEdge(source=source, target=target, param=param)
    except Exception as e:
        print("  [warn] couldn't wire {0}: {1} [{2}]".format(what, e, type_text))
        return False
    # RNK-0294 / ladder W3. Report-only, once per run: this must not change the
    # graph any caller builds, and it does not read back the wire it just made.
    try:
        probe_new_edge_return(graph, handed_back)
    except Exception as e:
        print("  [warn] the newEdge return probe itself failed: {0} (the wire "
              "above is unaffected)".format(e))
    verdict = _verify_edge_by_id(graph, handed_back)
    if verdict is True:
        print("  {0} WIRED -- edge reads back [{1}]".format(what, type_text))
    elif verdict is False:
        print("  [WARN] {0}: the call did not raise, but NO edge reads back on "
              "that parameter [{1}]".format(what, type_text))
    else:
        print("  {0} CALL OK, UNVERIFIED -- no edge read-back here [{1}]".format(
            what, type_text))
    # The scalar note is FACTS, not a verdict. M5 proved a type-4 target lands on
    # a BRDF and verified it on read-back; the same type on a TEXTURE node
    # (`bump_height`) cannot be reached. The node is printed above, so the read
    # that settles it is right there on the line. Only worth saying when the
    # graph could not be asked -- once an edge reads back, it reads back.
    if verdict is not True and is_scalar_value_type(ptype):
        print("      note: that target is a scalar type. M5 probed this and it "
              "goes BOTH ways -- drivable on a BRDF (curvature -> "
              "metal.roughness landed and read back), not drivable on a texture "
              "node (bump_height). The node name on the line above is the "
              "discriminator; judge it on the render.")
    return True


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
        scale_base = LEGACY_SCALE_BASE.get(k)
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
# Center On: Part (texture_space, type-2 int enum)
# --------------------------------------------------------------------------
# Maps texture Scale to part bounds instead of model bounds. PROBED 2026-07-28:
# param is PARAMETER_TYPE_INTEGER(2), string "Part" fails. Enum values:
# 0=Legacy (OBSERVED AB09), 1=Model (fresh default), 2=Part (CONFIRMED 2026-07-29).
# Overridable per run from dialog.
CENTER_ON_PART_INTS = (2,)


# AB09: set once per run from the dialog / DEFAULT_OPTIONS. None = try the
# candidate list in order.
CENTER_ON_OVERRIDE = None


def set_center_on_override(value):
    """Pin the Center On int for this run. Anything unreadable, or 0 (Legacy,
    observed), falls back to the candidate list."""
    global CENTER_ON_OVERRIDE
    try:
        val = int(value)
    except (TypeError, ValueError):
        CENTER_ON_OVERRIDE = None
        return
    if val == 0:
        print("  [info] center_on_int 0 is 'Legacy' (observed on this build) -- "
              "ignoring it and using the Part candidates {0}".format(
                  list(CENTER_ON_PART_INTS)))
        CENTER_ON_OVERRIDE = None
        return
    CENTER_ON_OVERRIDE = val


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
    if CENTER_ON_OVERRIDE is not None:
        candidates = [CENTER_ON_OVERRIDE]
    else:
        candidates = list(CENTER_ON_PART_INTS)
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
        if got == val:
            if val == 2:
                print("  [info] 'Center On' = 2 (Part -- confirmed at render "
                      "2026-07-29)")
            else:
                print("  [info] 'Center On' set to int {0} (non-default; 2 is the "
                      "confirmed Part value, 0 is Legacy)".format(val))
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


# ===== RADIUS ================================================================
# API takes METRES, panel shows MILLIMETRES. Unit convention, not scene property.
# MEASURED 2026-08-03: wrote 1.0, panel read 1000. Old value 1350 was wrong
# (0.74x error). Same convention as TEXTURE_DISPLAY_FACTOR (both are 1000.0).
# Radius does NOT depend on part's scene-unit scale; mm_to_scene not needed.
# Texture Scale IS part-relative; the two stay separate.
# Two constants kept intentionally: each is one observation, not a law.
# Occlusion radius: UNMEASURED whether same convention. Keeps scene-unit path
# until bench reads the panel after mode 8's 1.0 write.
RADIUS_DISPLAY_FACTOR = 1000.0
RADIUS_DISPLAY_FACTOR_LIVE = [RADIUS_DISPLAY_FACTOR]

# This scene's millimetres per scene unit, set once per build from
# resolve_part_size. Occlusion-style nodes need it because their Radius is in
# scene units; curvature-style nodes do not, because their panel is in mm.
SCENE_MM_PER_UNIT_LIVE = [None]

# The part's real size in millimetres, set once per build. A radius is absolute,
# which is right (an edge break is 1-2 mm whether the part is 200 mm or 2 m) and
# is exactly why it needs a sanity check against the part: the 2026-07-31 cube run
# asked for a 17 mm grime radius on a 10 mm cube, so the occlusion node read every
# point as occluded and the grime colour covered the object end to end. A radius
# larger than the part is never what anyone meant.
PART_MM_LIVE = [None]

# A radius bigger than this fraction of the part stops being an edge break and
# becomes a wash over the whole surface. Clamped, and said out loud.
RADIUS_MAX_PART_FRACTION = 0.25

# Said once per run, not once per radius: three identical warnings read as three
# problems. One is a fact about the run.
CLAMP_UNKNOWN_SAID = [False]

# The mask viewer sets this to True so the radius clamp REPORTS but does not
# APPLY. The viewer's job is showing what a value does, including one that is
# too big. Generators keep this at False so they clamp normally. RNK-0296.
CLAMP_REPORT_ONLY = [False]


def resolve_part_mm(scale_info):
    """The part's size in real millimetres, however it can be got.

    Prefers the number the operator typed, falls back to the measured extent
    converted through this scene's unit, and returns 0.0 when neither is
    available (which every caller reads as 'unknown, do not clamp')."""
    entered = as_float(scale_info.get("part_size_mm"), 0.0)
    if entered > 0.0:
        return entered
    extent = as_float(scale_info.get("part_extent_scene"), 0.0)
    per_unit = as_float(scale_info.get("units_to_mm"), 0.0)
    if extent > 0.0 and per_unit > 0.0:
        return extent * per_unit
    return 0.0


def clamp_radius_to_part(radius_mm, label):
    """Hold a radius to something that can still read as a local feature.

    Returns the radius to use. Loud on clamp, silent otherwise: a clamp means the
    number asked for could not have produced local wear on this part, which is a
    thing to fix in the dialog rather than to discover from a flat render.

    It is also loud when it CANNOT check, which it was not until 2026-08-05. The
    mask viewer never populated PART_MM_LIVE, so in the one script whose whole job
    is diagnosing mask failures this returned early and said nothing, every run: a
    150 mm radius went onto a 220 mm part unwarned. A guard that can silently
    no-op is not a guard, it reads as a check that passed."""
    part_mm = PART_MM_LIVE[0]
    if not part_mm or part_mm <= 0.0:
        if not CLAMP_UNKNOWN_SAID[0]:
            CLAMP_UNKNOWN_SAID[0] = True
            print("    [warn] part size is UNKNOWN, so no radius can be checked "
                  "against it this run ({0} and every radius after it). This is "
                  "not 'the radius is fine', it is 'nobody looked'. Enter the "
                  "part size in the dialog, or filter to a part that "
                  "measures.".format(label))
        return radius_mm
    ceiling = part_mm * RADIUS_MAX_PART_FRACTION
    if radius_mm <= ceiling:
        return radius_mm
    if CLAMP_REPORT_ONLY[0]:
        print("    [info] {0}: radius {1} mm WOULD be clamped to {2} mm "
              "({3}x the {4} mm part). Viewer: using the asked-for radius to "
              "show what it does.".format(
                  label, round(radius_mm, 4), round(ceiling, 4),
                  round(radius_mm / part_mm, 2), round(part_mm, 4)))
        return radius_mm
    print("    [warn] {0}: radius {1} mm is {2}x the part ({3} mm), which reads "
          "as a wash over the whole surface rather than a local feature. "
          "CLAMPED to {4} mm ({5} of the part). Lower it in the dialog if you "
          "meant something else.".format(
              label, round(radius_mm, 4), round(radius_mm / part_mm, 2),
              round(part_mm, 4), round(ceiling, 4), RADIUS_MAX_PART_FRACTION))
    return ceiling


def set_radius_mode(node, in_pixels, radius_mm, radius_px, label):
    """Set a mask node's Radius in the unit THAT NODE actually reads.

    There are two kinds of node here and they do not agree, which cost a render
    on 2026-07-30 when a single rule was applied to both:

    CURVATURE has `adaptive_radius`, display 'Radius In Pixels'.
      ON (the default) -> Radius counts SCREEN PIXELS, so any scene-unit value
      asks for a one-pixel edge and the mask comes back black. OFF -> the panel
      is in MILLIMETRES and takes a value RADIUS_DISPLAY_FACTOR (1000, measured
      2026-08-03; this docstring said 1350 for two days after that) times
      smaller. Confirmed by render at 1.5 mm.

    OCCLUSION has NO such parameter -- it was never screen-space, so the display
      factor must NOT be applied to it. Its Radius is in SCENE UNITS, which is
      what `mm_to_scene` was doing before. Applying 1350 to it wrote 0.0074 on a
      270-unit part, a radius of effectively zero, and the whole surface read as
      occluded: the black speckled render.

    So the NODE decides, not the call site. Presence of the toggle is the test,
    and every write says which unit it used. The radius is held to a fraction of
    the part first, because neither unit rescues a radius bigger than the object
    (the 2026-07-31 cube run: 17 mm of grime on a 10 mm cube)."""
    radius_mm = clamp_radius_to_part(radius_mm, label)
    p = find_param(node, ["radius in pixels", "adaptive_radius", "adaptive radius"])

    if p is None:
        # MEASURED 2026-08-03: an OCCLUSION radius panel also reads 1000 for a
        # written 1.0. So there is ONE rule, not two. The 2026-07-30 conclusion
        # that occlusion was in scene units was wrong, and it was wrong in the
        # same session and for the same reason as the 1350: both came from
        # inference over a render rather than from writing a known value and
        # reading the panel.
        #
        # What the scene-unit path was doing, straight off the 2026-08-03 log:
        # for a 1.5 mm radius it wrote **1041.6** on a part 152770 units across,
        # instead of 0.0015. Every point on the part reads as occluded at that
        # size, which is precisely the "whole surface covered in grime" failure
        # this workstream chased on 2026-07-30 and again on 2026-07-31.
        #
        # mm_to_scene therefore has no part in ANY radius any more. It stays for
        # genuinely scene-unit quantities; a radius is not one of them.
        value = radius_mm / RADIUS_DISPLAY_FACTOR_LIVE[0]
        set_display(node, ["radius"], value)
        print("    {0}: no pixel toggle -- wrote {1}, panel should read {2} mm "
              "(same metres-to-millimetres rule as curvature, measured "
              "2026-08-03)".format(label, value, round(radius_mm, 4)))
        return value

    was = None
    try:
        was = p.getValue()
    except Exception:
        was = "unreadable"
    try:
        p.setValue(bool(in_pixels))
    except Exception as e:
        print("    [warn] {0}: could not set 'Radius In Pixels' ({1})".format(label, e))

    if in_pixels:
        value = radius_px
        set_display(node, ["radius"], value)
        print("    {0}: Radius In Pixels was {1}, set True -> radius {2} PIXELS "
              "(resolution and camera dependent)".format(label, was, value))
    else:
        value = radius_mm / RADIUS_DISPLAY_FACTOR_LIVE[0]
        set_display(node, ["radius"], value)
        print("    {0}: Radius In Pixels was {1}, set False -> wrote {2}, panel "
              "should read {3} mm (factor {4})".format(
                  label, was, value, round(radius_mm, 4),
                  RADIUS_DISPLAY_FACTOR_LIVE[0]))
    return value


# None means DO NOT WRITE IT. See set_curvature_cutoff for why this stopped
# being 0.0 within hours of becoming it.
CURVATURE_CUTOFF = None


def set_curvature_cutoff(node, cutoff=None):
    """Set the Curvature node's CUTOFF, which no rev of any script ever touched.

    MEASURED AT THE BENCH 2026-08-03, by hand, and it is the difference between
    a black mask and a working one. Mode 2 of the label probe rendered the part
    fully transparent (the mask black everywhere) at the scripted defaults. The
    operator set Cutoff to 0 and raised the radius, and the same graph rendered
    green with red on every edge, rim and bolt hole -- the result this whole
    architecture was gated on.

    Cutoff discards curvature below a threshold. KeyShot's default is not zero,
    so a genuine but modest edge signal is floored to black before it reaches
    anything downstream, and every mask built by this repo has been fighting it
    blind. It is the `Wear Contrast` equivalent RNK-0276 already names as unused.

    LEFT AT KEYSHOT'S DEFAULT unless a caller passes a value, and the default is
    PRINTED, because that number is evidence rather than trivia.

    This forced 0.0 for a few hours on 2026-08-03 and that was a mistake of
    exactly the kind this file keeps warning about. The reasoning was "keep
    everything, shape it downstream", built on one bench observation: the
    operator set Cutoff to 0, raised the radius to 145 mm, and mode 2 rendered
    correctly. Two variables changed and only one got the credit.

    The counter-evidence was already in the repo. The 2026-07-30 mask viewer run
    put a crisp mask on every edge of the 220 mm discharge body at a radius of
    1.5 mm, and no rev before 2026-08-03 ever wrote Cutoff at all, so that run
    had the default. Forcing 0 then made mode 1 come back BLACK on the same
    scene at the same radius.

    SWEPT AT THE BENCH 2026-08-03, on the 220 mm discharge body at 1.5 mm, with
    Performance Mode off. KeyShot's default is 1.

        cutoff 1 (default)  crisp bright lines on the rims and bolt circles.
                            The working value, and the one every good run has
                            silently used.
        cutoff 0            the part goes almost entirely WHITE. Only the
                            concave seams stay dark. A mask that is white
                            everywhere means WEAR EVERYWHERE.
        cutoff 0.1          almost entirely black, edges only faintly present.
        cutoff 0.5          dark, low contrast, edges faint.

    So it is NOT a simple threshold, and 0 is the worst possible setting rather
    than the most permissive one -- a cylindrical body has gentle positive
    curvature over its whole surface, and at 0 all of it counts. (The 0.1 and
    0.5 frames were phone photos of a mostly-dark screen, so their relative
    brightness is not reliable evidence; the white-at-0 jump is unmistakable and
    is the part that matters.)

    THIS REINTERPRETS THE 2026-08-03 MODE 2 RESULT. That frame was rendered at
    cutoff 0, so the mask was white nearly everywhere and the red that showed
    through was the CONCAVE seams, not the convex edges. It still proves what
    the gate asked -- a spatially varying mask does drive a label's opacity and
    it does render -- but the picture was "wear everywhere except the seams",
    which is the inverse of what a wear mask wants. At the default cutoff the
    same graph should put wear on the edges instead.

    Nothing is written here. The default is right, it is printed as evidence,
    and the dialog can sweep it when someone wants to tune selectivity."""
    if cutoff is None:
        cutoff = CURVATURE_CUTOFF
    p = find_param(node, ["cutoff"])
    if cutoff is None:
        if p is not None:
            try:
                print("    curvature: Cutoff LEFT AT KEYSHOT'S DEFAULT of {0} "
                      "(nothing written -- sweep it from the dialog to settle "
                      "what it does)".format(p.getValue()))
            except Exception:
                print("    curvature: Cutoff left at default (unreadable)")
        return False
    if p is None:
        print("    [info] curvature: no 'Cutoff' parameter on this build "
              "(nothing to floor the mask, so nothing to clear)")
        return False
    try:
        was = p.getValue()
    except Exception:
        was = "unreadable"
    ok = set_display(node, ["cutoff"], cutoff)
    if ok:
        # 2026-08-04: the sentence that used to print here asserted that a
        # non-zero cutoff floors a real edge signal to black. THIS FUNCTION'S
        # OWN DOCSTRING RETRACTS THAT, and the 2026-08-03 sweep measured the
        # opposite: at cutoff 1.0 the edges read crisply, and at 0 the part went
        # almost entirely WHITE with only the concave seams dark. The claim
        # survived in the one place the operator actually reads. Reported as a
        # write and a warning now, with the measurement instead of the theory.
        print("    curvature: Cutoff was {0}, set {1}".format(was, cutoff))
        if cutoff is not None and float(cutoff) == 0.0:
            print("    [warn] cutoff 0 was MEASURED on 2026-08-03 to wash the "
                  "part almost entirely WHITE, leaving only concave seams dark. "
                  "The value that gave crisp edges in that sweep was KeyShot's "
                  "own default of 1.0. If this frame reads washed out, that is "
                  "the first thing to change.")
    return ok


def add_curvature_mask(graph, radius_mm=None, in_pixels=False, radius_px=4.0,
                       cutoff=None):
    """Convex-edge mask: white on positive curvature (edges/corners), black on
    the flats -- param names confirmed from the material-graph dump. AB13: this
    drives the effect texture's own colour slot (never a bump input, which
    refuses a Curvature node -- probe M1).

    AB14 SETS THE RADIUS. Every rev up to AB13 left it at KeyShot's default, an
    absolute value in SCENE units -- so on the discharge body (152770 units
    across) the mask hunted for edges at a size with no relation to the part and
    found nothing. The paint generator hit the identical wall on 2026-07-30 with
    hardcoded radii of 0.35 and 1.60. `radius` here is already in scene units,
    converted from millimetres by the caller via `mm_to_scene`."""
    n = try_new_node(graph, "SHADER_TYPE_CURVATURE", "Curvature (edge mask)")
    if n is None:
        return None
    if radius_mm is not None:
        set_radius_mode(n, in_pixels, radius_mm, radius_px, "curvature")
    set_curvature_cutoff(n, cutoff)
    set_display(n, ["positive curvature"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
    set_display(n, ["zero curvature"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
    set_display(n, ["negative curvature"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
    return n


def add_occlusion_mask(graph, radius_mm=None, in_pixels=False, radius_px=4.0):
    """Cavity mask: white in occluded crevices, black on exposed faces -- the
    inverse of the edge mask, so pitting lands only in the crevices. AB13: wired
    into the effect texture's own colour slot (probe M3 PASS); a bump input
    refuses an Occlusion node outright. Best-effort: masking degrades to unmasked
    if the names aren't found."""
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (cavity mask)")
    if n is None:
        return None
    if radius_mm is not None:
        set_radius_mode(n, in_pixels, radius_mm, radius_px, "occlusion")
    set_display(n, ["occluded"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
    set_display(n, ["unoccluded", "bright", "far", "exposed"], (0.0, 0.0, 0.0),
                ptype=PT_COLOR)
    return n


BLEND_NORMAL_INT = 0
BLEND_MULTIPLY_NAME = "Multiply"
BLEND_MULTIPLY_INT = 1


def _composite_amount(node, amount, label):
    """Set a Color Composite's blend AMOUNT, which is what makes a contribution
    weighted rather than absolute. The AB02 dump lists `alpha`, `source_alpha`
    and `background_alpha` as plain floats on this node; the first that takes is
    used. Returns True if an amount could be set.

    If none exists on this build we CANNOT do a partial weight -- and that is
    said out loud rather than silently composited at full strength, because a
    silently-full-strength modulation is exactly the intersection behaviour this
    function exists to replace."""
    for kw in (["source alpha", "source_alpha"], ["alpha"], ["opacity"]):
        p = find_param(node, kw)
        if p is None or p.isPure():
            continue
        if set_display(node, kw, float(amount)):
            print("    {0}: amount {1} via '{2}'".format(
                label, amount, p.getDisplayName()))
            return True
    print("    [warn] {0}: no blend-amount parameter on this build, so this "
          "contribution is FULL STRENGTH. An amount of 0 still turns the layer "
          "off entirely (it is not built at all); anything between 0 and 1 is "
          "not available here.".format(label))
    return False


def _composite(graph, source, background, blend_name, blend_int, amount, label):
    """One weighted composite stage. Returns the composite node, or the
    unchanged background if any part of it could not be built -- so a missing
    node degrades to 'this contribution did not happen', never to a black mask."""
    comp = try_new_node(graph, "SHADER_TYPE_COLOR_COMPOSITE",
                        "Color Composite ({0})".format(label))
    if comp is None:
        print("    [warn] {0}: Color Composite unavailable -- contribution "
              "skipped".format(label))
        return background
    src_name, bg_name = _composite_inputs(comp)
    if not src_name or not bg_name:
        print("    [warn] {0}: Color Composite has no two colour inputs -- "
              "contribution skipped".format(label))
        _drop_node(graph, comp)
        return background
    ok1 = safe_edge(graph, source=source, target=comp, param=src_name,
                    label="{0}: source".format(label))
    ok2 = safe_edge(graph, source=background, target=comp, param=bg_name,
                    label="{0}: background".format(label))
    if not (ok1 and ok2):
        print("    [warn] {0}: could not wire both inputs -- contribution "
              "skipped".format(label))
        _drop_node(graph, comp)
        return background
    set_blend_mode(comp, blend_name, blend_int)
    if amount is not None:
        _composite_amount(comp, amount, label)
    return comp


def build_wear_mask(graph, curvature=None, grunge=None, occlusion=None,
                    grunge_amount=0.5, ao_amount=0.5, contrast=None):
    """Compose a wear mask the way a wear GENERATOR does, not the way a boolean
    does. RNK-0276.

    THE BUG THIS REPLACES. Every mask this repo has built was the INTERSECTION
    of the curvature band and a grunge pattern: the pattern drove the effect's
    colour and the curvature gated it, so either signal going sparse took the
    whole layer to black, and there was no amount at which the pattern could be
    turned off. Two of the black renders this workstream chased were that
    intersection behaving exactly as written.

    THE MODEL, taken from how Substance's Metal Edge Wear and Paint Wear
    generators are actually built:

        wear  =  curvature                      the PRIMARY signal, alone
        wear  =  wear modulated by grunge       a WEIGHTED contribution, and the
                                                weight reaches zero, at which
                                                point the pattern is simply not
                                                in the graph
        wear  =  wear suppressed by occlusion   AO REMOVES wear from crevices
                                                rather than adding grime to them
        wear  =  contrast(wear)                 the shaping step, the `Wear
                                                Contrast` equivalent

    Curvature alone is a valid mask and is what you get with both amounts at 0.
    That is the property the old composition could not express and the reason
    a sparse pattern could black out an entire layer.

    Cutoff is set on the curvature node itself (see set_curvature_cutoff) and is
    the other half of the shaping: measured at the bench 2026-08-03, a non-zero
    default floors a real edge signal to black before any of this runs.

    Every stage degrades to the stage before it, so the worst case is a plainer
    mask rather than no mask. Returns the node carrying the final mask, ready to
    drive a label's opacity (the stacked-label architecture) or a texture's
    inside_color (the composite stack). Returns None only if there is no
    curvature node to start from."""
    if curvature is None:
        print("  [warn] wear mask: no curvature node -- nothing to build on")
        return None
    print("  wear mask: curvature is the primary signal")
    wear = curvature

    if grunge is not None and grunge_amount and grunge_amount > 0.0:
        wear = _composite(graph, grunge, wear, BLEND_MULTIPLY_NAME,
                          BLEND_MULTIPLY_INT, grunge_amount, "grunge modulation")
    elif grunge is not None:
        print("    grunge amount is 0 -- pattern deliberately NOT in the mask, "
              "so the mask is pure curvature")
        _drop_node(graph, grunge)
    else:
        print("    no grunge pattern -- mask is pure curvature")

    if occlusion is not None and ao_amount and ao_amount > 0.0:
        # AO SUPPRESSES. An occlusion node is white in the crevices, so used
        # directly it would ADD wear exactly where a real part is protected.
        # Inverted and multiplied, it removes wear from cavities, which is what
        # the reference generators do and the opposite of what this repo did.
        inv = try_new_node(graph, "SHADER_TYPE_COLOR_INVERT",
                           "Color Invert (AO suppression)")
        if inv is None:
            print("    [warn] AO suppression: no Color Invert on this build -- "
                  "occlusion left out rather than wired the wrong way round")
            _drop_node(graph, occlusion)
        else:
            # MEASURED 2026-08-03: a Color Invert's one input is named SOURCE,
            # display 'Source', type 14. This lookup asked for "color" or
            # "input", matched neither, and the console said "could not wire the
            # invert -- occlusion left out". So the AO half of the very first
            # composed-mask run never existed, and the frame was judged without
            # it. Guessed parameter names have now produced this class of bug
            # five times in this repo (lux.newMaterial, displace.height,
            # texture_use_profile, METAL anisotropy, and this one); the standing
            # rule is to read the dump rather than to reason about the name.
            src = find_param(inv, ["source", "color", "input"])
            if src is None or not safe_edge(graph, source=occlusion, target=inv,
                                            param=src.getName(),
                                            label="AO suppression: occlusion -> invert"):
                print("    [warn] AO suppression: could not wire the invert -- "
                      "occlusion left out")
                _drop_node(graph, inv)
                _drop_node(graph, occlusion)
            else:
                wear = _composite(graph, inv, wear, BLEND_MULTIPLY_NAME,
                                  BLEND_MULTIPLY_INT, ao_amount, "AO suppression")
    elif occlusion is not None:
        print("    AO amount is 0 -- occlusion deliberately not in the mask")
        _drop_node(graph, occlusion)

    if contrast is not None:
        adj = try_new_node(graph, "SHADER_TYPE_COLOR_ADJUST",
                           "Color Adjust (wear contrast)")
        if adj is None:
            print("    [info] wear contrast: no Color Adjust on this build -- "
                  "shaping left to Cutoff alone")
        else:
            src = find_param(adj, ["source", "color", "input"])
            if src is None or not safe_edge(graph, source=wear, target=adj,
                                            param=src.getName(),
                                            label="wear contrast: mask -> adjust"):
                print("    [info] wear contrast: could not wire -- skipped")
                _drop_node(graph, adj)
            elif set_display(adj, ["contrast"], float(contrast)):
                print("    wear contrast: {0}".format(contrast))
                wear = adj
            else:
                print("    [info] wear contrast: no 'Contrast' parameter -- "
                      "skipped")
                _drop_node(graph, adj)
    return wear


def mask_bump_layer(graph, effect_node, mask_node, label):
    """Spatially gate a bump layer by driving the EFFECT TEXTURE'S OWN COLOUR
    SLOTS with the mask, so the effect only has contrast where the mask is white.

    AB13, built on probe M1/M2/M3. A bump input accepts texture-class nodes and
    REFUSES every colour utility (Curvature, Occlusion, Color Composite, Color To
    Number, Color Adjust, Color Invert -- all six refused, verified). So a mask
    can never be carried into the bump domain by a utility node, which is what
    both earlier designs tried: Color Composite (Rev 1) and curvature-carries-the
    -effect (the "plan B", which P16 had already shown failing at the second hop).

    Instead the mask lives INSIDE the texture. A texture used as bump is read as
    a height field off its own output colour, so:
        mask -> effect.inside_color     (white where wear belongs)
        effect.outside_color = black
        effect -> the bump bus          (unchanged, a plain texture edge)
    On the flats both colours are black: no contrast, no bump. On the edges (or
    in the cavities) the interiors go white and the effect appears.

    Still non-fatal: if the colour slot refuses the connection the layer is left
    unmasked and present, exactly as before, and the mask node is removed rather
    than left orphaned."""
    if effect_node is None or mask_node is None:
        return effect_node
    inside = find_param(effect_node, ["inside_color", "color"])
    if inside is None:
        print("  [warn] {0}: no colour slot to mask through -- left unmasked".format(label))
        _drop_node(graph, mask_node)
        return effect_node
    ok = safe_edge(graph, source=mask_node, target=effect_node, param=inside.getName(),
                   label="{0}: mask -> {1}".format(label, inside.getName()))
    if ok:
        # Read the edge back. AB07's lesson: an API call that neither raises nor
        # returns anything useful is not evidence it did something -- setMaterial
        # scored six revs of successes as failures that way. The probe verified
        # every edge this way; so does this.
        try:
            if not effect_node.getInputEdge(inside.getName()):
                print("  [warn] {0}: the mask edge was accepted but reads back "
                      "empty -- treating as unmasked".format(label))
                ok = False
        except Exception:
            pass  # no read-back API on this build; accept the non-raising set
    if not ok:
        print("  [info] {0}: colour slot refused the mask -- left unmasked".format(label))
        _drop_node(graph, mask_node)
        return effect_node
    # The other half of the mask: without a black background the flats keep full
    # contrast and the layer reads unmasked even though the mask landed.
    if not set_display(effect_node, ["outside_color", "background"], (0.0, 0.0, 0.0),
                       ptype=PT_COLOR):
        print("  [info] {0}: mask wired, but the background colour could not be "
              "set to black -- wear will still show on the flats".format(label))
    else:
        print("  [info] {0}: masked (mask -> colour slot, background black)".format(label))
    return effect_node


def _drop_node(graph, node):
    """Remove a node that turned out to be unusable, so a failed mask does not
    leave an orphan cluttering the graph."""
    try:
        graph.removeNode(node)
    except Exception:
        pass


def make_image_map(graph, path, label, label_scale=1.0):
    """Create an image/texture-map node pointed at `path`, self-probing the node
    type by getattr over IMAGE_MAP_CANDIDATES (first that exists). Returns the node,
    or None if no image-map node type exists on this build (labels are then skipped)
    or the path is empty. DEBUG-dumps ALL of the node's params so the render log
    reveals the real API (file-path + bump/strength display names), sets the file
    path defensively over several candidate names, and places it via
    set_center_on_part + Scale. Fully non-fatal."""
    if not path:
        return None
    shader_type = None
    resolved_attr = None
    for attr in IMAGE_MAP_CANDIDATES:
        st = getattr(lux, attr, None)
        if st is not None:
            shader_type = st
            resolved_attr = attr
            break
    if shader_type is None:
        print("  [warn] no image-map node type on this build -- labels skipped "
              "(tried {0})".format(", ".join(IMAGE_MAP_CANDIDATES)))
        return None
    try:
        n = graph.newNode(shader_type)
    except Exception as e:
        print("  [warn] couldn't create image-map node for {0} ({1}): {2} -- skipping".format(
            label, resolved_attr, e))
        return None
    print("  [info] image-map node for {0} resolved via lux.{1}".format(label, resolved_attr))
    # DEBUG-dump ALL params (unconditional -- this node is the API probe).
    dump_node(n, "Image Map ({0}) [{1}]".format(label, resolved_attr))
    # Set the file path defensively (the real display name is UNPROBED).
    # PROBED 2026-07-28: the image input is 'texture' / display "Texture",
    # PARAMETER_TYPE_STRING (9). AB06 searched ["image","file","filename",...] and
    # the substring pass matched "Use Embedded Color Profile" -- "file" lives
    # inside "pro-FILE-" -- so it tried to write a path into a Boolean and every
    # label channel silently loaded nothing. Pin the type to 9 so a name collision
    # cannot pick a bool again.
    ok = set_display(n, ["texture"], path, ptype=PTYPE_STRING)
    if not ok:
        # Last resort: any type-9 parameter on the node.
        for cand in n.getParameters():
            if cand.getType() == PTYPE_STRING and not cand.isPure():
                try:
                    cand.setValue(path)
                    print("  [info] image path set via type-9 fallback "
                          "'{0}'".format(cand.getName()))
                    ok = True
                    break
                except Exception:
                    pass
    if not ok:
        print("  [warn] label '{0}': couldn't set the image file path -- the node "
              "won't show the texture; confirm the path param display name from the "
              "dump above".format(label))
    # Placement: map to the PART (not the whole model) + apply the label scale.
    set_center_on_part(n)
    set_display(n, ["scale"], label_scale)
    return n


def _make_colour_node(graph, base_color):
    """Best-effort plain-colour node (the colour overlay's Background side), set to
    `base_color`. Resolves the node type over COLOR_NODE_CANDIDATES; returns the
    node or None. Non-fatal -- the caller falls back to setting the Composite's
    Background colour value directly when this returns None."""
    shader_type = None
    resolved_attr = None
    for attr in COLOR_NODE_CANDIDATES:
        st = getattr(lux, attr, None)
        if st is not None:
            shader_type = st
            resolved_attr = attr
            break
    if shader_type is None:
        return None
    try:
        n = graph.newNode(shader_type)
    except Exception as e:
        print("  [info] label overlay: couldn't create a colour node ({0}): {1}".format(
            resolved_attr, e))
        return None
    # Match the colour input by NAME with no type filter: a colour input can be the
    # type-14 connection kind (not PT_COLOR/13), and filtering by PT_COLOR would miss
    # it -- the same lesson as the base-colour wiring in build_material.
    set_display(n, ["color", "colour", "diffuse"], base_color)
    return n


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
        if not candidates:
            print("  [warn] THE SCENE TREE WALK FOUND NO NODES AT ALL. Seen on "
                  "2026-07-31, on a scene where KeyShot's own log was repeating "
                  "'Unknown node type in _getObjects 7' as a critical error, so "
                  "this is the scene's structure rather than the walk. The "
                  "id-based fallback below is the only route on such a scene.")

    applied, skipped = 0, 0
    kind_counts = {}
    for node in candidates:
        kind = None
        if DEBUG:
            try:
                kind = node.getKind()
            except Exception:
                kind = "?"
        # AB07 -- do NOT trust setMaterial()'s return value. AB06 did
        # `ok = bool(node.setMaterial(name))` and reported "applied to 0 node(s),
        # skipped 5" on a scene that plainly had geometry. setMaterial returns
        # None on this build, so bool(None) counted every success as a failure.
        # The count was wrong; whether the material actually landed was never
        # established either way. Verify by reading the material back instead.
        raised = False
        try:
            node.setMaterial(name)
        except Exception as e:
            raised = True
            if DEBUG:
                print("  [warn] setMaterial raised (kind={0}): {1}".format(kind, e))
        ok = False
        if not raised:
            try:
                ok = (node.getMaterial() == name)
            except Exception:
                # No read-back available -- a set that did not raise is the best
                # evidence we have.
                ok = True
        if ok:
            applied += 1
            if DEBUG:
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
        else:
            skipped += 1

    # Fallback: if the tree walk landed on nothing, go at the objects directly.
    # lux.getObjects() returns object IDs (38 of them on the operator's scene,
    # where the recursive walk found only 5 nodes and no kind-2 OBJECT at all),
    # and lux.setObjectMaterial(id, name) applies by ID without any traversal.
    if applied == 0:
        obj_ids = []
        getter = getattr(lux, "getObjects", None)
        setter = getattr(lux, "setObjectMaterial", None)
        if getter is not None and setter is not None:
            try:
                obj_ids = list(getter())
            except Exception as e:
                print("  [warn] lux.getObjects() failed: {0}".format(e))
            if obj_ids:
                print("  [info] tree walk applied to 0 -- falling back to "
                      "lux.setObjectMaterial over {0} object id(s)".format(len(obj_ids)))
                # AA07/AB17 (2026-07-31): this fallback had NEVER worked. It was
                # added in AB07 against a scene where the tree walk happened to
                # succeed, so it was never exercised until the label probe hit a
                # scene where the walk found nothing -- and then every one of the
                # 16 objects failed with "argument 1 must be str, not int".
                # The signature is not what AB07 assumed and cannot be read from
                # the API, so try the plausible forms, keep the one that works,
                # and NAME it. One run turns this into a settled fact.
                forms = [
                    ("setObjectMaterial(id, material)", lambda o: setter(o, name)),
                    ("setObjectMaterial(str(id), material)", lambda o: setter(str(o), name)),
                    ("setObjectMaterial(material, id)", lambda o: setter(name, o)),
                    ("setObjectMaterial(material, str(id))", lambda o: setter(name, str(o))),
                ]
                working = None
                first_error = {}
                for form_name, call in forms:
                    probe_id = obj_ids[0]
                    try:
                        call(probe_id)
                        working = (form_name, call)
                        print("  [info] object apply form that works: "
                              "{0}".format(form_name))
                        break
                    except Exception as e:
                        first_error[form_name] = str(e)
                if working is None:
                    print("  [warn] NO call form of setObjectMaterial was accepted. "
                          "What each one said:")
                    for form_name, _ in forms:
                        print("    {0} -> {1}".format(
                            form_name, first_error.get(form_name, "?")))
                else:
                    call = working[1]
                    for oid in obj_ids:
                        try:
                            call(oid)
                            applied += 1
                        except Exception as e:
                            if DEBUG:
                                print("  [warn] object {0} refused: {1}".format(oid, e))
                    # Read it back where the API allows, because an apply that
                    # does not raise is not an apply that landed -- the lesson
                    # setMaterial taught this workstream the expensive way.
                    reader = getattr(lux, "getObjectMaterial", None)
                    if reader is not None and applied:
                        # AA03 (2026-08-03): the first real run read back 1865 of
                        # 3724, and this loop could not say why -- it `break`s
                        # after the first call form that does not RAISE, so a
                        # reader that answers for some ids and returns something
                        # else for others looks identical to half the applies
                        # failing. Try both forms per id, count what each one
                        # says, and name the split. A number without a reason is
                        # what sent this workstream chasing the scene twice.
                        confirmed = 0
                        mismatched = 0
                        unreadable = 0
                        for oid in obj_ids:
                            answered = False
                            hit = False
                            for arg in (oid, str(oid)):
                                try:
                                    answered = True
                                    if reader(arg) == name:
                                        hit = True
                                        break
                                except Exception:
                                    continue
                            if hit:
                                confirmed += 1
                            elif answered:
                                mismatched += 1
                            else:
                                unreadable += 1
                        print("  [info] read-back confirms the material on {0} of "
                              "{1} object(s)".format(confirmed, len(obj_ids)))
                        if mismatched or unreadable:
                            print("  [info] of the rest: {0} answered with a "
                                  "different material, {1} could not be read at "
                                  "all. A large 'different material' count on a "
                                  "scene that renders correctly usually means "
                                  "the id list holds groups or instances as well "
                                  "as geometry, not that the apply "
                                  "failed".format(mismatched, unreadable))
                if applied:
                    print("  [info] id-based apply reached {0} object(s)".format(applied))
        else:
            print("  [info] lux.getObjects / lux.setObjectMaterial unavailable -- "
                  "no id-based fallback on this build")
    suffix = " matching {0}".format(repr(name_filter)) if name_filter else ""
    print("Applied '{0}' to {1} node(s){2}, skipped {3}".format(name, applied, suffix, skipped))
    if DEBUG and applied:
        print("  applied to node kinds: {0}".format(kind_counts))
    if applied == 0:
        print("  [warn] THE MATERIAL IS NOT ON ANY GEOMETRY -- a render will show the "
              "old material, not this one. Neither the tree walk nor the id-based "
              "fallback applied anything; see the 'candidate kinds' histogram above "
              "(2=OBJECT, 5=MODEL, 4=MODEL_SET, 1=GROUP, 6=CAMERA) and confirm a model "
              "is loaded.")
    return applied


def mm_to_scene(mm, units_to_mm, extent, fraction, what):
    """Convert a real-world millimetre size into scene units for a RADIUS.

    `units_to_mm` is how many millimetres one scene unit is worth, measured this run
    (entered part size / measured extent). One millimetre is therefore 1/units_to_mm
    scene units. When that is unknown we cannot convert, so we fall back to a
    fraction of the part extent and say so -- a radius in the right order of
    magnitude beats a radius that is right in units nobody established.

    Returns a float in scene units. Never raises; a bad conversion falls back."""
    try:
        if units_to_mm and units_to_mm > 0.0:
            scene = float(mm) / float(units_to_mm)
            if scene > 0.0:
                print("  [info] {0} radius {1} mm = {2} scene units "
                      "(1 unit = {3} mm)".format(what, mm, scene,
                                                 "{0:.6g}".format(units_to_mm)))
                return scene
    except Exception:
        pass
    scene = float(extent) * float(fraction)
    print("  [info] {0} radius: no mm-per-unit established, using {1} of the part "
          "extent = {2} scene units. Enter the real part size in mm to get a "
          "true-size radius.".format(what, fraction, scene))
    return scene


# ===== END CORE BLOCK v1 ======================================================

# AB14: mask reach, in REAL MILLIMETRES -- deliberately NOT fractions of the part.
# A texture Scale is a fraction (a bigger part gets a proportionally bigger scratch
# field, which is what SCALE_FRACTIONS below does, and it is right). A curvature or
# occlusion RADIUS is a real-world size: an edge break on a casting is one or two
# millimetres whether the part is 200 mm or 2 m across, so scaling it with the part
# is as wrong as hardcoding it. Every rev up to AB13 did neither -- it never set the
# radius at all, leaving KeyShot's scene-unit default, which on the discharge body
# (152770 scene units across) has no relation to the part. That is why masked wear
# has never been seen to read. The paint generator hit the identical wall on
# 2026-07-30 with hardcoded radii of 0.35 and 1.60 scene units (0.00046 mm), and the
# fix there is the fix here. Converted through the measured mm-per-unit by
# `mm_to_scene` (shared, in the core block); both are dialog fields.
EDGE_MASK_RADIUS_MM = 1.5
CAVITY_MASK_RADIUS_MM = 10.0
# Used only when no mm-per-unit could be established (no real part size entered):
# a fraction of the extent is wrong in principle but keeps the radius inside the
# part's own order of magnitude, instead of five orders out.
EDGE_RADIUS_FRACTION = 0.008
CAVITY_RADIUS_FRACTION = 0.05


import math
import json


# --------------------------------------------------------------------------
# Debug / diagnostics
# --------------------------------------------------------------------------


GENERATOR_REV = "AB34"


# Demo spec-plate label set (03_OUTPUT/labels/spec-plate/) -- the DEFAULT_OPTIONS
# label paths. Forward slashes (Windows accepts them and they avoid backslash-escape
# hazards like \U in a plain, f-string-free ASCII source). An empty path skips that
# channel.
# AB07: this was an ABSOLUTE path on the author's machine. The KeyShot box is a
# different computer with no git and no workspace checkout, so the demo PNGs are
# simply not there -- AB06 shipped those paths as the label defaults and every
# channel pointed at a file that could not exist. Left EMPTY by default: an empty
# path skips that channel cleanly, and anyone wanting labels types a real path
# into the dialog. Set this to a folder that exists on THIS machine to restore
# one-click demo labels.
LABEL_DEMO_DIR = ""


def _label_demo(filename):
    """A demo label path, or the NO_LABEL sentinel when no demo dir is configured.
    Concatenating a bare filename onto an empty dir would yield
    "/spec-plate_opacity.png" -- a path that looks set but cannot resolve -- so
    return the sentinel and let the channel skip cleanly. AB08 returns "none"
    rather than "" because the dialog will not take an empty default string."""
    if not LABEL_DEMO_DIR:
        return NO_LABEL
    return LABEL_DEMO_DIR.rstrip("/") + "/" + filename

# --------------------------------------------------------------------------
# Part-size-aware texture scaling (AB05)
# --------------------------------------------------------------------------
# Fallback when the operator neither entered a part size nor a bounding-box API
# could measure one. 50 mm is a reasonable "small hardware part" default; the
# console prints a clear [info] telling the operator to enter a Part size for
# correct scaling when this is used.
DEFAULT_PART_SIZE_MM = 50.0




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

# AB08: set to False to skip the input dialog entirely and run straight off
# DEFAULT_OPTIONS below. Use it if the dialog misbehaves on this build, or to
# script a fixed configuration. Edit the values in DEFAULT_OPTIONS to steer the
# run -- "part_size_mm" is the one worth setting by hand (the real part size in
# mm), since it is the most reliable route to correct texture scaling.
USE_DIALOG = True







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
    # AB09: which int the texture "Center On" enum should be set to. 0 is Legacy
    # (observed), 1 is most likely Model, 2 is the Part candidate. Exposed so the
    # two can be compared from render to render without editing this file.
    "center_on_int": 2,
    # AB11: bbox unit -> texture Scale unit. 0.001 observed on KeyShot 13.2.0.184.
    "scale_factor": TEXTURE_SCALE_FACTOR,
    "edge_radius_mm": EDGE_MASK_RADIUS_MM,
    "cavity_radius_mm": CAVITY_MASK_RADIUS_MM,
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
    # AB06: optional emulated image-label (OFF by default). enable_labels gates the
    # whole feature; each channel path is independent (empty = skip that channel).
    # Defaults point at the demo spec-plate set in 03_OUTPUT/labels/spec-plate/.
    "enable_labels": False,
    "label_opacity_path": _label_demo("spec-plate_opacity.png"),
    "label_bump_path": _label_demo("spec-plate_bump.png"),
    "label_spec_path": _label_demo("spec-plate_spec.png"),
    "label_scale": 1.0,
    "label_bump_strength": 1.0,
    "label_spec_strength": 1.0,
}














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






# --------------------------------------------------------------------------
# Part-size resolution (AB05) -- entered > measured > default
# --------------------------------------------------------------------------
# KeyShot's default "Center On: Model" maps a procedural texture's tiling Scale to
# the whole model's bounding box, so a fixed Scale reads completely differently on
# a 40 mm part vs a 6700-unit model. AB05 resolves a characteristic PART dimension
# (mm) and drives every texture Scale off it (SCALE_FRACTIONS). This is where that
# dimension comes from. The bounding-box APIs below are UNPROBED on the real build
# -- every call is guarded, and a total miss just falls back to the default.



# TEXTURE_SCALE_FACTOR is defined above DEFAULT_OPTIONS (AB12), because
# DEFAULT_OPTIONS reads it at module level and Python cares about the order.










# --------------------------------------------------------------------------
# Options dialog (GUI only -- auto-skipped in headless mode)
# --------------------------------------------------------------------------

def get_options():
    if lux.isHeadless():
        print("Headless session detected -- skipping dialog, using DEFAULT_OPTIONS.")
        return dict(DEFAULT_OPTIONS)

    if not USE_DIALOG:
        print("USE_DIALOG is False -- skipping dialog, using DEFAULT_OPTIONS.")
        print("  part size {0} mm, material '{1}', wear '{2}', finish '{3}'".format(
            DEFAULT_OPTIONS["part_size_mm"], DEFAULT_OPTIONS["material_type"],
            DEFAULT_OPTIONS["wear_level"], DEFAULT_OPTIONS["finish"]))
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
        ("part_size_mm", lux.DIALOG_DOUBLE,
         "Real part size in mm (log only -- scale is measured):",
         DEFAULT_OPTIONS["part_size_mm"], (0.0, 100000.0)),
        # AB09: the Center On enum, exposed so 2 and 1 can be compared from render
        # to render. 0 is Legacy (observed on this build) and is ignored if entered.
        ("center_on_int", lux.DIALOG_INTEGER,
         "Texture 'Center On' int (2 = Part, 0 = Legacy):",
         DEFAULT_OPTIONS["center_on_int"], (0, 8)),
        # AB11: if the texture panel reads 1000x the intended Scale, this is the
        # field to change -- see the two Scale lines the build prints.
        ("edge_radius_mm", lux.DIALOG_DOUBLE,
         "Edge-mask reach (REAL mm -- an edge break, so 1-2):",
         DEFAULT_OPTIONS["edge_radius_mm"], (0.01, 1000.0)),
        ("cavity_radius_mm", lux.DIALOG_DOUBLE,
         "Cavity-mask reach (REAL mm -- how deep a crevice collects grime):",
         DEFAULT_OPTIONS["cavity_radius_mm"], (0.01, 1000.0)),
        ("scale_factor", lux.DIALOG_DOUBLE,
         "Texture scale factor (0.001 = observed on 13.2):",
         DEFAULT_OPTIONS["scale_factor"], (0.0000001, 1000.0)),
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
    # AB06: optional emulated image-label (opt-in). Placed AFTER the application
    # section. enable_labels gates it; each channel path is independent (leave a
    # path blank to skip that channel). Defaults point at the demo spec-plate set.
    values.append((lux.DIALOG_LABEL, "-- image label (experimental, emulated -- opt-in) --"))
    values.append(("enable_labels", lux.DIALOG_CHECK,
                    "Add an emulated image label (bump + spec + masked colour)",
                    DEFAULT_OPTIONS["enable_labels"]))
    values.append(("label_opacity_path", lux.DIALOG_TEXT,
                    "Label colour/opacity PNG ('none' = skip colour overlay):",
                    DEFAULT_OPTIONS["label_opacity_path"]))
    values.append(("label_bump_path", lux.DIALOG_TEXT,
                    "Label bump PNG ('none' = skip bump):",
                    DEFAULT_OPTIONS["label_bump_path"]))
    values.append(("label_spec_path", lux.DIALOG_TEXT,
                    "Label spec/roughness PNG ('none' = skip spec):",
                    DEFAULT_OPTIONS["label_spec_path"]))
    values.append(("label_scale", lux.DIALOG_DOUBLE,
                    "Label scale (x):", DEFAULT_OPTIONS["label_scale"], (0.1, 10.0)))
    values.append(("label_bump_strength", lux.DIALOG_DOUBLE,
                    "Label bump strength:", DEFAULT_OPTIONS["label_bump_strength"], (0.0, 3.0)))
    values.append(("label_spec_strength", lux.DIALOG_DOUBLE,
                    "Label spec strength:", DEFAULT_OPTIONS["label_spec_strength"], (0.0, 3.0)))

    # AB08: the dialog is no longer allowed to end the run. AB07 raised in here
    # before the dialog appeared and the whole script became unrunnable. If it
    # fails again, say so plainly, name the workaround, and carry on with
    # DEFAULT_OPTIONS -- none of the four console reads need the dialog.
    try:
        opts = lux.getInputDialog(
            title="Procedural Material Generator (AB08)",
            desc="Tick the layers you want, pick a base + wear + finish, and click OK. "
                 "(Part-size-aware texture scaling -- enter your Part size in mm "
                 "for correct feature sizes, or leave 0 to auto-measure. Textures "
                 "map Center On: Part, not the whole model. Optional emulated "
                 "image label -- tick 'Add an emulated image label' and point the "
                 "three path fields at PNGs on THIS machine; leave a field as "
                 "'none' to skip that channel, or leave the label off entirely "
                 "for a plain material.)",
            values=values,
            id="procedural_material_generator_dialog",
        )
    except Exception as e:
        print("  [warn] the input dialog failed to open: {0}: {1}".format(
            type(e).__name__, e))
        print("  [warn] running on DEFAULT_OPTIONS instead -- the run continues, but "
              "nothing you would have typed is being used. To steer it, edit "
              "DEFAULT_OPTIONS near the top of this file (part_size_mm especially) "
              "and set USE_DIALOG = False to skip this dialog cleanly.")
        print("  [warn] PLEASE PASTE THE TWO LINES ABOVE BACK -- the exception name "
              "is what identifies which dialog field this build refuses.")
        return dict(DEFAULT_OPTIONS)

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
    # AB08: "none", "-", blank and stray whitespace all mean "skip this channel".
    for key in ("label_opacity_path", "label_bump_path", "label_spec_path"):
        opts[key] = normalise_label_path(opts.get(key))
    return opts


# --------------------------------------------------------------------------
# Node/parameter helpers (all non-fatal)
# --------------------------------------------------------------------------







# AB04: family-specific shader fallback chains. NONE of the new constants
# (SHADER_TYPE_DIELECTRIC/GLASS/SOLID_GLASS, SHADER_TYPE_THIN_FILM) are probed on
# the real build -- resolve_shader tries them in order via getattr and drops to a
# working opaque shader (Plastic then Metal) with a logged note if all are absent.
FAMILY_SHADER_FALLBACKS = {
    "dielectric": ["SHADER_TYPE_DIELECTRIC", "SHADER_TYPE_GLASS", "SHADER_TYPE_SOLID_GLASS"],
    "thinfilm":   ["SHADER_TYPE_THIN_FILM"],
    # AB07: anisotropy is a SHADER, not a parameter. METAL has no anisotropy
    # param (probed), so metal_aniso rows must be built on ANISOTROPIC, which
    # exposes roughness_x / roughness_y / angle. Falls back to METAL (a plain
    # non-directional metal) if the constant is missing on some build.
    "metal_aniso": ["SHADER_TYPE_ANISOTROPIC", "SHADER_TYPE_METAL"],
}

# Families whose base shader is REPLACED rather than merely refined. For these,
# resolve_shader ignores the MATERIALS row's own shader and leads with the
# family chain above.
FAMILY_OVERRIDES_SHADER = ("metal_aniso",)


# AB09: the attribute name resolve_shader() last actually built on. The SPEC used
# to echo the MATERIALS row instead, so a metal_aniso row reported
# SHADER_TYPE_METAL while building on SHADER_TYPE_ANISOTROPIC.
LAST_SHADER_ATTR = None


def resolve_shader(shader_attr, family="opaque"):
    """Resolve a base-material shader by attribute name, falling back through the
    family's alternates (AB04) and then to Plastic/Metal, so an unknown constant
    (e.g. SHADER_TYPE_PAINT, or the new SHADER_TYPE_DIELECTRIC / SHADER_TYPE_THIN_FILM
    on a build that lacks them) degrades to a working material instead of crashing.
    For an opaque row this is identical to AB03 (chain = shader, Plastic, Metal)."""
    if family in FAMILY_OVERRIDES_SHADER:
        # The row says METAL, but this family needs a different BRDF entirely.
        chain = []
    else:
        chain = [shader_attr]
    for alt in FAMILY_SHADER_FALLBACKS.get(family, []):
        if alt not in chain:
            chain.append(alt)
    if shader_attr not in chain:
        chain.append(shader_attr)
    # Thin film prefers a Metal fallback (an iridescent coating still reads best on
    # a metal base); everything else prefers Plastic first. Both end at Metal.
    tail = ["SHADER_TYPE_METAL", "SHADER_TYPE_PLASTIC"] if family == "thinfilm" \
        else ["SHADER_TYPE_PLASTIC", "SHADER_TYPE_METAL"]
    for a in tail:
        if a not in chain:
            chain.append(a)
    global LAST_SHADER_ATTR
    for attr in chain:
        st = getattr(lux, attr, None)
        if st is not None:
            LAST_SHADER_ATTR = attr
            if attr != shader_attr:
                # AB09: distinguish a DELIBERATE family override from a genuinely
                # missing constant. The old wording claimed SHADER_TYPE_METAL was
                # absent on a build that plainly has it.
                if family in FAMILY_OVERRIDES_SHADER and chain and attr == chain[0]:
                    print("  [info] family '{0}' overrides the row's {1} -- building on {2} "
                          "(different BRDF, deliberate)".format(family, shader_attr, attr))
                else:
                    print("  [warn] {0} unavailable on this build -- using {1} instead".format(
                        shader_attr, attr))
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
        # PROBED 2026-07-28: SHADER_TYPE_METAL has NO anisotropy parameter at all
        # -- its 14 params are colour / roughness / film_* / metal_type. AB06 set
        # "anisotropy" and "angle" on METAL and both matched nothing, so
        # anisotropic metal never did anything. Real anisotropy lives on
        # SHADER_TYPE_ANISOTROPIC as roughness_x / roughness_y / angle, which is a
        # different BASE SHADER, not a parameter -- resolve_shader() now returns it
        # for this family. Split roughness into x/y around the base value: the
        # wider the split, the stronger the directional stretch.
        aniso = clamp01(as_float(extra.get("anisotropy"), 0.5))
        base_r = clampf(as_float(extra.get("base_roughness"), 0.25), 0.01, 1.0)
        set_display(base_node, ["roughness x"], clampf(base_r * (1.0 - 0.8 * aniso), 0.005, 1.0))
        set_display(base_node, ["roughness y"], clampf(base_r * (1.0 + 2.0 * aniso), 0.005, 1.0))
        # Angle: the Scratches direction_field is a type-2 enum (not a degree
        # value), so we deliberately do NOT read it. Pick a STABLE per-build angle
        # from the placement RNG and record it, so the brush highlight has a
        # consistent (reproducible) per-material orientation. CONFIRM AT RENDER:
        # the "anisotropy angle" display name (degrees vs 0-1 is unprobed).
        angle = extra.get("aniso_angle")
        if angle is None:
            angle = rng.uniform(0.0, 180.0)
        extra["aniso_angle_used"] = angle
        set_display(base_node, ["angle"], angle)
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
            # PROBED 2026-07-28: DIELECTRIC has no "refraction roughness". The
            # real name is roughness_transmission / "Roughness Transmission", so
            # AB06's call matched nothing and clear vs frosted glass built
            # IDENTICALLY. Both names kept, real one first.
            set_display(base_node, ["roughness transmission", "refraction roughness"], frost)
        # Absorption / tint is via the base colour input (set in build_material).
    elif family == "thinfilm":
        set_display(base_node, ["thickness", "film thickness"],
                    clampf(as_float(extra.get("film_thickness"), 500.0), 1.0, 2000.0))
        set_display(base_node, ["index of refraction", "ior"],
                    clampf(as_float(extra.get("film_ior"), 1.4), 1.0, 3.0))
    return family














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




















# --------------------------------------------------------------------------
# Masking (targeted wear) -- Curvature/Occlusion mask onto a bump layer's
# bump-height. Node ids confirmed (11.0 lux ref); input-slot names discovered
# at run time; any wiring failure degrades to the unmasked effect so masking
# can never break the base material. See MWR-9C4E21. (Unchanged from AB01.)
# --------------------------------------------------------------------------









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


def make_occlusion_roughness_node(graph, base_roughness, radius_mm=None):
    """Create an Occlusion node as a ROUGHNESS-bus source (crevice grime -> rougher
    in cavities, base roughness on exposed faces). Returns the node (not wired);
    None if unavailable. Occluded/unoccluded colour param names vary by build;
    best-effort -- if they aren't set it degrades to the node's defaults."""
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (roughness/grime source)")
    if n is not None:
        # AB15: millimetres, via the shared converter (panel is in mm).
        if radius_mm is not None:
            set_radius_mode(n, False, radius_mm, 4.0, "occlusion roughness")
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
# Image-label (emulated) -- AB06. Self-probing image-map node + the three-channel
# apply (bump + spec via the proven buses, then a guarded masked colour overlay).
# EVERY node/param/path is UNPROBED -> getattr/find_param/try-except; a miss logs
# and the plain material still builds. The human render loop is the API probe, so
# the created image-map node is DEBUG-dumped (dump_node) to reveal the real API.
# --------------------------------------------------------------------------





def _apply_label_colour_overlay(graph, base_node, base_color, opacity_path, label_scale):
    """HIGHER-RISK colour channel (done LAST + fully guarded). Composite the label
    COLOUR (source) over the base colour (background) via a Color Composite (blend
    Normal), with the label ALPHA best-effort wired into the Composite's PURE
    clipping_mask, then drive the BASE COLOUR input with the composite.

    CRITICAL: the label alpha is wired ONLY into clipping_mask, NEVER into the base
    opacity/transparency input -- wiring alpha into opacity would make the whole PART
    transparent where the label isn't. The graphic lands on base COLOUR via the mask.

    Any failure logs "[info] label colour overlay skipped -- bump/spec still applied"
    and returns without touching the (already-wired) bump/spec channels."""
    label_node = make_image_map(graph, opacity_path, "label colour", label_scale)
    if label_node is None:
        print("  [info] label colour overlay skipped -- no image-map node; bump/spec still applied")
        return
    comp = try_new_node(graph, "SHADER_TYPE_COLOR_COMPOSITE", "Color Composite (label overlay)")
    if comp is None:
        print("  [info] label colour overlay skipped -- Color Composite unavailable; bump/spec still applied")
        return
    src_name, bg_name = _composite_inputs(comp)
    if not src_name or not bg_name:
        print("  [info] label colour overlay skipped -- Composite Source/Background inputs "
              "not found (see dump); bump/spec still applied")
        try:
            graph.removeNode(comp)
        except Exception:
            pass
        return
    # source = label image node.
    safe_edge(graph, source=label_node, target=comp, param=src_name, label="label overlay source")
    # background = base colour: prefer a plain colour node, else set the Background
    # colour VALUE directly (a type-14 input carries a settable colour value too).
    bg_ok = False
    colour_node = _make_colour_node(graph, base_color)
    if colour_node is not None:
        bg_ok = safe_edge(graph, source=colour_node, target=comp, param=bg_name,
                          label="label overlay background")
    if not bg_ok:
        # Background is a type-14 connection input that also carries a settable
        # colour VALUE -- match by name, no PT_COLOR (type-13) filter.
        bg_ok = set_display(comp, ["background", "base", "bottom"], base_color)
    if not bg_ok:
        # Without a base-colour background the composite would blacken every
        # non-label area of the part -- refuse the overlay rather than wreck the base.
        print("  [info] label colour overlay skipped -- couldn't set the base colour as the "
              "composite background (would blacken non-label areas); bump/spec still applied")
        try:
            graph.removeNode(comp)
        except Exception:
            pass
        return
    # Blend mode Normal (label sits on top where the mask is white; base shows through
    # where it's black). Normal is index 0 in KeyShot's documented blend list.
    set_blend_mode(comp, "Normal", 0)
    # Label ALPHA -> clipping_mask (PURE type-14 input). Best-effort: wire the label
    # image node into the mask so the composite only shows the label where alpha is
    # opaque. This is the ONLY place the alpha is used -- never base opacity.
    cm = find_param(comp, ["clipping mask", "clip mask", "mask"])
    if cm is not None:
        ok_mask = safe_edge(graph, source=label_node, target=comp, param=cm.getName(),
                            label="label alpha -> clipping_mask")
        if not ok_mask:
            print("  [info] label overlay: alpha not wired into clipping_mask -- the label's "
                  "own alpha may still apply; base opacity is untouched")
    else:
        print("  [info] label overlay: no clipping_mask input on this Composite -- the label's "
              "own alpha may still apply; base opacity is untouched")
    # Drive the BASE COLOUR input with the composite.
    p = find_param(base_node, ["color", "diffuse", "base color"])
    if p is None:
        print("  [info] label colour overlay skipped -- base has no colour input to drive; "
              "bump/spec still applied")
        try:
            graph.removeNode(comp)
        except Exception:
            pass
        return
    ok = safe_edge(graph, source=comp, target=base_node, param=p.getName(),
                   label="label composite -> base.color")
    if ok:
        # AB27/RNK-0257: "the call was accepted", not "LANDED". safe_edge has
        # just printed the verdict for this same edge with the target's real
        # type; this line only adds what the overlay is FOR.
        print("  [info] label colour overlay: call accepted -- masked label colour over "
              "base colour (blend Normal, alpha -> clipping_mask, base opacity untouched). "
              "The WIRED / UNVERIFIED verdict for it is the line above.")
    else:
        print("  [info] label colour overlay skipped -- couldn't wire composite into base "
              "colour; bump/spec still applied")
        try:
            graph.removeNode(comp)
        except Exception:
            pass


def apply_image_label(graph, base_node, base_color, label, bump_sources, rough_sources):
    """AB06 emulated image-label. Contributes an image-map node to the bump bus and
    the roughness bus (by APPENDING to the passed `bump_sources` / `rough_sources`
    lists BEFORE either bus is combined), then does the higher-risk masked colour
    overlay LAST. `label` is the validated spec['label'] dict. Fully non-fatal:
    every channel is independent and guarded, and the plain material still builds if
    any channel can't wire. An empty channel path skips that channel."""
    opacity_path = label.get("opacity_path", "") or ""
    bump_path = label.get("bump_path", "") or ""
    spec_path = label.get("spec_path", "") or ""
    label_scale = as_float(label.get("scale"), 1.0)
    bump_strength = as_float(label.get("bump_strength"), 1.0)
    spec_strength = as_float(label.get("spec_strength"), 1.0)

    # 1. BUMP channel (LOW RISK -- rides the proven bump bus). Append BEFORE
    #    combine_bump_sources so the label bump combines with the other bump layers.
    if bump_path:
        bnode = make_image_map(graph, bump_path, "label bump", label_scale)
        if bnode is not None:
            bh = find_param(bnode, ["bump height", "height"])
            if bh is not None and not bh.isPure():
                cur = None
                try:
                    cur = bh.getValue()
                except Exception:
                    cur = None
                base_h = cur if (isinstance(cur, (int, float)) and not isinstance(cur, bool)
                                 and cur) else 1.0
                set_display(bnode, ["bump height", "height"], base_h * bump_strength)
                print("  [info] label bump -> bump bus (strength {0})".format(bump_strength))
            else:
                print("  [info] label bump has no bump-height param -- wired as-is "
                      "(strength ignored)")
            bump_sources.append(bnode)
        else:
            print("  [info] label bump channel skipped -- no image-map node")

    # 2. SPEC channel (LOW RISK -- rides the roughness bus, composites via Lighten).
    #    Append BEFORE the roughness bus builds.
    if spec_path:
        snode = make_image_map(graph, spec_path, "label spec", label_scale)
        if snode is not None:
            applied = False
            for kw in (["contrast"], ["strength"], ["gain"]):
                p = find_param(snode, kw)
                if p is not None and not p.isPure():
                    set_display(snode, kw, spec_strength)
                    applied = True
                    break
            if applied:
                print("  [info] label spec -> roughness bus (strength {0})".format(spec_strength))
            else:
                print("  [info] label spec has no strength/contrast param -- wired as-is")
            rough_sources.append(snode)
        else:
            print("  [info] label spec channel skipped -- no image-map node")

    # 3. COLOUR overlay (HIGHER RISK -- LAST, fully guarded). Does NOT touch the
    #    already-appended bump/spec channels if it fails.
    if opacity_path:
        try:
            _apply_label_colour_overlay(graph, base_node, base_color, opacity_path, label_scale)
        except Exception as e:
            print("  [info] label colour overlay skipped ({0}) -- bump/spec still applied".format(e))


# --------------------------------------------------------------------------
# Post-build wire audit (MDD-4B7A9F sec 7) -- optional/defensive
# --------------------------------------------------------------------------



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
    part_size, size_source, units_to_mm = resolve_part_size(opts, name_filter)

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
            # AB10: the load-bearing figure, in SCENE units (what texture Scale
            # takes). part_size_mm is the real-world number kept for the record;
            # units_to_mm is this scene's derived unit, or null.
            "part_extent_scene": part_size,
            "part_size_mm": as_float(opts.get("part_size_mm"), 0.0) or None,
            "units_to_mm": units_to_mm,
            "scale_factor": as_float(opts.get("scale_factor"), TEXTURE_SCALE_FACTOR),
            "source": size_source,
            # AB14: mask reach in REAL millimetres, converted to scene units at
            # build time. A radius is not a fraction of the part -- see the
            # AB14 header block.
            "edge_radius_mm": as_float(opts.get("edge_radius_mm"),
                                       EDGE_MASK_RADIUS_MM),
            "cavity_radius_mm": as_float(opts.get("cavity_radius_mm"),
                                         CAVITY_MASK_RADIUS_MM),
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
        # AB06: emulated image-label config. Captured whether or not enabled so the
        # emitted spec fully reproduces the build. An empty channel path skips that
        # channel. Clamped in validate_spec.
        "label": {
            "enabled": bool(opts.get("enable_labels", DEFAULT_OPTIONS["enable_labels"])),
            "opacity_path": normalise_label_path(
                opts.get("label_opacity_path", DEFAULT_OPTIONS["label_opacity_path"])),
            "bump_path": normalise_label_path(
                opts.get("label_bump_path", DEFAULT_OPTIONS["label_bump_path"])),
            "spec_path": normalise_label_path(
                opts.get("label_spec_path", DEFAULT_OPTIONS["label_spec_path"])),
            "scale": as_float(opts.get("label_scale"), DEFAULT_OPTIONS["label_scale"]),
            "bump_strength": as_float(opts.get("label_bump_strength"),
                                      DEFAULT_OPTIONS["label_bump_strength"]),
            "spec_strength": as_float(opts.get("label_spec_strength"),
                                      DEFAULT_OPTIONS["label_spec_strength"]),
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
    # AB10: the load-bearing number is the extent in SCENE units. part_size_mm is
    # the operator's real-world figure, carried for the record only.
    extent = as_float(scale.get("part_extent_scene"), DEFAULT_PART_EXTENT)
    if extent <= 0.0:
        extent = DEFAULT_PART_EXTENT
    scale["part_extent_scene"] = extent
    scale.setdefault("source", "default")
    scale.setdefault("part_size_mm", None)
    scale.setdefault("units_to_mm", None)

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

    # AB06: sanity-check + clamp the emulated image-label block (defensive -- all
    # optional + coerced). Paths coerced to strings (non-strings dropped to empty ->
    # that channel is skipped); scale [0.1,10.0]; strengths [0,3]. Kept on the spec
    # so the emitted spec stays reproducible.
    label = spec.setdefault("label", {})
    label["enabled"] = bool(label.get("enabled", False))
    for k in ("opacity_path", "bump_path", "spec_path"):
        v = label.get(k, "")
        label[k] = v if isinstance(v, str) else ""
    label["scale"] = clampf(as_float(label.get("scale"), 1.0), 0.1, 10.0)
    label["bump_strength"] = clampf(as_float(label.get("bump_strength"), 1.0), 0.0, 3.0)
    label["spec_strength"] = clampf(as_float(label.get("spec_strength"), 1.0), 0.0, 3.0)

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
    # AB06: emulated image-label config (a dict; enabled gates the whole feature).
    label = spec.get("label", {}) or {}
    labels_on = bool(label.get("enabled"))

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
    part_size = as_float(scale_info.get("part_extent_scene"), DEFAULT_PART_EXTENT)
    if part_size <= 0.0:
        part_size = DEFAULT_PART_EXTENT
    size_source = scale_info.get("source", "default")
    # AB11: fraction of the measured extent, THEN the bbox-unit -> Scale-unit
    # conversion. Without the second step the panel reads 1000x these numbers.
    # AB31 / RNK-0292: this substituted a sane factor SILENTLY, which is the same
    # class of failure as the mask viewer's zero even though the outcome was
    # benign here. `resolve_scale_factor` is the one shared rule and it says so
    # when it substitutes.
    factor = resolve_scale_factor(scale_info.get("scale_factor"))
    tex_scales = {
        "fine_noise": part_size * SCALE_FRACTIONS["fine_noise"] * factor,
        "scratches": part_size * SCALE_FRACTIONS["scratch_scale"] * factor,
        "fractal": part_size * SCALE_FRACTIONS["fractal"] * factor,
        "cellular": part_size * SCALE_FRACTIONS["cellular"] * factor,
        "spots": part_size * SCALE_FRACTIONS["spots_scale"] * factor,
    }

    # AB14: mask reach in scene units, converted from real millimetres. NOT
    # multiplied by `factor` -- that conversion belongs to texture Scale
    # parameters, and a radius is a different parameter in a different unit.
    # AB15: a radius is MILLIMETRES and nothing else. The Curvature/Occlusion
    # panel is in mm, so the value does not depend on the part's scene-unit
    # scale -- `mm_to_scene`, added in AB14 for exactly this, turned out to be
    # solving a problem that is not on this path. Texture SCALE below is still
    # part-relative; the two are different quantities and stay different.
    SCENE_MM_PER_UNIT_LIVE[0] = scale_info.get("units_to_mm")
    # AB17: the part's real size, so a radius bigger than the object clamps and
    # says so instead of washing the whole surface (the 2026-07-31 cube run asked
    # for 17 mm of grime radius on a 10 mm cube and got a uniformly brown part).
    PART_MM_LIVE[0] = resolve_part_mm(scale_info)
    print("  Scale: panel should read {0} mm (scratches) and {1} mm (spots). "
          "Masked wear reads between 0.01 and 0.05 mm on a 10 mm part "
          "(bench-measured 2026-07-31); well outside that and the mask comes "
          "back black.".format(
              round(texture_scale_to_mm(tex_scales["scratches"]), 5),
              round(texture_scale_to_mm(tex_scales["spots"]), 5)))
    edge_radius_mm = as_float(scale_info.get("edge_radius_mm"), EDGE_MASK_RADIUS_MM)
    cavity_radius_mm = as_float(scale_info.get("cavity_radius_mm"),
                                CAVITY_MASK_RADIUS_MM)

    # AB04: family + its shader params (opaque rows carry {} -> family "opaque").
    extra = base.get("extra", {}) or {}
    family = material_family(extra)

    shader_type = resolve_shader(base["shader"], family)
    # AB09: record what was really built, so the SPEC line cannot misreport it.
    spec["base"]["shader_used"] = LAST_SHADER_ATTR or base["shader"]
    if spec["base"]["shader_used"] != base["shader"]:
        print("  Shader: requested {0} -> built on {1}".format(
            base["shader"], spec["base"]["shader_used"]))
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
    units_to_mm = spec.get("scale", {}).get("units_to_mm")
    panel = dict((k, v / factor) for k, v in tex_scales.items())
    real_note = ""
    if units_to_mm:
        real_note = " = {0} mm real".format(round(part_size * units_to_mm, 2))
    print("  Scale: part {0} scene units ({1}){2}".format(
        part_size, size_source, real_note))
    print("         written -> scratches {0}, fine {1}, fractal {2}, cellular {3}, "
          "spots {4}".format(
              tex_scales["scratches"], tex_scales["fine_noise"], tex_scales["fractal"],
              tex_scales["cellular"], tex_scales["spots"]))
    print("         the texture panel should read -> scratches {0}, fine {1}, "
          "fractal {2}, cellular {3}, spots {4} (x{5} factor, Center On: Part)".format(
              round(panel["scratches"], 4), round(panel["fine_noise"], 4),
              round(panel["fractal"], 4), round(panel["cellular"], 4),
              round(panel["spots"], 4), factor))
    print("         if the panel shows 1000x these, TEXTURE_SCALE_FACTOR is wrong "
          "for this build -- change the one dialog field, not the code")
    if labels_on:
        print("  Labels: ENABLED (emulated) -- opacity={0}, bump={1}, spec={2}; "
              "scale={3}, bump_strength={4}, spec_strength={5}".format(
                  repr(label.get("opacity_path", "")), repr(label.get("bump_path", "")),
                  repr(label.get("spec_path", "")), label.get("scale"),
                  label.get("bump_strength"), label.get("spec_strength")))
    else:
        print("  Labels: disabled (set enable_labels to wire an emulated image label)")

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
        # AB07: the anisotropic split needs the row's base roughness to widen
        # around, and extra{} is the only channel into apply_family_params.
        extra["base_roughness"] = spec["base"]["roughness"]
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
            mask_bump_layer(graph, scratches_node, add_curvature_mask(graph, edge_radius_mm),
                            "scratches->edges")
        bump_sources.append(scratches_node)
    if features["add_rounded_edges"]:
        # Rounded Edges is a geometry-based bump, not a tiling texture -- no
        # placement randomisation (nothing to de-repeat) and no Center On / Scale.
        bump_sources.append(add_rounded_edges_bump(graph, wear_mult, damping))
    if features["add_spots"]:
        sp = add_spots_bump(graph, wear_mult, damping, tex_scales["spots"])
        randomize_placement(sp, placement_rng, "spots", tex_scales["spots"])
        if masks.get("mask_spots_to_cavities"):
            sp = mask_bump_layer(graph, sp, add_occlusion_mask(graph, cavity_radius_mm),
                                 "spots->cavities")
        bump_sources.append(sp)
    if features["add_cellular"]:
        cell_node = add_cellular_bump(graph, wear_mult, damping, tex_scales["cellular"])
        randomize_placement(cell_node, placement_rng, "cellular", tex_scales["cellular"])
        bump_sources.append(cell_node)

    # --- ROUGHNESS SOURCES (assembled BEFORE the bump combine so AB06 labels can
    #     contribute to BOTH buses in one apply_image_label pass) ----------------
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
        oc = make_occlusion_roughness_node(graph, base_roughness, cavity_radius_mm)
        if oc is not None:
            # Occlusion has no tiling scale, but its bias_x/y/z DO offset the AO
            # sampling (confirmed in the AB02 dump) -- FIX 2 jitters those so even
            # the crevice-grime source varies per material instead of being global.
            randomize_placement(oc, placement_rng, "occlusion")
            rough_sources.append(oc)

    # --- AB06 IMAGE LABEL (emulated) ----------------------------------------
    # Contributes a bump image-map to bump_sources and a spec image-map to
    # rough_sources BEFORE either bus is combined (so the label rides the proven
    # buses), then does the higher-risk masked colour overlay LAST. All UNPROBED +
    # guarded: if any channel can't wire, the plain material still builds. Runs only
    # when enable_labels is set.
    if labels_on:
        apply_image_label(graph, base_node, base_color, label, bump_sources, rough_sources)

    # --- BUMP BUS: combine all bump-domain layers (incl. the label bump) into
    #     one bump input -------------------------------------------------------
    combined_bump = combine_bump_sources(graph, bump_sources)
    if combined_bump is not None:
        base_bump_slots = connection_param_names(base_node, PT_SHADERBUMP)
        if base_bump_slots:
            safe_edge(graph, source=combined_bump, target=base_node, param=base_bump_slots[0],
                      label="combined bump -> base.bump")
        else:
            print("  [warn] base material has no bump input")

    # --- ROUGHNESS BUS: composite all roughness sources (incl. the label spec)
    #     into the one roughness input via Lighten ------------------------------
    rough_mode = build_roughness_bus(graph, base_node, rough_sources)
    print("  Roughness bus: {0} source(s) -> mode '{1}'".format(len(rough_sources), rough_mode))

    # --- COLOUR BUS: base colour + optional gradient driver (single) --------
    if features["add_color_gradient"]:
        add_color_gradient(graph, base_node, base_color)

    # --- post-build wire audit (silent-edge-failure guard) ------------------
    wire_audit(base_node, "base")

    print("Built material graph: {0}".format(name))
    return graph, name








if __name__ == "__main__":
    options = get_options()
    perf_on = check_performance_mode()
    if options is None:
        print("Cancelled -- nothing built.")
    else:
        set_center_on_override(options.get("center_on_int",
                                           DEFAULT_OPTIONS["center_on_int"]))
        spec = validate_spec(sample_spec(options))
        graph, material_name = build_material(spec)
        emit_spec(spec)  # emitted after build so meta.name reflects the final name
        apply_material_to_parts(material_name, name_filter=spec["application"]["name_filter"])