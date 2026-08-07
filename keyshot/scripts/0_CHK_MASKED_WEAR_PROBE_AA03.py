# -*- coding: utf-8 -*-
# AUTHOR claude-opus
# REV AA03
# HEADLESS COMPLIANT
# AA02 FIX: AA01 called lux.newMaterial(), which does not exist on this build, so
# the probe died before probe M1 with "[FATAL] couldn't get the material graph".
# The proven call, used by the generator and the earlier probe pack every run, is
# lux.createSceneMaterial(). Guessing an API name is the exact failure this pack
# was written to stop other people making. Now getattr-checked, and if it is ever
# missing the probe prints the module's real create*/material* surface instead of
# just failing.
#
# MASKED WEAR probe pack -- a throwaway diagnostic for ONE question: how do you
# make wear land only where it physically would (scratches on edges, pitting in
# crevices) when the API refuses the obvious route? Builds one disposable scene
# material ('MASKED_WEAR_PROBE'). Delete it afterwards. No render needed for M1-M5.
#
# WHY THIS EXISTS
# ---------------
# The generator has logged this on every run since AB01:
#     [warn] couldn't wire scratches->edges: mask -> bump height: Could not
#            create requested edge!
# and the standing plan was the "probed plan-B" from MWR-9C4E21: nest the effect
# into a Curvature colour slot (probe P2, PASS) and let curvature carry the
# masked effect into the bump chain. Reading the AB01 log properly, that plan is
# only HALF proven, and the unproven half FAILED:
#     P2  scratches -> curvature.positive_curvature  -> LANDED
#     P16 curvature(masked) -> metal.bumpmap         -> RAISED, could not create
# So the mask goes IN and then has nowhere to go. Masked wear has never been
# wireable end to end, and no amount of renaming will change that.
#
# WHAT THE THREE KNOWN DATA POINTS ACTUALLY IMPLY
#   scratches -> metal.bumpmap            LANDS   (the generator does it daily)
#   curvature -> metal.bumpmap            RAISES  (P16)
#   composite -> metal.bumpmap            RAISES  (the Rev 2 correction in MWR)
# A bump input does not take just any node. It looks like it takes TEXTURE-class
# nodes and refuses UTILITY-class ones. M1 turns that hunch into a table.
#
# AND THE IDEA WORTH TESTING (M2) -- mask INSIDE the texture, not after it
# A texture used as bump is read as a height field off its own output colour. So
# instead of masking the bump AFTER the texture (refused), drive the texture's
# own COLOUR slots with the mask:
#     curvature -> scratches.inside_color     (white on edges, black on flats)
#     scratches.outside_color = black
#     scratches -> metal.bumpmap              (a plain texture edge, which works)
# On a flat face inside and outside are both black, so the surface is flat. On an
# edge the scratch interiors go white, so the grooves appear. That is a spatially
# masked bump built entirely out of edges the API already accepts -- IF a colour
# slot on a texture node takes a connection. P2 proved exactly that shape for
# curvature.positive_curvature (type 13, pure=False, and it LANDED), so this is
# a reasonable bet rather than a hopeful one.
#
# PARAMETER TYPE RULES worth holding while reading results (from the AB01 dumps):
#   type 4  float   -- REFUSED an edge on a texture node (bump_height, P3), but
#                      metal.roughness (also type 4) IS wired every run. So the
#                      gate is not the type alone; it is type AND which node.
#   type 13 colour  -- accepts a connection even with pure=False (P2).
#   type 14 texturable -- accepts (displace.displace, composite inputs).
#   type 65539 bump -- accepts texture-class nodes only. That is what M1 tests.
#
# !! KEYSHOT PYTHON CONSTRAINT -- READ BEFORE EDITING !!
# f-string-FREE + ASCII-ONLY (embedded interpreter is < 3.6, ASCII-sensitive).
# Every lux constant is getattr-guarded; every probe is wrapped so one failure
# never stops the rest. Paste the whole console output back.

import lux

SCRATCH_NAME = "MASKED_WEAR_PROBE"

