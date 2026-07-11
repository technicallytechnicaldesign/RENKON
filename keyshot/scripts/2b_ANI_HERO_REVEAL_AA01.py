# AUTHOR tajf
# REV AA01
# HEADLESS COMPLIANT
"""
KeyShot Hero Reveal Shot
===========================

A simple, reliable camera move: track straight in (or straight out) to a
chosen camera's own framing, optionally craning up or down at the same
time, while the HDRI environment slowly rotates and brightness ramps up in
sync with the arrival. Optionally imports the shot's object into a named
Model Set that already carries a GUI-authored animation (e.g. a rotate),
and plays that animation in sync with the render.

Built for a scene with many cameras already set up: you can target the
current viewport camera (single ad hoc shot), one named camera/Studio, a
comma-separated handful, or every camera in the scene — one reveal video is
produced per target.

--------------------------------------------------------------------------
OBJECT IMPORT + MODEL SET ANIMATION
--------------------------------------------------------------------------
KeyShot's native keyframe/Animation-timeline feature isn't something this
pipeline can *author* from a script — there's no confirmed API for
creating keyframes. What IS confirmed: reading/advancing the CURRENT frame
of an animation that already exists, built in the GUI:
lux.getAnimationFrame(), lux.setAnimationFrame(frame),
lux.getAnimationInfo(). So the intended workflow is: build the rotate (or
whatever) animation on a Model Set in the KeyShot GUI once, then this
script imports the part into that same Model Set every run (confirmed:
lux.getModelSets()/setModelSets()/lux.importFile(opts={"model_set_import_
to": 1, ...})) and steps the existing animation's current frame in sync
with the shot's own timeline. It will NOT create the Model Set for you —
importing into one that doesn't already exist would just import into
nothing with the animation missing, so this checks first and falls back to
a plain import with a warning if the name isn't found.

lux.getAnimationInfo()'s docs don't specify whether it returns a dict or a
tuple, so its result is parsed defensively.

--------------------------------------------------------------------------
OBJECT ALWAYS CENTERED
--------------------------------------------------------------------------
By default the look-at pivot is computed once (from the hero camera's own
framing) and held fixed. With "object always centered" enabled, it instead
re-reads the object's live world-space center every frame
(SceneNode.getCenter(world=True), the same confirmed call already used in
the scatter/turntable scripts) and re-aims there each frame — so if a
Model Set animation rotates around a pivot that isn't dead-center, the
camera still tracks the object instead of the empty point where it used to
be. Since setCameraLookAt() puts whatever point it's given at the exact
center of frame, continuously re-aiming at the object's live center is
what keeps it centered in frame throughout the shot.

--------------------------------------------------------------------------
GROUND RENDERING
--------------------------------------------------------------------------
Confirmed (2026-07-11, KeyShot 11.0 scripting reference at
media.keyshot.com/scripting/doc/11.0/lux.html): env.setGroundShadows(bool)
and env.setGroundReflections(bool) are the real setter names, alongside the
getters this script already relied on. This script still tries them via a
short candidate list (setGroundShadows / enableGroundShadows /
setGroundShadowsEnabled, same for reflections) rather than calling them
directly, since that list costs nothing and keeps the script working on
older KeyShot versions where the confirmed name might differ — but the
first candidate in each list is now a documented API, not a guess.

--------------------------------------------------------------------------
WHY THERE'S NO ORBIT/ARC
--------------------------------------------------------------------------
An earlier version also swung the camera sideways around the object
(orbiting it around its own "up" vector). That's fragile — Rodrigues'
rotation formula leaves a vector unchanged when the rotation axis is
parallel to it, so for any camera whose up vector happens to be closely
aligned with the camera-to-object direction, the orbit silently collapsed
to zero and only the dolly (zoom) was visible. It's been removed in favor
of a single, monotonic zoom track plus an optional vertical crane — both
plain vector addition, no rotation involved.

--------------------------------------------------------------------------
STUDIOS vs CAMERAS
--------------------------------------------------------------------------
A Studio pairs a camera with its matching environment/lighting (and image
style) — confirmed: lux.getStudios(), lux.getStudio(name),
lux.setActiveStudio(name). Where a target name matches a Studio, this
script activates the Studio; a plain camera name just switches the camera
and leaves whatever environment is already active.

--------------------------------------------------------------------------
QUEUEING
--------------------------------------------------------------------------
"Add to queue" adds every rendered frame, for every camera, to KeyShot's
render queue instead of rendering immediately. A video can only be encoded
once every one of its frames has actually finished rendering, so without
"process queue after" this script queues everything and stops there rather
than guessing at encoding a possibly-incomplete folder.

--------------------------------------------------------------------------
CONFIRMED vs EXPERIMENTAL
--------------------------------------------------------------------------
Confirmed (KeyShot's own scripting reference): lux.getCameraPosition/
LookAt/Up, setCameraPosition/LookAt, lux.getActiveEnvironment(),
env.getBrightness/setBrightness, env.setBackplateImage, lux.renderImage,
lux.encodeVideo, lux.openFile(), lux.getStudios(), lux.getStudio(name),
lux.setActiveStudio(name), lux.getCameras(), lux.setCamera(name),
lux.getModelSets(), lux.setModelSets(names), lux.getImportOptions(),
lux.importFile(path, opts=...), lux.getAnimationFrame(),
lux.setAnimationFrame(frame), SceneNode.getCenter(world=True),
env ground-state getters (isGroundShadowsEnabled-style),
lux.getRenderOptions()/setAddToQueue()/setMaxTimeRendering(),
lux.processQueue().
Inferred-but-unconfirmed: env.setRotation() — the get/set pairing pattern
is consistent everywhere else in this API, but the literal setRotation
signature isn't in the docs. (The ground shadow/reflection setter names
were in this same unconfirmed category until a 2026-07-11 research pass
found them documented — see the GROUND RENDERING note above; they're
confirmed now.)
Experimental: lux.getAnimationInfo()'s exact return shape (dict vs tuple)
isn't documented; the optional product-turntable spin's Matrix.rotate()
signature also isn't confirmed (same flag as the scatter animation
script) — if you have a real Model Set animation to drive instead, that's
the more reliable route.

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
FRAME_PATTERN = "reveal_frame.%d.png"

MANIFEST_FIELDS = ["timestamp", "scene_template", "target", "video_name", "output_path", "status"]

ZOOM_DIRECTIONS = ["Zoom In", "Zoom Out"]
VERTICAL_DIRECTIONS = ["Rise into frame", "Descend into frame"]

DEFAULT_OPTIONS = {
    "scene_template_path": "",
    "import_file_path": "",
    "import_model_set_name": "New Model Set 1",
    "play_model_animation": True,
    "camera_selection": "ALL",
    "num_frames": 90,
    "fps": 24,
    "hold_start": 4,
    "hold_end": 20,
    "zoom_direction": "Zoom In",
    "zoom_amount": 1.6,
    "vertical_move_enabled": False,
    "vertical_move_direction": "Rise into frame",
    "vertical_move_amount": 0.3,
    "object_always_centered": False,
    "render_ground": True,
    "rotate_environment": True,
    "environment_rotation_degrees": 45.0,
    "brightness_ramp": True,
    "brightness_ramp_start_mult": 0.25,
    "backplate_image": "",
    "product_turntable": False,
    "product_turntable_degrees": 15.0,
    "turntable_name_filter": "",
    "preview_mode": True,
    "add_to_queue": False,
    "process_queue_after": False,
    "output_folder": "",
    "video_name_prefix": "REVEAL",
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
    Confirmed: lux.openFile() opens a file (as opposed to lux.importFile(),
    documented for bringing geometry into an existing scene). Non-fatal."""
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
    """Import a part file into a named, already-existing Model Set (so it
    picks up whatever GUI-authored animation lives on that Model Set).
    Confirmed: lux.getModelSets(), lux.setModelSets(), lux.getImportOptions(),
    lux.importFile(path, opts={'model_set_import_to': 1, ...}) (1 = Active).
    Does NOT create the Model Set if missing -- a freshly-created empty one
    wouldn't carry the original animation, so this warns and falls back to
    a plain import instead of silently doing the wrong thing."""
    if not file_path:
        return True

    try:
        existing = lux.getModelSets()
    except Exception as e:
        print(f"[warn] couldn't list model sets: {e}")
        existing = []

    if model_set_name not in existing:
        print(f"[warn] model set '{model_set_name}' not found in the loaded scene "
              f"(found: {existing}) — importing without a specific model set target, "
              f"so any animation on '{model_set_name}' won't apply.")
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


