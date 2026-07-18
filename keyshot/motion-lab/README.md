# KeyShot Motion Lab

A single-file browser tool for comparing four motion concepts side by side, so
the team can pick a direction before committing to a deeper build. This is a
**direction-finding / comparison viewer, not a finished export tool** &mdash;
there is no render pipeline, no download button, nothing to ship. Just four
looping Canvas prototypes running at once so you can trust your gut.

## The four concepts

- **1. Fluid Orbit Loop** (loop / ambient) &mdash; fluid ribbons, drifting
  highlights, an orbital ring and a subtle starfield. Best for hero
  backgrounds; soft, premium, endlessly loopable.
- **2. Reactor Flow Loop** (loop / industrial) &mdash; glowing conduits, pipe
  motion, pulse trains and a reactor-core center. Heavier, more architectural,
  better for machinery.
- **3. Orbital Parallax Hero** (presentation / hero) &mdash; camera-like drift
  across layered parallax planes, slow ring movement and nebula haze. Reads
  like a cinematic product-deck hero.
- **4. Studio Sweep Cinematic** (presentation / premium) &mdash; slow softbox
  light sweeps, a glassy floor reflection and clean negative space for product
  storytelling.

The first two are animated backplates (loop and forget); the second two are
presentation motion (deliberate camera feel, compositional storytelling).

## How it works

Each concept is a plain `requestAnimationFrame` loop driving a `<canvas
width="960" height="540">` with 2D context drawing &mdash; no CSS animation, no
Web Animations API, no SMIL. A shared clock (`performance.now()` minus a
resettable `startTime`) feeds all four draw functions each frame, so **Pause
all** / **Resume all** freezes every concept in lockstep and **Reset demos**
rewinds them together. Each card's **Fullscreen** button re-targets the same
draw function at a second, larger canvas inside a modal (Esc or click-outside
to close) &mdash; same math, bigger canvas, no separate rendering path.

## Files

- `index.html` &mdash; the tool (self-contained; the only external references
  are the two brand fonts).

No build step. Open `index.html` in a browser, or serve it under the RENKON
Pages base &mdash; relative links only.
