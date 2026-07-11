# -*- coding: utf-8 -*-
# AUTHOR tajf
# REV AA01
# HEADLESS COMPLIANT
"""
KeyShot Orientation / Up-Axis Sanity Check
===========================================

Trial-imports every file of a chosen extension from a folder, one at a time,
and computes a "footprint ratio" from each part's axis-aligned bounding box.
AFTER the whole folder has been processed, it looks at the spread of ratios
across the batch and flags any part whose ratio sits far outside the rest --
a statistical-outlier detector, not a per-part pass/fail check.

--------------------------------------------------------------------------
READ THIS BEFORE TRUSTING THE OUTPUT -- WHAT THIS SCRIPT ACTUALLY IS
--------------------------------------------------------------------------
This script CANNOT know a part's true intended orientation. There is no
KeyShot API that answers "is this part upside down?" -- that question
requires knowing design intent, and nothing surfaced by lux tells you that.

What it CAN do is notice when one part's proportions look statistically
different from its neighbors in the same import batch. The reasoning: if
you trial-import a whole folder of parts from the same product family, most
of them probably share a roughly consistent "resting" orientation (all
imported with the same Up Orientation setting, or all genuinely similar
shapes) -- so a part whose footprint ratio is a big outlier from the rest of
the batch is worth a human glance. It might be legitimately different (a
tall bracket mixed into a batch of flat plates is not "wrong," just
different). It might also be exactly the up-axis mismatch this check exists
to catch. This script cannot tell those two cases apart -- it can only say
"this one doesn't look like its neighbors."

This is a HEURISTIC REVIEW-FLAGGING tool. It is not an auto-fixer (it never
changes an import's orientation), and it is not a ground-truth checker (a
part can be flagged and be perfectly correct, or sail through unflagged and
still be wrong if the whole batch was imported with the same bad setting --
an outlier check can't see a mismatch that every part shares equally). Same
honest-about-uncertainty tone as this pipeline's other heuristic tools (see
1_HLP_MAT_PREFLIGHT_AA01.py's "unchanged material" check, and the GHOST
FADE / OPACITY section of 2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py for a case
where an entire feature stays openly labeled as a best-effort guess) --
flagged parts need a human look, not blind trust either way.

--------------------------------------------------------------------------
CONFIRMED vs PROBED vs HEURISTIC -- three different kinds of claim below
--------------------------------------------------------------------------
Keeping these separate on purpose, per this pipeline's documentation habit:

(a) CONFIRMED KeyShot API calls (KeyShot's own scripting reference,
    media.keyshot.com/scripting/doc/11.0/lux.html, pulled during the
    2026-07-11 research pass -- see RESEARCH_CREO_KEYSHOT.md): lux.newScene(),
    lux.importFile(path), lux.getSceneTree(), lux.isHeadless(),
    lux.getInputDialog(). SceneNode.getBoundingBox() is ALSO confirmed to
    exist and to return (min, max) vectors -- this was probed as one of
    several unconfirmed candidate names in 2b_ANI_CUTAWAY_REVEAL_AA01.py and
    2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py before that research pass landed.

(b) PROBED-BUT-NOT-FULLY-DOCUMENTED: the bounding-box call's exact return
    SHAPE. KeyShot's reference confirms the call exists and returns
    (min, max) vectors, but this pipeline has not independently confirmed
    the exact Python type of what "vector" means on your build (a tuple? an
    object with .x/.y/.z? something else?). resolve_bounding_box() and
    _parse_bbox_result() below are copied VERBATIM from
    2b_ANI_CUTAWAY_REVEAL_AA01.py rather than re-derived, keeping the same
    defensive multi-shape parsing and version-tolerant candidate probing
    (getBoundingBox(world=True), getBoundingBox(), getWorldBoundingBox(),
    getBounds(world=True), getBounds()) that script already relies on.

(c) HEURISTIC, this script's own judgment call: the footprint-ratio formula
    itself and the "more than N standard deviations from the batch mean"
    outlier rule. Neither of these is a KeyShot API claim at all -- there is
    nothing to confirm or leave unconfirmed here, it is simply a piece of
    math this script chose, documented below (see FOOTPRINT RATIO) so it can
    be judged and retuned rather than trusted blindly.

--------------------------------------------------------------------------
FOOTPRINT RATIO -- the heuristic number, and why this formula
--------------------------------------------------------------------------
KeyShot's global scene axis is always Y-up (confirmed via KeyShot's own
manual, "Position and Orientation" -- manual.keyshot.com/manual/cameras/
position-and-orientation/ -- see RESEARCH_CREO_KEYSHOT.md). That means once
a part lands in a KeyShot scene, its Y-extent is specifically KeyShot's own
notion of "height," regardless of what axis the source CAD system called
"up." X and Z extents are the two horizontal/footprint dimensions.

footprint_ratio = height / sqrt(width * depth)

  where height = Y-extent, and width/depth = X/Z extents (labels are
  arbitrary between X and Z -- KeyShot doesn't distinguish "width" from
  "depth," this script just needs consistent naming for the CSV).

Why sqrt(width * depth) rather than max(width, depth) or min(width, depth):
it's the geometric mean of the two horizontal extents, which is symmetric
(doesn't care which of X/Z is larger) and represents a single "characteristic
footprint size" rather than picking a worst-case or best-case side. A part
that is short and skinny but also long (imagine a ruler lying flat) has a
small height relative to a footprint size dominated by its length, giving a
ratio well below 1 ("flat and wide" reading) even though one horizontal
extent alone is small -- which is the intended behavior: a ruler on its side
and a ruler lying flat are very different footprint shapes, and this formula
tells them apart, whereas max(width, depth) alone would not change between
"lying flat" and "standing on end and rotated" as cleanly. A ratio near 1.0
reads as roughly cubic; ratios well above 1.0 read as tall and narrow;
ratios well below 1.0 read as flat and wide. This is a documented judgment
call, not a derived law -- a different formula (e.g. height / max(width,
depth)) is equally defensible and could be swapped in here if it matches
your part families better.

--------------------------------------------------------------------------
OUTLIER DETECTION -- two-pass, relative to the batch, not an absolute rule
--------------------------------------------------------------------------
A batch of tall narrow brackets and a batch of flat wide plates are both
"normal" for their own family, just different from each other -- there is
no single absolute footprint-ratio threshold that means "wrong" across every
possible batch. So this script runs in two passes: gather every part's
extents and footprint ratio FIRST (import loop, no flagging), then AFTER the
whole folder is done, compute the batch's mean and standard deviation of
footprint ratios (stdlib `statistics` module, no numpy) and flag any part
whose ratio is more than OUTLIER_STD_DEV_THRESHOLD standard deviations from
that mean. The threshold is a tunable constant below, same pattern as
PADDING_FACTOR in 2a_BAT_STD_VIEW_AA01.py.

Small batches make sample standard deviation meaningless (and a batch of 1
makes it undefined -- division by zero). MIN_PARTS_FOR_OUTLIER_CHECK guards
this: below that count, outlier flagging is skipped entirely for the whole
run, with a clear printed message, rather than computing and printing a
number that would just be noise.

--------------------------------------------------------------------------
NO RENDERING
--------------------------------------------------------------------------
Same fast/cheap pre-flight design as 1_HLP_MAT_PREFLIGHT_AA01.py and its
stage-0_ siblings -- this only imports and measures, never calls
lux.renderImage(). Meant to run in seconds ahead of a full batch.

Run inside the KeyShot Scripting Console, or via `keyshot -script` headless
(dialog auto-skips headless -> falls back to input()-based prompts, same
dual-path pattern as 2a_BAT_STD_VIEW_AA01.py's main()).
"""