RESULTS = []  # (probe id, verdict, note)


def hr(title):
    print("=" * 70)
    print(title)
    print("=" * 70)


def record(pid, verdict, note=""):
    RESULTS.append((pid, verdict, note))
    print("  >> {0}: {1}{2}".format(pid, verdict, (" -- " + note) if note else ""))


def params_of(node):
    try:
        return list(node.getParameters())
    except Exception as e:
        print("    [warn] couldn't list parameters: {0}".format(e))
        return []


def dump(node, label=""):
    print("--- {0} ---".format(label or "node"))
    for p in params_of(node):
        try:
            print("    name={0:<24} display={1:<24} type={2} pure={3}".format(
                repr(p.getName()), repr(p.getDisplayName()), p.getType(), p.isPure()))
        except Exception:
            pass


def shader(attr):
    return getattr(lux, attr, None)


def make(graph, attr, label=""):
    """Create a node by lux constant name; None (with a note) if absent."""
    st = shader(attr)
    if st is None:
        print("  [absent] lux.{0} not on this build".format(attr))
        return None
    try:
        n = graph.newNode(st)
        print("  [created] {0}{1}".format(attr, (" -- " + label) if label else ""))
        return n
    except Exception as e:
        print("  [warn] couldn't create {0}: {1}".format(attr, e))
        return None


def find_param(node, needle):
    """EXACT name/display match first, substring only as a fallback. Substring-only
    matching has produced three false negatives in this project (displace.height,
    texture_use_profile, and the Noise routing collision) -- do not reintroduce it."""
    ps = params_of(node)
    low = needle.lower()
    for p in ps:
        try:
            if p.getName().lower() == low or p.getDisplayName().lower() == low:
                return p
        except Exception:
            pass
    for p in ps:
        try:
            if low in p.getName().lower() or low in p.getDisplayName().lower():
                return p
        except Exception:
            pass
    return None


def describe(p, label):
    try:
        print("  {0}: name={1} display={2} type={3} pure={4}".format(
            label, repr(p.getName()), repr(p.getDisplayName()), p.getType(), p.isPure()))
    except Exception:
        pass


def try_edge(graph, source, target, param_name, label):
    """Attempt an edge; report LANDED / RAISED. Verified by re-reading the input
    edge where the API supports it, because a silent no-op would otherwise read
    as success -- which is exactly how the material spent six revs not applying."""
    if source is None or target is None:
        print("  [skip] {0} -- a node is missing".format(label))
        return False
    try:
        graph.newEdge(source, target, param_name)
    except Exception as e:
        print("  edge {0} -> RAISED: {1}".format(label, e))
        return False
    try:
        edge = target.getInputEdge(param_name)
        if edge:
            print("  edge {0} -> LANDED (verified)".format(label))
            return True
        print("  edge {0} -> ACCEPTED but reads back EMPTY (treat as failed)".format(label))
        return False
    except Exception:
        print("  edge {0} -> ACCEPTED (no read-back API; unverified)".format(label))
        return True


def set_color(node, needle, rgb):
    p = find_param(node, needle)
    if p is None:
        print("  [warn] no parameter matching '{0}'".format(needle))
        return False
    try:
        p.setValue(rgb)
        return True
    except Exception as e:
        print("  [warn] couldn't set '{0}': {1}".format(needle, e))
        return False


# ---------------------------------------------------------------------------
# M1  WHAT DOES A BUMP INPUT ACTUALLY ACCEPT?
# ---------------------------------------------------------------------------

