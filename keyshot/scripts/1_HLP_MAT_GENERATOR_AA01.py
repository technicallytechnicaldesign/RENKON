# -*- coding: utf-8 -*-
# AUTHOR claude-subagent
# REV AA01
# HEADLESS COMPLIANT
# Procedural material *variant* generator: a dialog of independently
# toggleable feature layers (fine noise, scratches, spots, cellular, rounded
# edges, fractal/occlusion roughness, colour gradient) combined onto a chosen
# base (metal/plastic) at a chosen wear level, each build auto-named
# MAT-<TYPE>-<WEAR>-<hex>. Sits in the 1_ helper stage as the material-
# *authoring* member of the MAT family, alongside 1_HLP_MAT_PREFLIGHT
# (coverage QC) and 1_HLP_MAT_LOOKUP (Creo -> KeyShot name mapping).
#
# Confirmed layers (per KeyShot's scripting docs): Fine Noise, Scratches,
# Rounded Edges, Spots, Fractal Noise, Occlusion. Experimental (getattr-
# guarded — skip with a console [warn] if the lux constant is absent on this
# build): Cellular, Colour Gradient. Full confirmed-vs-experimental notes and
# the Thin-Film removal rationale are in the module docstring below.

"""
KeyShot Procedural Material Generator
======================================

Pivoted from a single fixed recipe into a variant generator: a dialog full
of tick-box feature layers, each independently toggleable, combined onto a
chosen base material (metal/plastic) at a chosen wear level. Every generated
material gets a random, unique, technical-style name (e.g. MAT-ALU-LGT-7F3A2C)
rather than one you have to type.

Run inside the KeyShot Scripting Console, or via `keyshot -script` headless
(dialog auto-skips headless -> DEFAULT_OPTIONS is used instead).

--------------------------------------------------------------------------
CONFIRMED vs EXPERIMENTAL LAYERS
--------------------------------------------------------------------------
Confirmed against KeyShot's own scripting docs (safe bets):
  Fine Noise, Scratches, Rounded Edges, Spots, Fractal Noise, Occlusion

Experimental (constant name is a reasonable guess, not confirmed to exist
in every KeyShot version) — these use getattr() and skip cleanly with a
console warning if unavailable, rather than crashing:
  Cellular, Color Gradient, Thin Film

If a toggle you enabled doesn't show up in the final material, check the
console for a "[warn] ... not available in this KeyShot version" line —
that tells you definitively rather than leaving you guessing.
"""

import lux
import random
import math

# --------------------------------------------------------------------------
# Debug / diagnostics
# --------------------------------------------------------------------------

DEBUG = True  # prints real parameters for each node as it's created

# --------------------------------------------------------------------------
# Material type presets
# --------------------------------------------------------------------------

MATERIAL_TYPES = {
    "Aluminum (brushed metal)": (lambda: lux.SHADER_TYPE_METAL, (0.72, 0.73, 0.75), 0.18),
    "Steel (metal)":            (lambda: lux.SHADER_TYPE_METAL, (0.55, 0.56, 0.58), 0.25),
    "Chrome (metal)":           (lambda: lux.SHADER_TYPE_METAL, (0.90, 0.90, 0.92), 0.05),
    "ABS Plastic":              (lambda: lux.SHADER_TYPE_PLASTIC, (0.15, 0.15, 0.16), 0.35),
}
MATERIAL_TYPE_ORDER = list(MATERIAL_TYPES.keys())
TYPE_ABBR = {"Aluminum (brushed metal)": "ALU", "Steel (metal)": "STL",
             "Chrome (metal)": "CHR", "ABS Plastic": "ABS"}

WEAR_PRESETS = {"Pristine": 0.3, "Light Wear": 1.0, "Moderate Wear": 2.5, "Heavy Wear": 5.0}
WEAR_ORDER = list(WEAR_PRESETS.keys())
WEAR_ABBR = {"Pristine": "PRI", "Light Wear": "LGT", "Moderate Wear": "MOD", "Heavy Wear": "HVY"}

