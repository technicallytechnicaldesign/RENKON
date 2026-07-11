# -*- coding: utf-8 -*-
# AUTHOR claude-subagent
# REV AA01
# Standalone Python 3 script -- NOT a KeyShot script, NOT a lux script. Run
# this with a regular Python interpreter, on a folder of *.step/*.stp files,
# BEFORE any of this pipeline's 2a_/2b_ batch scripts touch them.
#
# Why this exists: scale/unit mismatch on import is the single most commonly
# reported KeyShot import complaint (KeyShot's own import dialog has a
# "Geometry Unit" dropdown specifically because this goes wrong so often --
# see the "Research pass (2026-07-11)" section of keyshot/RESEARCH_CREO_KEYSHOT.md
# for the forum-grounded writeup this script is built from). STEP (ISO
# 10303-21) is a plain-text exchange format, so a unit mismatch can be
# caught by reading the file as text -- no CAD kernel, no lux API, no
# KeyShot instance required.
#
# Four independent checks against a target folder of STEP files:
#   1. Unit/scale declaration  -- regex-extract the declared linear unit and
#      flag anything that isn't EXPECTED_UNIT, or where no unit could be
#      found at all.
#   2. Filename hygiene        -- flag characters that would break or
#      surprise this pipeline's "{baseName}_{view}.{ext}" output naming
#      (2a_BAT_STD_VIEW_AA01.py / 2a_BAT_TURNTABLE_AA01.py).
#   3. Duplicate base names    -- case-insensitive collision check, since
#      "Bracket.step" and "bracket.STEP" would both output "Bracket_*" and
#      clobber each other.
#   4. Material-name hints     -- best-effort text scan for a PRODUCT-level
#      "material" PROPERTY_DEFINITION; optionally cross-referenced against a
#      1_HLP_MAT_LOOKUP_AA01.py-format mapping file if one is supplied.
#
# -----------------------------------------------------------------------
# HONESTY NOTE -- this is a regex heuristic against ISO-10303-21 text, NOT
# a real STEP/EXPRESS parser
# -----------------------------------------------------------------------
# A real STEP reader resolves entity references across a graph (#89 points
# at #57 points at #12, etc). None of that is attempted here -- these are
# flat regex scans against the raw file text, same "confirmed vs. heuristic"
# discipline this pipeline already applies to unconfirmed KeyShot API calls
# (see 1_HLP_MAT_LOOKUP_AA01.py's OBJECT_TEMPLATE_SETTERS probe, or the
# candidate-list probes in the 2b_ANI_* scripts). That means:
#   - Exporter-specific whitespace/line-wrapping quirks can defeat the
#     regexes below. When a unit can't be found, this script says so
#     explicitly ("unknown -- review manually") rather than assuming
#     compliance.
#   - The material-hint scan does not walk entity references, so it can
#     miss materials that are one hop away from the PROPERTY_DEFINITION
#     entity it matches, or report a name fragment that isn't the full
#     descriptive string. Treat hits as leads to check by eye, not ground
#     truth.
# Confirmed against a real source: the mm SI_UNIT format below is verified
# against the Open Cascade developer forum's documented example
# (#89=(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.));) -- see
# RESEARCH_CREO_KEYSHOT.md. Everything else here (CONVERSION_BASED_UNIT
# inch detection, material-hint scan) is this script's own best-effort
# heuristic, not verified against a spec or forum example, and is
# documented as such inline.
#
# Usage:
#   python 0_VAL_STEP_PREFLIGHT_AA01.py /path/to/step/folder [mapping.csv|mapping.json]
# or just run it with no arguments and it'll ask (mapping file is optional --
# press enter to skip it).

import os
import re
import sys
import csv
import json

# ---------------------------------------------------------------------------
# Config -- edit these constants, same spirit as PADDING_FACTOR in the 2a_
# batch scripts or HOLD_SECONDS/FADE_SECONDS in 3_PRC_FADE_REEL_AA01.py.
# ---------------------------------------------------------------------------

