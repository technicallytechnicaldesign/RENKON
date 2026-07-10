# keyshot

KeyShot automation and scene assets. Empty for now — files get dropped in as
they arrive, and the folder gets structured once there's enough to structure.

Live placeholder page: [`index.html`](index.html).

## What lives here (eventually)

- **Scripts** — Python 3.10+ automation using the `lux` / `luxmath` modules
  (scene setup, material assignment, batch renders). Headless CLI execution is
  supported.
- **Scene / material binaries** — `.bip`, `.ksp`, `.kmtp`, etc. Tracked via
  Git LFS (see root `.gitattributes`). Name versions clearly (`chair_v3.bip`) —
  binary scene files can't be meaningfully diffed or merged.

## Notes

- Headless automation needs a machine with a **licensed KeyShot install**;
  GitHub-hosted Actions runners can't run it.
- Install `git lfs` (`git lfs install`) before committing any binary scene
  files, or the LFS pointers won't be generated.
