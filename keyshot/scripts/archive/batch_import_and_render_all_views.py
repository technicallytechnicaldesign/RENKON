# -*- coding: utf-8 -*-
# AUTHOR tajf (built on KeyShot's renderimages.py reference script)
# VERSION 0.8.0
# HEADLESS COMPLIANT
# ARCHIVED -- superseded by 2a_BAT_STD_VIEW_AA01.py (Studios-aware camera/
# lighting selection). Kept for reference only, not part of the active
# pipeline. See keyshot/SCRIPT_STOCK.md.
# Batch-imports every model with a chosen extension from a folder, applies an
# optional material template, then queues a render for EVERY camera defined
# in each imported part (not just a single forced view).
import os, re, sys
import os.path
import csv
from datetime import datetime

MANIFEST_FIELDS = ["timestamp", "part_file", "base_name", "view", "template", "output_path", "status"]

def logManifestRow(manifestPath, row):
    isNew = not os.path.isfile(manifestPath)
    with open(manifestPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)

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
            sys.stdout.write("\n")  # Yield a new line so next input isn't on same line.
            continue
        except KeyboardInterrupt:
            sys.exit()

def inputFolder(msg):
    return genericInput(msg, check=lambda x: os.path.isdir(x))

def inputOptionalFolder(msg, fallback):
    # Same as inputFolder, but blank input is allowed and falls back to `fallback`.
    val = genericInput(msg, default="", check=lambda x: len(x) == 0 or os.path.isdir(x))
    return val if len(val) > 0 else fallback

def inputText(msg, default):
    return genericInput(msg, default=default)

def intInRange(value, valueRange=None):
    try:
        n = int(value)
        if valueRange is not None:
            return n >= valueRange[0] and n <= valueRange[1]
        else:
            return True
    except ValueError:
        return False

def inputInt(msg, default, valueRange=None):
    return int(genericInput(msg, default=default, check=lambda x: intInRange(x, valueRange)))

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

# How much extra room to leave around each part after fitting, as a
# multiplier on the fitted camera distance. 1.0 = no padding (tight fit).
# 1.15 pulls the camera back 15%, 1.3 = 30%, etc. Tune to taste.
PADDING_FACTOR = 1.15

def stripExt(filename, ext):
    # Strips a trailing ".ext" (case-insensitive) from filename if present.
    lower = filename.lower()
    dotExt = "." + ext
    if lower.endswith(dotExt):
        return filename[:-len(dotExt)]
    if lower.endswith(ext):
        return filename[:-len(ext)]
    return filename

def main():
    tmpls = ["-- None --"] + lux.getMaterialTemplates()
    info = lux.getSceneInfo()
    opts = {}
    if not lux.isHeadless():
        values = [("folder", lux.DIALOG_FOLDER, "Folder to import from:", None),
                  ("outFolder", lux.DIALOG_FOLDER, "Folder to save renders to (leave blank = same as import folder):", ""),
                  ("iext", lux.DIALOG_TEXT, "Input file format to read:", "bip"),
                  ("oext", lux.DIALOG_TEXT, "Output image format:", "png"),
                  ("width", lux.DIALOG_INTEGER, "Output width:", info["width"]),
                  ("height", lux.DIALOG_INTEGER, "Output height:", info["height"]),
                  (lux.DIALOG_LABEL, "--"),
                  ("template", lux.DIALOG_ITEM, "Apply material template on each import (optional):",
                   tmpls[0], tmpls),
                  (lux.DIALOG_LABEL, "--"),
                  ("queue", lux.DIALOG_CHECK, "Add to queue", True),
                  ("process", lux.DIALOG_CHECK, "Process queue after running script", False)]
        desc = "Imports every model of a chosen extension, applies a material template, and renders EVERY camera view of each part."
        opts = lux.getInputDialog(title = "Render All Views",
                                  desc = desc,
                                  values = values,
                                  id = "renderallviews.py.luxion")
    else:
        opts["folder"] = inputFolder("Folder to import from:")
        opts["outFolder"] = inputOptionalFolder("Folder to save renders to (blank = same as import folder):", opts["folder"])
        opts["iext"] = inputText("Input file format to read:", "bip")
        opts["oext"] =  inputText("Output image format:", "png")
        opts["width"] =  inputInt("Output width:", info["width"])
        opts["height"] =  inputInt("Output height:", info["height"])
        opts["template"] = inputItem("Apply material template on each import (optional):", 0, tmpls)
        opts["queue"] = inputBool("Add to queue", True)
        opts["process"] = inputBool("Process queue after running script", False)
    if not opts: return

    if len(opts["folder"]) == 0:
        raise Exception("Folder cannot be empty!")
    fld = opts["folder"]
    outFld = opts["outFolder"] if len(opts.get("outFolder", "")) > 0 else fld
    manifestPath = os.path.join(outFld, "render_manifest.csv")

    if len(opts["iext"]) == 0:
        raise Exception("Input extension cannot be empty!")
    iext = cleanExt(opts["iext"])
    reFiles = re.compile(".*{}".format(iext), re.IGNORECASE)
    found = False
    for f in os.listdir(fld):
        if reFiles.match(f):
            found = True
            break
    if not found:
        raise Exception("Could not find any input files matching the extension \"{}\" in \"{}\"!"
                        .format(iext, fld))

    if len(opts["oext"]) == 0:
        raise Exception("Output extension cannot be empty!")
    oext = cleanExt(opts["oext"])

    width = opts["width"]
    height = opts["height"]
    template = opts["template"]
    queue = opts["queue"]
    process = opts["process"]

    # Only set template if one was chosen.
    if template[0] == 0:
        template = None
    else:
        template = template[1]

    # Render options object -- separate name from the `opts` dialog-result dict
    # above so the two don't shadow each other.
    renderOpts = lux.getRenderOptions()
    renderOpts.setAddToQueue(queue)

    for f in [f for f in os.listdir(fld) if f.lower().endswith(iext)]:
        path = fld + os.path.sep + f
        lux.newScene()

        print("Importing {}".format(path))
        lux.importFile(path)

        if template:
            print("  Setting material template {}".format(template))
            lux.setMaterialTemplate(template)

        baseName = stripExt(f, iext)

        cameras = lux.getCameras()
        if not cameras:
            print("  No cameras found in {}, skipping.".format(f))
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": baseName,
                "view": "",
                "template": template or "",
                "output_path": "",
                "status": "SKIPPED (no cameras)",
            })
            continue

        sceneRoot = lux.getSceneTree()

        for cam in cameras:
            lux.setCamera(cam)
            # Reframe the active camera to the part's bounding box. Keeps the
            # camera's orientation (front stays front, iso stays iso) but
            # adjusts distance/zoom so parts of any size fill the frame the
            # same way instead of some being tiny and some overflowing.
            sceneRoot.centerAndFit()
            # Pull the camera back to leave padding around the part instead
            # of a tight edge-to-edge fit.
            lux.setCameraDistance(lux.getCameraDistance() * PADDING_FACTOR)
            outPath = os.path.join(outFld, "{}_{}.{}".format(baseName, cam, oext))
            print("  Queuing {} -> {}".format(cam, outPath))
            success = lux.renderImage(path=outPath, width=width, height=height, opts=renderOpts)
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": baseName,
                "view": cam,
                "template": template or "",
                "output_path": outPath,
                "status": "queued" if success else "FAILED",
            })

    if process:
        print("Processing queue")
        lux.processQueue()

    print("Manifest written to {}".format(manifestPath))

main()
