# Material Diversity — Design Exploration

**UID:** MDD-4B7A9F
**Rev:** 1
**Date:** 2026-07-15
**Audience:** whoever evolves `1_HLP_MAT_GENERATOR_AA02.py` next (TJ + agent).
**Status:** design exploration — nothing here is built. Grounded against (a) the
hard-won render-iteration ground truth from the AA02 cycle, (b) the KeyShot
11.0 + 2024.1 lux scripting references, (c) the KeyShot manual's material-graph
node pages. Companion to MWR-9C4E21 (`MASKED_WEAR_RESEARCH.md`), which it
partly supersedes on the "what's scriptable" question.

> **How to read confidence tags.** Same discipline as the rest of the pipeline:
> - **[CONFIRMED]** — in the lux reference by exact name, or proven in a real
>   render this cycle.
> - **[LIKELY]** — in the reference but parameter surface unprobed on the real
>   build; expect it to work, `dump_node()` it first.
> - **[PROBE]** — plausible, contradicts or extends past evidence, or
>   version-sensitive; needs a throwaway-material test before any design leans
>   on it. Section 8 collects every probe into one diagnostic script spec.

---

## 0. The headline discoveries (read this even if you skim the rest)

Researching the full lux reference (11.0 and 2024.1 — both list essentially
the same set) against what AA02 currently uses turned up four things that
change the game:

1. **The scriptable node census is ~90 SHADER_TYPE constants, not 16.**
   AA02 touches 16 of them. The reference confirms base materials we thought
   were out of reach (Anisotropic, Metallic Paint, Glass ×4, Translucent ×3,
   Gem, Velvet, Cloth, Emissive, Advanced, Generic, Thin Film *as a base*),
   procedural textures we've never instantiated (Wood, Wood Advanced, Marble,
   Granite, Leather, Weave, Carbon/Fiber Weave, Mesh, Camouflage, Contour,
   Brushed, Brushed Radial, Flakes, Bubbles), and utilities that solve real
   AA02 problems (Color Adjust, Color Invert, Color Key Mask, **Bump To
   Roughness**, Mapping 2D, Tri-Planar, Mapping Warp, Object Info, Curve Color
   Randomize, Displace, image Texture Map). Full census in §1. [CONFIRMED as
   constants; parameter surfaces LIKELY]

2. **Multi-material IS scriptable.** MWR-9C4E21 §0 says "no label/multi-
   material API" — that's half wrong. There is still no *label* API method,
   but `MaterialGraph.setMultiMaterial(enable)` and
   `setCurrentSubMaterial(node)` are in the 11.0 reference, and
   `getMaterialNodes()` returns "the individual sub-material roots" for a
   multi-material. That's not spatial masking (sub-materials are variants, not
   layers), but it means one generated graph can carry N colourway/finish
   variants natively. [CONFIRMED constants/methods; behaviour PROBE]

3. **The root node has a SHADERLABEL input (type 65538) — seen in our own
   dump.** `PARAMETER_TYPE_SHADERLABEL = 65538` exists, and the AA02 ground
   truth notes 65538 on the root. If `newEdge(source=<material node>,
   target=root, param=<the 65538 slot>)` is accepted, the classic
   **worn-edge-label** technique (a glossier/rustier sub-material whose
   *opacity* is driven by Curvature) comes back from the dead — entirely
   inside one scripted graph. This is the single highest-value probe in this
   document. [PROBE — evidence is suggestive, not proof]

4. **Roughness blending is a solved problem we haven't used.** Color
   Composite carries full blend modes (Normal, Multiply, Screen, Overlay,
   Soft/Hard Light, Darken, **Lighten**, Burn, Difference, **Sum**) plus
   clipping-mask/alpha inputs, and — per our own ground truth — a Composite
   IS accepted into roughness and colour inputs (only bump refuses it).
   Lighten = per-pixel max, Sum = add, Multiply = mask. That's a complete
   grayscale-math toolkit for combining N roughness sources into the single
   roughness input. The "one roughness driver, first wins" limitation in AA02
   is architectural, not a KeyShot limit. [CONFIRMED]

---

## 1. The scriptable capability surface (full census)

