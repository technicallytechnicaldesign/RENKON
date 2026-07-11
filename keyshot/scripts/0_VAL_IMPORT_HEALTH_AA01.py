# -*- coding: utf-8 -*-
# AUTHOR claude-subagent
# REV AA01
# HEADLESS COMPLIANT
# Trial-import geometry/appearance health check -- a CHEAP, FAST pre-flight
# gate that runs BEFORE a folder gets committed to the expensive multi-Studio
# batch render pass in 2a_BAT_STD_VIEW_AA01.py / 2a_BAT_TURNTABLE_AA01.py.
# For every file of a chosen extension in a folder, this does a trial
# lux.newScene() + lux.importFile() and three lightweight checks -- no
# rendering at all, same "runs in seconds" design as 1_HLP_MAT_PREFLIGHT_AA01.py.
#
# This is the P2 backlog item "Trial-import geometry/appearance health check"
# from SCRIPT_STOCK.md -- the original "Pre-import geometry/appearance
# validator" idea, now split into three concrete sub-checks and grounded in
# specific forum-reported failure modes documented in the "Research pass
# (2026-07-11): forum-grounded gaps for stage 0_" section of
# RESEARCH_CREO_KEYSHOT.md:
#
#   1. IMPORT FAILURE -- outright "unable to import" errors. Caught and
#      reported per-file so one bad file doesn't crash the whole folder run.
#   2. BOUNDING-BOX SANITY -- a zero/near-zero-volume bounding box is a
#      strong signal of a degenerate or failed import (geometry silently
#      didn't come through even though importFile() didn't raise). A
#      suspiciously huge bounding box is also flagged, as a soft heuristic.
#      This targets the "gaps... around all flat surfaces that had bends or
#      chamfers" / choppy-tessellation reports in RESEARCH_CREO_KEYSHOT.md --
#      severe tessellation failures often also distort the reported extents.
#   3. OBJECT/MESH COUNT SANITY -- an assembly-named file (filename contains
#      "ASSY"/"ASSM"/"ASM", case-insensitive) that resolves to only 1 object
#      node is a possible "components missing from assembly imports"
#      symptom -- reported independently on the Siemens community and
#      GrabCAD's KeyShot Users group (see RESEARCH_CREO_KEYSHOT.md). A file
#      that resolves to 0 object nodes at all is flagged as a totally empty
#      import -- a distinct failure signal from "import succeeded but
#      nothing there".
#   4. STUDIO/CAMERA PRESENCE -- a part with neither Studios nor raw cameras
#      will silently fall back to raw-camera rendering with whatever
#      lighting happens to be active when it hits 2a_BAT_STD_VIEW_AA01.py /
#      2a_BAT_TURNTABLE_AA01.py (both already warn about this mid-run, one
#      file at a time). This script's value is surfacing that for an ENTIRE
#      FOLDER up front, before a human commits to watching a long batch run.
#
# -----------------------------------------------------------------------
# CONFIRMED vs EXPERIMENTAL (this pipeline's established discipline)
# -----------------------------------------------------------------------
# Confirmed (KeyShot's own scripting reference, media.keyshot.com/scripting/
# doc/11.0/lux.html, and/or already relied on elsewhere in this pipeline):
# lux.newScene(), lux.importFile(path), lux.getSceneTree(), node.isObject(),
# node.getChildren(), node.getName(), lux.getStudios(), lux.getStudio(name),
# lux.getCameras(), lux.isHeadless(), lux.getInputDialog().
# SceneNode.getBoundingBox() -- the CALL is confirmed real as of the
# 2026-07-11 research pass (see RESEARCH_CREO_KEYSHOT.md), returning
# (min, max) vectors. What is NOT documented anywhere pulled here is the
# exact RETURN SHAPE (tuple vs object with .min/.max, world-space kwarg
# name, etc.), so resolve_bounding_box() / _parse_bbox_result() below still
# probe a short candidate list and a couple of plausible result shapes --
# copied verbatim from 2b_ANI_CUTAWAY_REVEAL_AA01.py /
# 2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py, which already carry this exact
# defensive pattern, rather than re-derived here.
#
# EXPERIMENTAL / this-script's-own-judgment-call (NOT a KeyShot API
# uncertainty -- a design decision this script is making on its own):
# what counts as "near-zero volume", "suspiciously large", or "too few
# objects for an assembly-named file" is a heuristic threshold this script
# picks, not something KeyShot's API tells us is wrong. SUSPICIOUS_SIZE_
# THRESHOLD and ASSEMBLY_NAME_HINTS below are exposed as tunable constants
# for exactly that reason -- treat every "FLAG" in the manifest as "worth a
# human look", not as a certainty.
import os, re, sys
import os.path
import csv
from datetime import datetime

