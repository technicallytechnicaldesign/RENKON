                       
                                   
          
                    
                                                                    
                                                                            
                                                                             
                                                                    
                                                                       
                                                                     
                                                                    
 
                                                        
                                                                               
                                                                               
                                                                             
                                                               
 
                                                                         
                                                                        
                                                                             
                                                                             
                                                                              
                                                                            
                                                                                
           
                                                

   
                                     
                                      

                                                                   
                                                              
                                                                       
                                                                          
                     

                                                                           
                                                                

                                                                          
                                
                                                                          
                                                           
                                                                       

                                                                         
                                                                        
                                                     
                                     

                                                 
                                                                             
                                                                                
                                                                               
                                                                     

                                                                        
                                                                        
                                                             
   

import lux
import random
import math

                                                                      
                                                                                 
                                                                             
                                                                              
                                                                           
                                                                           
                                                                                  
PT_COLOR = getattr(lux, "PARAMETER_TYPE_COLOR", None)
PT_SHADERBUMP = getattr(lux, "PARAMETER_TYPE_SHADERBUMP", None)

                                                                            
                     
                                                                            

DEBUG = True                                                        

                                                                            
                       
                                                                            

                                                                           
                                                                    
                                                                             
                                                                            
                                                                              
                                                                             
                                                                              
MATERIALS = [
                                                                                       
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
]
MATERIAL_TYPE_ORDER = [m[0] for m in MATERIALS]
MATERIAL_BY_NAME = {m[0]: m for m in MATERIALS}
TYPE_ABBR = {m[0]: m[4] for m in MATERIALS}

WEAR_PRESETS = {"Pristine": 0.3, "Light Wear": 1.0, "Moderate Wear": 2.5, "Heavy Wear": 5.0}
WEAR_ORDER = list(WEAR_PRESETS.keys())
WEAR_ABBR = {"Pristine": "PRI", "Light Wear": "LGT", "Moderate Wear": "MOD", "Heavy Wear": "HVY"}

                                                                            
                                                                    
BASE = {
    "fine_noise_scale":    0.15,
    "fine_noise_bump":     0.01,
    "fractal_scale":       4.0,
    "scratch_bump_height": 0.02,
    "scratch_density":     0.12,
    "scratch_size":        0.04,
    "scratch_dir_noise":   0.6,
    "scratch_noise":       0.3,
    "scratch_levels":      2,
    "edge_amount":         0.02,
    "spots_bump_height":   0.02,
    "spots_density":       0.08,
    "spots_size":          0.05,
    "cellular_bump_height": 0.015,
    "cellular_scale":      2.0,
}

                                                                           
                                                                           
                                                                           
                                                                           
                                                                          
                                                                         
                                                                     
                                                                            
LOUD_BUMP_FEATURES = ["add_scratches", "add_rounded_edges", "add_spots", "add_cellular"]
MAX_SIMULTANEOUS_LOUD_LAYERS = 2

                                                                              
                                                                           
                                                                            
                                                                        
                                                                   
                                                                
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
FEATURE_PROBS = {                                                  
    "add_fine_noise": 0.85, "add_scratches": 0.55, "add_rounded_edges": 0.35,
    "add_spots": 0.25, "add_cellular": 0.15, "add_fractal_roughness": 0.6,
    "add_occlusion_roughness": 0.25, "add_color_gradient": 0.12,
}

                                                                              
                                                                              
                              
MASK_KEYS = ["mask_scratches_to_edges", "mask_spots_to_cavities"]

DEFAULT_OPTIONS = {
    "name_prefix": "MAT",
    "material_type": "Aluminum (brushed metal)",
    "wear_level": "Light Wear",
    "wear_multiplier": 1.0,
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
                                                                            
                                                                             
                                                                               
    "random_seed": "auto",
    "name_filter": "",
}


def clamp01(v):
    return max(0.0, min(1.0, v))


                                                                          
                                                                         
                                                                      
                                                                           
