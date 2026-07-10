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
  scene binaries. Placeholder page for now; files drop in as they arrive.

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
- Each tool carries its own `CHANGELOG.md` (human-readable narrative) and
  `README.md`. Tag milestones in git (e.g. `paramgen-v8`).
- You review diffs → commit → push. Commit identity is set repo-local to the
  GitHub noreply address.

## Build & conventions

- **No build step, no framework.** Tools are self-contained single-file HTML
  apps that open directly in a browser. Minimize dependencies (the only current
  one is `gif.js` via CDN, and that's the broken path — see the toolkit brief).
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
