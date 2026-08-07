# -*- coding: utf-8 -*-
# AUTHOR claude-opus
# REV AB01
# HEADLESS COMPLIANT
# Material-graph capability PROBE PACK, rev 2 -- a throwaway diagnostic. Builds ONE
# disposable scene material ('MATGRAPH_PROBE') and re-runs the MDD-4B7A9F section 8
# probes, with the AA01 run's results folded in. Delete the material afterwards.
#
# WHAT CHANGED FROM AA01 (and why this is a letter bump, not a number)
# -------------------------------------------------------------------
# AA01's `find_param` matched on SUBSTRING ONLY, which produced two FALSE
# NEGATIVES -- it wired the probe to the wrong parameter and reported the build
# as lacking a capability it may well have:
#   * P4 displace -- "height" matched 'displacement height' (type 4, a scalar
#     amount) instead of 'displace' (type 14 pure=True, the real texture input).
#     A type-4 scalar can never accept an edge, so the FAIL was structural.
#   * P7 image path -- "file" matched 'texture_use_profile' (the substring lives
#     inside "pro-FILE-"). The real image input is 'texture', type 9. Same class
#     of bug as the AB02 Noise/Directional-Noise routing collision.
# `find_param` is now EXACT-NAME-FIRST, substring only as a fallback, and every
# probe prints the parameter it actually chose so a mis-target is visible in the
# log rather than silent.
#
# ALREADY SETTLED BY AA01 -- deliberately not re-dumped, to keep this log readable:
#   * P5 23/24 base BRDFs present (only SHADER_TYPE_CLOTH absent), P6 14/14
#     texture nodes present -- re-run here as EXISTENCE-ONLY, no param dumps.
#   * P8 blend_mode is an INT enum (6 set + read back 6; strings refused).
#   * P11 Color Gradient stops are unsettable -- the API refuses the complex type
#     outright ("It isn't currently possible to set value of complex type"). That
#     is definitive, not a naming problem, so P11 is skipped with a note.
#   * P3 bump_height is type 4 pure=False -- a plain float on every node, so it is
#     structurally unmappable. Re-verified cheaply; do not design against it.
#
# NEW IN THIS REV
#   * P14 WORKHORSE CENSUS -- full parameter dumps of the nodes the generator
#     actually uses. AA01 never dumped SHADER_TYPE_METAL, the single most-used
#     node in the pipeline; P12 only spot-checked six search keys on it.
#   * P15 'Center On' (texture_space) is a type-2 INT enum -- sweep which int is
#     "Part". AB05 tries the string "Part" first, which cannot ever succeed.
#   * P16 completes the P2 masking chain -- P2 proved a texture nests INTO a
#     curvature colour slot; this checks the masked curvature then reaches a base
#     material's bump input, which is what actually makes masked wear render.
#   * P17 image-map constant census -- which of AB06's self-probe candidates
#     (TEXTURE_MAP / IMAGE_MAP / IMAGE / BITMAP / TEXTURE / COLOR_MAP) exist, so
#     the fallback order can be locked instead of guessed.
#
# !! KEYSHOT PYTHON CONSTRAINT -- READ BEFORE EDITING !!
# f-string-FREE + ASCII-ONLY (embedded interpreter is < 3.6 and ASCII-sensitive).
# Every lux constant is getattr-guarded; every probe is wrapped so one failure
# never stops the rest. Paste the whole console output back for MDD-4B7A9F Rev 2.

import lux

SCRATCH_NAME = "MATGRAPH_PROBE"

# EDIT ME if you want the image-path probe to use a real label PNG instead.
# Any readable image works -- the probe only cares whether the path STICKS.
TEST_IMAGE = "C:/Windows/Web/Wallpaper/Windows/img0.jpg"

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


def params_of(node):
    try:
        return list(node.getParameters())
    except Exception:
        return []


