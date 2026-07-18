# blender

Blender (`bpy`) pipeline scripts — tools that run headless *inside Blender*,
not inside KeyShot or a browser, to produce assets that feed downstream into
KeyShot. Kept separate from `keyshot/` because nothing here runs via
KeyShot's own `lux`/`luxmath` API or follows its script-naming convention;
separate from `proc-gen/` because these aren't browser apps. Each tool lives
in its own folder and is self-contained.

## Tools

| Tool | What it does | Status |
|---|---|---|
| [`fluid-cache-gen/`](fluid-cache-gen/) | Bakes fluid Alembic (`.abc`) caches for KeyShot import — real Mantaflow FLIP sims (`fluidgen.py`) or cheap procedural surfaces (`make_fluids.py`). | Unverified — no Blender in this environment; needs a real Blender 4.x smoke-test before production use. |

More tools get added here as they land. Each should carry its own `README.md`
and `CHANGELOG.md`, and use git (not filename suffixes) for versioning. There
is no build step and no browser page for this area — these scripts are
invoked directly by Blender's `-P` flag on a machine that has it installed.
