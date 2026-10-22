                       
            
          
                    
   
                                          

                                                                           
                                                             
                                                                            
                                                                          
                                                                        
                                                                        
                                                                         
                                                                        

                                                                       
                                                                        
                                                                           
                                                      
                                                                         
                                                                            
                                                                           
                                                                

                                                                     
                                                                        
                                                                   
                                                                 
                                                

                                                                       
                                                                      
                                                                     
                                                             
   

import os, re, sys
import os.path
import csv
import statistics
from datetime import datetime

                                                                        
                                                                           
                                                                           
                                                                           
                                                                           
                                                                 
                                            
OUTLIER_STD_DEV_THRESHOLD = 2.0

                                                                       
                                                                          
                                                                      
                                    
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
            sys.stdout.write("\n")                                                      
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
                                                                           
    lower = filename.lower()
    dotExt = "." + ext
    if lower.endswith(dotExt):
        return filename[:-len(dotExt)]
    if lower.endswith(ext):
        return filename[:-len(ext)]
    return filename


                                                                            
                                                       
                                                                            

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


                                                                            
                                                                      
                                                                           
                                                          
                                                                            

def _parse_bbox_result(result):
                                                                       
                                                                    
                                                                         
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


                                                                            
                                                                           
                                                                            
                                                                            

def compute_footprint_ratio(lo_xyz, hi_xyz):
                                                                           
                                                                          
                                                                          
                                                                       
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

                                                                           
                                                                      
                                                                      
                                                               
                                                                           
    measurements = []                                                               
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
        stdev_ratio = statistics.stdev(ratios)                                                       

        print("")
        print("Batch footprint ratio: mean={:.4f} stdev={:.4f} (n={})"
              .format(mean_ratio, stdev_ratio, len(ratios)))

        for m in measurements:
            if stdev_ratio > 0:
                deviation = abs(m["ratio"] - mean_ratio) / stdev_ratio
            else:
                                                                           
                                               
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