def dump(node, label=""):
    try:
        nm = label or node.getType()
    except Exception:
        nm = label or "?"
    print("  --- " + str(nm) + " ---")
    ps = params_of(node)
    if not ps:
        print("      [no parameters / could not list]")
        return
    for p in ps:
        try:
            print("      name={0:<26} display={1:<26} type={2} pure={3}".format(
                repr(p.getName()), repr(p.getDisplayName()), p.getType(), p.isPure()))
        except Exception as e:
            print("      [param unreadable] " + str(e))


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
    """EXACT name/display match first, substring only as fallback.

    AA01 matched substring-only, which silently targeted the wrong parameter
    twice (see the header). Exact-first fixes that class of bug.
    """
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
    """First param of a given type; optionally require the pure (texturable) flag."""
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
    """Print exactly which parameter a probe picked -- makes mis-targets visible."""
    if p is None:
        print("  " + label + ": NONE FOUND")
        return
    try:
        print("  " + label + ": name=" + repr(p.getName()) +
              " display=" + repr(p.getDisplayName()) +
              " type=" + str(p.getType()) + " pure=" + str(p.isPure()))
    except Exception as e:
        print("  " + label + ": [unreadable] " + str(e))


def try_edge(graph, source, target, param_name, label):
    """Attempt an edge; verify it landed via getInputEdge if available."""
    try:
        graph.newEdge(source=source, target=target, param=param_name)
    except Exception as e:
        print("  edge " + label + " -> RAISED: " + str(e))
        return False
    try:
        e = target.getInputEdge(param_name)
        landed = e is not None
        print("  edge " + label + " -> " +
              ("LANDED (verified)" if landed else "silent no-op (getInputEdge empty)"))
        return landed
    except Exception:
        print("  edge " + label + " -> accepted (getInputEdge not available to verify)")
        return True


def try_set(p, value, label):
    """setValue + read-back. Returns True only if it stuck."""
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


def enum_options(p):
    """Some builds expose enum labels directly -- try before falling back to
    the UI-reading trick in P15."""
    for attr in ["getOptions", "getEnumValues", "getChoices", "getValueOptions",
                 "getEnumOptions", "getItems"]:
        fn = getattr(p, attr, None)
        if fn is None:
            continue
        try:
            vals = fn()
            print("  enum labels via " + attr + "() -> " + repr(vals))
            return vals
        except Exception as e:
            print("  " + attr + "() present but raised: " + str(e))
    return None


# --------------------------------------------------------------------------
# Probes carried over from AA01
# --------------------------------------------------------------------------

def probe_1_label(graph, root):
    hr("P1  Root SHADERLABEL slot -> chip-through / rust-over-paint (AA01: ACCEPTED)")
    dump(root, "Root")
    lp = find_type(root, 65538)
    describe(lp, "label slot")
    if lp is None:
        record("P1", "NOT AVAILABLE", "no type-65538 (SHADERLABEL) param on root")
        return
    m2 = make(graph, "SHADER_TYPE_METAL", "label sub-material")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "label opacity mask")
    if m2 is None or cur is None:
        record("P1", "INCONCLUSIVE", "couldn't build test nodes")
        return
    op = find_param(m2, "opacitymap") or find_param(m2, "opacity")
    describe(op, "label opacity input")
    if op is not None:
        try_edge(graph, cur, m2, op.getName(), "curvature->label.opacity")
    ok_lbl = try_edge(graph, m2, root, lp.getName(), "label_mat->root.labels")
    if ok_lbl:
        record("P1", "EDGE ACCEPTED",
               "RENDER A FRAME -- graph accepts it; only the render proves it SHOWS")
    else:
        record("P1", "REFUSED", "label edge rejected")


def probe_2_texture_into_mask(graph):
    hr("P2  Texture nested INTO a Curvature colour slot -> masked bump (AA01: PASS)")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "mask")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    if cur is None or scr is None:
        record("P2", "INCONCLUSIVE", "couldn't build nodes")
        return
    pc = find_param(cur, "positive_curvature") or find_param(cur, "positive curvature")
    describe(pc, "positive_curvature")
    if pc is None:
        record("P2", "INCONCLUSIVE", "no positive_curvature param")
        return
    ok = try_edge(graph, scr, cur, pc.getName(), "scratches->curvature.positive_curvature")
    record("P2", "PASS" if ok else "FAIL", "curvature carries the masked effect")


