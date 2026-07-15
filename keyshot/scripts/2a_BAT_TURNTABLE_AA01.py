# -*- coding: utf-8 -*-
# AUTHOR tajf (built on KeyShot's renderimages.py reference script)
# REV AA01
# HEADLESS COMPLIANT
# Batch-imports every model of a chosen extension from a folder, applies an
# optional material template, then spins each part 360 degrees around a
# chosen base camera and encodes a small turntable video per part. The base
# camera field accepts either a Studio name (preferred -- a Studio pairs a
# camera with its matching environment/lighting, confirmed via
# lux.getStudios()/lux.getStudio()/lux.setActiveStudio() in KeyShot's own
# scripting reference) or a raw camera name for parts with no Studios.
# Falls back to matching cameras directly (old behavior) if nothing studio-
# related is found, and just uses whatever lighting was already active.
import os, re, sys
import os.path
import csv
import time
import json
from datetime import datetime

MANIFEST_FIELDS = ["timestamp", "part_file", "base_name", "view", "template", "output_path", "status"]

def logManifestRow(manifestPath, row):
    isNew = not os.path.isfile(manifestPath)
    with open(manifestPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)

# --------------------------------------------------------------------------
# Reliability helpers (Phase-1, RAR-6E1F3B sec 6). ASCII-only, f-string-free.
# --------------------------------------------------------------------------

def verify_output(path, started_at):
    """Confirm a render actually wrote: exists, non-trivial size, mtime >= start.
    renderImage's return value is undocumented, so the file on disk is the truth."""
    try:
        if not os.path.exists(path):
            return False
        st = os.stat(path)
        if st.st_size < 512:
            return False
        return st.st_mtime >= (started_at - 2.0)
    except Exception:
        return False


def verify_frame_sequence(folder, filenames):
    missing = []
    for fn in filenames:
        p = os.path.join(folder, fn)
        try:
            if (not os.path.exists(p)) or os.stat(p).st_size < 512:
                missing.append(fn)
        except Exception:
            missing.append(fn)
    return (len(missing) == 0, missing)


_SANITIZE_RE = re.compile(r'[\\/:*?"<>|\s]+')


def sanitize_name(name):
    """Replace path-hostile characters (/ \\ : * ? " < > |) and whitespace runs
    with '_' so a studio/camera/base name can't produce an invalid output path."""
    cleaned = _SANITIZE_RE.sub("_", str(name)).strip("_")
    return cleaned if cleaned else "unnamed"


def load_job_json(folder):
    """Headless AUTO sidecar (RPA-7B2E4D sec 3): if a job.json sits in `folder`,
    load it and return its dict so its keys can override DEFAULT_OPTIONS. Never
    fatal -- a missing or malformed job.json yields {}."""
    if not folder:
        return {}
    jp = os.path.join(folder, "job.json")
    try:
        if not os.path.isfile(jp):
            return {}
        fh = open(jp)
        try:
            data = json.load(fh)
        finally:
            fh.close()
        if isinstance(data, dict):
            print("Loaded job.json from {0}".format(jp))
            return data
        print("[warn] job.json at {0} is not a JSON object -- ignoring".format(jp))
    except Exception as e:
        print("[warn] couldn't read job.json at {0}: {1}".format(jp, e))
    return {}


