   
                                                                                         

                                                               
                                               
                                             

                                
                                                      
                                              
                                                
                                               

                                                                                             
                                                                           

                      
                                                                                             
                                                                                          
                         
                                                                                       
                                                                                            
                                                                                       
                                                                                            
   
import bpy, sys, os, math

OUT  = os.path.join(os.getcwd(), "fluid_out")                                   
RES  = {"preview": 48, "final": 160}                                        

                                                                                      
PRESETS = {
    "jet":    dict(dom=(3.0,1.4,1.4), dloc=(0.3,0,0.1),
                   inflow=((-1.0,0,0.35), 0.12, (7.0,0,-0.6)),
                   collider="ground", gz=-0.6, frames=(1,80),  visc=0.0, tension=0.0),
    "pipe":   dict(dom=(3.0,1.0,1.0), dloc=(0,0,0),
                   inflow=((-1.0,0,0.06), 0.11, (3.0,0,0)),
                   collider="pipe",   gz=0.0,  frames=(1,90),  visc=0.0, tension=0.0),
    "drip":   dict(dom=(0.9,0.9,2.2), dloc=(0,0,0.2),
                   inflow=((0,0,0.85), 0.08, (0,0,-0.05)),
                   collider="ground", gz=-0.9, frames=(1,110), visc=0.0, tension=0.9),
    "splash": dict(dom=(1.7,1.7,1.7), dloc=(0,0,0.2),
                   inflow=((0,0,0.7), 0.12, (0,0,-4.0)),
                   collider="plate",  gz=0.0,  frames=(1,70),  visc=0.0, tension=0.05),
}

                                                                                
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def add_domain(size, loc, res):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    d = bpy.context.view_layer.objects.active; d.name = "Domain"; d.scale = size
    m = d.modifiers.new("Fluid", 'FLUID'); m.fluid_type = 'DOMAIN'
    ds = m.domain_settings; ds.domain_type = 'LIQUID'
    ds.resolution_max = res; ds.use_mesh = True; ds.cache_type = 'ALL'
    return d, ds

def set_look(ds, visc, tension):
    try: ds.surface_tension = tension
    except Exception: pass
    if visc:
        try: ds.use_viscosity, ds.viscosity_value = True, visc              
        except Exception: pass

def add_inflow(loc, radius, vel):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, location=loc, subdivisions=3)
    o = bpy.context.view_layer.objects.active; o.name = "Inflow"; o.hide_render = True
    m = o.modifiers.new("Fluid", 'FLUID'); m.fluid_type = 'FLOW'
    fs = m.flow_settings; fs.flow_type = 'LIQUID'; fs.flow_behavior = 'INFLOW'
    fs.use_initial_velocity = True; fs.velocity_coord = vel

def effector(obj):
    m = obj.modifiers.new("Fluid", 'FLUID'); m.fluid_type = 'EFFECTOR'
    m.effector_settings.effector_type = 'COLLISION'; obj.hide_render = True

def add_collider(kind, gz):
    if kind == "ground" or kind == "plate":
        bpy.ops.mesh.primitive_plane_add(size=6 if kind == "ground" else 2.2,
                                         location=(0, 0, gz))
    elif kind == "pipe":                                                                  
        bpy.ops.mesh.primitive_cylinder_add(radius=0.26, depth=2.6, vertices=48,
                                            end_fill_type='NOTHING',
                                            rotation=(0, math.radians(90), 0))
    effector(bpy.context.view_layer.objects.active)

                                                                                
def bake(domain):
    with bpy.context.temp_override(active_object=domain, object=domain,
                                   selected_objects=[domain]):
        bpy.ops.fluid.bake_all()

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
    p = PRESETS[name]; f0, f1 = p["frames"]
    reset()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = f0, f1
    sc.gravity = (0, 0, -9.81)
    d, ds = add_domain(p["dom"], p["dloc"], RES[tier])
    ds.cache_directory = os.path.join(OUT, f"cache_{name}")
    ds.cache_frame_start, ds.cache_frame_end = f0, f1
    set_look(ds, p["visc"], p["tension"])
    loc, r, v = p["inflow"]; add_inflow(loc, r, v)
    add_collider(p["collider"], p["gz"])
    print(f"[{name}/{tier}] baking frames {f0}-{f1} @ res {RES[tier]} ...")
    bake(d)
    out = os.path.join(OUT, f"{name}.abc")
    export(d, out, f0, f1); print("  wrote", out)

                                                                       
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
which = argv[0] if argv else "all"
tier  = argv[1] if len(argv) > 1 else "preview"
targets = list(PRESETS) if which == "all" else [which]
for name in targets:
    try:
        build(name, tier)
    except Exception as e:
        import traceback; print(f"[SKIP {name}] {e}"); traceback.print_exc()
print("done ->", OUT)
