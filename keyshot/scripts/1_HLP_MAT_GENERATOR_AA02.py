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
# !! KEYSHOT PYTHON CONSTRAINT -- READ BEFORE EDITING !!
# KeyShot's embedded interpreter here predates f-strings (Python < 3.6) and its
# console is ASCII-sensitive. Keep this file f-string-FREE (use "{0}".format())
# and ASCII-ONLY (use -- not an em-dash). An f-string or a stray Unicode char
# makes the whole script fail to load in the Scripting Console. Every sibling
# script that loads cleanly obeys this; the ones that don't (this file's old
# revision, the 2b_ANI_* set) are exactly the ones that wouldn't load.
#
# Confirmed layers (per KeyShot's scripting docs): Fine Noise, Scratches,
# Rounded Edges, Spots, Fractal Noise, Occlusion. Experimental (getattr-
# guarded -- skip with a console [warn] if the lux constant is absent on this
# build): Cellular, Colour Gradient. Masking (targeted wear) uses Curvature +
# Occlusion + Color Composite (ids confirmed in the 11.0 lux ref); the exact
# input-slot wiring is probe-and-confirm -- masking degrades to unmasked on any
# wiring failure, so it can never break the base material. See MWR-9C4E21
# (scripts/research/MASKED_WEAR_RESEARCH.md). Fingerprints (raster) are a
# planned follow-on.

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
in every KeyShot version) -- these use getattr() and skip cleanly with a
console warning if unavailable, rather than crashing:
  Cellular, Color Gradient, Thin Film

Masking / targeted wear (opt-in, off by default):
  Scratches-to-edges (Curvature mask) and Spots-to-cavities (Occlusion mask),
  composited via Color Composite (alpha = mask). Node ids are confirmed; the
  exact input-slot names are discovered at run time (DEBUG dumps them), and
  any wiring failure falls back to the unmasked effect.

If a toggle you enabled doesn't show up in the final material, check the
console for a "[warn] ... not available in this KeyShot version" line --
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

# Subtle base amplitudes at Light Wear (1.0x) -- learned last round that
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
# combined -- verified against the confirmed research: KeyShot's own manual
# describes Cellular as capable of "cracked surfaces, hammered metal", i.e.
# a strong effect even alone. Rather than let any combination of these pile
# up unbounded, LOUD_BUMP_FEATURES are capped (see randomize_feature_flags
# and the damping factor in build_material) so total surface energy stays
# roughly constant regardless of how many of them are active at once.
# Fine noise is excluded from the cap -- it's deliberately subtle by design.
LOUD_BUMP_FEATURES = ["add_scratches", "add_rounded_edges", "add_spots", "add_cellular"]
MAX_SIMULTANEOUS_LOUD_LAYERS = 2

# Feature keys, dialog labels, and (for randomize mode) inclusion probability.
# NOTE: Thin Film was removed. Research turned up that it's a full KeyShot
# *material type* (its own iridescent BRDF, like Metal or Plastic) -- not a
# texture with a bump/height output. Wiring it into a bump input slot, as
# the previous version of this script did, is a category error with
# undefined behavior -- the leading suspect for "wild" results. Bringing
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

# Masking modifiers -- separate from FEATURE_KEYS so they never get swept into
# the loud-layer cap or randomize logic. Opt-in, off by default; read straight
# from opts in build_material.
MASK_KEYS = ["mask_scratches_to_edges", "mask_spots_to_cavities"]

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
    "mask_scratches_to_edges": False,
    "mask_spots_to_cavities": False,
    "randomize_features": False,
    "random_seed": "",
    "name_filter": "",
}


def clamp01(v):
    return max(0.0, min(1.0, v))


# Material names must stay globally unique even when a run is seeded for a
# reproducible *look* (see _apply_seed), so the ID suffix is drawn from a
# dedicated, never-seeded RNG. This also keeps the createSceneMaterial
# collision-retry loop from regenerating the same name five times in a row.
_name_rng = random.Random()