# --------------------------------------------------------------------------
# Tunable constants
# --------------------------------------------------------------------------

# Bounding-box longest-edge length (in the scene's native units) above which
# a part is flagged as "suspiciously large". This is a soft heuristic
# relative to typical part sizes, NOT a hard failure -- a legitimately large
# assembly will trip this and that's fine, it just means "take a look".
# Tune to whatever your typical part-size range actually is.
SUSPICIOUS_SIZE_THRESHOLD = 5000.0

# Bounding-box volume below which a part is treated as a near-zero-volume /
# possibly-degenerate import. Deliberately tiny -- this is meant to catch
# genuinely collapsed/failed geometry, not just "a small part".
NEAR_ZERO_VOLUME_EPS = 1e-6

# Case-insensitive filename substrings that suggest a file is an assembly
# rather than a single part. If a file matching one of these imports down
# to only 1 object node, that's a possible "components missing" symptom.
ASSEMBLY_NAME_HINTS = ["ASSY", "ASSM", "ASM"]


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
    # Same recursive scene-tree walk as collectObjectNodes() in
    # 1_HLP_MAT_LOOKUP_AA01.py -- keeps node references so callers can count
    # or inspect them, not just names.
    if results is None:
        results = []
    if node.isObject():
        results.append(node)
    for child in node.getChildren():
        collectObjectNodes(child, results)
    return results


# --------------------------------------------------------------------------
# Bounding-box probe -- copied (not re-derived) from resolve_bounding_box()
# and _parse_bbox_result() in 2b_ANI_CUTAWAY_REVEAL_AA01.py and
# 2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py. See CONFIRMED vs EXPERIMENTAL header
# note above: the getBoundingBox() call itself is confirmed real; the exact
# return shape is not, so this still probes defensively.
# --------------------------------------------------------------------------

def vec_xyz(v):
    try:
        return (v[0], v[1], v[2])
    except Exception:
        pass
    try:
        return (v.x, v.y, v.z)
    except Exception:
        pass
    raise TypeError("Couldn't extract xyz from {!r}".format(v))

def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def _parse_bbox_result(result):
    """Try a couple of plausible return shapes for a bounding-box call.
    Returns (min_xyz, max_xyz) or None. The call itself is confirmed
    (getBoundingBox()); its exact return shape is not documented here."""
    if result is None:
        return None
    try:
        lo = vec_xyz(result.min)
        hi = vec_xyz(result.max)
        return lo, hi
    except Exception:
        pass
    try:
        if len(result) == 2:
            return vec_xyz(result[0]), vec_xyz(result[1])
        if len(result) == 6:
            return (result[0], result[1], result[2]), (result[3], result[4], result[5])
    except Exception:
        pass
    return None

