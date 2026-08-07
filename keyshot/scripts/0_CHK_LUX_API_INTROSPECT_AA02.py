# -*- coding: utf-8 -*-
# AUTHOR claude-opus
# REV AA02
# HEADLESS COMPLIANT
# lux API introspection: lists dir() on the lux module and on live
# graph/node/parameter objects instead of probing guessed names.
#
# Settles three things:
#   1. ENUM LABELS -- 'Center On' (texture_space) and Color Composite
#      'Blend Mode' are type-2 int enums; every int 0..15 is accepted, so a
#      value sticking proves nothing about its meaning. R3 sweeps safe
#      getters on type-2 parameter objects looking for a label accessor.
#   2. MATERIAL VISIBILITY -- createSceneMaterial() does not raise and
#      getMaterialGraph() returns a usable graph, but nothing appears in the
#      scene. R4 lists which scene/material/apply accessors actually exist.
#   3. BOUNDING-BOX API -- R5 dumps a real scene object's method list to find
#      the correct bbox call by name instead of guessing.
#
# SAFETY: zero-arg getters are called only on graph/node/parameter/scene
# objects, never on the lux module itself (a module-level get... could open
# a file dialog and hang the console). Module contents are listed, not called.
#
# KEYSHOT PYTHON CONSTRAINT: no f-strings, ASCII only (embedded interpreter
# is < 3.6 and ASCII-sensitive).

import lux

SCRATCH_NAME = "LUX_INTROSPECT_PROBE"

# Zero-arg getters are called on OBJECTS only (never the module). Anything whose
# name suggests a dialog or a write is skipped even so.
SAFE_GETTER_PREFIXES = ("get", "is", "has", "num", "count", "to")
NEVER_CALL = (
    "getfile", "getopenfile", "getsavefile", "getdirectory", "getfolder",
    "getinput", "getstring", "getvalueinput", "getdialog", "getpassword",
    "getscenetreeselection",
)


def hr(title):
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def sub(title):
    print("")
    print("  --- " + title + " ---")


def short(v, n=220):
    try:
        s = repr(v)
    except Exception:
        s = "<unreprable>"
    if len(s) > n:
        s = s[:n] + " ...(+" + str(len(s) - n) + " chars)"
    return s


def list_module(mod, label):
    """List a module's contents WITHOUT calling anything."""
    hr(label)
    names = []
    try:
        names = dir(mod)
    except Exception as e:
        print("  dir() failed: " + str(e))
        return
    consts_shader = []
    consts_param = []
    consts_other = []
    funcs = []
    classes = []
    for nm in names:
        if nm.startswith("_"):
            continue
        try:
            v = getattr(mod, nm)
        except Exception:
            consts_other.append((nm, "<unreadable>"))
            continue
        if callable(v):
            # crude class-vs-function split: classes are usually capitalised
            (classes if nm[:1].isupper() else funcs).append(nm)
        elif nm.startswith("SHADER_TYPE"):
            consts_shader.append((nm, v))
        elif nm.startswith("PARAMETER_TYPE") or nm.startswith("PARAM"):
            consts_param.append((nm, v))
        else:
            consts_other.append((nm, v))

    sub("CALLABLES -- functions (" + str(len(funcs)) + ")")
    for nm in funcs:
        print("      " + nm + "()")
    sub("CALLABLES -- classes / constructors (" + str(len(classes)) + ")")
    for nm in classes:
        print("      " + nm)
    sub("PARAMETER_TYPE constants (" + str(len(consts_param)) + ")")
    for nm, v in consts_param:
        print("      " + nm.ljust(34) + " = " + short(v, 60))
    sub("SHADER_TYPE constants (" + str(len(consts_shader)) + ")")
    for nm, v in consts_shader:
        print("      " + nm.ljust(40) + " = " + short(v, 60))
    sub("OTHER module attributes (" + str(len(consts_other)) + ")")
    for nm, v in consts_other:
        print("      " + nm.ljust(34) + " = " + short(v, 60))


def list_object(obj, label):
    """List an object's attributes, splitting callables from values."""
    sub(label + "  ->  " + short(obj, 90))
    try:
        names = dir(obj)
    except Exception as e:
        print("      dir() failed: " + str(e))
        return []
    meths = []
    for nm in names:
        if nm.startswith("_"):
            continue
        try:
            v = getattr(obj, nm)
        except Exception:
            print("      " + nm.ljust(30) + " <unreadable>")
            continue
        if callable(v):
            meths.append(nm)
        else:
            print("      " + nm.ljust(30) + " = " + short(v, 90))
    print("      methods: " + (", ".join(meths) if meths else "(none)"))
    return meths


