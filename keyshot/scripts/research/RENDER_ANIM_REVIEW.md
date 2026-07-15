# Render & Animation Scripts — Deep Design Review

**UID:** RAR-6E1F3B
**Rev:** 1
**Date:** 2026-07-15
**Type:** design review (no code changed — findings + design only)
**Scope:** the five L2 render/animation stage scripts —
`2a_BAT_STD_VIEW_AA01.py`, `2a_BAT_TURNTABLE_AA01.py`,
`2b_ANI_HERO_REVEAL_AA01.py`, `2b_ANI_CUTAWAY_REVEAL_AA01.py`,
`2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py`
**Grounded against:** RPA-7B2E4D Rev 3 (AUTO/PRO/EXPERT architecture),
RPR-3F9C1A Rev 2 (launcher/tier research), `RESEARCH_CREO_KEYSHOT.md`,
MDD-4B7A9F (MaterialSpec + probe-pack discipline), the material-generator
load-safety lessons, and a fresh 2026-07-15 pass over KeyShot's own
scripting references (11.0, 2024.1, and the 2026.1 headless doc at
media.keyshot.com/scripting — see Appendix A for the per-call census).
**Audience:** the agent implementing the Phase-1 fixes and the L3 shared
module; TJ for the decisions flagged along the way.

---

## 0. Headline findings (read this even if you skim the rest)

1. **The three `2b_ANI_*` scripts currently do not load in KeyShot at all.**
   KeyShot's embedded Python predates f-strings (< 3.6) and its console is
   ASCII-sensitive; a single f-string or non-ASCII character stops the whole
   file from loading. Verified by grep on 2026-07-15:
   `2b_ANI_HERO_REVEAL` (66 f-strings, 34 non-ASCII lines),
   `2b_ANI_CUTAWAY_REVEAL` (58 / 34), `2b_ANI_ASSEMBLY_PROCEDURAL` (66 / 51).
   Both `2a_BAT_*` scripts are clean (0 / 0). This is the identical failure
   that blocked `1_HLP_MAT_GENERATOR` until its 2026-07-15 load-safety pass —
   the fix pattern (`.format()` + ASCII-only) is already proven in this repo.
   Everything else in this review is moot for the 2b set until this lands.

2. **`lux.getStudio(name)` is a version trap — and every one of the five
   scripts calls it *before* `setActiveStudio()`.** A fresh pass over the
   actual references shows `getStudio()` (returning a Studio object with
   `getCamera()` etc.) is documented in **2024.1+ but NOT in the 11.0
   reference** this pipeline has treated as its source of truth. The scripts'
   headers claim it "confirmed"; on a KeyShot 11 build it raises. Because the
   call sits first inside the activation `try`, the failure modes differ by
   script and two are severe:
   - `2a_BAT_STD_VIEW`: every Studio logs `FAILED (studio activation)` and is
     skipped; since `studios` is non-empty the raw-camera fallback never
     triggers → **a whole batch run renders zero images** while looking like
     it merely had per-studio hiccups.
   - `2b_*` `activate_camera_or_studio()`: every Studio target returns None →
     all Studio shots skipped.
   - `2a_BAT_TURNTABLE`: degrades to raw-camera lighting (wrong environment,
     silent visually).
   The fix is trivial and version-safe: call `setActiveStudio(name)` (in every
   doc version) **first**, then getattr-guard `getStudio` purely to learn the
   camera name, falling back to `lux.getCamera()` after activation.

