# -*- coding: utf-8 -*-
# AUTHOR claude-subagent
# REV AA01
# HEADLESS COMPLIANT
# Material-name lookup table: Creo (native/import) material or appearance
# name -> KeyShot material template, applied per object instead of
# scene-wide. `1_HLP_MAT_PREFLIGHT_AA01.py` catches the SYMPTOM of missing
# material coverage (an object whose material didn't change when a template
# was applied); this script is the PREVENTION -- given a mapping file, it
# walks every imported part's scene tree and applies the matching template
# to each object individually, so parts with mixed materials (e.g. a
# steel-and-rubber assembly) don't all get forced onto one template the way
# lux.setMaterialTemplate() does when applied scene-wide.
#
# -----------------------------------------------------------------------
# MAPPING FILE FORMAT
# -----------------------------------------------------------------------
# CSV (default) -- two columns, header row required:
#     creo_material,keyshot_template
#     STEEL_GALV,Steel - Galvanized
#     PC_BLACK,Plastic - Polycarbonate Black
#
# JSON -- flat object, same pairing:
#     {"STEEL_GALV": "Steel - Galvanized", "PC_BLACK": "Plastic - Polycarbonate Black"}
#
# Format is picked from the mapping file's extension (.csv vs .json).
# Lookup is case-insensitive and trims whitespace on both sides, since Creo
# material/appearance names and KeyShot template names both drift on
# casing between exports. First match wins if the file has duplicate keys.
#
# -----------------------------------------------------------------------
# CONFIRMED vs INFERRED/EXPERIMENTAL
# -----------------------------------------------------------------------
# Confirmed (used the same way in 1_HLP_MAT_PREFLIGHT_AA01.py and
# 2a_BAT_STD_VIEW_AA01.py already in this pipeline): lux.newScene(),
# lux.importFile(), lux.getSceneTree(), node.isObject(), node.getChildren(),
# node.getName(), node.getMaterial(), lux.getMaterialTemplates(),
# lux.setMaterialTemplate(name) (scene-wide only -- not what we want here,
# kept only as a last-resort fallback, see below).
#
# EXPERIMENTAL: there is no confirmed KeyShot scripting API in the
# reference available here for assigning a material template to ONE object
# node rather than the whole scene. Rather than invent a confirmed-sounding
# call, this tries a short list of plausible method names on the object
# node itself and reports whichever one actually worked on your build --
# same defensive-probe pattern as set_ground_rendering() in
# 2b_ANI_HERO_REVEAL_AA01.py. If none of them exist on your KeyShot
# version, every "hit" is logged as a mapping success but an APPLY
# FAILURE, and the script warns once and keeps going rather than pretending
# it applied something it didn't. Run help(node) in the Scripting Console
# on an object node to find the real method name if that happens, and add
# it to OBJECT_TEMPLATE_SETTERS below.
import os, re, sys
import os.path
import csv
import json
from datetime import datetime

# Candidate method names for assigning a material template to a single
# object node. Tried in order; first one that exists AND doesn't raise
# wins. None of these are confirmed against KeyShot's own scripting
# reference -- see the EXPERIMENTAL note above.
OBJECT_TEMPLATE_SETTERS = ["setMaterialTemplate", "applyMaterialTemplate", "setMaterial"]


def genericInput(msg, default=None, check=lambda x: len(x) > 0):
    if default is not None:
        msg += " [{}] ".format(default)
    if not msg.endswith(" "):
        msg += " "
    while True:
        try:
            value = input(msg)
            if check(value):
                return value
            elif len(value) == 0 and default is not None:
                return default
        except EOFError:
            sys.stdout.write("\n")
            continue
        except KeyboardInterrupt:
            sys.exit()

def inputFolder(msg):
    return genericInput(msg, check=lambda x: os.path.isdir(x))

def inputFile(msg):
    return genericInput(msg, check=lambda x: os.path.isfile(x))

def inputText(msg, default):
    return genericInput(msg, default=default)

def inputInt(msg, default, valueRange=None):
    def check(x):
        try:
            n = int(x)
            return valueRange is None or (n >= valueRange[0] and n <= valueRange[1])
        except ValueError:
            return False
    return int(genericInput(msg, default=default, check=check))

def inputItem(msg, defaultIndex, items):
    pre = ""
    for i in range(len(items)):
        pre += "[{}] {}\n".format(i + 1, items[i])
    idx = inputInt(pre + msg, defaultIndex + 1, (1, len(items))) - 1
    return (idx, items[idx])

