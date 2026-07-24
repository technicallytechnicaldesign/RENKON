# Render Calculators — Changelog

## v1 — 2026-07-24

First cut. The RENKON "Calculators" landing slot (reserved when the shop-math
tools moved to TOOLBOX) is now live and render-specific.

- **Time from quality** — frames × quality → total render time, per-frame time,
  energy and electricity cost.
- **Quality from time** — frames + deadline → highest quality tier that fits, a
  plain-spoken verdict ("you're fine" → "fucked"), affordable samples/frame,
  and a fallback lever (frame count that *would* fit Product) when it busts.
- **Calibrate-or-preset basis** — anchor `k` (s per pixel·sample) on one real
  measured test frame, or fall back to rough hardware presets.
- **Electricity** — whole-machine wattage × active render time × price/kWh, with
  an EUR / GBP / USD / NZD / DKK currency picker (rate snaps to a sensible
  default on switch, then editable).
- Quality tiers (Draft/Preview/Product/Hero/Max) ↔ editable samples-per-pixel.
- Per-quality-tier time bars; the inverse view overlays the deadline as a line
  so affordable tiers read at a glance.
- All inputs persist to `localStorage`; shared RENKON chrome (theme, reveal,
  nav) and house style throughout.