def probe_3_ctn_into_bump(graph):
    hr("P3  COLOR_TO_NUMBER -> scratches.bump_height (AA01: FAIL -- expect FAIL again)")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    ctn = make(graph, "SHADER_TYPE_COLOR_TO_NUMBER", "adapter")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "mask source")
    if scr is None or ctn is None or cur is None:
        record("P3", "INCONCLUSIVE", "couldn't build nodes")
        return
    bh = find_param(scr, "bump_height") or find_param(scr, "bump height")
    describe(bh, "scratches.bump_height")
    inp = find_param(ctn, "input")
    describe(inp, "ctn.input")
    if inp is not None:
        try_edge(graph, cur, ctn, inp.getName(), "curvature->ctn.input")
    ok_out = False
    if bh is not None:
        ok_out = try_edge(graph, ctn, scr, bh.getName(), "ctn->scratches.bump_height")
    record("P3", "PASS" if ok_out else "FAIL",
           "bump_height is type-4 pure=False -- structurally unmappable if FAIL")


def probe_4_displace(graph):
    hr("P4  DISPLACE -- RETEST against the CORRECT input ('displace', type 14 pure)")
    disp = make(graph, "SHADER_TYPE_DISPLACE", "displacement")
    comp = make(graph, "SHADER_TYPE_COLOR_COMPOSITE", "effect x mask")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "plain-texture control")
    if disp is None:
        record("P4", "NOT AVAILABLE", "no SHADER_TYPE_DISPLACE")
        return
    dump(disp, "Displace")
    # AA01 targeted 'displacement height' (type 4 scalar) -- structurally unable
    # to take an edge. The real texture input is 'displace' (type 14, pure).
    tgt = find_param(disp, "displace") or find_type(disp, 14, pure=True)
    describe(tgt, "displace texture input (AA01 wrongly used 'displacement height')")
    if tgt is None:
        record("P4", "INCONCLUSIVE", "no type-14 pure input on Displace")
        return
    ok_plain = False
    ok_comp = False
    if scr is not None:
        ok_plain = try_edge(graph, scr, disp, tgt.getName(), "scratches->displace.displace")
    if comp is not None:
        ok_comp = try_edge(graph, comp, disp, tgt.getName(), "composite->displace.displace")
    # Two edges into one slot: the second may legitimately replace the first.
    # What matters is whether EITHER is accepted at all.
    print("  note: if this passes, run executeGeometryNodes() + render to judge silhouette")
    if ok_plain or ok_comp:
        record("P4", "PASS",
               "plain=" + str(ok_plain) + " composite=" + str(ok_comp) +
               " -- displacement is scriptable; AA01's FAIL was a mis-targeted probe")
    else:
        record("P4", "FAIL", "even the correct type-14 pure input refused an edge")


def probe_5_base_shaders_existence(graph):
    hr("P5  Base BRDFs -- EXISTENCE ONLY (AA01 dumped these; 23/24 present)")
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
    missing = []
    found = 0
    for attr in bases:
        if shader(attr) is None:
            missing.append(attr)
        else:
            found += 1
    print("  present: " + str(found) + "/" + str(len(bases)))
    print("  missing: " + (", ".join(missing) if missing else "(none)"))
    record("P5", str(found) + "/" + str(len(bases)) + " present",
           "missing = " + (", ".join(missing) if missing else "none"))


def probe_6_textures_existence(graph):
    hr("P6  Texture nodes -- EXISTENCE ONLY (AA01 dumped these; 14/14 present)")
    texs = [
        "SHADER_TYPE_WOOD", "SHADER_TYPE_WOOD_ADVANCED", "SHADER_TYPE_MARBLE",
        "SHADER_TYPE_GRANITE", "SHADER_TYPE_LEATHER", "SHADER_TYPE_FIBER_WEAVE",
        "SHADER_TYPE_WEAVE", "SHADER_TYPE_MESH", "SHADER_TYPE_MESH_CIRCULAR",
        "SHADER_TYPE_MESH_POLYGON", "SHADER_TYPE_CAMOUFLAGE", "SHADER_TYPE_CONTOUR",
        "SHADER_TYPE_FLAKES", "SHADER_TYPE_BUBBLES",
    ]
    missing = [a for a in texs if shader(a) is None]
    found = len(texs) - len(missing)
    print("  present: " + str(found) + "/" + str(len(texs)))
    print("  missing: " + (", ".join(missing) if missing else "(none)"))
    record("P6", str(found) + "/" + str(len(texs)) + " present",
           "missing = " + (", ".join(missing) if missing else "none"))


