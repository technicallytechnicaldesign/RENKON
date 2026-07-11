# -*- coding: utf-8 -*-
# AUTHOR tajf
# REV AA01
# Standalone Python 3 script -- NOT a KeyShot script, run this with a regular
# Python interpreter. Two independent checks against a target folder:
#
#   1. Naming-compliance audit -- scans a folder of *.py pipeline scripts and
#      validates each filename against the {PREFIX}_{AREA}_{NAME}_{REV}.py
#      convention documented in keyshot/README.md, reporting exactly which
#      component is wrong rather than a generic pass/fail.
#   2. Render-completeness audit -- finds every *_manifest.csv in a folder
#      (render_manifest.csv, reveal_manifest.csv, cutaway_manifest.csv,
#      material_lookup_manifest.csv, etc.), cross-checks each row's output
#      path against what's actually on disk, and flags rows whose status
#      looks like a failure/skip separately from rows whose file just isn't
#      there.
#
# Usage:
#   python 4_CHK_AUDIT_AA01.py /path/to/scripts_or_output_folder
# or just run it with no arguments and it'll ask.

import os
import re
import csv
import sys
import glob

# ---------------------------------------------------------------------------
# Check 1: naming-compliance audit
# ---------------------------------------------------------------------------

VALID_PREFIXES = ("0", "1", "2a", "2b", "3", "4")
AREA_RE = re.compile(r"^[A-Z]{3}$")
NAME_WORD_RE = re.compile(r"^[A-Z0-9]+$")
REV_RE = re.compile(r"^[A-Z]{2}[0-9]{2}$")

# README says NAME is "2-4 words" as a style guideline, but the real script
# set already includes legitimate single-word names (TURNTABLE, AUDIT), so
# word count is reported as a note, not treated as a compliance failure.
NAME_WORD_COUNT_RANGE = (2, 4)


def auditFilename(filename):
    """Returns (isCompliant, issues, notes) for one *.py filename.

    issues -- list of strings, each a specific reason the file is NOT
    compliant (empty list means compliant).
    notes -- list of strings, non-blocking observations (e.g. NAME word
    count outside the 2-4 style guideline) that don't fail the file.
    """
    issues = []
    notes = []

    if not filename.lower().endswith(".py"):
        return False, ["not a .py file"], notes

    stem = filename[:-3]
    parts = stem.split("_")

    if len(parts) < 4:
        issues.append(
            "not enough underscore-separated components for PREFIX_AREA_NAME_REV "
            "(found {}: {})".format(len(parts), parts)
        )
        return False, issues, notes

    prefix, area, revToken = parts[0], parts[1], parts[-1]
    nameParts = parts[2:-1]

    if prefix not in VALID_PREFIXES:
        issues.append(
            "invalid PREFIX '{}' (expected one of {})".format(prefix, ", ".join(VALID_PREFIXES))
        )

    if not AREA_RE.match(area):
        issues.append(
            "invalid AREA '{}' (expected exactly 3 uppercase letters)".format(area)
        )

    if not REV_RE.match(revToken):
        issues.append(
            "invalid REV '{}' (expected shape LLNN, e.g. AA01)".format(revToken)
        )

    if not nameParts:
        issues.append("missing NAME (no component between AREA and REV)")
    else:
        badWords = [w for w in nameParts if not NAME_WORD_RE.match(w)]
        if badWords:
            issues.append(
                "invalid NAME word(s) {} (expected uppercase letters/digits only)".format(badWords)
            )
        elif not (NAME_WORD_COUNT_RANGE[0] <= len(nameParts) <= NAME_WORD_COUNT_RANGE[1]):
            notes.append(
                "NAME has {} word(s) ({}); README style guideline is 2-4".format(
                    len(nameParts), "_".join(nameParts)
                )
            )

    return (len(issues) == 0), issues, notes


def collectPyFiles(rootFolder):
    """Walks rootFolder for *.py files, skipping anything under a subfolder
    literally named 'archive' (case-insensitive) -- those are pre-convention
    on purpose (see keyshot/SCRIPT_STOCK.md archive entries)."""
    found = []
    for dirpath, dirnames, filenames in os.walk(rootFolder):
        dirnames[:] = [d for d in dirnames if d.lower() != "archive"]
        for f in filenames:
            if f.lower().endswith(".py"):
                found.append(os.path.join(dirpath, f))
    return sorted(found)


def runNamingAudit(scriptsFolder):
    print("=" * 70)
    print("CHECK 1 -- naming compliance ({})".format(scriptsFolder))
    print("=" * 70)

    pyFiles = collectPyFiles(scriptsFolder)
    if not pyFiles:
        print("No .py files found (outside of any 'archive' subfolder).")
        return

    compliantCount = 0
    nonCompliant = []

    for fullPath in pyFiles:
        filename = os.path.basename(fullPath)
        relPath = os.path.relpath(fullPath, scriptsFolder)
        isCompliant, issues, notes = auditFilename(filename)
        if isCompliant:
            compliantCount += 1
            tag = "OK"
            if notes:
                tag += " (note: {})".format("; ".join(notes))
            print("  [{}] {}".format(tag, relPath))
        else:
            nonCompliant.append((relPath, issues))
            print("  [FAIL] {}".format(relPath))
            for issue in issues:
                print("           - {}".format(issue))

    print("")
    print("Naming audit: {} of {} file(s) compliant.".format(compliantCount, len(pyFiles)))
    if nonCompliant:
        print("{} file(s) need a rename before they're pipeline-compliant.".format(len(nonCompliant)))
    else:
        print("Everything in scope matches {PREFIX}_{AREA}_{NAME}_{REV}.py.")


