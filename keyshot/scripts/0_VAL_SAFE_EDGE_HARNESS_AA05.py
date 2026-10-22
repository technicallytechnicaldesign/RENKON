                       
                                   
          
                                                                            
 
                                                                              
                                                                           
                                                                        
 
                                                                            
                                                                         
 
                                                                              
                                                                            
                                                                            
                                                                     
                                                                           
 
                                                                               

import io
import os
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
lux.PARAMETER_TYPE_INTEGER = 6
lux.PARAMETER_TYPE_BOOLEAN = 2
lux.PARAMETER_TYPE_STRING = 9
lux.PARAMETER_TYPE_COLOR = 13
lux.PARAMETER_TYPE_SHADERBUMP = 20
lux.SHADER_TYPE_PAINT = 31
lux.SHADER_TYPE_TEXTURE_MAP = 55
sys.modules["lux"] = lux


def load_core_helpers():
                                                                                 
    path = os.path.join(HERE, SRC)
    text = io.open(path, encoding="utf-8").read()
    start = text.index("def _build_param_type_names()")
    end = text.index("def combine_bump_sources(")
    ns = {"lux": lux}
    exec(compile(text[start:end], "core_block_excerpt", "exec"), ns)
    return ns


class Param(object):
    def __init__(self, name, ptype, pure=False):
        self._n, self._t, self._p = name, ptype, pure

    def getName(self):
        return self._n

    def getType(self):
        return self._t

    def isPure(self):
        return self._p


class Node(object):
    def __init__(self, name, params, stype=lux.SHADER_TYPE_PAINT):
        self._name, self._params, self._stype = name, params, stype

    def getName(self):
        return self._name

    def getType(self):
        return self._stype

    def getParameters(self):
        return self._params



class DictTypeNode(Node):
                                                                            
                                                                     
                 

    def getType(self):
        return {"name": "Paint", "id": 31, "category": "shader"}


class NoNameNode(object):
                                                                               

    def __init__(self, params):
        self._params = params

    def getType(self):
        return {"name": "Curvature", "id": 10}

    def getParameters(self):
        return self._params


class Edge(object):
    def __init__(self, target, param):
        self._t, self._p = target, param

    def getTarget(self):
        return self._t

    def getParam(self):
        return self._p


class EdgeHandle(object):
                                                                            
                                                                            
                                                                           
                                               

    def __init__(self, edge_id):
        self.id = edge_id


class Graph(object):
                                                                              
                                                                                
                                                                   

    def __init__(self, readback=True, raises=False, accepts=True, handle=False,
                 from_id=False):
        self._edges = []
        self._raises = raises
        self._accepts = accepts
        self._handle = handle
        self._next_id = 1
        if readback:
            self.getEdges = lambda: list(self._edges)
        if from_id:
            self.getEdgeFromID = lambda h: self._edges[0] if self._edges else None

    def newEdge(self, source, target, param):
        if self._raises:
            raise RuntimeError("Could not create requested edge!")
        if self._accepts:
            self._edges.append(Edge(target, param))
        if self._handle:
            handle = EdgeHandle(self._next_id)
            self._next_id += 1
            return handle
        return None


FAILURES = []


def expect(case, log, must_contain, must_not_contain=()):
                                                                              
    text = "\n".join(log)
    for phrase in must_contain:
        if phrase not in text:
            FAILURES.append("%s: missing %r" % (case, phrase))
    for phrase in must_not_contain:
        if phrase in text:
            FAILURES.append("%s: should not say %r" % (case, phrase))


class Capture(object):
                                                                                  

    def __init__(self):
        self.lines = []
        self._real = sys.stdout

    def write(self, text):
        self.lines.append(text)
        self._real.write(text)

    def flush(self):
        self._real.flush()


                                                                             
                                                                            
                       
KEEP = object()


def run_case(ns, source, title, graph, target, param, label, reset_probe=KEEP,
             reset_edge_probe=False):
    print("")
    print(title)
    if reset_probe is not KEEP:
        ns["_EDGE_READBACK_API"][0] = reset_probe
                                                                            
                                                                            
                          
    if reset_edge_probe:
        ns["_NEW_EDGE_PROBED"][0] = False
    cap = Capture()
    old = sys.stdout
    sys.stdout = cap
    try:
        result = ns["safe_edge"](graph, source, target, param, label=label)
    finally:
        sys.stdout = old
    print("  returned: %s" % result)
    return "".join(cap.lines).split("\n"), result


