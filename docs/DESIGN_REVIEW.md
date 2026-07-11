# RENKON — Site-wide Design Review & Implementation Plan

**Status: NOT STARTED — planning/review pass only.** This doc is the handoff for
a Sonnet implementer. No site files were edited producing it. It covers all
four live pages (`index.html`, `proc-gen/parametric-generators/index.html`,
`keyshot/index.html`, `keyshot/scripts.html`) plus shared `assets/`.

Scope of the ask (verbatim): *"do a design review of the site. make it easier
to read, more cohesive and have light dark mode and for the generators to be
more intuitive / easier to use without losing functionality."*

Four review lenses below (Readability, Cohesion, Light/Dark, Generator
Usability), each with findings then an ordered, concrete implementation plan.
Read the "What NOT to change" and "Verification" sections before starting.

---

## Lens 1 — Readability

### Findings
- **Type is uniformly tiny.** Labels are 9–11px, body/help 11–12px, almost all
  uppercase with 0.05–0.1em tracking, in IBM Plex Mono. Uppercase + wide
  tracking + 10px in a mono face is hard to scan in bulk (worst in the
  proc-gen control wall). Chips/section-labels at 9px (root `index.html:69`,
  proc-gen `index.html:120,125`) are near the floor of legibility.
- **`--muted` fails contrast for body text.** `--muted:#7a7f83` on
  `--panel-bg:#0d1520` is ≈4.0:1 — under WCAG AA (4.5:1) for the 11–12px body
  copy it is used for everywhere (`.tile p`, `.card p`, `.page-head p`,
  `.stage-body .note`, footers). It reads as low-effort-to-parse grey mush.
- **Unbounded line length in proc-gen.** `footer.note` (proc-gen
  `index.html:165`, content at `1593` and `3101`) has no `max-width`, so on a
  1400px `#app-main` the explanatory paragraphs run the full width — the single
  most important "what do these exports mean" text is the hardest to read.
- **Density with no landmarks.** The texture tool's entire control set lives in
  one flat `.param-panel.texture-controls` flex-wrap wall (proc-gen
  `index.html:2580`+) with exactly one divider ("Levels", `2740`). Nothing
  guides the eye from pattern → shape → tone → export.

### Plan (ordered)
1. **Bump the type scale by one step, everywhere it's a readability floor.** In
   each page's `<style>`: smallest label tier 9px → 10px (chips, group-labels,
   section-labels); body/help 11px → 12px (`.tile p`, `.card p`, `.stage-body
   .note`, `.param-hint`, `.status-line`, footers). Keep `.page-head h1` and
   headings as-is. Do **not** touch letter-spacing on headings; do reduce
   tracking on 10px uppercase labels from 0.1em → 0.06em where it's currently
   0.1em (proc-gen `index.html:120,125`) — tight tracking + tiny + uppercase is
   the least legible combo.
2. **Lighten `--muted` to pass AA.** Change `--muted:#7a7f83` →
   `--muted:#93999e` in the dark `:root` of all four pages (contrast ≈5.1:1 on
   `--panel-bg`, still clearly secondary vs `--text`). This is a one-line change
   per page and it's the highest-leverage readability fix.
3. **Cap explanatory prose width.** Add `max-width: 74ch` to `footer.note`
   (proc-gen `index.html:165`) and to `.note`-style copy. Body paragraphs
   already cap at 62–68ch — match that discipline for the export footnote.
4. **Add section landmarks to the proc-gen control wall** — covered in Lens 4
   (this is where readability + usability overlap; do it there).

---

## Lens 2 — Cohesion

The four pages **almost** share a language but proc-gen has drifted and the CSS
is copy-pasted (no shared stylesheet), so drift is invisible until you diff.
Concrete inconsistencies, with file:line:

1. **proc-gen never loads `reveal.js`.** Root (`index.html:105`),
   keyshot hub (`keyshot/index.html:102`) and scripts
   (`keyshot/scripts.html:169`) all load `reveal.js` in `<head>`; proc-gen loads
   only `menu.js` (`proc-gen/.../index.html:3510`) and no reveal. So three pages
   animate content in and one doesn't — a visible inconsistency on navigation.