# ---------------------------------------------------------------------------
# Check 2: render-completeness audit
# ---------------------------------------------------------------------------

# Column name candidates for the "where did this render go" field, tried in
# order -- every manifest observed in this pipeline as of today uses
# "output_path", but this list keeps the check tolerant of minor schema
# drift between scripts.
OUTPUT_PATH_COLUMNS = ("output_path", "outputPath", "output_file", "path")

# Heuristic classifier only -- built from the status strings actually used
# across this pipeline's manifests as of 2026-07-11 (render_manifest.csv,
# reveal_manifest.csv, cutaway_manifest.csv, material_lookup_manifest.csv).
# New scripts may introduce new status strings this won't recognize; those
# fall into the "unclassified" bucket below rather than being silently
# miscounted as good or bad.
FAILURE_MARKERS = ("fail", "skip", "miss")
SUCCESS_MARKERS = ("queued", "encoded", "applied", "hit")


def classifyStatus(status):
    """Returns 'ok', 'bad', or 'unknown' for a manifest status string."""
    if status is None:
        return "unknown"
    s = status.strip().lower()
    if not s:
        return "unknown"
    if any(marker in s for marker in FAILURE_MARKERS):
        return "bad"
    if any(marker in s for marker in SUCCESS_MARKERS):
        return "ok"
    return "unknown"


def findOutputPath(row):
    for col in OUTPUT_PATH_COLUMNS:
        val = row.get(col)
        if val:
            return val, col
    return None, None


def runRenderCompletenessAudit(targetFolder):
    print("")
    print("=" * 70)
    print("CHECK 2 -- render completeness ({})".format(targetFolder))
    print("=" * 70)

    manifestPaths = sorted(glob.glob(os.path.join(targetFolder, "*_manifest.csv")))
    if not manifestPaths:
        print("No *_manifest.csv files found in this folder.")
        return

    totalRows = 0
    existingFiles = 0
    missingFiles = 0
    badStatusRows = []
    unclassifiedStatuses = set()

    for manifestPath in manifestPaths:
        manifestName = os.path.basename(manifestPath)
        with open(manifestPath, "r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rowsInThisManifest = 0
            for row in reader:
                rowsInThisManifest += 1
                totalRows += 1

                outputPath, matchedCol = findOutputPath(row)
                status = row.get("status")
                statusClass = classifyStatus(status)

                if statusClass == "unknown" and status:
                    unclassifiedStatuses.add(status)

                fileExists = False
                if outputPath:
                    checkPath = outputPath
                    if not os.path.isabs(checkPath):
                        checkPath = os.path.join(targetFolder, checkPath)
                    fileExists = os.path.isfile(checkPath)

                if fileExists:
                    existingFiles += 1
                else:
                    missingFiles += 1

                if statusClass == "bad":
                    badStatusRows.append((manifestName, outputPath, status))

        print("  {} -- {} row(s)".format(manifestName, rowsInThisManifest))

    print("")
    print("Render completeness: {} manifest row(s) across {} manifest file(s).".format(
        totalRows, len(manifestPaths)))
    print("  {} row(s) point at a file that exists on disk right now.".format(existingFiles))
    print("  {} row(s) point at a file that is NOT currently on disk.".format(missingFiles))

    if badStatusRows:
        print("")
        print("{} row(s) have a status that looks like a failure/skip (flagged separately".format(
            len(badStatusRows)))
        print("from missing-file cases, since 'status says failed' and 'file just isn't there")
        print("yet' are different problems):")
        for manifestName, outputPath, status in badStatusRows:
            print("    [{}] status='{}' output_path='{}'".format(manifestName, status, outputPath))
    else:
        print("No rows with a recognizably bad status.")

    if unclassifiedStatuses:
        print("")
        print("Note: {} status string(s) didn't match the known-good/known-bad heuristic".format(
            len(unclassifiedStatuses)))
        print("and were left unclassified (not counted as either): {}".format(
            sorted(unclassifiedStatuses)))
        print("This classifier is a heuristic against status strings observed in this pipeline")
        print("as of today -- it is not guaranteed exhaustive.")


# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) > 1:
        targetFolder = sys.argv[1]
    else:
        targetFolder = input("Folder to audit (scripts folder and/or render output folder): ").strip()

    if not os.path.isdir(targetFolder):
        print("Not a folder: {}".format(targetFolder))
        sys.exit(1)

    runNamingAudit(targetFolder)
    runRenderCompletenessAudit(targetFolder)


if __name__ == "__main__":
    main()
