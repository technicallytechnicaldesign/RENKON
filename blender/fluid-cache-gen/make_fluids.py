   
                                                                               

                                                                  
                                                          
                                                

                                                                                
                                                                                 
                                                                              
                                                                                 
                                                                                 

                                                                             
                                                                                
                                                                                 
                                                                                  
                                                                 

                                                                                  
                                                                             
                                                                             
                                                                               
                                                                               
                                                          

                                                                  
                                                                              
                                                                                
                                                                              
                                                                               
                                                                            
                                                      
                                                                               
                                                                                 
                                                                              
                           
                                                                              
                                                                                
                   
                                                                             
                             
                                                                                 
                                                                               
                                                                           
                                  
   
import bpy, sys, os

OUT  = os.path.join(os.getcwd(), "fluid_out")                          
RES  = {"preview": 64, "final": 200}                                               

                                                                               
                                                        
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

                                                                                
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def add_grid(size_m, loc, subdiv):
                                                                                
                                                                          
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdiv, y_subdivisions=subdiv,
                                    size=size_m, location=loc)
    g = bpy.context.view_layer.objects.active
    g.name = "Surface"
    return g

def _try(obj, attr, value):
                                                                               
                                                                           
                                                             
    try:
        setattr(obj, attr, value)
    except Exception as e:
        print("  [info] '{0}' not settable ({1})".format(attr, e))

                                                                                   
def build_ocean(g, lk, f0, f1):
                                                                                
                                                                            
    m = g.modifiers.new("Ocean", 'OCEAN')
    m.geometry_mode = 'DISPLACE'                                                                
    m.spatial_size = lk["spatial_size"]                                                                   
    m.wave_scale = lk["wave_scale"]
    m.choppiness = lk["choppiness"]
    m.wind_velocity = lk["wind_velocity"]
    _try(m, "wave_scale_min", lk["wave_scale_min"])                       
                                                                               
                                                                                 
                                                                             
    m.time = lk["t0"]; m.keyframe_insert(data_path="time", frame=f0)
    m.time = lk["t1"]; m.keyframe_insert(data_path="time", frame=f1)

def build_wave(g, center, lk, start_frame):
                                                                               
                                                                            
                                                                                
                                                                 
    m = g.modifiers.new("Wave", 'WAVE')
    m.use_x = True
    m.use_y = True
    m.use_cyclic = False
    m.height = lk["height"]
    m.width = lk["width"]
    m.narrowness = lk["narrowness"]
    m.speed = lk["speed"]
    m.start_position_x = center[0]                                                          
    m.start_position_y = center[1]
    m.time_offset = float(start_frame)                                          
    m.lifetime = 0                                                           
    _try(m, "damping_time", lk["damping_time"])                           
    _try(m, "falloff_radius", lk["falloff_radius"])                       
    return m

def build_flow(g, lk, f0, f1):
                                                                                  
                                                                                 
                                                                                 
    tex = bpy.data.textures.new("flow_noise", type='CLOUDS')                                           
    _try(tex, "noise_scale", lk["noise_scale"])
    _try(tex, "noise_depth", lk["noise_depth"])
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    drv = bpy.context.view_layer.objects.active
    drv.name = "FlowDriver"
    dx, dy, dz = lk["drift"]
    drv.location = (0.0, 0.0, 0.0); drv.keyframe_insert(data_path="location", frame=f0)
    drv.location = (dx, dy, dz);    drv.keyframe_insert(data_path="location", frame=f1)
    m = g.modifiers.new("Displace", 'DISPLACE')
    m.texture = tex
    m.texture_coords = 'OBJECT'                                                                      
    m.texture_coords_object = drv
    m.strength = lk["strength"]
    m.mid_level = lk["mid_level"]
    m.direction = 'Z'                                                                  
                                                                                 
                                                                           
    bpy.context.view_layer.objects.active = g

def build_splash(g, lk):
                                                                                  
                                                                                   
                                                                     
    c0, c1 = lk["centers"]
    s0, s1 = lk["start_frames"]
    build_wave(g, c0, lk, s0)
    build_wave(g, c1, lk, s1)

                                                                                                            
def export(domain, path, f0, f1):
    for o in bpy.context.scene.objects: o.select_set(False)
    domain.select_set(True); bpy.context.view_layer.objects.active = domain
    kw = dict(filepath=path, start=f0, end=f1, selected=True,
              triangulate=True, quad_method='FIXED', ngon_method='BEAUTY',
              as_background_job=False)                                                         
    try: bpy.ops.wm.alembic_export(**kw)                                                           
    except TypeError:                                                                             
        kw.pop("as_background_job", None)
        try: bpy.ops.wm.alembic_export(**kw)
        except TypeError:                                                               
            bpy.ops.wm.alembic_export(filepath=path, start=f0, end=f1, selected=True)

                                                                                 
def build(name, tier):
    p = PRESETS[name]; f0, f1 = p["frames"]; lk = p["look"]; kind = p["kind"]
    reset()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = f0, f1
    sc.gravity = (0, 0, -9.81)                                                             
    g = add_grid(p["size"], p["loc"], RES[tier])
    if   kind == "ocean":  build_ocean(g, lk, f0, f1)
    elif kind == "ripple": build_wave(g, lk["center"], lk, lk.get("start_frame", f0))
    elif kind == "flow":   build_flow(g, lk, f0, f1)
    elif kind == "splash": build_splash(g, lk)
    else: raise ValueError("unknown kind: {0}".format(kind))
    print("[{0}/{1}] exporting frames {2}-{3} @ grid {4} ...".format(name, tier, f0, f1, RES[tier]))
    out = os.path.join(OUT, "{0}.abc".format(name))
    export(g, out, f0, f1); print("  wrote", out)

                                                                       
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
