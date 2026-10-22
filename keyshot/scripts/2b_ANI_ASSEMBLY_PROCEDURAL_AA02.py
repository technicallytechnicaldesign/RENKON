            
          
                    
   
                                           
                                                
                                                                          
                                                                
                                   

                                                                        
                                                                             
                                                                      
                                           

                                                                           
                                                   
                                                                 
                                                                           
                                                                         
                                                                        
                                                                        
                                                                        
                                                                        
                                                                      
                                                       
                                                                     
                                                                          
                                     

                                                                    
                                                                        
                                                                       
                                                            

                                                                     
                                                                   
                                                                          
                                                                           
                                                                          
                                                                         
                       

                                                                        
                                                                 

                                                                       
                                                                        
                                                                          
                                                        
                                                                    
                                                                 
                                                                       
                                                                    
                                                                      
                     

                                                                           
                                                                
   

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
                          
    "scatter_radius_mult": 3.0,
    "scatter_rotation_enabled": True,
    "scatter_rotation_max_degrees": 90.0,
                           
    "staggered_order": "Scene Order",
    "staggered_overlap_frac": 0.25,
    "staggered_arrival_axis": "Z",
    "staggered_arrival_distance_mult": 4.0,
                           
    "spiral_turns": 1.5,
    "spiral_amplitude_mult": 1.0,
                      
    "ghost_fade_start_opacity": 0.0,
    "ghost_fade_end_opacity": 1.0,
                                         
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
    "video_name_prefix": "ASSEMBLY",
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


def load_scene_template(path):
                                                                     
                                            
    if not path:
        return True
    try:
        lux.openFile(path, dontAsk=True)
        print('Loaded scene template: {0}'.format(path))
        return True
    except Exception as e:
        print("[warn] couldn't load scene template '{0}': {1} -- continuing with whatever scene is currently open".format(path, e))
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
            print("[warn] model set '{0}' not found in the loaded scene (found: {1}) -- importing without a specific model set target.".format(model_set_name, existing))
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
            print("  [warn] couldn't find model set '{0}': {1}".format(model_set_name, e))
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
        print('  Ground rendering set to {0} (via {1} / {2})'.format(enabled, used_shadow or '-', used_reflect or '-'))
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
                                                                   
                                                                  
        get_studio = getattr(lux, "getStudio", None)
        if get_studio is not None:
            for s in studios:
                try:
                    c = get_studio(s).getCamera()
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
                lux.setCamera(cam)
            return cam or name
        except Exception as e:
            print("  [warn] couldn't activate studio '{0}': {1}".format(name, e))
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
def vlen(a): return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


def vnorm(a):
    l = vlen(a)
    return (0.0, 0.0, 1.0) if l < 1e-9 else (a[0] / l, a[1] / l, a[2] / l)


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def resolve_filter(value, sentinel="ALL"):
                                                                          
                                           
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


                                                                            
                                  
                                                                            

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
            return lo, hi, name
    return None, None, None


_extent_fallback_warned = False


