# Changelog — KeyShot Motion Lab

## 2026-07-18 — Merged into Mockup Studio as the Presets tab

This page is now a redirect to `../mockup-studio/index.html#presets`. The four
concepts, shared pause/reset clock and fullscreen comparison modal moved into
Mockup Studio's new **Presets** tab verbatim (namespaced `ml-` in the ported
CSS, `presets*`/`ml*` ids in the ported JS to avoid clashing with Mockup
Studio's own compositor and modal). No behavior changed &mdash; still a
direction-finding/comparison viewer, no export pipeline. Kept as a redirect
stub rather than deleted so existing bookmarks/links keep working.

## 2026-07-18 — Established

Established from the Fluid Forge archive (`fluid_forge_motion_lab_compare.html`
&mdash; "Compare 2 + 2"): reskinned the bespoke dark/blue Inter chrome into the
RENKON house shell (Space Grotesk/Space Mono, `#0C141D` token scale, sharp
corners, 1px grid lines). The four Canvas motion concepts (Fluid Orbit Loop,
Reactor Flow Loop, Orbital Parallax Hero, Studio Sweep Cinematic), the shared
pause/reset clock and the fullscreen comparison modal are carried over
functionally unchanged &mdash; only the surrounding chrome changed. Stays a
direction-finding/comparison viewer; no export pipeline was added.
