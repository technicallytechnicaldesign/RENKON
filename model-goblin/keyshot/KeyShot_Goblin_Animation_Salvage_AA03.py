"""Model Goblin AA03 - working KeyShot rigid-animation salvage bridge.

The bridge samples evaluated local bounding boxes to recover translation curves,
records camera motion, detects turntables, and exports a frame-zero GLB.
Run inside KeyShot 2024.x via Window > Scripting.
"""

import json
import math
import os
import time
import traceback

import lux


FPS = 30
OUTPUT_BASENAME = "keyshotbridge"
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "KeyShot_Goblin_Animation_Salvage_AA03")
EXPORT_GLB = True
CAPTURE_CAMERA = True
SETTLE_SECONDS = 0.01
CHANGE_EPSILON = 1.0e-7


LOG_LINES = []


def log(message):
    line = "[Goblin Salvage AA03] " + str(message)
    print(line)
    LOG_LINES.append(line)


def safe_call(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def clean(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    val = safe_call(lambda: value.val(), None)
    if val is not None:
        return clean(val)
    return str(value)


def vec(value):
    data = clean(value)
    if isinstance(data, list) and len(data) >= 3:
        return [float(data[0]), float(data[1]), float(data[2])]
    return None


def bbox(node, world=False):
    data = clean(safe_call(lambda: node.getBoundingBox(world=world), None))
    if not isinstance(data, list) or len(data) < 2:
        return None
    lo, hi = vec(data[0]), vec(data[1])
    if lo is None or hi is None:
        return None
    return {
        "min": lo,
        "max": hi,
        "center": [(lo[i] + hi[i]) * 0.5 for i in range(3)],
        "size": [hi[i] - lo[i] for i in range(3)],
    }


def matrix(node, world=False):
    data = clean(safe_call(lambda: node.getTransform(world=world), None))
    if not isinstance(data, list):
        return None
    flat = []
    for item in data:
        flat.extend(item if isinstance(item, list) else [item])
    return [float(v) for v in flat[:16]] if len(flat) >= 16 else None


def node_path(node):
    path = safe_call(lambda: node.getPath(text=True), None)
    if path:
        return "/".join(str(x) for x in path)
    names = []
    current = node
    while current is not None:
        names.append(str(safe_call(lambda n=current: n.getName(), "<unnamed>")))
        current = safe_call(lambda n=current: n.getParent(), None)
    return "/".join(reversed(names))


def walk(node):
    yield node
    for child in safe_call(lambda: node.getChildren(), []) or []:
        for nested in walk(child):
            yield nested


def differs(values):
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return False
    first = values[0]
    for value in values[1:]:
        if isinstance(first, list) and isinstance(value, list):
            if len(first) != len(value) or any(abs(float(a) - float(b)) > CHANGE_EPSILON for a, b in zip(first, value)):
                return True
        elif value != first:
            return True
    return False


def camera_sample(t):
    return {
        "time": t,
        "position": vec(safe_call(lux.getCameraPosition)),
        "target": vec(safe_call(lux.getCameraLookAt)),
        "up": vec(safe_call(lux.getCameraUp)),
        "fov": safe_call(lux.getCameraFieldOfView),
        "lens": clean(safe_call(lux.getCameraLens)),
    }


def animation_kind(name):
    text = str(name or "").lower()
    if "turntable" in text:
        return "turntable"
    if "translation" in text or "translate" in text:
        return "translation"
    if "rotation" in text or "rotate" in text:
        return "rotation"
    if "fade" in text or "visibility" in text:
        return "visibility"
    return "unknown"


def export_glb(path):
    options = {
        "mode": lux.EXPORT_BAKING,
        "max_resolution": 2048,
        "num_samples": 8,
        "occlusion": True,
        "draco_compression": False,
        "preferred_output": lux.EXPORT_OUTPUT_TEXTURES,
        "include_cameras": True,
    }
    try:
        return lux.exportFile(path, lux.EXPORT_GLTF, mode=options)
    except Exception:
        options.pop("include_cameras", None)
        try:
            return lux.exportFile(path, lux.EXPORT_GLTF, mode=options)
        except Exception:
            return lux.exportFile(path, lux.EXPORT_GLTF)


os.makedirs(OUTPUT_DIR, exist_ok=True)
json_path = os.path.join(OUTPUT_DIR, OUTPUT_BASENAME + ".goblinsalvage.json")
glb_path = os.path.join(OUTPUT_DIR, OUTPUT_BASENAME + ".glb")
log_path = os.path.join(OUTPUT_DIR, OUTPUT_BASENAME + ".AA03_log.txt")
original_time = safe_call(lux.getAnimationTime, 0.0)
was_paused = bool(safe_call(lux.isPaused, False))

try:
    log("Starting AA03 salvage bridge.")
    log("KeyShot version: %s" % clean(safe_call(lux.getKeyShotVersion)))
    info = clean(safe_call(lux.getAnimationInfo, {})) or {}
    duration = float(info.get("duration", 0.0) if isinstance(info, dict) else 0.0)
    reported_frames = int(info.get("frames", round(duration * FPS)) if isinstance(info, dict) else round(duration * FPS))
    effective_fps = float(reported_frames) / duration if duration > 0 and reported_frames > 0 else float(FPS)
    sample_count = max(1, reported_frames) + 1 if reported_frames > 0 else max(1, int(round(duration * FPS))) + 1
    log("Animation info: %s" % info)
    log("Duration: %.9f" % duration)
    log("Reported frames: %d" % reported_frames)
    log("Original time: %.9f" % float(original_time or 0.0))
    log("Renderer was paused: %s" % was_paused)
    if was_paused:
        lux.unpause()
        log("Renderer temporarily unpaused.")

    root = lux.getSceneTree()
    all_nodes = list(walk(root))
    animation_nodes = [n for n in all_nodes if bool(safe_call(lambda n=n: n.isAnimation(), False))]
    log("Animation nodes found: %d" % len(animation_nodes))
    targets = {}
    for anim in animation_nodes:
        parent = safe_call(lambda n=anim: n.getParent(), None)
        if parent is None:
            continue
        path = node_path(parent)
        kind = animation_kind(safe_call(lambda n=anim: n.getName(), ""))
        entry = targets.setdefault(path, {"node": parent, "animations": []})
        entry["animations"].append({
            "name": safe_call(lambda n=anim: n.getName(), ""),
            "path": node_path(anim),
            "kind": kind,
            "dump": safe_call(lambda n=anim: n.dump(), str(anim)),
        })
        log("Animation: %s -> %s (%s)" % (node_path(anim), path, kind))

    root_world_bounds = bbox(root, True)
    log("Sampling %d timeline positions at %.6g fps." % (sample_count, effective_fps))
    camera_samples = []
    raw_samples = {path: [] for path in targets}
    for frame in range(sample_count):
        t = min(duration, frame / effective_fps) if duration > 0 else 0.0
        lux.setAnimationTime(t)
        safe_call(lux.sync)
        time.sleep(SETTLE_SECONDS)
        if CAPTURE_CAMERA:
            camera_samples.append(camera_sample(t))
        for path, target in targets.items():
            node = target["node"]
            local_box = bbox(node, False)
            world_box = bbox(node, True)
            raw_samples[path].append({
                "time": t,
                "localCenter": local_box["center"] if local_box else None,
                "localSize": local_box["size"] if local_box else None,
                "worldCenter": world_box["center"] if world_box else None,
                "worldSize": world_box["size"] if world_box else None,
                "localMatrix": matrix(node, False),
                "worldMatrix": matrix(node, True),
                "hidden": bool(safe_call(lambda n=node: n.isHidden(), False)),
            })
        if frame % max(1, sample_count // 10) == 0:
            log("Sample %d/%d" % (frame + 1, sample_count))

    tracks = []
    for path, target in targets.items():
        samples = raw_samples[path]
        changes = {
            "local_center": differs([s["localCenter"] for s in samples]),
            "local_size": differs([s["localSize"] for s in samples]),
            "world_center": differs([s["worldCenter"] for s in samples]),
            "world_size": differs([s["worldSize"] for s in samples]),
            "hidden": differs([s["hidden"] for s in samples]),
            "local_matrix": differs([s["localMatrix"] for s in samples]),
            "world_matrix": differs([s["worldMatrix"] for s in samples]),
        }
        kinds = [a["kind"] for a in target["animations"]]
        log("Target changes: %s" % changes)
        track = {
            "target": {
                "name": safe_call(lambda n=target["node"]: n.getName(), ""),
                "path": path,
                "id": clean(safe_call(lambda n=target["node"]: n.getID())),
            },
            "animations": target["animations"],
            "changes": changes,
            "translation": {
                "enabled": changes["local_center"] or changes["world_center"],
                "method": "local-bbox-center-delta" if changes["local_center"] else "world-bbox-center-delta",
                "samples": [{"time": s["time"], "value": s["localCenter"] if changes["local_center"] else s["worldCenter"]} for s in samples],
            },
            "visibility": {
                "enabled": changes["hidden"],
                "samples": [{"time": s["time"], "hidden": s["hidden"]} for s in samples],
            },
            "turntable": {
                "enabled": "turntable" in kinds,
                "axis": "y",
                "degrees": 360.0,
                "direction": 1,
                "sourceNames": [a["name"] for a in target["animations"] if a["kind"] == "turntable"],
            },
            "forensics": {"samples": samples},
        }
        if track["translation"]["enabled"] or track["visibility"]["enabled"] or track["turntable"]["enabled"]:
            tracks.append(track)

    payload = {
        "schema": "model-goblin-salvage-aa03",
        "version": 3,
        "source": {
            "keyshotVersion": clean(safe_call(lux.getKeyShotVersion)),
            "sceneInfo": clean(safe_call(lux.getSceneInfo, {})),
            "animationInfo": info,
            "sceneBounds": root_world_bounds,
        },
        "fps": effective_fps,
        "duration": duration,
        "frameCount": reported_frames,
        "tracks": tracks,
        "camera": {"enabled": CAPTURE_CAMERA and bool(camera_samples), "samples": camera_samples},
        "defaults": {"turntableDirection": 1, "turntableDegrees": 360.0, "translationGain": 1.0},
    }
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    log("Salvage JSON written: " + json_path)
    log("Tracks written: %d" % len(tracks))
    log("BBox-motion tracks: %d" % sum(1 for t in tracks if t["translation"]["enabled"]))
    log("Procedural turntables: %d" % sum(1 for t in tracks if t["turntable"]["enabled"]))

    if EXPORT_GLB:
        lux.setAnimationTime(0.0)
        safe_call(lux.sync)
        log("Exporting static GLB at time zero: " + glb_path)
        result = export_glb(glb_path)
        log("GLB export returned: %s" % result)
    log("AA03 salvage complete.")
except Exception:
    log("FAILED\n" + traceback.format_exc())
finally:
    safe_call(lambda: lux.setAnimationTime(original_time))
    safe_call(lux.sync)
    if was_paused:
        safe_call(lux.pause)
    log("Restored original animation time: %s" % original_time)
    if was_paused:
        log("Restored paused renderer state.")
    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(LOG_LINES))
