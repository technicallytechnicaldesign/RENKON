# -*- coding: utf-8 -*-
# AUTHOR tajf
# REV AA01
# Standalone Python 3 script -- NOT a KeyShot script, run this with a regular
# Python interpreter after a batch render or turntable run. It scans an
# output folder for rendered stills ("PartName_View.ext") and turntable
# videos ("PartName_turntable.mp4"), groups them by part, and writes a single
# contact_sheet.html so you can eyeball an entire batch in one scroll instead
# of opening files one by one.
#
# Usage:
#   python contact_sheet.py /path/to/output/folder
# or just run it with no arguments and it'll ask.

import os
import re
import sys
from datetime import datetime

IMAGE_EXTS = ("png", "jpg", "jpeg")
VIDEO_EXTS = ("mp4",)

# Common standard-view names get sorted first, in this order; anything else
# falls back to alphabetical. Purely cosmetic -- tweak to your naming.
PREFERRED_VIEW_ORDER = ["front", "back", "left", "right", "top", "bottom", "iso", "isometric"]

def viewSortKey(view):
    lower = view.lower()
    if lower in PREFERRED_VIEW_ORDER:
        return (0, PREFERRED_VIEW_ORDER.index(lower))
    return (1, lower)

def scanFolder(folder):
    imagePattern = re.compile(r"^(.+)_([^_]+)\.({})$".format("|".join(IMAGE_EXTS)), re.IGNORECASE)
    videoPattern = re.compile(r"^(.+)_turntable\.({})$".format("|".join(VIDEO_EXTS)), re.IGNORECASE)

    parts = {}  # baseName -> {"images": [(view, filename)], "video": filename or None}

    for f in sorted(os.listdir(folder)):
        full = os.path.join(folder, f)
        if not os.path.isfile(full):
            continue

        m = videoPattern.match(f)
        if m:
            baseName = m.group(1)
            parts.setdefault(baseName, {"images": [], "video": None})
            parts[baseName]["video"] = f
            continue

        m = imagePattern.match(f)
        if m:
            baseName, view = m.group(1), m.group(2)
            parts.setdefault(baseName, {"images": [], "video": None})
            parts[baseName]["images"].append((view, f))
            continue

    for baseName in parts:
        parts[baseName]["images"].sort(key=lambda pair: viewSortKey(pair[0]))

    return parts

def buildHtml(folder, parts):
    totalParts = len(parts)
    totalImages = sum(len(p["images"]) for p in parts.values())
    totalVideos = sum(1 for p in parts.values() if p["video"])
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = []
    for baseName in sorted(parts.keys()):
        part = parts[baseName]
        thumbs = []
        for view, filename in part["images"]:
            thumbs.append(
                '<figure class="thumb">'
                '<img src="{filename}" loading="lazy" alt="{view}">'
                '<figcaption>{view}</figcaption>'
                '</figure>'.format(filename=filename, view=view)
            )
        videoBlock = ""
        if part["video"]:
            videoBlock = (
                '<figure class="thumb video">'
                '<video src="{filename}" autoplay loop muted playsinline></video>'
                '<figcaption>turntable</figcaption>'
                '</figure>'.format(filename=part["video"])
            )
        sections.append(
            '<section class="part">'
            '<h2>{baseName}</h2>'
            '<div class="grid">{videoBlock}{thumbs}</div>'
            '</section>'.format(baseName=baseName, videoBlock=videoBlock, thumbs="".join(thumbs))
        )

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Contact Sheet -- {folder}</title>
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
  .part {{
    margin-bottom: 40px;
  }}
  .part h2 {{
    font-size: 13px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin-bottom: 16px;
  }}
  .grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }}
  .thumb {{
    background: var(--panel);
    border: 1px solid var(--border);
    margin: 0;
    padding: 6px;
    width: 220px;
  }}
  .thumb img, .thumb video {{
    display: block;
    width: 100%;
    height: 160px;
    object-fit: contain;
    background: #000000;
  }}
  .thumb.video {{
    border-color: #555555;
  }}
  figcaption {{
    font-size: 11px;
    color: var(--muted);
    text-align: center;
    padding-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
</style>
</head>
<body>
<header>
  <h1>Contact Sheet</h1>
  <div class="stats">{totalParts} parts &middot; {totalImages} stills &middot; {totalVideos} turntables &middot; generated {generated}</div>
</header>
{sections}
</body>
</html>
""".format(
        folder=folder,
        totalParts=totalParts,
        totalImages=totalImages,
        totalVideos=totalVideos,
        generated=generated,
        sections="".join(sections),
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
    if not parts:
        print("No renders matching 'PartName_View.ext' or 'PartName_turntable.mp4' found in {}".format(folder))
        sys.exit(1)

    html = buildHtml(folder, parts)
    outPath = os.path.join(folder, "contact_sheet.html")
    with open(outPath, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("Wrote {} ({} parts)".format(outPath, len(parts)))

if __name__ == "__main__":
    main()