def main():
    ns = load_core_helpers()

    SRC_NODE = Node("Composite", [], stype=lux.SHADER_TYPE_TEXTURE_MAP)
    BASE = Node("Paint base", [
        Param("color", 14),                                             
        Param("roughness", 4),                                                        
        Param("clipping_mask", 14, pure=True),
    ], stype=lux.SHADER_TYPE_PAINT)
    TEX = Node("Scratches", [
        Param("bump_height", 4),                                                           
    ], stype=lux.SHADER_TYPE_TEXTURE_MAP)

    print("type naming: %s | %s | %s" % (
        ns["param_type_name"](4), ns["param_type_name"](14), ns["param_type_name"](None)))

    log, ok = run_case(ns, SRC_NODE, "CASE 1 -- connection target, build HAS read-back",
                       Graph(readback=True), BASE, "color",
                       "colour stack -> base colour", reset_probe=None)
    expect("case 1", log, ["WIRED", "PAINT.color"], ["UNVERIFIED"])

    log, ok = run_case(ns, SRC_NODE, "CASE 2 -- connection target, NO read-back",
                       Graph(readback=False), BASE, "color",
                       "colour stack -> base colour", reset_probe=None)
    expect("case 2", log, ["CALL OK, UNVERIFIED", "PAINT.color"], ["WIRED --"])

    log, ok = run_case(ns, SRC_NODE, "CASE 3 -- scalar target, verified by read-back",
                       Graph(readback=True), BASE, "roughness",
                       "roughness stack -> base roughness", reset_probe=None)
    expect("case 3", log, ["WIRED", "PAINT.roughness", "4 (FLOAT)"], ["note: that target"])

    log, ok = run_case(ns, SRC_NODE, "CASE 4 -- newEdge raises",
                       Graph(readback=True, raises=True), BASE, "color",
                       "colour stack -> base colour", reset_probe=None)
    expect("case 4", log, ["couldn't wire", "PAINT.color"], ["WIRED"])
    if ok is not False:
        FAILURES.append("case 4: a raising newEdge must return False")

    log, ok = run_case(ns, SRC_NODE, "CASE 5 -- read-back works, the edge is genuinely absent",
                       Graph(readback=True, accepts=False), BASE, "color",
                       "colour stack -> base colour", reset_probe=None)
    expect("case 5", log, ["NO edge reads back", "PAINT.color"], ["WIRED"])

    log, ok = run_case(ns, SRC_NODE, "CASE 6 -- scalar target AND no read-back",
                       Graph(readback=False), BASE, "roughness",
                       "roughness stack -> base roughness", reset_probe=None)
    expect("case 6", log, ["CALL OK, UNVERIFIED", "PAINT.roughness", "note: that target"])

    log, ok = run_case(ns, SRC_NODE, "CASE 7 -- the same scalar on a TEXTURE node",
                       Graph(readback=False), TEX, "bump_height",
                       "mask -> scratches.bump_height", reset_probe=False)
    expect("case 7", log, ["TEXTURE_MAP.bump_height", "note: that target"])


                                                                               
                                                                              
                                                                
                                                                        
    print("")
    print("CASE 8 -- node.getType() returns a DICT (the real build's shape)")
    ns["_EDGE_READBACK_API"][0] = False
    dict_node = DictTypeNode("Paint base", [Param("color", 14), Param("roughness", 4)])
    log, ok = run_case(ns, SRC_NODE, "  (running)", Graph(readback=False), dict_node,
                       "color", "colour stack -> base colour", reset_probe=False)
    expect("case 8", log, ["CALL OK, UNVERIFIED", "Paint.color"], ["Traceback"])
    if ok is not True:
        FAILURES.append("case 8: an unhashable node type must not break the wire")

    print("")
    print("CASE 9 -- a node with NO getName: identity must be honest, not guessed")
    anon_a = NoNameNode([Param("color", 14)])
    anon_b = NoNameNode([Param("color", 14)])
    ident = ns["_node_identity"]
    if ident(anon_a) == ident(anon_b):
        FAILURES.append("case 9: two DIFFERENT nameless nodes must not share an identity")
        print("    FAIL two different nameless nodes compare equal")
    else:
        print("    ok   two different nameless nodes have different identities")
    if ident(anon_a) != ident(anon_a):
        FAILURES.append("case 9: a node must equal itself")
        print("    FAIL a node does not equal itself")
    else:
        print("    ok   a node equals itself")
                                                                               
                                                                              
                                                                    
    log, ok = run_case(ns, SRC_NODE,
                       "CASE 10 -- newEdge hands back a handle, getEdgeFromID takes it",
                       Graph(readback=False, handle=True, from_id=True), BASE,
                       "color", "colour stack -> base colour", reset_probe=False,
                       reset_edge_probe=True)
    expect("case 10", log,
           ["[probe] newEdge returned", "it OFFERS", "getEdgeFromID(<that value>) returned"],
           ["FAIL as predicted"])
    if ok is not True:
        FAILURES.append("case 10: the probe must not change what safe_edge returns")

    log, ok = run_case(ns, SRC_NODE,
                       "CASE 11 -- newEdge returns None: the closed-route answer",
                       Graph(readback=False), BASE, "color",
                       "colour stack -> base colour", reset_probe=False,
                       reset_edge_probe=True)
                                                                      
                                                                      
                                                       
    expect("case 11", log, ["FAIL as predicted", "this route to checking a wire is closed"],
           ["it OFFERS"])

    log, ok = run_case(ns, SRC_NODE,
                       "CASE 12 -- the probe is once per run, not once per wire",
                       Graph(readback=False, handle=True, from_id=True), BASE,
                       "color", "colour stack -> base colour", reset_probe=False)
    expect("case 12", log, [], ["[probe]"])

    print("")
    print("=" * 70)
    if FAILURES:
        print("FAIL -- %d expectation(s) not met" % len(FAILURES))
        for line in FAILURES:
            print("  " + line)
        sys.exit(1)
    print("PASS -- all 12 cases report what they should")
    print("The read that matters: case 3 says PAINT.roughness and case 7 says")
    print("TEXTURE_MAP.bump_height. Same param type, opposite M5 verdicts, and the")
    print("log now names the half that decides it.")


main()