def call_safe_getters(obj, label):
    """Call zero-arg getters on an OBJECT and print what comes back.

    This is how an unguessed enum-label accessor gets found -- we do not need to
    know its name, only that it takes no arguments and starts with get/is/has.
    """
    sub("safe zero-arg getters on " + label)
    hits = 0
    try:
        names = dir(obj)
    except Exception:
        print("      dir() failed")
        return
    for nm in names:
        if nm.startswith("_"):
            continue
        low = nm.lower()
        if not low.startswith(SAFE_GETTER_PREFIXES):
            continue
        if low in NEVER_CALL:
            print("      " + nm + "() -> SKIPPED (denylist: may open a dialog)")
            continue
        try:
            fn = getattr(obj, nm)
        except Exception:
            continue
        if not callable(fn):
            continue
        try:
            v = fn()
        except Exception as e:
            print("      " + nm + "() -> raised: " + str(e)[:90])
            continue
        hits += 1
        print("      " + nm + "() -> " + short(v))
    if hits == 0:
        print("      (no zero-arg getter returned a value)")


# --------------------------------------------------------------------------
# R1  the lux module itself
# --------------------------------------------------------------------------

def r1_module():
    list_module(lux, "R1  dir(lux) -- the whole module surface, listed not called")
    try:
        import luxmath
        list_module(luxmath, "R1b  dir(luxmath)")
    except Exception as e:
        print("")
        print("  luxmath not importable here: " + str(e))


# --------------------------------------------------------------------------
# R2 / R3  graph, node and parameter objects -- and the enum-label hunt
# --------------------------------------------------------------------------

def r2_graph_and_nodes():
    hr("R2  Live graph / node / parameter objects")
    try:
        lux.createSceneMaterial(SCRATCH_NAME)
    except Exception as e:
        print("  createSceneMaterial note: " + str(e))
    graph = None
    try:
        graph = lux.getMaterialGraph(SCRATCH_NAME)
    except Exception as e:
        print("  getMaterialGraph FAILED: " + str(e))
        return None, None
    list_object(graph, "MaterialGraph")
    call_safe_getters(graph, "MaterialGraph")

    root = None
    try:
        root = graph.getRoot()
        list_object(root, "Root node")
        call_safe_getters(root, "Root node")
    except Exception as e:
        print("  getRoot failed: " + str(e))

    node = None
    st = getattr(lux, "SHADER_TYPE_SCRATCHES", None)
    if st is not None:
        try:
            node = graph.newNode(st)
            list_object(node, "Scratches node")
            call_safe_getters(node, "Scratches node")
        except Exception as e:
            print("  newNode(SCRATCHES) failed: " + str(e))
    return graph, node


def r3_enum_labels(node):
    hr("R3  ENUM LABELS -- can a type-2 parameter name its own options?")
    print("  Center On + Blend Mode are int enums that accept ANY int, so the value")
    print("  we set proves nothing. The probe material never appears in the scene, so")
    print("  reading the dropdown is not an option. If a label accessor exists under")
    print("  a name we have not guessed, the getter sweep below will surface it.")
    if node is None:
        print("  no node available -- skipping")
        return
    targets = []
    try:
        for p in node.getParameters():
            if p.getType() == 2:
                targets.append(p)
    except Exception as e:
        print("  getParameters failed: " + str(e))
        return
    if not targets:
        print("  no type-2 parameters on this node")
        return
    for p in targets[:3]:
        try:
            nm = p.getName()
            dn = p.getDisplayName()
        except Exception:
            nm, dn = "?", "?"
        sub("type-2 param " + repr(nm) + " (display " + repr(dn) + ")")
        list_object(p, "parameter object")
        call_safe_getters(p, "parameter " + repr(nm))

    # A type-14 (texturable) and a type-9 (image) parameter for comparison --
    # different types may expose different accessors.
    for want in (14, 9, 13):
        try:
            for p in node.getParameters():
                if p.getType() == want:
                    sub("type-" + str(want) + " param " + repr(p.getName()) + " for comparison")
                    list_object(p, "parameter object")
                    break
        except Exception:
            pass


# --------------------------------------------------------------------------
# R4  why does the scene material never appear?
# --------------------------------------------------------------------------

