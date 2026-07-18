"""
make_fluids.py -> procedural liquid-surface .abc caches for KeyShot, no solver.

RUN:  blender -b -P make_fluids.py -- <preset|all> <preview|final>
  e.g. blender -b -P make_fluids.py -- ocean_swell preview
       blender -b -P make_fluids.py -- all final

PRESETS (cheap animated surfaces -- displaced/animated mesh, NOT a fluid solve):
  ocean_swell      - broad rolling swell             (Ocean modifier, keyed time)
  droplet_ripple   - concentric ripples, one impact  (Wave modifier, circular)
  flow_turbulence  - restless flowing surface        (Displace + scrolling noise)
  splash_merge     - two expanding rings crossing     (two Wave modifiers summed)

Sibling of fluidgen.py (real Mantaflow FLIP sims). This one skips the solver:
every surface here is animated GEOMETRY, exported per-frame to .abc via the SAME
export path fluidgen.py uses (bake left live, evaluated by the Alembic exporter).
Cheap, fast, deterministic, loops cleanly -- reach for it when you want believable
liquid MOTION behind a product shot and don't need real dynamics.

Written for Blender 4.x. Untested outside a real Blender; structured to fail loud,
one preset at a time (any preset that trips an API mismatch is skipped with a
traceback, the rest still export). NEEDS A REAL BLENDER 4.x SMOKE-TEST before
production use -- several modifier/property names below are best-effort against
the 4.x API and flagged inline with "# CHECK". Always validate at 'preview' res
first (a fine 'final' grid makes large .abc point caches).

NOTES / honest limits (what "no solver" costs you vs fluidgen.py):
  * NO real dynamics. There is no momentum, no mass, no collision response, no
    pressure -- nothing here reacts to anything. A ripple doesn't know a wall is
    there; the swell doesn't break; the "splash" is two math ripples crossing,
    not liquid actually merging. It's a moving displacement field that READS as
    water, not a simulation of water. For genuine impact / pinch-off / crown
    splash dynamics, use fluidgen.py (Mantaflow FLIP).
  * SURFACE ONLY, always closed. These are height-field displacements of a flat
    sheet -> no droplets separating, no spray / foam / bubbles, no overturning or
    breaking waves, no thin sheets or ligaments. The mesh stays one continuous
    surface the whole time.
  * splash_merge in particular is a LOOK, not physics: two Wave fields summed.
    Real two-jet splash interaction (sheet collision, crown, secondary droplets)
    needs a solver.
  * Water look only. Cryogenic / other-liquid appearance lives in the KeyShot
    material, not this cache.
  * Mesh is triangulated on export (KeyShot 11/2023/2024 choke on n-gons). Object
    + .abc names kept ASCII. Modifiers are left LIVE and evaluated per frame by
    the Alembic exporter, so the animation bakes into point positions -- no
    manual per-frame apply needed.
"""
import bpy, sys, os

OUT  = os.path.join(os.getcwd(), "fluid_out")          # .abc land here
RES  = {"preview": 64, "final": 200}                   # grid subdivisions per side

# preset = kind + square plane size (m) + location + frame range + look params.
# 'look' keys are consumed by that kind's builder below.
PRESETS = {
    "ocean_swell": dict(
        kind="ocean", size=14.0, loc=(0, 0, 0), frames=(1, 120),
        look=dict(spatial_size=14, wave_scale=1.6, wave_scale_min=0.0,
                  choppiness=0.85, wind_velocity=24.0, t0=0.0, t1=8.0)),
    "droplet_ripple": dict(
        kind="ripple", size=6.0, loc=(0, 0, 0), frames=(1, 96),
        look=dict(center=(0.0, 0.0), height=0.14, width=0.35, narrowness=1.4,
                  speed=0.055, damping_time=120.0, falloff_radius=3.2,
                  start_frame=1)),
    "flow_turbulence": dict(
        kind="flow", size=9.0, loc=(0, 0, 0), frames=(1, 120),
        look=dict(strength=0.4, mid_level=0.5, noise_scale=0.9, noise_depth=2,
                  drift=(3.0, 0.8, 0.0))),
    "splash_merge": dict(
        kind="splash", size=8.0, loc=(0, 0, 0), frames=(1, 90),
        look=dict(centers=((-1.3, 0.3), (1.4, -0.4)), height=0.2, width=0.32,
                  narrowness=1.7, speed=0.075, damping_time=80.0,
                  falloff_radius=2.6, start_frames=(1, 16))),
}

# ---------------------------------------------------------------- scene helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def add_grid(size_m, loc, subdiv):
    # A flat subdivided plane centred on 'loc'. x/y_subdivisions = cuts per side
    # (more -> finer displacement). Square, so no object scale to bake in.
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdiv, y_subdivisions=subdiv,
                                    size=size_m, location=loc)
    g = bpy.context.active_object
    g.name = "Surface"
    return g

def _try(obj, attr, value):
    # Set an uncertain / optional property, skip-with-note if the name moved in
    # this build (mirrors fluidgen's set_look guarding). Core props are set
    # directly so a real mismatch fails loud at preset level.
    try:
        setattr(obj, attr, value)
    except Exception as e:
        print("  [info] '{0}' not settable ({1})".format(attr, e))

