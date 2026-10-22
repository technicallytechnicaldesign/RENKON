                       
                                   
          
 
                                                                                                                     
 
                                                             
                                                                          
                                                       

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


                                                                                

VIEWER_REV = "AA27"

                                                                             
                                                                               
CLAMP_REPORT_ONLY[0] = True

MODE_CURVATURE = "1 curvature (edge mask)"
MODE_OCCLUSION = "2 occlusion (cavity mask)"
MODE_SCRATCHES = "3 scratches (raw pattern)"
MODE_SPOTS = "4 spots (raw pattern)"
MODE_MASKED = "5 masked texture (curvature -> scratch colour)"
MODE_COMPOSITE = "6 composite gate (RED source / GREEN background / curvature mask)"
MODE_WEAR = "7 composed wear mask (curvature primary, grunge weighted, AO suppressing)"
MODE_CALIBRATE = "8 CALIBRATE this scene (write 1.0 to both, read both panels)"
MODE_FLAT = "9 FLAT COLOUR null test (no nodes at all -- ladder R1)"

                                                                               
                                                                            
                                                                                
                                                
MODE_ORDER = [MODE_CURVATURE, MODE_OCCLUSION, MODE_SCRATCHES, MODE_SPOTS,
              MODE_MASKED, MODE_COMPOSITE, MODE_WEAR, MODE_CALIBRATE,
              MODE_FLAT]

                                                                          
                                                                             
                                                                               
                                                                               
                 
FLAT_TEST_COLOUR = (1.0, 0.0, 1.0)

                                                                                
                                                                            
GATE_SOURCE_COLOUR = (1.0, 0.0, 0.0)
GATE_BACKGROUND_COLOUR = (0.0, 1.0, 0.0)

DEFAULT_OPTIONS = {
    "mode_int": 1,
    "part_size_mm": 0.0,
    "radius_mm": 1.5,
    "texture_scale_fraction": 0.05,
    "scale_factor": 0.001,
    "center_on_int": 2,
    "cutoff": -1.0,
                                                                  
                                                                    
                                                                  
                                                                     
                                                                    
                                                                          
    "grunge_amount": 0.0,
    "ao_amount": 0.0,
    "wear_contrast": 0.0,
                                                                      
                                                                      
                                                                        
                                                                         
                                                                     
                                                              
    "radius_in_pixels": False,
    "radius_px": 4.0,
    "radius_display_factor": RADIUS_DISPLAY_FACTOR,
    "name_filter": "all",
}

                                                                            
                                                                       
NO_FILTER_WORDS = ("all", "none", "-", "")

RADIUS_FALLBACK_FRACTION = 0.008