# This pipeline's working assumption elsewhere is millimeters; none of the
# 2a_/2b_ scripts hardcode a unit, so this is a sensible default, not a
# confirmed pipeline-wide contract. Edit per-project if your source CAD
# exports in something else.
EXPECTED_UNIT = "MM"

STEP_EXTENSIONS = (".step", ".stp")

# Characters considered "safe" in a source filename (before the extension).
# Anything outside this set can produce a broken or surprising output path
# once run through "{baseName}_{view}.{ext}".format(...) downstream.
SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


# ---------------------------------------------------------------------------
# Check 1: unit / scale declaration
# ---------------------------------------------------------------------------

# Matches the confirmed SI_UNIT(prefix, base) shape, e.g.
#   SI_UNIT(.MILLI.,.METRE.)
#   SI_UNIT($,.METRE.)                 <- bare base unit, no prefix
# Whitespace/line-wrapping is exporter-dependent, hence \s* everywhere and
# re.DOTALL when scanning (a declaration can be split across lines).
SI_UNIT_RE = re.compile(
    r"SI_UNIT\s*\(\s*(\$|\.[A-Z]*\.)\s*,\s*\.([A-Z]+)\.\s*\)",
    re.IGNORECASE,
)

# CONVERSION_BASED_UNIT entities are how STEP expresses non-SI units (most
# commonly inch) -- a named unit defined as a numeric factor times an SI
# base unit, rather than a dedicated non-SI unit type. There is no single
# fixed textual shape for this across exporters, so this is a best-effort
# heuristic: look for the CONVERSION_BASED_UNIT keyword, then look nearby
# for a numeric literal close to the well-known inch-to-mm factor (25.4).
CONVERSION_BASED_UNIT_RE = re.compile(r"CONVERSION_BASED_UNIT", re.IGNORECASE)
INCH_FACTOR_RE = re.compile(r"\b25\.4\b")
# Loosely: how far (in characters) to look around a CONVERSION_BASED_UNIT
# hit for a nearby 25.4 literal. STEP entities referencing each other by
# number aren't necessarily textually adjacent, so this is a window guess,
# not a graph walk -- documented limitation, see header note.
CONVERSION_SEARCH_WINDOW = 400

PREFIX_MULTIPLIERS = {
    "": "M",       # bare base unit, no SI prefix -> base unit itself
    "MILLI": "MM",
    "CENTI": "CM",
    "KILO": "KM",
}


def normalizeSiUnit(prefixToken, baseToken):
    """Turns a (prefix, base) SI_UNIT regex match into a simple string like
    "MM", "CM", "M", "KM". Returns None if the base unit isn't METRE (this
    script only cares about linear units) or the prefix isn't one this
    script recognizes."""
    base = baseToken.strip().upper()
    if base != "METRE":
        return None

    prefix = prefixToken.strip()
    if prefix in ("$", ""):
        prefixKey = ""
    else:
        prefixKey = prefix.strip(".").upper()

    return PREFIX_MULTIPLIERS.get(prefixKey)


def detectUnit(text):
    """Returns (unitString or None, detectionMethod string) for one STEP
    file's raw text. unitString is one of "MM"/"CM"/"M"/"KM"/"INCH
    (conversion-based)", or None if nothing could be detected."""

    # Check CONVERSION_BASED_UNIT + nearby 25.4 first (inch-based exports,
    # common on US-locale CAD systems). This has to run BEFORE the plain
    # SI_UNIT check below: a CONVERSION_BASED_UNIT entity is itself defined
    # in terms of an underlying SI_UNIT (e.g. inch-as-25.4-mm), so a file
    # with an inch geometry unit will ALSO contain a legitimate millimeter
    # SI_UNIT declaration -- that SI_UNIT describes the conversion's base,
    # not the geometry's actual unit. Checking conversion-based first
    # avoids misreporting an inch file as millimeters. Best-effort only --
    # see header note.
    for m in CONVERSION_BASED_UNIT_RE.finditer(text):
        windowStart = max(0, m.start() - CONVERSION_SEARCH_WINDOW)
        windowEnd = min(len(text), m.end() + CONVERSION_SEARCH_WINDOW)
        window = text[windowStart:windowEnd]
        if INCH_FACTOR_RE.search(window):
            return "INCH (conversion-based)", "CONVERSION_BASED_UNIT+25.4"

    # Try every SI_UNIT match, prefer the first that resolves to a linear
    # (METRE-based) unit this script recognizes. A file can carry SI_UNIT
    # declarations for other quantities (angle, solid angle) too, hence
    # "try every match" rather than just the first.
    for m in SI_UNIT_RE.finditer(text):
        unit = normalizeSiUnit(m.group(1), m.group(2))
        if unit:
            return unit, "SI_UNIT"

    return None, None


