# AUTHOR tajf
# REV AA01
# HEADLESS COMPLIANT
"""
KeyShot Cutaway / Cross-Section Reveal
===========================================

Sweeps a clipping/section plane straight through an assembly over a render
sequence, progressively clipping geometry away to expose internal structure
-- the camera itself never moves. This is the geometry-clipping counterpart
to 2b_ANI_HERO_REVEAL_AA01.py, which moves the camera and never touches
clipping at all; the two scripts are deliberately kept separate rather than
merged into one, since "camera moves" and "geometry gets cut open" are
different shots with different failure modes.

Per RESEARCH_CREO_KEYSHOT.md: assemblies benefit far more than single parts
from a section-plane reveal (you're exposing an interior that single parts
mostly don't have), so this defaults to sweeping the WHOLE loaded scene/
model-set bounding box rather than a single part.

Built for the same many-cameras scene setup as the hero reveal script: you
can target the current viewport camera, one named camera/Studio, a comma-
separated handful, or every camera in the scene -- one cutaway video is
produced per target, sweeping the exact same plane motion for each.

--------------------------------------------------------------------------
CLIPPING PLANE / SECTION SWEEP -- READ THIS BEFORE TRUSTING THE OUTPUT
--------------------------------------------------------------------------
KeyShot's section/clipping-plane scripting surface has NOT been used or
confirmed anywhere else in this pipeline. Nothing below is a verified API
call -- every clipping-plane method name is a plausible GUESS based on
naming-convention analogy with the rest of the confirmed `lux` API (the
same "getX/setX pairing is consistent everywhere else" reasoning the hero
reveal script uses for env.setRotation(), just applied to a part of the API
this pipeline has never touched at all).

What this script actually does about that: it does NOT assume any one name
is real. resolve_clipping_plane() probes a short list of candidate call
shapes, in order, entirely through getattr(...) so a missing name is just
skipped rather than raising:

  - lux-level getters for an existing plane object: lux.getClippingPlane(),
    lux.getSection(), lux.getCuttingPlane(), lux.getClipPlane()
  - lux-level "create one" calls, tried only if no getter worked:
    lux.addClippingPlane(), lux.createClippingPlane(), lux.addSection(),
    lux.createSection()
  - on whatever handle (if any) came back, enable/activate candidates:
    setEnabled(True), enable(True), setActive(True), setVisible(True)
  - on the same handle, position candidates tried per frame:
    setPosition(pt), setOffset(scalar), setOrigin(pt), setPlane(pt, normal)
  - and normal/axis candidates: setNormal(vec), setDirection(vec),
    setAxis(vec)

Whichever candidate name actually succeeds is printed once at setup
("Clipping plane control resolved via: ..."), so you can see exactly what
your KeyShot build answered to. If NONE of the get/create candidates
resolve to a usable handle, the script does not crash or fabricate a plane
-- it prints a loud warning, disables the clip sweep, and still renders the
un-clipped frames (camera-static, so effectively a still-life sequence) so
a failed probe degrades to "no cutaway" rather than a hard stop. Same rule
applies mid-run: if a position/normal call that worked at setup starts
throwing partway through the sweep, that channel is disabled and a warning
is printed once, exactly like the env-rotation degrade pattern in the hero
reveal script.

There is also a documented alternative shape worth knowing about if none of
the above pan out on your build: a PER-NODE clip attribute rather than a
single scene-wide plane object (i.e. each SceneNode individually exposing
something like setClippingEnabled()/setClipPlane()). This script does not
attempt to drive that path today -- probing every node in a large assembly
per frame is a different cost profile than one scene-level plane -- but
resolve_clipping_plane() is structured so a per-node fallback could be
slotted in next to the scene-level candidates without restructuring the
render loop. If you confirm the real API on your build (run `dir(lux)` /
`help(lux)` in the Scripting Console, or `dir()` on whatever
lux.getClippingPlane()-style call actually returns something), update the
candidate lists here and promote the working name(s) out of "experimental"
in the section below.

--------------------------------------------------------------------------
SWEEP GEOMETRY -- BOUNDING BOX + AXIS
--------------------------------------------------------------------------
The sweep needs a start offset fully outside the assembly on one side and
an end offset fully outside on the other, so the whole interior is exposed
somewhere mid-sweep. That range is derived from the target node's
axis-aligned bounding box. CONFIRMED as of a 2026-07-11 research pass
(KeyShot 11.0 scripting reference, media.keyshot.com/scripting/doc/11.0/
lux.html): SceneNode.getBoundingBox() is real, returning (min, max)
vectors -- this was written against an unconfirmed guess and happened to
land on a real name. resolve_bounding_box() still probes a short list
(getBoundingBox(world=True), getBoundingBox(), getWorldBoundingBox(),
getBounds(world=True), getBounds()) rather than calling the confirmed form
directly, for graceful behavior on older KeyShot versions or a different
kwarg shape, and accepts a couple of plausible return shapes (an object
with .min/.max, a 2-tuple of points, or a flat 6-tuple). If somehow none of
those work, the sweep falls back to manual numeric start/end offsets from
the options dialog (clip_start_override / clip_end_override) and warns
that auto-framing the sweep wasn't possible.

--------------------------------------------------------------------------
STUDIOS vs CAMERAS
--------------------------------------------------------------------------
Copied verbatim from the hero reveal script's approach: a Studio pairs a
camera with its matching environment/lighting (and image style) --
confirmed: lux.getStudios(), lux.getStudio(name), lux.setActiveStudio(name).
Where a target name matches a Studio, this script activates the Studio; a
plain camera name just switches the camera and leaves whatever environment
is already active. Unlike the hero reveal script, the camera itself is
never moved once activated -- it just sits and watches the plane sweep.

--------------------------------------------------------------------------
GROUND RENDERING
--------------------------------------------------------------------------
Same situation and same defensive candidate-list treatment as the hero
reveal script: ground shadow/reflection getters AND setters
(env.setGroundShadows/setGroundReflections) are confirmed (see hero reveal
script's GROUND RENDERING note for the source). See set_ground_rendering()
below -- logic is a direct copy of the hero reveal script's version.

--------------------------------------------------------------------------
QUEUEING
--------------------------------------------------------------------------
Same as the hero reveal script: "add to queue" adds every rendered frame,
for every camera, to KeyShot's render queue instead of rendering
immediately. A video can only be encoded once every frame has actually
finished rendering, so without "process queue after" this script queues
everything and stops there rather than guessing at encoding a possibly-
incomplete folder.

--------------------------------------------------------------------------
CONFIRMED vs EXPERIMENTAL
--------------------------------------------------------------------------
Confirmed (KeyShot's own scripting reference, and/or already used
elsewhere in this pipeline): lux.getActiveEnvironment(), env.getBrightness/
setBrightness, env.setBackplateImage, lux.renderImage, lux.encodeVideo,
lux.openFile(), lux.getStudios(), lux.getStudio(name),
lux.setActiveStudio(name), lux.getCameras(), lux.setCamera(name),
lux.getModelSets(), lux.setModelSets(names), lux.getImportOptions(),
lux.importFile(path, opts=...), SceneNode.getCenter(world=True),
SceneNode.getBoundingBox() (confirmed 2026-07-11 -- see SWEEP GEOMETRY
above), env ground-state getters AND setters (env.setGroundShadows/
setGroundReflections, confirmed 2026-07-11 -- see GROUND RENDERING above),
lux.getRenderOptions()/setAddToQueue()/setMaxTimeRendering(),
lux.processQueue(), lux.isHeadless(), lux.getInputDialog().

Inferred-but-unconfirmed, wrapped defensively throughout: env.setRotation()
(same flag as the hero reveal script).

Experimental / entirely unverified -- flagged loudly and probed via
getattr(...) rather than called directly, degrading gracefully to "no
cutaway effect" if nothing resolves: EVERY clipping-plane method name
(lux.getClippingPlane / lux.getSection / lux.getCuttingPlane /
lux.getClipPlane / lux.addClippingPlane / lux.createClippingPlane /
lux.addSection / lux.createSection, and the handle's setEnabled / enable /
setActive / setVisible / setPosition / setOffset / setOrigin / setPlane /
setNormal / setDirection / setAxis). None of these appear in a confirmed
reference available to this pipeline -- treat the whole clipping-plane
feature as needing a real KeyShot session to validate, and update the
candidate list / promote the working name once confirmed.

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
FRAME_PATTERN = "cutaway_frame.%d.png"

MANIFEST_FIELDS = ["timestamp", "scene_template", "target", "video_name", "output_path", "status"]

AXIS_OPTIONS = ["X", "Y", "Z"]
SWEEP_DIRECTIONS = ["Positive -> Negative", "Negative -> Positive"]

AXIS_VECTORS = {
    "X": (1.0, 0.0, 0.0),
    "Y": (0.0, 1.0, 0.0),
    "Z": (0.0, 0.0, 1.0),
}

DEFAULT_OPTIONS = {
    "scene_template_path": "",
    "import_file_path": "",
    "target_model_set_name": "",
    "camera_selection": "ALL",
    "num_frames": 90,
    "fps": 24,
    "hold_start": 4,
    "hold_end": 20,
    "clip_axis": "X",
    "sweep_direction": "Positive -> Negative",
    "clip_margin_mult": 1.15,
    "clip_start_override": None,
    "clip_end_override": None,
    "render_ground": True,
    "rotate_environment": False,
    "environment_rotation_degrees": 30.0,
    "brightness_ramp": False,
    "brightness_ramp_start_mult": 0.6,
    "backplate_image": "",
    "preview_mode": True,
    "add_to_queue": False,
    "process_queue_after": False,
    "output_folder": "",
    "video_name_prefix": "CUTAWAY",
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
    (so the sweep has a stable target to compute a bounding box against).
    Confirmed: lux.getModelSets(), lux.setModelSets(), lux.getImportOptions(),
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
    """Resolve the node the sweep is framed around: the named model set if
    given and found, else the whole scene root. Same fallback pattern as
    get_focus_node() in the hero reveal script."""
    root = lux.getSceneTree()
    if model_set_name:
        try:
            matches = root.find(name=model_set_name, types=lux.NODE_TYPE_MODEL_SET)
            if matches:
                return matches[0]
        except Exception as e:
            print(f"  [warn] couldn't find model set '{model_set_name}' for sweep framing: {e}")
    return root


def set_ground_rendering(env, enabled):
    """Toggle the environment's ground shadow/reflection catcher. Copied
    from the hero reveal script — getters are confirmed, setter names are
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
# Camera / Studio selection (copied from the hero reveal script)
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
    None on failure. Copied verbatim from the hero reveal script."""
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
# Vector helpers (copied from the hero reveal script)
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


# --------------------------------------------------------------------------
# getBoundingBox() is confirmed to exist (2026-07-11) — see SWEEP GEOMETRY
# header note. Exact return-value shape still probed defensively below.
# --------------------------------------------------------------------------

def _parse_bbox_result(result):
    """Try a couple of plausible return shapes for a bounding-box call.
    Returns (min_xyz, max_xyz) or None. The call itself is confirmed
    (getBoundingBox()); its exact return shape is not documented here."""
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
    """getBoundingBox() is confirmed to exist — see SWEEP GEOMETRY header
    note. Probes a short list of plausible getter names/kwargs via
    getattr(...) for version tolerance; exact return shape isn't
    confirmed anywhere in this pipeline. Returns (min_xyz, max_xyz, api_name)
    or (None, None, None) if nothing resolved."""
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
            print(f"  Bounding box resolved via {name}({kwargs}) — min={lo} max={hi}")
            return lo, hi, name
    print("  [warn] couldn't resolve a bounding box on this KeyShot version via any of "
          "getBoundingBox/getWorldBoundingBox/getBounds — the sweep will fall back to "
          "manual clip_start_override/clip_end_override values (or an untuned default "
          "range if those are also blank). Run help(node) in the Scripting Console to "
          "find the exact call on your build.")
    return None, None, None


# --------------------------------------------------------------------------
# EXPERIMENTAL: clipping-plane probe — see CLIPPING PLANE header note
# --------------------------------------------------------------------------

CLIP_GET_CANDIDATES = ["getClippingPlane", "getSection", "getCuttingPlane", "getClipPlane"]
CLIP_ADD_CANDIDATES = ["addClippingPlane", "createClippingPlane", "addSection", "createSection"]
CLIP_ENABLE_CANDIDATES = ["setEnabled", "enable", "setActive", "setVisible"]
CLIP_POSITION_CANDIDATES = ["setPosition", "setOffset", "setOrigin"]
CLIP_NORMAL_CANDIDATES = ["setNormal", "setDirection", "setAxis"]
CLIP_COMBINED_CANDIDATES = ["setPlane"]  # tried as setPlane(point, normal)


def resolve_clipping_plane():
    """EXPERIMENTAL — see the CLIPPING PLANE / SECTION SWEEP header note.
    Tries to get a handle to an existing clipping plane, then falls back to
    creating one. Returns (handle, working_api_dict) or (None, {}) if the
    whole feature isn't available on this KeyShot build."""
    handle = None
    used_get = None
    for name in CLIP_GET_CANDIDATES:
        fn = getattr(lux, name, None)
        if fn is None:
            continue
        try:
            candidate = fn()
        except Exception:
            continue
        if candidate is not None:
            handle = candidate
            used_get = name
            break

    used_add = None
    if handle is None:
        for name in CLIP_ADD_CANDIDATES:
            fn = getattr(lux, name, None)
            if fn is None:
                continue
            try:
                candidate = fn()
            except Exception:
                continue
            if candidate is not None:
                handle = candidate
                used_add = name
                break

    if handle is None:
        print("  [warn] no clipping-plane API resolved on this KeyShot build — tried "
              f"getters {CLIP_GET_CANDIDATES} and creators {CLIP_ADD_CANDIDATES}, none "
              "worked. The cutaway sweep will be SKIPPED; frames will render un-clipped. "
              "Run `dir(lux)` in the Scripting Console to find the real name and add it "
              "to the candidate lists at the top of this file.")
        return None, {}

    def find_working(obj, names, test_args):
        for name in names:
            fn = getattr(obj, name, None)
            if fn is None:
                continue
            try:
                fn(*test_args)
                return name
            except Exception:
                continue
        return None

    used_enable = find_working(handle, CLIP_ENABLE_CANDIDATES, (True,))
    api = {
        "get": used_get,
        "add": used_add,
        "enable": used_enable,
        # position/normal/combined are validated per-frame instead of here,
        # since a no-op test call at t=0 wouldn't tell us much — the first
        # real frame call in the render loop determines what sticks.
        "position": None,
        "normal": None,
        "combined": None,
    }
    print(f"  Clipping plane control resolved via: get={used_get} add={used_add} "
          f"enable={used_enable} (position/normal resolved on first frame)")
    return handle, api