import os, re, sys
import os.path
import csv
import statistics
from datetime import datetime

# How many standard deviations a part's footprint ratio must be from the
# batch mean before it gets flagged as an orientation outlier worth a human
# look. Lower = more sensitive (more flags, more false positives). Higher =
# fewer flags, easier to miss a real mismatch. 2.0 is a reasonable starting
# point (roughly the "clearly stands out" range for a normal-ish spread) --
# tune to taste per part family. Same tunable-constant pattern as
# PADDING_FACTOR in 2a_BAT_STD_VIEW_AA01.py.
OUTLIER_STD_DEV_THRESHOLD = 2.0

# Below this many parts in the batch, sample standard deviation isn't a
# meaningful comparison group (and at 1 part it's undefined -- division by
# zero) -- outlier flagging is skipped entirely and a clear message is
# printed instead of a bogus number.
MIN_PARTS_FOR_OUTLIER_CHECK = 4

MANIFEST_FIELDS = ["timestamp", "part_file", "base_name", "width_x", "height_y", "depth_z",
                    "footprint_ratio", "outlier_flag", "status"]


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


def inputText(msg, default):
    return genericInput(msg, default=default)


def cleanExt(ext):
    while ext.startswith("."):
        ext = ext[1:]
    return ext.lower()


def stripExt(filename, ext):
    # Strips a trailing ".ext" (case-insensitive) from filename if present.
    lower = filename.lower()
    dotExt = "." + ext
    if lower.endswith(dotExt):
        return filename[:-len(dotExt)]
    if lower.endswith(ext):
        return filename[:-len(ext)]
    return filename


