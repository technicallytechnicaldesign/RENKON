            
          
                    
   
                                      

                                                                           
                                                                      
                                                    
                                                                         
                                                                     
              

                                                                         
                                                                        
                     

                                                                     
                                                                       
                                                                    

                                                                           
                                                                          
                                                                      
                                                                      
                                                                         
                                                                         
                                                                    
                                                                  
                                                                     
                                                                        
                                                                    
                                                                        
                                                                
                                                                       
                                                        

                                                                   
                                                                          
                                                                
                                                               
                                                                     
                                                                        
                                                                     

                                                                         
                                                                 
                                                                        
                                                                       
                                                   

                                                                         
                                                                          
            

                                                                         
                                                                    
                                                                     

                                                                     
                                                                       
                                                      
                                                                 
                                                                    
                                                                
                                                                      
                                                             
                                                           

                                                                     
                                                                        
                                                                       
                               

                                                                           
                                                                
   

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
                                                                              
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name or "").strip("_")
    return cleaned or random_suffix()


def logManifestRow(manifestPath, row):
    isNew = not os.path.isfile(manifestPath)
    with open(manifestPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)


def verify_frame_sequence(folder, filenames):
    missing = []
    for fn in filenames:
        p = os.path.join(folder, fn)
        try:
            if (not os.path.exists(p)) or os.stat(p).st_size < 512:
                missing.append(fn)
        except Exception:
            missing.append(fn)
    return (len(missing) == 0, missing)


def load_scene_template(path):
                                                                     
                                            
    if not path:
        return True
    try:
        lux.openFile(path, dontAsk=True)
        print("Loaded scene template: {0}".format(path))
        return True
    except Exception as e:
        print("[warn] couldn't load scene template '{0}': {1} -- "
              "continuing with whatever scene is currently open".format(path, e))
        return False


def import_into_model_set(file_path, model_set_name):
                                                                           
                                                                         
                                                                              
                                                                            
                                                                         
                                                              
    if not file_path:
        return True

    try:
        existing = lux.getModelSets()
    except Exception as e:
        print("[warn] couldn't list model sets: {0}".format(e))
        existing = []

    if not model_set_name or model_set_name not in existing:
        if model_set_name:
            print("[warn] model set '{0}' not found in the loaded scene "
                  "(found: {1}) -- importing without a specific model set target.".format(model_set_name, existing))
        try:
            lux.importFile(file_path)
            return True
        except Exception as e:
            print("[error] couldn't import '{0}': {1}".format(file_path, e))
            return False

    try:
        ok = lux.setModelSets([model_set_name])
        if not ok:
            print("[warn] couldn't cleanly activate model set '{0}' -- continuing anyway".format(model_set_name))
    except Exception as e:
        print("[warn] couldn't activate model set '{0}': {1}".format(model_set_name, e))

    try:
        import_opts = lux.getImportOptions()
    except Exception as e:
        print("[warn] couldn't get import options, using defaults: {0}".format(e))
        import_opts = {}
    import_opts["model_set_import_to"] = 1                        

    try:
        lux.importFile(file_path, opts=import_opts)
        print("Imported '{0}' into model set '{1}'".format(file_path, model_set_name))
        return True
    except Exception as e:
        print("[error] couldn't import '{0}' into '{1}': {2}".format(file_path, model_set_name, e))
        return False


def get_target_node(model_set_name):
                                                                          
                                                                        
                                                  
    root = lux.getSceneTree()
    if model_set_name:
        try:
            matches = root.find(name=model_set_name, types=lux.NODE_TYPE_MODEL_SET)
            if matches:
                return matches[0]
        except Exception as e:
            print("  [warn] couldn't find model set '{0}' for sweep framing: {1}".format(model_set_name, e))
    return root


def set_ground_rendering(env, enabled):
                                                                        
                                                                          
                                                                   
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
              "version -- 'render ground' setting was not applied. Run help(env) in the Scripting "
              "Console to find the exact method name on your build.")
        return False
    if DEBUG:
        print("  Ground rendering set to {0} (via {1} / {2})".format(enabled, used_shadow or '-', used_reflect or '-'))
    return True


                                                                            
                                                                
                                                                            

def resolve_camera_list(raw_value):
                                                 
                                                                              
                                                                      
                                                 
                                                                          
       
    v = (raw_value or "").strip()
    if not v:
        return None
    if v.upper() == "ALL":
        try:
            studios = list(lux.getStudios())
        except Exception as e:
            print("[warn] couldn't list studios: {0}".format(e))
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
            print("[warn] couldn't list cameras: {0}".format(e))
            cameras = []
        extras = [c for c in cameras if c not in covered]
        return studios + extras
    return [n.strip() for n in v.split(",") if n.strip()]