def random_suffix(n=6):
    return "".join(_name_rng.choice("0123456789ABCDEF") for _ in range(n))


def resolve_filter(value, sentinel="ALL"):
    """Normalize a name-filter dialog field: None, '', or the sentinel all
    mean 'no filter' (match everything)."""
    v = (value or "").strip()
    return None if (not v or v.upper() == sentinel) else v


def resolve_material_name(prefix, material_type, wear_level):
    base = (prefix or "MAT").strip().upper().replace(" ", "_") or "MAT"
    type_code = TYPE_ABBR.get(material_type, "GEN")
    wear_code = WEAR_ABBR.get(wear_level, "GEN")
    return "{0}-{1}-{2}-{3}".format(base, type_code, wear_code, random_suffix())


def randomize_feature_flags():
    """Randomize, but cap how many 'loud' bump layers can stack at once --
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


def _apply_seed(opts):
    """Seed the feature/parameter RNG for reproducible variants. Blank = fully
    random. Only meaningful with 'Randomize features' on -- in manual mode the
    look is fully determined by the checkboxes, so a seed has nothing to vary.
    Material *names* stay unique regardless (see _name_rng). Accepts an int or
    any hashable string."""
    raw = str(opts.get("random_seed", "") or "").strip()
    if not raw:
        return None
    try:
        seed = int(raw)
    except ValueError:
        seed = raw
    random.seed(seed)
    return seed


# --------------------------------------------------------------------------
# Options dialog (GUI only -- auto-skipped in headless mode)
# --------------------------------------------------------------------------

def get_options():
    if lux.isHeadless():
        print("Headless session detected -- skipping dialog, using DEFAULT_OPTIONS.")
        return dict(DEFAULT_OPTIONS)

    values = [
        ("name_prefix", lux.DIALOG_TEXT, "Name prefix (blank = 'MAT'):", DEFAULT_OPTIONS["name_prefix"]),
        # DIALOG_ITEM default is an INDEX into the item list, not the label --
        # passing the label string here left KeyShot with no valid default and
        # (combined with the index-typed return value) silently defeated the
        # dropdown. See norm_item below for the matching return-side fix.
        ("material_type", lux.DIALOG_ITEM, "Material type:",
         MATERIAL_TYPE_ORDER.index(DEFAULT_OPTIONS["material_type"]), MATERIAL_TYPE_ORDER),
        ("wear_level", lux.DIALOG_ITEM, "Wear level:",
         WEAR_ORDER.index(DEFAULT_OPTIONS["wear_level"]), WEAR_ORDER),
        ("wear_multiplier", lux.DIALOG_DOUBLE, "Wear fine-tune (x):",
         DEFAULT_OPTIONS["wear_multiplier"], (0.0, 3.0)),
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
    values.append((lux.DIALOG_LABEL, "-- roughness / color drivers (pick one of each pair) --"))
    for key in ["add_fractal_roughness", "add_occlusion_roughness", "add_color_gradient"]:
        values.append((key, lux.DIALOG_CHECK, FEATURE_LABELS[key], DEFAULT_OPTIONS[key]))
    values.append((lux.DIALOG_LABEL, "-- generation --"))
    values.append(("randomize_features", lux.DIALOG_CHECK,
                    "Randomize features instead (ignores checkboxes above)",
                    DEFAULT_OPTIONS["randomize_features"]))
    values.append(("random_seed", lux.DIALOG_TEXT,
                    "Seed (blank = random; only affects Randomize):",
                    DEFAULT_OPTIONS["random_seed"]))
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
        # KeyShot's DIALOG_ITEM return type varies by build: usually the
        # selected index (int), sometimes the label (str), occasionally a
        # list. Normalise all three to a valid label and never return
        # something that isn't a real option -- the old code returned the raw
        # value, so an int index bypassed the selection entirely and always
        # fell through to the default material/wear.
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
    return opts


# --------------------------------------------------------------------------
# Node/parameter helpers (all non-fatal)
# --------------------------------------------------------------------------

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
    """Resolve lux.<attr_name> safely; create the node if it exists."""
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
        print("  [warn] no parameter matching '{0}' on this node".format(label))
        return False
    if p.isPure():
        print("  [warn] '{0}' is a connection-only (pure) parameter".format(label))
        return False
    try:
        p.setValue(value)
        return True
    except Exception as e:
        print("  [warn] couldn't set '{0}'={1}: {2} (left at default)".format(label, repr(value), e))
        return False


def safe_edge(graph, source, target, param, label=""):
    try:
        graph.newEdge(source=source, target=target, param=param)
        return True
    except Exception as e:
        print("  [warn] couldn't wire {0}: {1}".format(label or param, e))
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
            print("  [warn] stopping bump combination early -- Bump Add unavailable")
            return current
        slots = connection_param_names(bump_add, lux.PARAMETER_TYPE_SHADERBUMP)
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


# --------------------------------------------------------------------------
# Masking (targeted wear) -- Curvature/Occlusion mask x effect via Color
# Composite. Node ids are confirmed (11.0 lux ref); input-slot names are
# discovered at run time, and any wiring failure degrades to the unmasked
# effect so masking can never break the base material. See MWR-9C4E21.
# --------------------------------------------------------------------------

def add_curvature_mask(graph, feather=True):
    """Convex-edge mask: white on positive curvature (edges/corners), black on
    the flats -- so an effect composited through it only lands on edges."""
    n = try_new_node(graph, "SHADER_TYPE_CURVATURE", "Curvature (edge mask)")
    if n is None:
        return None
    set_display(n, ["positive curvature"], (1.0, 1.0, 1.0), ptype=lux.PARAMETER_TYPE_COLOR)
    # A mid-grey zero-curvature feathers the wear off the edge onto the faces;
    # pure black gives a hard rim only on the corners.
    zero = (0.35, 0.35, 0.35) if feather else (0.0, 0.0, 0.0)
    set_display(n, ["zero curvature"], zero, ptype=lux.PARAMETER_TYPE_COLOR)
    set_display(n, ["negative curvature"], (0.0, 0.0, 0.0), ptype=lux.PARAMETER_TYPE_COLOR)
    return n


def add_occlusion_mask(graph):
    """Cavity mask: white in occluded crevices, black on exposed faces -- the
    inverse of the edge mask, so grime composited through it collects in the
    cavities. Occluded/unoccluded colour param names vary by build; best-effort
    (masking degrades gracefully if they aren't found)."""
    n = try_new_node(graph, "SHADER_TYPE_OCCLUSION", "Occlusion (cavity mask)")
    if n is None:
        return None
    set_display(n, ["occluded"], (1.0, 1.0, 1.0), ptype=lux.PARAMETER_TYPE_COLOR)
    set_display(n, ["unoccluded", "bright", "far", "exposed"], (0.0, 0.0, 0.0),
                ptype=lux.PARAMETER_TYPE_COLOR)
    return n


def masked(graph, effect_node, mask_node, label="masked"):
    """Gate effect_node by mask_node through a Color Composite (alpha = mask),
    returning a node that can drop in wherever effect_node would have gone.
    Defensive: if the composite or its wiring is unavailable, returns the raw
    effect_node so a mask can never make an effect vanish entirely. The exact
    slot names are build-dependent -- DEBUG dumps them on first run so they can
    be pinned precisely later."""
    if effect_node is None:
        return None
    if mask_node is None:
        return effect_node
    comp = try_new_node(graph, "SHADER_TYPE_COLOR_COMPOSITE", "Color Composite ({0})".format(label))
    if comp is None:
        print("  [warn] Color Composite unavailable -- {0} left unmasked".format(label))
        return effect_node

    color_slots = connection_param_names(comp, lux.PARAMETER_TYPE_SHADERCOLOR)
    alpha_param = find_param(comp, ["alpha", "opacity", "mask", "blend amount"])

    ok_effect = False
    if color_slots:
        ok_effect = safe_edge(graph, source=effect_node, target=comp,
                              param=color_slots[0], label="{0}: effect->input".format(label))
    ok_mask = False
    if alpha_param is not None:
        ok_mask = safe_edge(graph, source=mask_node, target=comp,
                            param=alpha_param.getName(), label="{0}: mask->alpha".format(label))
    elif len(color_slots) >= 2:
        # No obvious alpha slot -- fall back to the second colour input so the
        # mask still modulates the blend rather than being dropped silently.
        ok_mask = safe_edge(graph, source=mask_node, target=comp,
                            param=color_slots[1], label="{0}: mask->input2".format(label))

    if ok_effect and ok_mask:
        return comp
    print("  [warn] {0}: mask wiring incomplete (effect={1}, mask={2}) -- using unmasked effect".format(
        label, ok_effect, ok_mask))
    return effect_node


# --------------------------------------------------------------------------
# Layer builders -- each returns a node (bump-domain) or bool (scalar drivers)
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
    # hammered metal" -- a strong effect even alone, hence the extra 0.6x.
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
    # possibly high-contrast) in place -- this was the leading suspect for
    # "wild" output. Best-effort: this node's UI is a draggable color bar,
    # which may not expose simple named color parameters the way other
    # nodes do. If no match is found, that's reported rather than assumed.
    light = tuple(clamp01(c * 1.25 + 0.05) for c in base_color)
    dark = tuple(clamp01(c * 0.6) for c in base_color)
    ok1 = set_display(n, ["color 1", "start color", "color a"], light, ptype=lux.PARAMETER_TYPE_COLOR)
    ok2 = set_display(n, ["color 2", "end color", "color b"], dark, ptype=lux.PARAMETER_TYPE_COLOR)
    if not (ok1 or ok2):
        print("  [warn] couldn't find Color Gradient's color-stop parameters -- it will use "
              "KeyShot's own default gradient colors, which may look more extreme than intended")
    return wire_scalar_driver(graph, n, base_node,
                              ["color", "diffuse", "tint", "reflectance"], "color")


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def build_material(opts):
    material_type = opts.get("material_type", DEFAULT_OPTIONS["material_type"])
    wear_level = opts.get("wear_level", DEFAULT_OPTIONS["wear_level"])
    wear_mult = WEAR_PRESETS.get(wear_level, 1.0) * float(opts.get("wear_multiplier", 1.0))

    seed = _apply_seed(opts)
    if seed is not None:
        print("  Seeded feature RNG with {0} (reproducible in randomize mode)".format(repr(seed)))

    features = {k: bool(opts.get(k, False)) for k in FEATURE_KEYS}
    if opts.get("randomize_features"):
        features = randomize_feature_flags()

    mask_scratches = bool(opts.get("mask_scratches_to_edges"))
    mask_spots = bool(opts.get("mask_spots_to_cavities"))

    shader_fn, base_color, base_roughness = MATERIAL_TYPES.get(
        material_type, MATERIAL_TYPES[DEFAULT_OPTIONS["material_type"]])
    shader_type = shader_fn()

    name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level)

    print("lux.isHeadless() = {0}".format(lux.isHeadless()))
    print("Building '{0}' | type={1} | wear={2} (x{3:.2f})".format(name, material_type, wear_level, wear_mult))
    active = [FEATURE_LABELS[k] for k, v in features.items() if v]
    active_str = ", ".join(active) if active else "(none)"
    print("Features: {0}".format(active_str))
    masks_on = [m for m, on in [("scratches->edges", mask_scratches),
                                ("spots->cavities", mask_spots)] if on]
    if masks_on:
        print("Masking: {0}".format(", ".join(masks_on)))

    # Damp each loud bump layer's amplitude by how many are stacked, so
    # total surface energy stays roughly bounded regardless of how many
    # ended up active -- this is what actually stops combinations from
    # compounding into chaotic noise.
    active_loud_count = sum(1 for k in LOUD_BUMP_FEATURES if features.get(k))
    damping = 1.0 / math.sqrt(max(1, active_loud_count))
    if active_loud_count > 1:
        print("  {0} loud bump layers active -- damping each by {1:.2f}x".format(active_loud_count, damping))

    for attempt in range(5):
        try:
            lux.createSceneMaterial(name)
            break
        except Exception as e:
            print("  [warn] couldn't create material '{0}': {1} -- trying a new random name".format(name, e))
            name = resolve_material_name(opts.get("name_prefix", ""), material_type, wear_level)
    else:
        raise RuntimeError("Couldn't create a scene material after 5 attempts")

    graph = lux.getMaterialGraph(name)
    root = graph.getRoot()
    if DEBUG:
        dump_node(root, "Root")

    base_node = new_node(graph, shader_type, material_type)
    safe_edge(graph, source=base_node, target=root, param="surface", label="base -> root.surface")
    # "diffuse" is essential: KeyShot's Plastic material names its colour
    # channel "Diffuse", not "Color" -- without it, plastic bases silently kept
    # KeyShot's default colour instead of the one picked here. Metal uses
    # "Color"; both are covered by the keyword list.
    set_display(base_node, ["color", "diffuse", "tint", "reflectance", "base color"],
                base_color, ptype=lux.PARAMETER_TYPE_COLOR)
    set_display(base_node, ["roughness"], base_roughness)

    # --- bump-domain layers, combined into one bump input -----------------
    # Masking is applied per-layer here: a masked layer is wrapped through a
    # Curvature/Occlusion + Color Composite before it joins the bump chain.
    bump_sources = []
    if features["add_fine_noise"]:
        bump_sources.append(add_fine_noise_bump(graph))
    if features["add_scratches"]:
        scr = add_scratches_bump(graph, wear_mult, damping)
        if mask_scratches:
            scr = masked(graph, scr, add_curvature_mask(graph, feather=(wear_level != "Heavy Wear")),
                         "scratches->edges")
        bump_sources.append(scr)
    if features["add_rounded_edges"]:
        bump_sources.append(add_rounded_edges_bump(graph, wear_mult, damping))
    if features["add_spots"]:
        sp = add_spots_bump(graph, wear_mult, damping)
        if mask_spots:
            sp = masked(graph, sp, add_occlusion_mask(graph), "spots->cavities")
        bump_sources.append(sp)
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

    print("Built material graph: {0}".format(name))
    return graph, name


def apply_material_to_parts(name, name_filter=None):
    """Apply `name` across the scene. Deliberately does NOT pre-filter to
    isObject() -- KeyShot's own docs confirm Group nodes accept setMaterial()
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
                print("  [warn] setMaterial failed (kind={0}): {1}".format(kind, e))
        if ok:
            applied += 1
            if DEBUG:
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
        else:
            skipped += 1
    suffix = " matching {0}".format(repr(name_filter)) if name_filter else ""
    print("Applied '{0}' to {1} node(s){2}, skipped {3}".format(name, applied, suffix, skipped))
    if DEBUG and applied:
        print("  applied to node kinds: {0}".format(kind_counts))
    if applied == 0 and DEBUG:
        print("  [info] nothing matched -- run with DEBUG=True and check the node "
              "kinds above, or confirm the scene actually has geometry loaded")
    return applied


if __name__ == "__main__":
    options = get_options()
    if options is None:
        print("Cancelled -- nothing built.")
    else:
        graph, material_name = build_material(options)
        apply_material_to_parts(material_name, name_filter=resolve_filter(options.get("name_filter")))