def resolve_animation_frame_count():
    """Best-effort resolution of the scene animation's total frame count.
    lux.getAnimationInfo() is confirmed to return duration + frame count,
    but the exact shape (dict vs tuple) isn't documented -- this tries a
    couple of reasonable shapes and returns None if none pan out."""
    try:
        info = lux.getAnimationInfo()
    except Exception as e:
        print(f"[warn] couldn't get animation info: {e}")
        return None
    if isinstance(info, dict):
        for key in ("frames", "frame_count", "num_frames", "total_frames"):
            if key in info:
                return info[key]
    if isinstance(info, (list, tuple)) and len(info) >= 2:
        return info[1]
    print(f"[warn] couldn't interpret lux.getAnimationInfo() result ({info!r}) — "
          f"animation sync will be skipped")
    return None


def get_focus_node(model_set_name):
    """Resolve the node whose live center the camera should track when
    'object always centered' is enabled. Prefers the named model set (the
    thing actually being shot); falls back to the whole scene."""
    root = lux.getSceneTree()
    if model_set_name:
        try:
            matches = root.find(name=model_set_name, types=lux.NODE_TYPE_MODEL_SET)
            if matches:
                return matches[0]
        except Exception as e:
            print(f"  [warn] couldn't find model set '{model_set_name}' for focus tracking: {e}")
    return root


