                       
                                   
          
 
                                                                    
                                       
 
                                                             
                                                                          
                                                       

import lux
import random


                                                                                
                                                                                
                                                                                
                                                                          
                                                                                
                                             
 
                                                                            
                                                                            
                                                                    
                                                                            
                                         
 
                                                                        
                                                                        
                                                                                

                                                                      
                                                                                 
                                                                             
                                                                              
                                                                           
                                                                           
                                                                                  
PT_COLOR = getattr(lux, "PARAMETER_TYPE_COLOR", None)


PT_SHADERBUMP = getattr(lux, "PARAMETER_TYPE_SHADERBUMP", None)


DEBUG = True                                                        


                                                                            
                                         
                                                                            
                                                                             
                                                                                 
                                                                                  
                                                                                    
                                                                                 
                                                                                  
                                                                
                                                                                
                                                         
PTYPE_STRING = 9


                                                                                 
                                                                                 
                                                                                 
                                     
IMAGE_MAP_CANDIDATES = [
    "SHADER_TYPE_TEXTURE_MAP", "SHADER_TYPE_IMAGE_MAP", "SHADER_TYPE_IMAGE",
    "SHADER_TYPE_BITMAP", "SHADER_TYPE_TEXTURE",
]


                                                                                  
                                                                               
                                                                         
COLOR_NODE_CANDIDATES = [
    "SHADER_TYPE_COLOR", "SHADER_TYPE_SOLID_COLOR", "SHADER_TYPE_COLOR_MAP",
    "SHADER_TYPE_COLORMAP", "SHADER_TYPE_CONSTANT_COLOR",
]


                                                                                 
                                                                                 
                                                                                
                                                         
                                                                         
                                                                
                                                                        
                                                  
                                                                                 
                                                                                     
                                                                 
                                                                             
                                                                                
                                                                                
                                       
LEGACY_SCALE_BASE = {
    "fine_noise": 0.15,
    "scratches":  5.0,
    "fractal":    4.0,
    "cellular":   2.0,
}


                                                                                
                                                                 
 
                                                                         
                                                                              
                                                                      
                                                                               
                                                                             
                                                                               
                                                                                
                                                  
SCALE_FRACTIONS = {
    "scratch_scale": 0.004,
    "fine_noise":    0.02,
    "fractal":       0.15,
    "cellular":      0.08,
    "spots_scale":   0.004,
}


                                                                                 
                                                                                 
                                                                                 
                                      
NO_LABEL = "none"


def normalise_label_path(value):
                                                                                 
                                                                              
                      
    if value is None:
        return ""
    text = str(value).strip()
                                                                                
                                                                                 
                                                                                  
                                                     
    while len(text) >= 2 and text[0] == text[-1] and text[0] in ("\"", "'"):
        text = text[1:-1].strip()
    if text.lower() in (NO_LABEL, "-", ""):
        return ""
    return text


                                                                     
                                                                   
                                                            
                                                                  
                                                    
TEXTURE_DISPLAY_FACTOR = 1000.0
TEXTURE_DISPLAY_FACTOR_LIVE = [TEXTURE_DISPLAY_FACTOR]

                                                                                 
                                                              
TEXTURE_SCALE_FACTOR = 1.0 / TEXTURE_DISPLAY_FACTOR

                                                                                 
                                                                                 
                                                                                
                                                                              
                                                                            
                                                                                
                                                                             
                                 
TEXTURE_SCALE_MIN = 0.0000001


def resolve_scale_factor(raw, label="scale_factor"):
                                                                              

                                                                             
                                                                                 
                                                                  
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
                                                                          

                                                                              
                                                                              
                                                                       
                                                    
                                                                      
                                                                            
                                                             
    factor = TEXTURE_DISPLAY_FACTOR_LIVE[0] or TEXTURE_DISPLAY_FACTOR
    return float(mm) / factor


def texture_scale_to_mm(value):
                                                               
    factor = TEXTURE_DISPLAY_FACTOR_LIVE[0] or TEXTURE_DISPLAY_FACTOR
    return float(value) * factor


def clamp01(v):
    return max(0.0, min(1.0, v))


def as_float(v, default):
                                                                                
                                                                     
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def clampf(v, lo, hi):
                                                                                 
                                              
    return max(lo, min(hi, v))


                                                                          
                                                                         
                                                                      
                                                                           
_name_rng = random.Random()


def random_suffix(n=6):
    return "".join(_name_rng.choice("0123456789ABCDEF") for _ in range(n))


def resolve_filter(value, sentinel="ALL"):
                                                                          
                                           
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


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


def derive_placement_seed(seed):
                                                                                
                                                                                
                                                                               
                                                                                
                                                                             
                                                                              
                             

                                                                        
                                                                             
                                                                              
                                                  
    if seed is not None:
        return random.Random("placement|" + str(seed)).randint(0, 2147483647)
    return random.Random().randint(0, 2147483647)


                                                                            
                                                                               
                                                                                  
                                                                         
                                                                             
                                                                               
                                         
BBOX_METHODS = ["getBoundingBox", "getWorldBounds", "getBounds"]


                                                                                
                                                                              
                                                                            
                                                                                
                                                                                                 
                                                                                
                                                                             
                                                                                
                                                                      
 
                                                                                 
                                                          
DEFAULT_PART_EXTENT = 1.0


def _vec3(v):
                                                                              
                                                                             
                                                                     
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
                break                                                            
    if best is None:
        print("  [info] part measure: no bounding-box API returned usable bounds "
              "(tried {0}) -- will fall back".format(", ".join(BBOX_METHODS)))
        return None
    print("  [info] part measure: max extent {0} scene units via {1}()".format(
        best, method_used))
    return best


def check_performance_mode():
                                                                  

                                                                               
                                                                              
                                                                                
                                                                          
                                                                              
                                                       

                                                                            
                                                                               
                                                                         
                                                                              
                                                                       
                                                                              
                                                          

                                                                              
                                                                                
                                                                                
                                                                              
                     

                                                                              
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
                                                                                
                                                                                
                                                                                
                                                                                 
                                                                          
                                                                                 
                                                                                
                                                                             
    if isinstance(keywords, str):
        keywords = [keywords]
    try:
        params = node.getParameters()
    except Exception:
        return None
                                                                                
    for kw in keywords:
        kwx = kw.strip().lower()
        for p in params:
            if p.getDisplayName().strip().lower() == kwx:
                if ptype is None or p.getType() == ptype:
                    return p
                                                                               
                                                                               
                                         
    for kw in keywords:
        kwx = kw.lower()
        for p in params:
            if kwx in p.getDisplayName().lower():
                if ptype is None or p.getType() == ptype:
                    return p
                                                                              
                                                                               
                                                                                
                                                                              
                                                                                 
                                                                              
                                                                            
                                                            
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
                                                                                
                                                                            
                                                        
    if got is None:
        return False
    if isinstance(want, bool) or isinstance(got, bool):
        try:
            return bool(got) == bool(want)
        except Exception:
            return False
    if isinstance(want, (tuple, list)):
                                                                              
                                                                               
                                                                                
                                                                               
                                                                                 
                                                                                 
                                                                               
                                                                              
                                                                                 
                                                                       
                                                                           
                                                           
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


                                                                            
                                 
                                                                            
                                                                            
                                                                         
                                                                 
                                                                              
                                                                              
                 


