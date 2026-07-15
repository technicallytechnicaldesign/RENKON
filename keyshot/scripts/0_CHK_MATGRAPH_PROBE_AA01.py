# -*- coding: utf-8 -*-
# AUTHOR claude-opus
# REV AA01
# HEADLESS COMPLIANT
# Material-graph capability PROBE PACK -- a throwaway diagnostic. Builds ONE
# disposable scene material ('MATGRAPH_PROBE') and runs the 13 probes from
# MATERIAL_DIVERSITY_DESIGN.md (MDD-4B7A9F) section 8, printing PASS / FAIL /
# MISSING + parameter dumps for each, so the design's assumptions become ground
# truth. It does NOT touch your geometry; it only creates that one scratch
# material -- delete it afterwards. Run in the KeyShot Scripting Console (a few
# probes -- labels, displace, film sweep -- also want a rendered frame to judge
# by eye; the script reports whether the GRAPH operation succeeded).
#
# !! KEYSHOT PYTHON CONSTRAINT -- READ BEFORE EDITING !!
# f-string-FREE + ASCII-ONLY (embedded interpreter is < 3.6 and ASCII-sensitive).
# Every lux constant is getattr-guarded; every probe is wrapped so one failure
# never stops the rest. Paste the whole console output back for a Rev-2 of the
# design doc.

import lux

SCRATCH_NAME = "MATGRAPH_PROBE"
RESULTS = []  # (probe id, verdict, note)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def hr(title):
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def record(pid, verdict, note=""):
    RESULTS.append((pid, verdict, note))
    print("  >> " + pid + ": " + verdict + ((" -- " + note) if note else ""))


def dump(node, label=""):
    try:
        nm = label or node.getType()
    except Exception:
        nm = label or "?"
    print("  --- " + str(nm) + " ---")
    try:
        for p in node.getParameters():
            print("      name={0:<26} display={1:<26} type={2} pure={3}".format(
                repr(p.getName()), repr(p.getDisplayName()), p.getType(), p.isPure()))
    except Exception as e:
        print("      [could not list params] " + str(e))


def shader(attr):
    return getattr(lux, attr, None)


def make(graph, attr, label=""):
    """Create a node by SHADER_TYPE attr name; report + return it (or None)."""
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
    try:
        for p in node.getParameters():
            if needle in p.getDisplayName().lower() or needle in p.getName().lower():
                return p
    except Exception:
        pass
    return None


def find_type(node, tnum):
    try:
        for p in node.getParameters():
            if p.getType() == tnum:
                return p
    except Exception:
        pass
    return None


def try_edge(graph, source, target, param_name, label):
    """Attempt an edge; verify it landed via getInputEdge if available."""
    try:
        graph.newEdge(source=source, target=target, param=param_name)
    except Exception as e:
        print("  edge " + label + " -> RAISED: " + str(e))
        return False
    # verify it actually landed (the bump_height bug was a silent no-op)
    try:
        e = target.getInputEdge(param_name)
        landed = e is not None
        print("  edge " + label + " -> " + ("LANDED (verified)" if landed else "silent no-op (getInputEdge empty)"))
        return landed
    except Exception:
        print("  edge " + label + " -> accepted (getInputEdge not available to verify)")
        return True


# --------------------------------------------------------------------------
# Probes
# --------------------------------------------------------------------------

def probe_1_label(graph, root):
    hr("P1  Root SHADERLABEL slot -> chip-through / rust-over-paint (HIGHEST VALUE)")
    dump(root, "Root")
    lp = find_type(root, 65538)
    if lp is None:
        record("P1", "NOT AVAILABLE", "no type-65538 (SHADERLABEL) param on root")
        return
    print("  label slot: name=" + repr(lp.getName()) + " pure=" + str(lp.isPure()))
    m2 = make(graph, "SHADER_TYPE_METAL", "label sub-material")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "label opacity mask")
    if m2 is None or cur is None:
        record("P1", "INCONCLUSIVE", "couldn't build test nodes")
        return
    op = find_param(m2, "opacity")
    ok_op = False
    if op is not None:
        ok_op = try_edge(graph, cur, m2, op.getName(), "curvature->label.opacity")
    else:
        print("  no opacity param found on the label metal")
    ok_lbl = try_edge(graph, m2, root, lp.getName(), "label_mat->root.label")
    if ok_lbl:
        record("P1", "EDGE ACCEPTED", "render a frame -- if the sub-material shows on edges, chip-through is UNLOCKED")
    else:
        record("P1", "REFUSED", "label edge rejected; chip-through stays approximated by colour/roughness")


