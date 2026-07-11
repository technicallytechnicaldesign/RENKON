# AUTHOR tajf
# REV AA01
# HEADLESS COMPLIANT
"""
KeyShot Assembly Reveal — Procedural Modes
================================================

Animates an assembly's OWN PARTS converging into their authored final
positions -- the camera is static (or on a simple Studio/Camera selection,
same as the sibling scripts) and never moves. This is the parts-move
counterpart to 2b_ANI_HERO_REVEAL_AA01.py (camera moves, parts don't) and
2b_ANI_CUTAWAY_REVEAL_AA01.py (a clip plane sweeps, parts don't) -- three
different shot types kept as separate scripts on purpose, same reasoning as
the cutaway script's header: different motion, different failure modes.

Four selectable procedural modes (no Creo explode-state import needed --
see the P1 "Creo-driven" backlog item in SCRIPT_STOCK.md for that separate,
not-yet-started sibling):

  scatter_settle  -- every part starts scattered to a randomized offset
                     (and optionally a randomized rotation) relative to its
                     own authored final position; the shot watches them
                     settle home in a straight line.
  staggered_build -- parts arrive one at a time in assembly order
                     (stop-motion style): each part is off-frame until its
                     own window starts, then eases in and holds.
  spiral_converge -- same start -> final convergence as scatter_settle, but
                     the path curves: a perpendicular spiral offset is added
                     on top of the straight-line path and decays to zero by
                     t=1, so the part still lands exactly on its authored
                     final transform.
  ghost_fade       -- parts never move (they sit in their final position
                     for the whole shot) and instead fade in from
                     transparent to full opacity.

--------------------------------------------------------------------------
TRANSFORM MECHANICS -- READ THIS BEFORE TRUSTING THE OUTPUT
--------------------------------------------------------------------------
The only CONFIRMED per-node transform mutator anywhere in this pipeline is
the RELATIVE call node.applyTransform(matrix, absolute=False), used
experimentally for the product-turntable spin in
2b_ANI_HERO_REVEAL_AA01.py (search that file for "applyTransform"). There
is no confirmed ABSOLUTE get/set-position API for a scene node anywhere in
this codebase's history -- so this script never tries to "set" a part's
position directly. Instead:

  - Every part's motion is expressed as a DISPLACEMENT FUNCTION of the
    shot's progress t in [0, 1], always defined so displacement(t=1) is
    exactly the zero vector / zero degrees -- the same "zero at t=1"
    discipline as compute_vertical_offset() in the hero reveal script
    (that function's whole point is that the crane move always lands
    exactly on the hero framing regardless of amount/direction; the same
    idea here guarantees a part always lands exactly on its authored
    final position/orientation regardless of scatter radius or spiral
    turns).
  - Each frame, this script computes displacement(t_now) - displacement
    (t_previous) and applies ONLY that incremental delta via
    node.applyTransform(delta_matrix, absolute=False) -- never the full
    displacement. Because the deltas are relative and composed frame over
    frame, their sum telescopes back to exactly -displacement(t=0), i.e.
    net zero over the whole shot, by construction (not by measurement --
    there is no confirmed readback API to verify a node's live position,
    so this is trusted arithmetic, not a verified result).
  - luxmath.Matrix() is used to build each delta, mirroring the
    `luxmath.Matrix().makeIdentity().rotate(delta_deg, axis_v)` pattern in
    the hero reveal script's turntable section. Translation deltas use
    this repo's plain vec_xyz/vadd/vsub/vscale/vlen/vnorm helpers, copied
    verbatim from that same script.
  - Rotation deltas are only ever applied about a SINGLE FIXED AXIS per
    part (scatter_settle's optional randomized spin). Rotations about a
    fixed axis compose additively in angle, so summing per-frame deltas
    is safe; this script does NOT attempt multi-axis rotation composition
    anywhere, since that would not commute the same way and the drift
    risk would be much higher.
  - Composing MANY sequential relative transforms -- one delta per frame,
    per part, potentially dozens of parts across dozens of frames -- is a
    genuinely NOVEL use of applyTransform(absolute=False) in this
    pipeline; nothing else here has driven it at this scale. Some float
    drift over many frames is plausible. Mitigation: on the final frame of
    each part's motion, this script tracks its own running total of
    everything it has told KeyShot to apply (translation vector sum +
    rotation angle sum) and issues one more small corrective delta equal
    to the negative of that running total. This is a BEST-EFFORT
    re-assertion based on this script's own bookkeeping of what it asked
    KeyShot to do -- NOT a true readback-based correction (there is no
    confirmed getPosition()/getRotation() to verify against), mirroring
    the spirit, not the letter, of the hero reveal script's "restore
    exact hero state" step at the end of shoot_one_reveal().
  - luxmath.Matrix().translate(vector) is assumed to exist by the SAME
    naming-convention analogy the hero reveal script uses for
    env.setRotation() and this pipeline's other getX/setX-pairing
    inferences -- but unlike .rotate(), which is at least already in use
    (experimentally) elsewhere in this pipeline, .translate() has NEVER
    been called anywhere in this codebase before. Treat it as a pure
    guess, probed defensively via getattr(...) exactly like every other
    unconfirmed candidate in this file, and gracefully degraded (a part
    just won't translate on this KeyShot build) if it doesn't exist.

--------------------------------------------------------------------------
PART EXTENT / SCATTER SCALE
--------------------------------------------------------------------------
Scatter/spiral offsets need to scale with each part's own size so small
parts don't fly absurdly far and large parts don't clip through their
neighbors. The only confirmed spatial query available anywhere in this
pipeline is SceneNode.getCenter(world=True) (a point, not an extent). A
bounding-box GETTER would give a proper extent but is NOT confirmed --
resolve_bounding_box() below is copied from 2b_ANI_CUTAWAY_REVEAL_AA01.py's
identical probe (same candidate list: getBoundingBox(world=True),
getBoundingBox(), getWorldBoundingBox(), getBounds(world=True),
getBounds()), since that script already worked out the defensive shape-
parsing needed for whatever a bounding-box call returns. If NONE of those
resolve on this KeyShot build, this script falls back to a much cruder
estimate -- the part's own center-to-scene-origin distance, scaled by
extent_fallback_mult -- which is a genuinely worse proxy for "how big is
this part" but at least keeps every part's scatter radius in the same
rough ballpark as its distance from the rest of the assembly, with a loud
one-time warning that per-part sizing wasn't available.

--------------------------------------------------------------------------
SUB-ASSEMBLY BUILD (OUT OF SCOPE)
--------------------------------------------------------------------------
"Sub-assemblies converge as groups before the groups converge to final" is
a larger follow-on backlog item (RESEARCH_CREO_KEYSHOT.md) building on this
script and is deliberately NOT implemented here. The natural extension
point is in get_parts()/schedule_staggered_windows() below: grouping parts
by parent node (root.find() results already carry scene-tree structure)
before flattening to the current per-part list is where a sub-assembly
tier would slot in, without needing to change the per-frame transform
mechanics above at all.

--------------------------------------------------------------------------
GHOST FADE / OPACITY -- READ THIS BEFORE TRUSTING THE OUTPUT
--------------------------------------------------------------------------
Object/material opacity control has NEVER been used anywhere in this
pipeline; there is no confirmed API for it at all. Every candidate method
name tried below is unconfirmed/experimental, treated with the exact same
discipline as set_ground_rendering() in the hero reveal script and the
clip-plane probing in the cutaway script: short candidate lists, tried via
getattr(obj, name, None) so a missing name is skipped rather than raising,
and whichever one actually works is reported once. Two layers are probed:

  1. NODE-level opacity setters directly on the SceneNode: setOpacity,
     setTransparency, setAlpha.
  2. MATERIAL-level setters, reached via a settable material OBJECT rather
     than the material name STRING that node.getMaterial() is already
     confirmed to return elsewhere in this pipeline (see
     1_HLP_MAT_PREFLIGHT_AA01.py: `results[node.getName()] =
     node.getMaterial()` -- that's a name, not an object, so it is NOT
     reused here for opacity). Instead this probes a short list of
     plausible OBJECT-returning accessors -- getMaterialNode,
     getAppearance, getMaterialObject, getMaterialGraph -- and, only if
     one of those returns something, tries the same setOpacity/
     setTransparency/setAlpha candidates on THAT object instead.

If nothing resolves on either layer for a given part, this script warns
ONCE (not once per part -- that would spam a large assembly) and falls
back to a hard cut: since ghost_fade parts never move, "no working opacity
API" simply means the part is visible for the whole shot instead of fading
in, which is what naturally happens if no opacity call is ever made --
rather than silently doing nothing and calling it a fade.

--------------------------------------------------------------------------
STUDIOS vs CAMERAS
--------------------------------------------------------------------------
Copied verbatim from the hero reveal / cutaway scripts' approach: a Studio
pairs a camera with its matching environment/lighting (and image style) --
confirmed: lux.getStudios(), lux.getStudio(name), lux.setActiveStudio(name).
Where a target name matches a Studio, this script activates the Studio; a
plain camera name just switches the camera and leaves whatever environment
is already active. The camera itself is never moved once activated -- only
the assembly's own parts (or their opacity) animate.

--------------------------------------------------------------------------
GROUND RENDERING
--------------------------------------------------------------------------
Same situation and same defensive candidate-list treatment as the hero
reveal / cutaway scripts: ground shadow/reflection getters are confirmed,
the exact setter names aren't, so a short list of plausible setter names is
tried and whichever one worked is reported. set_ground_rendering() below is
a direct copy of the sibling scripts' version.

--------------------------------------------------------------------------
QUEUEING
--------------------------------------------------------------------------
Same as the sibling scripts: "add to queue" adds every rendered frame, for
every camera, to KeyShot's render queue instead of rendering immediately. A
video can only be encoded once every frame has actually finished rendering,
so without "process queue after" this script queues everything and stops
there rather than guessing at encoding a possibly-incomplete folder.

--------------------------------------------------------------------------
CONFIRMED vs EXPERIMENTAL
--------------------------------------------------------------------------
Confirmed (KeyShot's own scripting reference, and/or already used elsewhere
in this pipeline): lux.getActiveEnvironment(), env.getBrightness/
setBrightness, env.setBackplateImage, lux.renderImage, lux.encodeVideo,
lux.openFile(), lux.getStudios(), lux.getStudio(name),
lux.setActiveStudio(name), lux.getCameras(), lux.setCamera(name),
lux.getModelSets(), lux.setModelSets(names), lux.getImportOptions(),
lux.importFile(path, opts=...), lux.getSceneTree(), root.find(...),
node.isObject(), node.getName(), SceneNode.getCenter(world=True), env
ground-state getters (isGroundShadowsEnabled-style),
lux.getRenderOptions()/setAddToQueue()/setMaxTimeRendering(),
lux.processQueue(), lux.isHeadless(), lux.getInputDialog(),
node.applyTransform(matrix, absolute=False) as a call (its use here, for a
long sequence of many small per-frame deltas across many parts, is itself
a NOVEL usage pattern not attempted elsewhere -- see TRANSFORM MECHANICS).

Inferred-but-unconfirmed, wrapped defensively throughout: env.setRotation()
(same flag as the sibling scripts), the ground shadow/reflection *setter*
names (same flag as the sibling scripts).

Experimental / entirely unverified -- flagged loudly and probed via
getattr(...) rather than called directly, degrading gracefully if nothing
resolves:
  - luxmath.Matrix().rotate(degrees, axis_vector) -- same flag already
    raised in the hero reveal script for the turntable spin; reused here
    for scatter_settle's optional randomized rotation.
  - luxmath.Matrix().translate(vector) -- NEVER used anywhere in this
    pipeline before this file; pure naming-convention guess alongside
    .rotate(). This is the single most load-bearing unconfirmed call in
    this script, since every translation-based mode depends on it.
  - Every bounding-box getter name (getBoundingBox / getWorldBoundingBox /
    getBounds, with or without a world= kwarg) -- copied from the cutaway
    script's identical, already-unconfirmed probe.
  - The entire opacity/transparency control surface used by ghost_fade:
    node-level setOpacity / setTransparency / setAlpha, and the material-
    object accessor candidates getMaterialNode / getAppearance /
    getMaterialObject / getMaterialGraph plus their own setOpacity /
    setTransparency / setAlpha candidates. None of these appear in a
    confirmed reference available to this pipeline.

Run inside the KeyShot Scripting Console, or via `keyshot -script` headless
(dialog auto-skips headless -> DEFAULT_OPTIONS is used instead).
"""

