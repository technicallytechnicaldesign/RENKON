# Advanced Textures module — plan for a subagent

Status: **planned, not started.** This is a handoff brief for whoever (human
or subagent) picks this up next. Read `HANDOFF_BRIEF_v2.md` and
`ANIMATED_EXPORT.md` first for context on the existing Texture & Bump Map
Generator this builds on.

## Why this exists

The 8 patterns on the Texture & Bump Map Generator (Noise, Cellular, Wood
Grain, Grid, Waves, Scratches, Splotches, Cracks) are all **generic and
seed-randomized** — good procedural building blocks, but nothing in there
reads as a specific, intentional finish a render artist would reach for.
Advanced Textures is a second tier: a small set of **art-directed, dialed-in**
textures modeled on real fabrication/finishing processes, meant to be the
last 10% that makes a KeyShot scene look professionally finished rather than
proceduralish — brushed machining marks, hand-applied paint strokes, and
similar. Less "random field," more "this is what a lathe/brush/sprayer
actually leaves behind."

## Where this fits

Same tool (`proc-gen/parametric-generators/index.html`), new pattern group
called **"Pro Finish"** alongside Organic / Geometric / Weathering in
`PATTERN_GROUPS`. It reuses the whole existing pipeline — `computeTextureData`,
Contrast, Levels, Invert, bump preview, static PNG export, and the
BLOB-URL-GALL animated frame-sequence export all keep working unmodified.
**Do not build a separate page or a separate export path.**

## The one architectural change this needs

The existing generic patterns all share one fixed slider set (Scale, Octaves,
Count, Roughness, Contrast, Bump Strength, Light Angle, Levels x3, Invert),
toggled visible/hidden per pattern via `PATTERN_META[kind].params`. Advanced
Textures need genuinely different controls — e.g. Machining Marks wants a
Linear/Radial direction toggle and a "pitch" (step-over spacing); Paint
Strokes wants stroke length and flow turbulence. Forcing these into the
existing 7-slider set would be a hack.

**Add a small per-pattern custom-param mechanism:**

```js
// Each entry in PATTERN_META may optionally declare its own extra controls,
// on top of (or instead of) the shared scale/octaves/count/roughness set.
// `custom` params live in state.custom[patternKind][paramKey] so they don't
// collide across patterns when switching. `type: "select"` renders a small
// button group (like the pattern selector itself); `type: "range"` renders
// a normal slider row.
machining: {
  name: "Machining Marks",
  params: { scale: false, octaves: false, count: false },
  custom: [
    { key: "direction", label: "Direction", type: "select",
      options: [{ value: "linear", label: "Linear" }, { value: "radial", label: "Radial" }],
      default: "linear" },
    { key: "pitch", label: "Pitch", type: "range", min: 2, max: 40, step: 1, default: 10 },
    { key: "waviness", label: "Waviness", type: "range", min: 0, max: 1, step: 0.05, default: 0.15 }
  ]
}
```

Build one generic renderer that reads a pattern's `custom` array and creates
the rows (reuse the existing `row()` helper's pattern — you'll likely need a
`customRow()` variant that reads/writes `state.custom[state.pattern][key]`
instead of `state[key]`, plus a `selectRow()` for the button-group type).
Hide/show the whole custom-controls container based on the selected pattern,
same as the existing `scaleRow`/`octaveRow`/`countRow` show/hide. Generator
functions receive `p.custom[p.pattern]` (or just pass the resolved custom
param object directly — either is fine, pick whichever reads cleaner) in
addition to the normal `p` state.

Keep it **backward compatible**: the 8 existing patterns get no `custom` key
(or an empty array) and are completely unaffected.

## Operator refinements (2026-07-11, verified against index.html as of commit 12f0476)

Read these alongside the sections below — they resolve four gaps between the
plan as written and the actual current code:

1. **Roughness needs no mechanism change.** The plan below says machining
   should "set `params.roughness = true`, everything else in the shared set
   off" — but the real code only show/hides the `scale`/`octaves`/`count`
   rows via `PATTERN_META[kind].params`; Roughness, Contrast, Bump Strength,
   Light Angle, and Levels are *unconditionally visible* for every pattern.
   So: give new patterns `params: { scale: false, octaves: false, count: … }`
   and simply *use* `p.roughness` in the generator — do not build a
   roughness-visibility toggle.
2. **Normalize custom length params by resolution.** Params like `pitch` and
   `strokeLength` are specified "in px" — but generators run at both
   `TEXTURE_PREVIEW_SIZE` (320) and `TEXTURE_EXPORT_SIZE` (1024), so a raw
   pixel value produces a visibly different (much finer) texture at export
   than in the preview. Treat custom length values as "px at preview size"
   and scale inside the generator: `const px = value * (w / 320)` (use the
   `TEXTURE_PREVIEW_SIZE` constant, with a comment). The existing `count`
   params dodge this via `spacing = w / count`; new absolute-length params
   must handle it explicitly, or preview and export won't match.
3. **Custom-param state + row lifecycle.** Initialize `state.custom` eagerly
   at mount: for every `PATTERN_META` entry with a `custom` array, populate
   `state.custom[kind][key] = default`. Build each pattern's custom rows
   *once* at mount into a per-pattern container div (hidden unless that
   pattern is selected, toggled in the same pattern-button click handler
   that toggles `scaleRow`/`octaveRow`/`countRow`) — don't rebuild rows on
   every switch, so slider positions persist the same way the shared rows
   do. Generators read `const c = p.custom[p.pattern] || {}`. Because
   `exportFrameSequence` and both static exports pass `state` straight into
   `computeTextureData`, custom params flow into every export path with
   zero export-code changes.
4. **Radial machining center: use the canvas center** (`w/2, h/2`), not a
   seeded off-center point like Wood Grain's pith — a lathe/faced part reads
   as centered, and a predictable center makes the map placeable. (Wood
   Grain keeps its seeded pith; that's the organic look, this is the
   machined one.)

## P1 — build these two (the ones actually asked for)

### 1. Machining Marks

Directional tool-mark texture — regular, physically-motivated, NOT randomly
scattered like the existing Scratches pattern. Two modes:

- **Linear** (mill/planing pass): parallel straight grooves at a fixed pitch,
  each with the same subtle waviness (a lathe/mill toolpath is not perfectly
  straight at the pixel level — low-frequency noise offset, amplitude driven
  by `waviness`). Use a `sin`-based groove profile (not a hard step) so the
  bump preview shows rounded grooves, not razor edges:
  `v = 0.5 + 0.5 * cos(2π * (perpendicularDistance + warp) / pitch)`.
- **Radial** (lathe/turning pass): same idea but grooves are concentric
  circles around a center point (reuse the distance-from-center approach
  already in `generateWood` — same math, tighter/regular pitch instead of
  organic ring spacing, and no big warp).

Params: `direction` (linear/radial, custom select), `pitch` (custom range),
`waviness` (custom range). Reuses the shared `roughness` slider for
groove-edge sharpness (low roughness = crisp sinusoidal groove, high = softer)
— set `params.roughness = true`, everything else in the shared set off.
Animate: grooves don't need motion in the "boiling/breathing" sense of the
other patterns — a subtle idea is the toolpath *advancing* (phase shift in
the sin, same trick as Wood Grain/Waves), representing the tool progressing.
Keep it optional/subtle; this pattern is meant to export as a static finish
more often than not.

### 2. Paint Strokes

Directional streaks that follow a flow field, simulating a hand-brushed or
roller-applied coat — NOT the existing Scratches pattern (which is discrete
random line segments with no shared direction). Approach:

1. Build a low-frequency warp field (reuse `buildValueField`, same as Wood
   Grain/Waves) to get a smoothly-varying flow direction per region instead
   of one fixed global angle — this is what makes it read as "brushed by
   hand" instead of "printed lines."