# Subtle base amplitudes at Light Wear (1.0x) — learned last round that
# these read as much stronger visually than the raw [0,1] numbers suggest.
BASE = {
    "fine_noise_scale":    0.15,
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

# "Loud" bump layers actually distort the surface and stack additively when
# combined — verified against the confirmed research: KeyShot's own manual
# describes Cellular as capable of "cracked surfaces, hammered metal", i.e.
# a strong effect even alone. Rather than let any combination of these pile
# up unbounded, LOUD_BUMP_FEATURES are capped (see randomize_feature_flags
# and the damping factor in build_material) so total surface energy stays
# roughly constant regardless of how many of them are active at once.
# Fine noise is excluded from the cap — it's deliberately subtle by design.
LOUD_BUMP_FEATURES = ["add_scratches", "add_rounded_edges", "add_spots", "add_cellular"]
MAX_SIMULTANEOUS_LOUD_LAYERS = 2

# Feature keys, dialog labels, and (for randomize mode) inclusion probability.
# NOTE: Thin Film was removed. Research turned up that it's a full KeyShot
# *material type* (its own iridescent BRDF, like Metal or Plastic) — not a
# texture with a bump/height output. Wiring it into a bump input slot, as
# the previous version of this script did, is a category error with
# undefined behavior — the leading suspect for "wild" results. Bringing
# Thin Film back properly would mean offering it as an alternate base
# material (MATERIAL_TYPES entry), not a layer toggle, which is a bigger
# change than this fix.
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
FEATURE_PROBS = {  # used only when "Randomize features" is checked
    "add_fine_noise": 0.85, "add_scratches": 0.55, "add_rounded_edges": 0.35,
    "add_spots": 0.25, "add_cellular": 0.15, "add_fractal_roughness": 0.6,
    "add_occlusion_roughness": 0.25, "add_color_gradient": 0.12,
}

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
    "randomize_features": False,
    "name_filter": "",
}


def clamp01(v):
    return max(0.0, min(1.0, v))


def random_suffix(n=6):
    return "".join(random.choice("0123456789ABCDEF") for _ in range(n))


def resolve_filter(value, sentinel="ALL"):
    """Normalize a name-filter dialog field: None, '', or the sentinel all
    mean 'no filter' (match everything)."""
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


def resolve_material_name(prefix, material_type, wear_level):
    base = (prefix or "MAT").strip().upper().replace(" ", "_") or "MAT"
    type_code = TYPE_ABBR.get(material_type, "GEN")
    wear_code = WEAR_ABBR.get(wear_level, "GEN")
    return f"{base}-{type_code}-{wear_code}-{random_suffix()}"


def randomize_feature_flags():
    """Randomize, but cap how many 'loud' bump layers can stack at once —
    independently rolling each one (the previous approach) could enable
    all four simultaneously, which compounds into chaotic surface noise
    even though each layer alone is tuned to be subtle."""
    flags = {k: False for k in FEATURE_KEYS}
    flags["add_fine_noise"] = random.random() < FEATURE_PROBS["add_fine_noise"]

    loud_candidates = [k for k in LOUD_BUMP_FEATURES if random.random() < FEATURE_PROBS[k]]
    random.shuffle(loud_candidates)
    for k in loud_candidates[:MAX_SIMULTANEOUS_LOUD_LAYERS]:
        flags[k] = True

    flags["add_fractal_roughness"] = random.random() < FEATURE_PROBS["add_fractal_roughness"]
    flags["add_occlusion_roughness"] = random.random() < FEATURE_PROBS["add_occlusion_roughness"]
    flags["add_color_gradient"] = random.random() < FEATURE_PROBS["add_color_gradient"]

    # don't fight over the single roughness-driver slot
    if flags["add_fractal_roughness"] and flags["add_occlusion_roughness"]:
        if random.random() < 0.5:
            flags["add_occlusion_roughness"] = False
        else:
            flags["add_fractal_roughness"] = False
    return flags


# --------------------------------------------------------------------------
# Options dialog (GUI only — auto-skipped in headless mode)
# --------------------------------------------------------------------------

