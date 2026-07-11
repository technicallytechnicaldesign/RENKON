# -*- coding: utf-8 -*-
# AUTHOR tajf
# REV AA01
# HEADLESS COMPLIANT
# Fast QC pass: imports every part in a folder, applies a material template,
# and reports which objects' materials did NOT change when the template was
# applied. An unchanged material name after applying a template is a strong
# signal (not an absolute guarantee) that the template has no entry covering
# that object's native material/color name -- i.e. it fell through and is
# probably still wearing whatever default it imported with.
#
# This does no rendering at all, so it's meant to run in seconds ahead of a
# full batch, not as a replacement for eyeballing results.
import os, re, sys
import os.path
import csv
from datetime import datetime

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

def cleanExt(ext):
    while ext.startswith("."):
        ext = ext[1:]
    return ext.lower()

def collectObjectMaterials(node, results=None):
    # Recursively walks the scene tree, recording {object_name: material_name}
    # for every object node under `node`.
    if results is None:
        results = {}
    if node.isObject():
        results[node.getName()] = node.getMaterial()
    for child in node.getChildren():
        collectObjectMaterials(child, results)
    return results

REPORT_FIELDS = ["timestamp", "part_file", "object_name", "material_name", "status"]

def logReportRow(reportPath, row):
    isNew = not os.path.isfile(reportPath)
    with open(reportPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)

def main():
    tmpls = lux.getMaterialTemplates()
    if not tmpls:
        print("No material templates found in the library -- nothing to check.")
        return

    if not lux.isHeadless():
        values = [("folder", lux.DIALOG_FOLDER, "Folder to import from:", None),
                  ("iext", lux.DIALOG_TEXT, "Input file format to read:", "bip"),
                  ("template", lux.DIALOG_ITEM, "Material template to check:", tmpls[0], tmpls)]
        desc = "Checks whether a material template covers every object's native material name across a batch of parts, before you commit to a full render run."
        opts = lux.getInputDialog(title = "Material Template Pre-flight",
                                  desc = desc,
                                  values = values,
                                  id = "materialpreflight.py.luxion")
    else:
        opts = {}
        opts["folder"] = inputFolder("Folder to import from:")
        opts["iext"] = inputText("Input file format to read:", "bip")
        opts["template"] = inputItem("Material template to check:", 0, tmpls)
    if not opts: return

    fld = opts["folder"]
    if len(fld) == 0:
        raise Exception("Folder cannot be empty!")

    iext = cleanExt(opts["iext"])
    if len(iext) == 0:
        raise Exception("Input extension cannot be empty!")

    template = opts["template"][1]
    reportPath = os.path.join(fld, "material_preflight_report.csv")

    files = [f for f in os.listdir(fld) if f.lower().endswith(iext)]
    if not files:
        raise Exception("Could not find any input files matching the extension \"{}\" in \"{}\"!"
                        .format(iext, fld))

    totalParts = 0
    partsWithFlags = 0
    totalFlags = 0

    for f in files:
        path = fld + os.path.sep + f
        lux.newScene()

        print("Checking {}".format(f))
        lux.importFile(path)
        totalParts += 1

        root = lux.getSceneTree()
        before = collectObjectMaterials(root)

        lux.setMaterialTemplate(template)

        after = collectObjectMaterials(root)

        flagged = {name: mat for name, mat in after.items() if before.get(name) == mat}

        if flagged:
            partsWithFlags += 1
            for name, mat in flagged.items():
                totalFlags += 1
                print("  POSSIBLY UNCOVERED: object '{}' still on material '{}' after applying '{}'"
                      .format(name, mat, template))
                logReportRow(reportPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "object_name": name,
                    "material_name": mat,
                    "status": "unchanged after template",
                })
        else:
            print("  Clean -- every object's material changed when the template was applied.")

    print("")
    print("Checked {} part(s) against template '{}'.".format(totalParts, template))
    print("{} part(s) had at least one possibly-uncovered object ({} flag(s) total).".format(partsWithFlags, totalFlags))
    if totalFlags:
        print("Details written to {}".format(reportPath))
    print("Remember: this is a heuristic, not a certainty -- a name can legitimately stay")
    print("the same across the template if that's genuinely what the template intends.")
    print("Worth a quick visual double check on any part flagged above.")

main()