2. For each of `count` strokes: seed a start point, then step along the local
   flow direction (sample the warp field's gradient, or just perturb a base
   angle by the warp value) for `strokeLength` steps, depositing a soft round
   "brush dab" (falloff similar to `generateSplotches`'s per-blob falloff) at
   each step, width tapering slightly at both ends of the stroke.
3. Overlap of many strokes builds up the final height field — accumulate
   with `Math.min(1, existing + dab)`, same accumulation style as
   `generateSplotches`.

Params: `strokeLength` (custom range, in px at generation size — scale
sensibly, e.g. 20–200), `turbulence` (custom range, how much the warp field
bends each stroke off a straight line), plus the shared `count` (how many
strokes) and `roughness` (dab softness/edge). Animate: strokes "growing" —
reveal the stroke progressively along its length as a function of `p.time`,
which is a nice, legitimately different animation feel from every existing
pattern (all of which pulse/shimmer/drift in place; nothing currently does a
directional reveal). Loop it by having strokes reset and re-grow each cycle
(`time` 0→1 = one full reveal), which is trivially seamless since frame 0 and
frame 1 (mid-reset) can just both render at "0% grown" — accept a one-frame
snap at the loop boundary here rather than forcing a seamless in-place loop;
call this out explicitly in the in-file comment so it's not mistaken for a
bug later.

## P2 — stretch goals, only if time remains (each is its own small plan)

Sketch only — flesh out before building if you get here:

- **Orange Peel**: fine, soft, layered Worley/noise combo (small cell size,
  low contrast, no sharp edges) mimicking spray-paint surface dimpling.
  Reuses `buildWorleyField` at a much smaller `cellSize` than Cellular, plus
  a touch of `buildValueField` noise blended in for irregularity.
- **Knurling**: two `generateWaves`-style directional bands crossed at
  roughly ±45°, multiplied together, to form a diamond-knurl bump grid.
  Straight-knurl variant = just one band set, no cross.
  Custom params: `angle`, `pitch`, `diamond` (bool: cross the second band or not).
- **Anodize Swirl**: radial variant of brushed strokes — same flow-field
  stroke technique as Paint Strokes, but flow direction is tangential to
  circles around a center point instead of warp-perturbed straight lines.

## Build & verification notes (read this — it'll save you time)

- **No headless test runner is set up in this repo.** The way this session
  verified generator correctness: copy `index.html` to a scratch directory,
  drive it in headless Edge (`msedge.exe --headless=new --disable-gpu
  --allow-file-access-from-files --virtual-time-budget=8000 --dump-dom`)
  loaded inside a small driver HTML page that iframes the app, clicks
  pattern/control buttons via `contentDocument`, and reads back
  `canvas.getContext('2d').getImageData()` stats (mean/min/max/NaN-count) to
  confirm each pattern produces varied, non-degenerate output. `msedge.exe`
  lives at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` on
  this machine. In Git Bash, prefix the command with
  `MSYS2_ARG_CONV_EXCL="*"` and keep test files **outside** any path
  containing `AppData\Local\Temp` — Git Bash silently remaps that to `/tmp`
  and mangles `file://` URLs built from it.
- Verify every new pattern: no `NaN` in the pixel data, sensible min/max
  spread (not a flat, degenerate 0 or 255 field), and that turning `animate`
  on and sampling a few `time` values produces genuinely different frames.
- Verify the custom-param mechanism doesn't regress the 8 existing patterns
  — same headless click-through, confirm their stats are unchanged from
  before your edit (or re-run the check documented in this session's history
  if you have access to it).
- Update `CHANGELOG.md` (this tool's, not the repo root) and mark this file's
  Status line at the top as shipped once done.
- Commit with a real message describing what shipped; this repo's convention
  is git-as-history, no `index_2.html`-style file versioning.