import lux
import luxmath
import math
import random
import re
import os
import csv
from datetime import datetime

DEBUG = True
FRAME_PATTERN = "assembly_frame.%d.png"

MANIFEST_FIELDS = ["timestamp", "scene_template", "target", "video_name", "output_path", "status"]

MODE_OPTIONS = ["scatter_settle", "staggered_build", "spiral_converge", "ghost_fade"]
STAGGERED_ORDER_OPTIONS = ["Scene Order", "Name"]
STAGGERED_ARRIVAL_AXES = ["X", "Y", "Z"]

AXIS_VECTORS = {
    "X": (1.0, 0.0, 0.0),
    "Y": (0.0, 1.0, 0.0),
    "Z": (0.0, 0.0, 1.0),
}

DEFAULT_OPTIONS = {
    "scene_template_path": "",
    "import_file_path": "",
    "target_model_set_name": "",
    "part_name_filter": "ALL",
    "camera_selection": "ALL",
    "mode": "scatter_settle",
    "num_frames": 90,
    "fps": 24,
    "hold_start": 4,
    "hold_end": 20,
    "random_seed": 0,
    "extent_fallback_mult": 0.5,
    # -- scatter_settle --
    "scatter_radius_mult": 3.0,
    "scatter_rotation_enabled": True,
    "scatter_rotation_max_degrees": 90.0,
    # -- staggered_build --
    "staggered_order": "Scene Order",
    "staggered_overlap_frac": 0.25,
    "staggered_arrival_axis": "Z",
    "staggered_arrival_distance_mult": 4.0,
    # -- spiral_converge --
    "spiral_turns": 1.5,
    "spiral_amplitude_mult": 1.0,
    # -- ghost_fade --
    "ghost_fade_start_opacity": 0.0,
    "ghost_fade_end_opacity": 1.0,
    # -- dynamic background / lighting --
    "render_ground": True,
    "rotate_environment": False,
    "environment_rotation_degrees": 30.0,
    "brightness_ramp": False,
    "brightness_ramp_start_mult": 0.6,
    "backplate_image": "",
    # -- rendering --
    "preview_mode": True,
    "add_to_queue": False,
    "process_queue_after": False,
    # -- output --
    "output_folder": "",
    "video_name_prefix": "ASSEMBLY",
    "width": 1920,
    "height": 1080,
    "keep_frames": False,
}


def random_suffix(n=6):
    return "".join(random.choice("0123456789ABCDEF") for _ in range(n))