# Headless defaults mirror the PRO dialog's keys/defaults. A job.json (CWD or
# import folder) overrides these; the interactive input() path is gone (a closed
# stdin under keyshot_headless -script made it spin forever -- RAR-6E1F3B 1.2-W6).
# template is an index into the runtime template list (0 = "-- None --").
DEFAULT_OPTIONS = {
    "folder": "",
    "outFolder": "",
    "iext": "bip",
    "baseCamera": "Iso",
    "template": 0,
}

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
                  ("baseCamera", lux.DIALOG_TEXT, "Studio or camera to base the turntable on (Studio preferred -- pairs camera + lighting; falls back to the first camera found):", "Iso"),
                  (lux.DIALOG_LABEL, "--"),
                  ("template", lux.DIALOG_ITEM, "Apply material template on each import (optional):",
                   tmpls[0], tmpls)]
        desc = "Imports every model of a chosen extension and renders a small 360-degree turntable mp4 for each."
        opts = lux.getInputDialog(title = "Render Turntables",
                                  desc = desc,
                                  values = values,
                                  id = "renderturntables.py.luxion")
    else:
        # Headless: no interactive prompts (a closed stdin would hang). Start
        # from DEFAULT_OPTIONS, overlay a job.json from the CWD, then one from
        # the import folder that job.json may have named (RPA-7B2E4D sec 3).
        opts = dict(DEFAULT_OPTIONS)
        try:
            cwd = os.getcwd()
        except Exception:
            cwd = ""
        opts.update(load_job_json(cwd))
        jobFld = opts.get("folder", "") or ""
        if jobFld and (not cwd or os.path.abspath(jobFld) != os.path.abspath(cwd)):
            opts.update(load_job_json(jobFld))
        # Normalise the template index into the (index, label) shape the code
        # below expects (mirrors the old inputItem return / the dialog result).
        try:
            ti = int(opts.get("template", 0))
        except (ValueError, TypeError):
            ti = 0
        if ti < 0 or ti >= len(tmpls):
            ti = 0
        opts["template"] = (ti, tmpls[ti])
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

    for f in sorted([f for f in os.listdir(fld) if f.lower().endswith(iext)]):
        path = fld + os.path.sep + f
        lux.newScene()

        print("Importing {}".format(path))
        # Wrap the import so one corrupt file yields one FAILED row + continue
        # instead of killing the whole batch (1.1-W2 / 1.2 inherited).
        try:
            lux.importFile(path)
        except Exception as e:
            print("  [warn] couldn't import {0}: {1} -- skipping".format(path, e))
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": stripExt(f, iext),
                "view": "",
                "template": template or "",
                "output_path": "",
                "status": "FAILED (import)",
            })
            continue

        if template:
            print("  Setting material template {}".format(template))
            lux.setMaterialTemplate(template)

        baseName = stripExt(f, iext)

        # Studio-aware camera/lighting selection. A Studio pairs a camera
        # with its matching environment (confirmed: lux.getStudios(),
        # lux.getStudio(name), lux.setActiveStudio(name)) -- using it instead
        # of a raw camera means the turntable actually gets the lighting the
        # part was built with, instead of whatever happened to already be
        # active in the scene.
        studios = []
        try:
            studios = lux.getStudios()
        except Exception as e:
            print("  [warn] couldn't list studios: {}".format(e))

        # getStudio is 2024.1+ ONLY; getattr-guard it so a KS11 build stays
        # version-safe (RAR-6E1F3B headline #2 / 1.2-W1).
        _gs = getattr(lux, "getStudio", None)

        studioName = None
        if baseCameraName in studios:
            studioName = baseCameraName
        elif studios and _gs is not None:
            # No direct name match -- if a studio happens to be built on the
            # requested camera name, prefer that studio so lighting stays
            # paired correctly rather than silently falling back to raw. This
            # inspection needs getStudio; when it's absent we simply can't do
            # it -- a studio named exactly baseCameraName is still handled
            # above (then activated version-safely below), and anything else
            # degrades to the raw-camera path (current behaviour).
            for s in studios:
                try:
                    if _gs(s).getCamera() == baseCameraName:
                        studioName = s
                        break
                except Exception:
                    continue

        cam = None
        if studioName:
            # Activation FIRST and unconditionally -- setActiveStudio exists in
            # every build and pairs camera + environment. It must NOT be gated on
            # getStudio, or a KS11 build silently drops to raw-camera lighting.
            try:
                lux.setActiveStudio(studioName)
            except Exception as e:
                print("  [warn] couldn't activate studio '{}': {} -- falling back to raw camera.".format(studioName, e))
                studioName = None
            if studioName:
                # getStudio (guarded) only to LEARN the paired camera name;
                # its absence must not drop us to raw lighting.
                if _gs is not None:
                    try:
                        cam = _gs(studioName).getCamera()
                        if cam:
                            lux.setCamera(cam)
                    except Exception as e:
                        print("  [warn] getStudio('{}') unusable ({}) -- using active camera".format(studioName, e))
                        cam = None
                if not cam:
                    try:
                        cam = lux.getCamera()
                    except Exception:
                        cam = None
                print("  Using studio '{}' (camera '{}') for lighting + camera.".format(studioName, cam))

        if not studioName:
            cameras = lux.getCameras()
            if not cameras:
                print("  No studios or cameras found in {}, skipping.".format(f))
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "base_name": baseName,
                    "view": "",
                    "template": template or "",
                    "output_path": "",
                    "status": "SKIPPED (no studios or cameras)",
                })
                continue

            cam = baseCameraName if baseCameraName in cameras else cameras[0]
            if cam != baseCameraName:
                print("  '{}' not found as a studio or camera, using camera '{}' instead.".format(baseCameraName, cam))
            lux.setCamera(cam)
            if studios:
                print("  [warn] studio(s) exist ({}) but none reference camera '{}' -- lighting will be "
                      "whatever's currently active, not necessarily matched to this camera.".format(
                          ", ".join(studios), cam))

        sceneRoot = lux.getSceneTree()
        sceneRoot.centerAndFit()
        lux.setCameraDistance(lux.getCameraDistance() * PADDING_FACTOR)

        azimuth, incl, twist = lux.getSphericalCamera()

        safeBase = sanitize_name(baseName)
        frameFolder = os.path.join(outFld, safeBase + "_turntable_frames")
        if not os.path.isdir(frameFolder):
            os.makedirs(frameFolder)

        print("  Rendering {} turntable frames for {}...".format(FRAME_COUNT, baseName))
        frameNames = []
        for i in range(1, FRAME_COUNT + 1):
            az = (azimuth + (i - 1) * (360.0 / FRAME_COUNT)) % 360.0
            if az > 180.0:
                az -= 360.0
            lux.setSphericalCamera(az, incl, twist)
            frameName = "frame.{}.jpg".format(i)
            framePath = os.path.join(frameFolder, frameName)
            lux.renderImage(path=framePath, width=TURNTABLE_WIDTH, height=TURNTABLE_HEIGHT, opts=turnOpts)
            frameNames.append(frameName)

        videoPath = os.path.join(outFld, safeBase + "_turntable.mp4")

        # Never encode an incomplete sequence: verify every expected frame
        # exists + is non-trivial first (1.2-W3 / sec 3.2 #4). On a gap, skip
        # the encode, log FAILED with the missing list, and keep the frames.
        seqOk, missing = verify_frame_sequence(frameFolder, frameNames)
        if not seqOk:
            print("  [warn] {} of {} frames missing -- NOT encoding {}: {}".format(
                len(missing), FRAME_COUNT, baseName, ", ".join(missing)))
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": baseName,
                "view": "turntable",
                "template": template or "",
                "output_path": videoPath,
                "status": "FAILED (missing frames: {})".format(", ".join(missing)),
            })
            continue

        print("  Encoding {}".format(videoPath))
        # Wrap encodeVideo: an encode failure logs a FAILED row and continues to
        # the next part instead of killing the whole batch (1.2-W2).
        try:
            lux.encodeVideo(folder=frameFolder,
                             frameFiles="frame.%d.jpg",
                             videoName=videoPath,
                             fps=FPS,
                             firstFrame=1,
                             lastFrame=FRAME_COUNT,
                             keepFrames=False)
        except Exception as e:
            print("  [warn] encodeVideo failed for {}: {} -- continuing".format(videoPath, e))
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": baseName,
                "view": "turntable",
                "template": template or "",
                "output_path": videoPath,
                "status": "FAILED (encode)",
            })
            continue
        viewLabel = "turntable ({} / studio {})".format(cam, studioName) if studioName else "turntable ({})".format(cam)
        logManifestRow(manifestPath, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "part_file": f,
            "base_name": baseName,
            "view": viewLabel,
            "template": template or "",
            "output_path": videoPath,
            "status": "encoded",
        })

    print("Manifest written to {}".format(manifestPath))

main()