def _build_param_type_names():
                                                                         
                                                                               
                                                                           
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


                                                                               
                                                                                
                                          
 
                                                                            
                                                    
                                                                       
                                                                             
                                                                         
                                              
                                      
 
                                                                              
                                                                          
                        
OBSERVED_PARAM_TYPES = "see the table above -- measured 2026-08-04, do not guess"


def _build_shader_type_names():
                                                                              
                                                                              
                                                                           
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
                                                                 

                                                                               
                                                                             
                                                                          
                                                                            
                                                                               
                                                                              
                                                                             
                                                                             
    try:
        return table.get(key)
    except TypeError:
        return None


                                                                          
                                                                               
                                                                               
                                                                              
                                                                               
TYPE_NAME_KEYS = ("name", "type", "displayName", "display_name", "label", "title")


def describe_opaque(value):
                                                                                
                                                                        
                                                        
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


                                                                              
                                                                              
                                                                       
                                                                         
                                                                     
 
                                                                                
                                                                              
                                                         
SCALAR_VALUE_TYPE_NAMES = (
    "BOOLEAN", "DOUBLE", "DOUBLE3", "FLOAT", "FLOAT2", "FLOAT3", "FLOATARRAY",
    "INTEGER", "INTEGERLIST", "STRING", "STRINGLIST",
)


def param_type_name(ptype):
                                                                             
                                                                             
                                                            

                                                                         
                                                                              
                                                                                 
    if ptype is None:
        return "unknown"
    name = lookup_type_name(PARAM_TYPE_NAMES, ptype)
    if name is None:
        if isinstance(ptype, int):
            return "{0} (unnamed on this build)".format(ptype)
        return describe_opaque(ptype)
    return "{0} ({1})".format(ptype, name)


def is_scalar_value_type(ptype):
                                                                                
    return lookup_type_name(PARAM_TYPE_NAMES, ptype) in SCALAR_VALUE_TYPE_NAMES


def describe_target_param(node, param_name):
                                                                            
                                                                              
                                                    
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


                                                                               
_EDGE_READBACK_API = [None]


def graph_edges(graph):
                                                                            
                                                                             
                                                                              
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
                                                                           

                                                                              
                                                                                
                                                                            
                                                                               
                                                                             
                                                        

                                                                               
                                                                          
              
    fn = getattr(node, "getName", None)
    if fn is not None:
        try:
            value = fn()
        except Exception:
            value = None
        if isinstance(value, str) and value.strip():
            return ("name", value)
                                                                               
                                                                              
                            
    return ("object", id(node))


def _edge_target_of(edge):
                                                                               
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
                                                                                
                                                                      

                                                                               
                                                                                
       
    edges = graph_edges(graph)
    if edges is None:
        return None
                                                                             
                                                                              
                                                                         
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


                                                                                
_NEW_EDGE_PROBED = [False]

                                                                    
_EDGE_ID_TRIP_REPORTED = [False]


def probe_new_edge_return(graph, handed_back):
                                                                                 
                          

                                                                 
                                                                         
                                                                               
                                                                              
                                                                                
                                                                              
                                                                             

                                                                                
                                                                               
                                                                             
                                                                           
                   

                                                                                 
                                                                               
                                                                              
                                                                  

                                                                           
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
                                                                                
                                                                                
                                                          
    what = label or param
    ptype, pure, type_text = describe_target_param(target, param)
    try:
        handed_back = graph.newEdge(source=source, target=target, param=param)
    except Exception as e:
        print("  [warn] couldn't wire {0}: {1} [{2}]".format(what, e, type_text))
        return False
                                                                               
                                                                               
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
                                                                                 
                                                                          
                                                                               
                                                                            
                                                                         
    if verdict is not True and is_scalar_value_type(ptype):
        print("      note: that target is a scalar type. M5 probed this and it "
              "goes BOTH ways -- drivable on a BRDF (curvature -> "
              "metal.roughness landed and read back), not drivable on a texture "
              "node (bump_height). The node name on the line above is the "
              "discriminator; judge it on the render.")
    return True


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


def _try_set_placement(param, value, what):
                                                                                 
                                                                               
    try:
        param.setValue(value)
        return True
    except Exception as e:
        print("  [info] placement: {0} not settable here ({1})".format(what, e))
        return False


def _placement_param(node, keywords, what):
                                                                                  
                                                                                   
    p = find_param(node, keywords)
    if p is None:
        print("  [info] placement: {0} not settable here (no matching param)".format(what))
        return None
    if p.isPure():
        print("  [info] placement: {0} is connection-only here -- skipped".format(what))
        return None
    return p


def _jitter_mult(node, keywords, rng, lo, hi, what, base_default=None):
                                                                              
                                                                                 
                                                                                   
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
                                                                                
                                                                             
    p = _placement_param(node, keywords, what)
    if p is None:
        return False
    return _try_set_placement(p, rng.uniform(lo, hi), what)


def _set_fresh_seed(node, rng, what="seed"):
                                                                             
                                                                           
                                                                                 
    p = _placement_param(node, [what, "seed"], what)
    if p is None:
        return False
    return _try_set_placement(p, rng.randint(0, 999999), what)


def randomize_placement(node, rng, kind=None, scale_base=None):
                                                                                 
                                                                                  
                                                                                
                                                                                  
                                                                               
                                                                          
                                                                                  
                                                                            
                                                                                  
                           
    if node is None:
        return
    k = (kind or "").strip().lower()

                                                                                
                                                                                
                                             
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
                                                                                
        pass
    elif k == "spots":
                                                                             
        _set_fresh_seed(node, rng)
        _jitter_add(node, ["distortion"], rng, 0.0, 0.15, "distortion", cap=1.0)
        _jitter_mult(node, ["radius"], rng, 0.85, 1.2, "radius")
    elif k == "cellular":
        _jitter_mult(node, ["noise scale", "noise_scale"], rng, 0.7, 1.4, "noise_scale")
        _jitter_mult(node, ["shape 1", "shape_1"], rng, 0.9, 1.1, "shape_1")
        _jitter_mult(node, ["shape 2", "shape_2"], rng, 0.9, 1.1, "shape_2")
        _jitter_mult(node, ["shape 3", "shape_3"], rng, 0.9, 1.1, "shape_3")
    elif k == "occlusion":
                                                                                
                                                           
        _jitter_set(node, ["bias x", "bias_x"], rng, -0.5, 0.5, "bias_x")
        _jitter_set(node, ["bias y", "bias_y"], rng, -0.5, 0.5, "bias_y")
        _jitter_set(node, ["bias z", "bias_z"], rng, -0.5, 0.5, "bias_z")
    else:
        print("  [info] placement: unknown node kind {0} -- only scale jittered".format(repr(kind)))


                                                       
                                                                              
                                                                     