def resolve_bounding_box(node):
    """getBoundingBox() is confirmed to exist -- see CONFIRMED vs
    EXPERIMENTAL header note. Probes a short list of plausible getter
    names/kwargs via getattr(...) for version tolerance; exact return shape
    isn't confirmed anywhere in this pipeline. Returns (min_xyz, max_xyz,
    api_name) or (None, None, None) if nothing resolved."""
    candidates = [
        ("getBoundingBox", {"world": True}),
        ("getBoundingBox", {}),
        ("getWorldBoundingBox", {}),
        ("getBounds", {"world": True}),
        ("getBounds", {}),
    ]
    for name, kwargs in candidates:
        fn = getattr(node, name, None)
        if fn is None:
            continue
        result = None
        try:
            result = fn(**kwargs) if kwargs else fn()
        except Exception:
            try:
                result = fn()
            except Exception:
                continue
        parsed = _parse_bbox_result(result)
        if parsed:
            lo, hi = parsed
            print("  Bounding box resolved via {}({}) -- min={} max={}".format(name, kwargs, lo, hi))
            return lo, hi, name
    print("  [warn] couldn't resolve a bounding box on this KeyShot version via any of "
          "getBoundingBox/getWorldBoundingBox/getBounds -- bbox check will be reported "
          "UNRESOLVED for this file. Run help(node) in the Scripting Console to find the "
          "exact call on your build.")
    return None, None, None

def bbox_volume_and_extent(lo, hi):
    dims = vsub(hi, lo)
    absDims = (abs(dims[0]), abs(dims[1]), abs(dims[2]))
    volume = absDims[0] * absDims[1] * absDims[2]
    longestEdge = max(absDims)
    return volume, longestEdge


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

MANIFEST_FIELDS = ["timestamp", "part_file", "bbox_status", "object_count",
                   "studio_camera_status", "overall_status", "notes"]

