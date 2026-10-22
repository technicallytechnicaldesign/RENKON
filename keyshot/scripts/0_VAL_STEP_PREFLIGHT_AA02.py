                       
                                   
          
                                                                           
                                                                             
                                
 
                                                                       
                                                                            
                                                                        
                                                                             
 
                                                                
                                                                          
                                                                      
                                                                      
                                                                     
                                                                                  
                                                                                  
                                                                           
                                                                            
                                                                         
 
                                                                          
                                                                             
                                                                         
                                                                            
                                                                         
                                                                           
                                                                      
                                                                              
                                                                
                                                                              
                                                                             
                                                       
 
        
                                                                                       
                                                                      

import os
import re
import sys
import csv
import json

                                                                             
                                                                          
                                                                        
                                                                             

                                                                          
                                                                       
                                                                       
                            
EXPECTED_UNIT = "MM"

STEP_EXTENSIONS = (".step", ".stp")

                                                                           
                                                                          
                                                                    
SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


                                                                             
                                   
                                                                             

                                                         
                            
                                                                   
                                                                          
                                                                    
SI_UNIT_RE = re.compile(
    r"SI_UNIT\s*\(\s*(\$|\.[A-Z]*\.)\s*,\s*\.([A-Z]+)\.\s*\)",
    re.IGNORECASE,
)

                                                                          
                                                                        
                                                                         
                                                                         
                                                                         
                                                                         
CONVERSION_BASED_UNIT_RE = re.compile(r"CONVERSION_BASED_UNIT", re.IGNORECASE)
INCH_FACTOR_RE = re.compile(r"\b25\.4\b")
                                                                         
                                                                        
                                                                          
                                                             
CONVERSION_SEARCH_WINDOW = 400

PREFIX_MULTIPLIERS = {
    "": "M",                                                         
    "MILLI": "MM",
    "CENTI": "CM",
    "KILO": "KM",
}


def normalizeSiUnit(prefixToken, baseToken):
                                                                           
                                                                          
                                                                      
                         
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
                                                                        
                                                                  
                                                                 

                                                                          
                                                                        
                                                                           
                                                                         
                                                                          
                                                                          
                                                                     
                                                                          
                      
    for m in CONVERSION_BASED_UNIT_RE.finditer(text):
        windowStart = max(0, m.start() - CONVERSION_SEARCH_WINDOW)
        windowEnd = min(len(text), m.end() + CONVERSION_SEARCH_WINDOW)
        window = text[windowStart:windowEnd]
        if INCH_FACTOR_RE.search(window):
            return "INCH (conversion-based)", "CONVERSION_BASED_UNIT+25.4"

                                                                         
                                                                         
                                                                       
                                                   
    for m in SI_UNIT_RE.finditer(text):
        unit = normalizeSiUnit(m.group(1), m.group(2))
        if unit:
            return unit, "SI_UNIT"

    return None, None


                                                                             
                           
                                                                             

def findUnsafeChars(stem):
                                                                         
                                                               
    bad = set()
    for ch in stem:
        if not re.match(r"[A-Za-z0-9_\-]", ch):
            bad.add(ch)
    return sorted(bad)


                                                                             
                                                    
                                                                             

                                                                          
                                                                         
                                                                           
                                                                           
                                                                            
                                                                     
                                                                       
                
PROPERTY_DEFINITION_RE = re.compile(
    r"PROPERTY_DEFINITION\s*\([^)]*\)", re.IGNORECASE
)
QUOTED_STRING_RE = re.compile(r"'([^']*)'")


def findMaterialHints(text):
                                                                          
                                                                        
                                                                        
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
                                                                           
                                                                       
                                                                          
    path = os.path.join(folder, filename)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


                                                                             
                 
                                                                             

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
        print("Downstream output naming is \"{baseName}_{view}.{ext}\" (2a_BAT_STD_VIEW_AA02.py /")
        print("2a_BAT_TURNTABLE_AA02.py) -- spaces, non-ASCII characters, or path separators in a")
        print("source filename will produce a broken or surprising output path.")


def runDuplicateCheck(folder, stepFiles):
    print("")
    print("=" * 70)
    print("CHECK 3 -- duplicate base names (case-insensitive)")
    print("=" * 70)

    groups = {}                                           
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
        print("This is a left-shifted, cheaper version of what 1_HLP_MAT_PREFLIGHT_AA02.py and")
        print("1_HLP_MAT_LOOKUP_AA02.py already check mid-pipeline (both require an actual KeyShot")
        print("import) -- it complements, not duplicates, those checks.")
    else:
        print("No mapping file supplied -- skipped the mapping cross-reference. Pass a")
        print("1_HLP_MAT_LOOKUP_AA02.py-format mapping file (.csv or .json) as the second argument")
        print("to cross-check hints against known creo_material -> keyshot_template entries.")
    print("Remember: this is a regex text scan, not a real entity-reference resolver -- it can")
    print("miss materials that are one hop away from the PROPERTY_DEFINITION entity it matches.")


                                                                             

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
            "1_HLP_MAT_LOOKUP_AA02.py) -- press enter to skip: "
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