BLEND_LIGHTEN_NAME = "Lighten"


BLEND_LIGHTEN_INT = 7


def _blend_matches(got, name, ival):
    if got == ival:
        return True
    if isinstance(got, str) and got.strip().lower() == name.lower():
        return True
    return False


def set_blend_mode(node, mode_name, mode_int):
                                                                                 
                                                                                
                                                                                 
                                                                   
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
                                                                                 
                                                                               
                                                                               
                                                                        
    for val in (mode_name, mode_int, mode_name.lower(), mode_name.upper()):
        try:
            p.setValue(val)
        except Exception:
            continue
        if not can_read:
                                                                               
                                                                              
                                              
            return True
        try:
            got = p.getValue()
        except Exception:
            return True
        if _blend_matches(got, mode_name, mode_int):
            return True
    print("  [warn] couldn't confirm blend mode '{0}' -- left at node default".format(mode_name))
    return False


                                                                            
                                                  
                                                                            
                                                                               
                                                                       
                                                                                   
                                  
CENTER_ON_PART_INTS = (2,)


                                                                          
                          
CENTER_ON_OVERRIDE = None


def set_center_on_override(value):
                                                                             
                                                   
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
                                                                               
                                                      

                                                                                  
                                                                               
                                                                        
                                                                             
                                                                        
                                                                              
                                                                               
                                                                            
    src = find_param(comp, ["source", "foreground", "top"])
    bg = find_param(comp, ["background", "base", "bottom"])
    if src is not None and bg is not None and src.getName() != bg.getName():
        return src.getName(), bg.getName()

    try:
        params = comp.getParameters()
    except Exception:
        params = []

                                                                               
                                                        
    conn_type = None
    for cand in (src, bg):
        if cand is not None and conn_type is None:
            try:
                conn_type = cand.getType()
            except Exception:
                conn_type = None

    names = []
    if conn_type is not None:
                                                                    
                                                                    
        for p in params:
            try:
                if p.getType() == conn_type and not p.isPure():
                    names.append(p.getName())
            except Exception:
                continue
    else:
                                                                               
                                                                                   
                                                                           
                                                                                  
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
                                                                           
                                            
    if composited:
        ok2 = wire_scalar_driver(graph, sources[0], base_node, ["roughness"], "roughness (fallback)")
        return "single-fallback" if ok2 else "value"
    return "value"


                                                                               
                                                                                 
                                                                           
                                                                             
                                                                            
                                                        
                                                                       
                                                                             
                                                       
RADIUS_DISPLAY_FACTOR = 1000.0
RADIUS_DISPLAY_FACTOR_LIVE = [RADIUS_DISPLAY_FACTOR]

                                                                  
                                                                             
                                                                          
SCENE_MM_PER_UNIT_LIVE = [None]

                                                                                
                                                                                
                                                                                  
                                                                                  
                                                                                
                                                  
PART_MM_LIVE = [None]

                                                                              
                                                                    
RADIUS_MAX_PART_FRACTION = 0.25

                                                                                
                                        
CLAMP_UNKNOWN_SAID = [False]

                                                                            
                                                                             
                                                                          
CLAMP_REPORT_ONLY = [False]


def resolve_part_mm(scale_info):
                                                                  

                                                                            
                                                                        
                                                                       
    entered = as_float(scale_info.get("part_size_mm"), 0.0)
    if entered > 0.0:
        return entered
    extent = as_float(scale_info.get("part_extent_scene"), 0.0)
    per_unit = as_float(scale_info.get("units_to_mm"), 0.0)
    if extent > 0.0 and per_unit > 0.0:
        return extent * per_unit
    return 0.0


def clamp_radius_to_part(radius_mm, label):
                                                                         

                                                                                 
                                                                                
                                                                          

                                                                                
                                                                                  
                                                                                  
                                                                             
                                                             
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
                                                                     

                                                                               
                                                         

                                                                
                                                                              
                                                                               
                                                                               
                                                                         
                                             

                                                                                
                                                                              
                                                                                
                                                                                
                                          

                                                                               
                                                                                
                                                                                
                                                                 
    radius_mm = clamp_radius_to_part(radius_mm, label)
    p = find_param(node, ["radius in pixels", "adaptive_radius", "adaptive radius"])

    if p is None:
                                                                              
                                                                               
                                                                              
                                                                          
                                                                            
                            
         
                                                                              
                                                                                
                                                                              
                                                                               
                                                                       
         
                                                                                
                                                                       
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


                                                                           
                                        
CURVATURE_CUTOFF = None


def set_curvature_cutoff(node, cutoff=None):
                                                                                

                                                                               
                                                                               
                                                                               
                                                                               
                                                                            
                              

                                                                               
                                                                             
                                                                               
                                                                                 

                                                                                
                                                                

                                                                           
                                                                           
                                                                         
                                                                              
                                                                 

                                                                                
                                                                              
                                                                              
                                                                           
                             

                                                                               
                                                 

                                                                            
                                                                             
                                          
                                                                         
                                                                         
                                                             
                                                                              
                                                            

                                                                               
                                                                          
                                                                             
                                                                           
                                                                                
                              

                                                                              
                                                                             
                                                                             
                                                                               
                                                                             
                                                                             
                                                    

                                                                             
                                                                          
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
                                                                            
                                                                            
                                                                               
                                                                             
        inv = try_new_node(graph, "SHADER_TYPE_COLOR_INVERT",
                           "Color Invert (AO suppression)")
        if inv is None:
            print("    [warn] AO suppression: no Color Invert on this build -- "
                  "occlusion left out rather than wired the wrong way round")
            _drop_node(graph, occlusion)
        else:
                                                                              
                                                                         
                                                                                
                                                                             
                                                                               
                                                                             
                                                                        
                                                                                
                                                                            
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
                                                                                
                                                                                 
                                                                               
                                            
        try:
            if not effect_node.getInputEdge(inside.getName()):
                print("  [warn] {0}: the mask edge was accepted but reads back "
                      "empty -- treating as unmasked".format(label))
                ok = False
        except Exception:
            pass                                                              
    if not ok:
        print("  [info] {0}: colour slot refused the mask -- left unmasked".format(label))
        _drop_node(graph, mask_node)
        return effect_node
                                                                                
                                                                        
    if not set_display(effect_node, ["outside_color", "background"], (0.0, 0.0, 0.0),
                       ptype=PT_COLOR):
        print("  [info] {0}: mask wired, but the background colour could not be "
              "set to black -- wear will still show on the flats".format(label))
    else:
        print("  [info] {0}: colour masked (roughness bus only -- bump_height "
              "cannot be wired on this build, see mask_bump_layer docstring; "
              "caller should drop this node from bump_sources)".format(label))
    return effect_node