def probe_2_texture_into_mask(graph):
    hr("P2  Texture nested INTO a Curvature/Occlusion colour slot -> masked bump")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "mask")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    if cur is None or scr is None:
        record("P2", "INCONCLUSIVE", "couldn't build nodes")
        return
    pc = find_param(cur, "positive curvature")
    if pc is None:
        record("P2", "INCONCLUSIVE", "no positive_curvature param")
        return
    print("  positive_curvature: name=" + repr(pc.getName()) + " type=" + str(pc.getType()) + " pure=" + str(pc.isPure()))
    ok = try_edge(graph, scr, cur, pc.getName(), "scratches->curvature.positive_curvature")
    record("P2", "PASS" if ok else "FAIL",
           "if PASS, curvature-node itself carries the masked effect into the bump chain (masking solved)")


def probe_3_ctn_into_bump(graph):
    hr("P3  COLOR_TO_NUMBER -> scratches.bump_height (float-typed source into bump)")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    ctn = make(graph, "SHADER_TYPE_COLOR_TO_NUMBER", "adapter")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "mask source")
    if scr is None or ctn is None or cur is None:
        record("P3", "INCONCLUSIVE", "couldn't build nodes")
        return
    dump(ctn, "Color To Number")
    bh = find_param(scr, "bump height")
    inp = None
    for p in ctn.getParameters():
        if p.isPure() or p.getType() in (13, 14):
            inp = p
            break
    ok_in = False
    if inp is not None:
        ok_in = try_edge(graph, cur, ctn, inp.getName(), "curvature->ctn.input")
    ok_out = False
    if bh is not None:
        ok_out = try_edge(graph, ctn, scr, bh.getName(), "ctn->scratches.bump_height")
    record("P3", "PASS" if ok_out else "FAIL",
           "float-typed source into bump_height " + ("accepted" if ok_out else "still refused"))


def probe_4_displace(graph):
    hr("P4  DISPLACE height input texturable + Composite accepted (heavy wear ceiling)")
    disp = make(graph, "SHADER_TYPE_DISPLACE", "displacement")
    comp = make(graph, "SHADER_TYPE_COLOR_COMPOSITE", "effect x mask")
    if disp is None:
        record("P4", "NOT AVAILABLE", "no SHADER_TYPE_DISPLACE")
        return
    dump(disp, "Displace")
    h = find_param(disp, "height") or find_param(disp, "texture") or find_type(disp, 14)
    if h is None:
        record("P4", "INCONCLUSIVE", "no obvious height/texture input on Displace")
        return
    ok = False
    if comp is not None:
        ok = try_edge(graph, comp, disp, h.getName(), "composite->displace.height")
    print("  note: run lux.getMaterialGraph(name).executeGeometryNodes() + render to judge silhouette change")
    record("P4", "PASS" if ok else "FAIL",
           "Composite into Displace.height " + ("accepted -- silhouette-true damage possible" if ok else "refused"))


def probe_5_base_shaders(graph):
    hr("P5  New base-material BRDFs -- existence + parameter surface")
    bases = [
        "SHADER_TYPE_ANISOTROPIC", "SHADER_TYPE_BRUSHED", "SHADER_TYPE_BRUSHED_RADIAL",
        "SHADER_TYPE_METALLIC_PAINT", "SHADER_TYPE_AXALTA_PAINT",
        "SHADER_TYPE_DIELECTRIC", "SHADER_TYPE_GLASS", "SHADER_TYPE_GLASS_SOLID",
        "SHADER_TYPE_GEM", "SHADER_TYPE_LIQUID",
        "SHADER_TYPE_TRANSLUCENT", "SHADER_TYPE_TRANSLUCENT_ADVANCED",
        "SHADER_TYPE_PLASTIC_TRANSPARENT", "SHADER_TYPE_PLASTIC_CLOUDY",
        "SHADER_TYPE_VELVET", "SHADER_TYPE_CLOTH", "SHADER_TYPE_REALCLOTH",
        "SHADER_TYPE_DIFFUSE", "SHADER_TYPE_EMISSIVE",
        "SHADER_TYPE_ADVANCED", "SHADER_TYPE_GENERIC", "SHADER_TYPE_GENERAL",
        "SHADER_TYPE_THIN_FILM", "SHADER_TYPE_MOLD_TECH_PLASTIC",
    ]
    found = 0
    for attr in bases:
        n = make(graph, attr, "")
        if n is not None:
            found += 1
            dump(n, attr)
    record("P5", str(found) + "/" + str(len(bases)) + " present", "see dumps for real param names")