_name_rng = random.Random()


def random_suffix(n=6):
    return "".join(_name_rng.choice("0123456789ABCDEF") for _ in range(n))


def resolve_filter(value, sentinel="ALL"):
                                                                          
                                           
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


def resolve_material_name(prefix, material_type, wear_level):
    base = (prefix or "MAT").strip().upper().replace(" ", "_") or "MAT"
    type_code = TYPE_ABBR.get(material_type, "GEN")
    wear_code = WEAR_ABBR.get(wear_level, "GEN")
    return "{0}-{1}-{2}-{3}".format(base, type_code, wear_code, random_suffix())


def randomize_feature_flags():
                                                                          
                                                                       
                                                                       
                                                          
    flags = {k: False for k in FEATURE_KEYS}
    flags["add_fine_noise"] = random.random() < FEATURE_PROBS["add_fine_noise"]

    loud_candidates = [k for k in LOUD_BUMP_FEATURES if random.random() < FEATURE_PROBS[k]]
    random.shuffle(loud_candidates)
    for k in loud_candidates[:MAX_SIMULTANEOUS_LOUD_LAYERS]:
        flags[k] = True

    flags["add_fractal_roughness"] = random.random() < FEATURE_PROBS["add_fractal_roughness"]
    flags["add_occlusion_roughness"] = random.random() < FEATURE_PROBS["add_occlusion_roughness"]
    flags["add_color_gradient"] = random.random() < FEATURE_PROBS["add_color_gradient"]

                                                       
    if flags["add_fractal_roughness"] and flags["add_occlusion_roughness"]:
        if random.random() < 0.5:
            flags["add_occlusion_roughness"] = False
        else:
            flags["add_fractal_roughness"] = False
    return flags


def _apply_seed(opts):
                                                                              
                                                                              
                                                                              
                                                                              
                           
    raw = str(opts.get("random_seed", "") or "").strip()
    if not raw or raw.lower() in ("auto", "random", "none"):
        return None
    try:
        seed = int(raw)
    except ValueError:
        seed = raw
    random.seed(seed)
    return seed


                                                                            
                                                            
                                                                            

def get_options():
    if lux.isHeadless():
        print("Headless session detected -- skipping dialog, using DEFAULT_OPTIONS.")
        return dict(DEFAULT_OPTIONS)

    values = [
        ("name_prefix", lux.DIALOG_TEXT, "Name prefix (blank = 'MAT'):", DEFAULT_OPTIONS["name_prefix"]),
                                                                              
                                                                              
                                                                            
                                                                         
        ("material_type", lux.DIALOG_ITEM, "Material type:",
         MATERIAL_TYPE_ORDER.index(DEFAULT_OPTIONS["material_type"]), MATERIAL_TYPE_ORDER),
        ("wear_level", lux.DIALOG_ITEM, "Wear level:",
         WEAR_ORDER.index(DEFAULT_OPTIONS["wear_level"]), WEAR_ORDER),
        ("wear_multiplier", lux.DIALOG_DOUBLE, "Wear fine-tune (x):",
         DEFAULT_OPTIONS["wear_multiplier"], (0.0, 3.0)),
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
    values.append((lux.DIALOG_LABEL, "-- roughness / color drivers (pick one of each pair) --"))
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
        title="Procedural Material Generator",
        desc="Tick the layers you want, pick a base + wear level, and click OK.",
        values=values,
        id="procedural_material_generator_dialog",
    )

    if opts is None:
        print("Dialog cancelled.")
        return None

    def norm_item(v, valid):
                                                                        
                                                                         
                                                                     
                                                                          
                                                                            
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
    return opts


                                                                            
                                        
                                                                            

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
                                                                       
    shader_type = getattr(lux, attr_name, None)
    if shader_type is None:
        print("  [warn] lux.{0} not available in this KeyShot version -- skipping {1}".format(attr_name, label))
        return None
    try:
        return new_node(graph, shader_type, label)
    except Exception as e:
        print("  [warn] couldn't create {0} ({1}): {2} -- skipping".format(label, attr_name, e))
        return None


