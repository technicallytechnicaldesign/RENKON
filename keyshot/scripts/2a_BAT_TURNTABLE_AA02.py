                       
                                                                  
          
                    
                                                                           
                                                                       
                                                                           
                                                                          
                                                              
                                                                         
                                                                      
                                                                           
                                                                       
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

                                                                            
                                                                             
                                                                            

def verify_output(path, started_at):
                                                                                 
                                                                                    
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
                                                                               
                                                                                  
    cleaned = _SANITIZE_RE.sub("_", str(name)).strip("_")
    return cleaned if cleaned else "unnamed"


def load_job_json(folder):
                                                                                
                                                                               
                                                          
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

                                                     
FRAME_COUNT = 36                                                                  
FPS = 24
TURNTABLE_SAMPLES = 16                                                               
TURNTABLE_WIDTH = 640
TURNTABLE_HEIGHT = 640
PADDING_FACTOR = 1.15                                                         

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
                                                                             
                                                                              
                                                                            
        opts = dict(DEFAULT_OPTIONS)
        try:
            cwd = os.getcwd()
        except Exception:
            cwd = ""
        opts.update(load_job_json(cwd))
        jobFld = opts.get("folder", "") or ""
        if jobFld and (not cwd or os.path.abspath(jobFld) != os.path.abspath(cwd)):
            opts.update(load_job_json(jobFld))
                                                                             
                                                                               
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
                                                                          
                                                                         
                                                 

    for f in sorted([f for f in os.listdir(fld) if f.lower().endswith(iext)]):
        path = fld + os.path.sep + f
        lux.newScene()

        print("Importing {}".format(path))
                                                                              
                                                                      
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

                                                                         
                                                                     
                                                                             
                                                                            
                                                                         
                              
        studios = []
        try:
            studios = lux.getStudios()
        except Exception as e:
            print("  [warn] couldn't list studios: {}".format(e))

                                                                           
                                                         
        _gs = getattr(lux, "getStudio", None)

        studioName = None
        if baseCameraName in studios:
            studioName = baseCameraName
        elif studios and _gs is not None:
                                                                            
                                                                         
                                                                             
                                                                             
                                                                          
                                                                            
                                                                  
            for s in studios:
                try:
                    if _gs(s).getCamera() == baseCameraName:
                        studioName = s
                        break
                except Exception:
                    continue

        cam = None
        if studioName:
                                                                               
                                                                                 
                                                                               
            try:
                lux.setActiveStudio(studioName)
            except Exception as e:
                print("  [warn] couldn't activate studio '{}': {} -- falling back to raw camera.".format(studioName, e))
                studioName = None
            if studioName:
                                                                           
                                                               
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