def activate_camera_or_studio(name):
                                                                            
                                                                          
                                                        

                                                                               
                                                                                
                                                                              
                                                                       
    try:
        studios = lux.getStudios()
    except Exception:
        studios = []

    if name in studios:
        try:
            lux.setActiveStudio(name)
        except Exception as e:
            print("  [warn] couldn't activate studio '{0}': {1}".format(name, e))
            return None
        cam = None
        get_studio = getattr(lux, "getStudio", None)
        if get_studio is not None:
            try:
                cam = get_studio(name).getCamera()
            except Exception:
                cam = None
        if not cam:
            try:
                cam = lux.getCamera()
            except Exception:
                cam = None
        if cam:
            try:
                lux.setCamera(cam)
            except Exception as e:
                print("  [warn] couldn't set camera '{0}' for studio '{1}': {2}".format(cam, name, e))
        return cam or name

    try:
        cameras = lux.getCameras()
    except Exception:
        cameras = []
    if name in cameras:
        try:
            lux.setCamera(name)
            return name
        except Exception as e:
            print("  [warn] couldn't set camera '{0}': {1}".format(name, e))
            return None

    print("  [warn] '{0}' not found as a studio or camera -- skipping".format(name))
    return None


                                                                            
                                                     
                                                                            

def vec_xyz(v):
    try:
        return (v[0], v[1], v[2])
    except Exception:
        pass
    try:
        return (v.x, v.y, v.z)
    except Exception:
        pass
    raise TypeError("Couldn't extract xyz from {0!r}".format(v))


def vadd(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def vscale(a, s): return (a[0] * s, a[1] * s, a[2] * s)


                                                                            
                                                                           
                                                          
                                                                            

def _parse_bbox_result(result):
                                                                       
                                                                    
                                                                         
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
            print("  Bounding box resolved via {0}({1}) -- min={2} max={3}".format(name, kwargs, lo, hi))
            return lo, hi, name
    print("  [warn] couldn't resolve a bounding box on this KeyShot version via any of "
          "getBoundingBox/getWorldBoundingBox/getBounds -- the sweep will fall back to "
          "manual clip_start_override/clip_end_override values (or an untuned default "
          "range if those are also blank). Run help(node) in the Scripting Console to "
          "find the exact call on your build.")
    return None, None, None


                                                                            
                                                                      
                                                                            

CLIP_GET_CANDIDATES = ["getClippingPlane", "getSection", "getCuttingPlane", "getClipPlane"]
CLIP_ADD_CANDIDATES = ["addClippingPlane", "createClippingPlane", "addSection", "createSection"]
CLIP_ENABLE_CANDIDATES = ["setEnabled", "enable", "setActive", "setVisible"]
CLIP_POSITION_CANDIDATES = ["setPosition", "setOffset", "setOrigin"]
CLIP_NORMAL_CANDIDATES = ["setNormal", "setDirection", "setAxis"]
CLIP_COMBINED_CANDIDATES = ["setPlane"]                                    


def resolve_clipping_plane():
                                                                          
                                                                           
                                                                         
                                                           
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
        print("  [warn] no clipping-plane API resolved on this KeyShot build -- tried "
              "getters {0} and creators {1}, none "
              "worked. The cutaway sweep will be SKIPPED; frames will render un-clipped. "
              "Run `dir(lux)` in the Scripting Console to find the real name and add it "
              "to the candidate lists at the top of this file.".format(CLIP_GET_CANDIDATES, CLIP_ADD_CANDIDATES))
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
                                                                           
                                                                           
                                                                    
        "position": None,
        "normal": None,
        "combined": None,
    }
    print("  Clipping plane control resolved via: get={0} add={1} "
          "enable={2} (position/normal resolved on first frame)".format(used_get, used_add, used_enable))
    return handle, api


def apply_clip_plane(handle, api, point, normal):
                                                                       
                                                                       
                                                                  
                                                                              
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
            api["combined"] = False                                                      

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


                                                                            
                                                            
                                                                            

def get_options():
    if lux.isHeadless():
        print("Headless session detected -- skipping dialog, using DEFAULT_OPTIONS.")
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
         "Camera(s)/Studio(s) to shoot -- blank = current viewport camera, 'ALL' = every one found, "
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
             "KeyShot build -- see the script header for what's confirmed vs. probed.",
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


                                                                            
                                                                      
                                                                  
                                                                            

def build_sweep_profile(num_frames, hold_start, hold_end):
                                                                   
                                                       
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


                                                                            
                        
                                                                            