Everything below is a `lux.SHADER_TYPE_*` constant in the 11.0 reference
(cross-checked against 2024.1 — the set is stable across versions, so the
operator's build almost certainly has all of it; getattr-guard anyway).
Internal ids given because they're what `getType()` returns and what
`getNodesFromType()` wants.

### 1.1 Base material BRDFs

| Constant | id | Relevance to variety |
|---|---|---|
| `METAL` | `lux_metal` | in use; also carries `metal_type`, `metal_preset`, `spectral_ior`, `film_*` (thin-film/anodize), `coated` — most of an anodize/oxide system is already on this one node |
| `PLASTIC` | `lux_plastic_simple` | in use ("Diffuse" colour) |
| `PLASTIC_TRANSPARENT` | `lux_plastic` | tinted translucent plastics (PC, PMMA) |
| `PLASTIC_CLOUDY` | `lux_cloudy_plastic` | frosted/filled plastics |
| `PAINT` | `lux_paint` | in use; has implicit clearcoat-ish gloss |
| `METALLIC_PAINT` | `metallic_paint` | automotive base+flake+**clearcoat** model — the clearcoat lever |
| `AXALTA_PAINT` | `dupont_paint` | measured automotive paints |
| `GLASS` | `lux_window_glass` | thin glass |
| `GLASS_SOLID` | `lux_glass_simple` | solid glass |
| `DIELECTRIC` | `lux_glass` | full refractive glass w/ IOR, abbe |
| `GEM` | `lux_gem` | dispersion |
| `LIQUID` | `lux_liquid` | interface-aware refraction |
| `TRANSLUCENT` | `lux_translucent` | SSS-lite (soap, wax, skin-ish) |
| `TRANSLUCENT_ADVANCED` | `lux_translucent2` | better SSS |
| `TRANSLUCENT_MEDIUM` | `lux_translucent_mc` | volumetric SSS |
| `ANISOTROPIC` | `lux_anisotropic` | **directional roughness** — brushed/turned/machined finishes |
| `BRUSHED` | `lux_brushed2` | brushed-metal BRDF (linear) |
| `BRUSHED_RADIAL` | `lux_brushed_solid` | radial/turned brushing (spun aluminium, lathe faces) |
| `VELVET` | `lux_velvet` | sheen/asperity — fabric, suede |
| `CLOTH` / `REALCLOTH` | `lux_realcloth` / `lux_real_cloth` (2024) | woven fabric BRDF |
| `FUZZ` | `lux_fuzz` | geometric fuzz (also a geometry node) |
| `DIFFUSE` | `lux_diffuse` | pure lambert — chalk, unfinished plaster |
| `EMISSIVE` | `lux_emissive` | indicator LEDs, screens, lamp filaments |
| `ADVANCED` | `lux_advanced` | the kitchen-sink BRDF: diffuse+specular+IOR+fresnel controls |
| `GENERAL` / `GENERIC` | `lux_general` / `lux_generic` | Generic = KeyShot's PBR-style metal/rough workflow material |
| `THIN_FILM` | `lux_thinfilm` | iridescence **as a base material** (the AA02 header already learned this lesson) |
| `MEASURED` | `__measured` | measured BRDF files |
| `TOON`, `XRAY`, `FLAT`, `GROUND` | — | non-photoreal / staging; out of scope for realism but FLAT (`lux_constant`) is a useful "constant colour" utility source |

### 1.2 Procedural textures (colour and/or bump sources)

| Constant | id | Variety unlock |
|---|---|---|
| `NOISE_TEXTURE` / `NOISE_FRACTAL` | `lux_noise` / `lux_fractal_noise` | in use |
| `SCRATCHES` | `lux_scratches_worley` | in use |
| `SPOTS` | `lux_spots` | in use |
| `CELLULAR` | `lux_worley` | in use (experimental) |
| `OCCLUSION` | `lux_occlusion_tex` | in use |
| `CURVATURE` | `lux_curvature` | in use (mask) |
| `WOOD` / `WOOD_ADVANCED` | `lux_wood` / `lux_wood2` | wood family — rings, grain |
| `MARBLE` | `lux_marble` | marble/veined stone |
| `GRANITE` | `lux_granite` | granite, and a good **concrete/cast-mineral** base |
| `LEATHER` | `lux_leather_tex` | leather grain (colour+bump) |
| `WEAVE` | `lux_weave2` | woven textile pattern |
| `FIBER_WEAVE` | `lux_carbon` | **carbon fibre / CFRP** — a whole composite family from one node |
| `MESH`, `MESH_CIRCULAR`, `MESH_POLYGON` | `lux_mesh`, `lux_lattice_*` | perforated metal, speaker grilles, knurling-adjacent lattices |
| `CAMOUFLAGE` | `lux_camouflage` | blotch generator — surprisingly useful as an organic mask (mottling, patina blotches) |
| `CONTOUR` | `lux_contour_tex` | contour/topographic banding — machining-step / layer-line looks |
| `FLAKES` | `lux_flakes` | metallic flake sparkle (also geometry) |
| `BUBBLES` | `lux_bubbles` | subsurface bubble defects (cast resin, glass) |
| `COLOR_GRADIENT` | `lux_color_gradient` | in AA02, stops not script-settable (known); `PARAMETER_TYPE_COLORGRADIENT = 16` exists, so the *typed value* may be settable via `setValue` with the right payload — [PROBE] |
| `TEXTURE_MAP` | `__texture` | **image maps** — fingerprints, rust albedo, decals-as-textures. Param for the file path needs a probe (expect a string param, `PARAMETER_TYPE_STRING = 9`) |
| `TILED_UV` | `lux_tiled_texturemap` | tiled image maps |
| `VIDEO_MAP` | `sequence_rgba` | animated maps (out of scope) |
| `VERTEX_COLOR` | `lux_vertex_color` | if CAD import carries vertex colours |
| `MATCAP` | `matcap` | stylised; out of scope |

### 1.3 Utilities (the glue)

| Constant | id | Role |
|---|---|---|
| `COLOR_COMPOSITE` | `lux_color_blend` | **the mixer**: `source`(14) / `background`(14) / `clipping_mask`(14, pure) / `alpha`(4) / `blend_mode` / `mask_mode` / `invert_mask` — confirmed param surface from our dump. Blend modes: Normal, Multiply, Screen, Overlay, Soft Light, Hard Light, Darken, Lighten, Burn, Difference, Sum |
| `COLOR_ADJUST` | `lux_color_adjust` | hue/sat/brightness/contrast on any upstream colour — the **cheap variation knob** (one wood node, endless stain tones) |
| `COLOR_INVERT` | `lux_color_invert` | invert — pairs with masks and the brighter=rougher convention |
| `COLOR_KEY_MASK` | `lux_color_distance` | mask by colour similarity — e.g. isolate wood's dark rings into a roughness mask |
| `COLOR_TO_NUMBER` | `convert_rgba_to_float` | colour→scalar with input/output range remap (and inversion by swapping output range) — the **type adapter** for scalar inputs |
| `BUMP_ADD` | `lux_bumpmap_add` | in use — bump combiner |
| `BUMP_TO_ROUGHNESS` | `lux_bump2roughness` | **new to us**: converts bump micro-structure into roughness — the physically-motivated coupling lever (§6.2), and possibly a bump-domain→scalar-domain bridge for masking tricks [PROBE] |
| `MAPPING_2D` | `mapping2d` | explicit texture transform control |
| `TRI_PLANAR` | `triplanar` | UV-free projection — **the fix for CAD parts with garbage UVs**; wrap any image/2D texture in tri-planar and scale is consistent across every part |
| `MAPPING_WARP` | `lux_mapping_warp` | distort a texture's lookup by another texture — turns clean procedurals into organic ones (wavy wood, smeared grime) |
| `OBJECT_INFO` | `lux_object_info` | per-object values — **per-part variation inside one material** (assembly colour jitter) [PROBE param surface] |
| `CURVE_COLOR_RANDOMIZE` | `lux_curve_randomize` | randomised colour per curve/object — same family of trick |
| `RAY_MASK`, `SURFACE_BACKSIDE_MASK`, `CUTAWAY`, `WIREFRAME` | — | staging/special; `lux_backside_mask` could gate interior-vs-exterior wear [PROBE, low pri] |

### 1.4 Geometry nodes (change the surface, not just the shading)

| Constant | id | Use |
|---|---|---|
| `DISPLACE` | `lux_displace` | true displacement from a texture — **real chipped edges, hammered dents, cast texture** with silhouette change. Heavier render cost. `MaterialGraph.executeGeometryNodes()` exists specifically to run these — strong hint they're fully scriptable |
| `ROUNDED_EDGES` | `lux_rounded` | in use |
| `FLAKES`, `BUBBLES`, `FUZZ` | — | geometric sparkle / defects / fibres |

### 1.5 Graph/param API beyond what AA02 uses

- `graph.getNodes()`, `getNodesFromType(type)`, `getNodeFromID(id)` — lets a
  probe/verifier script *audit* a built graph instead of trusting the build.
- `node.getInputEdges()`, `getOutputEdges()`, `getInputEdge(param)` — confirm
  a wire actually landed (the mask→bump_height failure was *silent*; this is
  the antidote — after every `newEdge`, check `getInputEdge(param)` is real).
- `MaterialGraph.setMultiMaterial(enable)` / `setCurrentSubMaterial(node)` /
  `getMaterialNodes()` — multi-material variant sets (§4.7).
- `lux.setMaterialTemplate(name)` / `getMaterialTemplates()` — template
  presets exist as API; peripheral here but relevant to the Creo→KeyShot
  lookup sibling script.
- `PARAMETER_TYPE_COLORGRADIENT = 16`, `PARAMETER_TYPE_WEAVEPATTERN = 19` —
  typed values for gradient stops and weave patterns exist; `setValue` with a
  correctly-shaped payload may set them even though the GUI widget looks
  unscriptable. [PROBE]

### 1.6 Reconciliation with AA02 ground truth

Nothing above contradicts the render-proven facts; two refinements:

- The dump's `PARAMETER_TYPE` numbers map cleanly onto the reference's names:
  13 = COLOR (plain value), 14 = COLORALPHA (texturable colour input),
  15 = FLOATARRAY (spectral/IOR curves), 12 = MATRIX (texture transform).
  Useful because it tells us **the type number alone predicts wireability**:
  wire textures into 14s freely; 13s are value-only (this is why Curvature's
  `positive_curvature`(13) may refuse a nested texture — see §4.3 probe);
  4s (float) accept edges *sometimes* (roughness did, bump_height didn't) —
  the discriminator is probably `isPure()` plus per-node engine rules, so
  probe per-slot, never assume.
- "No label API" (MWR-9C4E21) stands for *methods*, but the SHADERLABEL
  parameter type + our own root dump reopens the question at the *graph edge*
  level (§4.4).

---

## 2. A material-variety taxonomy

Variety is not "more toggles" — it's independent axes multiplied together.
Four axes cover essentially everything a product render needs:

```
LOOK = FAMILY (what it is)
     x FINISH (how it was made)
     x WEATHERING (what happened to it since)
     x CONTEXT (scale, part-role, palette)
```

### 2.1 Axis 1 — material families

Reachability legend: ● = every needed node confirmed, ◐ = confirmed nodes but
unprobed params, ○ = needs probe pack first.

| Family | Sub-families | Base recipe | Reach |
|---|---|---|---|
| **Ferrous metal** | mild steel, stainless, cast iron, blued steel | `METAL` + grey tints; cast iron adds Cellular bump + high rough | ● |
| **Non-ferrous metal** | aluminium (mill/brushed/anodised), titanium, zinc | `METAL` (+ `film_*` for anodise/titanium heat tint; `coated` toggle confirmed on our build) | ● |
| **Precious/decorative** | brass, bronze, copper, gold, chrome | `METAL` tints (already in the palette) | ● |
| **Oxidised metal** | rust, mill scale, verdigris/patina, tarnish | metal base + colour composite of rust tones masked by Camouflage/Cellular + occlusion; heavy versions add Displace | ◐ |
| **Rigid plastic** | ABS, PC, nylon (glass-filled), PP | `PLASTIC` / `PLASTIC_TRANSPARENT`; filled nylon = fine noise + slight colour mottle | ● |
| **Elastomer** | rubber, TPU, silicone | `PLASTIC` high rough, low spec + `TRANSLUCENT` for silicone | ◐ |
| **Textured moulding** | mould-tech textures, bead-blast plastic | `MOLD_TECH_PLASTIC` (`lux_moldtech_plastic`!) or plastic + noise/spots bump | ◐ |
| **Painted** | wet paint, powder-coat (orange peel!), e-coat | `PAINT` + Noise bump at low amplitude for orange peel | ● |
| **Automotive** | metallic paint, clearcoat, candy | `METALLIC_PAINT` (flakes + clearcoat built in), `AXALTA_PAINT` | ◐ |
| **Anodised** | clear/black/colour anodise | already faked with tinted metal; *proper* = `coated`/`film_*` on Metal — confirmed present on our build | ◐ |
| **Glass/transparent** | window, solid, frosted, tinted PC | `GLASS`, `GLASS_SOLID`, `DIELECTRIC`, `PLASTIC_TRANSPARENT`; frosted = roughness on dielectric | ◐ |
| **Translucent** | wax, soap, resin prints, diffuser plastic | `TRANSLUCENT`(+`_ADVANCED`) | ◐ |
| **Ceramic** | glazed, technical (alumina), porcelain | glazed = `PLASTIC` low rough + slight SSS; technical = `DIFFUSE`-ish + fine noise | ◐ |
| **Composite** | CFRP (twill/plain), fibreglass | `FIBER_WEAVE` colour+bump under a clearcoat-ish low-rough surface | ◐ |
| **Organic** | wood (+stained/varnished), leather | `WOOD`/`WOOD_ADVANCED`/`LEATHER` textures driving colour+bump on plastic-ish base; `COLOR_ADJUST` for stains | ◐ |
| **Stone/mineral** | marble, granite, concrete, terrazzo | `MARBLE`/`GRANITE` + fine noise; concrete = granite desaturated + spots + occlusion grime | ◐ |
| **Fabric** | woven, velvet/suede, mesh | `CLOTH`/`WEAVE`, `VELVET`, `MESH_*` | ○ |
| **Emissive** | LEDs, panels | `EMISSIVE` | ◐ |
| **Iridescent** | thin-film, oil-slick, heat tint | `THIN_FILM` base or Metal `film_*` | ◐ |

That's ~18 families vs. today's 3 — and 12 of them need zero new *node types*
beyond what §1 confirms, only new recipe rows and probed params.

### 2.2 Axis 2 — finishes (process signatures)

A finish is (micro-bump pattern) + (roughness value/pattern) + (anisotropy) —
independent of family where physically sensible:

| Finish | Signature | Recipe |
|---|---|---|
| Polished / mirror | rough ≈ 0.02–0.06, no visible bump | value only |
| Brushed (linear) | anisotropic streaks | `ANISOTROPIC`/`BRUSHED` base **or** Scratches (high density, aligned, tiny) → roughness + bump [§4.5] |
| Spun / turned (radial) | radial anisotropy | `BRUSHED_RADIAL` base |
| Satin / bead-blasted | uniform micro-matte, no direction | rough 0.25–0.45 + Noise fine bump |
| Machined | faint regular tool marks | `CONTOUR` or aligned Scratches at low amplitude → bump + rough |
| Cast (sand/die) | grainy pebbled bump, mid-rough | Cellular + Noise bump stack |
| Hammered | large soft dents | Cellular, big scale, deep bump (or Displace) |
| Knurled / gridded | regular relief | `MESH_*` bump [PROBE scale control] |
| EDM / spark-eroded | dense random pitting | Spots high density, tiny radius |
| Orange peel (powder-coat) | low-freq wavy bump on paint | Noise, scale ~0.3, bump ~0.01 |
| Mould-tech | standardised plastic textures | `MOLD_TECH_PLASTIC` [PROBE] |
| Layer lines (FDM print) | fine parallel ridges | Contour/Scratches aligned, regular |

### 2.3 Axis 3 — weathering (history)

Ordered roughly pristine → destroyed; each is a *layer* with its own mask
logic and channel targets (C=colour, R=roughness, B=bump, G=geometry):

| Layer | Channels | Natural mask | Family gate |
|---|---|---|---|
| Fingerprints / smudges | R | sparse noise threshold | polished/glossy only |
| Dust settle | C+R | **up-facing** — no normal-direction node confirmed; approximate with Occlusion-inverse or accept uniform + intensity [PROBE: any "up" signal] |  all |
| Water spots | R (+slight C) | Spots, sparse | glossy |
| Handling polish (worn-smooth edges) | R (darker=smoother on edges!) | Curvature | all |
| Edge wear / paint chip-through | C+R (+B if probed) | Curvature (tight) | painted/anodised/coated |
| Scratches (directional handling) | R+B | Curvature or uniform | all |
| Cavity grime | C+R | Occlusion | all |
| UV fade / yellowing | C | broad, low-freq noise | plastics, paints |
| Tarnish / oxide film | C+R | Camouflage/noise mottle | Cu alloys, silver, steel |
| Patina (verdigris) | C+R+B | Occlusion-weighted mottle | copper/bronze/brass ONLY |
| Rust | C+R+B(+G) | Cellular ∪ Spots, occlusion-weighted | ferrous ONLY |
| Paint blistering/peel | B+C | Spots large sparse | painted |
| Dents / dings | B/G | sparse | sheet metal |
| Cracks / crazing | B+C | Cellular thin-edge mode | ceramics, old paint, plastics |

The **family gate** column is the core of "curated randomness" (§5): rust
never lands on brass, patina never on ABS.

### 2.4 Axis 4 — context

- **Scale-awareness**: texture scales must track part bbox (the pipeline's
  5-tier size classification from RPA-7B2E4D plugs straight in — a 2 mm part
  and a 70 m assembly cannot share `scratch_size`).
- **Part role**: housings vs. fasteners vs. sightglass — a future hook for the
  Creo-name→family lookup (`1_HLP_MAT_LOOKUP`).
- **Palette**: per-family curated colour sets (§5.4), not one global 12-list.

---

## 3. Composable architecture — the recipe model

### 3.1 The shape of the problem with AA02

AA02 is a *flat option dict* → one hardcoded build path. Every new capability
(a family, a finish, a wear layer) currently means new toggles, new branches,
and new interference rules (the loud-layer cap, the "one roughness driver"
arbitration). That's O(n²) interactions. The fix is to make the *description*
of a material first-class and let one small engine compile any description.

### 3.2 MaterialSpec — the data model

A plain dict (JSON-serialisable — Python <3.6-safe, no dataclasses), built by
*samplers*, compiled by *one* builder:

```python
spec = {
    "meta": {
        "name": "MAT-STL-MCH-MOD-7F3A2C",
        "seed": 42117,
        "generator_rev": "AB01",
        "family": "metal.ferrous.steel",
        "finish": "machined",
        "wear_story": "workshop_veteran",   # see 5.3
    },
    "base": {
        "shader": "SHADER_TYPE_METAL",       # resolved defensively as today
        "params": {                          # display-name keyed, set_display()
            "color": [0.55, 0.56, 0.58],
            "roughness": 0.25,
            # family extras ride along untyped:
            # "metal_type": ..., "coated": True, "film_thickness": ...
        },
    },
    "finish": {                              # exactly one
        "kind": "machined",
        "bump": [ {"node": "SHADER_TYPE_SCRATCHES",
                    "params": {"density": 0.9, "size": 0.01,
                                "directional noise": 0.05,
                                "bump height": 0.004}} ],
        "roughness_layers": [                # composited, in order (4.2)
            {"node": "SHADER_TYPE_SCRATCHES", "blend": "lighten",
              "params": {"color": [0.5,0.5,0.5]}} ],
        "anisotropy": None,                  # or {"mode":"linear","angle":90}
    },
    "weathering": [                          # ZERO OR MORE, ordered
        {"kind": "edge_wear", "intensity": 0.6,
          "mask": {"type": "curvature", "feather": 0.3},
          "channels": {
              "roughness": {"node": "SHADER_TYPE_NOISE_TEXTURE",
                             "blend": "lighten", "value_hi": 0.7},
              "color":     {"blend": "normal", "alpha": 0.35,
                             "tint": [0.62, 0.62, 0.64]},
              "bump":      {"strategy": "best_available"}   # see 4.3
          }},
        {"kind": "cavity_grime", "intensity": 0.4,
          "mask": {"type": "occlusion", "radius": 0.008},
          "channels": {"color": {...}, "roughness": {...}}},
    ],
    "micro": {"fine_noise": {"scale": 0.15, "bump": 0.01}},
    "mapping": {"scale_tier": "Standard"},   # bbox tier -> global scale mult
}
```

Key properties:

- **Layers are data, not code paths.** Adding "tarnish" = adding a sampler
  entry + a channel recipe, zero new builder branches.
- **The spec is the reproducibility artifact.** Today a seed only reproduces
  a look if the script rev is identical. Write the spec itself to the console
  (and optionally a sidecar JSON next to the .bip) — any future rev can
  rebuild the exact material from the spec, and the render pipeline's
  manifest/audit stages (`3_`, `4_`) can log which spec produced which frame.
- **Dialog compatibility**: the existing dialog becomes just another sampler —
  checkboxes construct a spec. Randomize mode constructs a spec from
  distributions. A future batch mode constructs N specs.

### 3.3 The compile pipeline

```
sample_spec(family, finish, wear_level, seed)   # or from dialog / JSON
        |
validate_spec(spec)      # family gates, cap rules, scale tiers
        |
build_material(spec)     # ONE builder:
    1. base node + params
    2. finish -> bump bus + roughness bus + (aniso base swap)
    3. each weathering layer -> per-channel contributions:
         colour bus (Color Composite chain onto base colour input)
         roughness bus (Color Composite chain onto roughness input)
         bump bus (Bump Add chain, masked via best_available strategy)
    4. micro layer -> bump bus tail
    5. verify: walk getInputEdges() on base; log every wire that DIDN'T land
        |
apply + report (unchanged)
```

The three **buses** are the architectural heart — see §4.1/4.2. The builder
never special-cases "scratches also drive roughness"; a layer just declares
contributions to more than one bus.

### 3.4 Why this scales to "thousands of distinct looks"

Counting conservatively: 18 families × avg 3 sub-families × 8 applicable
finishes × 4 wear levels × ~10 meaningfully-distinct weathering combinations
× continuous colour/param jitter ≈ **17k+ discrete recipe skeletons** before
any continuous variation — from ~25 layer implementations and ~60 sampler
range entries. The multiplication only works because the axes are composed
independently; a flat toggle list can never get there.

---

## 4. Graph connection strategies (the wiring cookbook)

Every recipe below uses confirmed param names from our own dumps where we
have them; others are [LIKELY]/[PROBE] tagged.

### 4.1 The colour bus — N tint layers onto one colour input [CONFIRMED]

Chain Color Composites; each weathering layer's colour contribution is one
link:

```
base_colour (constant, set on base node OR a FLAT node)        <- background
wear_tint_1 (e.g. grime colour or a texture)                    <- source
mask_1 (Curvature/Occlusion/noise)                              <- clipping_mask (pure, type 14)
blend_mode = Normal (or Multiply for grime), alpha = intensity
        v
composite_1  -> becomes background of composite_2 -> ... -> base.color (type 14)
```

Confirmed mechanics: `source`/`background`/`clipping_mask`/`alpha`/
`blend_mode`/`mask_mode`/`invert_mask` all exist on `lux_color_blend`;
composites are accepted by colour inputs; textures fan out (one Curvature can
mask several composites).

Open question worth one probe: whether `blend_mode` sets by enum int or
string label — dump it, set both ways, read back with `getValue()`.

### 4.2 The roughness bus — SOLVING the "drivers compete" problem [CONFIRMED]

Today: one winner wires into `roughness`. Instead, composite in grayscale
space (brighter = rougher, render-confirmed):

```
finish_roughness  = FLAT/constant grey at base rough (background)
+ scratches (colour output: streak 0.75 / bg = base rough)   blend=Lighten
+ fractal broad variation (remapped to ±0.08 around base)     blend=Normal, alpha=0.5
+ cavity grime (white in cavities via Occlusion colours)      blend=Lighten
+ handling polish on edges (DARK on edges via Curvature)      blend=Darken
        v
final composite -> base.roughness
```

- **Lighten (max)** is the physically-right combiner for "wear only ever
  roughens": no over-add blowout, no competition.
- **Darken** expresses the opposite and under-used truth: *handled edges get
  POLISHED* (smoother, brighter highlights) — worn brass door handles. A
  Curvature with dark `positive_curvature`, mid-grey elsewhere, Darken-blended,
  gives "gloss ring on the edges" — a look the current generator cannot make
  and one of the strongest realism reads available. [LIKELY — needs one render
  to taste]
- **Sum** with small values for accumulative layers (dust).
- To *remap* a texture's range before blending (e.g. fractal noise 0–1 →
  0.2–0.35): `COLOR_TO_NUMBER` has input/output range remap but outputs a
  number — fine for a final scalar input, not for composite chains. In-chain,
  use the texture's own colour/background params (Scratches-style) where they
  exist, or `COLOR_ADJUST` (brightness/contrast) where they don't. [LIKELY]

Note the base node's roughness *value* param stays as fallback: if any wire
fails, `set_display(base, "roughness", value)` still applies — keep AA02's
degrade-never-break behaviour per bus.

### 4.3 Spatial bump masking — the unsolved problem, four plan-Bs, ranked

Ground truth: `bump_height` refused a texture edge; Composite→bump refused
("Could not create requested edge"). Candidate strategies, in the order the
probe pack should try them:

**(a) Nest the effect inside the mask node's colour slots. [PROBE — best
payoff/effort]** Curvature/Occlusion are *texture* nodes (`lux_curvature`,
`lux_occlusion_tex`). If their colour slots are texturable, wire the effect
INTO the mask instead of the mask into the effect:

```
Scratches (colour out) -> Curvature.positive_curvature
flat black             -> Curvature.zero/negative_curvature
Curvature (now "scratches only on edges" as a texture) -> Bump Add slot
```

The Curvature node itself then enters the bump chain — no composite, all
texture-domain. Our dump typed those slots 13 (value-only), which predicts
refusal — BUT the GUI demonstrably allows nesting textures into Curvature
colour inputs (KeyShot's own "colorful edge effects" workflow), so either the
dump misread, the type differs per version, or `newEdge` ignores the 13/14
distinction. One `safe_edge` call answers it. If (a) works, masking is solved
for every layer with zero new architecture — this is the highest-priority
probe after labels.

**(b) Route the mask through COLOR_TO_NUMBER into bump_height. [PROBE]**
The failed edge was texture(colour)→bump_height(float). A float-typed source
might be accepted where a colour-typed one wasn't:
`Curvature -> convert_rgba_to_float -> scratches.bump_height`. Cheap to test.
(Suspicion from the roughness precedent: roughness is also type 4 and accepted
a *texture* directly, so type coercion exists *somewhere* — the bump_height
refusal may be a per-slot rule that no adapter fixes. Probe anyway; it's one
edge.)

**(c) Masked DISPLACE instead of masked bump. [PROBE — highest ceiling]**
`lux_displace` reads a height *texture* input (type expected 14 — texturable),
so `Composite(effect x mask) -> Displace.height` should be legal where
Composite→bump was not. Displacement also buys silhouette-true chips, dents
and hammering that bump can never deliver. Costs: geometry memory, needs
`executeGeometryNodes()`, and amplitude discipline (tie to bbox tier). Even if
(a) works, displacement is worth probing for the *heavy* end of the wear axis.

**(d) Concede bump; mask roughness+colour only. [CONFIRMED fallback]**
Already proven: masked wear reads ~80% through roughness/colour. Keep global
low-amplitude bump for texture, express *placement* entirely in the other two
buses. This is the shipping default until a probe wins.

Also worth knowing: `BUMP_TO_ROUGHNESS` (`lux_bump2roughness`) can convert
whatever bump stack exists into a roughness contribution — so even when bump
is unmasked, the *roughness consequence* of the bump can join the masked
roughness bus, keeping the two channels coherent. [PROBE param surface]

### 4.4 Labels — the possible resurrection [PROBE, highest single payoff]

Evidence: `PARAMETER_TYPE_SHADERLABEL = 65538` exists; our root dump showed a
65538 param on the root node. The classic worn-edge technique is a *label*
sub-material (rust / bare-metal / gloss) whose opacity is masked so it only
appears in wear zones. If the root's label slot accepts an edge from a
material node:

```
label_mat = graph.newNode(lux.SHADER_TYPE_METAL)        # bare-steel chip-through
curvature -> label_mat.opacitymap        # opacitymap CONFIRMED type 14 on Metal!
graph.newEdge(source=label_mat, target=root, param=<65538 slot name>)
```

...then paint-chipped-to-metal, rust-over-paint, sticker/decal wear — the
whole two-material vocabulary — becomes scriptable inside one graph. Note the
enabling fact we already own: **`opacitymap` is a confirmed texturable input
on Metal** — the mask goes into *opacity*, which is exactly the mappable slot
that `bump_height` wasn't. Probe order: dump the root's parameters, find the
65538 name (likely `labels` or similar), attempt the edge, render one frame.
If multiple labels chain, even better (grime over chips over paint).

### 4.5 Anisotropy / brushed metal [LIKELY]

Three routes, cheapest first:

1. **Fake with aligned Scratches** (available today): density 0.8+, size tiny,
   directional noise ~0.05, driving roughness + faint bump. Reads brushed at
   product-shot distance. [CONFIRMED nodes]
2. **`SHADER_TYPE_BRUSHED` / `BRUSHED_RADIAL` as base** — purpose-built,
   likely exposes brush angle/strength. Radial variant covers spun/turned
   faces (a look route 1 cannot fake). [LIKELY — dump params]
3. **`SHADER_TYPE_ANISOTROPIC` as base** — expect roughness X/Y + angle +
   sample params; the general solution and the one that composes with the
   roughness bus (its roughness inputs may be texturable). [PROBE]

Family table entries: brushed/spun finishes swap the *base shader* rather
than adding layers — the spec's `finish.anisotropy` field triggers the swap.
This is why finish belongs in the spec, not in a bolt-on toggle.

### 4.6 Clearcoat / automotive / coated looks [LIKELY]

- `METALLIC_PAINT` (`metallic_paint`): base colour + flake controls +
  clearcoat layer in one BRDF. Expect params for flake size/density and clear
  coat roughness/thickness. Weathering interplay: scratches on a clearcoat cut
  the *coat* (white-ish scuffs, roughness-only) — conveniently exactly what our
  masked roughness bus does best; deep chips need the label probe.
- `PAINT` (current) reads as single-stage paint.
- Metal's confirmed `coated` ('Anodized' toggle) + `film_*` params: proper
  anodise (dye colour = tint, film = sheen) and titanium heat-tint gradients.
  One render session of param sweeps turns the current "tinted metal" anodise
  fakes into the real thing. [CONFIRMED params exist; values need tasting]

### 4.7 Translucency / glass [LIKELY]

- Frosted glass = `DIELECTRIC` + roughness (the roughness bus works on any
  base — sandblasted-band-on-glass is just a masked roughness layer).
- Tinted PC = `PLASTIC_TRANSPARENT` + colour.
- Wax/resin/diffusers = `TRANSLUCENT`(+`_ADVANCED`); expect translucency
  colour + depth params.
- Weathering gate: most wear layers apply (dust, scratches, fingerprints —
  fingerprints on glass are the classic), but bump layers should damp (bump
  on refractive surfaces distorts violently — cap amplitudes ~0.3×).

### 4.8 Per-part variation inside one material [PROBE, sleeper hit]

`OBJECT_INFO` (`lux_object_info`) and `CURVE_COLOR_RANDOMIZE`
(`lux_curve_randomize`) suggest per-object signals usable as colour/mask
sources. If Object Info exposes a random-per-part colour/id: one material
applied to a 200-part assembly renders with subtle per-part tint/roughness
jitter — the single cheapest "CG-ness killer" for assemblies, and it composes
with everything else (wire it as a low-alpha layer on the colour bus).

### 4.9 Mapping discipline [LIKELY]

- Wrap image textures (`__texture`) in `TRI_PLANAR` so CAD parts without UVs
  texture correctly — mandatory before the fingerprint/rust-map work lands.
- `MAPPING_WARP`: distort clean procedurals with a noise for organic grime
  edges (straight Occlusion masks read mechanical; warped ones read grown).
- Global scale multiplier per bbox tier (§2.4) applied to every `scale`-like
  param — one number, everything coherent at any part size.

---

## 5. The procedural variation engine — curated randomness

### 5.1 Principle

Uniform random over a big parameter space produces mush; realism lives on a
low-dimensional manifold inside it. The engine's job is to sample *stories*,
not parameters: pick a family, pick a plausible process for that family, pick
a plausible history for that process, then jitter within tight, per-family
ranges.

```
seed -> family (weighted) -> sub-family -> finish (from family's allowed set)
     -> wear story (from family x finish allowed set) -> intensity scalar
     -> per-layer param jitter (tight gaussians, family-tuned)
     -> palette pick (family palette, jittered in HSV by small deltas)
```

Everything downstream of the seed is deterministic → the seed + generator rev
(or better, the emitted spec) reproduces the material exactly. Keep AA02's
separate never-seeded `_name_rng` for name uniqueness.

### 5.2 Family gating tables (the realism firewall)

```python
WEAR_COMPAT = {
    "rust":        lambda fam: fam.startswith("metal.ferrous"),
    "patina":      lambda fam: fam in ("metal.precious.copper",
                                        "metal.precious.brass",
                                        "metal.precious.bronze"),
    "uv_fade":     lambda fam: fam.startswith(("plastic", "paint")),
    "chip":        lambda fam: fam.startswith(("paint", "anodised", "ceramic")),
    "fingerprint": lambda fam, finish: finish in GLOSSY_FINISHES,
    ...
}
FINISH_COMPAT = {
    "brushed":  metals_only, "spun": metals_only,
    "orange_peel": paints_only, "mold_tech": plastics_only,
    "knurled": metals_plus_hard_plastics, ...
}
```

Sampling *rejects* (or never proposes) incompatible combos. This one table is
the difference between "huge variety" and "casino noise".

### 5.3 Wear stories — correlated layer bundles

Independent per-layer rolls make incoherent objects (pristine gloss + heavy
rust). Sample a *story*, which fixes which layers appear and correlates their
intensities to one age scalar:

| Story | Layers (weights vs. age) |
|---|---|
| `shelf_queen` | dust 0.3, fingerprints 0.2 |
| `daily_driver` | fingerprints 0.6, edge polish 0.5, light scratches 0.4, grime 0.3 |
| `workshop_veteran` | scratches 0.8, edge wear 0.8, grime 0.7, dents 0.4, oxide film 0.3 |
| `outdoor_service` | UV fade 0.7, rust/patina 0.6 (family-gated), grime 0.6, water spots 0.4 |
| `salvage` | everything at 0.7–1.0, chips + heavy rust + displacement if available |

Age scalar replaces the current wear multiplier; stories replace the flat
toggle grid in randomize mode (the manual checkbox path still exists — it
just builds a custom story).

### 5.4 Per-family palettes

Replace the single 12-row list with per-family curated sets + jitter:

- **Metals**: physically-plausible tint ranges per alloy (steel greys
  0.50–0.58 neutral; brass hue 38–45° etc.). Jitter value ±0.03, hue ±3°.
- **Anodise**: the real dye catalogue (clear, black, red, blue, gold, violet…).
- **Paints**: RAL-classic and safety colours as anchors; powder-coats skew
  satin, wet paints skew gloss.
- **Plastics**: molded-part tones (jet black 0.02–0.05, naturals, PANTONE-ish
  brights).
- **Grime/rust/patina tint tables** shared across families (rust core
  #6a3b22→#8c5a2b range; verdigris #3e7f6f range) — wear colours are far more
  universal than base colours.

Palette + jitter means two materials with the same recipe still differ — the
long tail of variety comes free.

### 5.5 Loudness budget, generalised

Keep AA02's `1/sqrt(n)` damping but move it to *per-bus energy budgets*:
bump bus total amplitude ≤ B(tier, family), roughness bus deviation ≤ R,
colour bus alpha sum ≤ C. Layers spend from the budget in story-priority
order; late layers get squeezed rather than the whole surface saturating.
Same idea as today, but it scales to 8 layers instead of 4 toggles.

---

## 6. Realism levers (what makes it read as *real*)

1. **Fresnel comes free — protect it.** Every KeyShot BRDF is already
   energy-conserving with proper fresnel; there is no fresnel node because
   it's built in. The way scripts *break* the read is albedo abuse: metals
   tinted with non-physical colours, plastics with albedo ≥ 0.9. Clamp
   family albedo ranges in the sampler (paint white 0.90 is already at the
   ceiling — good; never above).
2. **Roughness–bump coherence.** Any visible bump structure should have a
   roughness consequence and vice versa. `BUMP_TO_ROUGHNESS` is the literal
   node for this; short of it, every finish recipe pairs its bump texture
   with a matching roughness-bus layer (already accidentally true for
   scratches — make it a rule).
3. **Micro-variation is non-optional.** Perfectly uniform roughness is the
   #1 CG tell. The spec's `micro` block (fine noise bump ~0.01) plus a
   ±0.03 fractal layer on the roughness bus should be ON by default for every
   family, damped only for mirror finishes.
4. **Wear tells a story in the RIGHT places.** Edges polish *and* chip;
   cavities collect grime *and* keep original gloss under it. The
   Curvature-Darken edge-polish trick (§4.2) + Occlusion grime together are
   the 80/20 of "this object has been owned".
5. **Colour–roughness coupling in wear layers.** Grime darkens AND roughens
   (pair the layers, one mask, both buses). Polish brightens metals slightly
   AND smooths. Never move one channel alone in a wear layer.
6. **Two-scale rule.** Every surface gets one micro (fine noise) and one
   macro (fractal/mottle) variation at ~10× different scales. Real materials
   have detail at every octave; two is the minimum that fools the eye.
7. **Anisotropy where the process implies it.** Brushed/spun/machined
   surfaces with isotropic roughness read as paint-over-metal. Even the
   scratch-fake (§4.5 route 1) beats isotropic.
8. **Scale honesty.** Tie all texture scales to bbox tier; a scratch is
   0.2–2 mm in the real world, and it should be on the part too, whether the
   part is a watch case or a chassis.
9. **Restraint as a feature.** The most realistic materials the generator
   will ever emit are `daily_driver` at age 0.2 — barely-there wear. Bias the
   story sampler toward subtle; make `salvage` rare.

---

## 7. What stays true from AA02 (don't regress these)

- ASCII-only, f-string-free, Python <3.6 (embedded interpreter constraint).
- getattr-guarded constants; `try_new_node` / `set_display` / `safe_edge`
  never-fatal helpers; degrade-never-break per layer.
- Headless path via DEFAULT_OPTIONS; dialog in GUI.
- Brighter = rougher; brighter = raised bump; negative bump = grooves.
- Plastic's colour is "Diffuse"; base colour input is type 14 — match by
  name, not type.
- DIALOG_ITEM index/label normalisation (`norm_item`).
- The `_name_rng` split; collision-retry on `createSceneMaterial`.
- The loud-layer damping *concept* (generalised in §5.5, not removed).

New discipline to add: **post-build wire audit** — after building, walk
`base.getInputEdges()` / `getInputEdge(param)` and print a one-line wiring
manifest. Silent edge failures (the bump_height bug) become impossible to
miss.

---

## 8. The probe pack — one throwaway script before Phase 2

`0_CHK_MATGRAPH_PROBE_AA01.py` (or run in console): builds one disposable
material, then for each question below, attempts it, prints PASS/FAIL +
dump, and removes its nodes. Output pasted back into this doc as Rev 2.

| # | Probe | Method | Unblocks |
|---|---|---|---|
| P1 | Root label slot | dump root params; find 65538; `newEdge(metal2 -> root, param)`; drive metal2.opacitymap with Curvature; render 1 frame | §4.4 chip-through, rust-over-paint |
| P2 | Texture into Curvature/Occlusion colour slots | `newEdge(scratches -> curvature.positive_curvature)` | §4.3(a) masked bump |
| P3 | COLOR_TO_NUMBER into bump_height | build chain, check `getInputEdge` | §4.3(b) |
| P4 | Displace height input texturable + Composite accepted | wire, `executeGeometryNodes()`, render | §4.3(c) heavy wear |
| P5 | New base params: dump ANISOTROPIC, BRUSHED, BRUSHED_RADIAL, METALLIC_PAINT, DIELECTRIC, TRANSLUCENT, EMISSIVE, GENERIC, THIN_FILM, MOLD_TECH_PLASTIC | `dump_node` each | §2.1 families, §4.5–4.7 |
| P6 | Texture nodes: dump WOOD(+2), MARBLE, GRANITE, LEATHER, FIBER_WEAVE, WEAVE, MESH_*, CAMOUFLAGE, CONTOUR, FLAKES, BUBBLES | `dump_node` each | family recipes |
| P7 | `__texture` file path param: create TEXTURE_MAP, dump, set a PNG path string, render | fingerprints/rust maps |
| P8 | Composite blend_mode value format (int enum vs string) + Lighten/Darken behaviour on roughness | set, `getValue`, render grey chart | §4.2 roughness bus |
| P9 | OBJECT_INFO + CURVE_COLOR_RANDOMIZE param surfaces | dump; wire to colour on a multi-part scene | §4.8 |
| P10 | setMultiMaterial(True) + sub-material behaviour from script | build 2 sub-roots, switch, save | §4.7 variant sets |
| P11 | COLORGRADIENT (16) setValue payload shapes | try list-of-stops formats on Color Gradient | resurrect gradient node |
| P12 | Metal `film_*` / `coated` sweep | 6 renders, thickness sweep | proper anodise/heat tint |
| P13 | BUMP_TO_ROUGHNESS in/out types | dump + wire bump stack through it into roughness bus | §6.2 coupling |

Rule stays the rule: **nothing ships designed *around* a probe result until
the probe has actually run on the real build.** Design-for (this doc) is
fine; depend-on is not.

---

## 9. Roadmap — shippable increments

Each phase renders something new; no phase depends on an unprobed assumption.

**Phase 0 — Probe pack + wire audit.** (small)
The §8 script + the `getInputEdges` post-build manifest added to AA02 as-is.
Ship: a Rev-2 update of this doc with PASS/FAIL ground truth.
Risk: none. Value: converts 13 unknowns into facts.

**Phase 1 — Spec refactor (AB01).** (the architectural release)
Same features as AA02, rebuilt as sample→validate→compile with the three
buses. Roughness bus lands here (CONFIRMED tech, immediate visible win:
scratches + fractal + occlusion coexist at last). Dialog unchanged; emits the
spec to console for reproducibility.
Ship: visibly richer roughness on existing 12 materials.
Risk: low — pure restructure plus one confirmed capability.

**Phase 2 — Families + palettes.** 
New MATERIALS rows become family entries: glass/dielectric, transparent +
cloudy plastic, translucent, emissive, metallic paint, thin-film base, and
the probed anodise (`film_*`). Per-family palettes + jitter (§5.4).
Ship: palette grows 12 → 40+; first non-opaque materials.
Risk: low; every family degrades to Plastic via `resolve_shader` if a
constant is missing.

**Phase 3 — Finishes.** 
Finish layer in the spec: satin/bead-blast/cast/machined/orange-peel from
confirmed nodes; brushed/spun via probed BRUSHED/ANISOTROPIC (fallback:
scratch-fake route). Bbox-tier scale multiplier.
Ship: process-true surfaces; brushed aluminium that actually streaks.
Risk: medium on aniso params (P5 covers it).

**Phase 4 — Weathering engine.** 
Wear stories + family gates + per-bus budgets; masked colour/roughness wear
via composite chains (CONFIRMED); bump masking via best probe winner (else
strategy (d)); grime/tarnish/patina/rust colour recipes; fingerprints if P7
passed.
Ship: the "this object has been owned" release — the biggest visual leap.
Risk: medium — most new code, but every layer is independently degradable.

**Phase 5 — The lottery.** 
Batch mode: N seeded specs → N materials (optionally straight onto the
`3_PRC_CONTACT_SHEET` pipeline for a material contact sheet per run). Spec
sidecar JSON. Multi-material variant sets if P10 passed.
Ship: "give me 24 plausible steels" in one run + a sheet to pick from.
Risk: low; it's iteration around Phase 1–4 machinery.

**Phase 6 — Frontier.** 
Displacement wear (P4), label-based chip-through (P1), per-part jitter (P9),
wood/marble/leather/carbon organic families (P6), Mapping Warp organic masks.
Ship: hero-grade damage + full family coverage.
Risk: highest — everything here is gated on a probe by design.

### Biggest risks / unknowns, honestly ranked

1. **Bump masking may be flatly impossible** (P2/P3/P4 all fail) → strategy
   (d) is the permanent answer; acceptable (roughness+colour carry the read).
2. **Label slot may refuse script edges** (P1) → chip-through stays
   approximated by colour/roughness composites; patina/rust still fine.
3. **Aniso/brushed params may be GUI-oriented** (weird types, non-settable)
   → scratch-fake fallback already designed in.
4. **Param *names* drift across KeyShot versions** — mitigated by the
   existing find_param display-name fuzzy match + the new wire audit.
5. **Performance**: 8-layer graphs × 200-part assemblies — unknown render
   cost. Probe on a real assembly early in Phase 4; budget system caps layer
   count if needed.

---

## 10. Open questions (→ DECISIONS.md)

1. **Probe pack timing** — run P1–P13 as one console session next time
   KeyShot is open, or fold into Phase 1 dev? _Rec: standalone console
   session first; it needs a human watching renders anyway._ #triage:eyes
2. **Spec sidecar files** — write per-material spec JSON next to the scene,
   or console-only? _Rec: console-only until the batch phase, then sidecar._
   #triage:routine
3. **KeyShot version pin** — docs exist for 11.0→2026.1 and the constant set
   is stable, but which build is the real target? Affects nothing designed
   here except probe expectations. _Rec: record the build number in the
   probe-pack output header._ #triage:routine
4. **How bold on displacement** — **Resolved 2026-07-22 (RNK-0064): opt-in
   flag per material, defaulting to True/checked** (overrides this doc's own
   "off by default" rec). No existing "hero quality" gate to hook into —
   build it as a standalone boolean. Still blocked on P4 passing.

---

## Appendix A — source map

- KeyShot 11.0 lux reference (`media.keyshot.com/scripting/doc/11.0/lux.html`)
  — full SHADER_TYPE/PARAMETER_TYPE census, MaterialGraph/ShaderNode/
  ShaderParameter APIs, multi-material methods.
- KeyShot 2024.1 lux reference — cross-check; constant set stable; adds
  REALCLOTH id variant; MultiMaterial class methods.
- KeyShot manual, Material Graph Nodes + Color Composite pages — blend mode
  list, mask modes, node category inventory.
- KeyShot manual, Roughness Parameter — black=0 gloss / white=1 matte
  (independently confirms the render-derived brighter=rougher).
- AA02 ground truth (this repo) — param types from real dumps, the
  bump_height and Composite→bump refusals, opacitymap(14) on Metal, Color
  Gradient stops unsettable, no-label-methods finding.
- MWR-9C4E21 — masking recipes; superseded on "no multi-material API" and
  extended on bump-masking plan-Bs.
