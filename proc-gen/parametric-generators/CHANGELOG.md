# Changelog — Parametric Generators

All notable changes to this tool. Newest first.

This file replaces the old `toolkit_N.html` filename-versioning scheme: the app
file is now a stable `index.html`, and *iteration is tracked here + in git history*
(commit messages for the detail, this file for the human-readable narrative, git
tags for milestones). Don't create `index_8.html` etc. — commit instead.

Versioning: informal `vN` milestones tagged in git as `paramgen-vN`.

## [Unreleased]

### Added — animated texture/bump preview (handoff §6.1 + §6.2)
- **Time-parametrized generators.** Each of the four generators takes an
  `animate` flag + `time` (0–1, one loop) and has its own seamless-looping
  motion: noise *breathes* (cyclic blend to a second field and back), grid
  *shimmers* (phase-shifted sinusoidal coord displacement), scratches *flicker*
  (per-streak fade in/out on staggered phase), splotches *boil* (per-blob
  size/strength pulse). Loops are seamless (`time 0` frame == `time 1` frame)
  and verified to have no boundary seam.
- **Live rAF preview.** Play/Pause button + loop-duration slider (0.5–8s) drive
  a `requestAnimationFrame` loop that cycles `time` and repaints both canvases.
  Self-cleans when you navigate away from the tool.
- **No regression.** With animation off, generator output is byte-identical to
  before — all motion is gated behind the `animate` flag. Pause returns to the
  canonical static frame.

### Changed — PNG export opens in a new tab
- Both texture exports now render to a `blob:` URL and open a small host page in
  a new tab (image + a working "Save PNG" link), instead of triggering a direct
  download. This sidesteps download restrictions (sandboxed iframes, etc.) and
  the `data:`-URL top-frame-navigation block, and works on Pages/local/sandbox.
  Falls back to a direct download if the popup is blocked.

### Still to do (next)
- Animated **export** (§6.3): PNG frame-sequence first (the KeyShot-friendly
  deliverable) via the same new-tab pattern (a numbered gallery of blob-URL
  frames), then optionally WebM via `MediaRecorder`. Export is currently a
  single static frame.
- The open GIF-export bug (§3) — unchanged; deprioritized in favor of the
  Worker-free frame-sequence path.

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