def resolve_sweep_range(target_node, axis, margin_mult, start_override, end_override):
                                                                        
                                                                 
                                                                           
                                                                            
    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]

    lo, hi, bbox_api = resolve_bounding_box(target_node)
    if lo is not None and hi is not None:
        lo_a, hi_a = lo[axis_index], hi[axis_index]
        extent = hi_a - lo_a
        margin = extent * (max(margin_mult, 1.0) - 1.0) / 2.0
        return lo_a - margin, hi_a + margin

    if start_override is not None and end_override is not None:
        print("  Using manual sweep overrides: start={0} end={1}".format(start_override, end_override))
        return float(start_override), float(end_override)

    print("  [warn] no bounding box and no manual overrides -- falling back to an untuned "
          "default range of -100..100 along the sweep axis. Set clip_start_override / "
          "clip_end_override in the dialog for a real result.")
    return -100.0, 100.0


                                                                            
                                                                  
                                                                            

def shoot_one_cutaway(opts, target, render_opts, output_folder, queueing, target_node,
                       clip_handle, clip_api, axis_vec, start_offset, end_offset):
    label = target if target else "current"
    safe_name = sanitize_name(label)
    video_name = "{0}_{1}.mp4".format(opts.get('video_name_prefix') or 'CUTAWAY', safe_name)
    frame_folder = os.path.join(output_folder, "{0}_cutaway_frames".format(safe_name))

    result = {"target": label, "video_name": video_name, "frame_folder": frame_folder,
              "frame_count": 0, "ok": False, "status": "FAILED", "output_path": ""}

    if target is not None:
        resolved_cam = activate_camera_or_studio(target)
        if resolved_cam is None:
            result["status"] = "FAILED (couldn't activate '{0}')".format(target)
            return result
        print("--- Shooting '{0}' (camera '{1}') ---".format(target, resolved_cam))
    else:
        print("--- Shooting current viewport camera ---")

    try:
        center = vec_xyz(target_node.getCenter(world=True))
    except Exception as e:
        print("  [warn] couldn't read target center, using world origin: {0}".format(e))
        center = (0.0, 0.0, 0.0)

                                                                              
    env = None
    start_rotation, start_brightness = None, None
    try:
        env = lux.getActiveEnvironment()
    except Exception as e:
        print("  [warn] couldn't get active environment: {0}".format(e))
    if env is not None:
        try:
            start_rotation = env.getRotation()
        except Exception as e:
            print("  [warn] couldn't read environment rotation: {0}".format(e))
        try:
            start_brightness = env.getBrightness()
        except Exception as e:
            print("  [warn] couldn't read environment brightness: {0}".format(e))
    if env is not None and opts.get("backplate_image"):
        try:
            env.setBackplateImage(opts["backplate_image"])
        except Exception as e:
            print("  [warn] couldn't set backplate image: {0}".format(e))
    if env is not None:
        set_ground_rendering(env, bool(opts.get("render_ground", True)))

    if not os.path.isdir(frame_folder):
        try:
            os.makedirs(frame_folder)
        except Exception as e:
            print("  [error] couldn't create frame folder '{0}': {1}".format(frame_folder, e))
            result["status"] = "FAILED (frame folder: {0})".format(e)
            return result

    profile = build_sweep_profile(opts["num_frames"], opts["hold_start"], opts["hold_end"])

    reversed_sweep = opts.get("sweep_direction") == "Negative -> Positive"
    sweep_start = end_offset if reversed_sweep else start_offset
    sweep_end = start_offset if reversed_sweep else end_offset

    env_rotate_available = True
    clip_available = clip_handle is not None

    for f, t in enumerate(profile):
                                  
        if clip_available:
            offset_scalar = sweep_start + (sweep_end - sweep_start) * t
            point = vadd(center, vscale(axis_vec, offset_scalar))
            ok = apply_clip_plane(clip_handle, clip_api, point, axis_vec)
            if not ok and f == 0:
                clip_available = False
                print("  [warn] clip plane position/normal calls didn't work on frame 0 -- "
                      "disabling the sweep for this target, frames will render un-clipped")

                                                                         
        if env is not None and env_rotate_available and opts.get("rotate_environment") and start_rotation is not None:
            try:
                sweep = opts["environment_rotation_degrees"] * (f / max(1, len(profile) - 1))
                                                                           
                                                                                
                                                                       
                env.setRotation((start_rotation + sweep) % 360.0)
            except Exception as e:
                env_rotate_available = False
                print("  [warn] environment rotation not available in this KeyShot version "
                      "({0}) -- continuing without it".format(e))

                                                      
        if env is not None and opts.get("brightness_ramp") and start_brightness is not None:
            try:
                start_mult = opts.get("brightness_ramp_start_mult", 0.6)
                low = start_brightness * start_mult
                env.setBrightness(low + (start_brightness - low) * t)
            except Exception as e:
                print("  [warn] couldn't ramp brightness on frame {0}: {1}".format(f, e))

        frame_file = FRAME_PATTERN % f
        frame_path = os.path.join(frame_folder, frame_file)
        try:
            if render_opts is not None:
                lux.renderImage(frame_path, width=opts["width"], height=opts["height"], opts=render_opts)
            else:
                lux.renderImage(frame_path, width=opts["width"], height=opts["height"])
        except Exception as e:
            print("  [warn] couldn't render frame {0}: {1}".format(f, e))

        if f % 10 == 0 or f == len(profile) - 1:
            print("    frame {0}/{1} (t={2:.2f})".format(f + 1, len(profile), t))

                                                                             
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
                                                                     
                                                                         
                                                                       
    if not result.get("ok"):
        return result

                                                                               
                                                                            
                                                                           
                                                              
    frame_count = result.get("frame_count", 0)
    expected_frames = [FRAME_PATTERN % i for i in range(frame_count)]
    all_present, missing = verify_frame_sequence(result["frame_folder"], expected_frames)
    if not all_present:
        shown = ", ".join(missing[:20])
        if len(missing) > 20:
            shown = "{0}, ... (+{1} more)".format(shown, len(missing) - 20)
        result["status"] = "FAILED (missing frames: {0})".format(shown)
        print("  [warn] not encoding '{0}': {1} of {2} frame(s) missing or too small -- "
              "keeping frames at {3}; missing: {4}".format(
                  result["target"], len(missing), frame_count, result["frame_folder"], shown))
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
        print("  Video encoded: {0}".format(os.path.abspath(video_path)))
        result["status"] = "encoded"
        result["output_path"] = video_path
    except Exception as e:
        result["status"] = "FAILED (encode: {0})".format(e)
        print("  [warn] video encoding failed for '{0}': {1} -- "
              "frames are still on disk at {2}".format(
                  result["target"], e, result["frame_folder"]))
    return result


                                                                            
     
                                                                            