# ---------------------------------------------------------------------------
# Check 2: filename hygiene
# ---------------------------------------------------------------------------

def findUnsafeChars(stem):
    """Returns the sorted set of characters in stem that fall outside the
    safe filename set (letters, digits, underscore, hyphen)."""
    bad = set()
    for ch in stem:
        if not re.match(r"[A-Za-z0-9_\-]", ch):
            bad.add(ch)
    return sorted(bad)


# ---------------------------------------------------------------------------
# Check 4: best-effort material-name hint extraction
# ---------------------------------------------------------------------------

# Looks for a PROPERTY_DEFINITION entity whose descriptive text/name field
# contains something resembling "material" (case-insensitive), then grabs
# whatever quoted strings appear on that same entity line as candidate hint
# text. This does NOT resolve entity references (a real STEP property graph
# requires following #-numbered pointers to a separate representation_item /
# descriptive_representation_item entity for the actual value) -- see
# header note. Treat any hit as "worth a human glance", not a confirmed
# material name.
PROPERTY_DEFINITION_RE = re.compile(
    r"PROPERTY_DEFINITION\s*\([^)]*\)", re.IGNORECASE
)
QUOTED_STRING_RE = re.compile(r"'([^']*)'")


def findMaterialHints(text):
    """Returns a list of candidate material-name-ish strings found via the
    PROPERTY_DEFINITION heuristic described above. Best-effort, may find
    nothing even on files that do carry material data some other way."""
    hints = []
    for m in PROPERTY_DEFINITION_RE.finditer(text):
        entityText = m.group(0)
        if "material" not in entityText.lower():
            continue
        quoted = QUOTED_STRING_RE.findall(entityText)
        for q in quoted:
            qClean = q.strip()
            if qClean and qClean.lower() != "material":
                hints.append(qClean)
    # De-dupe while preserving order.
    seen = set()
    deduped = []
    for h in hints:
        key = h.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(h)
    return deduped