def resolve_part_extent(node, fallback_mult):
                                                                      
                                                                     
                                                                          
                                                                   
                                                                     
    global _extent_fallback_warned
    lo, hi, api_name = resolve_bounding_box(node)
    if lo is not None and hi is not None:
        extent = vlen(vsub(hi, lo)) / 2.0
        if extent > 1e-6:
            return extent

    if not _extent_fallback_warned:
        print("  [warn] no bounding-box getter resolved on this KeyShot version (tried "
              "getBoundingBox/getWorldBoundingBox/getBounds) -- falling back to each part's "
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
    return 10.0                                                                     


                                                                            
                                                                           
                                                                            

def build_delta_matrix(translation_delta, rotation_deg_delta, axis_vec):
                                                                       
                                                                    
                                                                         
                                                                         
                                                                      
                                                                         
                                                                        
                                                    
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
        print("  [warn] applyTransform failed for '{0}' ({1}) -- disabling further motion for this part".format(state.get('name', '?'), e))
        return

    if vlen(translation_delta) > 1e-9 and not translate_ok and state.get("translate_available", True):
        state["translate_available"] = False
        print("  [warn] luxmath.Matrix().translate() not available on this KeyShot version -- '{0}' will not translate (rotation, if any, still applies)".format(state.get('name', '?')))
    if abs(rotation_deg_delta) > 1e-9 and not rotate_ok and state.get("rotate_available", True):
        state["rotate_available"] = False
        print("  [warn] luxmath.Matrix().rotate() not available on this KeyShot version -- '{0}' will not rotate (translation, if any, still applies)".format(state.get('name', '?')))

    state["applied_translation"] = vadd(state.get("applied_translation", (0.0, 0.0, 0.0)),
                                         translation_delta if translate_ok else (0.0, 0.0, 0.0))
    state["applied_rotation_deg"] = state.get("applied_rotation_deg", 0.0) + (
        rotation_deg_delta if rotate_ok else 0.0)


def apply_final_correction(node, state):
                                                                          
                                                                         
                                                                      
                                                                         
                                                                            
                                                                          
                                                                         
                                                             
    residual_translation = vscale(state.get("applied_translation", (0.0, 0.0, 0.0)), -1.0)
    residual_rotation = -state.get("applied_rotation_deg", 0.0)
    if vlen(residual_translation) < 1e-9 and abs(residual_rotation) < 1e-9:
        return
    apply_part_delta(node, residual_translation, residual_rotation,
                      state.get("rotation_axis", (0.0, 1.0, 0.0)), state)


                                                                            
                                                                        
                                                                            

NODE_OPACITY_SETTERS = ["setOpacity", "setTransparency", "setAlpha"]
MATERIAL_OBJECT_ACCESSORS = ["getMaterialNode", "getAppearance", "getMaterialObject", "getMaterialGraph"]
MATERIAL_OPACITY_SETTERS = ["setOpacity", "setTransparency", "setAlpha"]

_opacity_warned = False


def resolve_opacity_control(node):
                                                                            
                                                                    
                                                                        
                                                                    
                                                                     
                                                                     
    for name in NODE_OPACITY_SETTERS:
        fn = getattr(node, name, None)
        if fn is None:
            continue
        try:
            fn(1.0)                                                                            
            return fn, 'node.{0}'.format(name)
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
            continue                                                                                  
        for setter in MATERIAL_OPACITY_SETTERS:
            fn = getattr(material_obj, setter, None)
            if fn is None:
                continue
            try:
                fn(1.0)
                return fn, '{0}().{1}'.format(accessor, setter)
            except Exception:
                continue

    return None, None


def warn_opacity_once():
    global _opacity_warned
    if not _opacity_warned:
        print('  [warn] no working opacity/transparency API resolved on this KeyShot version -- tried node-level setOpacity/setTransparency/setAlpha and material-object accessors {0} with the same setters. Falling back to a hard cut: parts will be visible for the whole shot instead of fading in. Run help(node) / help(node.getMaterialNode()) (or whichever accessor exists) in the Scripting Console to find the real API and add it to the candidate lists at the top of this file.'.format(MATERIAL_OBJECT_ACCESSORS))
        _opacity_warned = True


                                                                            
                                                                     
                                                                            

def ease_smooth(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def build_convergence_profile(num_frames, hold_start, hold_end):
                                                                        
                                                                            
                                                                           
                                                                          
                                     
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


                                                                            
                                        
                                                                            

def get_parts(target_node, name_filter=None, order="Scene Order"):
                                                                          
                                                                          
                                                                         
                                                               
                                                                     
                                                                       
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
                                                                         
                                                                       
                                       
    z = random.uniform(-1.0, 1.0)
    theta = random.uniform(0.0, 2.0 * math.pi)
    r = math.sqrt(max(0.0, 1.0 - z * z))
    return (r * math.cos(theta), r * math.sin(theta), z)


def perpendicular_basis(direction):
                                                                       
                                                                        
                                                                     
                                                                  
                                                                
    ref = (0.0, 0.0, 1.0)
    if abs(direction[2]) > 0.9:
        ref = (0.0, 1.0, 0.0)
    perp1 = vnorm(vcross(direction, ref))
    perp2 = vnorm(vcross(direction, perp1))
    return perp1, perp2


def build_part_states(parts, opts, mode):
                                                                          
                                                                          
                                                               
                       
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
                print("  Opacity control for '{0}' resolved via {1}".format(name, api_name))

        states.append(state)

    return states


def compute_spiral_offset(t, state):
                                                                       
                                                      
                                                                         
                                                                        
                
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
    return base                                                    


def compute_rotation_at(t, state, mode):
    if mode != "scatter_settle":
        return 0.0
    return state.get("rotation_total_deg", 0.0) * (1.0 - t)


                                                                            
                                                                
                                                                            

def shoot_one_assembly(opts, target, render_opts, output_folder, queueing, part_states, mode, profile,
                        staggered_windows):
    label = target if target else "current"
    safe_name = sanitize_name(label)
    video_name = '{0}_{1}.mp4'.format(opts.get('video_name_prefix') or 'ASSEMBLY', safe_name)
    frame_folder = os.path.join(output_folder, '{0}_assembly_frames'.format(safe_name))

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
            result["status"] = 'FAILED (frame folder: {0})'.format(e)
            return result

                                                                          
                                                                      
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
                    print("  [warn] opacity call stopped working mid-shot for '{0}' ({1}) -- leaving it at its last opacity".format(state['name'], e))

            state["prev_t"] = t_part

                                                                         
        if env is not None and env_rotate_available and opts.get("rotate_environment") and start_rotation is not None:
            try:
                sweep = opts["environment_rotation_degrees"] * (f / max(1, opts["num_frames"] - 1))
                                                                              
                                                                                
                                        
                env.setRotation((start_rotation + sweep) % 360.0)
            except Exception as e:
                env_rotate_available = False
                print('  [warn] environment rotation not available in this KeyShot version ({0}) -- continuing without it'.format(e))

                                                                 
        if env is not None and opts.get("brightness_ramp") and start_brightness is not None:
            try:
                start_mult = opts.get("brightness_ramp_start_mult", 0.6)
                low = start_brightness * start_mult
                env.setBrightness(low + (start_brightness - low) * t_global)
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

        if f % 10 == 0 or f == opts["num_frames"] - 1:
            print('    frame {0}/{1} (t={2:.2f})'.format(f + 1, opts['num_frames'], t_global))

                                                                              
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

                                                                             
    if env is not None:
        if start_rotation is not None:
            try:
                env.setRotation(start_rotation % 360.0)
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


def encode_one_assembly(result, opts, output_folder):
                                                                     
                                                                         
                                                                
                                                                           
    if not result.get("ok"):
        return result
    video_path = os.path.join(output_folder, result["video_name"])

                                                                              
                                                                                
                                                          
    expected = [FRAME_PATTERN % f for f in range(result.get("frame_count", 0))]
    frames_ok, missing = verify_frame_sequence(result["frame_folder"], expected)
    if not frames_ok:
        result["status"] = "FAILED (missing frames: {0})".format(", ".join(missing))
        print("  [warn] not encoding '{0}' -- {1} of {2} expected frame(s) missing or "
              "truncated: {3} -- frames kept at {4}".format(
                  result["target"], len(missing), result.get("frame_count", 0),
                  ", ".join(missing), result["frame_folder"]))
        return result

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
        print('  Video encoded: {0}'.format(os.path.abspath(video_path)))
        result["status"] = "encoded"
        result["output_path"] = video_path
    except Exception as e:
        result["status"] = 'FAILED (encode: {0})'.format(e)
        print("  [warn] video encoding failed for '{0}': {1} -- frames are still on disk at {2}".format(result['target'], e, result['frame_folder']))
    return result


                                                                            
                                                            
                                                                            

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
         "Model set to gather parts from (blank = whole scene):", ""),
        ("part_name_filter", lux.DIALOG_TEXT, "Part name filter (ALL = every part found):",
         DEFAULT_OPTIONS["part_name_filter"]),
        ("camera_selection", lux.DIALOG_TEXT,
         "Camera(s)/Studio(s) to shoot -- blank = current viewport camera, 'ALL' = every one found, "
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
        title="Assembly Reveal -- Procedural Modes",
        desc="Parts converge into (or fade into) their authored final positions while the camera "
             "holds static. Per-node relative-transform composition and opacity control are "
             "EXPERIMENTAL on this KeyShot build -- see the script header for what's confirmed vs. "
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


                                                                            
     
                                                                            

def run_assembly(opts):
    print('lux.isHeadless() = {0}'.format(lux.isHeadless()))

    mode = opts.get("mode") or "scatter_settle"
    if mode not in MODE_OPTIONS:
        print("[warn] unrecognized mode '{0}' -- falling back to 'scatter_settle'".format(mode))
        mode = "scatter_settle"

    seed = opts.get("random_seed", 0)
    if seed:
        random.seed(seed)
        print('Random seed set to {0} -- scatter/spiral offsets are reproducible across runs'.format(seed))

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
        print("[error] no object parts resolved under the target -- nothing to animate.")
        return []
    print('Mode: {0} -- {1} part(s) found'.format(mode, len(parts)))

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
        print("[error] no cameras/studios resolved from camera_selection -- nothing to render.")
        return []
    print('Shooting {0} target(s): {1}'.format(len(targets), ', '.join(t or 'current' for t in targets)))

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
        result = shoot_one_assembly(opts, target, render_opts, output_folder, queueing, part_states,
                                     mode, profile, staggered_windows)
        outcomes.append(result)
        log(result)
        if queueing and result.get("ok"):
            pending.append(result)

    if queueing and pending:
        if opts.get("process_queue_after"):
            print('Processing render queue ({0} shot(s) pending)...'.format(len(pending)))
            queue_ok = True
            try:
                lux.processQueue()
            except Exception as e:
                queue_ok = False
                print("[warn] couldn't process render queue: {0} -- skipping video encoding; frames may still be sitting in KeyShot's queue".format(e))
            if queue_ok:
                for result in pending:
                    log(encode_one_assembly(result, opts, output_folder))
        else:
            print("[info] {0} shot(s) queued but not rendered yet. Process the queue in KeyShot (Render Queue window), then encode each frame folder into video manually -- or re-run with 'process queue after' enabled.".format(len(pending)))

    print('Manifest written to {0}'.format(manifest_path))
    return [o.get("video_name") for o in outcomes]


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled -- nothing rendered.")
    else:
        run_assembly(options)
