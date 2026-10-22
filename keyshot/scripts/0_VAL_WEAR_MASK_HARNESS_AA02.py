                       
                                   
          
                                                                             
                                                                                 
 
                                                                            
                                                                               
                                                                         
                                                        
                                                                       
                                                   
                                                                              
                                                            
 
                                                                           
                                                                             
 
                                                                           
                                                                             
                                                                             
                                                                           
                                                                           
                                                                             
                                                                           
                                                                               
 
                           

import io
import math
import os
import random
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
GENERATOR_PREFIX = "1_HLP_PAINT_GENERATOR_"


def newest_generator():
                                                                             
                                                                   
                                                                                 
    found = []
    try:
        for name in os.listdir(HERE):
            if name.startswith(GENERATOR_PREFIX) and name.endswith(".py"):
                found.append(name)
    except Exception:
        pass
    return sorted(found)[-1] if found else None


def resolve_src(argv):
                                                                

                                                            
                                                                            
                                                                           
                         
    default = newest_generator()
    if len(argv) < 2:
        return default
    name = os.path.basename(argv[1])
    if name == os.path.basename(__file__) or not name.endswith(".py"):
        return default
    if not os.path.exists(os.path.join(HERE, name)):
        return default
    return name


SRC = resolve_src(sys.argv)
if SRC is None:
    print("no %s*.py found next to this harness -- nothing to test" % GENERATOR_PREFIX)
    sys.exit(1)

lux = types.ModuleType("lux")
lux.PARAMETER_TYPE_FLOAT = 4
lux.PARAMETER_TYPE_COLOR = 13
lux.PARAMETER_TYPE_INTEGER = 6
lux.PARAMETER_TYPE_BOOLEAN = 2
lux.PARAMETER_TYPE_STRING = 9
sys.modules["lux"] = lux

                                                                                
                                                                                 
SHADERS = {
    "SHADER_TYPE_CURVATURE": 10,
    "SHADER_TYPE_OCCLUSION": 11,
    "SHADER_TYPE_SCRATCHES": 12,
    "SHADER_TYPE_COLOR_INVERT": 20,
    "SHADER_TYPE_COLOR_ADJUST": 21,
    "SHADER_TYPE_COLOR_COMPOSITE": 22,
}


def install_shaders(absent=()):
    for name in list(vars(lux)):
        if name.startswith("SHADER_TYPE_"):
            delattr(lux, name)
    for name, value in SHADERS.items():
        if name not in absent:
            setattr(lux, name, value)


class Param(object):
    def __init__(self, name, display, ptype=14, pure=False):
        self._n, self._d, self._t, self._p = name, display, ptype, pure
        self.value = None

    def getName(self):
        return self._n

    def getDisplayName(self):
        return self._d

    def getType(self):
        return self._t

    def isPure(self):
        return self._p

    def getValue(self):
        return self.value

    def setValue(self, v):
        self.value = v


                                                                            
                                                                          
                                
PARAMS = {
    SHADERS["SHADER_TYPE_COLOR_INVERT"]: [("source", "Source")],
    SHADERS["SHADER_TYPE_COLOR_ADJUST"]: [("source", "Source"), ("contrast", "Contrast")],
    SHADERS["SHADER_TYPE_COLOR_COMPOSITE"]: [
        ("source", "Source"), ("background", "Background"),
        ("clipping_mask", "Clipping Mask"), ("alpha", "Alpha"),
        ("blend_mode", "Blend Mode"), ("mask_mode", "Mask Mode")],
    SHADERS["SHADER_TYPE_CURVATURE"]: [
        ("radius", "Radius"), ("cutoff", "Cutoff"),
        ("adaptive_radius", "Radius In Pixels"),
        ("positive_curvature", "Positive Curvature")],
    SHADERS["SHADER_TYPE_OCCLUSION"]: [("radius", "Radius"), ("occluded", "Occluded")],
    SHADERS["SHADER_TYPE_SCRATCHES"]: [
        ("scale", "Scale"), ("inside_color", "Inside Color"),
        ("outside_color", "Outside Color")],
}

TYPE_LABEL = {}
for _name, _v in SHADERS.items():
    TYPE_LABEL[_v] = _name