2. **`.page-head h1` size drift:** 16px in proc-gen (`index.html:57`) vs 17px in
   root (`44`), keyshot hub (`51`) and scripts (`51`).
3. **Header treatment diverges.** Root/keyshot/scripts use a semantic
   `<header>` with `.wordmark` (REN**K**ON) + `.meta` (root `index.html:32-38`,
   keyshot `31-38`, scripts `31-38`). proc-gen uses a **sticky** `#app-header`
   with `.crumbs` + `.mark` = "OVERLAY TOOLKIT" (`index.html:41-52`) and shows
   **no RENKON wordmark** at all — the brand mark is absent on the busiest page.
4. **Back-nav affordance is inconsistent.** keyshot uses an `<a class="up-link">`
   reading "← Back to RENKON" (`keyshot/index.html:111`); proc-gen uses a
   `<button class="up-link">` reading "↑ Up to {label}" (`index.html:61-68`,
   built at `1387-1393`). Different element type **and** different arrow
   metaphor (back vs up) for the same action.
5. **Tile vs card duplication.** Root/keyshot render the grid with `.tile`
   (min-height 190px, `h2` 13px/weight 500 — root `index.html:56-71`); proc-gen
   renders the same concept with `.card` (min-height 130px, `h2` 14px/weight
   600 — `index.html:74-85`). Same visual pattern, two class systems, different
   type weights.
6. **Focus-outline offset:** 3px on root/keyshot/scripts (`:29` each) vs 2px on
   proc-gen (`index.html:34`).
7. **Theme-blind hardcoded colors** (these also block Lens 3): `.btn.primary:hover
   { color:#001A33 }` (proc-gen `index.html:159`); preview-canvas backgrounds
   `#060a10` (proc-gen `88,132`; also `.mini-stage`, `.large-stage`, text-field
   input `141`); splash rect `fill="#0a0f16"` (root `index.html:116`); new-tab
   export pages hardcode `#0a0f16`/`#e8e8e0` (proc-gen `3328,3355`). None use
   `var(--…)`, so they won't follow a theme switch.
8. **~100 lines of identical `:root` + reset + header + tile CSS are copy-pasted**
   across the four HTML files with no shared stylesheet — the root cause of all
   drift above.

### Plan (ordered)
1. **Add `reveal.js` to proc-gen.** Insert `<script src="../../assets/reveal.js">
   </script>` in its `<head>` (alongside where the others place it). Verify the
   reveal targets (`main h1/h2/h3`, `.tile/.card`) exist on the proc-gen views;
   proc-gen builds `main` dynamically, so confirm reveal's `DOMContentLoaded`
   run still finds content — if content mounts after DOMContentLoaded, call
   `window.__rkRunReveal()` at the end of the initial render instead, or accept
   reveal only animating the first static paint. **Open question for
   implementer** (see end).
2. **Normalize the shared tokens.** Set `.page-head h1` to 17px in proc-gen
   (`index.html:57`); set proc-gen focus offset to 3px (`:34`) to match. These
   are cosmetic, low-risk.
3. **Give proc-gen the RENKON wordmark.** In `#app-header`, keep the crumbs but
   add the `.wordmark` (REN**K**ON, linking to `../../index.html`) on the left
   or as a third element, matching the other headers' brand presence. Keep it
   sticky (that's a fine proc-gen-specific choice — note it, don't fight it).
4. **Unify back-nav to "← Back to {label}".** Change proc-gen's up-link arrow
   from "↑ Up to" to "← Back to" (`index.html:1393`) to match keyshot's
   metaphor. Element-type difference (button vs anchor) is acceptable (proc-gen
   navigates via hash-router), but the label/arrow must match.
5. **Card/tile:** low priority; do NOT re-plumb proc-gen's `.card` to `.tile`
   this pass (risk > reward on a 3500-line file). Instead align the two type
   values: set `.card h2` to 13px/weight 500 (`index.html:83`) so headings match
   the tile system. Leave layout alone.
6. **Convert theme-blind chrome colors to vars** — folded into Lens 3, step 4.
7. **(Stretch, note only — do not do this pass)** Extracting the shared chrome
   CSS to `assets/theme.css` would kill the copy-paste drift permanently, but
   it touches all four files' `<head>` and risks the theme work landing on a
   moving target. Recommend doing it as a **follow-up** after light/dark ships,
   not interleaved.