def read_options():
                                                                               
                                                       
    try:
        values = [
            ("mode_int", lux.DIALOG_INTEGER,
             "WHAT TO LOOK AT -- 1 curvature, 2 occlusion, 3 scratches, "
             "4 spots, 5 masked texture, 6 composite gate, 7 composed wear "
             "mask, 8 CALIBRATE this scene, 9 FLAT COLOUR null test:",
             DEFAULT_OPTIONS["mode_int"], (1, 9)),
            ("part_size_mm", lux.DIALOG_DOUBLE,
             "Real part size in mm (needed to convert the radius):",
             DEFAULT_OPTIONS["part_size_mm"], (0.0, 100000.0)),
            ("radius_mm", lux.DIALOG_DOUBLE,
             "Radius in REAL mm (sweep THIS -- modes 1, 2, 5, 6):",
             DEFAULT_OPTIONS["radius_mm"], (0.001, 10000.0)),
            ("grunge_amount", lux.DIALOG_DOUBLE,
             "Mode 7 grunge amount (0 = pure curvature, no pattern):",
             DEFAULT_OPTIONS["grunge_amount"], (0.0, 1.0)),
            ("ao_amount", lux.DIALOG_DOUBLE,
             "Mode 7 AO suppression amount (0 = no occlusion in the mask):",
             DEFAULT_OPTIONS["ao_amount"], (0.0, 1.0)),
            ("wear_contrast", lux.DIALOG_DOUBLE,
             "Mode 7 wear contrast (0 = off):",
             DEFAULT_OPTIONS["wear_contrast"], (0.0, 10.0)),
            ("cutoff", lux.DIALOG_DOUBLE,
             "Curvature Cutoff (-1 = default of 1, the WORKING value; 0 = white everywhere):",
             DEFAULT_OPTIONS["cutoff"], (-1.0, 1.0)),
            ("texture_scale_fraction", lux.DIALOG_DOUBLE,
             "Texture scale, as a fraction of the part (modes 3, 4, 5):",
             DEFAULT_OPTIONS["texture_scale_fraction"], (0.0001, 2.0)),
            ("scale_factor", lux.DIALOG_DOUBLE,
             "Texture scale factor (0.001 observed on 13.2):",
             DEFAULT_OPTIONS["scale_factor"], (0.0000001, 1000.0)),
            ("center_on_int", lux.DIALOG_INTEGER,
             "Center On int (2 = Part):",
             DEFAULT_OPTIONS["center_on_int"], (0, 8)),
            ("radius_in_pixels", lux.DIALOG_CHECK,
             "Radius in PIXELS (off = scene units -- THE question)",
             DEFAULT_OPTIONS["radius_in_pixels"]),
            ("radius_px", lux.DIALOG_DOUBLE,
             "Radius in pixels (used when the box above is ON):",
             DEFAULT_OPTIONS["radius_px"], (0.1, 500.0)),
            ("radius_display_factor", lux.DIALOG_DOUBLE,
             "Radius display factor (1350 observed -- panel mm / value written):",
             DEFAULT_OPTIONS["radius_display_factor"], (0.0001, 100000.0)),
            ("name_filter", lux.DIALOG_TEXT,
             "Only parts whose name contains ('all' = no filter):",
             DEFAULT_OPTIONS["name_filter"]),
        ]
        got = lux.getInputDialog(title="Mask Viewer " + VIEWER_REV,
                                 desc="Look at ONE node. White = 1.0, black = 0.0.",
                                 values=values)
        if not got:
            print("[info] dialog cancelled -- using defaults")
            return dict(DEFAULT_OPTIONS)
        print("[info] dialog returned: {0}".format(got))
        opts = dict(DEFAULT_OPTIONS)
        opts.update(got)
        return opts
    except Exception as e:
        print("[warn] the dialog raised ({0}) -- continuing on defaults".format(e))
        return dict(DEFAULT_OPTIONS)


def make_readout_base(graph):
                                                                          
                                                                            
    for attr in ("SHADER_TYPE_DIFFUSE", "SHADER_TYPE_FLAT", "SHADER_TYPE_PLASTIC",
                 "SHADER_TYPE_PAINT"):
        node = try_new_node(graph, attr, "Readout base")
        if node is not None:
            print("  readout base: {0}".format(attr))
            return node, attr
    return None, None


def build_pattern(graph, shader_attr, label, scale):
                                                  

                                                                                 
                                                                                 
                                                                          
                                                                           
                                                                                 
                                                                            
    if scale is None or scale <= 0.0:
        print("  [REFUSED] {0} not built: no usable texture Scale. Everything "
              "downstream of it is missing from this frame by design, so do not "
              "read the frame as a result.".format(label))
        return None
    node = try_new_node(graph, shader_attr, label)
    if node is None:
        return None
    set_display(node, ["scale"], scale)
    set_center_on_part(node)
    return node


def resolve_mode(opts):
                                                                                
                                                                             
                                                                              
                         
    raw = opts.get("mode_int", 1)
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else 1
    try:
        idx = int(float(raw))
    except (TypeError, ValueError):
        print("[warn] mode {0!r} not understood -- using mode 1".format(raw))
        idx = 1
    if not (1 <= idx <= len(MODE_ORDER)):
        print("[warn] mode {0} out of range -- using mode 1".format(idx))
        idx = 1
    return MODE_ORDER[idx - 1]


