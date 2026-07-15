# CLAUDE.md — RENKON

Context for Claude Code sessions. Read this first; it holds the conventions so
a session picks up without re-explaining.

## What this repo is

A design + rendering hub. Three workstreams under one repo, one live homepage
linking them:

- **`index.html`** (root) — the landing page. Served as the GitHub Pages root
  (`https://technicallytechnicaldesign.github.io/RENKON/`). A grid of tiles,
  each linking to a tool/area.
- **`proc-gen/`** — procedural / parametric generation tools. Currently
  `parametric-generators/` (single-file browser app: overlay SVG customizer +
  texture/bump map generator).
- **`keyshot/`** — KeyShot automation (Python `lux`/`luxmath` scripts) and
  scene binaries. Hub page (`index.html`) + a filterable script inventory
  (`scripts.html`) — no longer a placeholder, see Status & priorities below.

## Core principle: SVG-first, avoid PNG

Prefer **native vector SVG** over raster PNG wherever the content allows. This
is both practical and philosophically on-brand for parametric/generative work —
the output should be *described* (parameters, paths), not *baked* into pixels.

Why SVG wins here:
- Resolution-independent, tiny, and **diffable/mergeable in git** (it's text).
- Themeable at runtime via CSS custom properties (`var(--c-*)`), so one palette
  edit repaints everything — the whole toolkit already works this way.
- No LFS, no quota, no binary-blob versioning problems.

Reserve **raster (PNG/EXR/…) only when genuinely required**:
- Final KeyShot renders and photographic output.
- Texture / bump / height maps that a render engine consumes as raster material
  channels (these are raster *by nature* — SVG can't express them).

Practical rules:
- UI, icons, overlays, diagrams, page chrome → **SVG**, inline where possible.
- Overlay-tool exports → prefer the **SVG export** for vector assets; use PNG
  only for a consumer that can't take SVG.
- Don't commit PNGs to the homepage / proc-gen areas. If you think you need one,
  reach for SVG first.

## Iteration & versioning

- **Git is the version history**, not filenames. Do **not** create
  `index_8.html`, `toolkit_v9.html`, etc. Keep filenames stable, commit changes.
- **One sanctioned exception -- the `keyshot/scripts/*.py` `_REV` suffix.**
  These follow `{PREFIX}_{AREA}_{NAME}_{REV}.py` (e.g. `_AA02`); the `_REV` is
  *meant* to iterate. **Step it on each meaningful revision** -- rename the file
  **and** bump the `# REV` header (letter for a breaking change, number for a
  routine one), then update its references (README, SCRIPT_STOCK, scripts.html).
  There is always exactly one file whose name reflects its current REV -- this
  is NOT spawning parallel `_v8` copies (still forbidden). Per-commit churn
  lives in git; REV marks the revision. (Missed this once -- AA01 sat static
  across three substantive commits before being caught.)
- Each tool carries its own `CHANGELOG.md` (human-readable narrative) and
  `README.md`. Tag milestones in git (e.g. `paramgen-v8`).
- You review diffs → commit → push. Commit identity is set repo-local to the
  GitHub noreply address.

## Build & conventions

- **No build step, no framework.** Tools are self-contained single-file HTML
  apps that open directly in a browser. No external dependencies — everything
  is native browser APIs (Canvas, `blob:` URLs, Web Animations API, native SVG
  time control); the last CDN dependency (`gif.js`) was removed in favor of a
  Worker-free, dependency-free frame-sequence export.
- **Shared aesthetic** across all pages (keep new pages consistent):
  - Dark: `--bg:#0a0f16`, `--panel-bg:#0d1520`, `--line:#1c2733`,
    `--text:#e8e8e0`, `--muted:#7a7f83`.
  - Palette roles: `--c-structural:#002F67`, `--c-fluid:#2FA8B0`,
    `--c-accent:#E8792E` (accent = interactive/orange).
  - Font: `"IBM Plex Mono","Courier New",monospace`. Sharp corners, 1px grid
    lines, uppercase letter-spaced labels.
- **Relative links only** between pages (no leading `/`) so everything works
  both opened as local files and served under the `/RENKON/` Pages base.

## Binaries & LFS

- Git LFS tracks KeyShot / rendering binaries. Scene-format rules live in the
  root `.gitattributes`; raster render outputs (`*.png`, `*.jpg`, …) are scoped
  to `keyshot/.gitattributes` so they don't sweep up stray web assets elsewhere.
- Run `git lfs install` before committing any tracked binary.
- KeyShot binaries are drop-in only — Claude can't meaningfully edit them.

## Living plan

The evolving setup/roadmap lives in the design-hub plan doc
(UID `d1760e7f-2a5e-44b7-998b-7ca99822c5cc`). Ask to update it in place as
things change.

## Status & priorities (2026-07-11)

Cross-cutting snapshot for picking this repo back up. Each tool's own
`CHANGELOG.md` has full detail; this is the summary. Update this section in
place as things land — don't let it go stale like the old "keyshot is a
placeholder" line did.

### Shipped
- **Texture & Bump Map Generator** (`proc-gen/parametric-generators/index.html`,
  ~3500 lines, single file): 4 → 13 patterns (added Cellular, Wood Grain,
  Waves, Cracks, then a "Pro Finish" group — Machining Marks, Paint Strokes,
  Knurling, Orange Peel, Anodize Swirl), grouped/sortable pattern selector,
  Levels control, a per-pattern custom-param mechanism, seamless XY tiling
  for Noise + Grid plus a Tile Preview QA toggle, Normal Map export, and a
  preset library.
- **Overlay Asset Customizer** (same file): fixed a real SMIL-freeze bug
  (`animateMotion` positions were read via `transform.baseVal`, which is
  always `null` for motion animations — fixed via `getCTM()`), then retired
  `gif.js` entirely in favor of the same blob-URL frame-sequence export the
  texture tool uses. **The repo now has zero external dependencies.**
- **`keyshot/`**: split from one placeholder page into a hub (`index.html`)
  + filterable inventory (`scripts.html` — active scripts shown by default,
  pending/archive/locked behind a disclosure toggle). 14 current scripts
  across pipeline stages 0–4. Live inventory + backlog: `keyshot/SCRIPT_STOCK.md`.

### Priority list — what's next
1. **[keyshot, P1]** Assembly reveal, Creo-driven (animate an authored
   explode state) — blocked on verifying explode data survives the Creo
   plugin import; needs someone with Creo access to check first.
2. **[keyshot, P1]** Hand-staged one-off reveal (particles, rain) — still at
   design stage, not started.
3. **[proc-gen, unscoped]** KeyShot material-template bridge — pairs a
   texture/bump/normal export triple with a suggested KeyShot material-graph
   hookup. `FEATURE_BACKLOG.md` explicitly flags: *don't guess at this one* —
   needs whoever specs it to actually know the target KeyShot material graph
   shape.
4. **[keyshot, P2]** BOM-driven manifest — blocked on picking a BOM access
   method (research item, not started); dynamic BOM callouts on assembly
   renders depend on this landing first.
5. **[keyshot, P2]** Studio/camera-rig template library; assembly-reveal
   sub-assembly build (grouped convergence — extension point already noted
   in `2b_ANI_ASSEMBLY_PROCEDURAL_AA01.py`'s `get_parts()`/
   `schedule_staggered_windows()`).
6. **[proc-gen, low-pri]** Seed-variation gallery — thumbnail grid across
   seeds, same pattern/params. Low effort (reuses the frame-gallery UI
   shape from `ANIMATED_EXPORT.md`), just hasn't been asked for yet.

### Key points
- **Two `index.html` files matter here**: root (`/index.html`, the RENKON
  landing tile grid) and `proc-gen/parametric-generators/index.html` (the
  actual app — overlay customizer + texture generator, one file). `keyshot/`
  is `index.html` (hub) + `scripts.html` (inventory) — see `keyshot/README.md`.
- **Multiple agents can work this repo concurrently.** It happened for
  hours this session — a keyshot-focused track and a texture-generator
  track ran in parallel with zero conflicts. What made it work: scope each
  agent to a different area of the repo/file, and `git pull --rebase`
  before every push. Don't assume you're the only writer.
- **Headless verification pattern** (no test runner in this repo): drive the
  real `index.html` in headless Edge —
  `"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
  --headless=new --disable-gpu --allow-file-access-from-files
  --virtual-time-budget=N --dump-dom` — loaded via a small driver page that
  iframes the app and reads back canvas pixel stats / DOM state. In Git
  Bash, prefix with `MSYS2_ARG_CONV_EXCL="*"` and keep test files **outside**
  any path containing `AppData\Local\Temp` (Git Bash silently remaps that to
  `/tmp` and mangles `file://` URLs). Full worked example in
  `proc-gen/parametric-generators/docs/ADVANCED_TEXTURES.md`'s "Build &
  verification notes".
- Plan docs live in `proc-gen/parametric-generators/docs/`. `ADVANCED_TEXTURES.md`,
  `FEATURE_BACKLOG.md`, and `OVERLAY_EXPORT_MODERNIZATION.md` are all fully
  shipped (status line at the top of each says so). `HANDOFF_BRIEF_v2.md`
  and `ANIMATED_EXPORT.md` are the earlier architecture docs, still accurate.
