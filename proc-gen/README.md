# proc-gen

Procedural / parametric generation tools for the design + rendering pipeline.
Each tool lives in its own folder and is self-contained.

## Tools

| Tool | What it does | Status |
|---|---|---|
| [`parametric-generators/`](parametric-generators/) | Overlay SVG customizer + texture/bump map generator (single-file browser app). | Active — 44 overlays + static texture maps working; animated maps next. |
| [`label-generator/`](label-generator/) | Placeable render-label decals (fingerprints, scuffs, machining marks) with opacity/bump/spec maps. | Active. |
| [`signage/`](signage/) | Warning stickers, data plates, cert badges, pipe markers, lockout tags — placeable decals. | Active. |
| [`hydroform/`](hydroform/) | Procedural water / jets / fountains + pipe & process-flow — real-time Canvas fluid generator with studio-turntable presentation and PNG export. | Active. |

More tools get added here as they land. Each should carry its own `README.md`
and `CHANGELOG.md`, and use git (not filename suffixes) for versioning.