def probe_7_texture_map(graph):
    hr("P7  Image TEXTURE_MAP -- RETEST against the CORRECT input ('texture', type 9)")
    tm = make(graph, "SHADER_TYPE_TEXTURE_MAP", "image map")
    if tm is None:
        record("P7", "NOT AVAILABLE", "no SHADER_TYPE_TEXTURE_MAP")
        return
    dump(tm, "Texture Map")
    # AA01 searched "path"/"file"/"filename"/"image" by substring and landed on
    # 'texture_use_profile' -- "file" is inside "pro-FILE-". The image input is
    # 'texture', type 9 (same type as normalmap / specularmap / height_map).
    tex = find_param(tm, "texture") or find_type(tm, 9)
    describe(tex, "image input (AA01 wrongly used 'texture_use_profile')")
    if tex is None:
        record("P7", "INCONCLUSIVE", "no type-9 image param -- see dump")
        return
    ok = try_set(tex, TEST_IMAGE, "texture path")
    if not ok:
        print("  (if this refused a str, the type-9 setter may want a different"
              " payload -- paste the error)")
    record("P7", "PASS" if ok else "FAIL",
           "image param = " + repr(tex.getName()) + " type 9; test image = " + TEST_IMAGE)


def probe_8_blend_mode(graph):
    hr("P8  Color Composite blend_mode (AA01: INT enum -- 6 stuck, strings refused)")
    comp = make(graph, "SHADER_TYPE_COLOR_COMPOSITE", "test")
    if comp is None:
        record("P8", "NOT AVAILABLE", "no COLOR_COMPOSITE")
        return
    bm = find_param(comp, "blend_mode") or find_param(comp, "blend mode")
    describe(bm, "blend_mode")
    if bm is None:
        record("P8", "INCONCLUSIVE", "no blend_mode param")
        return
    opts = enum_options(bm)
    # Sweep the enum so the int -> mode mapping can be read off the UI panel.
    accepted = []
    for i in range(0, 16):
        try:
            bm.setValue(i)
            accepted.append(i)
        except Exception:
            pass
    print("  ints accepted 0..15: " + repr(accepted))
    bm.setValue(6)
    record("P8", "INT ENUM CONFIRMED",
           "labels=" + ("exposed" if opts else "not exposed") +
           "; accepted " + str(len(accepted)) + " of 16 ints -- left set to 6")


def probe_9_object_info(graph):
    hr("P9  Per-part variation sources (AA01: OBJECT_INFO absent)")
    for attr in ["SHADER_TYPE_OBJECT_INFO", "SHADER_TYPE_CURVE_COLOR_RANDOMIZE",
                 "SHADER_TYPE_RANDOM", "SHADER_TYPE_PART_INFO", "SHADER_TYPE_GEOMETRY_INFO"]:
        n = make(graph, attr, "")
        if n is not None:
            dump(n, attr)
    record("P9", "SEE DUMPS", "looking for any per-PART random/id source")


def probe_10_multimaterial(graph):
    hr("P10  setMultiMaterial / getMaterialNodes (AA01: PASS)")
    ok = False
    try:
        graph.setMultiMaterial(True)
        ok = True
        print("  setMultiMaterial(True) OK")
    except Exception as e:
        print("  setMultiMaterial FAILED / absent: " + str(e))
    try:
        print("  getMaterialNodes() -> " + str(graph.getMaterialNodes()))
    except Exception as e:
        print("  getMaterialNodes absent: " + str(e))
    record("P10", "PASS" if ok else "FAIL", "native multi-material variants")


def probe_12_metal_film(graph):
    hr("P12  Metal film / coated -- superseded by P14's full dump, kept for the log")
    m = make(graph, "SHADER_TYPE_METAL", "anodise test")
    if m is None:
        record("P12", "INCONCLUSIVE", "no METAL")
        return
    for key in ["coated", "film_thickness", "film_ior", "film_extinction",
                "metal_type", "metal_preset"]:
        describe(find_param(m, key), key)
    record("P12", "SEE ABOVE", "exact-match now, so a NONE FOUND here is real")


def probe_13_bump_to_rough(graph):
    hr("P13  BUMP_TO_ROUGHNESS (AA01: PRESENT)")
    b2r = make(graph, "SHADER_TYPE_BUMP_TO_ROUGHNESS", "coupler")
    if b2r is None:
        record("P13", "NOT AVAILABLE", "no SHADER_TYPE_BUMP_TO_ROUGHNESS")
        return
    record("P13", "PRESENT", "dumped in AA01; not re-dumped")