SCENE_ACCESSORS = [
    "getSceneTree", "getScene", "getSceneRoot", "getObjects", "getSceneObjects",
    "getModels", "getActiveModel", "getParts", "getGeometry", "getRootNode",
]
MATERIAL_ACCESSORS = [
    "getSceneMaterials", "getMaterials", "getMaterialNames", "getSceneMaterialNames",
    "getLibraryMaterials", "getMaterial", "getActiveMaterial",
]
APPLY_CANDIDATES = [
    "applyMaterial", "setMaterial", "assignMaterial", "setObjectMaterial",
    "applySceneMaterial", "setNodeMaterial",
]


def r4_material_visibility():
    hr("R4  The material that never appears -- what accessors actually exist?")
    print("  createSceneMaterial() does not raise and getMaterialGraph() returns a")
    print("  working graph, but the material is not visible in the scene even with")
    print("  geometry present. Below: which of these names are REAL on this build.")

    sub("scene accessors")
    scene_obj = None
    for nm in SCENE_ACCESSORS:
        fn = getattr(lux, nm, None)
        if fn is None:
            print("      [absent]  lux." + nm)
            continue
        try:
            v = fn()
            print("      [OK]      lux." + nm + "() -> " + short(v, 160))
            if scene_obj is None and v:
                scene_obj = v
        except Exception as e:
            print("      [raised]  lux." + nm + "(): " + str(e)[:90])

    sub("material accessors")
    for nm in MATERIAL_ACCESSORS:
        fn = getattr(lux, nm, None)
        if fn is None:
            print("      [absent]  lux." + nm)
            continue
        try:
            print("      [OK]      lux." + nm + "() -> " + short(fn(), 200))
        except Exception as e:
            print("      [raised]  lux." + nm + "(): " + str(e)[:90])

    sub("apply candidates (existence only -- NOT called)")
    for nm in APPLY_CANDIDATES:
        print("      " + ("[PRESENT] " if getattr(lux, nm, None) is not None else "[absent]  ") + "lux." + nm)

    return scene_obj


# --------------------------------------------------------------------------
# R5  the bounding-box API (part-size resolution)
# --------------------------------------------------------------------------

def r5_scene_object(scene_obj):
    hr("R5  A real scene object -- the bounding-box API for part sizing")
    print("  resolve_part_size() in the material generator tries a list of guessed")
    print("  bbox method names and silently falls back to a hardcoded 50 mm when they")
    print("  all miss. Put a part in the scene before running this so there is")
    print("  something real to inspect.")
    if not scene_obj:
        print("  no scene object captured in R4 -- is there geometry in the scene?")
        return
    obj = scene_obj
    # Walk into the first child if we were handed a container.
    for _ in range(3):
        try:
            kids = obj.getChildren()
        except Exception:
            break
        if not kids:
            break
        obj = kids[0]
    meths = list_object(obj, "scene object (walked to a leaf where possible)")
    call_safe_getters(obj, "scene object")
    bbox_like = [m for m in meths if "bound" in m.lower() or "bbox" in m.lower()
                 or "size" in m.lower() or "extent" in m.lower()]
    sub("bbox-looking methods")
    print("      " + (", ".join(bbox_like) if bbox_like else "(none found -- see the full method list above)"))


def main():
    hr("lux API INTROSPECTION  REV AA02 -- read the API, stop guessing")
    print("Creates a scratch material '" + SCRATCH_NAME + "'. Put a part in the")
    print("scene first so R5 has real geometry to measure.")
    try:
        r1_module()
    except Exception as e:
        print("R1 CRASHED: " + str(e))
    graph, node = (None, None)
    try:
        graph, node = r2_graph_and_nodes()
    except Exception as e:
        print("R2 CRASHED: " + str(e))
    try:
        r3_enum_labels(node)
    except Exception as e:
        print("R3 CRASHED: " + str(e))
    scene_obj = None
    try:
        scene_obj = r4_material_visibility()
    except Exception as e:
        print("R4 CRASHED: " + str(e))
    try:
        r5_scene_object(scene_obj)
    except Exception as e:
        print("R5 CRASHED: " + str(e))

    hr("DONE -- paste the whole log back")
    print("Looking for, in order of value:")
    print("  1. a parameter method that names enum options (unblocks Center On +")
    print("     Blend Mode, which cannot be read any other way right now)")
    print("  2. the real material-apply / scene-material call (explains the")
    print("     invisible material, and whether the generator's auto-apply works)")
    print("  3. the real bounding-box call (unblocks part-size resolution)")
    print("Remember to delete '" + SCRATCH_NAME + "' if it turns out to be visible.")


if __name__ == "__main__":
    main()