def resolve_shader(shader_attr):
                                                                                
                                                                             
                                                                              
    for attr in (shader_attr, "SHADER_TYPE_PLASTIC", "SHADER_TYPE_METAL"):
        st = getattr(lux, attr, None)
        if st is not None:
            if attr != shader_attr:
                print("  [warn] {0} unavailable on this build -- using {1} instead".format(shader_attr, attr))
            return st
    return None


def find_param(node, keywords, ptype=None):
    if isinstance(keywords, str):
        keywords = [keywords]
    for kw in keywords:
        kw = kw.lower()
        for p in node.getParameters():
            if kw in p.getDisplayName().lower():
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


                                                                            
                                                                        
                                                                        
                                                                         
                                                                      
                                                                            

def add_curvature_mask(graph):
                                                                              
                                                                            
                                                                
    n = try_new_node(graph, "SHADER_TYPE_CURVATURE", "Curvature (edge mask)")
    if n is None:
        return None
    set_display(n, ["positive curvature"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
    set_display(n, ["zero curvature"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
    set_display(n, ["negative curvature"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
    return n


def add_occlusion_mask(graph):
                                                                             
                                                                            
                                                                               
                                                          
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (cavity mask)")
    if n is None:
        return None
    set_display(n, ["occluded"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
    set_display(n, ["unoccluded", "bright", "far", "exposed"], (0.0, 0.0, 0.0),
                ptype=PT_COLOR)
    return n


def mask_bump_layer(graph, effect_node, mask_node, label):
                                                                                
                                                                             
                                                                                 
                                                                         
                                                                             

                                                                          
                                                                             
                                                                             
                                                                           
              
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
            graph.removeNode(mask_node)                                                   
        except Exception:
            pass
    return effect_node


                                                                            
                                                                              
                                                                            

def add_fine_noise_bump(graph):
    n = try_new_node(graph, "SHADER_TYPE_NOISE_TEXTURE", "Fine Noise")
    if n:
        set_display(n, ["scale"], BASE["fine_noise_scale"])
                                                                                  
                                                   
        set_display(n, ["bump height"], BASE["fine_noise_bump"])
    return n


def add_scratches_bump(graph, wear_mult, base_roughness, damping=1.0):
    n = try_new_node(graph, "SHADER_TYPE_SCRATCHES", "Scratches")
    if n:
                                                                               
                                                                                 
        set_display(n, ["bump height"], -clamp01(BASE["scratch_bump_height"] * wear_mult * damping))
        set_display(n, ["density"], clamp01(BASE["scratch_density"] * wear_mult))
        set_display(n, ["size"], clamp01(BASE["scratch_size"] * wear_mult))
        set_display(n, ["directional noise"], BASE["scratch_dir_noise"])
        set_display(n, ["noise"], BASE["scratch_noise"])
        set_display(n, ["levels"], BASE["scratch_levels"])
                                                                              
                                                                           
                                                                                
                                                                              
                                                                              
                                                 
        set_display(n, ["color"], (0.75, 0.75, 0.75), ptype=PT_COLOR)
        bg = clamp01(base_roughness)
        set_display(n, ["background"], (bg, bg, bg), ptype=PT_COLOR)
    return n


def add_rounded_edges_bump(graph, wear_mult, damping=1.0):
    n = try_new_node(graph, "SHADER_TYPE_ROUNDED_EDGES", "Rounded Edges")
    if n:
        set_display(n, ["radius", "bump height", "amount"],
                    clamp01(BASE["edge_amount"] * wear_mult * damping))
    return n


def add_spots_bump(graph, wear_mult, damping=1.0):
    n = try_new_node(graph, "SHADER_TYPE_SPOTS", "Spots / Pitting")
    if n:
        set_display(n, ["bump height", "height"], clamp01(BASE["spots_bump_height"] * wear_mult * damping))
        set_display(n, ["density"], clamp01(BASE["spots_density"] * wear_mult))
                                                                           
                        
        set_display(n, ["radius", "size", "scale"], clamp01(BASE["spots_size"] * wear_mult))
    return n


def add_cellular_bump(graph, wear_mult, damping=1.0):
                                                                          
                                                                          
    n = try_new_node(graph, "SHADER_TYPE_CELLULAR", "Cellular (experimental)")
    if n:
        set_display(n, ["scale"], BASE["cellular_scale"])
        set_display(n, ["bump height", "height"],
                    clamp01(BASE["cellular_bump_height"] * wear_mult * damping * 0.6))
    return n


def add_fractal_roughness(graph, base_node):
    n = try_new_node(graph, "SHADER_TYPE_NOISE_FRACTAL", "Fractal Noise (roughness driver)")
    if n is None:
        return False
    set_display(n, ["scale"], BASE["fractal_scale"])
    return wire_scalar_driver(graph, n, base_node, ["roughness"], "roughness")


def add_occlusion_roughness(graph, base_node):
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (roughness/grime driver)")
    if n is None:
        return False
    return wire_scalar_driver(graph, n, base_node, ["roughness"], "roughness")


def add_color_gradient(graph, base_node, base_color):
    n = try_new_node(graph, "SHADER_TYPE_COLOR_GRADIENT", "Color Gradient (experimental)")
    if n is None:
        return False
                                                                          
                                                                              
                                                                        
                                                                             
                                                                          
                   
    light = tuple(clamp01(c * 1.25 + 0.05) for c in base_color)
    dark = tuple(clamp01(c * 0.6) for c in base_color)
    ok1 = set_display(n, ["color 1", "start color", "color a"], light, ptype=PT_COLOR)
    ok2 = set_display(n, ["color 2", "end color", "color b"], dark, ptype=PT_COLOR)
    if not (ok1 or ok2):
                                                                          
                                                                            
                                                                       
                                                                            
                                                                            
        print("  [warn] Color Gradient stops aren't script-settable on this build -- "
              "removing it so it can't drive a garbage (magenta) colour or clutter the graph")
        try:
            graph.removeNode(n)
        except Exception:
            pass
        return False
    return wire_scalar_driver(graph, n, base_node,
                              ["color", "diffuse", "tint", "reflectance"], "color")


                                                                            
       
                                                                            

def build_material(opts):
    material_type = opts.get("material_type", DEFAULT_OPTIONS["material_type"])
    wear_level = opts.get("wear_level", DEFAULT_OPTIONS["wear_level"])
    wear_mult = WEAR_PRESETS.get(wear_level, 1.0) * float(opts.get("wear_multiplier", 1.0))

    seed = _apply_seed(opts)
    if seed is not None:
        print("  Seeded feature RNG with {0} (reproducible in randomize mode)".format(repr(seed)))

    features = {k: bool(opts.get(k, False)) for k in FEATURE_KEYS}
    if opts.get("randomize_features"):
        features = randomize_feature_flags()

    mask_scratches = bool(opts.get("mask_scratches_to_edges"))
    mask_spots = bool(opts.get("mask_spots_to_cavities"))

    mat = MATERIAL_BY_NAME.get(material_type, MATERIAL_BY_NAME[DEFAULT_OPTIONS["material_type"]])
    _, shader_attr, base_color, base_roughness, _ = mat
    shader_type = resolve_shader(shader_attr)
    if shader_type is None:
        raise RuntimeError("No usable base shader for '{0}'".format(material_type))

    name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level)

    print("lux.isHeadless() = {0}".format(lux.isHeadless()))
    print("Building '{0}' | type={1} | wear={2} (x{3:.2f})".format(name, material_type, wear_level, wear_mult))
    active = [FEATURE_LABELS[k] for k, v in features.items() if v]
    active_str = ", ".join(active) if active else "(none)"
    print("Features: {0}".format(active_str))
    masks_on = [m for m, on in [("scratches->edges", mask_scratches),
                                ("spots->cavities", mask_spots)] if on]
    if masks_on:
        print("Masking: {0}".format(", ".join(masks_on)))

                                                                       
                                                                       
                                                                      
                                     
    active_loud_count = sum(1 for k in LOUD_BUMP_FEATURES if features.get(k))
    damping = 1.0 / math.sqrt(max(1, active_loud_count))
    if active_loud_count > 1:
        print("  {0} loud bump layers active -- damping each by {1:.2f}x".format(active_loud_count, damping))

    for attempt in range(5):
        try:
            lux.createSceneMaterial(name)
            break
        except Exception as e:
            print("  [warn] couldn't create material '{0}': {1} -- trying a new random name".format(name, e))
            name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level)
    else:
        raise RuntimeError("Couldn't create a scene material after 5 attempts")

    graph = lux.getMaterialGraph(name)
    root = graph.getRoot()
    if DEBUG:
        dump_node(root, "Root")

    base_node = new_node(graph, shader_type, material_type)
    safe_edge(graph, source=base_node, target=root, param="surface", label="base -> root.surface")
                                                                         
                                                                               
                                                                         
                                                    
                                                                             
                                                                                
                                                                           
                                        
    set_display(base_node, ["color", "diffuse", "tint", "reflectance", "base color"],
                base_color)
    set_display(base_node, ["roughness"], base_roughness)

                                                                            
                                                                         
                                                                                
    bump_sources = []
    scratches_node = None                                                          
    if features["add_fine_noise"]:
        bump_sources.append(add_fine_noise_bump(graph))
    if features["add_scratches"]:
        scratches_node = add_scratches_bump(graph, wear_mult, base_roughness, damping)
        if mask_scratches:
            mask_bump_layer(graph, scratches_node, add_curvature_mask(graph), "scratches->edges")
        bump_sources.append(scratches_node)
    if features["add_rounded_edges"]:
        bump_sources.append(add_rounded_edges_bump(graph, wear_mult, damping))
    if features["add_spots"]:
        sp = add_spots_bump(graph, wear_mult, damping)
        if mask_spots:
            sp = mask_bump_layer(graph, sp, add_occlusion_mask(graph), "spots->cavities")
        bump_sources.append(sp)
    if features["add_cellular"]:
        bump_sources.append(add_cellular_bump(graph, wear_mult, damping))

    combined_bump = combine_bump_sources(graph, bump_sources)
    if combined_bump is not None:
        base_bump_slots = connection_param_names(base_node, PT_SHADERBUMP)
        if base_bump_slots:
            safe_edge(graph, source=combined_bump, target=base_node, param=base_bump_slots[0],
                      label="combined bump -> base.bump")
        else:
            print("  [warn] base material has no bump input")

                                                                             
                                                                              
                                                                              
                                                                               
    if scratches_node is not None:
        wire_scalar_driver(graph, scratches_node, base_node, ["roughness"],
                           "roughness (scratches)")
    elif features["add_fractal_roughness"]:
        add_fractal_roughness(graph, base_node)
    elif features["add_occlusion_roughness"]:
        add_occlusion_roughness(graph, base_node)

                                                                              
    if features["add_color_gradient"]:
        add_color_gradient(graph, base_node, base_color)

    print("Built material graph: {0}".format(name))
    return graph, name


def apply_material_to_parts(name, name_filter=None):
                                                                         
                                                                             
                                                                             
                                                                         
                                                                           
               
    root = lux.getSceneTree()
    candidates = root.find(name=name_filter) if name_filter else root.find("")
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
        print("  [info] nothing matched -- run with DEBUG=True and check the node "
              "kinds above, or confirm the scene actually has geometry loaded")
    return applied


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled -- nothing built.")
    else:
        graph, material_name = build_material(options)
        apply_material_to_parts(material_name, name_filter=resolve_filter(options.get("name_filter")))