def get_options():
    if lux.isHeadless():
        print("Headless session detected — skipping dialog, using DEFAULT_OPTIONS.")
        return dict(DEFAULT_OPTIONS)

    values = [
        ("name_prefix", lux.DIALOG_TEXT, "Name prefix (blank = 'MAT'):", DEFAULT_OPTIONS["name_prefix"]),
        ("material_type", lux.DIALOG_ITEM, "Material type:",
         DEFAULT_OPTIONS["material_type"], MATERIAL_TYPE_ORDER),
        ("wear_level", lux.DIALOG_ITEM, "Wear level:", DEFAULT_OPTIONS["wear_level"], WEAR_ORDER),
        ("wear_multiplier", lux.DIALOG_DOUBLE, "Wear fine-tune (x):",
         DEFAULT_OPTIONS["wear_multiplier"], (0.0, 3.0)),
        (lux.DIALOG_LABEL, "-- surface detail --"),
    ]
    for key in ["add_fine_noise", "add_scratches", "add_rounded_edges", "add_spots", "add_cellular"]:
        values.append((key, lux.DIALOG_CHECK, FEATURE_LABELS[key], DEFAULT_OPTIONS[key]))
    values.append((lux.DIALOG_LABEL, "-- roughness / color drivers (pick one of each pair) --"))
    for key in ["add_fractal_roughness", "add_occlusion_roughness", "add_color_gradient"]:
        values.append((key, lux.DIALOG_CHECK, FEATURE_LABELS[key], DEFAULT_OPTIONS[key]))
    values.append((lux.DIALOG_LABEL, "-- generation --"))
    values.append(("randomize_features", lux.DIALOG_CHECK,
                    "Randomize features instead (ignores checkboxes above)",
                    DEFAULT_OPTIONS["randomize_features"]))
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
        if isinstance(v, (list, tuple)):
            for candidate in reversed(v):
                if candidate in valid:
                    return candidate
            return v[-1]
        return v

    opts["material_type"] = norm_item(opts.get("material_type"), MATERIAL_TYPE_ORDER)
    opts["wear_level"] = norm_item(opts.get("wear_level"), WEAR_ORDER)
    return opts


# --------------------------------------------------------------------------
# Node/parameter helpers (all non-fatal)
# --------------------------------------------------------------------------

def dump_node(node, label=""):
    try:
        node_label = label or node.getType()
    except Exception:
        node_label = label or "?"
    print(f"--- {node_label} ---")
    try:
        for p in node.getParameters():
            print(f"    name={p.getName()!r:25} display={p.getDisplayName()!r:25} "
                  f"type={p.getType()} pure={p.isPure()}")
    except Exception as e:
        print(f"    [warn] couldn't list parameters: {e}")


def new_node(graph, shader_type, label=""):
    node = graph.newNode(shader_type)
    if DEBUG:
        dump_node(node, label or shader_type)
    return node


def try_new_node(graph, attr_name, label):
    """Resolve lux.<attr_name> safely; create the node if it exists."""
    shader_type = getattr(lux, attr_name, None)
    if shader_type is None:
        print(f"  [warn] lux.{attr_name} not available in this KeyShot version — skipping {label}")
        return None
    try:
        return new_node(graph, shader_type, label)
    except Exception as e:
        print(f"  [warn] couldn't create {label} ({attr_name}): {e} — skipping")
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
    return [p.getName() for p in node.getParameters() if p.getType() == ptype]


def set_display(node, keywords, value, ptype=None):
    label = keywords if isinstance(keywords, str) else "/".join(keywords)
    p = find_param(node, keywords, ptype)
    if p is None:
        print(f"  [warn] no parameter matching '{label}' on this node")
        return False
    if p.isPure():
        print(f"  [warn] '{label}' is a connection-only (pure) parameter")
        return False
    try:
        p.setValue(value)
        return True
    except Exception as e:
        print(f"  [warn] couldn't set '{label}'={value!r}: {e} (left at default)")
        return False


def safe_edge(graph, source, target, param, label=""):
    try:
        graph.newEdge(source=source, target=target, param=param)
        return True
    except Exception as e:
        print(f"  [warn] couldn't wire {label or param}: {e}")
        return False