---

## Lens 3 — Light / Dark mode

### Decision: one shared, self-contained `assets/theme.js`, loaded synchronously in `<head>`

Mirror the `menu.js` philosophy exactly (one dependency-free script, injects its
own CSS + DOM, resolves nothing external). **Do NOT** use a separate
`theme.css` `<link>`: a stylesheet can't set the pre-paint `data-theme`
attribute, so it would flash dark-then-light on load, and it would add a second
per-page tag. Fold the light-theme variable overrides, the persistence logic,
and the toggle button all into `theme.js`. Each page then adds exactly **one
line**.

Why `<head>` synchronous (not end-of-body like menu.js): to avoid a flash of the
wrong theme, the script must set `documentElement.dataset.theme` and inject the
override `<style>` **before first paint**. `reveal.js` already establishes the
"load a small script synchronously in `<head>`" precedent, so this is
consistent.

### `assets/theme.js` — exact behavior

```js
/* RENKON theme — self-contained light/dark toggle, dropped into every page's
 * <head> (synchronous, pre-paint) so there is no flash of the wrong theme.
 *   <script src="<path-to>/assets/theme.js"></script>
 * Persists the user's explicit choice in localStorage('renkon-theme');
 * otherwise follows prefers-color-scheme. Injects a toggle button into the
 * shared .rk-nav pill (from menu.js) if present, else a standalone fixed btn.
 */
(function () {
  if (window.__renkonTheme) return;
  window.__renkonTheme = true;

  var KEY = "renkon-theme";
  var root = document.documentElement;

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function prefersLight() {
    try { return matchMedia("(prefers-color-scheme: light)").matches; } catch (e) { return false; }
  }
  function resolve() {
    var s = stored();
    return (s === "light" || s === "dark") ? s : (prefersLight() ? "light" : "dark");
  }
  function apply(theme) { root.setAttribute("data-theme", theme); }

  // 1) PRE-PAINT: set attribute + inject the light-theme variable overrides now.
  apply(resolve());
  var css =
    ':root[data-theme="light"]{' +
      '--bg:#f4f6f8;--panel-bg:#ffffff;--panel-bg-raised:#eef1f4;' +
      '--line:#d3dbe2;--text:#16202b;--muted:#5c666e;' +
      '--c-structural:#002F67;--c-fluid:#1f8b93;--c-accent:#c6591a;' +
      // proc-gen-only extra roles (harmless on pages that don't use them):
      '--c-leader:#3a4653;--c-panel-base:#e7edf3;--c-panel:rgba(231,237,243,0.92);--c-label:#16202b;' +
    '}' +
    // Keep image viewports dark in BOTH themes via a var (see step 4):
    ':root{--stage-bg:#060a10}' +
    ':root[data-theme="light"]{--stage-bg:#0d1520}';
  var st = document.createElement("style");
  st.id = "rk-theme-style";
  st.textContent = css;
  (document.head || root).appendChild(st);

  // 2) Button injection deferred until body/nav exist.
  function mountBtn() {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "rk-btn rk-theme-btn";   // reuse menu.js .rk-btn styling
    btn.setAttribute("aria-label", "Toggle light / dark theme");
    btn.title = "Toggle theme";
    var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
    var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>';
    function paint() { btn.innerHTML = root.getAttribute("data-theme") === "light" ? MOON : SUN; }
    paint();
    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      apply(next);
      try { localStorage.setItem(KEY, next); } catch (e) {}
      paint();
    });
    var nav = document.querySelector(".rk-nav");   // menu.js pill
    if (nav) nav.appendChild(btn);                 // pill becomes [Home][Menu][Theme]
    else {                                         // fallback: own fixed button
      btn.style.cssText = "position:fixed;top:10px;right:12px;z-index:9999";
      document.body.appendChild(btn);
    }
  }
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", mountBtn);
  else mountBtn();
})();
```

Notes on the palette values (do not "improve" these without re-checking
contrast):
- **Light chrome:** `--bg:#f4f6f8` (cool near-white, keeps the blue-grey brand
  tint), `--panel-bg:#ffffff` (panels pop), `--panel-bg-raised:#eef1f4` (raised
  = slightly *darker* than panel on light, which is the correct hover direction
  when white is the base), `--line:#d3dbe2`, `--text:#16202b` (≈14:1 on bg),
  `--muted:#5c666e` (≈5.2:1 — AA for body).