# --------------------------------------------------------------------------
# Vector helper (same shape as the sibling 2b_ scripts)
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


# --------------------------------------------------------------------------
# getBoundingBox() is confirmed to exist (2026-07-11 research pass -- see
# module docstring, section (a)). Copied VERBATIM from
# 2b_ANI_CUTAWAY_REVEAL_AA01.py's resolve_bounding_box()/_parse_bbox_result()
# rather than re-derived, per the assignment brief -- the exact return shape
# is still probed defensively for version tolerance (see docstring section (b)).
# --------------------------------------------------------------------------

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
    """getBoundingBox() is confirmed to exist -- see module docstring
    section (a)/(b). Probes a short list of plausible getter names/kwargs
    via getattr(...) for version tolerance; exact return shape isn't
    confirmed anywhere in this pipeline. Returns (min_xyz, max_xyz, api_name)
    or (None, None, None) if nothing resolved."""
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
          "getBoundingBox/getWorldBoundingBox/getBounds -- this part will be skipped from "
          "the orientation check. Run help(node) in the Scripting Console to find the exact "
          "call on your build.")
    return None, None, None


# --------------------------------------------------------------------------
# Footprint ratio -- HEURISTIC, this script's own judgment call. See module
# docstring "FOOTPRINT RATIO" section for the reasoning behind this formula.
# --------------------------------------------------------------------------

def compute_footprint_ratio(lo_xyz, hi_xyz):
    """Returns (width_x, height_y, depth_z, footprint_ratio) or None if the
    extents are degenerate (zero-size on a horizontal axis -- can't take a
    meaningful geometric mean of a zero, and a genuinely flat/2D import is
    an edge case this heuristic isn't meant to reason about anyway)."""
    width_x = hi_xyz[0] - lo_xyz[0]
    height_y = hi_xyz[1] - lo_xyz[1]
    depth_z = hi_xyz[2] - lo_xyz[2]

    footprint_size = (width_x * depth_z) ** 0.5 if (width_x > 0 and depth_z > 0) else 0.0
    if footprint_size <= 0.0:
        return width_x, height_y, depth_z, None

    return width_x, height_y, depth_z, height_y / footprint_size


