                       
                                   
          
                    
                                                                        
                                                                        
                                                                          
                                                                             
                                                                     
                                                                         
                                                                          
                                                             
 
                                                                          
                                                                         
                                                                         
                                                                          
                                                                    
 
                                                                           
                                                                           
                                                                       
                                                                           
                                                                          
                     
 
                                                        
                                                                                 
                                                                            
                                                                                 

import lux

try:
    import luxmath
except Exception:
    luxmath = None

SCRATCH_NAME = "TEXTURE_TRANSFORM_PROBE"

                                                                         
                                                                               
TILING_NODES = [
    "SHADER_TYPE_SCRATCHES",
    "SHADER_TYPE_NOISE_TEXTURE",
    "SHADER_TYPE_NOISE_FRACTAL",
    "SHADER_TYPE_CELLULAR",
]

RESULTS = []                             


                                                                            
                                                                        
                                                                           
                                                                            

def hr(title):
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def record(pid, verdict, note=""):
    RESULTS.append((pid, verdict, note))
    print("  >> " + pid + ": " + verdict + ((" -- " + note) if note else ""))


def params_of(node):
    try:
        return list(node.getParameters())
    except Exception:
        return []


def shader(attr):
    return getattr(lux, attr, None)


def make(graph, attr, label=""):
    st = shader(attr)
    if st is None:
        print("  [MISSING] lux." + attr + " -- not on this build")
        return None
    try:
        n = graph.newNode(st)
        print("  [created] " + attr + ((" (" + label + ")") if label else ""))
        return n
    except Exception as e:
        print("  [create FAILED] " + attr + ": " + str(e))
        return None


def find_param(node, needle):
                                                                     
    needle = needle.lower()
    ps = params_of(node)
    for p in ps:
        try:
            if p.getName().lower() == needle or p.getDisplayName().lower() == needle:
                return p
        except Exception:
            pass
    for p in ps:
        try:
            if needle in p.getName().lower() or needle in p.getDisplayName().lower():
                return p
        except Exception:
            pass
    return None


def find_type(node, tnum, pure=None):
    for p in params_of(node):
        try:
            if p.getType() != tnum:
                continue
            if pure is not None and p.isPure() != pure:
                continue
            return p
        except Exception:
            pass
    return None


def describe(p, label):
    if p is None:
        print("  " + label + ": NONE FOUND")
        return
    try:
        print("  " + label + ": name=" + repr(p.getName()) +
              " display=" + repr(p.getDisplayName()) +
              " type=" + str(p.getType()) + " pure=" + str(p.isPure()))
    except Exception as e:
        print("  " + label + ": [unreadable] " + str(e))


def try_get(p, label):
                                                                      
                                                                      
                                                        
    try:
        v = p.getValue()
        print("  get " + label + " -> type=" + str(type(v)) + " value=" + repr(v))
        return v
    except Exception as e:
        print("  get " + label + " -> FAILED: " + str(e))
        return None


def try_set(p, value, label):
                                                              
    try:
        p.setValue(value)
    except Exception as e:
        print("  set " + label + " = " + repr(value) + " -> FAILED: " + str(e))
        return False
    try:
        back = p.getValue()
    except Exception:
        back = "?"
    print("  set " + label + " = " + repr(value) + " -> reads back " + repr(back))
    return True


                                                                            
        
                                                                            

def probe_1_luxmath_surface():
    hr("P1  luxmath module surface -- what matrix/vector types exist at all")
    if luxmath is None:
        record("P1", "NOT AVAILABLE", "import luxmath failed -- see traceback above")
        return
    names = [n for n in dir(luxmath) if not n.startswith("_")]
    print("  dir(luxmath) -> " + repr(names))
    for candidate in ["Matrix", "Mat4", "Mat4x4", "Mat3", "Mat3x3", "Vector", "Vec3", "Vec4"]:
        cls = getattr(luxmath, candidate, None)
        print("  luxmath." + candidate + " -> " + ("present" if cls is not None else "absent"))
    record("P1", "SEE DUMP", "names present = " + repr(names))


def probe_2_transform_param_census(graph):
    hr("P2  transform_obj_to_uv (type-12) census across every named tiling node")
    print("  Confirming the exact param name + untouched default PER NODE -- the")
    print("  generator comment (AB03) names these four as not moving; Spots is")
    print("  excluded on purpose, its variety is a different param ('seed').")
    found_nodes = {}
    for attr in TILING_NODES:
        n = make(graph, attr, "census")
        if n is None:
            record("P2:" + attr, "NOT AVAILABLE", "node type missing on this build")
            continue
        tp = find_param(n, "transform_obj_to_uv") or find_type(n, 12)
        describe(tp, attr + ".texture_transform")
        if tp is None:
            record("P2:" + attr, "NOT PRESENT", "no type-12 param found -- check full dump below")
            for p in params_of(n):
                try:
                    print("      name=" + repr(p.getName()) + " type=" + str(p.getType()))
                except Exception:
                    pass
            continue
        found_nodes[attr] = (n, tp)
        try_get(tp, attr + ".texture_transform (untouched default)")
        record("P2:" + attr, "PRESENT", "name=" + repr(tp.getName()))
    return found_nodes