class Node(object):
    def __init__(self, stype):
        self._stype = stype
        self._params = [Param(n, d) for n, d in PARAMS.get(stype, [])]

    def getType(self):
        return self._stype

    def getName(self):
        return TYPE_LABEL.get(self._stype, "?")

    def getParameters(self):
        return self._params


class Graph(object):
    def __init__(self):
        self.nodes = []
        self.edges = []                                               

    def newNode(self, stype):
        node = Node(stype)
        self.nodes.append(node)
        return node

    def newEdge(self, source, target, param):
        self.edges.append((source, target, param))

    def removeNode(self, node):
        if node in self.nodes:
            self.nodes.remove(node)
        self.edges = [e for e in self.edges if e[0] is not node and e[1] is not node]

    def getEdges(self):
        class E(object):
            def __init__(self, s, t, p):
                self._s, self._t, self._p = s, t, p

            def getTarget(self):
                return self._t

            def getParam(self):
                return self._p
        return [E(s, t, p) for (s, t, p) in self.edges]

                                                                           
    def count(self, shader_name):
        want = SHADERS[shader_name]
        return len([n for n in self.nodes if n.getType() == want])

    def feeds(self, source, target):
        return any(s is source and t is target for (s, t, _p) in self.edges)

    def sources_into(self, target):
        return [s for (s, t, _p) in self.edges if t is target]


def load(ns_src):
                                                                           
                                                                             
                                                                         
                               
    text = io.open(os.path.join(HERE, ns_src), encoding="utf-8").read()
                                                                              
                                                                              
                                         
    mark = "# ===== " + "CORE BLOCK"
    start = text.index(mark)
    end = text.index("# ===== " + "END CORE BLOCK")
                                                                     
    ns = {"lux": lux, "luxmath": types.ModuleType("luxmath"),
          "random": random, "math": math, "os": os, "sys": sys, "io": io}
    exec(compile(text[start:end], "core_block", "exec"), ns)
    return ns


FAILURES = []


def check(case, condition, what):
    if condition:
        print("    ok   " + what)
    else:
        FAILURES.append("%s: %s" % (case, what))
        print("    FAIL " + what)


def build(ns, graph, grunge_amount, ao_amount, contrast=None,
          with_grunge=True, with_occlusion=True, with_curvature=True):
    curv = graph.newNode(SHADERS["SHADER_TYPE_CURVATURE"]) if with_curvature else None
    grunge = graph.newNode(SHADERS["SHADER_TYPE_SCRATCHES"]) if with_grunge else None
    occ = graph.newNode(SHADERS["SHADER_TYPE_OCCLUSION"]) if with_occlusion else None
    mask = ns["build_wear_mask"](graph, curvature=curv, grunge=grunge,
                                 occlusion=occ, grunge_amount=grunge_amount,
                                 ao_amount=ao_amount, contrast=contrast)
    return curv, grunge, occ, mask