def main():
    if not lux.isHeadless():
        values = [("folder", lux.DIALOG_FOLDER, "Folder to import from:", None),
                  ("iext", lux.DIALOG_TEXT, "Input file format to read:", "bip")]
        desc = ("Trial-imports every model of a chosen extension and flags parts whose "
                 "proportions (footprint ratio) are statistical outliers relative to the "
                 "rest of the batch -- a heuristic hint that orientation/up-axis might be "
                 "off, not a certainty. See script header before trusting the output.")
        opts = lux.getInputDialog(title="Orientation / Up-Axis Sanity Check",
                                   desc=desc,
                                   values=values,
                                   id="orientationcheck.py.luxion")
    else:
        opts = {}
        opts["folder"] = inputFolder("Folder to import from:")
        opts["iext"] = inputText("Input file format to read:", "bip")
    if not opts:
        return

    fld = opts["folder"]
    if len(fld) == 0:
        raise Exception("Folder cannot be empty!")

    iext = cleanExt(opts["iext"])
    if len(iext) == 0:
        raise Exception("Input extension cannot be empty!")

    files = [f for f in os.listdir(fld) if f.lower().endswith(iext)]
    if not files:
        raise Exception("Could not find any input files matching the extension \"{}\" in \"{}\"!"
                        .format(iext, fld))

    manifestPath = os.path.join(fld, "orientation_check_manifest.csv")

    # ---------------------------------------------------------------------
    # Pass 1: import every part, measure extents + footprint ratio. No
    # flagging happens yet -- outliers only make sense relative to the
    # whole batch, computed after every part has been measured.
    # ---------------------------------------------------------------------
    measurements = []  # list of dicts: file, base_name, width, height, depth, ratio
    skipped = 0

    for f in files:
        path = fld + os.path.sep + f
        lux.newScene()

        print("Importing {}".format(path))
        try:
            lux.importFile(path)
        except Exception as e:
            print("  [warn] couldn't import '{}': {} -- skipping".format(f, e))
            skipped += 1
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": stripExt(f, iext),
                "width_x": "", "height_y": "", "depth_z": "",
                "footprint_ratio": "", "outlier_flag": "",
                "status": "FAILED (import)",
            })
            continue

        baseName = stripExt(f, iext)
        root = lux.getSceneTree()

        lo, hi, bbox_api = resolve_bounding_box(root)
        if lo is None or hi is None:
            skipped += 1
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": baseName,
                "width_x": "", "height_y": "", "depth_z": "",
                "footprint_ratio": "", "outlier_flag": "",
                "status": "SKIPPED (no bounding box)",
            })
            continue

        width_x, height_y, depth_z, ratio = compute_footprint_ratio(lo, hi)
        if ratio is None:
            print("  [warn] degenerate horizontal extents for '{}' (width={:.4f}, depth={:.4f}) -- "
                  "footprint ratio can't be computed, skipping from the outlier comparison."
                  .format(f, width_x, depth_z))
            skipped += 1
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": f,
                "base_name": baseName,
                "width_x": "{:.4f}".format(width_x),
                "height_y": "{:.4f}".format(height_y),
                "depth_z": "{:.4f}".format(depth_z),
                "footprint_ratio": "", "outlier_flag": "",
                "status": "SKIPPED (degenerate extents)",
            })
            continue

        print("  extents: width(X)={:.4f} height(Y)={:.4f} depth(Z)={:.4f} -> footprint_ratio={:.4f}"
              .format(width_x, height_y, depth_z, ratio))

        measurements.append({
            "part_file": f,
            "base_name": baseName,
            "width_x": width_x,
            "height_y": height_y,
            "depth_z": depth_z,
            "ratio": ratio,
        })

    # ---------------------------------------------------------------------
    # Pass 2: batch-relative outlier detection. Requires a real comparison
    # group -- see MIN_PARTS_FOR_OUTLIER_CHECK / module docstring.
    # ---------------------------------------------------------------------
    outlierFlaggedCount = 0

    if len(measurements) < MIN_PARTS_FOR_OUTLIER_CHECK:
        print("")
        print("Only {} part(s) produced a usable footprint ratio (minimum {} needed for a "
              "meaningful comparison group) -- orientation outlier flagging was SKIPPED for "
              "lack of a comparison group. Every part's raw extents are still in the manifest."
              .format(len(measurements), MIN_PARTS_FOR_OUTLIER_CHECK))
        for m in measurements:
            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": m["part_file"],
                "base_name": m["base_name"],
                "width_x": "{:.4f}".format(m["width_x"]),
                "height_y": "{:.4f}".format(m["height_y"]),
                "depth_z": "{:.4f}".format(m["depth_z"]),
                "footprint_ratio": "{:.4f}".format(m["ratio"]),
                "outlier_flag": "N/A (batch too small)",
                "status": "measured",
            })
    else:
        ratios = [m["ratio"] for m in measurements]
        mean_ratio = statistics.mean(ratios)
        stdev_ratio = statistics.stdev(ratios)  # sample stdev; len>=2 guaranteed by the branch above

        print("")
        print("Batch footprint ratio: mean={:.4f} stdev={:.4f} (n={})"
              .format(mean_ratio, stdev_ratio, len(ratios)))

        for m in measurements:
            if stdev_ratio > 0:
                deviation = abs(m["ratio"] - mean_ratio) / stdev_ratio
            else:
                # Every part in the batch has (near-)identical ratios -- no
                # spread to be an outlier from.
                deviation = 0.0
            isOutlier = deviation > OUTLIER_STD_DEV_THRESHOLD
            if isOutlier:
                outlierFlaggedCount += 1
                print("  FLAGGED: '{}' footprint_ratio={:.4f} is {:.2f} std dev from batch mean "
                      "({:.4f}) -- worth a human look, not necessarily wrong."
                      .format(m["part_file"], m["ratio"], deviation, mean_ratio))

            logManifestRow(manifestPath, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "part_file": m["part_file"],
                "base_name": m["base_name"],
                "width_x": "{:.4f}".format(m["width_x"]),
                "height_y": "{:.4f}".format(m["height_y"]),
                "depth_z": "{:.4f}".format(m["depth_z"]),
                "footprint_ratio": "{:.4f}".format(m["ratio"]),
                "outlier_flag": "OUTLIER" if isOutlier else "ok",
                "status": "measured",
            })

    print("")
    print("{} part(s) checked, {} flagged as orientation outlier(s) (>{:.1f} std dev from batch "
          "mean footprint ratio).".format(len(measurements), outlierFlaggedCount, OUTLIER_STD_DEV_THRESHOLD))
    if skipped:
        print("{} part(s) skipped (import failure, no bounding box, or degenerate extents) -- "
              "see manifest for details.".format(skipped))
    if outlierFlaggedCount:
        print("Flagged parts are a heuristic hint, not a verdict -- this script cannot know a "
              "part's true intended orientation. Give each flagged part a human look before "
              "assuming anything is actually wrong.")
    print("Manifest written to {}".format(manifestPath))


main()