BUMP_CANDIDATES = [
    ("SHADER_TYPE_SCRATCHES",       "texture   -- known good, the control"),
    ("SHADER_TYPE_NOISE_TEXTURE",   "texture"),
    ("SHADER_TYPE_SPOTS",           "texture"),
    ("SHADER_TYPE_CELLULAR",        "texture"),
    ("SHADER_TYPE_NOISE_FRACTAL",   "texture"),
    ("SHADER_TYPE_TEXTURE_MAP",     "image texture"),
    ("SHADER_TYPE_BUMP_ADD",        "bump utility -- known good"),
    ("SHADER_TYPE_CURVATURE",       "utility -- P16 says NO into metal.bumpmap"),
    ("SHADER_TYPE_OCCLUSION",       "utility"),
    ("SHADER_TYPE_COLOR_COMPOSITE", "utility -- MWR Rev 2 says NO"),
    ("SHADER_TYPE_COLOR_TO_NUMBER", "utility"),
    ("SHADER_TYPE_COLOR_ADJUST",    "utility"),
    ("SHADER_TYPE_COLOR_INVERT",    "utility"),
    ("SHADER_TYPE_ROUNDED_EDGES",   "geometry utility"),
]


def probe_m1(graph):
    hr("M1  Bump-input census -- which node CLASSES can drive a bump input?")
    print("  One fresh Metal per candidate, so a refused edge cannot poison the next.")
    base = make(graph, "SHADER_TYPE_METAL", "census base")
    if base is None:
        record("M1", "SKIPPED", "no METAL to test against")
        return
    bp = find_param(base, "bumpmap") or find_param(base, "bump")
    if bp is None:
        record("M1", "SKIPPED", "no bump input on METAL")
        return
    describe(bp, "metal bump input")
    accepted = []
    refused = []
    absent = []
    for attr, note in BUMP_CANDIDATES:
        host = make(graph, "SHADER_TYPE_METAL", "")
        if host is None:
            continue
        hp = find_param(host, "bumpmap") or find_param(host, "bump")
        node = make(graph, attr, note)
        if node is None:
            absent.append(attr)
            continue
        ok = try_edge(graph, node, host, hp.getName(), "{0} -> metal.bumpmap".format(attr))
        (accepted if ok else refused).append(attr)
    print("")
    print("  ACCEPTED into a bump input: {0}".format(", ".join(accepted) or "(none)"))
    print("  REFUSED:                    {0}".format(", ".join(refused) or "(none)"))
    if absent:
        print("  ABSENT on this build:       {0}".format(", ".join(absent)))
    record("M1", "SEE TABLE",
           "{0} accepted / {1} refused -- this is the rule the design must obey".format(
               len(accepted), len(refused)))


# ---------------------------------------------------------------------------
# M2  MASK INSIDE THE TEXTURE -- the route that would make masked bump work
# ---------------------------------------------------------------------------

def probe_m2(graph):
    hr("M2  Curvature -> scratches COLOUR slots -> bump (masked bump, the real prize)")
    print("  If a texture's colour slots take a connection, the mask can live")
    print("  INSIDE the texture and the bump edge stays a plain texture edge.")
    base = make(graph, "SHADER_TYPE_METAL", "chain base")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    curv = make(graph, "SHADER_TYPE_CURVATURE", "edge mask")
    if not (base and scr and curv):
        record("M2", "SKIPPED", "a node is missing")
        return
    dump(scr, "SHADER_TYPE_SCRATCHES (colour slots are the target)")
    set_color(curv, "positive curvature", (1.0, 1.0, 1.0))
    set_color(curv, "zero curvature", (0.0, 0.0, 0.0))
    set_color(curv, "negative curvature", (0.0, 0.0, 0.0))

    inside = find_param(scr, "inside_color") or find_param(scr, "color")
    outside = find_param(scr, "outside_color") or find_param(scr, "background")
    hit_in = hit_out = False
    if inside is not None:
        describe(inside, "scratches inside")
        hit_in = try_edge(graph, curv, scr, inside.getName(),
                          "curvature -> scratches.inside_color")
    if outside is not None:
        describe(outside, "scratches outside")
        hit_out = try_edge(graph, curv, scr, outside.getName(),
                           "curvature -> scratches.outside_color")
    bp = find_param(base, "bumpmap") or find_param(base, "bump")
    hit_bump = False
    if bp is not None:
        hit_bump = try_edge(graph, scr, base, bp.getName(),
                            "masked scratches -> metal.bumpmap")
    if (hit_in or hit_out) and hit_bump:
        record("M2", "PASS",
               "masked bump IS wireable this way -- render to confirm the mask READS")
    elif hit_bump:
        record("M2", "FAIL", "colour slots refuse a connection -- masked bump has no route")
    else:
        record("M2", "FAIL", "the bump edge itself did not land -- see M1")