def probe_3_write_shapes(node, param):
    hr("P3  Write-shape sweep on SHADER_TYPE_SCRATCHES.texture_transform")
    print("  Only run against ONE representative node to keep the log readable --")
    print("  if a shape works here, P2's census tells you the same param name/type")
    print("  exists on the other three, so it should transfer directly.")
    if param is None:
        record("P3", "SKIPPED", "no type-12 param found on Scratches in P2")
        return

                                                                     
    if luxmath is not None and hasattr(luxmath, "Matrix"):
        try:
            m = luxmath.Matrix()
            print("  luxmath.Matrix() -> " + repr(m))
            ok = try_set(param, m, "luxmath.Matrix() identity")
            record("P3a", "PASS" if ok else "FAIL", "luxmath.Matrix() identity object")
        except Exception as e:
            print("  luxmath.Matrix() construction FAILED: " + str(e))
            record("P3a", "INCONCLUSIVE", "could not construct luxmath.Matrix()")
    else:
        record("P3a", "SKIPPED", "no luxmath.Matrix on this build")

                                                                               
                                                                   
                                                                                
    if luxmath is not None and hasattr(luxmath, "Matrix"):
        try:
            m2 = luxmath.Matrix()
            translate_fn = getattr(m2, "translate", None)
            if translate_fn is not None:
                if luxmath is not None and hasattr(luxmath, "Vector"):
                    m2 = translate_fn(luxmath.Vector(0.25, 0.25, 0.0))
                else:
                    m2 = translate_fn((0.25, 0.25, 0.0))
                ok = try_set(param, m2, "luxmath.Matrix().translate(0.25,0.25,0)")
                record("P3a2", "PASS" if ok else "FAIL", "translated Matrix object")
            else:
                record("P3a2", "NOT AVAILABLE", "Matrix instance has no .translate")
        except Exception as e:
            print("  translate attempt FAILED: " + str(e))
            record("P3a2", "INCONCLUSIVE", str(e))
    else:
        record("P3a2", "SKIPPED", "no luxmath.Matrix on this build")

                                                              
    ident4 = [1.0, 0.0, 0.0, 0.0,
              0.0, 1.0, 0.0, 0.0,
              0.0, 0.0, 1.0, 0.0,
              0.0, 0.0, 0.0, 1.0]
    ok = try_set(param, ident4, "flat 16-float 4x4 identity (list)")
    record("P3b", "PASS" if ok else "FAIL", "flat list, 16 floats")

                                                             
    ident3 = [1.0, 0.0, 0.0,
              0.0, 1.0, 0.0,
              0.0, 0.0, 1.0]
    ok = try_set(param, ident3, "flat 9-float 3x3 identity (list)")
    record("P3c", "PASS" if ok else "FAIL", "flat list, 9 floats")

                                                      
    nested4 = [[1.0, 0.0, 0.0, 0.0],
               [0.0, 1.0, 0.0, 0.0],
               [0.0, 0.0, 1.0, 0.0],
               [0.0, 0.0, 0.0, 1.0]]
    ok = try_set(param, nested4, "nested 4x4 identity (list of rows)")
    record("P3d", "PASS" if ok else "FAIL", "nested list of 4 rows")

                                                                                    
    ok = try_set(param, tuple(ident4), "flat 16-float 4x4 identity (tuple)")
    record("P3e", "PASS" if ok else "FAIL", "flat tuple, 16 floats")


                                                                            
     
                                                                            

def main():
    hr("TEXTURE TRANSFORM PROBE  REV AA01  (RNK-0072 tier b)")
    print("Creating disposable material '" + SCRATCH_NAME + "' -- delete it when done.")
    try:
        lux.createSceneMaterial(SCRATCH_NAME)
    except Exception as e:
        print("createSceneMaterial note: " + str(e) + " (continuing -- may already exist)")
    graph = lux.getMaterialGraph(SCRATCH_NAME)

    try:
        probe_1_luxmath_surface()
    except Exception as e:
        record("P1", "CRASHED", str(e))

    found = {}
    try:
        found = probe_2_transform_param_census(graph) or {}
    except Exception as e:
        record("P2", "CRASHED", str(e))

    try:
        scr = found.get("SHADER_TYPE_SCRATCHES")
        if scr is not None:
            probe_3_write_shapes(scr[0], scr[1])
        else:
            hr("P3  SKIPPED -- Scratches had no type-12 param in P2")
            record("P3", "SKIPPED", "see P2:SHADER_TYPE_SCRATCHES")
    except Exception as e:
        record("P3", "CRASHED", str(e))

    hr("SUMMARY  (paste this whole log back for RNK-0072)")
    for pid, verdict, note in RESULTS:
        print("  " + pid.ljust(24) + " " + verdict + ((" -- " + note) if note else ""))
    print("")
    print("NEXT STEP if any P3 candidate PASSes: wire it into")
    print("1_HLP_MAT_GENERATOR's placement-jitter block (AB03 section) as a real")
    print("per-part transform, THEN RENDER A FRAME on a multi-part scene --")
    print("only a render proves the UV actually shifted, an accepted setValue")
    print("only proves the API took the write.")
    print("")
    print("Done. Remember to delete the '" + SCRATCH_NAME + "' material from the scene.")


if __name__ == "__main__":
    main()