def _drop_node(graph, node):
                                                                              
                                            
    try:
        graph.removeNode(node)
    except Exception:
        pass


def make_image_map(graph, path, label, label_scale=1.0):
                                                                                
                                                                                    
                                                                                    
                                                                                
                                                                                 
                                                                    
                                                   
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
                                                                          
    dump_node(n, "Image Map ({0}) [{1}]".format(label, resolved_attr))
                                                                        
                                                                          
                                                                                  
                                                                             
                                                                                
                                                                                  
                               
    ok = set_display(n, ["texture"], path, ptype=PTYPE_STRING)
    if not ok:
                                                        
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
                                                                               
    set_center_on_part(n)
    set_display(n, ["scale"], label_scale)
    return n


def _make_colour_node(graph, base_color):
                                                                                   
                                                                                
                                                                               
                                                               
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
                                                                                   
                                                                                     
                                                                        
    set_display(n, ["color", "colour", "diffuse"], base_color)
    return n


def wire_audit(base_node, label="base"):
                                                                               
                                                                           
                                                                          
                                                                 
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
                                                                             
                                                                                
    try:
        nm = node.getName()
    except Exception:
        return False
    if not nm:
        return False
    return name_filter.lower() in nm.lower()


def apply_material_to_parts(name, name_filter=None):
                                                                         
                                                                             
                                                                        
                                                                             
                                                                          
                                                        

                                                                                
                                                                                 
                                                                            
                                                                                 
                                                                         
    root = lux.getSceneTree()

                                                                              
                                        
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
                                                                                
                                   
                ok = True
        if ok:
            applied += 1
            if DEBUG:
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
        else:
            skipped += 1

                                                                               
                                                                              
                                                                               
                                                                              
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
                                                                              
                                                                              
                                                                           
                    reader = getattr(lux, "getObjectMaterial", None)
                    if reader is not None and applied:
                                                                                 
                                                                              
                                                                             
                                                                                
                                                                             
                                                                             
                                                                                
                                                                            
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


                                                                                

                                                                                  
                                                                                   
                                                                                   
                                                                                 
                                                                                   
                                                                                    
                                                                                  
                                                                                  
                                                                            
                                                                                    
                                                                          
                                                                    
EDGE_MASK_RADIUS_MM = 1.5
CAVITY_MASK_RADIUS_MM = 10.0
                                                                                 
                                                                                
                                                            
EDGE_RADIUS_FRACTION = 0.008
CAVITY_RADIUS_FRACTION = 0.05


import math
import json


                                                                            
                     
                                                                            


GENERATOR_REV = "AB36"


                                                                                 
                                                                                    
                                                                                   
          
                                                                               
                                                                                
                                                                              
                                                                                 
                                                                              
                                                                              
                        
LABEL_DEMO_DIR = ""


def _label_demo(filename):
                                                                                  
                                                               
                                                                               
                                                                             
                                                                               
    if not LABEL_DEMO_DIR:
        return NO_LABEL
    return LABEL_DEMO_DIR.rstrip("/") + "/" + filename

                                                                            
                                        
                                                                            
                                                                               
                                                                             
                                                                             
                                    
DEFAULT_PART_SIZE_MM = 50.0




                                                                            
                       
                                                                            

                                                                           
                                                                             
                                                                             
                                                                            
                                                                              
                                                                             
                                                                              
 
                                                                             
                                                                                
                                                                                  
                                                                             
                                                                                  
                                                                              
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
                                                                                  
                                                                                   
                                                                                   
                                                                                
                                                                                
    ("Aluminum (anisotropic brushed)", "SHADER_TYPE_METAL", (0.72, 0.73, 0.75), 0.18, "ANI",
        {"family": "metal_aniso", "anisotropy": 0.5, "aniso_angle": None}),
    ("Steel (anisotropic)",            "SHADER_TYPE_METAL", (0.55, 0.56, 0.58), 0.22, "ANS",
        {"family": "metal_aniso", "anisotropy": 0.6, "aniso_angle": None}),
                                                                               
                                                                                  
                                                                                    
    ("Glass (clear)",                  "SHADER_TYPE_DIELECTRIC", (0.95, 0.97, 0.98), 0.02, "GLC",
        {"family": "dielectric", "ior": 1.51, "transparent": True, "frost": 0.0}),
    ("Glass (frosted)",                "SHADER_TYPE_DIELECTRIC", (0.95, 0.97, 0.98), 0.30, "GLF",
        {"family": "dielectric", "ior": 1.51, "transparent": True, "frost": 0.30}),
                                                                                   
                                                                         
    ("Thin Film (oil slick)",          "SHADER_TYPE_THIN_FILM", (0.30, 0.30, 0.32), 0.10, "TFM",
        {"family": "thinfilm", "film_thickness": 420, "film_ior": 1.4}),
    ("Anodised (iridescent)",          "SHADER_TYPE_THIN_FILM", (0.20, 0.22, 0.28), 0.15, "IRI",
        {"family": "thinfilm", "film_thickness": 650, "film_ior": 1.4}),
]
MATERIAL_TYPE_ORDER = [m[0] for m in MATERIALS]
MATERIAL_BY_NAME = {m[0]: m for m in MATERIALS}
TYPE_ABBR = {m[0]: m[4] for m in MATERIALS}


def material_extra(mat):
                                                                                  
                                                                                  
                                    
    if len(mat) >= 6 and isinstance(mat[5], dict):
        return mat[5]
    return {}


def material_family(extra):
                                                                                
                                                                           
                                                         
    if not isinstance(extra, dict):
        return "opaque"
    return extra.get("family", "opaque") or "opaque"