# ---------------------------------------------------------------------------
# M3  the same trick for cavity grime, using Occlusion
# ---------------------------------------------------------------------------

def probe_m3(graph):
    hr("M3  Occlusion -> spots colour slots -> bump (pitting only in crevices)")
    base = make(graph, "SHADER_TYPE_METAL", "chain base")
    spots = make(graph, "SHADER_TYPE_SPOTS", "effect")
    occ = make(graph, "SHADER_TYPE_OCCLUSION", "cavity mask")
    if not (base and spots and occ):
        record("M3", "SKIPPED", "a node is missing")
        return
    set_color(occ, "occluded", (1.0, 1.0, 1.0))
    set_color(occ, "unoccluded", (0.0, 0.0, 0.0))
    inside = find_param(spots, "inside_color") or find_param(spots, "color")
    hit_in = False
    if inside is not None:
        describe(inside, "spots inside")
        hit_in = try_edge(graph, occ, spots, inside.getName(),
                          "occlusion -> spots.inside_color")
    bp = find_param(base, "bumpmap") or find_param(base, "bump")
    hit_bump = try_edge(graph, spots, base, bp.getName(),
                        "masked spots -> metal.bumpmap") if bp else False
    record("M3", "PASS" if (hit_in and hit_bump) else "FAIL",
           "cavity-masked pitting" + ("" if hit_in else " -- colour slot refused"))


# ---------------------------------------------------------------------------
# M4  the fallback everyone assumes works: mask into Bump Add
# ---------------------------------------------------------------------------

def probe_m4(graph):
    hr("M4  Curvature -> BumpAdd.bump_1 (control -- expected to fail like P16)")
    ba = make(graph, "SHADER_TYPE_BUMP_ADD", "bump combiner")
    curv = make(graph, "SHADER_TYPE_CURVATURE", "mask")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "texture control")
    if not (ba and curv):
        record("M4", "SKIPPED", "a node is missing")
        return
    b1 = find_param(ba, "bump_1")
    b2 = find_param(ba, "bump_2")
    if b1 is not None:
        describe(b1, "bump_1")
    hit_curv = try_edge(graph, curv, ba, b1.getName(),
                        "curvature -> bumpadd.bump_1") if b1 else False
    hit_tex = try_edge(graph, scr, ba, b2.getName(),
                       "scratches -> bumpadd.bump_2 (control)") if (b2 and scr) else False
    if hit_curv:
        record("M4", "PASS -- SURPRISE",
               "Bump Add accepts a utility node even though metal.bumpmap does not")
    else:
        record("M4", "FAIL as expected",
               "texture control {0} -- the bump domain takes textures only".format(
                   "landed" if hit_tex else "also failed, which would be odd"))


# ---------------------------------------------------------------------------
# M5  masked ROUGHNESS -- the route that is almost certainly available today
# ---------------------------------------------------------------------------

def probe_m5(graph):
    hr("M5  Masked roughness -- scratches nested in curvature, into metal.roughness")
    print("  metal.roughness is type 4 pure=False yet IS wired on every real run,")
    print("  so a type-4 param on a BRDF behaves differently from one on a texture.")
    base = make(graph, "SHADER_TYPE_METAL", "chain base")
    curv = make(graph, "SHADER_TYPE_CURVATURE", "mask carrying the effect")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    if not (base and curv and scr):
        record("M5", "SKIPPED", "a node is missing")
        return
    pc = find_param(curv, "positive_curvature")
    nested = try_edge(graph, scr, curv, pc.getName(),
                      "scratches -> curvature.positive_curvature (P2 repeat)") if pc else False
    rp = find_param(base, "roughness")
    if rp is not None:
        describe(rp, "metal roughness")
    landed = try_edge(graph, curv, base, rp.getName(),
                      "masked curvature -> metal.roughness") if rp else False
    record("M5", "PASS" if (nested and landed) else "FAIL",
           "edge-localised roughness is the fallback if bump masking is impossible")


