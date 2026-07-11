# -*- coding: utf-8 -*-
# AUTHOR tajf
# REV AA01
# Standalone Python 3 script -- NOT a KeyShot script, run this with a regular
# Python interpreter after a batch render (2a_BAT_STD_VIEW_AA01.py) or
# turntable run (2a_BAT_TURNTABLE_AA01.py). It scans an output folder for
# rendered stills ("PartName_View.ext"), groups them by part, and writes one
# self-contained "PartName_fade_reel.html" per part that crossfades through
# that part's Studio/camera views in a continuous loop -- a "turntable fade"
# built from a handful of fixed stills instead of a continuous 360 spin
# video. Pure CSS @keyframes opacity animation, no JS animation loop, no
# external dependencies (no ffmpeg, no PIL, nothing outside the stdlib).
#
# Per RESEARCH_CREO_KEYSHOT.md: crossfading is 2D compositing, not a render
# step, so this consumes stills already produced by 2a_BAT_TURNTABLE /
# 2a_BAT_STD_VIEW rather than changing either of those scripts.
#
# Usage:
#   python 3_PRC_FADE_REEL_AA01.py /path/to/output/folder
# or just run it with no arguments and it'll ask.

import os
import re
import sys
from datetime import datetime

IMAGE_EXTS = ("png", "jpg", "jpeg")

# Common standard-view names get sorted first, in this order; anything else
# falls back to alphabetical. Purely cosmetic -- tweak to your naming.
# Same concept as contact_sheet.py's PREFERRED_VIEW_ORDER, reused here so a
# fade reel and a contact sheet built from the same batch agree on order.
PREFERRED_VIEW_ORDER = ["front", "back", "left", "right", "top", "bottom", "iso", "isometric"]

# --- Crossfade timing, tune to taste -----------------------------------
# HOLD_SECONDS: how long each still stays fully visible before the next
#   crossfade begins. Raise this to give viewers more time to look at each
#   angle; lower it for a snappier cycle.
# FADE_SECONDS: how long the crossfade transition between two stills takes.
#   Must be shorter than HOLD_SECONDS or the hold plateau disappears and
#   adjacent images will overlap oddly.
# Total loop length per image = HOLD_SECONDS + FADE_SECONDS; the full reel
# length is that value times the number of images in the part.
HOLD_SECONDS = 1.8
FADE_SECONDS = 1.2


def viewSortKey(view):
    lower = view.lower()
    if lower in PREFERRED_VIEW_ORDER:
        return (0, PREFERRED_VIEW_ORDER.index(lower))
    return (1, lower)


def scanFolder(folder):
    # Same regex-based grouping-by-part-name approach as contact_sheet.py's
    # scanFolder(), minus the turntable-video handling (out of scope here --
    # this script only fades between stills).
    imagePattern = re.compile(r"^(.+)_([^_]+)\.({})$".format("|".join(IMAGE_EXTS)), re.IGNORECASE)

    parts = {}  # baseName -> [(view, filename), ...]

    for f in sorted(os.listdir(folder)):
        full = os.path.join(folder, f)
        if not os.path.isfile(full):
            continue

        m = imagePattern.match(f)
        if m:
            baseName, view = m.group(1), m.group(2)
            parts.setdefault(baseName, [])
            parts[baseName].append((view, f))

    for baseName in parts:
        parts[baseName].sort(key=lambda pair: viewSortKey(pair[0]))

    return parts