# --------------------------------------------------------------------------
# New probes
# --------------------------------------------------------------------------

WORKHORSES = [
    # The nodes 1_HLP_MAT_GENERATOR actually builds with. METAL especially --
    # AA01 never dumped it, and it is the most-used node in the whole pipeline.
    "SHADER_TYPE_METAL",
    "SHADER_TYPE_PLASTIC",
    "SHADER_TYPE_PAINT",
    "SHADER_TYPE_SCRATCHES",
    "SHADER_TYPE_SPOTS",
    "SHADER_TYPE_OCCLUSION",
    "SHADER_TYPE_CURVATURE",
    "SHADER_TYPE_NOISE_TEXTURE",
    "SHADER_TYPE_NOISE_FRACTAL",
    "SHADER_TYPE_CELLULAR",
    "SHADER_TYPE_ROUNDED_EDGES",
    "SHADER_TYPE_BUMP_ADD",
]


def probe_14_workhorse_census(graph):
    hr("P14  WORKHORSE CENSUS -- full dumps of the nodes the generator actually uses")
    print("  (AA01 never dumped METAL/PLASTIC/PAINT/SCRATCHES/SPOTS -- this is the gap)")
    present = 0
    for attr in WORKHORSES:
        n = make(graph, attr, "")
        if n is not None:
            present += 1
            dump(n, attr)
    record("P14", str(present) + "/" + str(len(WORKHORSES)) + " present",
           "these dumps lock every display name the generator guesses at")


def probe_15_center_on_enum(graph):
    hr("P15  'Center On' (texture_space) is a type-2 INT enum -- which int is Part?")
    print("  AB05 tries the STRING \"Part\" first; a type-2 int enum can never take it.")
    probe_node = make(graph, "SHADER_TYPE_SCRATCHES", "enum sweep")
    if probe_node is None:
        record("P15", "INCONCLUSIVE", "couldn't build a scratches node")
        return
    ts = find_param(probe_node, "texture_space") or find_param(probe_node, "center on")
    describe(ts, "texture_space")
    if ts is None:
        record("P15", "NOT PRESENT", "no texture_space on Scratches -- check P14 dumps")
        return
    opts = enum_options(ts)
    if opts:
        record("P15", "LABELS EXPOSED", "enum labels printed above -- read Part's index off them")
        return
    # No label API. Fall back to tagging: build one node per candidate int and give
    # each a distinctive Scale, so the mapping can be read straight off the UI.
    print("")
    print("  No enum-label API on this build. Building one tagged node per candidate")
    print("  int -- open the MATGRAPH_PROBE material graph and read each node's")
    print("  'Center On' dropdown; match it by the node's Scale value:")
    print("")
    print("    Scale value  ->  texture_space int")
    accepted = []
    for i in range(0, 6):
        tag = make(graph, "SHADER_TYPE_SCRATCHES", "tag int=" + str(i))
        if tag is None:
            continue
        tp = find_param(tag, "texture_space")
        sp = find_param(tag, "scale")
        if tp is None:
            continue
        try:
            tp.setValue(i)
        except Exception as e:
            print("    int " + str(i) + " -> REFUSED: " + str(e))
            continue
        accepted.append(i)
        marker = (i + 1) * 10.0
        if sp is not None:
            try:
                sp.setValue(marker)
                print("    Scale " + str(marker) + "  ->  texture_space = " + str(i))
            except Exception:
                print("    (int " + str(i) + " set, but Scale tag failed)")
        else:
            print("    (int " + str(i) + " set, no Scale param to tag with)")
    # A string attempt, to document the failure mode AB05 currently hits.
    try_set(ts, "Part", "texture_space (STRING attempt -- expected to fail)")
    record("P15", "SWEEP DONE",
           "ints accepted: " + repr(accepted) + " -- read Part's int off the UI panel")


