# KeyShot handoff — probe v01

Built 2026-07-26 on the Blender machine. **Open `OPEN_ME.html` in any browser** — it has the same content as this file plus the reference images, and it collects your answers into one block you can paste straight back.

This is the plain-text fallback for a machine where that isn't convenient.

## Import settings

- Import as: Alembic, animated / deforming geometry
- Scene units: **metres** (metres — or it lands 1000x out)
- Up axis: **Z-up**
- Frames: 1-20 (20 frames) @ 24 fps
- Bounding box: roughly 1.5 x 1.2 x 1.0 m -- the scale bar is exactly 1.000 m
- Triangles per frame: probe_a: 604-1,050 faces/frame; probe_b: 644-1,538 faces/frame
- Parts: fluid_surface, fluid_spray, probe_scalebar, probe_triad, probe_ticker
- UVs: none on purpose — use box/triplanar projection
- Motion blur: no velocities in this cache and none possible from Blender 5.0's Alembic exporter. Treat blur as a comp problem, don't hunt for the setting.

## Questions to answer

01. **Does the file import at all?**
    - How: Import probe_a.abc. Alembic / animated geometry. Note any dialog options you had to pick and what the defaults were.
    - Why: Baseline. Everything below assumes this worked.
    - If it fails: If the import errors outright, nothing else matters -- send the error text back and we change transport format entirely.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

02. **Does fluid_surface deform AND change topology across the 20 frames?**
    - How: Scrub frames 1-20. Two lobes (three in probe_b) should slide together and MERGE into one body. Watch for: frozen on frame 1, flickering, or geometry vanishing.
    - Why: THE make-or-break question. Every fluid cache this project produces changes vertex and face count every frame -- that is what a liquid surface is.
    - If it fails: If it is frozen or broken, Alembic is the wrong transport for fluid and we switch to a per-frame mesh sequence. This single answer can redirect the whole project, which is why it is being asked on a 2 MB file.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

03. **Measure probe_scalebar end to end. How long is it?**
    - How: It is exactly 1.000 m, with a tick every 100 mm (taller tick every 500 mm) and a separate 100 mm cube beside it. Measure in KeyShot and write down the number you actually get, not the number you expected.
    - Why: Units are the failure that looks like success -- a pump at 1000x reads as 'a pump'.
    - If it fails: 1.0 -> metres survived, nothing to change. 1000 -> it read millimetres; 0.001 -> the other way. Either way we set the exporter's scale here and stop relying on the import dialog.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

04. **Which way does probe_triad point?**
    - How: Three arms of different lengths: X 0.6 m ends in a CUBE, Y 0.4 m ends in a flat TAB, Z 0.8 m (the longest) ends in a BALL. The ball should point straight up.
    - Why: Asymmetric on purpose. A symmetric marker lets a Z-up/Y-up mix-up look correct from the wrong angle, and then every asset arrives lying on its side.
    - If it fails: If the ball is not up, tell us which arm IS up and we add the axis conversion at export (--yup) rather than making you rotate every import by hand.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

05. **At timeline frame N, where is probe_ticker?**
    - How: A small cube that steps +0.1 m in X once per frame, stepped not smooth. At frame 1 it is at its start, at frame 11 it should be 1.0 m further along. Read off two or three frames.
    - Why: Two answers in one: whether frames map 1:1 (nothing retimed) and whether animated TRANSFORMS are read at all -- the surface tests deformation, this tests transform.
    - If it fails: If the cube never moves but the blobs do, transform animation is ignored and any future moving part (a rotating inducer, a travelling nozzle) has to be baked into the deformation instead. Good to know before we build one.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

06. **Does fluid_spray arrive as droplets, and what does it cost?**
    - How: It is a realised cloud of small spheres -- the same construction the real spray layer uses. Check they are there, and note memory / responsiveness.
    - Why: On cryogenic fuels the spray layer carries the shot; it is not decoration.
    - If it fails: If realised instances are heavy, we lower droplet counts at pack time or split spray into its own file.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

07. **Assign materials to probe_a, then bring in probe_b. Do they stick?**
    - How: Give fluid_surface and fluid_spray any obvious materials in probe_a. Then import or update to probe_b -- same part names, different geometry. Do the materials stay bound, or come in blank? Note exactly which route you used (import / update / replace geometry), because the answer may differ per route.
    - Why: This decides the shape of the entire pipeline. Part names are already generic (fluid_surface / fluid_spray) specifically so one template scene could accept any asset.
    - If it fails: If bindings hold: you build the water material, lighting and camera ONCE, and every future handoff is a file swap -- minutes, not a work session. If they do not: we invest here in making the material numbers trivial to re-enter, and stop pretending a template scene is coming.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

08. **Where does it start to hurt?**
    - How: Rough answer only: at what per-frame triangle count does the viewport or render get unpleasant on that machine? The probe is tiny (a few thousand); the real assets run 25k-200k per frame.
    - Why: abcpack.py budgets polycount with a --budget flag currently set from a guess.
    - If it fails: Whatever number you give becomes the default budget here, permanently.
    - Answer: PASS / FAIL / PARTIAL / SKIPPED —

## What's in the box

- `probe_a.abc` — 2.2 MB — sha256 99419e01b1b6db51…
- `probe_b.abc` — 3.0 MB — sha256 677c6bd88d0bd5e4…
- `probe_kit.json` — 3.6 KB — sha256 7a301d4559d4c902…

**Run `VERIFY.cmd` first.** It re-checks every file against those hashes with no Python and no install. A truncated USB copy and a broken exporter look identical from the KeyShot side, and only one of them is real — rule the copy out before debugging anything else.

## Getting answers back

Easiest, since the drive comes home anyway: in `OPEN_ME.html` hit **Download as .md** and save the file back into this folder on the drive. Back on the Blender machine, everything on the stick gets filed in one go:

```
python handoff.py --collect=<drive>
```

Or use **Copy findings** and paste it into chat, or fill in the Answer lines above and send this file back — then `python handoff.py --intake=<file>`.
