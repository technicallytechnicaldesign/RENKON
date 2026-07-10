# Changelog — Parametric Generators

All notable changes to this tool. Newest first.

This file replaces the old `toolkit_N.html` filename-versioning scheme: the app
file is now a stable `index.html`, and *iteration is tracked here + in git history*
(commit messages for the detail, this file for the human-readable narrative, git
tags for milestones). Don't create `index_8.html` etc. — commit instead.

Versioning: informal `vN` milestones tagged in git as `paramgen-vN`.

## [Unreleased]

_Work in progress — see `docs/HANDOFF_BRIEF_v2.md` §6 for the roadmap
(animated bump/texture maps) and §3 for the open GIF-export bug._

## [v7] — 2026-07-10

Baseline import into the RENKON repo. This is the `toolkit_7.html` snapshot,
brought in as-is and renamed:

- Renamed `toolkit_7.html` → `index.html`; retitled "Overlay Toolkit" →
  "Parametric Generators" (the app houses two tools, not just overlays).
- Two tools present:
  - **Overlay Asset Customizer** — 44 SVG overlays, type→subtype→customize
    drill-down, global palette + per-asset param sliders, custom text, PNG export.
  - **Texture & Bump Map Generator** — procedural grayscale height/bump maps
    (noise, grid, scratches, splotches), simulated-relief preview, PNG export.
    Static output only for now.
- Known issue carried over: **GIF export is broken** (cross-origin Worker /
  CSP problem — see handoff brief §3). PNG export works.

### Pre-import history (manual `toolkit_1..7.html` saves)
Not reconstructed commit-by-commit — the v1→v7 evolution predates version
control. `docs/HANDOFF_BRIEF_v2.md` covers the design-system rationale and
architecture as of this baseline.
