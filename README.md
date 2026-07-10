# RENKON

A design + rendering hub — procedural tools, KeyShot automation, and a live
homepage tying them together. Built collaboratively via Claude Code.

**Live:** https://technicallytechnicaldesign.github.io/RENKON/

## Areas

| Area | What it is | Status |
|---|---|---|
| [`index.html`](index.html) | Landing page — grid of tiles linking to each area. Served as the Pages root. | Live |
| [`proc-gen/`](proc-gen/) | Procedural / parametric generation tools. | Active |
| &nbsp;&nbsp;↳ [`parametric-generators/`](proc-gen/parametric-generators/) | Overlay SVG customizer + texture/bump map generator (single-file app). | Live |
| [`keyshot/`](keyshot/) | KeyShot automation scripts + scene binaries. | Placeholder |

## How it's built

- **No build step.** Pages and tools are self-contained HTML that open directly
  in a browser. Homepage is served from the repo root via GitHub Pages.
- **SVG-first.** Vector SVG over raster PNG wherever possible — resolution-
  independent, diffable in git, themeable, and in keeping with the parametric /
  generative approach. Raster is reserved for things that genuinely need it
  (KeyShot renders, texture/bump maps). See [`CLAUDE.md`](CLAUDE.md).
- **Git for versions, not filenames.** No `_v7`-style file suffixes — commits
  and per-tool `CHANGELOG.md`s are the history.

## Working in here

Start with [`CLAUDE.md`](CLAUDE.md) for conventions (aesthetic tokens, iteration
rules, the SVG-first principle, LFS setup). Each tool folder has its own
`README.md` and `CHANGELOG.md`.