def probe_6_textures(graph):
    hr("P6  New procedural texture nodes -- existence + parameter surface")
    texs = [
        "SHADER_TYPE_WOOD", "SHADER_TYPE_WOOD_ADVANCED", "SHADER_TYPE_MARBLE",
        "SHADER_TYPE_GRANITE", "SHADER_TYPE_LEATHER", "SHADER_TYPE_FIBER_WEAVE",
        "SHADER_TYPE_WEAVE", "SHADER_TYPE_MESH", "SHADER_TYPE_MESH_CIRCULAR",
        "SHADER_TYPE_MESH_POLYGON", "SHADER_TYPE_CAMOUFLAGE", "SHADER_TYPE_CONTOUR",
        "SHADER_TYPE_FLAKES", "SHADER_TYPE_BUBBLES",
    ]
    found = 0
    for attr in texs:
        n = make(graph, attr, "")
        if n is not None:
            found += 1
            dump(n, attr)
    record("P6", str(found) + "/" + str(len(texs)) + " present", "see dumps")


def probe_7_texture_map(graph):
    hr("P7  Image TEXTURE_MAP -- file-path param (fingerprints / rust albedo)")
    tm = make(graph, "SHADER_TYPE_TEXTURE_MAP", "image map")
    if tm is None:
        record("P7", "NOT AVAILABLE", "no SHADER_TYPE_TEXTURE_MAP")
        return
    dump(tm, "Texture Map")
    path_p = find_param(tm, "path") or find_param(tm, "file") or find_param(tm, "filename") or find_param(tm, "image")
    if path_p is None:
        record("P7", "INCONCLUSIVE", "no obvious path/file string param -- see dump")
        return
    ok = False
    try:
        path_p.setValue("C:/Windows/Web/Wallpaper/Windows/img0.jpg")
        ok = True
    except Exception as e:
        print("  setValue on path FAILED: " + str(e))
    record("P7", "PASS" if ok else "FAIL", "path param = " + repr(path_p.getName()))


def probe_8_blend_mode(graph):
    hr("P8  Color Composite blend_mode value format (int enum vs string)")
    comp = make(graph, "SHADER_TYPE_COLOR_COMPOSITE", "test")
    if comp is None:
        record("P8", "NOT AVAILABLE", "no COLOR_COMPOSITE")
        return
    dump(comp, "Color Composite")
    bm = find_param(comp, "blend mode") or find_param(comp, "blend")
    if bm is None:
        record("P8", "INCONCLUSIVE", "no blend_mode param")
        return
    for candidate in [6, "Lighten", "lighten"]:
        try:
            bm.setValue(candidate)
            try:
                back = bm.getValue()
            except Exception:
                back = "?"
            print("  set blend_mode = " + repr(candidate) + " -> reads back " + repr(back))
        except Exception as e:
            print("  set blend_mode = " + repr(candidate) + " -> FAILED: " + str(e))
    record("P8", "SEE ABOVE", "note which candidate stuck (drives the roughness bus code)")


def probe_9_object_info(graph):
    hr("P9  OBJECT_INFO + CURVE_COLOR_RANDOMIZE -- per-part variation sources")
    for attr in ["SHADER_TYPE_OBJECT_INFO", "SHADER_TYPE_CURVE_COLOR_RANDOMIZE"]:
        n = make(graph, attr, "")
        if n is not None:
            dump(n, attr)
    record("P9", "SEE DUMPS", "look for a random/id/colour output usable as a colour-bus source")