def combine_bump_sources(graph, sources):
    """Chain N bump-domain nodes together pairwise via Bump Add. Non-fatal:
    if a chain link fails, returns the best combination achieved so far."""
    sources = [s for s in sources if s is not None]
    if not sources:
        return None
    if len(sources) == 1:
        return sources[0]
    current = sources[0]
    for nxt in sources[1:]:
        bump_add = try_new_node(graph, "SHADER_TYPE_BUMP_ADD", "Bump Add")
        if bump_add is None:
            print("  [warn] stopping bump combination early — Bump Add unavailable")
            return current
        slots = connection_param_names(bump_add, lux.PARAMETER_TYPE_SHADERBUMP)
        if len(slots) < 2:
            print(f"  [warn] Bump Add missing expected 2 inputs (found {slots}) — stopping chain")
            return current
        ok1 = safe_edge(graph, source=current, target=bump_add, param=slots[0], label="bump chain a")
        ok2 = safe_edge(graph, source=nxt, target=bump_add, param=slots[1], label="bump chain b")
        current = bump_add if (ok1 and ok2) else current
    return current


def wire_scalar_driver(graph, texture_node, base_node, keywords, label):
    p = find_param(base_node, keywords)
    if p is None:
        print(f"  [warn] no {label}-like parameter found on base material — skipping")
        return False
    ok = safe_edge(graph, source=texture_node, target=base_node, param=p.getName(),
                    label=f"-> base.{label}")
    if not ok:
        print(f"  [info] {label} driver skipped — static default still applies")
    return ok


# --------------------------------------------------------------------------
# Layer builders — each returns a node (bump-domain) or bool (scalar drivers)
# --------------------------------------------------------------------------

def add_fine_noise_bump(graph):
    n = try_new_node(graph, "SHADER_TYPE_NOISE_TEXTURE", "Fine Noise")
    if n:
        set_display(n, ["scale"], BASE["fine_noise_scale"])
    return n


def add_scratches_bump(graph, wear_mult, damping=1.0):
    n = try_new_node(graph, "SHADER_TYPE_SCRATCHES", "Scratches")
    if n:
        set_display(n, ["bump height"], clamp01(BASE["scratch_bump_height"] * wear_mult * damping))
        set_display(n, ["density"], clamp01(BASE["scratch_density"] * wear_mult))
        set_display(n, ["size"], clamp01(BASE["scratch_size"] * wear_mult))
        set_display(n, ["directional noise"], BASE["scratch_dir_noise"])
        set_display(n, ["noise"], BASE["scratch_noise"])
        set_display(n, ["levels"], BASE["scratch_levels"])
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
        set_display(n, ["size"], clamp01(BASE["spots_size"] * wear_mult))
    return n


