# -*- coding: utf-8 -*-
# AUTHOR tajf (built on KeyShot's renderimages.py reference script)
# REV AA01
# HEADLESS COMPLIANT
# Batch-imports every model with a chosen extension from a folder, applies an
# optional material template, then queues a render for EVERY Studio defined
# in each imported part. A Studio pairs a camera with its matching
# environment/lighting (confirmed: lux.getStudios(), lux.getStudio(name),
# lux.setActiveStudio(name) -- see KeyShot's own scripting reference), so
# this keeps lighting correct per view. Earlier versions rendered every raw
# Camera instead (lux.getCameras() / lux.setCamera()), which silently left
# whatever environment happened to already be active -- fine for parts with
# only one lighting setup, wrong for parts built with multiple Studios.
# Falls back to raw cameras only for parts that have no Studios defined.
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
# stdin under keyshot_headless -script made it spin forever -- RAR-6E1F3B 1.1-W5).
# width/height None -> fall back to the scene info size (the dialog's default);
# template is an index into the runtime template list (0 = "-- None --").
DEFAULT_OPTIONS = {
    "folder": "",
    "outFolder": "",
    "iext": "bip",
    "oext": "png",
    "width": None,
    "height": None,
    "template": 0,
    "queue": True,
    "process": False,
}

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
        if opts.get("width") is None:
            opts["width"] = info["width"]
        if opts.get("height") is None:
            opts["height"] = info["height"]
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

    if len(opts["folder"]) == 0:
        raise Exception("Folder cannot be empty!")
    fld = opts["folder"]
    outFld = opts["outFolder"] if len(opts.get("outFolder", "")) > 0 else fld
    manifestPath = os.path.join(outFld, "render_manifest.csv")

    if len(opts["iext"]) == 0:
        raise Exception("Input extension cannot be empty!")
    iext = cleanExt(opts["iext"])
    # Use the same endswith semantics as the processing loop below so the
    # found-check can't claim files exist that the loop then skips (1.1-W7).
    found = False
    for name in sorted(os.listdir(fld)):
        if name.lower().endswith(iext):
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

    # Timestamp before the batch so queue-mode reconciliation (after
    # processQueue) can confirm files were written during this run.
    runStart = time.time()
    # Queued rows are logged as "queued" now and reconciled to
    # rendered_verified / MISSING after processQueue (1.1-W3).
    queuedRows = []

    for f in sorted([f for f in os.listdir(fld) if f.lower().endswith(iext)]):
        path = fld + os.path.sep + f
        lux.newScene()

        print("Importing {}".format(path))
        # Wrap the import so one corrupt file yields one FAILED row + continue
        # instead of killing the whole batch (1.1-W2).
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

        sceneRoot = lux.getSceneTree()

        studios = []
        try:
            studios = lux.getStudios()
        except Exception as e:
            print("  [warn] couldn't list studios: {}".format(e))

        if studios:
            print("  Found {} studio(s): {}".format(len(studios), ", ".join(studios)))
            for studioName in studios:
                cam = None
                # Activation FIRST and unconditionally: setActiveStudio exists in
                # every documented build and switches camera + environment + image
                # style together. It must NEVER be gated on getStudio (2024.1+
                # only), or a KS11 build logs every studio FAILED and renders zero
                # images while "completing" (RAR-6E1F3B headline #2 / 1.1-W1).
                try:
                    lux.setActiveStudio(studioName)
                except Exception as e:
                    print("  [warn] couldn't activate studio '{}': {}".format(studioName, e))
                    logManifestRow(manifestPath, {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "part_file": f,
                        "base_name": baseName,
                        "view": studioName,
                        "template": template or "",
                        "output_path": "",
                        "status": "FAILED (studio activation)",
                    })
                    continue

                # getStudio is 2024.1+ ONLY -- use it (getattr-guarded) purely to
                # LEARN the paired camera name for the log + a belt-and-suspenders
                # setCamera. Its absence must not fail the studio; setActiveStudio
                # already paired the camera + lighting above.
                _gs = getattr(lux, "getStudio", None)
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

                # Reframe the active camera to the part's bounding box. Keeps the
                # camera's orientation (front stays front, iso stays iso) but
                # adjusts distance/zoom so parts of any size fill the frame the
                # same way instead of some being tiny and some overflowing.
                sceneRoot.centerAndFit()
                # Pull the camera back to leave padding around the part instead
                # of a tight edge-to-edge fit.
                lux.setCameraDistance(lux.getCameraDistance() * PADDING_FACTOR)
                outStem = sanitize_name("{}_{}".format(baseName, studioName))
                outPath = os.path.join(outFld, "{}.{}".format(outStem, oext))
                print("  Rendering studio '{}' (camera '{}') -> {}".format(studioName, cam, outPath))
                if queue:
                    lux.renderImage(path=outPath, width=width, height=height, opts=renderOpts)
                    queuedRows.append({"part_file": f, "base_name": baseName,
                                       "view": studioName, "template": template or "",
                                       "output_path": outPath})
                    status = "queued"
                else:
                    t0 = time.time()
                    lux.renderImage(path=outPath, width=width, height=height, opts=renderOpts)
                    status = "rendered_verified" if verify_output(outPath, t0) else "MISSING"
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "base_name": baseName,
                    "view": studioName,
                    "template": template or "",
                    "output_path": outPath,
                    "status": status,
                })
        else:
            # No Studios defined on this part -- fall back to the original
            # raw-camera behavior. Lighting will be whatever's currently
            # active for every view, same as before this change.
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

            print("  No studios found on this part -- falling back to raw cameras "
                  "(lighting will not vary per view).")
            for cam in cameras:
                lux.setCamera(cam)
                sceneRoot.centerAndFit()
                lux.setCameraDistance(lux.getCameraDistance() * PADDING_FACTOR)
                outStem = sanitize_name("{}_{}".format(baseName, cam))
                outPath = os.path.join(outFld, "{}.{}".format(outStem, oext))
                print("  Rendering {} -> {}".format(cam, outPath))
                if queue:
                    lux.renderImage(path=outPath, width=width, height=height, opts=renderOpts)
                    queuedRows.append({"part_file": f, "base_name": baseName,
                                       "view": cam, "template": template or "",
                                       "output_path": outPath})
                    status = "queued"
                else:
                    t0 = time.time()
                    lux.renderImage(path=outPath, width=width, height=height, opts=renderOpts)
                    status = "rendered_verified" if verify_output(outPath, t0) else "MISSING"
                logManifestRow(manifestPath, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "part_file": f,
                    "base_name": baseName,
                    "view": cam,
                    "template": template or "",
                    "output_path": outPath,
                    "status": status,
                })

    if process:
        print("Processing queue")
        lux.processQueue()
        # Reconcile every queued row now that processQueue has run: the file on
        # disk is the truth (1.1-W3). Append a reconciled row per queued output.
        for q in queuedRows:
            st = "rendered_verified" if verify_output(q["output_path"], runStart) else "MISSING"
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": q["part_file"],
                "base_name": q["base_name"],
                "view": q["view"],
                "template": q["template"],
                "output_path": q["output_path"],
                "status": st,
            })

    print("Manifest written to {}".format(manifestPath))

main()
