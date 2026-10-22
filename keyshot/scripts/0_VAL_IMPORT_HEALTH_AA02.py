                       
                                   
          
                    
                                                                            
                                                                       
                                                                      
                                                                     
            
 
                                                                          
                                      
                                                                        
                                                                         
                                                                          
                                                         
                                                                            
                                                                            
                                                                          
                                                                            
                                                                           
                                                                       
 
                                                                            
                                                                            
                                                                          
                                                                           
                                                                       
                                                                         
                                                     
 
                                                                           
                                                                        
                                                        
import os, re, sys
import os.path
import csv
from datetime import datetime

                                                                            
                   
                                                                            

                                                                            
                                                                     
                                                                            
                                                                       
                                                            
SUSPICIOUS_SIZE_THRESHOLD = 5000.0

                                                                           
                                                                         
                                                               
NEAR_ZERO_VOLUME_EPS = 1e-6

                                                                         
                                                                         
                                                                        
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
            sys.stdout.write("\n")                                                      
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
                                                               
                                                                            
                                      
    if results is None:
        results = []
    if node.isObject():
        results.append(node)
    for child in node.getChildren():
        collectObjectNodes(child, results)
    return results


                                                                            
                                                                           
                                                               
                                                                          
                                                                           
                                                        
                                                                            

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
