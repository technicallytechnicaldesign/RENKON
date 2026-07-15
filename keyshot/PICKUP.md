# PICKUP -- KeyShot workstream handoff

**Updated:** 2026-07-15. **Everything below is committed + pushed to `origin/main`.**
This is the "read this first when you pick the KeyShot work back up" doc. Keep it
current in place (like the repo's own CLAUDE.md status convention).

---

## TL;DR

Two KeyShot workstreams are mid-build, each driven by a deep Fable design review
and built/reviewed by Opus:

1. **Material generator** (`1_HLP_MAT_GENERATOR`) -- works. `AB01` is a
   spec-refactor **candidate under render-validation**; `AA02` is the stable
   fallback. Vision doc: **MDD-4B7A9F**.
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
2. **AB01 material generator** -- `git pull`, render a **Brass or Chrome** part
   (Scratches + Fractal both on). Confirm: colour comes through, a **glossy metal
   with subtle roughness variation + recessed matte scratch streaks** (NOT flat).
   Console should show `Roughness bus: N source(s) -> mode 'composite'` + a
   `SPEC {...}` line + a wire-audit. If good -> retire AA02, AB01 is canonical
   (RNK-0062). Watch for `[info] scratches->edges: bump-height not mappable`
   (means material edge-masking needs plan B).
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
translucent, anisotropic, metallic-paint, etc.; 12 -> 40+ materials) -- do the
probe pack first. Then Phase 3 finishes, 4 weathering engine, 5 batch "lottery",
6 frontier (displacement / label chip-through / organics).

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
| `1_HLP_MAT_GENERATOR_AB01.py` | **candidate** -- Phase-1 spec-refactor (3 buses, roughness blending). Render-validate then supersede AA02 |
| `1_HLP_MAT_GENERATOR_AA02.py` | stable fallback (kept until AB01 confirmed) |
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