def sanitize_name(name):
    """Turn a camera/Studio name into something safe for filenames/folders."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name or "").strip("_")
    return cleaned or random_suffix()


def logManifestRow(manifestPath, row):
    isNew = not os.path.isfile(manifestPath)
    with open(manifestPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)


def load_scene_template(path):
    """Load a saved KeyShot scene as the starting point for the shot.
    Confirmed: lux.openFile(). Non-fatal."""
    if not path:
        return True
    try:
        lux.openFile(path, dontAsk=True)
        print(f"Loaded scene template: {path}")
        return True
    except Exception as e:
        print(f"[warn] couldn't load scene template '{path}': {e} — "
              f"continuing with whatever scene is currently open")
        return False


def import_into_model_set(file_path, model_set_name):
    """Import a part/assembly file into a named, already-existing Model Set
    (so the parts list below has a stable target to work from). Confirmed:
    lux.getModelSets(), lux.setModelSets(), lux.getImportOptions(),
    lux.importFile(path, opts={'model_set_import_to': 1, ...}) (1 = Active).
    Does NOT create the Model Set if missing — warns and falls back to a
    plain import instead of silently doing the wrong thing."""
    if not file_path:
        return True

    try:
        existing = lux.getModelSets()
    except Exception as e:
        print(f"[warn] couldn't list model sets: {e}")
        existing = []

    if not model_set_name or model_set_name not in existing:
        if model_set_name:
            print(f"[warn] model set '{model_set_name}' not found in the loaded scene "
                  f"(found: {existing}) — importing without a specific model set target.")
        try:
            lux.importFile(file_path)
            return True
        except Exception as e:
            print(f"[error] couldn't import '{file_path}': {e}")
            return False

    try:
        ok = lux.setModelSets([model_set_name])
        if not ok:
            print(f"[warn] couldn't cleanly activate model set '{model_set_name}' — continuing anyway")
    except Exception as e:
        print(f"[warn] couldn't activate model set '{model_set_name}': {e}")

    try:
        import_opts = lux.getImportOptions()
    except Exception as e:
        print(f"[warn] couldn't get import options, using defaults: {e}")
        import_opts = {}
    import_opts["model_set_import_to"] = 1  # 1 = Active model set

    try:
        lux.importFile(file_path, opts=import_opts)
        print(f"Imported '{file_path}' into model set '{model_set_name}'")
        return True
    except Exception as e:
        print(f"[error] couldn't import '{file_path}' into '{model_set_name}': {e}")
        return False


def get_target_node(model_set_name):
    """Resolve the node the parts list is gathered from: the named model
    set if given and found, else the whole scene root. Same fallback
    pattern as get_focus_node()/get_target_node() in the sibling scripts."""
    root = lux.getSceneTree()
    if model_set_name:
        try:
            matches = root.find(name=model_set_name, types=lux.NODE_TYPE_MODEL_SET)
            if matches:
                return matches[0]
        except Exception as e:
            print(f"  [warn] couldn't find model set '{model_set_name}': {e}")
    return root


def set_ground_rendering(env, enabled):
    """Toggle the environment's ground shadow/reflection catcher. Copied
    from the sibling scripts — getters are confirmed, setter names are
    inferred by naming-convention analogy and tried defensively."""
    if env is None:
        return False
    shadow_setters = ["setGroundShadows", "enableGroundShadows", "setGroundShadowsEnabled"]
    reflection_setters = ["setGroundReflections", "enableGroundReflections", "setGroundReflectionsEnabled"]

    def try_setters(names):
        for name in names:
            fn = getattr(env, name, None)
            if fn is None:
                continue
            try:
                fn(enabled)
                return name
            except Exception:
                continue
        return None

    used_shadow = try_setters(shadow_setters)
    used_reflect = try_setters(reflection_setters)
    if not used_shadow and not used_reflect:
        print("  [warn] couldn't find a working ground shadow/reflection toggle on this KeyShot "
              "version — 'render ground' setting was not applied. Run help(env) in the Scripting "
              "Console to find the exact method name on your build.")
        return False
    if DEBUG:
        print(f"  Ground rendering set to {enabled} (via {used_shadow or '-'} / {used_reflect or '-'})")
    return True


# --------------------------------------------------------------------------
# Camera / Studio selection (copied from the sibling scripts)
# --------------------------------------------------------------------------

def resolve_camera_list(raw_value):
    """Resolve the camera_selection dialog field:
      - blank            -> None (sentinel: shoot whatever's currently active)
      - 'ALL'             -> every Studio, plus any camera not already
                              covered by a Studio
      - comma-separated   -> exactly those names (covers 'one' and 'some')
    """
    v = (raw_value or "").strip()
    if not v:
        return None
    if v.upper() == "ALL":
        try:
            studios = list(lux.getStudios())
        except Exception as e:
            print(f"[warn] couldn't list studios: {e}")
            studios = []
        covered = set()
        for s in studios:
            try:
                c = lux.getStudio(s).getCamera()
                if c:
                    covered.add(c)
            except Exception:
                continue
        try:
            cameras = lux.getCameras()
        except Exception as e:
            print(f"[warn] couldn't list cameras: {e}")
            cameras = []
        extras = [c for c in cameras if c not in covered]
        return studios + extras
    return [n.strip() for n in v.split(",") if n.strip()]


def activate_camera_or_studio(name):
    """Activate `name` as a Studio if one matches (pairs camera + lighting),
    else as a raw camera. Returns the camera name actually made active, or
    None on failure. Copied verbatim from the sibling scripts."""
    try:
        studios = lux.getStudios()
    except Exception:
        studios = []

    if name in studios:
        try:
            studio = lux.getStudio(name)
            lux.setActiveStudio(name)
            cam = studio.getCamera()
            if cam:
                lux.setCamera(cam)
            return cam or name
        except Exception as e:
            print(f"  [warn] couldn't activate studio '{name}': {e}")
            return None

    try:
        cameras = lux.getCameras()
    except Exception:
        cameras = []
    if name in cameras:
        try:
            lux.setCamera(name)
            return name
        except Exception as e:
            print(f"  [warn] couldn't set camera '{name}': {e}")
            return None

    print(f"  [warn] '{name}' not found as a studio or camera — skipping")
    return None


# --------------------------------------------------------------------------
# Vector helpers (copied verbatim from 2b_ANI_HERO_REVEAL_AA01.py)
# --------------------------------------------------------------------------

def vec_xyz(v):
    try:
        return (v[0], v[1], v[2])
    except Exception:
        pass
    try:
        return (v.x, v.y, v.z)
    except Exception:
        pass
    raise TypeError(f"Couldn't extract xyz from {v!r}")


def vadd(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def vscale(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def vlen(a): return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


def vnorm(a):
    l = vlen(a)
    return (0.0, 0.0, 1.0) if l < 1e-9 else (a[0] / l, a[1] / l, a[2] / l)


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def resolve_filter(value, sentinel="ALL"):
    """Normalize a name-filter dialog field: None, '', or the sentinel all
    mean 'no filter' (match everything)."""
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


# --------------------------------------------------------------------------
# EXPERIMENTAL: bounding-box probe — copied from
# 2b_ANI_CUTAWAY_REVEAL_AA01.py's resolve_bounding_box()/_parse_bbox_result()
# --------------------------------------------------------------------------

def _parse_bbox_result(result):
    """Try a couple of plausible return shapes for a bounding-box call.
    Returns (min_xyz, max_xyz) or None. Entirely unconfirmed shape."""
    if result is None:
        return None
    try:
        lo = vec_xyz(result.min)
        hi = vec_xyz(result.max)
        return lo, hi
    except Exception:
        pass
    try:
        if len(result) == 2:
            return vec_xyz(result[0]), vec_xyz(result[1])
        if len(result) == 6:
            return (result[0], result[1], result[2]), (result[3], result[4], result[5])
    except Exception:
        pass
    return None


def resolve_bounding_box(node):
    """EXPERIMENTAL — see the PART EXTENT header note. Probes a short list
    of plausible bounding-box getters via getattr(...); none are confirmed
    anywhere in this pipeline. Returns (min_xyz, max_xyz, api_name) or
    (None, None, None) if nothing resolved."""
    candidates = [
        ("getBoundingBox", {"world": True}),
        ("getBoundingBox", {}),
        ("getWorldBoundingBox", {}),
        ("getBounds", {"world": True}),
        ("getBounds", {}),
    ]
    for name, kwargs in candidates:
        fn = getattr(node, name, None)
        if fn is None:
            continue
        result = None
        try:
            result = fn(**kwargs) if kwargs else fn()
        except Exception:
            try:
                result = fn()
            except Exception:
                continue
        parsed = _parse_bbox_result(result)
        if parsed:
            lo, hi = parsed
            return lo, hi, name
    return None, None, None


_extent_fallback_warned = False


def resolve_part_extent(node, fallback_mult):
    """Best-effort characteristic size for one part, used to scale its
    scatter/spiral offsets. Prefers a real bounding-box half-diagonal
    (EXPERIMENTAL — see resolve_bounding_box()); falls back to the part's
    own center-to-scene-origin distance (a much cruder proxy) if no
    bounding-box call resolves, warning once rather than per-part."""
    global _extent_fallback_warned
    lo, hi, api_name = resolve_bounding_box(node)
    if lo is not None and hi is not None:
        extent = vlen(vsub(hi, lo)) / 2.0
        if extent > 1e-6:
            return extent

    if not _extent_fallback_warned:
        print("  [warn] no bounding-box getter resolved on this KeyShot version (tried "
              "getBoundingBox/getWorldBoundingBox/getBounds) — falling back to each part's "
              "center-to-origin distance as a much cruder size proxy. Run help(node) in the "
              "Scripting Console to find the exact call on your build.")
        _extent_fallback_warned = True

    try:
        center = vec_xyz(node.getCenter(world=True))
        dist = vlen(center)
        if dist > 1e-6:
            return dist * max(fallback_mult, 0.01)
    except Exception:
        pass
    return 10.0  # last-resort nominal default so scatter math never divides by zero


# --------------------------------------------------------------------------
# EXPERIMENTAL: relative transform delta builder — see TRANSFORM MECHANICS
# --------------------------------------------------------------------------

def build_delta_matrix(translation_delta, rotation_deg_delta, axis_vec):
    """Build the Matrix for ONE frame's incremental relative transform.
    EXPERIMENTAL end to end — see TRANSFORM MECHANICS in the module
    docstring. .rotate() is already used experimentally elsewhere in this
    pipeline (the hero reveal script's turntable); .translate() has NEVER
    been called anywhere in this codebase before and is a pure naming-
    convention guess. Returns (matrix, translate_ok, rotate_ok) — either
    flag can be False if that channel isn't available on this build, and
    the matrix still reflects whatever DID apply."""
    m = luxmath.Matrix().makeIdentity()
    rotate_ok = False
    translate_ok = False

    if abs(rotation_deg_delta) > 1e-9:
        try:
            axis_v = luxmath.Vector(axis_vec)
            m = m.rotate(rotation_deg_delta, axis_v)
            rotate_ok = True
        except Exception:
            rotate_ok = False

    if vlen(translation_delta) > 1e-9:
        translate_fn = getattr(m, "translate", None)
        if translate_fn is not None:
            try:
                tv = luxmath.Vector(translation_delta)
                m = translate_fn(tv)
                translate_ok = True
            except Exception:
                translate_ok = False

    return m, translate_ok, rotate_ok


def apply_part_delta(node, translation_delta, rotation_deg_delta, axis_vec, state):
    """Apply one frame's delta to `node` and update its bookkeeping in
    `state` (running totals used for the end-of-shot corrective step, plus
    per-channel availability flags so a failed channel isn't retried every
    frame — same degrade-once pattern as the sibling scripts' env-rotation
    and turntable-rotation handling)."""
    if not state.get("translate_available", True):
        translation_delta = (0.0, 0.0, 0.0)
    if not state.get("rotate_available", True):
        rotation_deg_delta = 0.0
    if vlen(translation_delta) < 1e-9 and abs(rotation_deg_delta) < 1e-9:
        return

    matrix, translate_ok, rotate_ok = build_delta_matrix(translation_delta, rotation_deg_delta, axis_vec)
    try:
        node.applyTransform(matrix, absolute=False)
    except Exception as e:
        state["translate_available"] = False
        state["rotate_available"] = False
        print(f"  [warn] applyTransform failed for '{state.get('name', '?')}' ({e}) — "
              f"disabling further motion for this part")
        return

    if vlen(translation_delta) > 1e-9 and not translate_ok and state.get("translate_available", True):
        state["translate_available"] = False
        print(f"  [warn] luxmath.Matrix().translate() not available on this KeyShot version — "
              f"'{state.get('name', '?')}' will not translate (rotation, if any, still applies)")
    if abs(rotation_deg_delta) > 1e-9 and not rotate_ok and state.get("rotate_available", True):
        state["rotate_available"] = False
        print(f"  [warn] luxmath.Matrix().rotate() not available on this KeyShot version — "
              f"'{state.get('name', '?')}' will not rotate (translation, if any, still applies)")

    state["applied_translation"] = vadd(state.get("applied_translation", (0.0, 0.0, 0.0)),
                                         translation_delta if translate_ok else (0.0, 0.0, 0.0))
    state["applied_rotation_deg"] = state.get("applied_rotation_deg", 0.0) + (
        rotation_deg_delta if rotate_ok else 0.0)


def apply_final_correction(node, state):
    """Best-effort re-assertion that a part landed exactly on its authored
    final transform: applies one more delta equal to the negative of this
    script's own running total of everything it told KeyShot to apply.
    This guards against float drift in the same SPIRIT as the hero reveal
    script's "restore exact hero state" step, but — unlike that step, which
    reads the hero pose right back off the camera — there is no confirmed
    readback API for a node's position/rotation, so this corrects against
    our own bookkeeping rather than a verified live value."""
    residual_translation = vscale(state.get("applied_translation", (0.0, 0.0, 0.0)), -1.0)
    residual_rotation = -state.get("applied_rotation_deg", 0.0)
    if vlen(residual_translation) < 1e-9 and abs(residual_rotation) < 1e-9:
        return
    apply_part_delta(node, residual_translation, residual_rotation,
                      state.get("rotation_axis", (0.0, 1.0, 0.0)), state)


# --------------------------------------------------------------------------
# EXPERIMENTAL: opacity/transparency probe — see GHOST FADE header note
# --------------------------------------------------------------------------

NODE_OPACITY_SETTERS = ["setOpacity", "setTransparency", "setAlpha"]
MATERIAL_OBJECT_ACCESSORS = ["getMaterialNode", "getAppearance", "getMaterialObject", "getMaterialGraph"]
MATERIAL_OPACITY_SETTERS = ["setOpacity", "setTransparency", "setAlpha"]

_opacity_warned = False


def resolve_opacity_control(node):
    """EXPERIMENTAL — see GHOST FADE header note. Probes node-level opacity
    setters first, then a material-OBJECT accessor (deliberately NOT
    node.getMaterial(), which is confirmed elsewhere in this pipeline to
    return a name string rather than a settable object) plus its own
    setters. Returns a zero-arg-free callable set_opacity(value) that
    applies whichever channel worked, or None if nothing resolved."""
    for name in NODE_OPACITY_SETTERS:
        fn = getattr(node, name, None)
        if fn is None:
            continue
        try:
            fn(1.0)  # probe call — full opacity is a safe no-visual-change value to test with
            return fn, f"node.{name}"
        except Exception:
            continue

    for accessor in MATERIAL_OBJECT_ACCESSORS:
        get_fn = getattr(node, accessor, None)
        if get_fn is None:
            continue
        try:
            material_obj = get_fn()
        except Exception:
            continue
        if material_obj is None or isinstance(material_obj, str):
            continue  # a name string isn't a settable object — same trap node.getMaterial() would be
        for setter in MATERIAL_OPACITY_SETTERS:
            fn = getattr(material_obj, setter, None)
            if fn is None:
                continue
            try:
                fn(1.0)
                return fn, f"{accessor}().{setter}"
            except Exception:
                continue

    return None, None


def warn_opacity_once():
    global _opacity_warned
    if not _opacity_warned:
        print("  [warn] no working opacity/transparency API resolved on this KeyShot version — "
              "tried node-level setOpacity/setTransparency/setAlpha and material-object accessors "
              f"{MATERIAL_OBJECT_ACCESSORS} with the same setters. Falling back to a hard cut: parts "
              "will be visible for the whole shot instead of fading in. Run help(node) / "
              "help(node.getMaterialNode()) (or whichever accessor exists) in the Scripting Console "
              "to find the real API and add it to the candidate lists at the top of this file.")
        _opacity_warned = True


# --------------------------------------------------------------------------
# Frame profile (same monotonic-ease approach as the sibling scripts)
# --------------------------------------------------------------------------

def ease_smooth(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def build_convergence_profile(num_frames, hold_start, hold_end):
    """List of length num_frames, values in [0,1]: 0 = fully scattered /
    unopened, 1 = fully converged / final. Monotonic — a single clean ease,
    no overshoot, no reversal. Used by scatter_settle, spiral_converge, and
    ghost_fade; staggered_build uses its own per-part windows instead (see
    schedule_staggered_windows())."""
    hold_start = min(hold_start, max(0, num_frames // 3))
    hold_end = min(hold_end, max(0, num_frames // 2))
    travel = max(2, num_frames - hold_start - hold_end)

    profile = [0.0] * hold_start
    for i in range(travel):
        t = i / max(1, travel - 1)
        profile.append(ease_smooth(t))
    profile += [1.0] * hold_end

    if len(profile) < num_frames:
        profile += [1.0] * (num_frames - len(profile))
    return profile[:num_frames]


def schedule_staggered_windows(num_parts, num_frames, hold_start, hold_end, overlap_frac):
    """Per-part [start_frame, end_frame) windows for staggered_build, in
    whatever order the caller already sorted the parts into. Windows are
    spaced evenly across the travel range and may overlap by
    `overlap_frac` of a window's own length (0 = hard cutover between
    parts, >0 = a little overlap so arrivals feel less mechanical) — this
    spacing/overlap scheme is this script's own design choice (the brief
    left it open), not something drawn from a confirmed API.

    Extension point for the (out-of-scope) sub-assembly build mode: group
    parts by parent node before calling this, then call it once per group
    with that group's own sub-range of frames, nesting group windows inside
    an outer group-convergence pass — see SUB-ASSEMBLY BUILD in the module
    docstring."""
    hold_start = min(hold_start, max(0, num_frames // 3))
    hold_end = min(hold_end, max(0, num_frames // 2))
    travel = max(2, num_frames - hold_start - hold_end)
    if num_parts <= 0:
        return []

    step = travel / float(num_parts)
    window_len = max(2.0, step * (1.0 + max(0.0, overlap_frac)))
    windows = []
    for i in range(num_parts):
        start_f = hold_start + int(round(i * step))
        end_f = min(hold_start + travel, int(round(start_f + window_len)))
        end_f = max(end_f, start_f + 1)
        windows.append((start_f, end_f))
    return windows


def staggered_t_at(frame, window):
    start_f, end_f = window
    if frame < start_f:
        return 0.0
    if frame >= end_f:
        return 1.0
    return ease_smooth((frame - start_f) / float(max(1, end_f - start_f)))


# --------------------------------------------------------------------------
# Part discovery + per-part motion setup
# --------------------------------------------------------------------------

def get_parts(target_node, name_filter=None, order="Scene Order"):
    """Every object (leaf part) node under `target_node`. Scene-tree order
    (whatever root.find() returns, the same order the turntable feature in
    the hero reveal script already relies on) by default; 'Name' sorts by
    node.getName() (confirmed elsewhere in this pipeline) for a
    deterministic, human-predictable arrival order instead. Extension
    point for sub-assembly grouping — see SUB-ASSEMBLY BUILD above."""
    candidates = target_node.find(name=name_filter) if name_filter else target_node.find("")
    parts = []
    for node in candidates:
        try:
            if node.isObject():
                parts.append(node)
        except Exception:
            continue

    if order == "Name":
        def safe_name(n):
            try:
                return n.getName() or ""
            except Exception:
                return ""
        parts = sorted(parts, key=safe_name)

    return parts


def random_unit_vector():
    """Uniform-ish random direction on the unit sphere (simple rejection-
    free spherical parameterization — fine for a visual scatter, not a
    statistically rigorous sampler)."""
    z = random.uniform(-1.0, 1.0)
    theta = random.uniform(0.0, 2.0 * math.pi)
    r = math.sqrt(max(0.0, 1.0 - z * z))
    return (r * math.cos(theta), r * math.sin(theta), z)


def perpendicular_basis(direction):
    """Two unit vectors perpendicular to `direction` and to each other,
    used as the spiral plane for spiral_converge. Picks a reference axis
    that isn't nearly parallel to `direction` to avoid the degenerate
    cross-product case (same class of failure mode the hero reveal
    script's header describes for its removed orbit feature)."""
    ref = (0.0, 0.0, 1.0)
    if abs(direction[2]) > 0.9:
        ref = (0.0, 1.0, 0.0)
    perp1 = vnorm(vcross(direction, ref))
    perp2 = vnorm(vcross(direction, perp1))
    return perp1, perp2


def build_part_states(parts, opts, mode):
    """Precompute each part's motion parameters once, up front, before the
    frame loop. Returns a list of per-part state dicts (see the fields set
    below); the frame loop only ever reads/updates these, never
    recomputes them."""
    fallback_mult = opts.get("extent_fallback_mult", 0.5)
    scatter_radius_mult = opts.get("scatter_radius_mult", 3.0)
    scatter_rot_enabled = opts.get("scatter_rotation_enabled", True)
    scatter_rot_max = opts.get("scatter_rotation_max_degrees", 90.0)
    arrival_axis = AXIS_VECTORS.get(opts.get("staggered_arrival_axis", "Z"), AXIS_VECTORS["Z"])
    arrival_dist_mult = opts.get("staggered_arrival_distance_mult", 4.0)
    spiral_turns = opts.get("spiral_turns", 1.5)
    spiral_amp_mult = opts.get("spiral_amplitude_mult", 1.0)

    states = []
    for node in parts:
        try:
            name = node.getName()
        except Exception:
            name = "?"

        extent = resolve_part_extent(node, fallback_mult)

        state = {
            "node": node,
            "name": name,
            "extent": extent,
            "prev_t": 0.0,
            "applied_translation": (0.0, 0.0, 0.0),
            "applied_rotation_deg": 0.0,
            "translate_available": True,
            "rotate_available": True,
            "rotation_axis": (0.0, 1.0, 0.0),
            "opacity_setter": None,
            "opacity_available": True,
        }

        if mode == "scatter_settle":
            state["translate_vector"] = vscale(random_unit_vector(), extent * scatter_radius_mult)
            if scatter_rot_enabled:
                state["rotation_axis"] = random_unit_vector()
                state["rotation_total_deg"] = random.uniform(-scatter_rot_max, scatter_rot_max)
            else:
                state["rotation_total_deg"] = 0.0

        elif mode == "spiral_converge":
            base_vector = vscale(random_unit_vector(), extent * scatter_radius_mult)
            state["translate_vector"] = base_vector
            path_dir = vnorm(base_vector)
            perp1, perp2 = perpendicular_basis(path_dir)
            state["spiral_perp1"] = perp1
            state["spiral_perp2"] = perp2
            state["spiral_amp"] = extent * spiral_amp_mult
            state["spiral_turns"] = spiral_turns
            state["rotation_total_deg"] = 0.0

        elif mode == "staggered_build":
            state["translate_vector"] = vscale(arrival_axis, extent * arrival_dist_mult)
            state["rotation_total_deg"] = 0.0

        elif mode == "ghost_fade":
            state["translate_vector"] = (0.0, 0.0, 0.0)
            state["rotation_total_deg"] = 0.0
            fn, api_name = resolve_opacity_control(node)
            state["opacity_setter"] = fn
            state["opacity_available"] = fn is not None
            if fn is None:
                warn_opacity_once()
            elif DEBUG:
                print(f"  Opacity control for '{name}' resolved via {api_name}")

        states.append(state)

    return states


def compute_spiral_offset(t, state):
    """Perpendicular spiral component added on top of the straight-line
    path for spiral_converge — zero at t=1, mirroring
    compute_vertical_offset()'s zero-at-t=1 discipline in the hero reveal
    script, so the curved path still lands exactly on the authored final
    position."""
    amp = state["spiral_amp"] * (1.0 - t)
    if amp < 1e-9:
        return (0.0, 0.0, 0.0)
    theta = state["spiral_turns"] * 2.0 * math.pi * (1.0 - t)
    return vadd(vscale(state["spiral_perp1"], amp * math.cos(theta)),
                vscale(state["spiral_perp2"], amp * math.sin(theta)))


def compute_translation_at(t, state, mode):
    if mode == "ghost_fade":
        return (0.0, 0.0, 0.0)
    base = vscale(state["translate_vector"], 1.0 - t)
    if mode == "spiral_converge":
        return vadd(base, compute_spiral_offset(t, state))
    return base  # scatter_settle, staggered_build — straight line


def compute_rotation_at(t, state, mode):
    if mode != "scatter_settle":
        return 0.0
    return state.get("rotation_total_deg", 0.0) * (1.0 - t)


# --------------------------------------------------------------------------
# One shot: animate parts for a single target, render its frames
# --------------------------------------------------------------------------

def shoot_one_assembly(opts, target, render_opts, output_folder, queueing, part_states, mode, profile,
                        staggered_windows):
    label = target if target else "current"
    safe_name = sanitize_name(label)
    video_name = f"{opts.get('video_name_prefix') or 'ASSEMBLY'}_{safe_name}.mp4"
    frame_folder = os.path.join(output_folder, f"{safe_name}_assembly_frames")

    result = {"target": label, "video_name": video_name, "frame_folder": frame_folder,
              "frame_count": 0, "ok": False, "status": "FAILED", "output_path": ""}

    if target is not None:
        resolved_cam = activate_camera_or_studio(target)
        if resolved_cam is None:
            result["status"] = f"FAILED (couldn't activate '{target}')"
            return result
        print(f"--- Shooting '{target}' (camera '{resolved_cam}') ---")
    else:
        print("--- Shooting current viewport camera ---")

    # --- environment, captured fresh per target (a Studio may swap it) ------
    env = None
    start_rotation, start_brightness = None, None
    try:
        env = lux.getActiveEnvironment()
    except Exception as e:
        print(f"  [warn] couldn't get active environment: {e}")
    if env is not None:
        try:
            start_rotation = env.getRotation()
        except Exception as e:
            print(f"  [warn] couldn't read environment rotation: {e}")
        try:
            start_brightness = env.getBrightness()
        except Exception as e:
            print(f"  [warn] couldn't read environment brightness: {e}")
    if env is not None and opts.get("backplate_image"):
        try:
            env.setBackplateImage(opts["backplate_image"])
        except Exception as e:
            print(f"  [warn] couldn't set backplate image: {e}")
    if env is not None:
        set_ground_rendering(env, bool(opts.get("render_ground", True)))

    if not os.path.isdir(frame_folder):
        try:
            os.makedirs(frame_folder)
        except Exception as e:
            print(f"  [error] couldn't create frame folder '{frame_folder}': {e}")
            result["status"] = f"FAILED (frame folder: {e})"
            return result

    # reset per-part running state fresh for this target, in case the same
    # part_states list is reused across multiple camera/Studio targets
    for state in part_states:
        state["prev_t"] = 0.0
        state["applied_translation"] = (0.0, 0.0, 0.0)
        state["applied_rotation_deg"] = 0.0
        state["translate_available"] = True
        state["rotate_available"] = True

    ghost_start_opacity = opts.get("ghost_fade_start_opacity", 0.0)
    ghost_end_opacity = opts.get("ghost_fade_end_opacity", 1.0)

    env_rotate_available = True

    for f in range(opts["num_frames"]):
        t_global = profile[f]

        for i, state in enumerate(part_states):
            if mode == "staggered_build":
                t_part = staggered_t_at(f, staggered_windows[i])
            else:
                t_part = t_global

            translation_now = compute_translation_at(t_part, state, mode)
            rotation_now = compute_rotation_at(t_part, state, mode)
            delta_translation = vsub(translation_now, compute_translation_at(state["prev_t"], state, mode))
            delta_rotation = rotation_now - compute_rotation_at(state["prev_t"], state, mode)

            if mode != "ghost_fade":
                apply_part_delta(state["node"], delta_translation, delta_rotation,
                                  state.get("rotation_axis", (0.0, 1.0, 0.0)), state)

            if mode == "ghost_fade" and state.get("opacity_available") and state.get("opacity_setter"):
                opacity_now = ghost_start_opacity + (ghost_end_opacity - ghost_start_opacity) * t_part
                try:
                    state["opacity_setter"](opacity_now)
                except Exception as e:
                    state["opacity_available"] = False
                    print(f"  [warn] opacity call stopped working mid-shot for '{state['name']}' "
                          f"({e}) — leaving it at its last opacity")

            state["prev_t"] = t_part

        # --- environment rotation (continuous across the whole clip) ---
        if env is not None and env_rotate_available and opts.get("rotate_environment") and start_rotation is not None:
            try:
                sweep = opts["environment_rotation_degrees"] * (f / max(1, opts["num_frames"] - 1))
                env.setRotation(start_rotation + sweep)
            except Exception as e:
                env_rotate_available = False
                print(f"  [warn] environment rotation not available in this KeyShot version "
                      f"({e}) — continuing without it")

        # --- brightness ramp, synced to convergence progress ---
        if env is not None and opts.get("brightness_ramp") and start_brightness is not None:
            try:
                start_mult = opts.get("brightness_ramp_start_mult", 0.6)
                low = start_brightness * start_mult
                env.setBrightness(low + (start_brightness - low) * t_global)
            except Exception as e:
                print(f"  [warn] couldn't ramp brightness on frame {f}: {e}")

        frame_file = FRAME_PATTERN % f
        frame_path = os.path.join(frame_folder, frame_file)
        try:
            if render_opts is not None:
                lux.renderImage(frame_path, width=opts["width"], height=opts["height"], opts=render_opts)
            else:
                lux.renderImage(frame_path, width=opts["width"], height=opts["height"])
        except Exception as e:
            print(f"  [warn] couldn't render frame {f}: {e}")

        if f % 10 == 0 or f == opts["num_frames"] - 1:
            print(f"    frame {f + 1}/{opts['num_frames']} (t={t_global:.2f})")

    # --- corrective step: re-assert each part's exact authored final state --
    if mode != "ghost_fade":
        for state in part_states:
            apply_final_correction(state["node"], state)
    else:
        for state in part_states:
            if state.get("opacity_available") and state.get("opacity_setter"):
                try:
                    state["opacity_setter"](ghost_end_opacity)
                except Exception:
                    pass

    # --- restore environment state (guards against any drift) --------------
    if env is not None:
        if start_rotation is not None:
            try:
                env.setRotation(start_rotation)
            except Exception:
                pass
        if start_brightness is not None:
            try:
                env.setBrightness(start_brightness)
            except Exception:
                pass

    result["frame_count"] = opts["num_frames"]
    result["ok"] = True

    if queueing:
        result["status"] = "queued (pending encode)"
        return result

    return encode_one_assembly(result, opts, output_folder)


def encode_one_assembly(result, opts, output_folder):
    """Encode a single target's already-rendered frames into a video.
    Only safe to call once every frame in result['frame_folder'] actually
    exists on disk — see the QUEUEING note in the module docstring."""
    if not result.get("ok"):
        return result
    video_path = os.path.join(output_folder, result["video_name"])
    try:
        lux.encodeVideo(
            folder=result["frame_folder"],
            frameFiles=FRAME_PATTERN,
            videoName=video_path,
            fps=opts["fps"],
            firstFrame=0,
            lastFrame=result["frame_count"] - 1,
            keepFrames=opts.get("keep_frames", False),
        )
        print(f"  Video encoded: {os.path.abspath(video_path)}")
        result["status"] = "encoded"
        result["output_path"] = video_path
    except Exception as e:
        result["status"] = f"FAILED (encode: {e})"
        print(f"  [warn] video encoding failed for '{result['target']}': {e} — "
              f"frames are still on disk at {result['frame_folder']}")
    return result


# --------------------------------------------------------------------------
# Options dialog (GUI only — auto-skipped in headless mode)
# --------------------------------------------------------------------------

def get_options():
    if lux.isHeadless():
        print("Headless session detected — skipping dialog, using DEFAULT_OPTIONS.")
        return dict(DEFAULT_OPTIONS)

    values = [
        (lux.DIALOG_LABEL, "-- scene setup (for automated / batch use) --"),
        ("scene_template_path", lux.DIALOG_FILE,
         "Scene template to load before shooting (blank = use whatever scene is already open):", None),
        (lux.DIALOG_LABEL, "-- assembly import --"),
        ("import_file_path", lux.DIALOG_FILE,
         "Assembly/part file to import (blank = use whatever's already in the scene):", None),
        ("target_model_set_name", lux.DIALOG_TEXT,
         "Model set to gather parts from (blank = whole scene):", ""),
        ("part_name_filter", lux.DIALOG_TEXT, "Part name filter (ALL = every part found):",
         DEFAULT_OPTIONS["part_name_filter"]),
        ("camera_selection", lux.DIALOG_TEXT,
         "Camera(s)/Studio(s) to shoot — blank = current viewport camera, 'ALL' = every one found, "
         "or a comma-separated list of names:", DEFAULT_OPTIONS["camera_selection"]),
        (lux.DIALOG_LABEL, "-- mode --"),
        ("mode", lux.DIALOG_ITEM,
         "Procedural mode:", DEFAULT_OPTIONS["mode"], MODE_OPTIONS),
        ("num_frames", lux.DIALOG_INTEGER, "Total frames:", DEFAULT_OPTIONS["num_frames"], (10, 600)),
        ("fps", lux.DIALOG_INTEGER, "Frames per second:", DEFAULT_OPTIONS["fps"], (1, 60)),
        ("hold_start", lux.DIALOG_INTEGER, "Hold frames before motion starts:",
         DEFAULT_OPTIONS["hold_start"], (0, 200)),
        ("hold_end", lux.DIALOG_INTEGER, "Hold frames once fully assembled:",
         DEFAULT_OPTIONS["hold_end"], (0, 400)),
        ("random_seed", lux.DIALOG_INTEGER,
         "Random seed (0 = non-deterministic each run; any other value = reproducible scatter):",
         DEFAULT_OPTIONS["random_seed"], (0, 999999)),
        ("extent_fallback_mult", lux.DIALOG_DOUBLE,
         "Fallback size multiplier if no bounding-box getter resolves (x center-to-origin distance):",
         DEFAULT_OPTIONS["extent_fallback_mult"], (0.01, 5.0)),
        (lux.DIALOG_LABEL, "-- scatter_settle --"),
        ("scatter_radius_mult", lux.DIALOG_DOUBLE, "Scatter radius (x each part's own size):",
         DEFAULT_OPTIONS["scatter_radius_mult"], (0.5, 20.0)),
        ("scatter_rotation_enabled", lux.DIALOG_CHECK, "Also randomize starting rotation",
         DEFAULT_OPTIONS["scatter_rotation_enabled"]),
        ("scatter_rotation_max_degrees", lux.DIALOG_DOUBLE, "Max starting rotation offset (degrees):",
         DEFAULT_OPTIONS["scatter_rotation_max_degrees"], (0.0, 360.0)),
        (lux.DIALOG_LABEL, "-- staggered_build --"),
        ("staggered_order", lux.DIALOG_ITEM, "Arrival order:",
         DEFAULT_OPTIONS["staggered_order"], STAGGERED_ORDER_OPTIONS),
        ("staggered_overlap_frac", lux.DIALOG_DOUBLE,
         "Window overlap between consecutive parts (0 = hard cutover, 1 = fully overlapping):",
         DEFAULT_OPTIONS["staggered_overlap_frac"], (0.0, 1.0)),
        ("staggered_arrival_axis", lux.DIALOG_ITEM, "Off-frame arrival axis:",
         DEFAULT_OPTIONS["staggered_arrival_axis"], STAGGERED_ARRIVAL_AXES),
        ("staggered_arrival_distance_mult", lux.DIALOG_DOUBLE,
         "Off-frame start distance (x each part's own size):",
         DEFAULT_OPTIONS["staggered_arrival_distance_mult"], (0.5, 20.0)),
        (lux.DIALOG_LABEL, "-- spiral_converge --"),
        ("spiral_turns", lux.DIALOG_DOUBLE, "Spiral turns over the whole approach:",
         DEFAULT_OPTIONS["spiral_turns"], (0.0, 10.0)),
        ("spiral_amplitude_mult", lux.DIALOG_DOUBLE, "Spiral amplitude (x each part's own size):",
         DEFAULT_OPTIONS["spiral_amplitude_mult"], (0.0, 5.0)),
        (lux.DIALOG_LABEL, "-- ghost_fade --"),
        ("ghost_fade_start_opacity", lux.DIALOG_DOUBLE, "Starting opacity:",
         DEFAULT_OPTIONS["ghost_fade_start_opacity"], (0.0, 1.0)),
        ("ghost_fade_end_opacity", lux.DIALOG_DOUBLE, "Final opacity:",
         DEFAULT_OPTIONS["ghost_fade_end_opacity"], (0.0, 1.0)),
        (lux.DIALOG_LABEL, "-- dynamic background / lighting (secondary to the parts' own motion) --"),
        ("render_ground", lux.DIALOG_CHECK, "Render ground (shadow/reflection catcher)",
         DEFAULT_OPTIONS["render_ground"]),
        ("rotate_environment", lux.DIALOG_CHECK, "Rotate HDRI environment during the shot",
         DEFAULT_OPTIONS["rotate_environment"]),
        ("environment_rotation_degrees", lux.DIALOG_DOUBLE, "Environment rotation over full clip (degrees):",
         DEFAULT_OPTIONS["environment_rotation_degrees"], (0.0, 360.0)),
        ("brightness_ramp", lux.DIALOG_CHECK, "Ramp brightness during the shot",
         DEFAULT_OPTIONS["brightness_ramp"]),
        ("brightness_ramp_start_mult", lux.DIALOG_DOUBLE, "Starting brightness (x current):",
         DEFAULT_OPTIONS["brightness_ramp_start_mult"], (0.0, 1.0)),
        ("backplate_image", lux.DIALOG_FILE, "Optional static backplate image (blank = none):", None),
        (lux.DIALOG_LABEL, "-- rendering --"),
        ("preview_mode", lux.DIALOG_CHECK, "Preview mode (fast, low-quality frames)",
         DEFAULT_OPTIONS["preview_mode"]),
        ("add_to_queue", lux.DIALOG_CHECK,
         "Add frames to KeyShot's render queue instead of rendering immediately",
         DEFAULT_OPTIONS["add_to_queue"]),
        ("process_queue_after", lux.DIALOG_CHECK,
         "Process the queue and encode videos once everything is queued (only used if queueing is on)",
         DEFAULT_OPTIONS["process_queue_after"]),
        (lux.DIALOG_LABEL, "-- output --"),
        ("output_folder", lux.DIALOG_FOLDER, "Output folder (blank = current):", None),
        ("video_name_prefix", lux.DIALOG_TEXT,
         "Video filename prefix (one video per target, e.g. PREFIX_CameraName.mp4):",
         DEFAULT_OPTIONS["video_name_prefix"]),
        ("width", lux.DIALOG_INTEGER, "Render width:", DEFAULT_OPTIONS["width"], (64, 8000)),
        ("height", lux.DIALOG_INTEGER, "Render height:", DEFAULT_OPTIONS["height"], (64, 8000)),
        ("keep_frames", lux.DIALOG_CHECK, "Keep individual frame images after encoding",
         DEFAULT_OPTIONS["keep_frames"]),
    ]

    opts = lux.getInputDialog(
        title="Assembly Reveal — Procedural Modes",
        desc="Parts converge into (or fade into) their authored final positions while the camera "
             "holds static. Per-node relative-transform composition and opacity control are "
             "EXPERIMENTAL on this KeyShot build — see the script header for what's confirmed vs. "
             "probed.",
        values=values,
        id="assembly_procedural_dialog",
    )

    if opts is None:
        return None

    def norm_item(v, valid):
        if isinstance(v, (list, tuple)):
            for candidate in reversed(v):
                if candidate in valid:
                    return candidate
            return v[-1]
        return v

    opts["mode"] = norm_item(opts.get("mode"), MODE_OPTIONS)
    opts["staggered_order"] = norm_item(opts.get("staggered_order"), STAGGERED_ORDER_OPTIONS)
    opts["staggered_arrival_axis"] = norm_item(opts.get("staggered_arrival_axis"), STAGGERED_ARRIVAL_AXES)
    return opts


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def run_assembly(opts):
    print(f"lux.isHeadless() = {lux.isHeadless()}")

    mode = opts.get("mode") or "scatter_settle"
    if mode not in MODE_OPTIONS:
        print(f"[warn] unrecognized mode '{mode}' — falling back to 'scatter_settle'")
        mode = "scatter_settle"

    seed = opts.get("random_seed", 0)
    if seed:
        random.seed(seed)
        print(f"Random seed set to {seed} — scatter/spiral offsets are reproducible across runs")

    output_folder = opts.get("output_folder") or "."
    abs_folder = os.path.abspath(output_folder)
    manifest_path = os.path.join(abs_folder, "assembly_manifest.csv")
    scene_template = opts.get("scene_template_path") or ""

    def log(result):
        logManifestRow(manifest_path, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "scene_template": scene_template,
            "target": result.get("target", ""),
            "video_name": result.get("video_name", ""),
            "output_path": result.get("output_path", ""),
            "status": result.get("status", ""),
        })

    load_scene_template(scene_template)
    import_into_model_set(opts.get("import_file_path"), opts.get("target_model_set_name"))

    target_node = get_target_node(opts.get("target_model_set_name"))
    parts = get_parts(target_node, resolve_filter(opts.get("part_name_filter")),
                       opts.get("staggered_order", "Scene Order"))
    if not parts:
        print("[error] no object parts resolved under the target — nothing to animate.")
        return []
    print(f"Mode: {mode} — {len(parts)} part(s) found")

    part_states = build_part_states(parts, opts, mode)

    profile = build_convergence_profile(opts["num_frames"], opts["hold_start"], opts["hold_end"])
    staggered_windows = []
    if mode == "staggered_build":
        staggered_windows = schedule_staggered_windows(
            len(parts), opts["num_frames"], opts["hold_start"], opts["hold_end"],
            opts.get("staggered_overlap_frac", 0.25))

    camera_list = resolve_camera_list(opts.get("camera_selection"))
    targets = [None] if camera_list is None else camera_list
    if not targets:
        print("[error] no cameras/studios resolved from camera_selection — nothing to render.")
        return []
    print(f"Shooting {len(targets)} target(s): {', '.join(t or 'current' for t in targets)}")

    render_opts = None
    try:
        render_opts = lux.getRenderOptions()
        if opts.get("preview_mode", True):
            try:
                render_opts.setMaxTimeRendering(2)
            except Exception as e:
                print(f"[warn] couldn't set preview render mode: {e}")
        if opts.get("add_to_queue"):
            try:
                render_opts.setAddToQueue(True)
            except Exception as e:
                print(f"[warn] couldn't enable queueing: {e}")
    except Exception as e:
        print(f"[warn] couldn't get render options, using KeyShot defaults: {e}")

    queueing = bool(opts.get("add_to_queue"))
    if queueing:
        print("Queueing enabled — frames go to KeyShot's render queue instead of rendering immediately.")

    pending = []
    outcomes = []

    for target in targets:
        result = shoot_one_assembly(opts, target, render_opts, output_folder, queueing, part_states,
                                     mode, profile, staggered_windows)
        outcomes.append(result)
        log(result)
        if queueing and result.get("ok"):
            pending.append(result)

    if queueing and pending:
        if opts.get("process_queue_after"):
            print(f"Processing render queue ({len(pending)} shot(s) pending)...")
            queue_ok = True
            try:
                lux.processQueue()
            except Exception as e:
                queue_ok = False
                print(f"[warn] couldn't process render queue: {e} — skipping video encoding; "
                      f"frames may still be sitting in KeyShot's queue")
            if queue_ok:
                for result in pending:
                    log(encode_one_assembly(result, opts, output_folder))
        else:
            print(f"[info] {len(pending)} shot(s) queued but not rendered yet. Process the queue in "
                  f"KeyShot (Render Queue window), then encode each frame folder into video manually — "
                  f"or re-run with 'process queue after' enabled.")

    print(f"Manifest written to {manifest_path}")
    return [o.get("video_name") for o in outcomes]


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled — nothing rendered.")
    else:
        run_assembly(options)