- **Palette roles stay recognizable:** `--c-structural` kept identical
  (`#002F67` deep blue reads on both). `--c-fluid` nudged from `#2FA8B0` →
  `#1f8b93` so the teal keeps ~4.5:1 as border/label ink on white while staying
  obviously "the teal." `--c-accent` deepened `#E8792E` → `#c6591a` (≈4.6:1 on
  `#f4f6f8` — the raw orange is only ~3:1 and fails AA for the small accent text
  and 1px borders it's used for). It is still unmistakably the RENKON orange.
- **Interaction with the Overlay Customizer palette panel:** that tool calls
  `applyPaletteToDOM()` which sets the six role vars as **inline styles on
  `documentElement`** (proc-gen `index.html:203-208`). Inline styles beat the
  `[data-theme]` stylesheet, so **inside the customizer view the roles revert to
  the user's chosen/brand values regardless of theme** — which is correct, it's
  a color tool showing true colors. The chrome vars (`--bg`/`--text`/etc.) are
  NOT touched by that function, so chrome still themes correctly there. Document
  this; it is by design, not a bug.

### Plan (ordered)
1. **Write `assets/theme.js`** exactly as above.
2. **Add one line to each of the four pages' `<head>`**, as the FIRST script
   (before `reveal.js`), with the correct relative depth:
   - `index.html` (root): `<script src="assets/theme.js"></script>`
   - `keyshot/index.html`: `<script src="../assets/theme.js"></script>`
   - `keyshot/scripts.html`: `<script src="../assets/theme.js"></script>`
   - `proc-gen/parametric-generators/index.html`:
     `<script src="../../assets/theme.js"></script>`
3. **Style parity for the theme button:** it reuses `.rk-btn` from `menu.js` so
   it already matches the pill. Confirm the sun/moon SVG sits at 30px like the
   other icons (it will — `.rk-btn svg{width:30px}`). No new CSS needed beyond
   what's inline.
4. **Fix the theme-blind hardcoded colors** (Lens 2 finding 7) so the switch
   actually looks right in light mode:
   - Replace preview/stage backgrounds `#060a10` with `var(--stage-bg)` at
     proc-gen `index.html:88` (`.mini-stage`), `132` (`.canvas-panel canvas`),
     `141` (`.text-field-wrap input`), `147` (`.large-stage`). `--stage-bg` is
     defined by `theme.js` (dark viewport in both themes — a texture/relief
     preview reads best on a dark stage; intentional). If you prefer the
     text-field input to follow the light panel instead, use `var(--panel-bg)`
     there — implementer's call, low stakes.
   - `.btn.primary:hover { color:#001A33 }` (proc-gen `index.html:159`): change
     to `color: var(--bg)` so hovered-primary text stays legible against the
     accent fill in both themes.
   - Root splash rect `fill="#0a0f16"` (`index.html:116`) and `#rk-word` fills:
     the splash only runs on the dark-default first paint and is removed after;
     lowest priority. If touched, set the rect fill to `var(--bg)` (it's inline
     SVG so `var()` resolves). Acceptable to leave as-is — note it.
   - New-tab export pages (proc-gen `3328,3355`) hardcode dark bg for the
     exported-frame gallery. These are **separate documents** with no RENKON
     chrome; leave them dark (a neutral dark viewer for image review is fine).
     Note the decision; do not wire theme into them.
5. **Optional (document as nice-to-have, not required):** live-update when the
   OS theme changes *and the user hasn't explicitly chosen* — add a
   `matchMedia("(prefers-color-scheme: dark)").addEventListener("change", …)`
   that re-applies `resolve()` only when `stored()` is null. Skip if it
   complicates; the core requirement (default to `prefers-color-scheme`, allow
   override, persist) is met without it.

---

## Lens 4 — Generator usability

Two tools live in `proc-gen/parametric-generators/index.html`. Every current
control, button, export option, pattern, and preset must remain reachable — the
changes below are **reorganization, labeling, and progressive disclosure only.**

### 4A — Texture & Bump Map Generator

**Current layout** (all inside one flat `.param-panel.texture-controls`,
built `index.html:2580`+, then canvases/exports appended to `main`):
1. Pattern row — 4 groups × 13 buttons (good — already grouped, `2779`).
2. `.texture-sliders` wall, in DOM order: **Seed** row (seed value + Randomize +
   **preset dropdown** + Save Preset + status, `2598-2633`) → Scale/Octaves/
   Count (`2659-2661`) → per-pattern **custom rows** (`2721-2731`) → Roughness/
   Contrast/BumpStrength/LightAngle (`2733-2736`) → "Levels" divider +
   Black/White/Gamma (`2739-2745`) → Invert (`2747-2760`).
3. **Animate** row (Play, Tile Preview, loop slider) — appended to `controls`
   at `3202`, so it renders at the bottom of the control panel.
4. Two preview canvases (`2982-2983`), then a flat row of **five** export
   controls (`3093-3097`), then one long footer paragraph explaining them
   (`3101`).

**Problems for a first-time user**
- One undifferentiated wall of ~14 sliders with a single divider. No sense of
  "start here."
- The **preset dropdown — the fastest path to a good result — is buried** in the
  middle of the Seed row, mixed with Randomize and Save.
- Pattern-specific custom rows (Pitch, Waviness, Stroke Length…) appear inline
  with no signal that they change when you switch pattern.
- **Five export controls with no inline explanation** of Height vs Preview vs
  Normal vs Frames — the only guidance is a small full-width paragraph below.
- The critical "Texture/Height Map = the real data, Bump Preview = just a
  lighting preview, not exported as-is" distinction is buried in that paragraph.

**Target layout** (same panel, add ordered `.section-label` landmarks — the
class already exists at `index.html:124` and is used once for Levels; reuse it).
Build the control panel in this order, each `.section-label`-headed block a
clear step:

1. **`PRESET`** *(new, first — move existing controls up)*
   - Preset dropdown + Save Preset + status (currently `2621-2632`). Move these
     out of the Seed row into their own first section so the newcomer sees
     "load a look" before anything else. Add a one-line helper under it:
     "Start from a preset, then tweak — or build from scratch below." (12px,
     `--muted`.)
2. **`PATTERN`**
   - The grouped pattern buttons (unchanged, already good). Add a one-line
     helper: "Pick a base pattern. Groups: Organic, Geometric, Weathering, Pro
     Finish." Keep Seed value + Randomize here (Seed belongs with pattern
     generation, not presets) — split the current combined Seed row so preset
     controls go to §1 and Seed+Randomize stay here.
