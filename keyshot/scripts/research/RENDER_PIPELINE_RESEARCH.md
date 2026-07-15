# KeyShot Render Pipeline — Launcher Design Research

**UID:** RPR-3F9C1A
**Rev:** 2
**Date:** 2026-07-11
**Rev 2 changes:** §5 rewritten — real size range from TJ (2mm parts to 70m
assemblies, ~35,000:1) rules out a binary "small part" checkbox. Replaced
with a tiered classification + confirmed units-detection API findings.
**Audience:** another agent picking up this project. Read `HANDOFF.md` first for
the existing scripts (batch views, turntable, hero reveal, preflight, contact
sheet) — this doc only covers the NEW launcher/preset-mode layer discussed
this session. Nothing below has been built yet; this is a design spec, not a
changelog.

---

## 1. Context

Operator is a single, non-expert KeyShot user rendering small engineering
parts of wildly varying physical scale (mm-scale brackets up to full
assemblies). Existing scripts already implement the right primitives:
Studios-first camera/lighting, `centerAndFit()` + padding-factor framing
(scale-invariant by construction), manifest CSV logging, material preflight,
contact sheet. What's missing is a single entry point that chains them and
adapts behavior by scale/fidelity without the operator having to know which
script to run or in what order.

## 2. Research finding: KeyShot 11 "Workflow Automation"

Not a separate GUI/automation system. It's Luxion's name for the v11
expansion of **headless scripting** — more `lux.*` functions callable without
a UI, plus Material Graph control added to headless mode
(confirmed: keyshot.com "KeyShot 11 Now Available" + manual.keyshot.com).
There is no dedicated automation wizard to adopt instead of what this project
already does. **Conclusion: the existing `lux.isHeadless()` branch pattern
already used across every script in this project *is* Workflow Automation.**
The launcher should be built the same way — one script, GUI dialog in
interactive mode, `DEFAULT_OPTIONS` dict in headless mode — not a new
mechanism.

## 3. Launcher architecture

Single script (`RUN_ALL.py`, working name) as the one-click entry point.

**Stage order (fixed):**
1. Material preflight (hard gate — see §4)
2. Import + scale classification (see §5)
3. Standard views batch (per preset)
4. Turntable (per preset, optional)
5. Hero reveal (per preset, optional)
6. Contact sheet generation + auto-open (see §4)
7. Manifest summary printed to console

Each stage is a function import from the existing scripts where possible
(refactor shared logic — Studio resolution, `logManifestRow`, `centerAndFit`
+ padding — into a small shared module rather than copy-pasting, since it's
currently duplicated near-verbatim across 4 files).

### Preset modes

Dialog exposes one `DIALOG_ITEM` picker for mode, everything else derives
from it (fewer decisions for the operator = fewer ways to misconfigure a
run). Proposed starting set — names/count are TJ's call, this is a strawman:

| Preset | Scope | Fidelity | Stages run |
|---|---|---|---|
| Single Part — Quick | one file | preview samples | preflight, std views |
| Single Part — Hero | one file | full samples | preflight, std views, hero reveal |
| Batch — Draft | folder | preview samples | preflight, std views, turntable |
| Batch — Final | folder | full samples | all stages |
| Assembly | folder, multi-part | full samples | preflight, std views, turntable — hero reveal opt-in (assemblies may not have a single clean hero framing) |

Each preset is a plain dict of overrides merged onto shared defaults
(samples/render mode, which stages run, width/height, queue vs immediate) —
same pattern as `DEFAULT_OPTIONS` in the reveal script. Adding a new preset
later is adding one dict, not new code paths.

## 4. Hard QC gate + auto-surfaced review (agreed, no open questions)

- Preflight runs first, always, not skippable via a dialog option. On flags:
  print a clear summary and require an explicit "continue anyway" — don't
  silently proceed and don't hard-crash (operator may legitimately have an
  unchanged material by design, per the existing preflight's own caveat).
- Contact sheet regenerates at the end of every run (not just batch runs —
  single-part runs get a one-part contact sheet too, for consistency) and
  the launcher opens it automatically (`webbrowser.open()` on the local
  HTML file) rather than leaving the operator to find it.

## 5. Scale classification (Rev 2 — replaces "small part mode" checkbox)

Real numbers from TJ: parts as small as 2mm, assemblies up to 70m — roughly
a 35,000:1 range, mostly mm-scene-units but with some BSP/inch-designated
parts in the mix. A single boolean flag doesn't cover this. Replaced with a
tiered classification, still using the hybrid auto-detect + manual override
approach agreed last round.

### 5a. Units — confirmed API findings

- `lux.getSceneInfo()` returns the scene's unit/meter scale as part of its
  dict (alongside name, filename, triangle counts) — confirmed across
  every scripting doc version checked, 6.1 through 11.0. Cheap to log on
  every import: if the reported scale is off by a factor that looks like
  25.4 (mm/inch) or 1000 (mm/m), that's a unit mixup showing up directly —
  no bounding-box math needed to catch it.