def logManifestRow(manifestPath, row):
    isNew = not os.path.isfile(manifestPath)
    with open(manifestPath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if isNew:
            writer.writeheader()
        writer.writerow(row)

def looksLikeAssembly(filename):
    upper = filename.upper()
    for hint in ASSEMBLY_NAME_HINTS:
        if hint.upper() in upper:
            return True
    return False


def main():
    if not lux.isHeadless():
        values = [("folder", lux.DIALOG_FOLDER, "Folder to trial-import from:", None),
                  ("iext", lux.DIALOG_TEXT, "Input file format to check:", "step")]
        desc = ("Trial-imports every model of a chosen extension from a folder and reports "
                "geometry/appearance health (bounding box, object count, Studio/camera "
                "presence) WITHOUT rendering -- a fast gate to run before committing a "
                "folder to the full 2a_ batch render pass.")
        opts = lux.getInputDialog(title = "Import Health Check",
                                  desc = desc,
                                  values = values,
                                  id = "importhealthcheck.py.luxion")
    else:
        opts = {}
        opts["folder"] = inputFolder("Folder to trial-import from:")
        opts["iext"] = inputText("Input file format to check:", "step")
    if not opts: return

    fld = opts["folder"]
    if len(fld) == 0:
        raise Exception("Folder cannot be empty!")

    iext = cleanExt(opts["iext"])
    if len(iext) == 0:
        raise Exception("Input extension cannot be empty!")

    manifestPath = os.path.join(fld, "import_health_manifest.csv")

    files = [f for f in os.listdir(fld) if f.lower().endswith(iext)]
    if not files:
        raise Exception("Could not find any input files matching the extension \"{}\" in \"{}\"!"
                        .format(iext, fld))

    totalChecked = 0
    totalFlagged = 0
    countImportFailed = 0
    countBboxFlag = 0
    countObjectCountFlag = 0
    countStudioCameraFlag = 0

    for f in files:
        path = fld + os.path.sep + f
        totalChecked += 1
        notes = []

        print("Checking {}".format(f))

        # -- 1. Trial import -----------------------------------------------
        try:
            lux.newScene()
            lux.importFile(path)
        except Exception as e:
            print("  [FAIL] import raised an exception: {}".format(e))
            countImportFailed += 1
            totalFlagged += 1
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "bbox_status": "N/A (import failed)",
                "object_count": "",
                "studio_camera_status": "N/A (import failed)",
                "overall_status": "FLAGGED",
                "notes": "import raised: {}".format(e),
            })
            continue

        root = lux.getSceneTree()

        # -- 2. Bounding-box sanity -----------------------------------------
        lo, hi, apiName = resolve_bounding_box(root)
        if lo is None:
            bboxStatus = "UNRESOLVED (bounding-box API unavailable on this build)"
        else:
            volume, longestEdge = bbox_volume_and_extent(lo, hi)
            if volume < NEAR_ZERO_VOLUME_EPS:
                bboxStatus = "FLAG: near-zero volume (possible degenerate/failed import)"
                notes.append("bbox volume={:.8g}".format(volume))
                countBboxFlag += 1
            elif longestEdge > SUSPICIOUS_SIZE_THRESHOLD:
                bboxStatus = "FLAG: suspiciously large bounding box (heuristic, longest edge={:.2f})".format(longestEdge)
                countBboxFlag += 1
            else:
                bboxStatus = "OK (longest edge={:.2f}, via {})".format(longestEdge, apiName)

        # -- 3. Object/mesh count sanity -------------------------------------
        objects = collectObjectNodes(root)
        objectCount = len(objects)
        assemblyLike = looksLikeAssembly(f)

        if objectCount == 0:
            objectStatus = "FLAG: empty import (0 object nodes)"
            countObjectCountFlag += 1
        elif assemblyLike and objectCount == 1:
            objectStatus = "FLAG: assembly-named file imported as a single object (possible missing components)"
            countObjectCountFlag += 1
        else:
            objectStatus = "OK"

        # -- 4. Studio/camera presence check ---------------------------------
        studios = []
        try:
            studios = lux.getStudios()
        except Exception as e:
            print("  [warn] couldn't list studios: {}".format(e))
        cameras = []
        try:
            cameras = lux.getCameras()
        except Exception as e:
            print("  [warn] couldn't list cameras: {}".format(e))

        if not studios and not cameras:
            studioCameraStatus = "FLAG: no studios or cameras (2a_ batch scripts will fall back to raw camera + whatever lighting is active)"
            countStudioCameraFlag += 1
        elif not studios:
            studioCameraStatus = "OK ({} raw camera(s), no Studios -- 2a_ will fall back to raw-camera rendering)".format(len(cameras))
        else:
            studioCameraStatus = "OK ({} studio(s))".format(len(studios))

        # -- Roll up ----------------------------------------------------------
        flags = []
        if bboxStatus.startswith("FLAG") or bboxStatus.startswith("UNRESOLVED"):
            flags.append("bbox")
        if objectStatus.startswith("FLAG"):
            flags.append("object_count")
        if studioCameraStatus.startswith("FLAG"):
            flags.append("studio_camera")

        overallStatus = "FLAGGED ({})".format(", ".join(flags)) if flags else "OK"
        if flags:
            totalFlagged += 1

        print("  bbox: {}".format(bboxStatus))
        print("  objects: {} ({})".format(objectCount, objectStatus))
        print("  studios/cameras: {}".format(studioCameraStatus))
        print("  overall: {}".format(overallStatus))

        logManifestRow(manifestPath, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "part_file": f,
            "bbox_status": bboxStatus,
            "object_count": objectCount,
            "studio_camera_status": studioCameraStatus,
            "overall_status": overallStatus,
            "notes": "; ".join(notes),
        })

    print("")
    print("{} part(s) checked, {} flagged for review.".format(totalChecked, totalFlagged))
    print("  {} import failure(s), {} bbox flag(s), {} object-count flag(s), {} studio/camera flag(s)."
          .format(countImportFailed, countBboxFlag, countObjectCountFlag, countStudioCameraFlag))
    print("Manifest written to {}".format(manifestPath))
    print("This is a fast pre-flight, not a substitute for the full 2a_ batch render pass --")
    print("a clean run here means the folder is worth committing to that batch, not that")
    print("every part is guaranteed render-ready.")

main()