# ---------------------------------------------------------------------------
# M6  masked DISPLACEMENT -- real geometry, the strongest version of edge wear
# ---------------------------------------------------------------------------

def probe_m6(graph):
    hr("M6  Masked displacement -- curvature (carrying scratches) -> displace.displace")
    print("  P4 already proved a plain texture AND a composite land on 'displace'.")
    print("  This asks whether the MASKED chain lands, which would give real")
    print("  geometric chipping on edges rather than a shading trick.")
    disp = make(graph, "SHADER_TYPE_DISPLACE", "displacement")
    curv = make(graph, "SHADER_TYPE_CURVATURE", "mask carrying the effect")
    scr = make(graph, "SHADER_TYPE_SCRATCHES", "effect")
    if not (disp and curv and scr):
        record("M6", "SKIPPED", "a node is missing")
        return
    pc = find_param(curv, "positive_curvature")
    if pc:
        try_edge(graph, scr, curv, pc.getName(), "scratches -> curvature.positive_curvature")
    dp = find_param(disp, "displace")
    if dp is not None:
        describe(dp, "displace input")
    landed = try_edge(graph, curv, disp, dp.getName(),
                      "masked curvature -> displace.displace") if dp else False
    print("  NOTE: displacement needs graph.executeGeometryNodes() (a MaterialGraph")
    print("        METHOD, not a lux module function) AND a render to judge.")
    record("M6", "PASS" if landed else "FAIL",
           "geometric edge wear" + (" -- run graph.executeGeometryNodes() next" if landed else ""))


def main():
    print("MASKED WEAR probe pack  REV AA03")
    print("Builds one scratch material '{0}'. Delete it when done.".format(SCRATCH_NAME))
    print("")
    create = getattr(lux, "createSceneMaterial", None)
    if create is None:
        print("[FATAL] lux.createSceneMaterial is missing on this build.")
        print("        The module's material-related surface is:")
        for name in sorted(dir(lux)):
            low = name.lower()
            if "material" in low or low.startswith("create") or low.startswith("new"):
                print("          {0}".format(name))
        print("        Use one of those and re-run.")
        return
    try:
        create(SCRATCH_NAME)
    except Exception as e:
        print("[info] createSceneMaterial: {0} (may already exist -- continuing)".format(e))
    try:
        graph = lux.getMaterialGraph(SCRATCH_NAME)
    except Exception as e:
        print("[FATAL] couldn't get the material graph: {0}".format(e))
        print("        The material was not created, so nothing below can run.")
        return
    if graph is None:
        print("[FATAL] getMaterialGraph returned nothing for '{0}'.".format(SCRATCH_NAME))
        return
    for fn in (probe_m1, probe_m2, probe_m3, probe_m4, probe_m5, probe_m6):
        try:
            fn(graph)
        except Exception as e:
            print("  [error] probe raised: {0}".format(e))
            record(fn.__name__, "ERROR", str(e))
        print("")
    hr("SUMMARY -- paste this whole log back")
    for pid, verdict, note in RESULTS:
        print("  {0:<6} {1}{2}".format(pid, verdict, (" -- " + note) if note else ""))
    print("")
    print("READ IT LIKE THIS:")
    print("  M2 PASS  -> masked bump is real; the generator's masking gets rebuilt")
    print("              around texture colour slots and edge wear finally works.")
    print("  M2 FAIL, M5 PASS -> masked bump is impossible in this API; targeted")
    print("              wear becomes a roughness/colour effect, which on metal")
    print("              still reads convincingly. Say so in the docs and stop")
    print("              retrying the bump route.")
    print("  M6 PASS  -> geometric edge wear is available for hero renders, at a")
    print("              geometry cost. Needs executeGeometryNodes() and a frame.")
    print("")
    print("Then delete the '{0}' material.".format(SCRATCH_NAME))


main()