def inputBool(msg, default=False):
    return str(genericInput(msg, default=default)).lower() in ["y", "yes", "true", "1"]

def cleanExt(ext):
    while ext.startswith("."):
        ext = ext[1:]
    return ext.lower()

def collectObjectNodes(node, results=None):
    # Same recursive scene-tree walk as collectObjectMaterials() in
    # 1_HLP_MAT_PREFLIGHT_AA01.py, but keeps the node reference itself
    # (not just its name) since applying a template per object requires
    # calling a method on that specific node, not just reading its name.
    if results is None:
        results = []
    if node.isObject():
        results.append(node)
    for child in node.getChildren():
        collectObjectNodes(child, results)
    return results

def normKey(name):
    return (name or "").strip().lower()

def loadMappingCsv(path):
    mapping = {}
    with open(path, "r", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "creo_material" not in reader.fieldnames or "keyshot_template" not in reader.fieldnames:
            raise Exception("Mapping CSV must have a header row with columns 'creo_material,keyshot_template' -- got {}"
                            .format(reader.fieldnames))
        for row in reader:
            key = normKey(row.get("creo_material"))
            val = (row.get("keyshot_template") or "").strip()
            if key and val and key not in mapping:
                mapping[key] = val
    return mapping

def loadMappingJson(path):
    with open(path, "r") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise Exception("Mapping JSON must be a flat object of {{\"creo_material\": \"keyshot_template\"}} pairs.")
    mapping = {}
    for key, val in raw.items():
        k = normKey(key)
        v = (val or "").strip()
        if k and v and k not in mapping:
            mapping[k] = v
    return mapping

def loadMapping(path):
    ext = cleanExt(os.path.splitext(path)[1])
    if ext == "json":
        mapping = loadMappingJson(path)
    else:
        mapping = loadMappingCsv(path)
    if not mapping:
        raise Exception("Mapping file '{}' loaded but contained no usable creo_material -> keyshot_template pairs."
                        .format(path))
    return mapping

def applyObjectTemplate(node, template):
    # Tries each candidate setter in turn; returns the method name that
    # worked, or None if none of them exist / all raised. See the
    # EXPERIMENTAL note in the header docstring -- this is a probe, not a
    # confirmed API call.
    for methodName in OBJECT_TEMPLATE_SETTERS:
        fn = getattr(node, methodName, None)
        if fn is None:
            continue
        try:
            fn(template)
            return methodName
        except Exception:
            continue
    return None

MANIFEST_FIELDS = ["timestamp", "part_file", "object_name", "creo_material",
                   "mapped_template", "status", "applied_via"]

def logManifestRow(manifestPath, row):
    isNew = not os.path.isfile(manifestPath)
    with open(manifestPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)

def main():
    if not lux.isHeadless():
        values = [("mapping", lux.DIALOG_FILE, "Mapping file (.csv or .json, creo_material -> keyshot_template):", None),
                  ("folder", lux.DIALOG_FOLDER, "Folder to import from:", None),
                  ("iext", lux.DIALOG_TEXT, "Input file format to read:", "bip"),
                  ("dryRun", lux.DIALOG_CHECK, "Dry run (log matches, don't actually apply templates)", False)]
        desc = "Maps each object's native Creo material name to a KeyShot material template via a lookup file, and applies the matching template per object (not scene-wide)."
        opts = lux.getInputDialog(title = "Material Lookup Table",
                                  desc = desc,
                                  values = values,
                                  id = "materiallookup.py.luxion")
    else:
        opts = {}
        opts["mapping"] = inputFile("Mapping file (.csv or .json, creo_material -> keyshot_template):")
        opts["folder"] = inputFolder("Folder to import from:")
        opts["iext"] = inputText("Input file format to read:", "bip")
        opts["dryRun"] = inputBool("Dry run (log matches, don't actually apply templates)", False)
    if not opts: return

    mappingPath = opts["mapping"]
    if not mappingPath or len(mappingPath) == 0:
        raise Exception("Mapping file cannot be empty!")

    fld = opts["folder"]
    if len(fld) == 0:
        raise Exception("Folder cannot be empty!")

    iext = cleanExt(opts["iext"])
    if len(iext) == 0:
        raise Exception("Input extension cannot be empty!")

    dryRun = bool(opts["dryRun"])

    mapping = loadMapping(mappingPath)
    print("Loaded {} mapping entr{} from {}".format(len(mapping), "y" if len(mapping) == 1 else "ies", mappingPath))

    availableTemplates = set()
    try:
        availableTemplates = set(lux.getMaterialTemplates())
    except Exception as e:
        print("[warn] couldn't list material templates from this KeyShot build: {}".format(e))
        print("       Continuing without validating mapped template names against the library.")

    manifestPath = os.path.join(fld, "material_lookup_manifest.csv")

    files = [f for f in os.listdir(fld) if f.lower().endswith(iext)]
    if not files:
        raise Exception("Could not find any input files matching the extension \"{}\" in \"{}\"!"
                        .format(iext, fld))

    setterUsed = {}      # methodName -> count of successful uses, for the summary
    totalObjects = 0
    totalHit = 0
    totalMiss = 0
    totalApplied = 0
    totalApplyFailed = 0
    warnedNoSetter = False

    for f in files:
        path = fld + os.path.sep + f
        lux.newScene()

        print("Processing {}".format(f))
        lux.importFile(path)

        root = lux.getSceneTree()
        objects = collectObjectNodes(root)

        for node in objects:
            totalObjects += 1
            try:
                name = node.getName()
            except Exception:
                name = "<unknown>"
            try:
                creoMat = node.getMaterial()
            except Exception as e:
                print("  [warn] couldn't read material on object '{}': {}".format(name, e))
                creoMat = None

            key = normKey(creoMat)
            template = mapping.get(key)

            if template is None:
                totalMiss += 1
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "object_name": name,
                    "creo_material": creoMat or "",
                    "mapped_template": "",
                    "status": "miss (no mapping entry)",
                    "applied_via": "",
                })
                continue

            totalHit += 1

            if availableTemplates and template not in availableTemplates:
                print("  [warn] object '{}': mapping points to template '{}', which isn't in this "
                      "KeyShot build's material template library -- logging the miss, skipping apply."
                      .format(name, template))
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "object_name": name,
                    "creo_material": creoMat or "",
                    "mapped_template": template,
                    "status": "hit (template not found in library)",
                    "applied_via": "",
                })
                continue

            if dryRun:
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "object_name": name,
                    "creo_material": creoMat or "",
                    "mapped_template": template,
                    "status": "hit (dry run, not applied)",
                    "applied_via": "",
                })
                continue

            usedVia = applyObjectTemplate(node, template)
            if usedVia:
                totalApplied += 1
                setterUsed[usedVia] = setterUsed.get(usedVia, 0) + 1
                print("  Applied '{}' to '{}' (native material '{}') via {}()"
                      .format(template, name, creoMat, usedVia))
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "object_name": name,
                    "creo_material": creoMat or "",
                    "mapped_template": template,
                    "status": "applied",
                    "applied_via": usedVia,
                })
            else:
                totalApplyFailed += 1
                if not warnedNoSetter:
                    print("  [warn] none of the candidate per-object template setters ({}) worked on "
                          "this KeyShot build -- the mapping is being logged as a hit, but the template "
                          "was NOT applied. Run help(node) on an object node in the Scripting Console to "
                          "find the real method name and add it to OBJECT_TEMPLATE_SETTERS at the top of "
                          "this script.".format(", ".join(OBJECT_TEMPLATE_SETTERS)))
                    warnedNoSetter = True
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "object_name": name,
                    "creo_material": creoMat or "",
                    "mapped_template": template,
                    "status": "FAILED (no working per-object apply method)",
                    "applied_via": "",
                })

    print("")
    print("Processed {} part(s), {} object(s) total.".format(len(files), totalObjects))
    print("  {} object(s) matched a mapping entry, {} had no entry in the lookup table.".format(totalHit, totalMiss))
    if dryRun:
        print("  Dry run -- nothing was actually applied.")
    else:
        print("  {} object(s) had a template successfully applied, {} matched but failed to apply."
              .format(totalApplied, totalApplyFailed))
        if setterUsed:
            print("  Apply method(s) that worked on this build: {}"
                  .format(", ".join("{}() x{}".format(k, v) for k, v in setterUsed.items())))
    print("Manifest written to {}".format(manifestPath))
    print("Unmapped-material count above is the complementary read to what "
          "1_HLP_MAT_PREFLIGHT_AA01.py reports: preflight flags objects whose material didn't change "
          "after a scene-wide template; this counts objects that never had a lookup entry to try in the "
          "first place. Worth feeding those names back into the mapping file over time.")

main()