def add_cellular_bump(graph, wear_mult, damping=1.0):
    # KeyShot's own manual describes this as capable of "cracked surfaces,
    # hammered metal" — a strong effect even alone, hence the extra 0.6x.
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
    # Nudge toward tasteful, near-neutral tones close to the base material
    # color rather than leaving KeyShot's own default gradient stops (unknown,
    # possibly high-contrast) in place — this was the leading suspect for
    # "wild" output. Best-effort: this node's UI is a draggable color bar,
    # which may not expose simple named color parameters the way other
    # nodes do. If no match is found, that's reported rather than assumed.
    light = tuple(clamp01(c * 1.25 + 0.05) for c in base_color)
    dark = tuple(clamp01(c * 0.6) for c in base_color)
    ok1 = set_display(n, ["color 1", "start color", "color a"], light, ptype=lux.PARAMETER_TYPE_COLOR)
    ok2 = set_display(n, ["color 2", "end color", "color b"], dark, ptype=lux.PARAMETER_TYPE_COLOR)
    if not (ok1 or ok2):
        print("  [warn] couldn't find Color Gradient's color-stop parameters — it will use "
              "KeyShot's own default gradient colors, which may look more extreme than intended")
    return wire_scalar_driver(graph, n, base_node, ["color", "tint", "reflectance"], "color")


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def build_material(opts):
    material_type = opts.get("material_type", DEFAULT_OPTIONS["material_type"])
    wear_level = opts.get("wear_level", DEFAULT_OPTIONS["wear_level"])
    wear_mult = WEAR_PRESETS.get(wear_level, 1.0) * float(opts.get("wear_multiplier", 1.0))

    features = {k: bool(opts.get(k, False)) for k in FEATURE_KEYS}
    if opts.get("randomize_features"):
        features = randomize_feature_flags()

    shader_fn, base_color, base_roughness = MATERIAL_TYPES.get(
        material_type, MATERIAL_TYPES[DEFAULT_OPTIONS["material_type"]])
    shader_type = shader_fn()

    name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level)

    print(f"lux.isHeadless() = {lux.isHeadless()}")
    print(f"Building '{name}' | type={material_type} | wear={wear_level} (x{wear_mult:.2f})")
    active = [FEATURE_LABELS[k] for k, v in features.items() if v]
    print(f"Features: {', '.join(active) if active else '(none)'}")

    # Damp each loud bump layer's amplitude by how many are stacked, so
    # total surface energy stays roughly bounded regardless of how many
    # ended up active — this is what actually stops combinations from
    # compounding into chaotic noise.
    active_loud_count = sum(1 for k in LOUD_BUMP_FEATURES if features.get(k))
    damping = 1.0 / math.sqrt(max(1, active_loud_count))
    if active_loud_count > 1:
        print(f"  {active_loud_count} loud bump layers active — damping each by {damping:.2f}x")

    for attempt in range(5):
        try:
            lux.createSceneMaterial(name)
            break
        except Exception as e:
            print(f"  [warn] couldn't create material '{name}': {e} — trying a new random name")
            name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level)
    else:
        raise RuntimeError("Couldn't create a scene material after 5 attempts")

    graph = lux.getMaterialGraph(name)
    root = graph.getRoot()
    if DEBUG:
        dump_node(root, "Root")

    base_node = new_node(graph, shader_type, material_type)
    safe_edge(graph, source=base_node, target=root, param="surface", label="base -> root.surface")
    set_display(base_node, ["color", "tint", "reflectance"], base_color, ptype=lux.PARAMETER_TYPE_COLOR)
    set_display(base_node, ["roughness"], base_roughness)

    # --- bump-domain layers, combined into one bump input -----------------
    bump_sources = []
    if features["add_fine_noise"]:
        bump_sources.append(add_fine_noise_bump(graph))
    if features["add_scratches"]:
        bump_sources.append(add_scratches_bump(graph, wear_mult, damping))
    if features["add_rounded_edges"]:
        bump_sources.append(add_rounded_edges_bump(graph, wear_mult, damping))
    if features["add_spots"]:
        bump_sources.append(add_spots_bump(graph, wear_mult, damping))
    if features["add_cellular"]:
        bump_sources.append(add_cellular_bump(graph, wear_mult, damping))

    combined_bump = combine_bump_sources(graph, bump_sources)
    if combined_bump is not None:
        base_bump_slots = connection_param_names(base_node, lux.PARAMETER_TYPE_SHADERBUMP)
        if base_bump_slots:
            safe_edge(graph, source=combined_bump, target=base_node, param=base_bump_slots[0],
                      label="combined bump -> base.bump")
        else:
            print("  [warn] base material has no bump input")

    # --- roughness-domain: first enabled driver wins -----------------------
    if features["add_fractal_roughness"]:
        add_fractal_roughness(graph, base_node)
    elif features["add_occlusion_roughness"]:
        add_occlusion_roughness(graph, base_node)

    # --- color-domain: single driver ----------------------------------------
    if features["add_color_gradient"]:
        add_color_gradient(graph, base_node, base_color)

    print(f"Built material graph: {name}")
    return graph, name


def apply_material_to_parts(name, name_filter=None):
    """Apply `name` across the scene. Deliberately does NOT pre-filter to
    isObject() — KeyShot's own docs confirm Group nodes accept setMaterial()
    and cascade it to their children, so excluding Groups (as an earlier
    version of this function did) silently skipped entire assemblies. Instead
    every node is tried; only genuine failures (cameras, lights, etc.) are
    skipped, based on what setMaterial() itself reports."""
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
                print(f"  [warn] setMaterial failed (kind={kind}): {e}")
        if ok:
            applied += 1
            if DEBUG:
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
        else:
            skipped += 1
    suffix = f" matching {name_filter!r}" if name_filter else ""
    print(f"Applied '{name}' to {applied} node(s){suffix}, skipped {skipped}")
    if DEBUG and applied:
        print(f"  applied to node kinds: {kind_counts}")
    if applied == 0 and DEBUG:
        print("  [info] nothing matched — run with DEBUG=True and check the node "
              "kinds above, or confirm the scene actually has geometry loaded")
    return applied


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled — nothing built.")
    else:
        graph, material_name = build_material(options)
        apply_material_to_parts(material_name, name_filter=resolve_filter(options.get("name_filter")))