def probe_10_multimaterial(graph):
    hr("P10  setMultiMaterial / setCurrentSubMaterial (variant sets)")
    ok = False
    try:
        graph.setMultiMaterial(True)
        ok = True
        print("  setMultiMaterial(True) OK")
    except Exception as e:
        print("  setMultiMaterial FAILED / absent: " + str(e))
    try:
        nodes = graph.getMaterialNodes()
        print("  getMaterialNodes() -> " + str(nodes))
    except Exception as e:
        print("  getMaterialNodes absent: " + str(e))
    record("P10", "PASS" if ok else "FAIL", "native multi-material variants " + ("scriptable" if ok else "not here"))


def probe_11_gradient(graph):
    hr("P11  Color Gradient stop payload via setValue (type-16 COLORGRADIENT)")
    cg = make(graph, "SHADER_TYPE_COLOR_GRADIENT", "gradient")
    if cg is None:
        record("P11", "NOT AVAILABLE", "no COLOR_GRADIENT")
        return
    dump(cg, "Color Gradient")
    gp = find_type(cg, 16) or find_param(cg, "gradient")
    if gp is None:
        record("P11", "INCONCLUSIVE", "no type-16 gradient param -- see dump")
        return
    for payload in [[(0.0, (0, 0, 0)), (1.0, (1, 1, 1))], [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]]:
        try:
            gp.setValue(payload)
            print("  setValue(" + repr(payload) + ") -> accepted")
        except Exception as e:
            print("  setValue(" + repr(payload) + ") -> FAILED: " + str(e))
    record("P11", "SEE ABOVE", "if any payload sticks, the gradient node is resurrected")


def probe_12_metal_film(graph):
    hr("P12  Metal film_* / coated (proper anodise / heat-tint) -- param surface")
    m = make(graph, "SHADER_TYPE_METAL", "anodise test")
    if m is None:
        record("P12", "INCONCLUSIVE", "no METAL")
        return
    for key in ["coated", "film", "anod", "metal type", "metal preset", "ior"]:
        p = find_param(m, key)
        if p is not None:
            print("  " + key + " -> name=" + repr(p.getName()) + " type=" + str(p.getType()) + " pure=" + str(p.isPure()))
    record("P12", "SEE ABOVE", "film_thickness/coated exist -> sweep values in a render session for real anodise")


def probe_13_bump_to_rough(graph):
    hr("P13  BUMP_TO_ROUGHNESS -- couple bump micro-structure into roughness")
    b2r = make(graph, "SHADER_TYPE_BUMP_TO_ROUGHNESS", "coupler")
    if b2r is None:
        record("P13", "NOT AVAILABLE", "no SHADER_TYPE_BUMP_TO_ROUGHNESS")
        return
    dump(b2r, "Bump To Roughness")
    record("P13", "PRESENT", "see dump for input(bump)/output(roughness) slot types")


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def main():
    hr("MATERIAL-GRAPH PROBE PACK  (MDD-4B7A9F section 8)")
    print("Creating disposable material '" + SCRATCH_NAME + "' -- delete it when done.")
    try:
        lux.createSceneMaterial(SCRATCH_NAME)
    except Exception as e:
        print("createSceneMaterial note: " + str(e) + " (continuing -- may already exist)")
    graph = lux.getMaterialGraph(SCRATCH_NAME)
    root = graph.getRoot()

    for fn in [probe_1_label]:
        try:
            fn(graph, root)
        except Exception as e:
            record("P1", "CRASHED", str(e))
    graph_probes = [probe_2_texture_into_mask, probe_3_ctn_into_bump, probe_4_displace,
                    probe_5_base_shaders, probe_6_textures, probe_7_texture_map,
                    probe_8_blend_mode, probe_9_object_info, probe_10_multimaterial,
                    probe_11_gradient, probe_12_metal_film, probe_13_bump_to_rough]
    for fn in graph_probes:
        try:
            fn(graph)
        except Exception as e:
            record(fn.__name__, "CRASHED", str(e))

    hr("SUMMARY  (paste this whole log back for MDD-4B7A9F Rev 2)")
    for pid, verdict, note in RESULTS:
        print("  " + pid.ljust(4) + " " + verdict + ((" -- " + note) if note else ""))
    print("")
    print("Done. Remember to delete the '" + SCRATCH_NAME + "' material from the scene.")


if __name__ == "__main__":
    main()