# ---------------------------------------------------------------- surface builders
def build_ocean(g, lk, f0, f1):
    # Ocean modifier in DISPLACE mode pushes the existing grid into a swell; the
    # look is animated by keyframing the modifier's 'time' across the range.
    m = g.modifiers.new("Ocean", 'OCEAN')
    m.geometry_mode = 'DISPLACE'                       # CHECK: 4.x enum {'GENERATE','DISPLACE'}
    m.spatial_size = lk["spatial_size"]                # CHECK: IntProperty in some builds (patch size, m)
    m.wave_scale = lk["wave_scale"]
    m.choppiness = lk["choppiness"]
    m.wind_velocity = lk["wind_velocity"]
    _try(m, "wave_scale_min", lk["wave_scale_min"])    # optional; guarded
    # keyframe 'time' on the modifier -> the object's animation gets the fcurve
    # 'modifiers["Ocean"].time'. The Alembic exporter re-evaluates the ocean each
    # frame from this value, baking the swell into per-frame point positions.
    m.time = lk["t0"]; m.keyframe_insert(data_path="time", frame=f0)
    m.time = lk["t1"]; m.keyframe_insert(data_path="time", frame=f1)

def build_wave(g, center, lk, start_frame):
    # One Wave modifier. use_x + use_y both on -> concentric (circular) ripples
    # radiating from (start_position_x, start_position_y). The Wave modifier
    # animates automatically off the scene frame (no keyframes needed): the ring
    # is born at 'time_offset' and propagates outward at 'speed'.
    m = g.modifiers.new("Wave", 'WAVE')
    m.use_x = True
    m.use_y = True
    m.use_cyclic = False
    m.height = lk["height"]
    m.width = lk["width"]
    m.narrowness = lk["narrowness"]
    m.speed = lk["speed"]
    m.start_position_x = center[0]                     # CHECK: 4.x names start_position_x/y
    m.start_position_y = center[1]
    m.time_offset = float(start_frame)                 # frame this ring is born
    m.lifetime = 0                                     # 0 -> persists to end
    _try(m, "damping_time", lk["damping_time"])        # optional; guarded
    _try(m, "falloff_radius", lk["falloff_radius"])    # optional; guarded
    return m

def build_flow(g, lk, f0, f1):
    # Displace modifier driven by a CLOUDS noise texture, whose mapping is tied to
    # an Empty. Keyframing the Empty's location scrolls the noise field under the
    # sheet -> a restless "flowing" surface with no repeating loop seam mid-shot.
    tex = bpy.data.textures.new("flow_noise", type='CLOUDS')   # CHECK: texture datablock type 'CLOUDS'
    _try(tex, "noise_scale", lk["noise_scale"])
    _try(tex, "noise_depth", lk["noise_depth"])
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    drv = bpy.context.active_object
    drv.name = "FlowDriver"
    dx, dy, dz = lk["drift"]
    drv.location = (0.0, 0.0, 0.0); drv.keyframe_insert(data_path="location", frame=f0)
    drv.location = (dx, dy, dz);    drv.keyframe_insert(data_path="location", frame=f1)
    m = g.modifiers.new("Displace", 'DISPLACE')
    m.texture = tex
    m.texture_coords = 'OBJECT'                        # CHECK: enum {'GLOBAL','LOCAL','OBJECT','UV'}
    m.texture_coords_object = drv
    m.strength = lk["strength"]
    m.mid_level = lk["mid_level"]
    m.direction = 'Z'                                  # CHECK: enum incl. 'Z','NORMAL'
    # the Empty is a separate object -> it is NOT selected at export, so it never
    # lands in the .abc; but make the Surface active again for bookkeeping.
    bpy.context.view_layer.objects.active = g

def build_splash(g, lk):
    # Two Wave modifiers with different centres + birth frames. Their height-field
    # displacements SUM, so two rings expand and visually cross/merge. Honest: this
    # is two math ripples overlapping, not liquid actually colliding.
    c0, c1 = lk["centers"]
    s0, s1 = lk["start_frames"]
    build_wave(g, c0, lk, s0)
    build_wave(g, c1, lk, s1)

# ---------------------------------------------------------------- export (reused verbatim from fluidgen.py)
def export(domain, path, f0, f1):
    for o in bpy.context.scene.objects: o.select_set(False)
    domain.select_set(True); bpy.context.view_layer.objects.active = domain
    kw = dict(filepath=path, start=f0, end=f1, selected=True,
              triangulate=True, quad_method='FIXED', ngon_method='BEAUTY')
    try: bpy.ops.wm.alembic_export(**kw)
    except TypeError:                                       # older builds: fewer args
        bpy.ops.wm.alembic_export(filepath=path, start=f0, end=f1, selected=True)

# ---------------------------------------------------------------- run one preset
def build(name, tier):
    p = PRESETS[name]; f0, f1 = p["frames"]; lk = p["look"]; kind = p["kind"]
    reset()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = f0, f1
    sc.gravity = (0, 0, -9.81)                             # harmless; parity with fluidgen
    g = add_grid(p["size"], p["loc"], RES[tier])
    if   kind == "ocean":  build_ocean(g, lk, f0, f1)
    elif kind == "ripple": build_wave(g, lk["center"], lk, lk.get("start_frame", f0))
    elif kind == "flow":   build_flow(g, lk, f0, f1)
    elif kind == "splash": build_splash(g, lk)
    else: raise ValueError("unknown kind: {0}".format(kind))
    print("[{0}/{1}] exporting frames {2}-{3} @ grid {4} ...".format(name, tier, f0, f1, RES[tier]))
    out = os.path.join(OUT, "{0}.abc".format(name))
    export(g, out, f0, f1); print("  wrote", out)

# ---------------------------------------------------------------- main
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
which = argv[0] if argv else "all"
tier  = argv[1] if len(argv) > 1 else "preview"
targets = list(PRESETS) if which == "all" else [which]
for name in targets:
    try:
        build(name, tier)
    except Exception as e:
        import traceback; print("[SKIP {0}] {1}".format(name, e)); traceback.print_exc()
print("done ->", OUT)