def run_cutaway(opts):
    print("lux.isHeadless() = {0}".format(lux.isHeadless()))

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

    print("Resolving clipping-plane control (experimental -- see script header)...")
    clip_handle, clip_api = resolve_clipping_plane()

    print("Resolving sweep range from bounding box (experimental -- see script header)...")
    start_offset, end_offset = resolve_sweep_range(
        target_node, axis,
        opts.get("clip_margin_mult", 1.15),
        opts.get("clip_start_override"),
        opts.get("clip_end_override"),
    )
    print("  Sweep axis={0} start={1:.3f} end={2:.3f}".format(axis, start_offset, end_offset))

    camera_list = resolve_camera_list(opts.get("camera_selection"))
    targets = [None] if camera_list is None else camera_list
    if not targets:
        print("[error] no cameras/studios resolved from camera_selection -- nothing to render.")
        return []
    print("Shooting {0} target(s): {1}".format(len(targets), ', '.join(t or 'current' for t in targets)))

    render_opts = None
    try:
        render_opts = lux.getRenderOptions()
        if opts.get("preview_mode", True):
            try:
                render_opts.setMaxTimeRendering(2)
            except Exception as e:
                print("[warn] couldn't set preview render mode: {0}".format(e))
        if opts.get("add_to_queue"):
            try:
                render_opts.setAddToQueue(True)
            except Exception as e:
                print("[warn] couldn't enable queueing: {0}".format(e))
    except Exception as e:
        print("[warn] couldn't get render options, using KeyShot defaults: {0}".format(e))

    queueing = bool(opts.get("add_to_queue"))
    if queueing:
        print("Queueing enabled -- frames go to KeyShot's render queue instead of rendering immediately.")

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
            print("Processing render queue ({0} shot(s) pending)...".format(len(pending)))
            queue_ok = True
            try:
                lux.processQueue()
            except Exception as e:
                queue_ok = False
                print("[warn] couldn't process render queue: {0} -- skipping video encoding; "
                      "frames may still be sitting in KeyShot's queue".format(e))
            if queue_ok:
                for result in pending:
                    log(encode_one_cutaway(result, opts, output_folder))
        else:
            print("[info] {0} shot(s) queued but not rendered yet. Process the queue in "
                  "KeyShot (Render Queue window), then encode each frame folder into video manually -- "
                  "or re-run with 'process queue after' enabled.".format(len(pending)))

    print("Manifest written to {0}".format(manifest_path))
    return [o.get("video_name") for o in outcomes]


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled -- nothing rendered.")
    else:
        run_cutaway(options)