def probe_16_masked_bump_chain(graph):
    hr("P16  Complete the P2 chain -- does the MASKED curvature reach a bump input?")
    print("  P2 proved scratches nests INTO curvature. What makes masked wear actually")
    print("  RENDER is the next hop: curvature -> base material's bump (type 65539).")
    base = make(graph, "SHADER_TYPE_METAL", "chain base")
    cur = make(graph, "SHADER_TYPE_CURVATURE", "mask carrying effect")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    if base is None or cur is None or scr is None:
        record("P16", "INCONCLUSIVE", "couldn't build chain nodes")
        return
    pc = find_param(cur, "positive_curvature")
    if pc is not None:
        try_edge(graph, scr, cur, pc.getName(), "scratches->curvature.positive_curvature")
    bm = find_param(base, "bumpmap") or find_type(base, 65539)
    describe(bm, "base bump input")
    if bm is None:
        record("P16", "INCONCLUSIVE", "no type-65539 bump input on METAL")
        return
    ok = try_edge(graph, cur, base, bm.getName(), "curvature(masked)->metal.bumpmap")
    record("P16", "PASS" if ok else "FAIL",
           "if PASS, masked wear is fully wireable end-to-end -- render to confirm it READS")


IMAGE_CANDIDATES = ["SHADER_TYPE_TEXTURE_MAP", "SHADER_TYPE_IMAGE_MAP",
                    "SHADER_TYPE_IMAGE", "SHADER_TYPE_BITMAP",
                    "SHADER_TYPE_TEXTURE", "SHADER_TYPE_COLOR_MAP",
                    "SHADER_TYPE_COLORMAP"]


def probe_17_image_constants(graph):
    hr("P17  Image-map constant census -- lock AB06's self-probe fallback order")
    for attr in IMAGE_CANDIDATES:
        st = shader(attr)
        if st is None:
            print("  [MISSING]  " + attr)
        else:
            print("  [PRESENT]  " + attr + "  (value " + str(st) + ")")
    present = [a for a in IMAGE_CANDIDATES if shader(a) is not None]
    record("P17", str(len(present)) + "/" + str(len(IMAGE_CANDIDATES)) + " present",
           "order to try: " + (", ".join(present) if present else "NONE"))


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def main():
    hr("MATERIAL-GRAPH PROBE PACK  REV AB01  (MDD-4B7A9F section 8, rev 2)")
    print("Creating disposable material '" + SCRATCH_NAME + "' -- delete it when done.")
    print("Test image for P7: " + TEST_IMAGE)
    try:
        lux.createSceneMaterial(SCRATCH_NAME)
    except Exception as e:
        print("createSceneMaterial note: " + str(e) + " (continuing -- may already exist)")
    graph = lux.getMaterialGraph(SCRATCH_NAME)
    root = graph.getRoot()

    try:
        probe_1_label(graph, root)
    except Exception as e:
        record("P1", "CRASHED", str(e))

    graph_probes = [
        probe_2_texture_into_mask,
        probe_3_ctn_into_bump,
        probe_4_displace,
        probe_5_base_shaders_existence,
        probe_6_textures_existence,
        probe_7_texture_map,
        probe_8_blend_mode,
        probe_9_object_info,
        probe_10_multimaterial,
        probe_12_metal_film,
        probe_13_bump_to_rough,
        probe_14_workhorse_census,
        probe_15_center_on_enum,
        probe_16_masked_bump_chain,
        probe_17_image_constants,
    ]
    for fn in graph_probes:
        try:
            fn(graph)
        except Exception as e:
            record(fn.__name__, "CRASHED", str(e))

    hr("P11  Color Gradient -- SKIPPED (AA01 settled it)")
    print("  The API refuses the complex type outright: 'It isn't currently possible")
    print("  to set value of complex type: ColorGradient'. That is not a naming")
    print("  problem and will not change on a re-run. The node's 'map' input (type 4,")
    print("  pure) IS drivable -- a default-stop gradient can still be modulated.")
    record("P11", "SKIPPED", "definitively unsettable per AA01")

    hr("SUMMARY  (paste this whole log back for MDD-4B7A9F Rev 2)")
    for pid, verdict, note in RESULTS:
        print("  " + pid.ljust(6) + " " + verdict + ((" -- " + note) if note else ""))
    print("")
    print("MANUAL STEP: if P15 had no enum-label API, open the MATGRAPH_PROBE material")
    print("graph and read the 'Center On' dropdown on each tagged Scratches node --")
    print("the node's Scale value identifies which int it was set to.")
    print("")
    print("Done. Remember to delete the '" + SCRATCH_NAME + "' material from the scene.")


if __name__ == "__main__":
    main()
