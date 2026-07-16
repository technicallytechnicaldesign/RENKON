# PICKUP -- KeyShot workstream handoff

**Updated:** 2026-07-16. **Everything below is committed + pushed to `origin/main`
EXCEPT the material generator `AB05` (part-size-aware scaling), which is written +
load-safe on disk but NOT yet committed** -- review the diff, then commit + push
(AB04 stays on disk pending recycle). This is the "read this first when you pick
the KeyShot work back up" doc. Keep it current in place (like the repo's own
CLAUDE.md status convention).

---

## TL;DR

Two KeyShot workstreams are mid-build, each driven by a deep Fable design review
and built/reviewed by Opus:

1. **Material generator** (`1_HLP_MAT_GENERATOR`) -- works. `AB05` is the current
   **candidate under render-validation** -- **PART-SIZE-AWARE TEXTURE SCALING**.
   AB04 and earlier were NOT part-size aware: no bounding-box query anywhere, and
   `Center On` (texture_space) was NEVER set -> KeyShot defaulted to *Center On:
   Model* and every procedural texture mapped to the whole ~6700-unit MODEL, so on
   a ~40 mm part feature sizes were wildly wrong ("textures loading at 6700, part
   is 40 mm"); all texture Scales were hardcoded absolutes; and Spots' own tiling
   Scale was never set at all (`["radius","size","scale"]` matched Radius first ->
   ~6700 default -> giant blobs). AB05 fixes all of it: (1) `resolve_part_size`
   (entered `part_size_mm` dialog field > `measure_part_size` walking scene
   geometry via UNPROBED bbox APIs > `DEFAULT_PART_SIZE_MM = 50`), captured into
   `spec['scale']`; (2) `SCALE_FRACTIONS` -- part-relative tiling Scales (scratch
   0.12/fine 0.02/fractal 0.15/cellular 0.08/spots 0.06 of part size), a 40 mm part
   reproduces roughly the old good values; (3) every tiling builder sets its Scale
   explicitly (incl. the Spots-Scale fix) + `set_center_on_part` (type-2 enum ->
   "Part"); (4) Spots distortion so pits read organic. ALL new APIs/params UNPROBED
   -> getattr/find_param guarded, always builds; load-safe 19/19. `AB04` is the
   superseded prior candidate (four shader FAMILIES added as data
   (per `AB04_FAMILIES_SPEC.md`, DSMI-2F5A-PROCGEN), on AB03's three-bugfix rev:
   (1) schema `extra` -- an optional 6th tuple element on MATERIALS rows carrying
   `family` + params (default `{}` = "opaque", every AB03 row untouched), threaded
   through sample_spec -> `spec['base']['extra']` -> validate_spec (clamped) ->
   build_material with a `meta.family` echo; (2) families -- metal_aniso
   (Aluminum/Steel anisotropic), dielectric glass shipping BOTH clear AND frosted
   on `SHADER_TYPE_DIELECTRIC` (fallbacks GLASS->SOLID_GLASS->Plastic), thinfilm
   (oil-slick + anodised iridescent) on `SHADER_TYPE_THIN_FILM` (fallback Metal);
   (3) `apply_family_params` sets IOR/refraction-roughness/anisotropy+angle/film-
   thickness+IOR defensively + `resolve_shader` per-family fallback chains; (4)
   `FAMILY_ALLOWED_LAYERS` per-family wear-layer gating so clear glass never gets
   grime/pitting (glass + thin film drop spots/cellular/occlusion/colour-gradient).
   ALL new constants + param names UNPROBED -> getattr/find_param guarded, always
   builds. `AB04` is kept on disk pending recycle (its prior candidates AB01-AB03
   were already recycled -- only AA02/AB04/AB05 remain on disk); `AA02` is the
   stable fallback. Vision docs: **MDD-4B7A9F**, **AB04_FAMILIES_SPEC**.
2. **Render/animation scripts** (`2a_BAT_*`, `2b_ANI_*`) -- **Phase 1 shipped**
   (load-safety + reliability). The 3 animation scripts now *load for the first
   time*. Review + roadmap doc: **RAR-6E1F3B**.

Nothing has been render-tested on the real KeyShot build yet this session -- a
test queue is waiting (below). Next build step for either stream is its Phase 2.

---

## !! HARD CONSTRAINTS (never violate) !!

- **KeyShot scripts must be ASCII-only + f-string-free** (embedded Python < 3.6,
  ASCII-sensitive console). Use `"{0}".format()`, `--` not em-dash. A single
  f-string or non-ASCII char stops the whole file loading.
  **Run `python keyshot/scripts/0_VAL_LOAD_SAFETY_AA01.py` before committing any
  script** -- it AST-scans every script and fails on any offender (18/18 pass now).
- **Git flow:** review diff -> commit -> push; `git pull --rebase` before push;
  commit identity is the repo-local noreply; end commit messages with the
  `Co-Authored-By: Claude Opus 4.8` trailer. Prefer `git mv` for renames.
- **REV cadence:** `{PREFIX}_{AREA}_{NAME}_{REV}.py`; step `_REV` (rename +
  `# REV` header + refs) on each meaningful revision (letter=breaking,
  number=routine). Update refs in scripts.html (SCRIPTS + UPDATED map), README,
  SCRIPT_STOCK.
- **Only the operator deletes** workspace paths (recycle via
  `_SYSTEM/scripts/recycle.ps1`); this repo lives under a workspace path.

---

## KeyShot TEST QUEUE (operator -- next time KeyShot is open)

Paste console output back so the design docs can be updated to Rev 2.

1. **Material probe pack** -- run `keyshot/scripts/0_CHK_MATGRAPH_PROBE_AA01.py`
   in the Scripting Console. 13 probes; turns MDD-4B7A9F's assumptions into
   facts (label slot / masked-bump / new node params / blend-mode format / ...).
   Delete the `MATGRAPH_PROBE` material afterwards. -> feeds MDD-4B7A9F Rev 2.
2. **AB05 material generator** -- `git pull`, render a **Brass or Chrome** part
   (Scratches + Fractal both on). **Enter the real Part size in mm in the dialog**
   (e.g. 40) -- or leave 0 to let it auto-measure / default to 50. Confirm: colour
   comes through, a **glossy metal with subtle roughness variation + recessed matte
   scratch streaks** (NOT flat). Console should show a `SPEC {...}` line (with
   `finish`, `meta.placement_seed`, `meta.family`, `base.extra`, and now a
   `scale` block: `part_size_mm` + `source` + `resolved`) + a wire-audit. If
   good -> retire AA02, AB05 is canonical, then recycle AB04 (RNK-0062).
   **AB05 PART-SIZE-AWARE SCALING -- the headline change (all UNPROBED, watch the
   console):**
   - **Center On: Part** -- every tiling texture should now read *Center On: Part*
     in the panel, NOT Model. Watch for `[info] couldn't confirm 'Center On' = Part`
     (the enum int differs on this build -- note which of string/1/0 took) or
     `[info] no 'Center On' parameter` (display name differs). This is the fix for
     "textures loading at 6700, part is 40 mm".
   - **Texture Scale** -- feature sizes should be part-appropriate (roughly 1-5 mm
     on a 40 mm part), NOT the old ~6700 model-scale. **Especially Spots** -- its
     Scale is now set explicitly (a separate `set_display`, not the old
     `["radius","size","scale"]` list that matched Radius first); it should NOT be
     giant blobs. If any Scale still reads ~6700, the "Scale" display name differs
     on that node (watch for `[warn] no parameter matching 'scale'`).
   - **Part size source** -- the console prints `part size {n} mm (entered)` /
     `(measured)` / `part size unknown -- using default 50.0 mm`. If measured, it
     names the bbox method that worked (`via getWorldBounds()` / `getBounds()` /
     `getBoundingBox()`) -- the bbox API is UNPROBED, so if it silently defaults,
     enter a Part size in the dialog and note which methods were absent.
   - **Spots distortion** -- the spot pattern should read organic / irregular, not
     perfectly round (Distortion ~0.4 + part-relative Distortion Scale). Watch for
     `[warn] no parameter matching 'distortion'` / `'distortion scale'`.
   - The build summary now prints a `Scale: part {n} mm ({source}) -> scratches ...`
     line -- eyeball the per-node mm values look sane for the part.
   **AB04 FAMILIES -- render one of each and watch the console** (EVERY shader
   constant + family param name below is UNPROBED; all degrade non-fatally to an
   opaque metal/plastic -- note which fell back):
   - **Glass (clear) vs Glass (frosted):** must visibly differ -- clear = smooth/
     see-through, frosted = matte/translucent. Watch for `[warn] SHADER_TYPE_DIELECTRIC
     unavailable ... using <fallback>` (falls to GLASS -> SOLID_GLASS -> Plastic)
     and `[warn] no parameter matching 'index of refraction'` / `'refraction
     roughness'`. Confirm **NO grime/pitting** on either -- the gate should log
     `[info] Spots / pitting skipped -- not applicable to dielectric` (and cellular/
     occlusion/colour-gradient) when those were ticked.
   - **Thin Film (oil slick) / Anodised (iridescent):** must read **iridescent**
     (oil-slick / anodised rainbow). Watch for `[warn] SHADER_TYPE_THIN_FILM
     unavailable ... using SHADER_TYPE_METAL instead` and `[warn] no parameter
     matching 'thickness'` / `'film thickness'` / `'index of refraction'`.
   - **Aluminum/Steel (anisotropic):** directional brushed highlight. Watch for
     `[warn] no parameter matching 'anisotropy'` / `'anisotropy angle'`. The brush
     angle is a STABLE per-build value from the placement RNG (recorded as
     `extra.aniso_angle_used` in the SPEC) -- the Scratches direction_field is a
     type-2 enum, deliberately NOT read.
   - Any family that fell all the way back to Plastic/Metal still produces a
     working (if wrong-looking) material -- report which constants/params missed so
     the display names can be locked for a follow-up rev.
   **AB03-inherited CONFIRM-AT-RENDER checks** (all degrade non-fatally, watch the
   console):
   - **FIX 1 (roughness composite):** expect `Roughness bus: N source(s) ->
     mode 'composite'` (NOT `single-fallback`) whenever >= 2 roughness sources are
     active (Scratches + Fractal). If it still says `single-fallback`, capture the
     Color Composite param dump -- the Source/Background display names differ.
   - **FIX 2 (placement):** the AB02 `[info] placement: offset/rotation not
     settable` spam should be **GONE**. Any remaining `[info] placement: <param>
     not settable` names a scalar whose display name differs on this build (e.g.
     noise_scale/level_scale/shape_1/bias_x) -- note which so we can lock the name.
     The type-12 Texture Transform matrix is intentionally left unset (no probe).
   - **FIX 3 (auto-apply, LEAST CERTAIN):** watch for the new
     `candidate kinds: {...}` histogram printed BEFORE applying. Confirm it shows
     geometry kinds (not only kind=6 cameras) and that `Applied '...' to N node(s)`
     has **N > 0**. If it's still 0 with all kind=6, paste the histogram -- the
     geometry isn't under `getChildren()` where we expect.
   - Also still: routing fix means **Directional Noise and Noise are set
     independently** -- eyeball that Worn/Heavy reads more chaotic than Brushed;
     watch for `[info] scratches->edges: bump-height not mappable` (edge-masking
     needs plan B).
3. **The 3 animation scripts now LOAD** -- run `2b_ANI_HERO_REVEAL`,
   `2b_ANI_CUTAWAY_REVEAL`, `2b_ANI_ASSEMBLY_PROCEDURAL`. EXPECTED-but-not-yet-fixed
   (don't be alarmed): **assembly parts EXPLODE outward instead of settling**
   (motion-inverted, Phase 3 fix pending) and **cutaway doesn't actually cut**
   (clip-plane API doesn't exist; Phase 4 redesign pending).
4. **Confirm the getStudio fix** -- run `2a_BAT_STD_VIEW` on a folder; it should
   now render images even on a KeyShot 11 build (it silently rendered ZERO before).

---

## BUILD QUEUE (next sessions -- Opus, following the Fable plans)

**Materials** (MDD-4B7A9F sec 9): Phase 2 = families + palettes (glass,
translucent, anisotropic, metallic-paint, etc.; 12 -> 40+ materials) -- **first
tranche landed in AB04** (anisotropic metal, dielectric glass clear+frosted, thin
film, via the `extra` schema + family gating; palette 12 -> 18 rows). Still to do:
more palette breadth + the probe pack to lock the guessed family shader/param
names. Then Phase 3 finishes, 4 weathering engine, 5 batch "lottery", 6 frontier
(displacement / label chip-through / organics).

**Render/animation** (RAR-6E1F3B sec 6): **Phase 2 = L3 shared module
`ks_shared.py` + RenderSpec preset system (draft/review/hero/comp/print/turntable;
denoise, GPU engine, EXR+passes) + Manifest v2.** THIS is where the 5 scripts get
their `AB01` letter-bump. Then Phase 3 = assembly motion-inverted fix +
getTransform drift check + turntable presets (needs probe RP4); Phase 4 = cutaway
redesign (`SHADER_TYPE_CUTAWAY` cutter-solid sweep); Phase 5 = pro output; Phase 6
= RUN_ALL launcher + watch.py (RPA-7B2E4D / RPR-3F9C1A).

Both have a probe pack (MDD sec 8 / RAR sec 6) -- run at KeyShot before the
probe-dependent phases; design-for is fine, depend-on is not.

---

## STATE BY FILE (keyshot/scripts/)

| File | State |
|---|---|
| `1_HLP_MAT_GENERATOR_AB05.py` | **candidate** (NOT yet committed) -- part-size-aware texture scaling on AB04: `resolve_part_size` (entered `part_size_mm` > measured via UNPROBED bbox APIs > default 50), `SCALE_FRACTIONS` (part-relative tiling Scales replacing hardcoded absolutes), `set_center_on_part` (Center On: Part enum, was defaulting to Model -> textures mapped to the whole ~6700-unit model), the Spots-Scale-never-set fix (giant blobs), and Spots distortion; `spec['scale']` captured for reproducibility. All new APIs/params UNPROBED, guarded, always builds; load-safe 19/19. Render-validate then supersede AB04 + AA02 |
| `1_HLP_MAT_GENERATOR_AB04.py` | superseded prior candidate -- four new shader families (anisotropic metal, dielectric glass clear+frosted, thin film) via a per-row `extra` dict + family-aware base-param pass + per-family wear-layer gating (per `AB04_FAMILIES_SPEC.md`). All new constants/params UNPROBED, guarded, always builds. Kept on disk until AB05 confirmed, then recycle |
| `1_HLP_MAT_GENERATOR_AA02.py` | stable fallback (kept until AB05 confirmed) |
| `0_CHK_MATGRAPH_PROBE_AA01.py` | material probe pack -- run it |
| `0_VAL_LOAD_SAFETY_AA01.py` | dev/CI guard (AST + ASCII); run before commits |
| `2a_BAT_STD_VIEW_AA01.py`, `2a_BAT_TURNTABLE_AA01.py` | Phase-1 fixed (reliable, load-safe) |
| `2b_ANI_HERO_REVEAL_AA01.py` | Phase-1 fixed -- LOADS now; camera math intact |
| `2b_ANI_CUTAWAY_REVEAL_AA01.py` | Phase-1 fixed -- LOADS now; cutaway is a no-op until Phase 4 |
| `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py` | Phase-1 fixed -- LOADS now; MOTION STILL INVERTED until Phase 3 |
| `1_HLP_MAT_LOOKUP/PREFLIGHT`, `0_VAL_*`, `2a`/`2b` others, `3_PRC_*`, `4_CHK_AUDIT` | stable, load-safe |

---

## DESIGN DOCS (read to pick up cold -- `keyshot/scripts/research/` unless noted)

- **MDD-4B7A9F** `MATERIAL_DIVERSITY_DESIGN.md` -- material generator vision:
  ~90 scriptable nodes, MaterialSpec recipe, 3 buses, roughness blending,
  bump-masking plan-Bs, 6-phase roadmap, 13-probe pack.
- **RAR-6E1F3B** `RENDER_ANIM_REVIEW.md` -- render/anim review: the 4 real bugs,
  RenderSpec presets, L3 module surface, dependability inventory, 6-phase
  roadmap, 13-probe pack, full API confidence census (Appendix A).
- **MWR-9C4E21** `MASKED_WEAR_RESEARCH.md` -- masking (Rev 2: mask -> bump-height,
  not Color Composite).
- **RPA-7B2E4D** `RENDER_PIPELINE_ARCHITECTURE.md` + **RPR-3F9C1A**
  `RENDER_PIPELINE_RESEARCH.md` -- AUTO/PRO/EXPERT launcher + 5-tier scale.
- `keyshot/RESEARCH_CREO_KEYSHOT.md` -- confirmed `lux` API facts.
- `keyshot/SCRIPT_STOCK.md` -- live inventory + backlog.

---

## KEY GROUND TRUTH (confirmed this session -- don't re-derive)

- KeyShot embedded Python < 3.6; ASCII-only console. (-> the load-safety law.)
- **Roughness texture: brighter = ROUGHER.** **Bump: brighter = raised, darker /
  negative bump-height = recessed groove.**
- Base colour is set **by name** (Metal `Color` / Plastic `Diffuse`), a
  PARAMETER_TYPE **14** input -- NOT `PT_COLOR` (13). Filter-by-type missed it.
- **Color Composite** (blend modes Lighten/Darken/Sum) is accepted into
  **roughness/colour** but **refused by bump** ("Could not create requested edge").
- **`bump_height` was NOT mappable** on the operator's build -> material
  edge-masking silently no-ops (degrades to unmasked). Plan-Bs in MDD sec 4.3.
- **`getStudio()` is 2024.1+ ONLY** (absent in 11.0) -> always `setActiveStudio`
  FIRST, getattr-guard `getStudio`.
- **No label API method**, BUT the root has a **SHADERLABEL (type 65538)** slot
  and Metal's `opacitymap` IS mappable -> possible scripted chip-through (probe P1).
- **No clip-plane API in any version** -> cutaway = **`SHADER_TYPE_CUTAWAY`**
  cutter-material on cutter geometry.
- **Confirmed render surface:** `setDenoise`, `setRenderEngine` (PRODUCT/INTERIOR
  +GPU), 12 render passes, `RENDER_OUTPUT_PNG/EXR/TIFF*/PSD*`, `renderAnimation`,
  image styles. `renderImage` return value is undocumented -> verify file on disk.
- **Multi-material IS scriptable** (`setMultiMaterial`); `Matrix().translate()`,
  `getTransform` readback, `hide()/show()` are documented (assembly Phase 3).
- Build version itself is unpinned -- record it in the first probe-pack output.

---

## WORKSPACE (PROJECTS/RENKON/, outside this git repo)

- Open decisions (`DECISIONS.md`): RNK-0064 displacement boldness (rec: opt-in);
  RNK-0013/0015 field-guide items (parked/both).
- Tasks (`TODO.md`): the KeyShot test queue + Phase-2 builds are logged;
  non-KeyShot items (overlay toolkit, flagship calculators, render field guide)
  also open.
- Render study renders live in `PROJECTS/RENKON/02_WORK/procgen_material_study/`.
- After editing any workspace TODO/project.json, run
  `_SYSTEM/scripts/refresh.ps1`.