def buildHtmlForPart(folder, baseName, images):
    n = len(images)
    cycleSeconds = (HOLD_SECONDS + FADE_SECONDS) * n
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Each still gets its own @keyframes rule so the hold/fade timing can be
    # expressed as simple percentage offsets into one shared animation
    # duration (cycleSeconds), staggered by animation-delay per layer. This
    # keeps everything pure CSS -- no JS timer, no requestAnimationFrame.
    holdPct = (HOLD_SECONDS / cycleSeconds) * 100.0
    fadePct = (FADE_SECONDS / cycleSeconds) * 100.0

    layers = []
    keyframeBlocks = []
    captions = []
    for i, (view, filename) in enumerate(images):
        delay = -1.0 * i * (HOLD_SECONDS + FADE_SECONDS)  # negative delay = starts mid-cycle, pre-synced
        animName = "fadeLayer{}".format(i)

        # Timeline for a single layer, in percent of the shared cycle:
        #   0%            -> hidden (opacity 0)
        #   just before holdPct -> still hidden, ramps up to 1 over fadePct
        #   through holdPct+fadePct -> fully visible (opacity 1)
        #   ramps back to 0 over the following fadePct
        #   stays hidden for the rest of the cycle
        fadeInEndPct = fadePct
        holdEndPct = fadePct + holdPct
        fadeOutEndPct = holdEndPct + fadePct

        keyframeBlocks.append(
            "@keyframes {name} {{\n"
            "  0% {{ opacity: 0; }}\n"
            "  {fadeInEndPct:.3f}% {{ opacity: 1; }}\n"
            "  {holdEndPct:.3f}% {{ opacity: 1; }}\n"
            "  {fadeOutEndPct:.3f}% {{ opacity: 0; }}\n"
            "  100% {{ opacity: 0; }}\n"
            "}}".format(
                name=animName,
                fadeInEndPct=fadeInEndPct,
                holdEndPct=holdEndPct,
                fadeOutEndPct=fadeOutEndPct,
            )
        )

        layers.append(
            '<img class="layer" src="{filename}" alt="{view}" '
            'style="animation-name:{animName}; animation-duration:{cycleSeconds}s; '
            'animation-delay:{delay}s; z-index:{z};">'.format(
                filename=filename,
                view=view,
                animName=animName,
                cycleSeconds=cycleSeconds,
                delay=delay,
                z=i,
            )
        )
        captions.append('<span class="tag">{}</span>'.format(view))

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Fade Reel -- {baseName}</title>
<style>
  :root {{
    --bg: #111111;
    --panel: #1a1a1a;
    --border: #333333;
    --text: #d8d8d8;
    --muted: #888888;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: "IBM Plex Mono", "SF Mono", Consolas, monospace;
    margin: 0;
    padding: 32px;
  }}
  header {{
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
    margin-bottom: 32px;
  }}
  h1 {{
    font-size: 16px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin: 0 0 8px 0;
  }}
  .stats {{
    color: var(--muted);
    font-size: 12px;
  }}
  .stage {{
    position: relative;
    background: #000000;
    border: 1px solid var(--border);
    width: 640px;
    max-width: 100%;
    height: 640px;
    overflow: hidden;
  }}
  .layer {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    opacity: 0;
    animation-iteration-count: infinite;
    animation-timing-function: linear;
  }}
  .tags {{
    margin-top: 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .tag {{
    display: inline-block;
    border: 1px solid var(--border);
    background: var(--panel);
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 4px 8px;
  }}
{keyframeBlocks}
</style>
</head>
<body>
<header>
  <h1>Fade Reel -- {baseName}</h1>
  <div class="stats">{n} views &middot; {holdSeconds:.1f}s hold / {fadeSeconds:.1f}s fade &middot; {cycleSeconds:.1f}s full loop &middot; generated {generated}</div>
</header>
<div class="stage">
{layers}
</div>
<div class="tags">{captions}</div>
</body>
</html>
""".format(
        baseName=baseName,
        n=n,
        holdSeconds=HOLD_SECONDS,
        fadeSeconds=FADE_SECONDS,
        cycleSeconds=cycleSeconds,
        generated=generated,
        keyframeBlocks="\n".join(keyframeBlocks),
        layers="\n".join(layers),
        captions="".join(captions),
    )
    return html


def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("Folder to scan for renders: ").strip()

    if not os.path.isdir(folder):
        print("Not a folder: {}".format(folder))
        sys.exit(1)

    parts = scanFolder(folder)
    # A fade needs at least two stills to crossfade between.
    parts = {baseName: images for baseName, images in parts.items() if len(images) >= 2}

    if not parts:
        print("No parts with 2+ renders matching 'PartName_View.ext' found in {}".format(folder))
        sys.exit(1)

    written = []
    for baseName in sorted(parts.keys()):
        images = parts[baseName]
        html = buildHtmlForPart(folder, baseName, images)
        outPath = os.path.join(folder, "{}_fade_reel.html".format(baseName))
        with open(outPath, "w", encoding="utf-8") as fh:
            fh.write(html)
        written.append((baseName, len(images), outPath))

    print("Wrote {} fade reel(s):".format(len(written)))
    for baseName, count, outPath in written:
        print("  {} ({} views) -> {}".format(baseName, count, outPath))


if __name__ == "__main__":
    main()