def run():
    perf_on = check_performance_mode()
    opts = read_options()
    mode = resolve_mode(opts)
    raw_filter = opts.get("name_filter")
    if isinstance(raw_filter, str) and raw_filter.strip().lower() in NO_FILTER_WORDS:
        raw_filter = ""
    name_filter = resolve_filter(raw_filter)

    print("")
    print("=== MASK VIEWER {0} -- {1} ===".format(VIEWER_REV, mode))

    extent, source, units_to_mm = resolve_part_size(opts, name_filter)
    SCENE_MM_PER_UNIT_LIVE[0] = units_to_mm
    if extent <= 0.0:
        extent = 100.0
                                                                              
                                                                                 
    radius_mm = as_float(opts.get("radius_mm"), 1.5)
                                                                              
                                                                                  
                                                                               
                                                                               
                                                  
    PART_MM_LIVE[0] = resolve_part_mm({
        "part_size_mm": opts.get("part_size_mm"),
        "part_extent_scene": extent,
        "units_to_mm": units_to_mm,
    })
    if PART_MM_LIVE[0] > 0.0:
        print("  part measures {0} mm -- radii are checked against it".format(
            round(PART_MM_LIVE[0], 4)))
                                                                                  
                                                                   
    factor = resolve_scale_factor(opts.get("scale_factor"))
    frac = as_float(opts.get("texture_scale_fraction"), 0.05)
    scale = texture_scale_or_refuse(extent, frac, factor, "mask viewer pattern")
    set_center_on_override(opts.get("center_on_int"))
    in_pixels = bool(opts.get("radius_in_pixels", True))
    radius_px = as_float(opts.get("radius_px"), 4.0)
    fac = as_float(opts.get("radius_display_factor"), RADIUS_DISPLAY_FACTOR)
    RADIUS_DISPLAY_FACTOR_LIVE[0] = fac if fac > 0.0 else RADIUS_DISPLAY_FACTOR
                                                                           
                                                                            
                                                         
    raw_cutoff = as_float(opts.get("cutoff"), -1.0)
    cutoff = None if raw_cutoff < 0.0 else raw_cutoff

    print("  part extent {0} scene units ({1})".format(extent, source))
                                                                              
                                                                                 
                                                                           
                                                              
    if scale is None:
        print("  radius {0} mm requested | texture scale REFUSED, no pattern node "
              "will be built this run".format(radius_mm))
    else:
        print("  radius {0} mm requested | texture scale {1} (panel should read "
              "{2} mm)".format(radius_mm, scale,
                               round(texture_scale_to_mm(scale), 5)))

    name = "MASKVIEW-" + str(mode)[:1] + "-" + random_suffix()
    try:
        lux.createSceneMaterial(name)
    except Exception as e:
        print("[warn] createSceneMaterial: {0}".format(e))
    try:
        graph = lux.getMaterialGraph(name)
    except Exception as e:
        print("[error] no material graph ({0}) -- cannot continue".format(e))
        return
    try:
        root = graph.getRoot()
    except Exception as e:
        print("[error] no graph root ({0}) -- cannot continue".format(e))
        return

    base, base_attr = make_readout_base(graph)
    if base is None:
        print("[error] could not create any readout shader -- cannot continue")
        return
    surface = find_param(root, ["surface"])
    if surface is not None:
        safe_edge(graph, source=base, target=root, param=surface.getName(),
                  label="readout base -> root.surface")

    driver = None

    if mode == MODE_CURVATURE:
        driver = add_curvature_mask(graph, radius_mm, in_pixels, radius_px)
        if driver is not None:
            if cutoff is not None:
                set_display(driver, ["cutoff"], cutoff)
        dump_node(driver, "Curvature")

    elif mode == MODE_OCCLUSION:
        driver = add_occlusion_mask(graph, radius_mm, in_pixels, radius_px)
        dump_node(driver, "Occlusion")

    elif mode == MODE_SCRATCHES:
        driver = build_pattern(graph, "SHADER_TYPE_SCRATCHES", "Scratches", scale)
        if driver is not None:
            set_display(driver, ["inside_color", "color"], (1.0, 1.0, 1.0),
                        ptype=PT_COLOR)
            set_display(driver, ["outside_color", "background"], (0.0, 0.0, 0.0),
                        ptype=PT_COLOR)
        dump_node(driver, "Scratches")

    elif mode == MODE_SPOTS:
        driver = build_pattern(graph, "SHADER_TYPE_SPOTS", "Spots", scale)
        if driver is not None:
            set_display(driver, ["inside_color", "color"], (1.0, 1.0, 1.0),
                        ptype=PT_COLOR)
            set_display(driver, ["outside_color", "background"], (0.0, 0.0, 0.0),
                        ptype=PT_COLOR)
        dump_node(driver, "Spots")

    elif mode == MODE_MASKED:
        driver = build_pattern(graph, "SHADER_TYPE_SCRATCHES", "Scratches", scale)
        curv = add_curvature_mask(graph, radius_mm, in_pixels, radius_px)
        if curv is not None:
            if cutoff is not None:
                set_display(curv, ["cutoff"], cutoff)
        if driver is not None and curv is not None:
            inside = find_param(driver, ["inside_color", "color"])
            if inside is None:
                print("  [warn] no colour slot on Scratches -- cannot mask")
            elif safe_edge(graph, source=curv, target=driver,
                           param=inside.getName(),
                           label="curvature -> scratches." + inside.getName()):
                set_display(driver, ["outside_color", "background"],
                            (0.0, 0.0, 0.0), ptype=PT_COLOR)
                print("  masked texture wired: white scratches only where "
                      "curvature is white")
            else:
                print("  [warn] the colour slot REFUSED the curvature edge -- "
                      "this is the AB13 route and it did not take")
        dump_node(driver, "Scratches (masked)")

    elif mode == MODE_COMPOSITE:
        comp = try_new_node(graph, "SHADER_TYPE_COLOR_COMPOSITE", "Gate test")
        curv = add_curvature_mask(graph, radius_mm, in_pixels, radius_px)
        if curv is not None:
            if cutoff is not None:
                set_display(curv, ["cutoff"], cutoff)
        if comp is not None:
            src_name, bg_name = _composite_inputs(comp)
            print("  composite inputs resolved: source='{0}' background='{1}'".format(
                src_name, bg_name))
            red = _make_colour_node(graph, GATE_SOURCE_COLOUR)
            green = _make_colour_node(graph, GATE_BACKGROUND_COLOUR)
            if red is not None and src_name:
                safe_edge(graph, source=red, target=comp, param=src_name,
                          label="RED -> " + src_name)
            if green is not None and bg_name:
                safe_edge(graph, source=green, target=comp, param=bg_name,
                          label="GREEN -> " + bg_name)
            mp = find_param(comp, ["clipping_mask", "clipping mask", "mask"])
            if mp is not None and curv is not None:
                safe_edge(graph, source=curv, target=comp, param=mp.getName(),
                          label="curvature -> " + mp.getName())
            print("  READ IT LIKE THIS: red on the edges and green elsewhere means")
            print("  the clipping mask GATES. Any uniform colour, or a blend of the")
            print("  two, means it does NOT -- and no blend-mode int will fix that.")
        dump_node(comp, "Composite (gate test)")
        driver = comp

    elif mode == MODE_WEAR:
                                                                           
                                                                           
                                                                             
                          
        curv = add_curvature_mask(graph, radius_mm, in_pixels, radius_px, cutoff)
        grunge = build_pattern(graph, "SHADER_TYPE_SCRATCHES", "Scratches (grunge)", scale)
        if grunge is not None:
            set_display(grunge, ["inside_color", "color"], (1.0, 1.0, 1.0), ptype=PT_COLOR)
            set_display(grunge, ["outside_color", "background"], (0.0, 0.0, 0.0), ptype=PT_COLOR)
        occ = add_occlusion_mask(graph, radius_mm, False, radius_px)
        g_amt = as_float(opts.get("grunge_amount"), 0.5)
        a_amt = as_float(opts.get("ao_amount"), 0.5)
        contrast = opts.get("wear_contrast")
        contrast = as_float(contrast, 0.0) if contrast is not None else 0.0
        driver = build_wear_mask(graph, curvature=curv, grunge=grunge,
                                 occlusion=occ, grunge_amount=g_amt,
                                 ao_amount=a_amt,
                                 contrast=(contrast if contrast > 0.0 else None))
        print("")
        print("  MODE 7 SETTINGS: radius {0} mm, pixels {1}, cutoff {2}, "
              "grunge {3}, AO {4}, contrast {5}".format(
                  radius_mm, in_pixels, cutoff, g_amt, a_amt, contrast))
        if in_pixels:
            print("  [warn] Radius In Pixels is ON, so the radius is a "
                  "SCREEN-SPACE band at {0} px, not {1} mm. On a large "
                  "render that is a hairline and it vanishes as soon as "
                  "anything multiplies it. Turn it OFF to judge this "
                  "mask.".format(radius_px, radius_mm))
        print("")
        print("  READ IT LIKE THIS. White is where wear will go.")
        print("  - Edges and rims white, flats black -> the primary signal is right.")
        print("  - Set grunge amount 0 and rerun: the mask must become CLEANER,")
        print("    not black. Black at 0 means the composition is still an")
        print("    intersection and this rebuild did not take.")
        print("  - Crevices should get DARKER as AO amount rises. If they get")
        print("    brighter the invert did not land and AO is adding wear.")
        dump_node(driver, "Wear mask (composed)")

    elif mode == MODE_CALIBRATE:
                                                                               
                                                                                 
                                                                                 
                                                                                
                                                                          
        curv = add_curvature_mask(graph, None, False, radius_px)
        if curv is not None:
            pix = find_param(curv, ["radius in pixels", "adaptive_radius",
                                    "adaptive radius"])
            if pix is not None:
                set_display(curv, [pix.getDisplayName()], False)
            else:
                print("  [info] no 'Radius In Pixels' toggle on this node")
            set_display(curv, ["radius"], 1.0)
                                                                                
                                                                                 
                                                                                  
                                                                                 
                                                                         
        tex = build_pattern(graph, "SHADER_TYPE_SCRATCHES",
                            "Scratches (calibration)", 1.0)
        driver = curv if curv is not None else tex
        occ_cal = add_occlusion_mask(graph, None, False, radius_px)
        if occ_cal is not None:
            set_display(occ_cal, ["radius"], 1.0)
        print("")
        print("  CALIBRATION. Exactly 1.0 has been written to ALL THREE:")
        print("    the Curvature node's Radius   (Radius In Pixels OFF)")
        print("    the Scratches node's Scale")
        print("    the Occlusion node's Radius   (no pixels toggle on that node)")
        print("  Open both nodes in the material graph and read the two panel")
        print("  numbers. EACH PANEL NUMBER IS THAT FACTOR FOR THIS SCENE:")
        print("    Radius panel reads R  ->  radius_display_factor = R")
        print("    Scale  panel reads S  ->  texture scale factor   = 1/S")
        print("  Enter them in this scene's dialog and everything downstream is")
        print("  right for this scene instead of for the discharge body.")
        print("")
        print("  AND THE QUESTION BEHIND THE QUESTION (RNK-0275): are they two")
        print("  constants or one conversion? This scene measures")
        print("    mm per scene unit = {0}".format(round(units_to_mm, 6)))
        print("    part extent       = {0} scene units ({1})".format(extent, source))
        print("  If the Radius panel number comes back close to that mm-per-unit")
        print("  figure, the radius was never a separate constant: it is the")
        print("  scene's own unit conversion, both factors collapse into one")
        print("  runtime measurement, and a whole class of error retires.")
        print("  SETTLED 2026-08-03 for Curvature and Scale: BOTH panels read")
        print("  1000. It is not a scene property at all -- the API takes METRES")
        print("  and the panel shows MILLIMETRES, one convention, every scene.")
        print("  The old 1350 was simply wrong, and cost a 0.74x error on every")
        print("  radius written since 2026-07-30.")
        print("")
                                                                           
                                                                             
                                                                              
                                                                               
                                                                              
                                                                 
        print("  OCCLUSION IS SETTLED TOO, and it is now READ THREE TIMES:")
        print("  1000 on 2026-08-03 (the run that retired the scene-units")
        print("  reading) and 1000 again at ladder R0 on 2026-08-05. It has no")
        print("  pixels toggle and it obeys the same metres-to-millimetres rule")
        print("  as everything else. mm_to_scene has no part in any radius.")
        print("")
        print("  SO ALL THREE PANELS ARE EXPECTED TO READ 1000 HERE. This mode")
        print("  is now a REGRESSION CHECK, not an open question: if any panel")
        print("  comes back as something else, that is a new finding about THIS")
        print("  scene and it outranks everything downstream of it.")
        print("  For reference, if a factor ever did track the scene, this one")
        print("  would read about {0}.".format(
            "{0:.6g}".format(1.0 * (units_to_mm or 0.0))))
        dump_node(curv, "Curvature (calibration, radius written 1.0)")
        dump_node(tex, "Scratches (calibration, scale written 1.0)")
        dump_node(occ_cal, "Occlusion (calibration, radius written 1.0)")

    elif mode == MODE_FLAT:
                                                                          
                                                                                
                                                                              
                                                                                 
                                                                            
         
                                                                                
                                                                               
                                                             
                                                                               
                                            
                                                                                
                                                                                
                                                                                
                                                                        
                                                                             
                                                                         
                                                                             
                                        
        set_display(base, ["color", "colour", "diffuse"], FLAT_TEST_COLOUR)
        dump_node(base, "Readout base (flat colour, no nodes)")
        print("")
        print("  FLAT COLOUR NULL TEST -- ladder R1. The graph contains ONE node")
        print("  and no masks, no textures, no radius and no scale. Nothing here")
        print("  can render dark for an interesting reason.")
        print("")
        print("  READ IT LIKE THIS:")
        print("    The part is MAGENTA          -> the apply path reaches the")
        print("      surface you are judging. Every later frame is at least")
        print("      ABOUT the material, and R2 and R3 are worth running.")
        print("    Some or all of it is NOT     -> ladder W6 is the whole story.")
        print("      The skipped nodes are the visible ones and every frame of")
        print("      the past week has been of geometry that never received a")
        print("      material. Nothing above this rung means anything until it")
        print("      is fixed.")
        print("    PART of it is magenta        -> say WHICH part. That is the")
        print("      most useful answer of the three, because it names the")
        print("      geometry the apply is missing.")

    if mode == MODE_FLAT:
                                                                               
                                                              
        wire_audit(base, "readout base")
        applied = apply_material_to_parts(name, name_filter)
        print("  applied to {0} node(s)".format(applied))
        print("")
        print("NOW RENDER IT. This frame answers exactly one question: does the")
        print("material reach the geometry you are looking at.")
        if perf_on:
            print("")
            print("REMINDER: PERFORMANCE MODE WAS ON FOR THIS RUN. It does not")
            print("void THIS rung -- a flat colour survives Performance Mode,")
            print("which is precisely why it is the rung that runs first -- but")
            print("turn it off before believing any mask above it.")
        return

    if driver is None:
        print("[error] the node for this mode could not be created -- nothing to show")
        return

    colour_param = find_param(base, ["color", "colour", "diffuse"])
    if colour_param is None:
        print("[error] no colour input on the readout base")
        return
    if safe_edge(graph, source=driver, target=base, param=colour_param.getName(),
                 label="driver -> readout base colour"):
                                                                              
                                                                              
                                                                           
                                                                               
                                                                              
        pass
    else:
        print("[error] the driver could NOT reach base colour. On this shader "
              "({0}) the colour input refused a texture edge -- which would also "
              "explain the paint generator, and is the single most important "
              "thing in this log.".format(base_attr))
        return

    wire_audit(base, "readout base")
    applied = apply_material_to_parts(name, name_filter)
    print("  applied to {0} node(s)".format(applied))
    print("")
    print("NOW RENDER IT. White = the node outputs 1.0 there, black = 0.0.")
    if perf_on:
        print("")
        print("REMINDER: PERFORMANCE MODE WAS ON FOR THIS RUN. Every "
              "mask above is void -- turn it off and run again.")
    print("If the whole part is one flat tone, that node is not varying across")
    print("the surface, and everything built on top of it cannot vary either.")


run()
