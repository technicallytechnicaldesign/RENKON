# Render Calculators

Two directions on the same render-budget math, plus the electricity bill. A
single self-contained page (`index.html`) — no build step, no dependencies,
opens straight in a browser. Lives under RENKON because it's render-specific;
the general shop-math calculators moved to the sibling **TOOLBOX** hub.

## The two directions

- **Time from quality** — you know the *frame count* and the *quality* you
  want. Out: total render time, per-frame time, energy (kWh) and cost.
- **Quality from time** — you know the *frame count* and a *hard deadline*.
  Out: the highest quality tier that fits, an honest verdict ("you're fine" →
  "fucked"), the samples/frame you can afford, and a lever if it doesn't fit
  (how many frames Product *would* fit in).

## How the numbers stay honest

Everything scales from one relation:

```
render_time_per_frame ≈ k · pixels · samples  +  overhead
```

where `k` (seconds per pixel·sample) folds in scene complexity **and**
hardware. You set `k` one of two ways:

- **Calibrate** *(default, recommended)* — render one real frame, type in its
  resolution, samples and measured time. `k = time / (pixels · samples)`.
  Numbers you can bet a deadline on.
- **Preset** — pick a rough hardware class (GPU 4090-class → CPU 8-core
  laptop). Instant, ballpark, replace it with a calibration the moment you can.

`overhead` is the fixed per-frame cost that doesn't scale with samples (scene
load, denoise, save-out).

## Electricity

`kWh = watts/1000 · active_render_hours`, `cost = kWh · price`. Whole-machine
draw at the wall; active render time only. Currency picker ships with EUR, GBP,
USD, NZD and DKK — selecting one snaps the rate to a sensible default you can
then edit. Every input persists to `localStorage`.

## Quality tiers

Named tiers back editable samples-per-pixel values: Draft 8 · Preview 16 ·
Product 64 · Hero 200 · Max 512. Pick a tier to fill the samples field, or type
a custom count and the tier label follows.