3. **The cutaway script's entire clip-plane probe list is aimed at an API
   that appears to exist in no version.** Neither 11.0 nor 2024.1 nor the
   2026.1 headless reference documents any clipping/section-plane function.
   What DOES exist: **`SHADER_TYPE_CUTAWAY` (`'lux_cutaway'`)** — cutaway in
   KeyShot is a *material* applied to cutter geometry, not a scene-level
   plane object. The right redesign (fully buildable with confirmed calls +
   the material-generator's existing graph machinery): a cutter solid in the
   master template, given a cutaway material, swept via
   `applyTransform(relative)`. Until then the script degrades to rendering
   N expensive, identical, un-clipped sequences — graceful, but useless.

4. **The assembly script's motion is inverted — parts explode instead of
   settling.** `compute_translation_at(t)` returns the intended *current
   displacement* (full at t=0, zero at t=1), but the frame loop only ever
   applies deltas from `prev_t = 0` — **the initial displacement is never
   applied**. Net effect: parts start assembled (authored position), drift by
   *minus* the scatter vector across the shot, then snap back after the last
   rendered frame via `apply_final_correction()`. All three translation modes
   (scatter_settle, staggered_build, spiral_converge) render backwards. One
   missing step fixes it: apply `displacement(t=0)` to every part before the
   frame loop (and count it in the running totals so the telescoping still
   zeroes out).

5. **Several "experimental" guesses can be promoted, and one "confirmed"
   readback gap closes.** `luxmath.Matrix().translate(Vector)` is documented
   (KeyShot 11 manual, "Transforming scene nodes" + luxmath reference) — the
   assembly script's single most load-bearing "pure guess" is real.
   `env.setRotation(deg)` is documented in 2024.1 ("float in [0, 360[" —
   note the range: the scripts' unwrapped `start + sweep` can exceed it).
   `SceneNode.getTransform(world=)` is confirmed get-only — so the assembly
   script's "trusted arithmetic, no readback" caveat is out of date: it CAN
   verify net-zero drift by comparing transforms before/after.
   `node.hide()/show()` are confirmed — a 100%-confirmed alternative for
   ghost_fade (staggered *appear*) whose opacity probe will likely never
   resolve (no opacity setter in any reference checked).

6. **The professional render-settings surface is far richer than the scripts
   use, and it's confirmed.** `RenderOptions` documents sample/time/max-sample
   modes, `setDenoise(enable)`, `setRenderEngine()` with
   `RENDER_ENGINE_PRODUCT/INTERIOR/PRODUCT_GPU/INTERIOR_GPU`, twelve render
   passes, `setOutputAlphaChannel`, `setRegion`, `setThreads`, and
   `getDict()` for baking settings into the manifest. `renderImage(...,
   format=)` takes `RENDER_OUTPUT_JPEG/PNG/EXR/TIFF8/TIFF32/PSD8/16/32`.
   `renderAnimation()` and `renderFrames()` exist for GUI-authored timelines.
   Today the scripts expose width/height and one samples constant. A
   RenderSpec (MaterialSpec's sibling) turns all of this into presets.

7. **Two latent dialog crashes and one headless hang.** The material
   generator's hard-won lesson — `getInputDialog` **rejects an empty-string
   default** — applies to the 2a scripts' `("outFolder", DIALOG_FOLDER, …,
   "")` rows, and plausibly to the cutaway script's `DIALOG_DOUBLE` rows with
   `None` defaults; both risk the dialog failing to open at all in PRO mode
   (probe RP10). And the 2a scripts' headless path uses `input()` loops that
   `continue` on `EOFError` — with a closed stdin (the normal
   `keyshot_headless -script` case) that is an **infinite spin**, not a
   prompt. The 2b scripts' `DEFAULT_OPTIONS` headless pattern is the correct
   one; the 2a scripts should adopt it (and, per RPA-7B2E4D §3, read a
   `job.json` in that branch).

---

## 1. Per-script audit

### 1.1 `2a_BAT_STD_VIEW_AA01.py` — Studios-first multi-view batch stills

**What it does well.** Studios-first with an explicit, well-reasoned
raw-camera fallback; per-row manifest with a FAILED/SKIPPED vocabulary;
`centerAndFit()` + `PADDING_FACTOR` scale-invariant framing; extension
hygiene (`cleanExt`/`stripExt`); the `renderOpts` vs dialog-`opts` shadowing
fix is documented in a comment. It is the closest of the five to the L3
extraction shape.

**Weaknesses, concrete:**

- **W1 (severe): `lux.getStudio(studioName)` called before
  `setActiveStudio`** (see headline #2). On a build without `getStudio`, the
  per-studio `try` catches the AttributeError, logs FAILED, `continue`s — the
  run completes "successfully" with zero renders and no raw-camera fallback
  (fallback only fires when `studios` is empty). This is the script's one
  catastrophic silent-ish no-op.
- **W2 (severe): no `try` around `lux.importFile(path)`.** One corrupt STEP
  file kills the whole batch mid-run with no manifest row and no recovery.
  Partial-batch death is exactly what AUTO can't tolerate.
- **W3: `renderImage` return value is undocumented** in every reference
  checked, yet `success = lux.renderImage(...)` drives the manifest status.
  Treat it as advisory; the real check is the file on disk (§3.2). Worse, in
  queue mode the file *cannot* exist yet — `status="queued"` rows are never
  reconciled after `processQueue()` runs, so the manifest never records
  whether anything actually rendered.
- **W4: default option combination `queue=True, process=False`** means the
  default run produces zero pixels until a human opens the Render Queue —
  defensible for PRO, wrong as a headless default (AUTO must force
  `process=True` or immediate render).
- **W5: headless `input()` path can hang forever** (headline #7). Also the
  headless branch prompts interactively at all — AUTO wants
  `DEFAULT_OPTIONS`/`job.json`, not stdin.
- **W6: no name sanitisation.** `outPath = "{}_{}.{}".format(baseName,
  studioName, oext)` — a Studio named `Front / Soft` produces an invalid
  path. The 2b scripts already carry `sanitize_name()`; the 2a scripts don't.
- **W7: found-check regex vs loop mismatch.** The "any input files?" check
  uses `re.compile(".*{}".format(iext))` (substring semantics — `bipartite.stp`
  matches `bip`), the actual loop uses `endswith`. Cosmetic today, but it can
  claim files exist and then process none.
- **W8: unordered batch.** `os.listdir()` order is arbitrary — sort for
  deterministic run order and resumability.
- **W9: flat output.** Everything lands in one folder; RPA §6 wants
  `<PartName>/stills/`. No skip-already-rendered, so a re-run re-renders
  everything.
- **W10: manifest schema is thin** — no width/height/samples/format/engine
  columns, and it differs from the 2b scripts' schema (unify in L3).
- **W11: `PADDING_FACTOR` hardcoded**, not exposed, not tier-aware
  (RPR-3F9C1A §5b wants padding per scale tier).
- **W12: possible dialog-open crash** from `""` defaults (headline #7,
  probe RP10).

**Highest-value fixes:** W1 + W2 + W3 (verify-on-disk) + W5. Those four turn
"can silently produce nothing / die mid-batch / hang" into "boringly
reliable"; everything else is enhancement.

### 1.2 `2a_BAT_TURNTABLE_AA01.py` — Studios-first 360 turntable batch

**What it does well.** The deliberate *no-queue* design with the reasoning
written down (frames must exist before `encodeVideo`) is exactly right; the
Studio-by-camera-reference matching (`getStudio(s).getCamera() ==
baseCameraName`) is a genuinely thoughtful touch; azimuth wrap into
[-180, 180] matches the documented `setSphericalCamera` domain; per-part
frame folders + `keepFrames=False` cleanup; the loop math avoids the
duplicate-last-frame seam (frame N is 360-step, not 360).

**Weaknesses, concrete:**

- **W1: `getStudio` ordering** — here the failure degrades to raw-camera
  lighting rather than nothing, which is *worse* in a way: output looks
  plausible but is lit wrong, silently (only a console warn). Same fix as
  1.1-W1.
- **W2: `lux.encodeVideo(...)` is not wrapped** — an encode failure kills the
  remaining batch AND writes no manifest row for the failed part. (The 2b
  scripts all wrap encode; this one predates the pattern.)
- **W3: no per-frame verification.** 36 unverified `renderImage` calls feed
  an encode; one licence popup or GPU hiccup mid-spin means encoding a
  gap-toothed sequence. Verify frame files exist before `encodeVideo`
  (§3.2) — this precheck is cheap and catches the whole class.
- **W4: everything about quality is a hardcoded constant** — `FRAME_COUNT=36`
  (10-degree steps at 24 fps = a choppy 1.5 s clip), `FPS=24`,
  `TURNTABLE_SAMPLES=16`, `640x640`. Fine as a draft preset; wrong as the
  *only* mode. Presets: DRAFT (36f/640/16s/denoise-on) and FINAL
  (120f @ 30 fps = 4 s, 1280+, 64+ samples) — see §2.
- **W5: camera-orbit is the only mode.** Orbiting the camera makes highlights
  and reflections travel across the part; the classic product-turntable
  alternative — rotate the *model*, hold camera+lighting — is now buildable
  (confirmed `applyTransform` + documented `Matrix` rotate, pivot probe RP4)
  and reads more "studio". Offer both.
- **W6: same headless-`input()` hang and `""`-default dialog risk as 1.1.**
- **W7: no import `try`, unordered listing, thin manifest — same as 1.1.**
- **W8: interpolation is linear-only** (constant angular velocity — correct
  for a loop) but there's no option for a non-looping 180-sweep with ease,
  which marketing clips often want. Low priority.

**Highest-value fixes:** W2 + W3 (never encode unverified frames), W1, then
the DRAFT/FINAL preset split (W4).

### 1.3 `2b_ANI_HERO_REVEAL_AA01.py` — hero-reveal camera move

**What it does well.** The best-documented script in the repo — the header's
confirmed-vs-experimental census, the removed-orbit post-mortem (Rodrigues
degeneracy), and the QUEUEING rationale are model documentation. The
monotonic zoom + optional crane with the zero-at-t=1 discipline is sound
camera math; `norm_item()` dialog normalisation, `sanitize_name()`,
per-target env capture/restore, degrade-once channel flags, and the
model-set import workflow (with the "won't create the Model Set" reasoning)
are all the right idioms. `resolve_animation_frame_count()`'s defensive
parse happens to match the now-confirmed `(duration_seconds, frame_count)`
shape.

**Weaknesses, concrete:**

- **W1 (blocker): does not load** — 66 f-strings, 34 non-ASCII lines
  (headline #1).
- **W2: `getStudio` ordering** in `activate_camera_or_studio()` — on a
  KS11 build every Studio target is skipped (headline #2). Additionally
  `resolve_camera_list("ALL")`'s `covered` computation fails the same way →
  `extras` becomes *every* camera → Studio+camera double-shooting on newer
  builds if a camera is also in a Studio under a different name; on KS11
  builds, ALL resolves to studios (which then all fail) + all cameras (raw
  lighting). The 'ALL' expansion needs the same version-safe treatment.
- **W3: env rotation can exceed the documented [0, 360[ domain.**
  `env.setRotation(start_rotation + sweep)` — if the build enforces the
  range, the first frame past 360 throws, the degrade-once flag disables
  env rotation *mid-shot*, and the clip visibly changes character. Wrap
  `% 360.0` always.
- **W4: the experimental product turntable rotates about the world origin.**
  `luxmath.Matrix().makeIdentity().rotate(delta, axis)` builds a rotation
  whose axis passes through the origin; a part not centred at the origin
  *orbits* rather than spins. Needs the conjugated form
  `T(center) * R * T(-center)` (translate is now documented, headline #5) —
  and pivot behaviour under `absolute=False` needs probe RP4 first.
- **W5: preview mode = `setMaxTimeRendering(2)`** — time-based sampling is
  nondeterministic (noise level varies with machine load) and 2 s/frame is
  invisible magic. Prefer `setMaxSamplesRendering`/`setAdvancedRendering`
  with a preset sample count + `setDenoise(True)` for previews — same speed,
  deterministic output.
- **W6: queue mode is a disk-space trap.** `setAddToQueue` is documented to
  save *a copy of the scene to disk for every queued job* — 90 frames x N
  targets = 90N scene copies. Per-frame queueing is a misuse of the queue at
  animation scale; either warn loudly, or restrict queueing to stills and
  make animations always render immediately.
- **W7: frame folders are reused across runs** — a shorter re-run leaves
  stale frames from a longer previous run in the folder. `encodeVideo`'s
  first/last window masks it today, but any pattern change or `keep_frames`
  inspection hits confusion. Clean the folder (recycle, per workspace rules,
  or overwrite-check) or use a per-run subfolder.
- **W8: per-frame `renderImage` failures only warn** — a shot can "complete"
  with 40 of 90 frames on disk and still report `ok=True` and encode. Frame
  verification before encode (§3.2) closes this.
- **W9: `output_folder` default `"."`** — frames land in KeyShot's CWD
  (unpredictable) while the manifest path is abspath'd from the same value;
  use one abspath everywhere.
- **W10: no `lux.pause()/unpause()` bracketing.** Every per-frame mutation
  (camera, env, animation frame) triggers realtime re-render work between
  `renderImage` calls. `pause()`/`unpause()` around the mutation block is a
  free speed win (documented: "Pauses renderer"; verify behaviour, RP11).
- **W11: when a GUI-authored model-set animation is the *only* motion**
  (no camera move wanted), stepping frames manually + per-frame renderImage
  reinvents `lux.renderAnimation()` (documented, takes `videoName`, fps,
  format) — offer a direct renderAnimation path for that case.

**Highest-value fixes:** W1 (load), W2, W3, frame verification (W8); then
W5/W6 as part of the RenderSpec work.

### 1.4 `2b_ANI_CUTAWAY_REVEAL_AA01.py` — clip-plane cutaway sweep

**What it does well.** The most honest script in the pipeline — the header
says plainly that every clipping call is a guess, the probe machinery
(`resolve_clipping_plane()`, per-frame candidate memoisation in
`apply_clip_plane()`) is genuinely good defensive engineering, and the
bbox-derived sweep range with margin + manual overrides + loud fallback is
the right shape. The degrade path works exactly as designed.

**Weaknesses, concrete:**

- **W1 (blocker): does not load** — 58 f-strings, 34 non-ASCII lines.
- **W2 (design-level): the probed API almost certainly doesn't exist.**
  No clipping/section function appears in 11.0, 2024.1, or 2026.1-headless
  references (headline #3). The script will always degrade to "no cutaway" —
  i.e. its steady state is rendering N identical un-clipped sequences per
  run, at full animation cost. Graceful degradation of a feature that never
  engages is a very expensive no-op.
  **Redesign (recommended):** KeyShot's actual cutaway mechanism is the
  **cutaway material** (`SHADER_TYPE_CUTAWAY = 'lux_cutaway'`, present in the
  2024.1 constants) applied to cutter *geometry*. Scriptable plan:
  1. Master template (`00_MASTER/master_template.bip`, per RPA §6) carries a
     cutter solid named e.g. `CUTTER_BOX`, larger than any part tier, with a
     cutaway material authored once in the GUI (or built via the material
     generator's confirmed graph machinery + `node.setMaterial()`).
  2. The script finds `CUTTER_BOX` by name (`root.find()`, confirmed),
     verifies its material, parks it outside the bbox, and sweeps it through
     the assembly with relative `applyTransform` translation deltas — the
     exact discipline the assembly script already implements.
  3. Degrade path stays: no cutter node found → warn loudly, skip the sweep,
     and (new) **skip the render too** unless the operator opts into
     "render anyway" — don't burn hours on frames that can't differ.
  Everything in that plan is confirmed except cutaway-material behaviour
  when its cutter moves per-frame → probe RP6.
- **W3: `DIALOG_DOUBLE` rows with `None` defaults** (`clip_start_override`,
  `clip_end_override`) — likely the same `getInputDialog` default-rejection
  crash class the generator hit (probe RP10). If it crashes, the dialog
  never opens and PRO mode is dead on arrival. Fix pattern: make overrides
  `DIALOG_TEXT` with `""`→None parsing, or give numeric sentinels.
- **W4: the untuned -100..100 fallback range should not silently render.**
  If neither bbox nor overrides resolve, sweeping an arbitrary range and
  rendering the full sequence is cost without value — prefer abort-with-row
  (`SKIPPED (no sweep range)`), operator can override to force.
- **W5:** shares 1.3's W3 (env rotation domain), W7 (stale frames), W8
  (unverified frames), W9 (`"."` output), W10 (no pause bracketing), W6
  (queue scene-copy cost) — all inherited from the same copied blocks, which
  is the L3 argument in miniature: fix once, fix everywhere (§5).

**Highest-value fixes:** W1, then the W2 redesign decision (it changes what
Phase-4 builds), W3 verification.

### 1.5 `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py` — procedural assembly reveal

**What it does well.** The most ambitious script, and the TRANSFORM
MECHANICS header is the best piece of reasoning in the repo — displacement
functions with zero-at-t=1, relative-delta composition with telescoping,
single-axis rotation to dodge non-commutativity, per-part degrade flags, a
final corrective delta, seeded reproducibility, per-part extent scaling with
a crude-but-honest fallback, and a written-down extension point for
sub-assembly grouping. `build_part_states()` precomputing everything before
the frame loop is the right structure.

**Weaknesses, concrete:**

- **W1 (blocker): does not load** — 66 f-strings, 51 non-ASCII lines.
- **W2 (critical logic bug): the initial displacement is never applied**
  (headline #4). The delta loop telescopes correctly *only if the part
  already sits at `displacement(t=0)`* when the loop starts. It doesn't —
  nothing ever moves parts to their scattered/off-frame start. Consequence,
  mode by mode: scatter_settle renders an outward *explosion* along the
  negated scatter vectors; staggered_build renders parts leaving one at a
  time; spiral_converge spirals outward. The end-of-shot correction then
  snaps everything home *after* the last rendered frame, so the bug also
  hides itself from any post-run scene inspection. Fix: before the frame
  loop (per target), apply `displacement(0)` (+ initial rotation) as one
  delta, recorded in the running totals; the final correction then
  naturally returns ~zero.
- **W3: rotation deltas likely orbit the world origin** — same pivot issue
  as 1.3-W4: `Matrix().rotate(deg, axis)` has its axis through the origin.
  For scatter rotation the intent is spin-about-own-center; needs the
  `T(center) * R * T(-center)` conjugation (translate now documented) and
  probe RP4 to pin down `applyTransform(…, absolute=False)` pivot semantics.
- **W4: the "no readback" premise is stale.** `SceneNode.getTransform(world=)`
  is confirmed (this repo's own RESEARCH_CREO_KEYSHOT.md says so). Capture
  each part's transform in `build_part_states()`, compare after
  `apply_final_correction()`, and warn (or hard-correct via one more delta)
  if drift exceeds epsilon. Turns "trusted arithmetic" into a verified wire —
  the confirm-the-wire discipline applied to motion.
- **W5: ghost_fade's opacity probe will likely never resolve.** No opacity/
  transparency setter on SceneNode or material appears in any reference
  checked (matching this repo's earlier finding). Two better routes:
  (a) **staggered appear via `hide()`/`show()`** — 100% confirmed, zero
  probe risk: parts pop in per staggered window (reads as stop-motion,
  honest and useful); (b) material-graph route — duplicate the part's
  material, drive a dielectric/advanced shader's transparency-ish param via
  the generator's `find_param`/`set_display` machinery (probe RP9). Ship (a)
  now, probe (b) later.
- **W6: `.translate()` guess is now documented** — promote from "pure guess"
  to confirmed-pending-smoke-test (call shape `translate(Vector)`, RP5), and
  update the header so future sessions stop re-deriving it.
- **W7: per-frame cost.** N parts x F frames of matrix builds + transforms +
  full realtime updates between renders — bracket the whole mutation block
  in `pause()`/`unpause()` (RP11), and consider only touching parts whose
  `t` changed (staggered_build: most parts are static most frames — skip
  zero deltas early; the code already early-returns on tiny deltas, good).
- **W8: `random_seed` default 0 = nondeterministic.** For a pipeline that
  values reproducibility (manifests, specs), the default should be a fixed
  seed with 0 as the explicit opt-*out*, not opt-in. Cheap flip, aligns with
  MDD's seeded-spec philosophy.
- **W9:** inherits the shared 2b weaknesses: env-rotation domain, stale
  frame folders, unverified frames before encode, `"."` output folder,
  queue scene-copy cost, `DIALOG_FILE`/`None` default risk.

**Highest-value fixes:** W1, W2 (the shot is wrong end-to-end without it),
W3+W4 together (pivot + readback verification), W5(a).

---

## 2. Customisability — an options model that doesn't drown the operator

### 2.1 The principle: presets first, spec underneath, doors decide who edits what

RPA-7B2E4D already gives the shape: AUTO gets *zero* decisions, PRO gets a
dialog, EXPERT gets raw access. Customisability lands correctly when each
knob is assigned to exactly one layer:

| Layer | Who edits | What lives here |
|---|---|---|
| **RenderSpec presets** (code, L3) | maintainer | quality/format/resolution bundles: `draft`, `review`, `hero`, `comp`, `turntable_draft`, `turntable_final`, `social_square`, `social_vertical` |
| **job.json** (AUTO sidecar / folder default) | pipeline config | preset name per hot-folder mode, output root, process-queue policy |
| **PRO dialog, tier 1** | operator, every run | preset picker, targets (Studios/cameras), output folder, part filter — the five-field dialog |
| **PRO dialog, tier 2 ("advanced")** | operator, rare | camera-move params, env/brightness options, per-run overrides of preset fields |
| **Per-part sidecar** `<PartName>.render.json` | operator, exceptional | overrides merged over the preset for one part (e.g. "this one at 4K") |
| **EXPERT** | operator, deliberate | hand-edit the merged spec JSON, guards off |

Merge order (one function in L3): `PRESET <- job.json <- dialog <-
per-part sidecar <- expert overrides`. Every run *writes the merged spec
back out* next to its outputs (§4.5) — customisation and reproducibility are
the same feature.

### 2.2 RenderSpec — the data model (MaterialSpec's sibling, MDD-4B7A9F §3.2)

Plain dict, JSON-serialisable, Python-3.4-safe, no dataclasses:

```python
RENDER_SPEC = {
    "meta":   {"preset": "review", "spec_rev": 1, "script": "2a_BAT_STD_VIEW",
               "script_rev": "AB01", "seed": 42117},
    "image":  {"width": 1920, "height": 1080,
               "format": "PNG",          # -> lux.RENDER_OUTPUT_* via L() guard
               "alpha": False},          # setOutputAlphaChannel
    "quality":{"mode": "samples",        # samples | max_samples | time
               "samples": 64,
               "max_time_s": 0,          # 0 = no time cap; both set = belt+braces
               "denoise": True,          # setDenoise  [CONFIRMED, version-gated]
               "engine": None,           # None=leave scene | product|interior|*_gpu
               "threads": 0},
    "passes": {"enabled": False,         # comp preset flips this
               "list": ["depth", "normals", "clown", "ao"],
               "render_layers": False},  # setOutputRenderLayers
    "framing":{"padding_factor": 1.15,   # tier-overridable (RPR 5b)
               "tier_override": None},
    "anim":   {"frames": 90, "fps": 24, "hold_start": 4, "hold_end": 20,
               "easing": "cosine",       # linear | cosine | smoothstep
               "loop": False},           # turntable: exact-loop framing math
    "output": {"folder": "", "per_part_subfolders": True,
               "overwrite": False,       # False => skip-already-rendered
               "keep_frames": False,
               "queue": False, "process_queue": False},
}
```

Rules:

- **`apply_render_spec(spec)` is one L3 function** returning
  `(render_opts, applied, skipped)` — every setter getattr-guarded, and the
  `skipped` list printed as a *settings audit* (the wire-audit idea applied
  to render options). A preset asking for `denoise` on a build without
  `setDenoise` degrades loudly, never breaks.
- **Presets are dicts, not code paths** — adding `print_tiff` is one entry
  (`format: "TIFF32"`, samples up, denoise off), zero new branches. Same
  argument that made MaterialSpec scale.
- **Scale tiers (RPR §5b) are one more overrides dict** merged between
  preset and dialog — Micro bumps samples + tightens padding, XL loosens
  padding + forces `adjust_environment` on import. The classifier already
  has confirmed footing (`getSceneInfo` units + `getBoundingBox(world=True)`).
- The camera-*move* parameters (zoom amount, crane, sweep axis, scatter
  radius…) stay per-script dialog fields — they're shot design, not render
  settings, and belong to PRO tier 2. The spec deliberately doesn't absorb
  them; it absorbs everything the five scripts currently hardcode or
  half-expose (resolution, samples, format, fps, frames, padding, queueing).

### 2.3 What each script gains, concretely

- **STD_VIEW:** preset picker replaces the width/height/format prompts;
  passes/alpha unlock the comp workflow; `overwrite=False` gives resume;
  per-part subfolders align output with RPA §6.
- **TURNTABLE:** `turntable_draft`/`turntable_final` presets replace the four
  hardcoded constants; `anim.frames/fps` finally operator-visible; a
  `rotate: camera|model` option (post-RP4) chooses highlight behaviour.
- **HERO/CUTAWAY/ASSEMBLY:** preview_mode becomes `preset=draft` (sampled +
  denoised, deterministic) instead of `setMaxTimeRendering(2)`; width/height/
  fps/frames come from the spec; easing selectable; social crops become one
  more preset consuming the same shot.
- **RUN_ALL (future L1):** the stage router passes one merged spec down to
  every stage — mode picks stages (RPA §4), spec picks fidelity, tier tunes
  framing. Three axes, never collapsed.

---

## 3. Dependability — boringly reliable, or loudly not

### 3.1 The load-safety pass (mandatory, Phase 1)

- Convert all f-strings in the three 2b scripts to `.format()`; replace every
  non-ASCII character (em dashes, arrows, ellipses in strings *and*
  docstrings/comments — the console is ASCII-sensitive, not merely
  f-string-averse). The generator's AA02→load-safe conversion is the worked
  example.
- **Add a guard so this never regresses:** extend `4_CHK_AUDIT_AA01.py` (or a
  tiny `0_VAL_LOAD_SAFETY` check, plain Python) that, for every
  `scripts/*.py` that imports `lux`: (a) `source.encode('ascii')` must
  succeed, (b) reject the f-string grammar (`ast` walk on a 3.x parse for
  `JoinedStr` nodes — runs fine in repo Python even though KeyShot can't),
  (c) optionally reject other >3.4 syntax (walrus, dataclasses import).
  Wire it into the repo's commit habit the way the naming audit already is.

### 3.2 Verify the render actually wrote — every place a script can silently do nothing

Current silent/quiet no-op inventory (each gets a named fix):

| # | Silent no-op | Where | Fix |
|---|---|---|---|
| 1 | All studios fail activation → zero renders, run "completes" | STD_VIEW (getStudio, headline #2) | setActiveStudio-first + version guard; **if every target failed, exit nonzero-style: print a run-level FAILURE banner + manifest summary row** |
| 2 | `renderImage` returns, file never appears | all five | `verify_output(path, started_at)`: exists + size > threshold + mtime >= start; manifest `status=rendered_verified` / `MISSING` |
| 3 | Queue mode: "queued" rows never reconciled | STD_VIEW, 2b queue path | after `processQueue()`, re-verify every queued path and rewrite/append reconciled rows |
| 4 | Frames missing mid-sequence → encode anyway or crash | TURNTABLE (crash), 2b (encode short) | `verify_frame_sequence(folder, pattern, first, last)` **before** `encodeVideo`; on gaps: no encode, status `FAILED (missing frames i, j, k)`, frames kept |
| 5 | Cutaway probe fails → renders N identical un-clipped sequences at full cost | CUTAWAY | feature-failed ⇒ skip render by default (opt-in "render anyway") |
| 6 | Ghost fade: no opacity API ⇒ static part renders sold as a "fade" | ASSEMBLY | hide/show appear mode as the confirmed fallback; status column records `mode_downgraded` |
| 7 | Env rotation dies mid-shot on the 360-domain edge | all 2b | `% 360.0` wrap in one L3 helper |
| 8 | Headless `input()` EOF spin | both 2a | DEFAULT_OPTIONS + job.json headless branch (2b pattern) |
| 9 | Assembly motion renders inverted, scene self-heals after | ASSEMBLY | initial-displacement fix + getTransform drift check (1.5-W2/W4) |
| 10 | Dialog silently fails to open (empty-string / None defaults) | 2a both, CUTAWAY | probe RP10, then sweep every dialog through a L3 `dialog_rows()` builder that rejects unsafe defaults at author time |

### 3.3 Resumability & partial-batch recovery

- **Skip-already-rendered:** with `output.overwrite=False`, a still whose
  verified output exists is skipped (manifest row `status=skipped_existing`).
  Because outputs are deterministically named (part x view x preset), resume
  is free — re-running a crashed 40-part batch redoes only the tail.
- **Per-part isolation:** every per-part body (`importFile` → stages) wrapped
  so one poisoned file yields one FAILED manifest row and the loop continues.
  AUTO's L0 watcher then routes that part to `99_FAILED/` (RPA §5) — but the
  L2 script must survive to *tell* it.
- **Run identity:** a `run_id` (timestamp + 4-hex) stamped into every
  manifest row and used as the frame-subfolder name — stale-frame
  contamination (1.3-W7) disappears, and two concurrent PRO sessions can't
  interleave rows ambiguously.
- **Timeouts/hangs:** `lux` offers no way to interrupt a wedged render from
  inside the script. Two-part answer: (a) belt-and-braces quality mode —
  samples target *plus* a generous `setMaxTimeRendering` cap so no single
  frame can run unbounded; (b) wall-clock ownership lives in L0 (`watch.py`
  kills/restarts a KeyShot that blows its per-part budget) — per RPA layering,
  KeyShot is a poor place for lifecycle enforcement.

### 3.4 Preflight (cheap, before any frame)

One L3 `preflight_run(spec)` called by every script:
- output folder abspath'd, created, **write-probed** (touch + delete);
- free disk vs a rough estimate (frames x WxH x 4 B x margin; queue mode
  adds scene-copy weight — warn specifically, 1.3-W6);
- scene census printed: `getSceneInfo()` units/triangles, studio + camera +
  model-set inventories (the "no studios, will fall back" surprise moves to
  second 0 instead of minute 40);
- version probe: `hasattr(lux, 'getStudio')`, `hasattr(render_opts,
  'setDenoise')` etc., printed once as a capability banner — the manifest
  records which capabilities the build actually had;
- `lux.isHeadless()` + door (AUTO/PRO) logged.

### 3.5 Determinism & structured logging

- Sample-count modes over time modes everywhere (1.3-W5); seeded randomness
  default-on (1.5-W8); sorted directory listings (1.1-W8); frame numbering
  zero-padded via one shared `FRAME_PATTERN` builder.
- One L3 log module: `info/warn/error` prefixes (already the de-facto
  convention), a run banner (script, rev, door, merged spec), and a
  run-end summary line (`N ok / N skipped / N FAILED — manifest: <path>`)
  so a human or the L0 watcher can grep one line for the verdict.
- Manifest v2 (§4.5) is the machine-readable twin of the same events.

---

## 4. Professionalism — output that lands predictably and looks intentional

### 4.1 Naming + folder lifecycle (RPA §5/§6 made real)

- One L3 `output_path(part, view, spec)` builder:
  `<root>/<PartName>/<stage>/<PartName>_<View>_<preset>[_<WxH>].<ext>`,
  everything through `sanitize_name()` (2a scripts currently unsanitised,
  1.1-W6). Stage subfolders `stills/ turntable/ reveal/` match the review
  structure so PRO output drops into the same contact sheet as AUTO.
- Manifest and contact sheet key on the same basename — naming is
  load-bearing (RPA §8), so the builder is the *only* place names are made.

### 4.2 Format discipline (all confirmed API)

| Use | Format | Spec preset | Notes |
|---|---|---|---|
| Web/review stills, contact sheet | PNG (+alpha when comping onto pages) | `review` | `RENDER_OUTPUT_PNG`, `setOutputAlphaChannel(True)` optional |
| Print / brand deliverables | TIFF32 (or PSD16 for retouch handoff) | `print` | 300-DPI sizing is a *pixel-dimensions* decision — lux has no DPI stamp; document target cm x 118 px/cm in the preset comment |
| Compositing / motion-graphics handoff | EXR + passes (depth, normals, clown, AO, reflection…) | `comp` | 12 pass setters confirmed; `setOutputRenderLayers` for layers |
| Animations | PNG frames → mp4 via `encodeVideo` (mov/avi/flv also documented) | `turntable_*`, reveal presets | GIF/webm for social stay a `3_PRC` post-stage, per the fade-reel precedent |

### 4.3 Colour, image styles, DoF — respect the Studio, log the truth

- **No gamma/exposure/tone-mapping functions exist** in any reference checked.
  Colour look lives in **Image Styles**, and those ARE scriptable:
  `getImageStyles()/setActiveImageStyle()/getActiveImageStyle()` (the
  returned ImageStyle exposes bloom/vignette/denoise/curve getters+setters
  per the 11.0 doc). Policy: image styles are *authored in the master
  template's Studios*, scripts never mutate them by default — but every
  manifest row records the active image style, and a PRO tier-2 option may
  select one by name. Tasteful bloom = a Studio decision, not a per-run knob.
- **DoF has no camera-side API** (no focus-distance/f-stop functions found;
  only `RenderOptions.setDofQuality(1-10)`). Same policy: author DoF on the
  Studio camera in the GUI; the `hero` preset bumps `setDofQuality` so
  authored DoF resolves clean in finals and stays cheap in drafts.
- `setDenoise(True)` is the single biggest professionalism-per-cost win for
  drafts and turntables: low samples + denoise reads clean at review size.
  Keep it off (or samples high) for `comp` — denoise before compositing is a
  known artefact source on passes.

### 4.4 Motion quality

- Turntables: FINAL = 120 frames @ 30 fps (4 s), perfect loop (the existing
  no-duplicate-frame math is right — keep it); DRAFT keeps 36 @ 24. Optional
  rotate-the-model mode (post-RP4) for static-highlight studio look.
- Reveals: easing library in L3 (`linear`, `cosine` — current, `smoothstep`,
  and a `settle` variant with a small late overshoot-and-return that still
  lands exactly at zero displacement — the zero-at-t=1 contract is the
  invariant, easing is free within it).
- Hold frames already exist (good instinct — editors want handles); expose
  them in the spec, keep defaults.

### 4.5 Provenance — the render manifest as the product's spec sheet

Manifest v2 (one schema, all five scripts, L3-owned):

```
run_id, timestamp, script, script_rev, door(AUTO|PRO|EXPERT), part_file,
base_name, view(studio|camera), studio, image_style, preset, width, height,
format, quality_mode, samples, denoise, engine, seed, frames, fps,
padding, tier, template, output_path, status, spec_hash, duration_s
```

Plus two sidecars written next to the outputs per run: the **merged
RenderSpec JSON** (rebuild-the-run artifact — MaterialSpec's "the spec is
the reproducibility artifact" applied to renders) and
`RenderOptions.getDict()` (documented) as ground truth of what KeyShot
actually held. The contact sheet (`3_PRC_CONTACT_SHEET`) can then surface
settings per thumbnail, and `4_CHK_AUDIT` can verify "every part got every
view at the right preset" mechanically.

---

## 5. The shared module (L3), concretely

RPA-7B2E4D §9 step 1 says extract it first. Here is the surface, sized so
all five scripts + the future `RUN_ALL.py` import it and each script sheds
150–400 lines of copies.

**Location & import mechanics.** `keyshot/scripts/shared/ks_shared.py`
(one file to start — KeyShot's console has no package context; a single
module keeps the bootstrap trivial). Every script gains a 4-line ASCII-safe
bootstrap: derive the scripts dir from `__file__` when present (the
`-script` path), else from a `KS_PIPELINE_HOME` env var, `sys.path.insert`,
import. The module itself obeys the same load-safety law: **no f-strings,
ASCII-only, Python-3.4-safe** — and the §3.1 audit covers it too.

```python
# ks_shared.py — surface (all names final, bodies per the sections above)

# -- compat / lux guards ---------------------------------------------------
L(name, default=None)              # getattr(lux, name, default) — constants & fns
has_capability(obj, name)          # hasattr probe, memoised, logged once
capability_banner()                # printed by preflight: version-sensitive calls

# -- logging ---------------------------------------------------------------
log_info(msg) / log_warn(msg) / log_error(msg)
run_banner(script_id, rev, door, spec)     # start record (AGENT_CONTRACT echo)
run_summary(ok, skipped, failed, manifest_path)

# -- options / doors -------------------------------------------------------
merge_options(*layers)             # preset <- job.json <- dialog <- sidecar
load_job_json(folder)              # AUTO sidecar (RPA section 3)
norm_item(value, valid)            # dialog item normalisation (existing idiom)
dialog_rows(fields)                # builds getInputDialog rows; REJECTS unsafe
                                   # defaults (empty-string / None on typed rows)
get_door()                         # AUTO if lux.isHeadless() else PRO

# -- studios / cameras -----------------------------------------------------
list_studios() / list_cameras()    # guarded, [] on failure
activate_target(name)              # setActiveStudio FIRST, then optional
                                   # getStudio camera resolve (version-safe);
                                   # returns (kind, camera_name) or None
resolve_targets(selection)         # ''|'ALL'|csv -> list; version-safe 'covered'

# -- framing / classification ---------------------------------------------
center_and_fit(padding, tier=None) # centerAndFit + padding (+ tier override)
classify_tier(node)                # bbox diagonal -> Micro..XL (RPR 5b table)
scene_census()                     # getSceneInfo + studios/cameras/modelsets

# -- geometry / transforms -------------------------------------------------
vec_xyz/vadd/vsub/vscale/vlen/vnorm/vcross
bbox(node)                         # probe list + shape parse (existing, pooled)
delta_matrix(translation, rot_deg, axis, pivot=None)  # pivot => conjugated
apply_delta(node, ..., state)      # bookkeeping + degrade-once flags
transform_snapshot(node) / transform_drift(node, snapshot)   # getTransform
                                   # readback verify (closes 1.5-W4)

# -- environment -----------------------------------------------------------
env_capture() / env_restore(state)
set_ground(env, enabled)           # setGroundShadows/Reflections, guarded
set_env_rotation(env, degrees)     # % 360 wrap + degrade-once

# -- render ----------------------------------------------------------------
PRESETS                            # the section-2 preset dicts
apply_render_spec(spec)            # -> (render_opts, applied, skipped-audit)
render_still(path, spec)           # pause-bracketed renderImage + verify
verify_output(path, started_at)    # exists + size + mtime
verify_frame_sequence(folder, pattern, first, last)  # pre-encode gate
preflight_run(spec)                # section 3.4

# -- animation -------------------------------------------------------------
build_profile(frames, hold_start, hold_end, easing)  # shared easing library
staggered_windows(n, frames, hold_start, hold_end, overlap)
FRAME_PATTERN(stem)                # zero-padded, shared

# -- video -----------------------------------------------------------------
encode_frames(folder, pattern, video_path, fps, first, last, keep)
                                   # wrapped, sequence-verified, never raises

# -- manifest --------------------------------------------------------------
Manifest(path)                     # v2 schema (section 4.5); .row(**kw)
write_spec_sidecar(folder, spec)   # merged spec + RenderOptions.getDict()
new_run_id()

# -- parts / model sets ----------------------------------------------------
get_parts(target_node, name_filter, order)
import_into_model_set(path, model_set)      # existing logic, pooled
sanitize_name(name)
```

**What each script keeps:** only its shot logic — STD_VIEW keeps the
per-studio loop; TURNTABLE keeps the azimuth walk; HERO keeps the
zoom/crane math and animation sync; CUTAWAY keeps the sweep geometry (and
gets the cutter-solid redesign); ASSEMBLY keeps the four displacement
functions. Everything they currently *copy* moves down. The dialog `values`
lists shrink to tier-1 fields + a per-script tier-2 block, both built
through `dialog_rows()`.

**REV discipline:** extracting L3 changes behaviour (verified renders, new
manifest schema) — that's a letter bump per repo convention: the five
scripts re-ship as `*_AB01.py` alongside the module.

---

## 6. Roadmap — shippable increments

Each phase ships something visible; nothing depends on an unprobed
assumption (MDD rule: design-for is fine, depend-on is not).

**Phase 1 — Load safety + truth (the unblocker).**
(a) f-string/ASCII conversion of the three 2b scripts (+ the §3.1 regression
audit); (b) `setActiveStudio`-first version-safe activation in all five;
(c) `verify_output` / `verify_frame_sequence` + wrapped `encodeVideo`
everywhere; (d) kill the 2a headless `input()` path (DEFAULT_OPTIONS +
job.json branch); (e) per-part `try` around import so batches survive bad
files; (f) env-rotation `% 360`.
Ship: all five scripts load, and none can silently render nothing.
Confidence: everything here is confirmed API or pure Python. No probes.

**Phase 2 — L3 extraction + Manifest v2 + RenderSpec.**
Extract `ks_shared.py` per §5 (mechanical; Phase-1 fixes land *in* it);
presets, `apply_render_spec` with the settings audit, spec sidecars,
unified manifest, preset-first dialogs, skip-already-rendered, run_id frame
folders, preflight banner. Scripts bump to `AB01`.
Ship: one place to fix anything; every output carries its settings.
Confidence: confirmed (formats/passes/denoise/engine version-gated by the
capability banner, degrade-loudly). Probe RP10 (dialog defaults) before
shipping the dialog builder; RP3 (denoise/engine presence on TJ's build).

**Phase 3 — Motion correctness.**
Assembly initial-displacement fix (1.5-W2) + `getTransform` drift
verification (1.5-W4) + seeded-by-default; rotation-pivot conjugation after
probe RP4; hide/show staggered-appear mode replacing ghost_fade's default;
turntable DRAFT/FINAL presets + optional rotate-model mode; easing library.
Ship: reveals that actually converge, turntables worth sending out.
Probes first: RP4 (pivot), RP5 (translate shape), RP12 (hidden-part
shadows).

**Phase 4 — Cutaway redesign.**
Retire the clip-plane candidate lists (keep one `dir(lux)` sweep in the
probe pack for the record); implement the cutter-solid +
`SHADER_TYPE_CUTAWAY` sweep per 1.4-W2; feature-failed ⇒ skip-render
default.
Ship: a cutaway that cuts.
Probes first: RP6 (cutaway material behaviour under a moving cutter).

**Phase 5 — Pro output surface.**
`comp` preset (EXR + passes + alpha), `print` (TIFF32), social crops;
image-style logging + optional selection; `renderAnimation()` direct path
for GUI-authored model-set animations (1.3-W11); `pause()/unpause()`
bracketing (RP11); contact-sheet settings surfacing; `4_CHK_AUDIT`
completeness check against Manifest v2.
Ship: studio-grade deliverables in one run, auditable.

**Phase 6 — Pipeline integration (RPA build-order steps 2–4).**
`RUN_ALL.py` consumes the L3 module + spec merge; `watch.py` owns lifecycle
moves + wall-clock timeouts; tier classifier calibrated (RPR open Q2) and
wired into `framing`; per-part sidecar overrides.
Ship: the AUTO door.

### Probe pack (RP) — run on the real build, paste results back as Rev 2

Same discipline as MDD-4B7A9F §8: one console session, PASS/FAIL + dumps.

| # | Probe | Method | Unblocks |
|---|---|---|---|
| RP1 | `lux.getStudio` present? Studio object methods? | `dir(lux)`; `dir(lux.getStudio(s))` on any studio | version-safe activation (Phase 1b) |
| RP2 | `renderImage` return value + synchronous file existence | render 1 tiny frame, print return, `os.path` checks immediately after | verify_output thresholds |
| RP3 | `setDenoise` / `setRenderEngine` / pass setters on build | `dir(lux.getRenderOptions())` | Phase-2 presets |
| RP4 | `applyTransform(…, absolute=False)` rotation pivot | offset cube, rotate 90°, compare `getTransform()` — spin vs orbit | Phase-3 conjugation |
| RP5 | `Matrix().translate(Vector)` call shape + `rotate` arg order (angle,axis) vs (axis,angle) | tiny transform test + getTransform readback | assembly translation |
| RP6 | `SHADER_TYPE_CUTAWAY` present; cutaway material assignable via `setMaterial`; cut updates when cutter moves between renders | template cube + 2-frame test | Phase-4 |
| RP7 | `getAnimationInfo()` live shape on a model-set animation | print `repr()` | hero sync (confirm the (duration, frames) read) |
| RP8 | `renderAnimation(videoName=…)` smoke test | 10-frame GUI anim, render | Phase-5 direct path |
| RP9 | any transparency-ish param on ADVANCED/GENERIC material root | generator's `dump_node`/`find_param` on a dielectric | ghost_fade route (b) |
| RP10 | `getInputDialog` with `DIALOG_FOLDER` default `""`, `DIALOG_DOUBLE`/`DIALOG_FILE` default `None` | 3 one-row dialogs | 2a + cutaway dialog fixes |
| RP11 | `pause()`/`unpause()` semantics + timing win in a mutate-render loop | 20-frame loop, timed both ways | Phase-5 bracketing |
| RP12 | `hide()`d parts: shadows/reflections gone? render cost? | 2 renders of a 2-part scene | staggered-appear mode |
| RP13 | queue mode: scene-copy disk cost + do queued jobs honour the given output path after `processQueue` | queue 3 stills, measure, process, verify | queue policy (1.3-W6) |

---

## Appendix A — API confidence census (2026-07-15 pass)

Doc versions checked: **11.0** (`media.keyshot.com/scripting/doc/11.0/lux.html`),
**2024.1** (`…/doc/2024.1/lux.html`), **2026.1 headless**
(`…/scripting/headless_doc/2026.1/lux.html`), plus the KeyShot 11 manual's
"Transforming scene nodes" scripting page. "Confirmed" = named in a
reference; version noted where it matters. TJ's build version is itself an
open fact to pin (RP1/RP3 settle it in practice).

**CONFIRMED (safe to design on, version-gate where flagged):**
`renderImage(path, width, height, opts, format)`;
`renderAnimation(folder, frameFiles, keepFrames, width, height, fps,
videoName, opts, format[, renderLastFrame in 2026.1])`; `renderFrames`;
`renderXR`; `renderConfiguration`; `encodeVideo(folder, frameFiles,
videoName, fps, firstFrame, lastFrame, keepFrames, opts)` (mp4/mov/avi/flv;
jpg/png/exr/tif sources); `processQueue()`;
RenderOptions: `setAdvancedRendering`, `setMaxTimeRendering`,
`setMaxSamplesRendering`, `setAntiAliasing`, `setGlobalIllumination`,
`setDofQuality`, `setShadowQuality`, `setCausticsQuality`,
`setIndirectBounces`, `setRayBounces`, `setPixelBlur`,
`setSharperTextureFiltering`, `setOutputAlphaChannel`, `setRegion`,
`setThreads`, `setAddToQueue` (saves a scene copy per job — documented),
`setSendToNetwork`, `setBackgroundRendering`, **`setDenoise`** (11.0+),
**`setRenderEngine`** + `RENDER_ENGINE_PRODUCT/INTERIOR/PRODUCT_GPU/
INTERIOR_GPU` (2024.1+), 12 `setOutput*Pass` setters,
`setOutputRenderLayers`, `getDict()`;
format constants `RENDER_OUTPUT_JPEG/PNG/EXR/TIFF8/TIFF32/PSD8/PSD16/PSD32`;
`getAnimationInfo()` → duration seconds + frame count; `get/setAnimationFrame`,
`get/setAnimationTime`; `pause()/unpause()` ("pauses renderer");
camera: `get/setCameraPosition/LookAt(obj|pt)/Up/Direction/Distance/
FieldOfView/FocalLength`, `get/setSphericalCamera` (azimuth [-180,180]),
`setStandardView`, `newCamera/removeCamera/saveCamera/isCameraUnsaved`;
studios: `getStudios()`, `getActiveStudio()`, `setActiveStudio(name)` (all
versions); **`getStudio(name)` + Studio object
(getCamera/getEnvironment/getImageStyle/getModelSets/setCamera/…) —
2024.1+ ONLY, absent from 11.0**;
environment: `getActiveEnvironment`, `get/setBrightness`,
**`get/setRotation` (2024.1 doc; domain [0, 360[)**, `setGroundShadows`,
`setGroundReflections`, `setBackplateImage`;
image styles: `getImageStyles/ set/getActiveImageStyle` (+ ImageStyle
bloom/vignette/denoise/curve accessors, 11.0);
scene: `getSceneInfo()` (name, filename, unit/meter scale, counts, scene +
render width/height), `setSceneUnit(unit, keep)`, `newScene(dontAsk)`,
`openFile(path, dontAsk)`, `importFile(path, showOpts, dontAsk, opts)` +
import-option keys incl. `model_set_import_to`, `adjust_environment`,
`geometry_units`, `up_vector`, `center_geometry`, `snap_to_ground`;
`saveFile`, `savePackage`; `getMaterialTemplates/setMaterialTemplate`;
scene tree: `getSceneTree`, `SceneNode.find`, `.isObject`, `.getName`,
`.getCenter(world)`, `.getBoundingBox(world)` → (min, max),
`.getTransform(world)` (**get-only** — no setTransform anywhere),
`.applyTransform(Matrix)`, `.setMaterial`, **`.hide()` / `.show()`**,
`.centerAndFit()`; model sets: `getModelSets/setModelSets`;
luxmath: `Matrix().makeIdentity()`, **`.translate(Vector)`** and
rotate-around-axis (KeyShot 11 manual scripting page + luxmath reference);
`SHADER_TYPE_CUTAWAY = 'lux_cutaway'` (2024.1 constants);
`isHeadless()`, `getInputDialog` (GUI only).

**LIKELY (consistent across sources, one detail unpinned):**
`Matrix.rotate` argument order (angle,axis) vs (axis,angle) — RP5;
`renderImage` blocking/synchronous file write — RP2; queued jobs honouring
scripted output paths — RP13; `pause()` = realtime raytracer (not
animation playback) — RP11.

**PROBE (no reference support — do not depend on):**
any scene-level clipping-plane API (`getClippingPlane`/`addSection`/… —
*expected absent everywhere*, RP6 replaces the feature); any opacity/
transparency setter on SceneNode or material (`setOpacity`/… — absent in
all docs; RP9 checks the material-param route); `applyTransform` pivot
semantics under `absolute=False` (RP4); dialog default-value tolerances
(RP10); DoF camera controls (none documented — treat as GUI-authored only);
gamma/exposure/tone-mapping functions (none documented — image styles are
the colour surface); license/GPU/hardware query functions (none documented —
preflight infers capability via hasattr instead).

## Appendix B — cross-references

- Load-safety precedent: `1_HLP_MAT_GENERATOR` AA02 pass, SCRIPT_STOCK
  2026-07-15 entry (the backlog already carries the 2b load-safety item as
  P1 — this review is its spec).
- Architecture: RPA-7B2E4D §3 (L3 as a named layer), §6 (folder lifecycle
  this doc's §4.1 implements), §9 (build order Phase 6 follows).
- Tiers/launcher: RPR-3F9C1A §5b (tier table consumed by `classify_tier`),
  §3 (preset-dict pattern RenderSpec generalises).
- Spec pattern + probe discipline: MDD-4B7A9F §3.2, §8.
- Prior confirmed-call corrections: RESEARCH_CREO_KEYSHOT.md 2026-07-11
  research pass (getBoundingBox / ground setters / getTransform get-only).