3. **`SHAPE`**
   - Scale / Octaves / Count (unchanged show/hide logic via `syncPatternUI`,
     `2768`).
   - Immediately below, a sub-label **`PATTERN OPTIONS`** (a second
     `.section-label`, or a lighter `.pattern-group-label`) heading the
     per-pattern custom rows (`customWraps`, `2720-2731`) so it's obvious these
     depend on the selected pattern. No logic change — just wrap the custom
     container under a labeled sub-heading.
4. **`SURFACE & TONE`**
   - Roughness, Contrast, then Levels (Black/White/Gamma), then Invert. Move
     Bump Strength + Light Angle into §5 (they only affect the relief preview /
     normal-map lighting, not the height data) — OR keep them here but label
     clearly. Recommended: keep the existing "Levels" divider as a sub-label
     inside this section.
5. **`PREVIEW & ANIMATION`**
   - Bump Strength + Light Angle (they drive the Bump Preview + Normal export),
     then the Animate row: Play, loop slider. Move **Tile Preview** here too but
     label it "Tile Preview (QA)" — its `title` tooltip already explains it
     (`3191`); keep that.
6. **Preview canvases** — add a one-line caption under each (12px `--muted`):
   - under "Texture / Height Map": "This is the exportable data."
   - under "Bump Preview (simulated light)": "Lighting preview only — not
     exported as a texture. Adjust Bump Strength / Light Angle above."