WEAR_PRESETS = {"Pristine": 0.3, "Light Wear": 1.0, "Moderate Wear": 2.5, "Heavy Wear": 5.0}
WEAR_ORDER = list(WEAR_PRESETS.keys())
WEAR_ABBR = {"Pristine": "PRI", "Light Wear": "LGT", "Moderate Wear": "MOD", "Heavy Wear": "HVY"}

                                                                          
                                                                             
                                                                        
                                                                               
                                                                            
                                                                            
                                                            
                                                                            
FINISH_PRESETS = {
    "Pristine": (0.1, 0.0, 1, -0.008),
    "Brushed":  (0.5, 0.1, 2, -0.012),
    "Worn":     (0.8, 0.3, 3, -0.018),
    "Heavy":    (1.0, 0.6, 4, -0.025),
}
FINISH_ORDER = ["Pristine", "Brushed", "Worn", "Heavy"]
                                                                               
                                                   
FINISH_ABBR = {"Pristine": "PRS", "Brushed": "BRU", "Worn": "WRN", "Heavy": "HEV"}

                                                                        
                                                                          
                                                                            
                                                                                  
                                                                          
                                                                                  
                                                                               
                           
BASE = {
    "fine_noise_scale":    0.15,
    "fine_noise_bump":     0.01,
    "fractal_scale":       4.0,
    "scratch_bump_height": 0.02,
    "scratch_density":     0.12,
    "scratch_size":        0.04,
                                                                                 
                                                                               
                                                                                 
    "scratch_scale":       5.0,
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

                                                                               
                                                                             
                                                                                 
                                                                             
                                                                                 
                                                                               
                                                                                
                                                                            
                                                                            
                                                                            
                                                               
FAMILY_ALLOWED_LAYERS = {
    "opaque":      set(FEATURE_KEYS),
    "metal_aniso": set(FEATURE_KEYS),
    "dielectric":  set(["add_fine_noise", "add_scratches",
                        "add_rounded_edges", "add_fractal_roughness"]),
    "thinfilm":    set(["add_fine_noise", "add_scratches", "add_rounded_edges"]),
}

                                                                              
                                                                              
                           
MASK_KEYS = ["mask_scratches_to_edges", "mask_spots_to_cavities"]

                                                                           
                                                                             
                                                                               
                                                                               
                                                                      
USE_DIALOG = True







DEFAULT_OPTIONS = {
    "name_prefix": "MAT",
    "material_type": "Aluminum (brushed metal)",
    "wear_level": "Light Wear",
                                                                               
                                                                                 
    "finish": "Brushed",
    "wear_multiplier": 1.0,
                                                                                  
                                                                                 
                                                
    "part_size_mm": 0.0,
                                                                                
                                                                                 
                                                                          
    "center_on_int": 2,
                                                                                  
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
                                                                            
                                                                             
                                                                               
    "random_seed": "auto",
    "name_filter": "",
                                                                                   
                                                                                  
                                                                                
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
                                                                              
                                                                              
                                                                            
                                                                         
        ("material_type", lux.DIALOG_ITEM, "Material type:",
         MATERIAL_TYPE_ORDER.index(DEFAULT_OPTIONS["material_type"]), MATERIAL_TYPE_ORDER),
        ("wear_level", lux.DIALOG_ITEM, "Wear level:",
         WEAR_ORDER.index(DEFAULT_OPTIONS["wear_level"]), WEAR_ORDER),
                                                                       
                                                                              
        ("finish", lux.DIALOG_ITEM, "Finish (surface character):",
         FINISH_ORDER.index(DEFAULT_OPTIONS["finish"]), FINISH_ORDER),
        ("wear_multiplier", lux.DIALOG_DOUBLE, "Wear fine-tune (x):",
         DEFAULT_OPTIONS["wear_multiplier"], (0.0, 3.0)),
                                                                             
                                                                           
        ("part_size_mm", lux.DIALOG_DOUBLE,
         "Real part size in mm (log only -- scale is measured):",
         DEFAULT_OPTIONS["part_size_mm"], (0.0, 100000.0)),
                                                                                  
                                                                                    
        ("center_on_int", lux.DIALOG_INTEGER,
         "Texture 'Center On' int (2 = Part, 0 = Legacy):",
         DEFAULT_OPTIONS["center_on_int"], (0, 8)),
                                                                                
                                                                      
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
                                                                                 
    for key in ("label_opacity_path", "label_bump_path", "label_spec_path"):
        opts[key] = normalise_label_path(opts.get(key))
    return opts


                                                                            
                                        
                                                                            







                                                                         
                                                                                 
                                                                                 
                                                                                  
FAMILY_SHADER_FALLBACKS = {
    "dielectric": ["SHADER_TYPE_DIELECTRIC", "SHADER_TYPE_GLASS", "SHADER_TYPE_SOLID_GLASS"],
    "thinfilm":   ["SHADER_TYPE_THIN_FILM"],
                                                                            
                                                                             
                                                                             
                                                                      
    "metal_aniso": ["SHADER_TYPE_ANISOTROPIC", "SHADER_TYPE_METAL"],
}

                                                                               
                                                                          
                     
FAMILY_OVERRIDES_SHADER = ("metal_aniso",)


                                                                                 
                                                                  
                                                              
LAST_SHADER_ATTR = None


def resolve_shader(shader_attr, family="opaque"):
                                                                                 
                                                                                
                                                                                      
                                                                                   
                                                                                    
    if family in FAMILY_OVERRIDES_SHADER:
                                                                              
        chain = []
    else:
        chain = [shader_attr]
    for alt in FAMILY_SHADER_FALLBACKS.get(family, []):
        if alt not in chain:
            chain.append(alt)
    if shader_attr not in chain:
        chain.append(shader_attr)
                                                                                   
                                                                              
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
                                                                                 
                                                                                 
                                                        
                if family in FAMILY_OVERRIDES_SHADER and chain and attr == chain[0]:
                    print("  [info] family '{0}' overrides the row's {1} -- building on {2} "
                          "(different BRDF, deliberate)".format(family, shader_attr, attr))
                else:
                    print("  [warn] {0} unavailable on this build -- using {1} instead".format(
                        shader_attr, attr))
            return st
    return None


def apply_family_params(graph, base_node, extra, rng):
                                                                                 
                                                                                   
                                                                                 
                                                                           
                                                                                
                                                                               
                                                                                     
    family = material_family(extra)
    if family == "metal_aniso":
                                                   
                                                                                 
                                                                                 
                                                                        
                                                                        
                                                                                  
                                                                                   
                                                                              
                                                                
        aniso = clamp01(as_float(extra.get("anisotropy"), 0.5))
        base_r = clampf(as_float(extra.get("base_roughness"), 0.25), 0.01, 1.0)
        set_display(base_node, ["roughness x"], clampf(base_r * (1.0 - 0.8 * aniso), 0.005, 1.0))
        set_display(base_node, ["roughness y"], clampf(base_r * (1.0 + 2.0 * aniso), 0.005, 1.0))
                                                                             
                                                                                  
                                                                            
                                                                                
                                                                           
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
                                                                               
                                                                                 
                                                                                 
                                                                              
                                                                             
                                                                              
                                                                                
                                                                          
                                                           
            set_display(base_node, ["roughness transmission", "refraction roughness"], frost)
                                                                                 
    elif family == "thinfilm":
        set_display(base_node, ["thickness", "film thickness"],
                    clampf(as_float(extra.get("film_thickness"), 500.0), 1.0, 2000.0))
        set_display(base_node, ["index of refraction", "ior"],
                    clampf(as_float(extra.get("film_ior"), 1.4), 1.0, 3.0))
    return family














                                                                            
                                                                      
                                                                            
                                                                             
                                                                             
                             
 
                                                                              
                                                                               
                                                                             
                                                                   
                                                  
 
                                                                        
                                                                               
                                                                              
                                                                             
                                                                             
                                                                          
                                                                               
                                                                     
                                                                      
                                                                          
                                                             
                                                                               
                                                                           
                                                                              
                                                                            
                                                                             
                                                                         
                                                                              
                                                                             
                                                                  
















                                                                            
                                                                       
                                                                            
                                                                             
                                                                                
                                                                                
                                                                                
                                                                               
                                                                                
                                                                               
                 




















                                                                            
                                                                         
                                                                             
                                                                            
                                                                           
                                                                            









                                                                            
                                                                           
                                                                         
                                                                           
                                          
                                                                            

def add_fine_noise_bump(graph, scale=None):
    n = try_new_node(graph, "SHADER_TYPE_NOISE_TEXTURE", "Fine Noise")
    if n:
                                                                                
                                                           
        set_display(n, ["scale"], scale if scale is not None else BASE["fine_noise_scale"])
                                                                                  
                                                   
        set_display(n, ["bump height"], BASE["fine_noise_bump"])
                                                     
        set_center_on_part(n)
    return n


def add_scratches_bump(graph, wear_mult, base_roughness, finish, damping=1.0, scale=None):
                                                                                 
                                                                               
                                                                                
                                                                                  
                                                                                
                                                                          
    n = try_new_node(graph, "SHADER_TYPE_SCRATCHES", "Scratches")
    if n:
        dir_noise = finish.get("dir_noise", BASE["scratch_dir_noise"])
        noise = finish.get("noise", BASE["scratch_noise"])
        levels = finish.get("levels", BASE["scratch_levels"])
        finish_bump = finish.get("scratch_bump_height", -BASE["scratch_bump_height"])
                                                                              
                                                                           
                                                                                
        eff_bump = -clamp01(abs(finish_bump) * wear_mult * damping)
        set_display(n, ["bump height"], eff_bump)
                                     
        set_display(n, ["density"], clamp01(BASE["scratch_density"] * wear_mult))
        set_display(n, ["size"], clamp01(BASE["scratch_size"] * wear_mult))
                                                                              
                                                                               
                                                   
        set_display(n, ["directional noise"], clamp01(dir_noise))
        set_display(n, ["noise"], clamp01(noise))
        set_display(n, ["levels"], levels)
                                                                                  
                                                                                   
                                                                                 
                                                                                  
                                                                                      
        set_display(n, ["scale"], scale if scale is not None else BASE["scratch_scale"])
                                                                              
                                                                           
                                                                                
                                                                              
                                                                              
                                                                                
                                                      
        set_display(n, ["color"], (0.75, 0.75, 0.75), ptype=PT_COLOR)
        bg = clamp01(base_roughness)
        set_display(n, ["background"], (bg, bg, bg), ptype=PT_COLOR)
                                                     
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
                                                                           
        set_display(n, ["radius"], clamp01(BASE["spots_size"] * wear_mult))
                                                                                  
                                                                                    
                                                                                
                                                                           
                                                                                  
                                                               
        if scale is not None:
            set_display(n, ["scale"], scale)
                                                                                    
                                                                                   
                                                                   
        set_display(n, ["distortion"], 0.4)
        if scale is not None:
            set_display(n, ["distortion scale", "distortion_scale"], scale)
                                                     
        set_center_on_part(n)
    return n


def add_cellular_bump(graph, wear_mult, damping=1.0, scale=None):
                                                                          
                                                                          
    n = try_new_node(graph, "SHADER_TYPE_CELLULAR", "Cellular (experimental)")
    if n:
                                                                                 
        set_display(n, ["scale"], scale if scale is not None else BASE["cellular_scale"])
        set_display(n, ["bump height", "height"],
                    clamp01(BASE["cellular_bump_height"] * wear_mult * damping * 0.6))
                                                     
        set_center_on_part(n)
    return n


def make_fractal_roughness_node(graph, base_roughness, scale=None):
                                                                               
                                                                              
                                       
    n = try_new_node(graph, "SHADER_TYPE_NOISE_FRACTAL", "Fractal Noise (roughness source)")
    if n is not None:
                                                                                 
        set_display(n, ["scale"], scale if scale is not None else BASE["fractal_scale"])
                                                                                  
                                                                             
                                                                             
                                                                                  
                                                                                   
        lo = clamp01(base_roughness - 0.06)
        hi = clamp01(base_roughness + 0.08)
        set_display(n, ["color 1", "color1", "color a"], (lo, lo, lo), ptype=PT_COLOR)
        set_display(n, ["color 2", "color2", "color b"], (hi, hi, hi), ptype=PT_COLOR)
                                                     
        set_center_on_part(n)
    return n


def make_occlusion_roughness_node(graph, base_roughness, radius_mm=None):
                                                                                   
                                                                                
                                                                              
                                                                            
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (roughness/grime source)")
    if n is not None:
                                                                       
        if radius_mm is not None:
            set_radius_mode(n, False, radius_mm, 4.0, "occlusion roughness")
                                                                               
                                                                                  
        grimy = clamp01(base_roughness + 0.35)
        exposed = clamp01(base_roughness)
        set_display(n, ["occluded"], (grimy, grimy, grimy), ptype=PT_COLOR)
        set_display(n, ["unoccluded", "bright", "far", "exposed"],
                    (exposed, exposed, exposed), ptype=PT_COLOR)
    return n


def make_occlusion_color_node(graph, base_color, radius_mm=None):
                                                                                
                                                                            
                                                       
                                                                              
                                                                           
                                                                          
                                                      

                                                                    
                                                                              
                                                                             
                                                                            
                                      
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (colour/grime source)")
    if n is not None:
        if radius_mm is not None:
            set_radius_mode(n, False, radius_mm, 4.0, "occlusion colour")
                                                                                
                                                                               
                                                                               
        grey = sum(base_color[:3]) / 3.0
        desat = tuple(clamp01(c * 0.4 + grey * 0.6) for c in base_color[:3])
        grime = tuple(clamp01(c * 0.35) for c in desat)
        exposed = tuple(clamp01(c) for c in base_color[:3])
        set_display(n, ["occluded"], grime, ptype=PT_COLOR)
        set_display(n, ["unoccluded", "bright", "far", "exposed"], exposed,
                    ptype=PT_COLOR)
    return n


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


                                                                            
                                                                                 
                                                                                 
                                                                                 
                                                                                 
                                                                                
                                                                            





def _apply_label_colour_overlay(graph, base_node, base_color, opacity_path, label_scale):
                                                                                  
                                                                                  
                                                                             
                                                                       

                                                                                   
                                                                                     
                                                                                     

                                                                                     
                                                                           
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
                                
    safe_edge(graph, source=label_node, target=comp, param=src_name, label="label overlay source")
                                                                                   
                                                                                  
    bg_ok = False
    colour_node = _make_colour_node(graph, base_color)
    if colour_node is not None:
        bg_ok = safe_edge(graph, source=colour_node, target=comp, param=bg_name,
                          label="label overlay background")
    if not bg_ok:
                                                                               
                                                                      
        bg_ok = set_display(comp, ["background", "base", "bottom"], base_color)
    if not bg_ok:
                                                                            
                                                                                      
        print("  [info] label colour overlay skipped -- couldn't set the base colour as the "
              "composite background (would blacken non-label areas); bump/spec still applied")
        try:
            graph.removeNode(comp)
        except Exception:
            pass
        return
                                                                                      
                                                                              
    set_blend_mode(comp, "Normal", 0)
                                                                                    
                                                                                   
                                                                             
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
                                                                                   
                                                                                  
                                                                                 
                                                                               
                                                                                    
                                                                        
    opacity_path = label.get("opacity_path", "") or ""
    bump_path = label.get("bump_path", "") or ""
    spec_path = label.get("spec_path", "") or ""
    label_scale = as_float(label.get("scale"), 1.0)
    bump_strength = as_float(label.get("bump_strength"), 1.0)
    spec_strength = as_float(label.get("spec_strength"), 1.0)

                                                                            
                                                                                    
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

                                                                                
                                                         
    if opacity_path:
        try:
            _apply_label_colour_overlay(graph, base_node, base_color, opacity_path, label_scale)
        except Exception as e:
            print("  [info] label colour overlay skipped ({0}) -- bump/spec still applied".format(e))


                                                                            
                                                                
                                                                            



                                                                            
                                                           
                                                                            

def sample_spec(opts):
                                                                             
                                                                              
                                                                                
                                                                              
                                                                               
                    
    material_type = opts.get("material_type", DEFAULT_OPTIONS["material_type"])
    wear_level = opts.get("wear_level", DEFAULT_OPTIONS["wear_level"])
    finish_name = opts.get("finish", DEFAULT_OPTIONS["finish"])
    wear_multiplier = float(opts.get("wear_multiplier", 1.0))

    seed = _apply_seed(opts)
                                                                                 
                                                                                
                                          
    placement_seed = derive_placement_seed(seed)

    features = {k: bool(opts.get(k, False)) for k in FEATURE_KEYS}
    randomized = bool(opts.get("randomize_features"))
    if randomized:
        features = randomize_feature_flags()

    masks = {k: bool(opts.get(k, False)) for k in MASK_KEYS}

    mat = MATERIAL_BY_NAME.get(material_type, MATERIAL_BY_NAME[DEFAULT_OPTIONS["material_type"]])
                                                                                  
                                                                                  
                                                                                   
    shader_attr = mat[1]
    base_color = mat[2]
    base_roughness = mat[3]
    extra = dict(material_extra(mat))
    family = material_family(extra)

    fp = FINISH_PRESETS.get(finish_name, FINISH_PRESETS[DEFAULT_OPTIONS["finish"]])

                                                                                   
                                                                                   
                                                                                    
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
                                                                                      
            "family": family,
        },
        "base": {
            "shader": shader_attr,
            "color": [base_color[0], base_color[1], base_color[2]],
            "roughness": base_roughness,
                                                                         
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
                                                                                 
                                                                                  
                                                                           
                                                                              
        "scale": {
                                                                               
                                                                                
                                                                
            "part_extent_scene": part_size,
            "part_size_mm": as_float(opts.get("part_size_mm"), 0.0) or None,
            "units_to_mm": units_to_mm,
            "scale_factor": as_float(opts.get("scale_factor"), TEXTURE_SCALE_FACTOR),
            "source": size_source,
                                                                               
                                                                           
                                
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
                                                                               
                                                                                
                                   
    base["extra"] = validate_family_extra(base.get("extra", {}))

                                                                                  
                                                                                   
                                            
    scale = spec.setdefault("scale", {})
                                                                                 
                                                                    
    extent = as_float(scale.get("part_extent_scene"), DEFAULT_PART_EXTENT)
    if extent <= 0.0:
        extent = DEFAULT_PART_EXTENT
    scale["part_extent_scene"] = extent
    scale.setdefault("source", "default")
    scale.setdefault("part_size_mm", None)
    scale.setdefault("units_to_mm", None)

                                                                             
                                                                                 
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
                                                                             
                                                                             
                                                                      
    try:
        print("SPEC {0}".format(json.dumps(spec, sort_keys=True)))
    except Exception:
        print("SPEC {0}".format(repr(spec)))


                                                                            
                                
                                                                            

def build_material(spec):
                                                                            
                                                                           
                                                                    
    meta = spec["meta"]
    base = spec["base"]
    wear = spec["wear"]
    finish = spec.get("finish", {})
    features = spec["features"]
    masks = spec["masks"]
    derived = spec.get("derived", {})
                                                                                  
    label = spec.get("label", {}) or {}
    labels_on = bool(label.get("enabled"))

    material_type = meta["material_type"]
    wear_level = meta["wear_level"]
    finish_name = meta.get("finish", DEFAULT_OPTIONS["finish"])
    wear_mult = wear["effective"]
    base_color = (base["color"][0], base["color"][1], base["color"][2])
    base_roughness = base["roughness"]

                                                                                   
                                                                                 
                                                                          
    scale_info = spec.get("scale", {})
    part_size = as_float(scale_info.get("part_extent_scene"), DEFAULT_PART_EXTENT)
    if part_size <= 0.0:
        part_size = DEFAULT_PART_EXTENT
    size_source = scale_info.get("source", "default")
                                                                             
                                                                              
                                                                                 
                                                                            
                                                                               
                          
    factor = resolve_scale_factor(scale_info.get("scale_factor"))
    tex_scales = {
        "fine_noise": part_size * SCALE_FRACTIONS["fine_noise"] * factor,
        "scratches": part_size * SCALE_FRACTIONS["scratch_scale"] * factor,
        "fractal": part_size * SCALE_FRACTIONS["fractal"] * factor,
        "cellular": part_size * SCALE_FRACTIONS["cellular"] * factor,
        "spots": part_size * SCALE_FRACTIONS["spots_scale"] * factor,
    }

                                                                           
                                                                        
                                                                            
                                                                             
                                                                           
                                                                              
                                                                              
                                                                         
    SCENE_MM_PER_UNIT_LIVE[0] = scale_info.get("units_to_mm")
                                                                               
                                                                                 
                                                                                
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

                                                                                 
    extra = base.get("extra", {}) or {}
    family = material_family(extra)

    shader_type = resolve_shader(base["shader"], family)
                                                                               
    spec["base"]["shader_used"] = LAST_SHADER_ATTR or base["shader"]
    if spec["base"]["shader_used"] != base["shader"]:
        print("  Shader: requested {0} -> built on {1}".format(
            base["shader"], spec["base"]["shader_used"]))
    if shader_type is None:
        raise RuntimeError("No usable base shader for '{0}'".format(material_type))

    seed = meta.get("seed")
    if seed is not None:
        print("  Seeded feature RNG with {0} (reproducible in randomize mode)".format(repr(seed)))

                                                                          
                                                                               
                                                                             
                                                 
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
    meta["name"] = name                                                     

    graph = lux.getMaterialGraph(name)
    root = graph.getRoot()
    if DEBUG:
        dump_node(root, "Root")

    base_node = new_node(graph, shader_type, material_type)
    safe_edge(graph, source=base_node, target=root, param="surface", label="base -> root.surface")
                                                                         
                                                                               
                                                                         
                                                    
                                                                             
                                                                                
                                                                           
                                        
    set_display(base_node, ["color", "diffuse", "tint", "reflectance", "base color"],
                base_color)
                                                                            
                                                                                
                                                                                
                                                     
    set_display(base_node, ["roughness"], base_roughness)

                                                                              
                                                                               
                                                                               
                                                                                  
    if family != "opaque":
                                                                             
                                                                           
        extra["base_roughness"] = spec["base"]["roughness"]
        apply_family_params(graph, base_node, extra, placement_rng)

                                                                              
                                                                         
                                                                                
                                                                             
                                                                               
    bump_sources = []
    scratches_node = None                                                          
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
                                                                               
                                                                               
                                                                                
                                                                                
                                                                  
            print("  [info] scratches->edges: groove depth left OUT of the bump "
                  "chain (unmaskable) -- wear reads as edge-confined roughness "
                  "only, not relief")
        else:
            bump_sources.append(scratches_node)
    if features["add_rounded_edges"]:
                                                                            
                                                                                  
        bump_sources.append(add_rounded_edges_bump(graph, wear_mult, damping))
    if features["add_spots"]:
        sp = add_spots_bump(graph, wear_mult, damping, tex_scales["spots"])
        randomize_placement(sp, placement_rng, "spots", tex_scales["spots"])
        if masks.get("mask_spots_to_cavities"):
            mask_bump_layer(graph, sp, add_occlusion_mask(graph, cavity_radius_mm),
                            "spots->cavities")
                                                                                  
                                                                                 
                                                                            
                                                  
            print("  [info] spots->cavities: pit depth left OUT of the bump "
                  "chain (unmaskable) -- grime reads as colour tint only, no "
                  "physical pitting")
        else:
            bump_sources.append(sp)
    if features["add_cellular"]:
        cell_node = add_cellular_bump(graph, wear_mult, damping, tex_scales["cellular"])
        randomize_placement(cell_node, placement_rng, "cellular", tex_scales["cellular"])
        bump_sources.append(cell_node)

                                                                                 
                                                                                  
                                                                         
                                                                            
                                                                             
                                                                             
                                                                             
                                                                              
                                                                           
                                                   
    rough_sources = []
    if scratches_node is not None:
        rough_sources.append(scratches_node)
    if features["add_fractal_roughness"]:
        fr = make_fractal_roughness_node(graph, base_roughness, tex_scales["fractal"])
        if fr is not None:
                                                                                         
            randomize_placement(fr, placement_rng, "fractal", tex_scales["fractal"])
            rough_sources.append(fr)
    if features["add_occlusion_roughness"]:
        oc = make_occlusion_roughness_node(graph, base_roughness, cavity_radius_mm)
        if oc is not None:
                                                                                
                                                                                  
                                                                                   
            randomize_placement(oc, placement_rng, "occlusion")
            rough_sources.append(oc)

                                                                              
                                                                          
                                                                                
                                                                                  
                                                                                    
                                
    if labels_on:
        apply_image_label(graph, base_node, base_color, label, bump_sources, rough_sources)

                                                                              
                                                                                
    combined_bump = combine_bump_sources(graph, bump_sources)
    if combined_bump is not None:
        base_bump_slots = connection_param_names(base_node, PT_SHADERBUMP)
        if base_bump_slots:
            safe_edge(graph, source=combined_bump, target=base_node, param=base_bump_slots[0],
                      label="combined bump -> base.bump")
        else:
            print("  [warn] base material has no bump input")

                                                                               
                                                                                 
    rough_mode = build_roughness_bus(graph, base_node, rough_sources)
    print("  Roughness bus: {0} source(s) -> mode '{1}'".format(len(rough_sources), rough_mode))

                                                                              
                                                                          
                                                                             
                                                                  
    if masks.get("mask_spots_to_cavities"):
        grime_node = make_occlusion_color_node(graph, base_color, cavity_radius_mm)
        if grime_node is not None:
            randomize_placement(grime_node, placement_rng, "grime_color")
            wire_scalar_driver(graph, grime_node, base_node,
                               ["color", "diffuse", "tint", "reflectance"],
                               "grime colour")
    if features["add_color_gradient"]:
                                                                         
                                                                       
                                                                         
                                                                             
                                                                            
                                                        
        gradient_wired = add_color_gradient(graph, base_node, base_color)
        if gradient_wired and masks.get("mask_spots_to_cavities"):
            print("  [info] colour bus: Color Gradient just overwrote the "
                  "grime tint on base.color -- only one wire survives")

                                                                              
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
        emit_spec(spec)                                                            
        apply_material_to_parts(material_name, name_filter=spec["application"]["name_filter"])