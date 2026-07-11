# -*- coding: utf-8 -*-
# AUTHOR tajf (built on KeyShot's renderimages.py reference script)
# VERSION 0.1.0
# HEADLESS COMPLIANT
# ARCHIVED -- superseded by 2a_BAT_TURNTABLE_AA01.py (Studios-aware camera/
# lighting selection). Kept for reference only, not part of the active
# pipeline. See keyshot/SCRIPT_STOCK.md.
# Batch-imports every model of a chosen extension from a folder, applies an
# optional material template, then spins each part 360 degrees around a
# chosen base camera and encodes a small turntable video per part.
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
            sys.stdout.write("\n")
            continue
        except KeyboardInterrupt:
            sys.exit()

def inputFolder(msg):
    return genericInput(msg, check=lambda x: os.path.isdir(x))

def inputOptionalFolder(msg, fallback):
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

def cleanExt(ext):
    while ext.startswith("."):
        ext = ext[1:]
    return ext.lower()

def stripExt(filename, ext):
    lower = filename.lower()
    dotExt = "." + ext
    if lower.endswith(dotExt):
        return filename[:-len(dotExt)]
    if lower.endswith(ext):
        return filename[:-len(ext)]
    return filename

# ---- turntable settings -- tune these to taste ----
FRAME_COUNT = 36          # 360 / 36 = 10 degree steps. Raise for smoother motion.
FPS = 24
TURNTABLE_SAMPLES = 16    # kept low -- these are quick spin previews, not hero shots
TURNTABLE_WIDTH = 640
TURNTABLE_HEIGHT = 640
PADDING_FACTOR = 1.15     # same padding trick as the still-image batch script

def main():
    tmpls = ["-- None --"] + lux.getMaterialTemplates()
    if not lux.isHeadless():
        values = [("folder", lux.DIALOG_FOLDER, "Folder to import from:", None),
                  ("outFolder", lux.DIALOG_FOLDER, "Folder to save turntables to (leave blank = same as import folder):", ""),
                  ("iext", lux.DIALOG_TEXT, "Input file format to read:", "bip"),
                  ("baseCamera", lux.DIALOG_TEXT, "Camera to base the turntable on (must exist in each part; falls back to the first camera found):", "Iso"),
                  (lux.DIALOG_LABEL, "--"),
                  ("template", lux.DIALOG_ITEM, "Apply material template on each import (optional):",
                   tmpls[0], tmpls)]
        desc = "Imports every model of a chosen extension and renders a small 360-degree turntable mp4 for each."
        opts = lux.getInputDialog(title = "Render Turntables",
                                  desc = desc,
                                  values = values,
                                  id = "renderturntables.py.luxion")
    else:
        opts = {}
        opts["folder"] = inputFolder("Folder to import from:")
        opts["outFolder"] = inputOptionalFolder("Folder to save turntables to (blank = same as import folder):", opts["folder"])
        opts["iext"] = inputText("Input file format to read:", "bip")
        opts["baseCamera"] = inputText("Camera to base the turntable on:", "Iso")
        opts["template"] = inputItem("Apply material template on each import (optional):", 0, tmpls)
    if not opts: return

    fld = opts["folder"]
    if len(fld) == 0:
        raise Exception("Folder cannot be empty!")
    outFld = opts["outFolder"] if len(opts.get("outFolder", "")) > 0 else fld
    manifestPath = os.path.join(outFld, "render_manifest.csv")

    iext = cleanExt(opts["iext"])
    if len(iext) == 0:
        raise Exception("Input extension cannot be empty!")

    baseCameraName = opts["baseCamera"]

    template = opts["template"]
    if template[0] == 0:
        template = None
    else:
        template = template[1]

    turnOpts = lux.getRenderOptions()
    turnOpts.setAdvancedRendering(TURNTABLE_SAMPLES)
    # Deliberately NOT using setAddToQueue here -- turntable frames render
    # immediately, one after another, so the folder is complete and ready
    # for encodeVideo() by the time we get to it.

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
                "base_name": stripExt(f, iext),
                "view": "",
                "template": template or "",
                "output_path": "",
                "status": "SKIPPED (no cameras)",
            })
            continue

        cam = baseCameraName if baseCameraName in cameras else cameras[0]
        if cam != baseCameraName:
            print("  '{}' not found, using '{}' instead.".format(baseCameraName, cam))
        lux.setCamera(cam)

        sceneRoot = lux.getSceneTree()
        sceneRoot.centerAndFit()
        lux.setCameraDistance(lux.getCameraDistance() * PADDING_FACTOR)

        azimuth, incl, twist = lux.getSphericalCamera()

        frameFolder = os.path.join(outFld, baseName + "_turntable_frames")
        if not os.path.isdir(frameFolder):
            os.makedirs(frameFolder)

        print("  Rendering {} turntable frames for {}...".format(FRAME_COUNT, baseName))
        for i in range(1, FRAME_COUNT + 1):
            az = (azimuth + (i - 1) * (360.0 / FRAME_COUNT)) % 360.0
            if az > 180.0:
                az -= 360.0
            lux.setSphericalCamera(az, incl, twist)
            framePath = os.path.join(frameFolder, "frame.{}.jpg".format(i))
            lux.renderImage(path=framePath, width=TURNTABLE_WIDTH, height=TURNTABLE_HEIGHT, opts=turnOpts)

        videoPath = os.path.join(outFld, baseName + "_turntable.mp4")
        print("  Encoding {}".format(videoPath))
        lux.encodeVideo(folder=frameFolder,
                         frameFiles="frame.%d.jpg",
                         videoName=videoPath,
                         fps=FPS,
                         firstFrame=1,
                         lastFrame=FRAME_COUNT,
                         keepFrames=False)
        logManifestRow(manifestPath, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "part_file": f,
            "base_name": baseName,
            "view": "turntable ({})".format(cam),
            "template": template or "",
            "output_path": videoPath,
            "status": "encoded",
        })

    print("Manifest written to {}".format(manifestPath))

main()