def set_ground_rendering(env, enabled):
    """Toggle the environment's ground shadow/reflection catcher. Getters
    for this are confirmed (env has isGroundShadowsEnabled-style calls per
    KeyShot's own scripting reference), but the exact setter names for
    turning shadows/reflections on and off aren't spelled out in the
    reference available here -- tries a short list of plausible names for
    each and reports whichever actually worked, same defensive pattern
    used elsewhere in this pipeline for genuinely uncertain calls."""
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
# Camera / Studio selection
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
    None on failure."""
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
# Vector helpers
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


def resolve_filter(value, sentinel="ALL"):
    """Normalize a name-filter dialog field: None, '', or the sentinel all
    mean 'no filter' (match everything)."""
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


def compute_dist_mult(t, zoom_direction, zoom_amount):
    """Single monotonic dolly. 'Zoom In' starts far (zoom_amount x hero
    distance) and arrives at hero distance. 'Zoom Out' starts close (hero
    distance / zoom_amount) and arrives at hero distance."""
    amount = max(zoom_amount, 1.0001)
    start_mult = amount if zoom_direction == "Zoom In" else 1.0 / amount
    return 1.0 + (start_mult - 1.0) * (1.0 - t)


def compute_vertical_offset(t, enabled, direction, amount, hero_distance):
    """Straight vertical crane, zero at t=1 so it always lands exactly on
    the hero framing regardless of amount/direction."""
    if not enabled or amount <= 0:
        return 0.0
    sign = -1.0 if direction == "Rise into frame" else 1.0
    return sign * amount * hero_distance * (1.0 - t)


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
        (lux.DIALOG_LABEL, "-- object import + animation --"),
        ("import_file_path", lux.DIALOG_FILE,
         "Part file to import into the model set below (blank = use whatever's already in the scene):", None),
        ("import_model_set_name", lux.DIALOG_TEXT,
         "Model set to import into (must already exist, e.g. with your rotate animation on it):",
         DEFAULT_OPTIONS["import_model_set_name"]),
        ("play_model_animation", lux.DIALOG_CHECK,
         "Play that model set's animation in sync with the shot",
         DEFAULT_OPTIONS["play_model_animation"]),
        ("camera_selection", lux.DIALOG_TEXT,
         "Camera(s)/Studio(s) to shoot — blank = current viewport camera, 'ALL' = every one found, "
         "or a comma-separated list of names:", DEFAULT_OPTIONS["camera_selection"]),
        ("num_frames", lux.DIALOG_INTEGER, "Total frames:", DEFAULT_OPTIONS["num_frames"], (10, 600)),
        ("fps", lux.DIALOG_INTEGER, "Frames per second:", DEFAULT_OPTIONS["fps"], (1, 60)),
        ("hold_start", lux.DIALOG_INTEGER, "Hold frames before the move starts:",
         DEFAULT_OPTIONS["hold_start"], (0, 200)),
        ("hold_end", lux.DIALOG_INTEGER, "Hold frames at final hero framing:",
         DEFAULT_OPTIONS["hold_end"], (0, 400)),
        (lux.DIALOG_LABEL, "-- camera move (ends on each target's own framing) --"),
        ("zoom_direction", lux.DIALOG_ITEM, "Zoom direction:",
         DEFAULT_OPTIONS["zoom_direction"], ZOOM_DIRECTIONS),
        ("zoom_amount", lux.DIALOG_DOUBLE, "Zoom amount (x hero distance):",
         DEFAULT_OPTIONS["zoom_amount"], (1.05, 5.0)),
        ("vertical_move_enabled", lux.DIALOG_CHECK, "Also move on the vertical axis (crane up/down)",
         DEFAULT_OPTIONS["vertical_move_enabled"]),
        ("vertical_move_direction", lux.DIALOG_ITEM, "Vertical direction:",
         DEFAULT_OPTIONS["vertical_move_direction"], VERTICAL_DIRECTIONS),
        ("vertical_move_amount", lux.DIALOG_DOUBLE, "Vertical travel (x hero distance):",
         DEFAULT_OPTIONS["vertical_move_amount"], (0.0, 2.0)),
        ("object_always_centered", lux.DIALOG_CHECK,
         "Object always in center of frame (camera continuously re-aims at it)",
         DEFAULT_OPTIONS["object_always_centered"]),
        (lux.DIALOG_LABEL, "-- dynamic background / lighting --"),
        ("render_ground", lux.DIALOG_CHECK, "Render ground (shadow/reflection catcher)",
         DEFAULT_OPTIONS["render_ground"]),
        ("rotate_environment", lux.DIALOG_CHECK, "Rotate HDRI environment (moving reflections)",
         DEFAULT_OPTIONS["rotate_environment"]),
        ("environment_rotation_degrees", lux.DIALOG_DOUBLE, "Environment rotation over full clip (degrees):",
         DEFAULT_OPTIONS["environment_rotation_degrees"], (0.0, 360.0)),
        ("brightness_ramp", lux.DIALOG_CHECK, "Ramp brightness up during the move",
         DEFAULT_OPTIONS["brightness_ramp"]),
        ("brightness_ramp_start_mult", lux.DIALOG_DOUBLE, "Starting brightness (x current):",
         DEFAULT_OPTIONS["brightness_ramp_start_mult"], (0.0, 1.0)),
        ("backplate_image", lux.DIALOG_FILE, "Optional static backplate image (blank = none):", None),
        (lux.DIALOG_LABEL, "-- optional --"),
        ("product_turntable", lux.DIALOG_CHECK,
         "Slow product turntable spin (experimental; use the model set animation above instead if you have one)",
         DEFAULT_OPTIONS["product_turntable"]),
        ("product_turntable_degrees", lux.DIALOG_DOUBLE, "Turntable rotation over full clip (degrees):",
         DEFAULT_OPTIONS["product_turntable_degrees"], (0.0, 360.0)),
        ("turntable_name_filter", lux.DIALOG_TEXT, "Turntable parts matching (ALL = every part):",
         "ALL"),
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
        title="Hero Reveal Shot",
        desc="Optionally imports a part into an animated Model Set, then zooms into (or out to) each "
             "selected camera/Studio's own framing while the animation plays.",
        values=values,
        id="hero_reveal_dialog",
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

    opts["zoom_direction"] = norm_item(opts.get("zoom_direction"), ZOOM_DIRECTIONS)
    opts["vertical_move_direction"] = norm_item(opts.get("vertical_move_direction"), VERTICAL_DIRECTIONS)
    return opts


# --------------------------------------------------------------------------
# Frame profile
# --------------------------------------------------------------------------

def build_reveal_profile(num_frames, hold_start, hold_end):
    """List of length num_frames, values in [0,1]: 0 = move start, 1 = hero
    framing. Monotonic — a single clean ease, no overshoot, no reversal."""
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
# Optional turntable target parts (mirrors the scatter-animation approach)
# --------------------------------------------------------------------------

def get_turntable_parts(name_filter=None):
    root = lux.getSceneTree()
    candidates = root.find(name=name_filter) if name_filter else root.find("")
    parts = []
    for node in candidates:
        try:
            if node.isObject():
                parts.append(node)
        except Exception:
            continue
    return parts


# --------------------------------------------------------------------------
# One shot: move into a single target's framing, render its frames
# --------------------------------------------------------------------------

def shoot_one_reveal(opts, target, render_opts, output_folder, queueing, focus_node, anim_total):
    label = target if target else "current"
    safe_name = sanitize_name(label)
    video_name = f"{opts.get('video_name_prefix') or 'REVEAL'}_{safe_name}.mp4"
    frame_folder = os.path.join(output_folder, f"{safe_name}_reveal_frames")

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

    # --- capture the hero framing for this target ---------------------------
    try:
        hero_pos = vec_xyz(lux.getCameraPosition())
        hero_lookat = vec_xyz(lux.getCameraLookAt())
        up = vec_xyz(lux.getCameraUp())
    except Exception as e:
        print(f"  [error] couldn't read the camera for '{label}' — is a camera active? ({e})")
        result["status"] = "FAILED (no active camera)"
        return result

    pivot = hero_lookat
    hero_offset = vsub(hero_pos, pivot)
    hero_distance = vlen(hero_offset)
    if hero_distance < 1e-6:
        print(f"  [error] camera position and look-at coincide for '{label}' — can't compute a move.")
        result["status"] = "FAILED (zero distance)"
        return result

    hero_dir = vnorm(hero_offset)
    up_unit = vnorm(up)

    print(f"  pos={tuple(round(x,2) for x in hero_pos)} look-at={tuple(round(x,2) for x in hero_lookat)}")

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

    turntable_parts = []
    if opts.get("product_turntable"):
        turntable_parts = get_turntable_parts(resolve_filter(opts.get("turntable_name_filter")))
        if turntable_parts:
            print(f"  Turntable: {len(turntable_parts)} part(s)")

    if not os.path.isdir(frame_folder):
        try:
            os.makedirs(frame_folder)
        except Exception as e:
            print(f"  [error] couldn't create frame folder '{frame_folder}': {e}")
            result["status"] = f"FAILED (frame folder: {e})"
            return result

    profile = build_reveal_profile(opts["num_frames"], opts["hold_start"], opts["hold_end"])

    zoom_direction = opts.get("zoom_direction", "Zoom In")
    zoom_amount = opts.get("zoom_amount", 1.6)
    vertical_enabled = opts.get("vertical_move_enabled", False)
    vertical_direction = opts.get("vertical_move_direction", "Rise into frame")
    vertical_amount = opts.get("vertical_move_amount", 0.0)
    always_centered = opts.get("object_always_centered", False)
    play_animation = bool(opts.get("play_model_animation")) and anim_total

    rotation_available = True
    env_rotate_available = True
    animation_sync_available = True
    prev_turntable_angle = 0.0

    for f, t in enumerate(profile):
        # --- pivot: fixed hero look-at, or the object's live center ---
        frame_pivot = pivot
        if always_centered and focus_node is not None:
            try:
                frame_pivot = vec_xyz(focus_node.getCenter(world=True))
            except Exception as e:
                print(f"  [warn] couldn't get live object center on frame {f}: {e}")

        # --- camera move: single monotonic zoom, plus optional vertical crane ---
        dist_mult_t = compute_dist_mult(t, zoom_direction, zoom_amount)
        base_offset = vscale(hero_dir, hero_distance * dist_mult_t)
        vertical_t = compute_vertical_offset(t, vertical_enabled, vertical_direction,
                                              vertical_amount, hero_distance)
        pos_t = vadd(vadd(frame_pivot, base_offset), vscale(up_unit, vertical_t))
        try:
            lux.setCameraPosition(pos_t)
            lux.setCameraLookAt(pt=frame_pivot)  # centers frame_pivot exactly in frame
        except Exception as e:
            print(f"  [warn] couldn't set camera on frame {f}: {e}")

        # --- play the model set's animation in sync with the shot ---
        if play_animation and animation_sync_available:
            anim_frame = int(round((anim_total - 1) * t)) if anim_total > 1 else 0
            try:
                lux.setAnimationFrame(anim_frame)
            except Exception as e:
                animation_sync_available = False
                print(f"  [warn] couldn't set animation frame ({e}) — continuing without animation sync")

        # --- environment rotation (continuous across the whole clip) ---
        if env is not None and env_rotate_available and opts.get("rotate_environment") and start_rotation is not None:
            try:
                sweep = opts["environment_rotation_degrees"] * (f / max(1, len(profile) - 1))
                env.setRotation(start_rotation + sweep)
            except Exception as e:
                env_rotate_available = False
                print(f"  [warn] environment rotation not available in this KeyShot version "
                      f"({e}) — continuing without it")

        # --- brightness ramp, synced to the move ---
        if env is not None and opts.get("brightness_ramp") and start_brightness is not None:
            try:
                start_mult = opts.get("brightness_ramp_start_mult", 0.25)
                low = start_brightness * start_mult
                env.setBrightness(low + (start_brightness - low) * t)
            except Exception as e:
                print(f"  [warn] couldn't ramp brightness on frame {f}: {e}")

        # --- optional experimental product turntable (skip if model-set animation is driving) ---
        if turntable_parts and rotation_available and not play_animation:
            try:
                target_angle = opts["product_turntable_degrees"] * (f / max(1, len(profile) - 1))
                delta_deg = target_angle - prev_turntable_angle
                prev_turntable_angle = target_angle
                axis_v = luxmath.Vector(up)
                R = luxmath.Matrix().makeIdentity().rotate(delta_deg, axis_v)
                for node in turntable_parts:
                    node.applyTransform(R, absolute=False)
            except Exception as e:
                rotation_available = False
                print(f"  [warn] turntable rotation not available in this KeyShot version "
                      f"({e}) — continuing without it")

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

    # --- restore exact hero state (guards against any float drift) ----------
    try:
        lux.setCameraPosition(hero_pos)
        lux.setCameraLookAt(pt=hero_lookat)
    except Exception as e:
        print(f"  [warn] couldn't restore hero camera pose: {e}")
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

    return encode_one_reveal(result, opts, output_folder)


def encode_one_reveal(result, opts, output_folder):
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

def run_reveal(opts):
    print(f"lux.isHeadless() = {lux.isHeadless()}")

    output_folder = opts.get("output_folder") or "."
    abs_folder = os.path.abspath(output_folder)
    manifest_path = os.path.join(abs_folder, "reveal_manifest.csv")
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
    import_into_model_set(opts.get("import_file_path"), opts.get("import_model_set_name"))

    focus_node = None
    if opts.get("object_always_centered"):
        focus_node = get_focus_node(opts.get("import_model_set_name"))

    anim_total = None
    if opts.get("play_model_animation"):
        anim_total = resolve_animation_frame_count()
        if anim_total:
            print(f"Animation: {anim_total} frame(s) found, will sync to the shot")
        else:
            print("[info] no readable animation found — shots will run without animation sync")

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
        result = shoot_one_reveal(opts, target, render_opts, output_folder, queueing, focus_node, anim_total)
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
                    log(encode_one_reveal(result, opts, output_folder))
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
        run_reveal(options)
