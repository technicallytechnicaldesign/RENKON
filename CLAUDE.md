# CLAUDE.md — RENKON

Context for Claude Code sessions. Read this first.

## What this repo is

The **public-facing RENKON tool-set**: a design + rendering hub served via
GitHub Pages (`https://technicallytechnicaldesign.github.io/RENKON/`). Tools
and scripts only — terse, impersonal, shippable.

- **`index.html`** (root) — landing page, a grid of tiles linking the areas.
- **`proc-gen/`** — procedural/parametric browser tools (parametric-generators,
  hydroform, pipeform, signage, label-generator).
- **`keyshot/`** — KeyShot automation: Python `lux`/`luxmath` scripts, hub page,
  filterable script inventory (`scripts.html`), backplate-creator.
- **`mockup-studio/`**, **`calculators/`** — render post-processing and
  render-domain calculators.
- **`model-goblin/`** — Model Goblin: zero-install browser toolkit for
  recovering KeyShot animation/material evidence and publishing it as an
  interactive 3D presentation (`author/` Author+Exporter and Published Viewer
  Template, `labs/` standalone bridge/salvage/visual-mode test labs). Folded
  in from its own workspace project 2026-08-23; workspace-side history lives
  in `PROJECTS/RENKON/PROJECT.md`.
- **`assets/`** — shared layer: theme, menus, overlay-engine (69-asset SVG
  library + rasterizer), fluid-engine, favicon.
- **`blender/fluid-cache-gen/`** — Blender-side fluid cache generators.

## History and the private lab

**History starts 2026-08-07.** This repo was republished with clean history as
part of a privacy split. Two private siblings exist:

- **`RENKON_LAB`** (private) — ALL process material: pickup notes, script
  inventory/backlog (SCRIPT_STOCK), research docs, the test ladder, the bench
  sheet. **Anything process-shaped you produce goes there, never here.**
- **`RENKON-ARCHIVE`** (private) — the frozen pre-split repo with full history.
  Reference only; never push to it.

**Hard rule: nothing personal, no session diaries.** Code comments state
engineering facts (constraints, measured API behaviour) impersonally, with no
dates-as-narrative, no anecdotes, no workspace paths, no usernames or machine
paths. No raster/diagnostic images — the root `.gitignore` blocks them (the
backplate-creator set is the one whitelisted exception).

## Core conventions

- **SVG-first, avoid PNG.** UI, icons, overlays, diagrams → inline SVG. Raster
  only where a render engine consumes it, and even then not committed here.
- **No build step, no framework, zero external JS dependencies.** Tools are
  self-contained single-file HTML apps. One sanctioned exception: brand fonts
  via Google Fonts with a non-blocking swap + system-font fallback.
- **Git is the version history**, not filenames — except the sanctioned
  `keyshot/scripts/*.py` `_REV` suffix (`{PREFIX}_{AREA}_{NAME}_{REV}.py`).
  **Any content change to a script = rename to the next REV** (`git mv`), bump
  the `# REV` header and any banner constant, and update every reference
  (scripts.html SCRIPTS + UPDATED map, keyshot/README.md) in the same commit.
  Machine-checked by `0_VAL_LOAD_SAFETY` — run it before pushing script changes.
- **CORE BLOCK**: the KeyShot generators duplicate a shared block, byte-identical
  in every carrier. Edit it in one file, propagate with
  `keyshot/scripts/_sync_core_block.ps1`; drift is a build failure.
- **KeyShot script constraints**: ASCII only, no f-strings, no walrus — the
  embedded interpreter chokes on all three and the whole file fails to load.
- **Relative links only** between pages so everything works both as local files
  and under the `/RENKON/` Pages base.
- **Brand**: dark working-tool surface, Space Grotesk + Space Mono, tokens
  `--bg:#0C141D --panel-bg:#14202C --panel-bg-raised:#182635 --line:#22303E
  --text:#ECF2F6 --muted:#6E7E8C --c-structural:#002F67 --c-fluid:#4FD1D9
  --c-accent:#F08A3C`. Keep new pages consistent.
- **LFS** rules exist for scene binaries (`*.bip` etc.) and are inert until such
  a file is committed; run `git lfs install` first if one ever is.
- Commit identity is repo-local, the GitHub noreply address. Multiple agents may
  work this repo concurrently — scope to different areas and `git pull --rebase`
  before every push.

## Evidence discipline (short form)

Tag claims MEASURED / LOGGED / ASSUMED; never state the condition of what you
cannot observe; one probe, one question, one prediction written before the run;
a stub politer than the real API tests nothing; two wrong diagnoses in a row is
a hard stop — build the instrument instead. The full version, with the bench
history behind it, lives in RENKON_LAB.