- `lux.setSceneUnit(unit, keep=True)` exists for a manual fix if one's ever
  needed (`lux.UNIT_MM/CM/IN/FT/M`; `keep=True` rescales to preserve real
  size rather than just relabeling).
- Import options include `geometry_units`: "the unit of the imported
  scene, **if not automatically detected**. Supply as a conversion factor
  from meters." I.e. KeyShot normally auto-detects units from the file's
  own metadata; this is a manual override for formats that don't carry
  that metadata.
- **The mismatch risk is format-dependent, not universal.** STEP/IGES
  (and similar) typically embed real unit metadata and should
  auto-detect reliably. STL/OBJ carry no unit metadata at all — raw
  numbers only — so if any part of the library comes in as STL/OBJ,
  that's specifically where a silent mm/inch mixup slips through.
  **Open question for TJ: what formats does the input library actually
  use?** — determines how much weight this check needs to carry.
- BSP designations are a thread-standard naming convention, not evidence
  the geometry itself is in inches — a part modeled in mm with a "1/4
  BSP" callout in its filename is normal. Treat inch/BSP-looking filenames
  as, at most, a secondary corroborating signal (flag for a human glance
  if the name suggests inches *and* the detected scale/bbox looks
  inconsistent) — not a trigger on its own.
- `SceneNode.getBoundingBox(world=True)` returns (min, max) vectors
  directly — confirmed, usable for a standalone diagonal-size check
  without needing to reframe the camera first (currently only used
  implicitly via `centerAndFit()`).

### 5b. Tiered scale classification

Bounding-box diagonal (scene-native mm, assumed) drives a tier; each tier
is an overrides dict merged onto the run's base options — same pattern as
presets, not a separate code path:

| Tier | Diagonal (strawman — needs calibration) | Overrides |
|---|---|---|
| Micro | < 15 mm | tight padding, camera-distance floor, higher samples, orthographic candidate |
| Small | 15 mm – 150 mm | tight padding, higher samples |
| Standard | 150 mm – 1.5 m | current defaults, no override |
| Large | 1.5 m – 15 m | looser padding, environment/ground scale check (§5c) |
| Extra-large | > 15 m, up to 70 m | looser padding, environment/ground scale check, hero-reveal opt-in only (one close hero framing may not suit a 70m assembly), larger render-time budget |

Breakpoints above are placeholders, not a recommendation — should come
from the actual size distribution of TJ's part library, not guessed round
numbers (see open questions). Auto-classify from bbox diagonal, pre-select
the matching tier in the dialog, manual override always wins — same
hybrid as agreed for the old small/normal split.

### 5c. Large/XL-specific concerns (new — not just a padding-factor problem)

At the top of the range, scale stops being purely a framing problem:
- **Environment sphere**: import options already expose
  `adjust_environment` — "adjust environment sphere to fit the imported
  geometry" — confirmed. Worth forcing this on for Large/XL tiers so the
  HDRI doesn't clip or look wrong at building-scale.
- **Ground plane**: the same padding-factor math that works for a bracket
  may place the ground plane somewhere visually wrong at multi-meter
  scale — needs a real test render before trusting it unmodified.
- **Render time / sample budget**: larger assemblies generally carry more
  geometry and scene complexity — preset fidelity (§3) may need sample
  counts tuned per scale tier too, not just per preset.

## 6. Open questions for TJ (before build)

1. **Input file formats** — STEP/IGES (unit metadata usually reliable) vs
   STL/OBJ (no unit metadata, raw numbers only)? Determines how much the
   bbox sanity check needs to carry vs how much auto-detection can be
   trusted.
2. **Real bbox diagonal breakpoints** for the 5-tier table in §5b — needs a
   look at the actual size distribution across the part library, not the
   placeholder round numbers above.
3. Is scene-native unit consistently mm across the whole library, or are
   there known exceptions beyond "mostly mm" that need an explicit
   `geometry_units` override on import?
4. Final preset list/names (§3 table) — starting point, not final.
5. Should orthographic-camera-for-Micro be a tier default or an
   experimental opt-in flag (same confidence-tier discipline as the rest
   of this project — flag experimental until tested on a real part)?
6. Shared module refactor (Studio resolution / manifest logging /
   `centerAndFit` padding currently duplicated across scripts) — before or
   after the launcher, since the launcher wants to import this logic
   rather than re-copy it a fifth time.

## 7. Suggested build order

1. Calibration pass: run `lux.getSceneInfo()` + bbox diagonal over a
   sample of TJ's real parts to set real §5b breakpoints and sanity-check
   unit detection, before writing any classifier logic.
2. Shared module extraction (small, low-risk, unblocks everything else).
3. `RUN_ALL.py` skeleton — stage chaining, hard QC gate, auto-opened
   contact sheet, no presets/tiers yet.
4. Preset dict table + dialog wiring.
5. Bounding-box tier classification + per-tier overrides overlay.