def apply_clip_plane(handle, api, point, normal):
    """Position the clipping plane for one frame. Tries setPlane(point,
    normal) first, then separate setPosition(...)/setNormal(...) calls.
    Mutates `api` in place to remember whichever channel worked so
    subsequent frames don't re-probe. Returns True if anything was applied."""
    if handle is None:
        return False

    applied = False

    if api.get("combined") is not False:
        for name in (CLIP_COMBINED_CANDIDATES if api.get("combined") is None else [api["combined"]]):
            fn = getattr(handle, name, None)
            if fn is None:
                continue
            try:
                fn(point, normal)
                api["combined"] = name
                applied = True
                break
            except Exception:
                continue
        if not applied and api.get("combined") is None:
            api["combined"] = False  # tried once, didn't work — don't retry every frame

    if not applied:
        pos_names = CLIP_POSITION_CANDIDATES if api.get("position") is None else [api["position"]]
        for name in pos_names:
            fn = getattr(handle, name, None)
            if fn is None:
                continue
            try:
                fn(point)
                api["position"] = name
                applied = True
                break
            except Exception:
                continue
        if not applied and api.get("position") is None:
            api["position"] = False

        norm_names = CLIP_NORMAL_CANDIDATES if api.get("normal") is None else [api["normal"]]
        for name in norm_names:
            fn = getattr(handle, name, None)
            if fn is None:
                continue
            try:
                fn(normal)
                api["normal"] = name
                applied = True
                break
            except Exception:
                continue
        if not applied and api.get("normal") is None:
            api["normal"] = False

    return applied


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
         "Model set to frame the sweep around (blank = whole scene):", ""),
        ("camera_selection", lux.DIALOG_TEXT,
         "Camera(s)/Studio(s) to shoot — blank = current viewport camera, 'ALL' = every one found, "
         "or a comma-separated list of names:", DEFAULT_OPTIONS["camera_selection"]),
        ("num_frames", lux.DIALOG_INTEGER, "Total frames:", DEFAULT_OPTIONS["num_frames"], (10, 600)),
        ("fps", lux.DIALOG_INTEGER, "Frames per second:", DEFAULT_OPTIONS["fps"], (1, 60)),
        ("hold_start", lux.DIALOG_INTEGER, "Hold frames before the sweep starts:",
         DEFAULT_OPTIONS["hold_start"], (0, 200)),
        ("hold_end", lux.DIALOG_INTEGER, "Hold frames at full cutaway:",
         DEFAULT_OPTIONS["hold_end"], (0, 400)),
        (lux.DIALOG_LABEL, "-- clip plane sweep --"),
        ("clip_axis", lux.DIALOG_ITEM, "Sweep axis (plane normal):",
         DEFAULT_OPTIONS["clip_axis"], AXIS_OPTIONS),
        ("sweep_direction", lux.DIALOG_ITEM, "Sweep direction along that axis:",
         DEFAULT_OPTIONS["sweep_direction"], SWEEP_DIRECTIONS),
        ("clip_margin_mult", lux.DIALOG_DOUBLE,
         "Margin beyond the bounding box (1.0 = exactly at the edge, 1.2 = 20% past it):",
         DEFAULT_OPTIONS["clip_margin_mult"], (1.0, 3.0)),
        ("clip_start_override", lux.DIALOG_DOUBLE,
         "Manual sweep start offset (blank/auto-bbox used if bounding box resolves):", None),
        ("clip_end_override", lux.DIALOG_DOUBLE,
         "Manual sweep end offset (blank/auto-bbox used if bounding box resolves):", None),
        (lux.DIALOG_LABEL, "-- dynamic background / lighting (secondary to the sweep) --"),
        ("render_ground", lux.DIALOG_CHECK, "Render ground (shadow/reflection catcher)",
         DEFAULT_OPTIONS["render_ground"]),
        ("rotate_environment", lux.DIALOG_CHECK, "Rotate HDRI environment during the sweep",
         DEFAULT_OPTIONS["rotate_environment"]),
        ("environment_rotation_degrees", lux.DIALOG_DOUBLE, "Environment rotation over full clip (degrees):",
         DEFAULT_OPTIONS["environment_rotation_degrees"], (0.0, 360.0)),
        ("brightness_ramp", lux.DIALOG_CHECK, "Ramp brightness during the sweep",
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
        title="Cutaway / Cross-Section Reveal",
        desc="Sweeps a clipping plane through the assembly's bounding box, camera held static, "
             "one video per selected camera/Studio. Clipping-plane API is EXPERIMENTAL on this "
             "KeyShot build — see the script header for what's confirmed vs. probed.",
        values=values,
        id="cutaway_reveal_dialog",
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

    opts["clip_axis"] = norm_item(opts.get("clip_axis"), AXIS_OPTIONS)
    opts["sweep_direction"] = norm_item(opts.get("sweep_direction"), SWEEP_DIRECTIONS)
    return opts


# --------------------------------------------------------------------------
# Frame profile (same easing approach as build_reveal_profile() in the
# hero reveal script — monotonic ease, no overshoot, no reversal)
# --------------------------------------------------------------------------

def build_sweep_profile(num_frames, hold_start, hold_end):
    """List of length num_frames, values in [0,1]: 0 = sweep start,
    1 = sweep end. Monotonic — a single clean ease."""
    hold_start = min(hold_start, max(0, num_frames // 3))
    hold_end = min(hold_end, max(0, num_frames // 2))
    travel = max(2, num_frames - hold_start - hold_end)

    profile = [0.0] * hold_start
    for i in range(travel):
        t = i / max(1, travel - 1)
        profile.append(0.5 - 0.5 * math.cos(math.pi * t))
    profile += [1.0] * hold_end

    if len(profile) < num_frames:
        profile += [1.0] * (num_frames - len(profile))
    return profile[:num_frames]


# --------------------------------------------------------------------------
# Sweep range resolution
# --------------------------------------------------------------------------

def resolve_sweep_range(target_node, axis, margin_mult, start_override, end_override):
    """Resolve the scalar start/end offsets (along `axis`, measured from
    world origin) that the clip plane sweeps between. Prefers the
    bounding-box probe; falls back to manual overrides; falls back again to
    an untuned default range with a loud warning if neither is available."""
    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]

    lo, hi, bbox_api = resolve_bounding_box(target_node)
    if lo is not None and hi is not None:
        lo_a, hi_a = lo[axis_index], hi[axis_index]
        extent = hi_a - lo_a
        margin = extent * (max(margin_mult, 1.0) - 1.0) / 2.0
        return lo_a - margin, hi_a + margin

    if start_override is not None and end_override is not None:
        print(f"  Using manual sweep overrides: start={start_override} end={end_override}")
        return float(start_override), float(end_override)

    print("  [warn] no bounding box and no manual overrides — falling back to an untuned "
          "default range of -100..100 along the sweep axis. Set clip_start_override / "
          "clip_end_override in the dialog for a real result.")
    return -100.0, 100.0


# --------------------------------------------------------------------------
# One shot: sweep the plane for a single target, render its frames
# --------------------------------------------------------------------------

def shoot_one_cutaway(opts, target, render_opts, output_folder, queueing, target_node,
                       clip_handle, clip_api, axis_vec, start_offset, end_offset):
    label = target if target else "current"
    safe_name = sanitize_name(label)
    video_name = f"{opts.get('video_name_prefix') or 'CUTAWAY'}_{safe_name}.mp4"
    frame_folder = os.path.join(output_folder, f"{safe_name}_cutaway_frames")

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

    try:
        center = vec_xyz(target_node.getCenter(world=True))
    except Exception as e:
        print(f"  [warn] couldn't read target center, using world origin: {e}")
        center = (0.0, 0.0, 0.0)

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

    profile = build_sweep_profile(opts["num_frames"], opts["hold_start"], opts["hold_end"])

    reversed_sweep = opts.get("sweep_direction") == "Negative -> Positive"
    sweep_start = end_offset if reversed_sweep else start_offset
    sweep_end = start_offset if reversed_sweep else end_offset

    env_rotate_available = True
    clip_available = clip_handle is not None

    for f, t in enumerate(profile):
        # --- clip plane sweep ---
        if clip_available:
            offset_scalar = sweep_start + (sweep_end - sweep_start) * t
            point = vadd(center, vscale(axis_vec, offset_scalar))
            ok = apply_clip_plane(clip_handle, clip_api, point, axis_vec)
            if not ok and f == 0:
                clip_available = False
                print("  [warn] clip plane position/normal calls didn't work on frame 0 — "
                      "disabling the sweep for this target, frames will render un-clipped")

        # --- environment rotation (continuous across the whole clip) ---
        if env is not None and env_rotate_available and opts.get("rotate_environment") and start_rotation is not None:
            try:
                sweep = opts["environment_rotation_degrees"] * (f / max(1, len(profile) - 1))
                env.setRotation(start_rotation + sweep)
            except Exception as e:
                env_rotate_available = False
                print(f"  [warn] environment rotation not available in this KeyShot version "
                      f"({e}) — continuing without it")

        # --- brightness ramp, synced to the sweep ---
        if env is not None and opts.get("brightness_ramp") and start_brightness is not None:
            try:
                start_mult = opts.get("brightness_ramp_start_mult", 0.6)
                low = start_brightness * start_mult
                env.setBrightness(low + (start_brightness - low) * t)
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

        if f % 10 == 0 or f == len(profile) - 1:
            print(f"    frame {f + 1}/{len(profile)} (t={t:.2f})")

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

    result["frame_count"] = len(profile)
    result["ok"] = True

    if queueing:
        result["status"] = "queued (pending encode)"
        return result

    return encode_one_cutaway(result, opts, output_folder)


def encode_one_cutaway(result, opts, output_folder):
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
# Run
# --------------------------------------------------------------------------

def run_cutaway(opts):
    print(f"lux.isHeadless() = {lux.isHeadless()}")

    output_folder = opts.get("output_folder") or "."
    abs_folder = os.path.abspath(output_folder)
    manifest_path = os.path.join(abs_folder, "cutaway_manifest.csv")
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

    axis = opts.get("clip_axis", "X")
    axis_vec = AXIS_VECTORS.get(axis, AXIS_VECTORS["X"])

    print("Resolving clipping-plane control (experimental — see script header)...")
    clip_handle, clip_api = resolve_clipping_plane()

    print("Resolving sweep range from bounding box (experimental — see script header)...")
    start_offset, end_offset = resolve_sweep_range(
        target_node, axis,
        opts.get("clip_margin_mult", 1.15),
        opts.get("clip_start_override"),
        opts.get("clip_end_override"),
    )
    print(f"  Sweep axis={axis} start={start_offset:.3f} end={end_offset:.3f}")

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
        result = shoot_one_cutaway(opts, target, render_opts, output_folder, queueing, target_node,
                                    clip_handle, clip_api, axis_vec, start_offset, end_offset)
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
                    log(encode_one_cutaway(result, opts, output_folder))
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
        run_cutaway(options)
