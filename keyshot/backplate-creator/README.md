# KeyShot Backplate Creator

A single-file browser tool for making 16:9 fluid backplates to sit behind KeyShot
product and industrial renders. Two modes share one RENKON shell:

- **Generate** — a procedural Canvas generator. 6 fluid styles (Viscous Current,
  Laminar Stream, Liquid Metal Droplets, Ripple Impact, Ink Bloom, Splash Crown)
  × 6 palettes (Polar Blue, Graphite Steel, Petroleum, Cyan Noir, Mercury,
  Milk & Ink), a deterministic seed, sliders (turbulence / viscosity / detail /
  light angle / highlight / horizon), preview + export guides, grain & vignette,
  a preset strip, and PNG/JPG export up to 5120×2880. Same seed + params always
  reproduces the same image. Exports as
  `renkon_backplate_<style>_<seed>_<w>x<h>.<fmt>`.
- **Curated** — the rendered pack: six real 2560×1440 (16:9) JPG backplates
  (01 Liquid Impact, 02 Laminar Arc, 03 Mercury Field, 04 Ink Bloom,
  05 Ripple Drop, 06 Viscous Current), each with a "best for" note, preview
  filters, a placement-guide toggle, per-card JPG download and a full-screen
  modal. The 6 JPGs live in `assets/` and are referenced relatively.

## KeyShot note

These are **photographic backplates, not HDRIs**. They set the *look* behind the
camera, not the lighting. Match your ground plane, camera perspective, shadow
direction and environment lighting separately in KeyShot.

## Files

- `index.html` — the tool (self-contained; only external refs are the two brand
  fonts and the 6 JPGs in `assets/`).
- `assets/NN_name_2560x1440.jpg` — the six curated rendered backplates.

No build step. Open `index.html` in a browser, or serve it under the RENKON
Pages base — relative links only.