7. **`EXPORT`** *(wrap the five controls in a labeled section; add a `title`
   tooltip AND a short caption to each — the footer paragraph text already
   exists, redistribute it):*
   - Group A "Static maps": Export Height/Bump Map PNG (`title`: "The grayscale
     height data — drop into a bump/height slot"), Export Preview Render PNG
     (`title`: "The shaded relief preview as a PNG — visual only, not a texture
     map"), Export Normal Map PNG (`title`: "Tangent-space RGB normal map via
     Sobel — usually preferred over height for surface detail").
   - Group B "Animated": frame-count select + Export Frame Sequence (`title`:
     "Renders one full animation loop as a numbered PNG sequence in a new tab").
   - Keep the existing footer paragraph (`3101`) but cap its width (Lens 1) — it
     becomes the "long-form" backup to the tooltips, not the only explanation.

**Progressive disclosure without hiding anything:** wrap §4 (Surface & Tone) and
§7's advanced/animated export group in `<details open>` blocks so they are
**expanded by default** (nothing hidden on first load) but collapsible for users
who want a shorter panel. Style the `<summary>` like a `.section-label`. Because
they default open, no feature is hidden — this satisfies the "without losing
functionality" constraint literally. Do NOT put Pattern, Shape, or the primary
Height export behind a collapsed disclosure.

**Implementation mechanics:** all of the above is DOM-ordering + a handful of
`.section-label` / caption elements + `title` attributes. The state model,
`syncPatternUI` show/hide, `regenerate()`, presets, and every export handler stay
byte-for-byte. Reorder the `appendChild` sequence and insert label/caption nodes;
change nothing in the generator or export logic.

### 4B — Overlay Asset Customizer

**Current** (`renderCustomize`, `index.html:1536`): Type grid → Subtype grid →
Customize view. Customize shows: full 6-swatch **palette panel**
(`buildPalettePanel`, `1620`) → param controls (Opacity/Thickness/Speed/
Roundness + Reset, `1482`) → optional text field → stage → actions (Replay/
Export PNG/Export Frames) → footer.

**Problems**
- The 6-role palette panel renders on **every** asset's customize screen and
  dominates it, even though most users came to tweak one asset's opacity/speed.
- **"Save Palette" is a dead control in a normal browser** — it calls
  `window.storage` (`1652`) which only exists in a sandbox host, so it shows
  "Storage unavailable" (`1655`). Confusing.

**Plan (ordered, no features removed)**
1. **Make the palette panel collapsible** via `<details>` (default **collapsed**
   here — it IS a rarely-used advanced control, and collapsing ≠ removing).
   Summary label: "Palette (advanced) — recolor all assets". The per-asset
   Opacity/Thickness/Speed/Roundness controls become the primary, always-visible
   controls. This is the one place a *collapsed*-by-default disclosure is
   justified because the panel is genuinely secondary and every control inside
   stays one click away.
2. **Fix the "Save Palette" dead-end.** Either (a) fall back to `localStorage`
   (same pattern the texture presets already use — see the excellent comment at
   proc-gen `index.html:2806-2816` explaining exactly why `window.storage` is
   the wrong API for this app), persisting `palette:default` and reloading it on
   mount; or (b) if you don't want palette persistence, relabel the button and
   its status so it never shows "Storage unavailable" to a normal user.
   Recommended: (a) — it makes the feature actually work in every context, and
   the texture-preset code is a copy-paste-able reference for the localStorage
   wrapper.
3. **Add `title` tooltips** to Opacity/Thickness/Speed/Roundness (one short
   phrase each) and keep the existing play-once hint (`1527-1530`).

---

## What NOT to change

- **No build step, no framework, no dependencies.** `theme.js` must be a single
  vanilla file using only native APIs (matchMedia, localStorage, DOM) — same as
  `menu.js`/`reveal.js`. No bundler, no CSS preprocessor.
- **Relative links only** (`assets/…`, `../assets/…`, `../../assets/…`) — never
  a leading `/`.
- **Do not remove, rename, or hide behind a *collapsed*-by-default disclosure any**
  texture pattern (all 13), export button (Height/Bump, Preview, Normal, Frame
  Sequence + frame count), preset (5 built-ins + user saved), the Tile Preview
  QA toggle, the Animate/loop controls, the palette roles, or the overlay
  per-asset params. Texture-tool advanced sections may use `<details open>`
  (expanded ⇒ nothing hidden). Only the Overlay *palette* panel may default
  collapsed (§4B), because it's genuinely secondary and stays one click away.
- **Do not rewrite the generator or export logic.** Lens 4 is DOM re-ordering +
  labels + tooltips + `<details>` wrappers only. `state`, `computeTextureData`,
  `syncPatternUI`, `regenerate`, all export handlers, and the preset engine stay
  intact.
- **Do not re-plumb proc-gen's `.card` into `.tile`** this pass (§ Lens 2.5) —
  only align the two type values.
- **Keep the palette-role colors recognizable in both themes** (structural =
  blue, fluid = teal, accent = orange). The light-theme values above deepen for
  contrast; do not invent new hues.
- **Do not commit or push.** Do not add PNGs. Update each affected tool's
  `CHANGELOG.md` per repo convention when implementing.

---

## Verification

No test runner in this repo; drive the real pages in headless Edge (pattern from
CLAUDE.md / `ADVANCED_TEXTURES.md` "Build & verification notes":
`msedge.exe --headless=new --disable-gpu --allow-file-access-from-files
--virtual-time-budget=N --dump-dom`; in Git Bash prefix `MSYS2_ARG_CONV_EXCL="*"`
and keep scratch files out of any `AppData\Local\Temp` path). Check:

1. **No-flash theme:** load each of the 4 pages with `localStorage` empty and OS
   set to light, then to dark — first paint must already be the resolved theme
   (dump `documentElement.getAttribute("data-theme")` and a computed `--bg`).
   No dark→light flip on load.
2. **Persistence + override:** click the theme button, reload — the chosen theme
   survives (`localStorage['renkon-theme']` set). Works identically on all 4
   pages (root, proc-gen, keyshot hub, keyshot scripts).
3. **Toggle placement:** the theme button appears inside the `.rk-nav` pill on
   every page (pill = Home + Menu + Theme), and the fallback fires if `.rk-nav`
   is somehow absent.
4. **Contrast:** spot-check `--text`, `--muted`, `--c-accent` against their
   backgrounds in light mode ≥ 4.5:1 for body text (the values above are
   pre-checked; re-verify if you change any).
5. **Customizer coexistence:** open the Overlay Customizer in light mode, change
   a palette swatch — chrome stays light, asset roles reflect the swatch (inline
   override wins, as designed). Switch theme while there — chrome flips, asset
   roles stay as chosen.
6. **Generators lose nothing:** enumerate that all 13 pattern buttons, all 5
   presets, Randomize, Tile Preview, Animate/Play, loop slider, and all 4 export
   buttons + frame-count select are present and functional after the Lens-4
   reorg. Confirm `<details>` sections default **open** (texture tool) and the
   only collapsed-by-default block is the Overlay palette panel.
7. **reveal.js on proc-gen:** confirm content still appears (reveal's 2.5s
   fail-safe means worst case it just shows without animating — never blank).
8. **Regression sweep of the texture tool:** re-run the headless canvas-stats
   check from `ADVANCED_TEXTURES.md` — every pattern still produces non-degenerate,
   NaN-free output, animation frames still differ, exports still open.

---

## Open questions for the implementer

1. **reveal.js on proc-gen (Lens 2.1):** proc-gen builds `main` dynamically via
   its hash-router, and `reveal.js` auto-runs on `DOMContentLoaded`. Decide
   whether to (a) call `window.__rkRunReveal()` at the end of each view render so
   navigations animate, (b) accept reveal animating only the first paint, or (c)
   skip reveal on proc-gen and instead document that proc-gen intentionally
   doesn't use the reveal effect (in which case fix the *inconsistency framing*,
   not the code). Recommended: (a) if cheap, else (b).
2. **`--stage-bg` in light mode (Lens 3.4):** confirmed recommendation is to keep
   preview/relief viewports dark in both themes (a texture/normal preview reads
   best on dark). If the user prefers light-panel previews, flip `--stage-bg`
   light — trivial, but it's an aesthetic call worth confirming with the user.
3. **Overlay "Save Palette" (Lens 4B.2):** confirm the user wants palette
   persistence wired to `localStorage` (option a) vs. just silencing the dead
   "Storage unavailable" message (option b).
