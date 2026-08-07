# Web pickup (no USB needed)

Web fallback for when the USB transfer is not available. This is an unchanged copy
of the probe handoff kit; the authoritative original lives outside this repo.

## Open the checklist in the browser, do not download it

https://technicallytechnicaldesign.github.io/RENKON/keyshot/fluid-probe-v01/OPEN_ME.html

Pages serves it live, so the eight questions and the **Copy findings** button work straight
in the browser. There is nothing to install and nothing to save.

## Download only these two

Right click, Save link as. They are binary, so let the browser save them as-is.

- https://raw.githubusercontent.com/technicallytechnicaldesign/RENKON/main/keyshot/fluid-probe-v01/probe_a.abc  (2.3 MB)
- https://raw.githubusercontent.com/technicallytechnicaldesign/RENKON/main/keyshot/fluid-probe-v01/probe_b.abc  (3.2 MB)

Put them anywhere you can reach from KeyShot's import dialog. They are throwaway.

## Skip VERIFY.cmd this time

`VERIFY.cmd` and `CHECKSUMS.txt` exist to catch a **USB copy that silently went wrong**, which
is a real failure mode for a drive and not one for an HTTPS download. If you would rather run it
anyway, you need every file in this folder in one place first, and the hashes will match because
these are byte copies. Otherwise ignore it.

## The two questions that matter

**02, does the topology survive**, and **04, the KeyShot performance read**. Both are guesses
right now and both redirect real work on the home machine. **07** (do material bindings survive a
cache swap) is the one that decides whether the fuel matrix is five file swaps in one template
scene or five looks rebuilt by hand, so it is worth the extra minutes if you have them.

`probe_a` and `probe_b` deliberately share part names (`fluid_surface`, `fluid_spray`). Swapping
one for the other in KeyShot is the whole of question 07.

## Getting the answers home

Hit **Copy findings** on the page and paste it into whatever reaches the home machine. There is no
drive to carry it back on this time, so nothing is collected automatically.