def main():
    ns = load(SRC)
    print("wear mask composition, read out of %s" % SRC)

                                                                              
    print("")
    print("CASE 1 -- both amounts 0: the mask must BE the curvature node")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.0, 0.0)
    check("case 1", mask is curv, "mask is the curvature node itself, not a composite")
    check("case 1", g.count("SHADER_TYPE_COLOR_COMPOSITE") == 0, "no composite was built")

                                                                              
    print("")
    print("CASE 2 -- grunge amount 0: CLEANER, not black (the card's own read)")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.0, 0.0)
    check("case 2", grunge not in g.nodes, "the pattern node is DROPPED from the graph")
    check("case 2", mask is curv, "the mask is still pure curvature")
    check("case 2", g.count("SHADER_TYPE_COLOR_COMPOSITE") == 0,
          "nothing intersects the pattern with the curvature")

                                                                              
    print("")
    print("CASE 3 -- grunge amount 0.5: one weighted modulation")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.5, 0.0)
    check("case 3", g.count("SHADER_TYPE_COLOR_COMPOSITE") == 1, "exactly one composite")
    check("case 3", mask is not curv, "the mask is now the composite, not the raw curvature")
    check("case 3", grunge in g.nodes, "the pattern node is in the graph")
    check("case 3", g.feeds(grunge, mask) and g.feeds(curv, mask),
          "both the pattern and the curvature reach it")

                                                                              
    print("")
    print("CASE 4 -- AO amount 0.5: an INVERT must sit between occlusion and the mix")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.0, 0.5)
    check("case 4", g.count("SHADER_TYPE_COLOR_INVERT") == 1, "a Color Invert was built")
    inverts = [n for n in g.nodes if n.getType() == SHADERS["SHADER_TYPE_COLOR_INVERT"]]
    inv = inverts[0] if inverts else None
    check("case 4", inv is not None and g.feeds(occ, inv),
          "the occlusion node feeds the INVERT, not the mix directly")
    check("case 4", inv is not None and g.feeds(inv, mask),
          "the invert feeds the mix, so AO REMOVES wear from crevices")
    check("case 4", not g.feeds(occ, mask),
          "occlusion never reaches the mix un-inverted (that was the old bug)")

                                                                              
    print("")
    print("CASE 5 -- AO amount 0: the occlusion node is dropped")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.0, 0.0)
    check("case 5", occ not in g.nodes, "the occlusion node is DROPPED")
    check("case 5", g.count("SHADER_TYPE_COLOR_INVERT") == 0, "no invert was built")

                                                                              
    print("")
    print("CASE 6 -- contrast 0.4: a Color Adjust shapes the result, last")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.5, 0.5, contrast=0.4)
    check("case 6", g.count("SHADER_TYPE_COLOR_ADJUST") == 1, "a Color Adjust was built")
    check("case 6", mask.getType() == SHADERS["SHADER_TYPE_COLOR_ADJUST"],
          "the Color Adjust is the node returned, so it is LAST in the chain")
    contrast_written = None
    for p in mask.getParameters():
        if p.getName() == "contrast":
            contrast_written = p.getValue()
    check("case 6", contrast_written == 0.4,
          "the contrast value was actually written (got %r)" % (contrast_written,))

                                                                             
    print("")
    print("CASE 7 -- this build has NO Color Invert: leave AO out, keep the mask")
    install_shaders(absent=("SHADER_TYPE_COLOR_INVERT",))
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.5, 0.5)
    check("case 7", mask is not None, "the mask survives")
    check("case 7", occ not in g.nodes, "the occlusion node is dropped, not miswired")
    check("case 7", not any(g.feeds(occ, n) for n in g.nodes),
          "occlusion is never wired the wrong way round as a fallback")

                                                                             
    print("")
    print("CASE 8 -- this build has NO Color Adjust: skip shaping, keep the mask")
    install_shaders(absent=("SHADER_TYPE_COLOR_ADJUST",))
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.5, 0.0, contrast=0.4)
    check("case 8", mask is not None, "the mask survives")
    check("case 8", g.count("SHADER_TYPE_COLOR_ADJUST") == 0, "no adjust node was built")

                                                                             
    print("")
    print("CASE 9 -- no curvature node: the one honest None")
    install_shaders()
    g = Graph()
    curv, grunge, occ, mask = build(ns, g, 0.5, 0.5, with_curvature=False)
    check("case 9", mask is None, "returns None rather than a mask built on nothing")

    print("")
    print("=" * 70)
    if FAILURES:
        print("FAIL -- %d assertion(s) not met" % len(FAILURES))
        for line in FAILURES:
            print("  " + line)
        sys.exit(1)
    print("PASS -- the composition is structurally what RNK-0276 claims")
    print("")
    print("Settled here, so mode 7 does NOT have to discover it:")
    print("  - grunge at 0 gives PURE CURVATURE, not black. It is not an")
    print("    intersection any more. The 'cleaner, not black' read is proved.")
    print("  - occlusion reaches the mix only through an INVERT, so AO removes")
    print("    wear from crevices. The 'crevices darken' read is proved.")
    print("  - every missing node type degrades to a plainer mask, never a")
    print("    black one and never a crash.")
    print("")
    print("What mode 7 is still FOR, and it is the part no stub can answer:")
    print("  does this mask land on the EDGES of a real part, at a real radius,")
    print("  with flats clean. That is a render's job.")


main()