def loadMappingCsv(path):
    mapping = {}
    with open(path, "r", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "creo_material" not in reader.fieldnames or "keyshot_template" not in reader.fieldnames:
            raise Exception(
                "Mapping CSV must have a header row with columns "
                "'creo_material,keyshot_template' -- got {}".format(reader.fieldnames)
            )
        for row in reader:
            key = (row.get("creo_material") or "").strip().lower()
            val = (row.get("keyshot_template") or "").strip()
            if key and val and key not in mapping:
                mapping[key] = val
    return mapping


def loadMappingJson(path):
    with open(path, "r") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise Exception("Mapping JSON must be a flat object of {\"creo_material\": \"keyshot_template\"} pairs.")
    mapping = {}
    for key, val in raw.items():
        k = (key or "").strip().lower()
        v = (val or "").strip()
        if k and v and k not in mapping:
            mapping[k] = v
    return mapping


def loadMapping(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "json":
        mapping = loadMappingJson(path)
    else:
        mapping = loadMappingCsv(path)
    if not mapping:
        raise Exception(
            "Mapping file '{}' loaded but contained no usable creo_material -> "
            "keyshot_template pairs.".format(path)
        )
    return mapping


# ---------------------------------------------------------------------------
# Folder scan
# ---------------------------------------------------------------------------

def collectStepFiles(folder):
    found = []
    for f in sorted(os.listdir(folder)):
        full = os.path.join(folder, f)
        if not os.path.isfile(full):
            continue
        if f.lower().endswith(STEP_EXTENSIONS):
            found.append(f)
    return found


def readStepText(folder, filename):
    """Reads a STEP file as plain text. STEP is ASCII per ISO 10303-21, but
    tolerate stray non-ASCII bytes (some exporters embed them in string
    literals) rather than crashing the whole preflight on one bad file."""
    path = os.path.join(folder, filename)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def runUnitCheck(folder, stepFiles, fileTextCache):
    print("=" * 70)
    print("CHECK 1 -- unit / scale declaration (expecting {})".format(EXPECTED_UNIT))
    print("=" * 70)

    okCount = 0
    mismatchCount = 0
    unknownCount = 0

    for f in stepFiles:
        text = fileTextCache[f]
        unit, method = detectUnit(text)

        if unit is None:
            unknownCount += 1
            print("  [FAIL] {} -- no unit declaration found (unknown -- review manually)".format(f))
        elif unit == EXPECTED_UNIT:
            okCount += 1
            print("  [OK] {} -- detected {} (via {})".format(f, unit, method))
        else:
            mismatchCount += 1
            print("  [FAIL] {} -- detected {} (via {}), expected {}".format(f, unit, method, EXPECTED_UNIT))

    print("")
    print("Unit check: {} of {} file(s) match {}, {} mismatch(es), {} undetected."
          .format(okCount, len(stepFiles), EXPECTED_UNIT, mismatchCount, unknownCount))
    if mismatchCount or unknownCount:
        print("Mismatched or undetected files should be reviewed by hand -- and, for mismatches,")
        print("re-exported at the expected scale or explicitly rescaled on import (KeyShot's own")
        print("import dialog has a Geometry Unit override for exactly this case).")


def runFilenameHygieneCheck(folder, stepFiles):
    print("")
    print("=" * 70)
    print("CHECK 2 -- filename hygiene")
    print("=" * 70)

    okCount = 0
    badCount = 0

    for f in stepFiles:
        stem = os.path.splitext(f)[0]
        badChars = findUnsafeChars(stem)
        if badChars:
            badCount += 1
            print("  [FAIL] {} -- unsafe character(s): {}".format(f, badChars))
        else:
            okCount += 1
            print("  [OK] {}".format(f))

    print("")
    print("Filename hygiene: {} of {} file(s) clean, {} flagged.".format(okCount, len(stepFiles), badCount))
    if badCount:
        print("Downstream output naming is \"{baseName}_{view}.{ext}\" (2a_BAT_STD_VIEW_AA01.py /")
        print("2a_BAT_TURNTABLE_AA01.py) -- spaces, non-ASCII characters, or path separators in a")
        print("source filename will produce a broken or surprising output path.")


def runDuplicateCheck(folder, stepFiles):
    print("")
    print("=" * 70)
    print("CHECK 3 -- duplicate base names (case-insensitive)")
    print("=" * 70)

    groups = {}  # lowercased stem -> [original filenames]
    for f in stepFiles:
        stem = os.path.splitext(f)[0]
        key = stem.lower()
        groups.setdefault(key, []).append(f)

    collisions = {k: v for k, v in groups.items() if len(v) > 1}

    if not collisions:
        print("No collisions -- every base name is unique (case-insensitive).")
    else:
        for key, filenames in sorted(collisions.items()):
            print("  [FAIL] base name '{}' collides across: {}".format(key, filenames))

    print("")
    print("Duplicate check: {} collision group(s) across {} file(s).".format(len(collisions), len(stepFiles)))
    if collisions:
        print("These would clobber each other's output once run through this pipeline's")
        print("\"{baseName}_{view}.{ext}\" naming -- rename before batch-processing.")


def runMaterialHintCheck(folder, stepFiles, fileTextCache, mapping):
    print("")
    print("=" * 70)
    print("CHECK 4 -- material-name hints (best-effort text scan, not a real")
    print("           STEP property-definition graph walk)")
    print("=" * 70)

    filesWithHints = 0
    filesWithoutHints = 0
    filesUnmapped = 0

    for f in stepFiles:
        text = fileTextCache[f]
        hints = findMaterialHints(text)

        if not hints:
            filesWithoutHints += 1
            print("  [--] {} -- no material-name hint found".format(f))
            continue

        filesWithHints += 1

        if mapping is None:
            print("  [OK] {} -- hint(s): {}".format(f, hints))
            continue

        mapped = [h for h in hints if h.strip().lower() in mapping]
        unmapped = [h for h in hints if h.strip().lower() not in mapping]

        if mapped:
            print("  [OK] {} -- hint(s) {} ; mapped: {}".format(f, hints, mapped))
        if unmapped and not mapped:
            filesUnmapped += 1
            print("  [FAIL] {} -- hint(s) {} have NO entry in the mapping file".format(f, unmapped))
        elif unmapped:
            print("         (also unmapped: {})".format(unmapped))

    print("")
    print("Material hint scan: {} of {} file(s) had a material-name hint, {} had none."
          .format(filesWithHints, len(stepFiles), filesWithoutHints))
    if mapping is not None:
        print("{} file(s) had a hint with no entry in the supplied mapping file.".format(filesUnmapped))
        print("This is a left-shifted, cheaper version of what 1_HLP_MAT_PREFLIGHT_AA01.py and")
        print("1_HLP_MAT_LOOKUP_AA01.py already check mid-pipeline (both require an actual KeyShot")
        print("import) -- it complements, not duplicates, those checks.")
    else:
        print("No mapping file supplied -- skipped the mapping cross-reference. Pass a")
        print("1_HLP_MAT_LOOKUP_AA01.py-format mapping file (.csv or .json) as the second argument")
        print("to cross-check hints against known creo_material -> keyshot_template entries.")
    print("Remember: this is a regex text scan, not a real entity-reference resolver -- it can")
    print("miss materials that are one hop away from the PROPERTY_DEFINITION entity it matches.")


# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("Folder of *.step/*.stp files to preflight: ").strip()

    if not os.path.isdir(folder):
        print("Not a folder: {}".format(folder))
        sys.exit(1)

    if len(sys.argv) > 2:
        mappingPath = sys.argv[2].strip()
    else:
        mappingPath = input(
            "Optional material mapping file (.csv or .json, same format as "
            "1_HLP_MAT_LOOKUP_AA01.py) -- press enter to skip: "
        ).strip()

    mapping = None
    if mappingPath:
        if not os.path.isfile(mappingPath):
            print("Mapping file not found: {} -- continuing without material cross-reference.".format(mappingPath))
        else:
            try:
                mapping = loadMapping(mappingPath)
                print("Loaded {} mapping entr{} from {}".format(
                    len(mapping), "y" if len(mapping) == 1 else "ies", mappingPath))
            except Exception as e:
                print("Couldn't load mapping file ({}) -- continuing without material cross-reference.".format(e))
                mapping = None

    stepFiles = collectStepFiles(folder)
    if not stepFiles:
        print("No *.step/*.stp files found in {}".format(folder))
        sys.exit(1)

    fileTextCache = {}
    for f in stepFiles:
        try:
            fileTextCache[f] = readStepText(folder, f)
        except Exception as e:
            print("[warn] couldn't read {}: {} -- treating as empty for text scans.".format(f, e))
            fileTextCache[f] = ""

    print("Found {} STEP file(s) in {}".format(len(stepFiles), folder))
    print("")

    runUnitCheck(folder, stepFiles, fileTextCache)
    runFilenameHygieneCheck(folder, stepFiles)
    runDuplicateCheck(folder, stepFiles)
    runMaterialHintCheck(folder, stepFiles, fileTextCache, mapping)


if __name__ == "__main__":
    main()
