"""Model Goblin AA03 - versioned KeyShot rigid-animation salvage bridge.

The bridge registers geometry-bearing bodies beneath each animated scene target,
samples evaluated bounding boxes to recover translation and group rotation,
records camera motion, and exports an identity-labelled frame-zero GLB.
Run inside KeyShot 2024.x via Window > Scripting.
"""

import json
import math
import os
import time
import traceback

import lux


FPS = 30
BRIDGE_VERSION = "0.6.5"
BUILD_ID = "2026-08-29.1"
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


def geometry_leaves(node):
    """Return geometry-bearing leaves below a scene target, excluding animations."""
    child_leaves = []
    for child in safe_call(lambda: node.getChildren(), []) or []:
        if bool(safe_call(lambda n=child: n.isAnimation(), False)):
            continue
        child_leaves.extend(geometry_leaves(child))
    if child_leaves:
        return child_leaves
    if bbox(node, False) is not None or bbox(node, True) is not None:
        return [node]
    return []


def register_geometry_target(targets, targets_by_id, leaf):
    """Register one scene body without collapsing duplicate readable paths."""
    leaf_path = node_path(leaf)
    leaf_id = clean(safe_call(lambda n=leaf: n.getID(), None))
    id_key = str(leaf_id) if leaf_id is not None else None
    target = targets_by_id.get(id_key) if id_key is not None else None
    if target is None and id_key is None:
        for candidate in targets:
            if candidate["node"] is leaf:
                target = candidate
                break
    if target is None:
        target = {
            "node": leaf,
            "nodeId": leaf_id,
            "path": leaf_path,
            "sampleKey": "target-%d" % len(targets),
            "animations": [],
            "sourcePaths": [],
        }
        targets.append(target)
        if id_key is not None:
            targets_by_id[id_key] = target
    return target


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


def rigid_quaternion(reference_points, current_points):
    """Fit a relative rigid rotation with Horn's quaternion method."""
    pairs = [(a, b) for a, b in zip(reference_points, current_points) if a is not None and b is not None]
    if len(pairs) < 2:
        return None
    ref_center = [sum(pair[0][axis] for pair in pairs) / len(pairs) for axis in range(3)]
    cur_center = [sum(pair[1][axis] for pair in pairs) / len(pairs) for axis in range(3)]
    ref = [[point[axis] - ref_center[axis] for axis in range(3)] for point, _ in pairs]
    cur = [[point[axis] - cur_center[axis] for axis in range(3)] for _, point in pairs]
    spread = sum(sum(value * value for value in point) for point in ref)
    if spread <= CHANGE_EPSILON:
        return None
    s = [[sum(a[row] * b[col] for a, b in zip(ref, cur)) for col in range(3)] for row in range(3)]
    sxx, sxy, sxz = s[0]
    syx, syy, syz = s[1]
    szx, szy, szz = s[2]
    trace = sxx + syy + szz
    horn = [
        [trace, syz - szy, szx - sxz, sxy - syx],
        [syz - szy, sxx - syy - szz, sxy + syx, szx + sxz],
        [szx - sxz, sxy + syx, -sxx + syy - szz, syz + szy],
        [sxy - syx, szx + sxz, syz + szy, -sxx - syy + szz],
    ]
    shift = sum(abs(value) for row in horn for value in row) + 1.0
    shifted = [[horn[row][col] + (shift if row == col else 0.0) for col in range(4)] for row in range(4)]
    quat = [1.0, 0.0, 0.0, 0.0]
    for _ in range(48):
        next_quat = [sum(shifted[row][col] * quat[col] for col in range(4)) for row in range(4)]
        length = math.sqrt(sum(value * value for value in next_quat))
        if length <= CHANGE_EPSILON:
            return None
        quat = [value / length for value in next_quat]
    if quat[0] < 0:
        quat = [-value for value in quat]
    return [quat[1], quat[2], quat[3], quat[0]]


def fitted_rotation_samples(members, raw_samples):
    """Recover one evaluated group rotation from descendant center motion."""
    if len(members) < 2:
        return []
    member_samples = [raw_samples[target["sampleKey"]] for target in members]
    if not member_samples or not member_samples[0]:
        return []
    field = "localCenter"
    if any(samples[0].get(field) is None for samples in member_samples):
        field = "worldCenter"
    reference = [samples[0].get(field) for samples in member_samples]
    output = []
    previous = None
    for frame_index in range(len(member_samples[0])):
        current = [samples[frame_index].get(field) for samples in member_samples]
        quat = rigid_quaternion(reference, current)
        if quat is None:
            return []
        if previous is not None and sum(a * b for a, b in zip(previous, quat)) < 0:
            quat = [-value for value in quat]
        previous = quat
        output.append({"time": member_samples[0][frame_index]["time"], "value": quat})
    return output


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
    log("Starting AA03 salvage bridge v%s [build %s]." % (BRIDGE_VERSION, BUILD_ID))
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
    animation_sources = {}
    for anim in animation_nodes:
        parent = safe_call(lambda n=anim: n.getParent(), None)
        if parent is None:
            continue
        path = node_path(parent)
        kind = animation_kind(safe_call(lambda n=anim: n.getName(), ""))
        animation_dump = clean(safe_call(lambda n=anim: n.dump(), str(anim)))
        entry = animation_sources.setdefault(path, {"node": parent, "animations": []})
        entry["animations"].append({
            "name": safe_call(lambda n=anim: n.getName(), ""),
            "path": node_path(anim),
            "kind": kind,
            "dump": animation_dump,
        })
        log("Animation: %s -> %s (%s)" % (node_path(anim), path, kind))
        log("Animation evidence: %s" % str(animation_dump)[:600])

    targets = []
    targets_by_id = {}
    for source_path, source in animation_sources.items():
        leaves = geometry_leaves(source["node"])
        if not leaves:
            log("No geometry bodies below animation target: %s" % source_path)
            continue
        log("Animation target %s registered %d geometry body/bodies." % (source_path, len(leaves)))
        for leaf in leaves:
            target = register_geometry_target(targets, targets_by_id, leaf)
            if source_path not in target["sourcePaths"]:
                target["sourcePaths"].append(source_path)
            known_animation_paths = set(a["path"] for a in target["animations"])
            for animation in source["animations"]:
                if animation["path"] not in known_animation_paths:
                    target["animations"].append(animation)
                    known_animation_paths.add(animation["path"])
    path_occurrences = {}
    for target_index, target in enumerate(targets):
        target["originalName"] = str(safe_call(lambda n=target["node"]: n.getName(), ""))
        target["exportName"] = "MG_AA03_%04d" % (target_index + 1)
        target["pathOccurrence"] = path_occurrences.get(target["path"], 0)
        path_occurrences[target["path"]] = target["pathOccurrence"] + 1
        log("Geometry body %d: %s [occurrence %d, id %s, export %s]" % (
            target_index + 1,
            target["path"],
            target["pathOccurrence"],
            target["nodeId"],
            target["exportName"],
        ))
    log("Geometry bodies registered for sampling: %d" % len(targets))

    root_world_bounds = bbox(root, True)
    log("Sampling %d timeline positions at %.6g fps." % (sample_count, effective_fps))
    camera_samples = []
    raw_samples = {target["sampleKey"]: [] for target in targets}
    for frame in range(sample_count):
        t = min(duration, frame / effective_fps) if duration > 0 else 0.0
        lux.setAnimationTime(t)
        safe_call(lux.sync)
        time.sleep(SETTLE_SECONDS)
        if CAPTURE_CAMERA:
            camera_samples.append(camera_sample(t))
        for target in targets:
            node = target["node"]
            local_box = bbox(node, False)
            world_box = bbox(node, True)
            raw_samples[target["sampleKey"]].append({
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

    rotation_by_source = {}
    for source_path, source in animation_sources.items():
        if not any(animation["kind"] == "rotation" for animation in source["animations"]):
            continue
        members = [target for target in targets if source_path in target["sourcePaths"]]
        clean_members = [target for target in members if len(target["sourcePaths"]) == 1]
        fit_members = clean_members if len(clean_members) >= 2 else members
        rotation_samples = fitted_rotation_samples(fit_members, raw_samples)
        changed = differs([sample["value"] for sample in rotation_samples])
        if rotation_samples and changed:
            rotation_by_source[source_path] = rotation_samples
            log("Rotation source %s fitted from %d body traces." % (source_path, len(fit_members)))
        else:
            log("Rotation source %s could not be fitted from %d body traces." % (source_path, len(fit_members)))

    tracks = []
    for target in targets:
        samples = raw_samples[target["sampleKey"]]
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
        rotation_source = next((path for path in target["sourcePaths"] if path in rotation_by_source), None)
        log("Target changes for %s: %s" % (target["exportName"], changes))
        track = {
            "target": {
                "name": target["originalName"],
                "exportName": target["exportName"],
                "path": target["path"],
                "pathOccurrence": target["pathOccurrence"],
                "id": target["nodeId"],
                "animationSourcePaths": target["sourcePaths"],
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
            "rotation": {
                "enabled": rotation_source is not None,
                "method": "descendant-center-rigid-fit" if rotation_source is not None else None,
                "sourcePath": rotation_source,
                "samples": rotation_by_source.get(rotation_source, []),
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
        if track["translation"]["enabled"] or track["rotation"]["enabled"] or track["visibility"]["enabled"] or track["turntable"]["enabled"]:
            tracks.append(track)

    payload = {
        "schema": "model-goblin-salvage-aa03",
        "version": 4,
        "bridgeVersion": BRIDGE_VERSION,
        "buildId": BUILD_ID,
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
    log("Tracks written: %d" % len(tracks))
    log("BBox-motion tracks: %d" % sum(1 for t in tracks if t["translation"]["enabled"]))
    log("Fitted rotation tracks: %d" % sum(1 for t in tracks if t["rotation"]["enabled"]))
    log("Procedural turntables: %d" % sum(1 for t in tracks if t["turntable"]["enabled"]))
    for track in tracks:
        log("TRACK %s: translation=%s rotation=%s visibility=%s animations=%s" % (
            track["target"]["exportName"],
            track["translation"]["enabled"],
            track["rotation"]["enabled"],
            track["visibility"]["enabled"],
            [animation["name"] for animation in track["animations"]],
        ))

    identity_labels_applied = 0
    if EXPORT_GLB:
        lux.setAnimationTime(0.0)
        safe_call(lux.sync)
        renamed_nodes = []
        try:
            for target in targets:
                changed_name = bool(safe_call(lambda n=target["node"], name=target["exportName"]: (n.setName(name), True)[1], False))
                verified_name = safe_call(lambda n=target["node"]: n.getName(), None) == target["exportName"]
                if changed_name:
                    renamed_nodes.append(target)
                if verified_name:
                    identity_labels_applied += 1
                else:
                    log("IDENTITY LABEL FAILED: %s -> %s" % (target["path"], target["exportName"]))
            log("Identity labels applied for GLB export: %d/%d" % (identity_labels_applied, len(targets)))
            log("Exporting static GLB at time zero: " + glb_path)
            result = export_glb(glb_path)
            log("GLB export returned: %s" % result)
        finally:
            for target in reversed(renamed_nodes):
                safe_call(lambda n=target["node"], name=target["originalName"]: n.setName(name))
            log("Restored %d temporary scene labels." % len(renamed_nodes))

    payload["identityLabelsApplied"] = identity_labels_applied
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    log("Salvage JSON written: " + json_path)
    log("AA03 v%s build %s salvage complete." % (BRIDGE_VERSION, BUILD_ID))
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
