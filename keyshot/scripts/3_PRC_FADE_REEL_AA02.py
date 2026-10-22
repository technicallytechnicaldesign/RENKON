                       
            
          
                                                                             
                                                                      
                                                                         
                                                                            
                                                                           
                                                                            
                                                                       
                                                                        
                                                                        
 
                                                                            
                                                                      
                                                               
 
        
                                                         
                                                 

import os
import re
import sys
from datetime import datetime

IMAGE_EXTS = ("png", "jpg", "jpeg")

                                                                           
                                                                      
                                                                           
                                                                         
PREFERRED_VIEW_ORDER = ["front", "back", "left", "right", "top", "bottom", "iso", "isometric"]

                                                                         
                                                                       
                                                                          
                                         
                                                                           
                                                                        
                                       
                                                                          
                                                              
HOLD_SECONDS = 1.8
FADE_SECONDS = 1.2


def viewSortKey(view):
    lower = view.lower()
    if lower in PREFERRED_VIEW_ORDER:
        return (0, PREFERRED_VIEW_ORDER.index(lower))
    return (1, lower)


def scanFolder(folder):
                                                                           
                                                                            
                                             
    imagePattern = re.compile(r"^(.+)_([^_]+)\.({})$".format("|".join(IMAGE_EXTS)), re.IGNORECASE)

    parts = {}                                       

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

                                                                            
                                                                      
                                                                           
                                                                         
    holdPct = (HOLD_SECONDS / cycleSeconds) * 100.0
    fadePct = (FADE_SECONDS / cycleSeconds) * 100.0

    layers = []
    keyframeBlocks = []
    captions = []
    for i, (view, filename) in enumerate(images):
        delay = -1.0 * i * (HOLD_SECONDS + FADE_SECONDS)                                                 
        animName = "fadeLayer{}".format(i)

                                                                      
                                               
                                                                           
                                                                
                                                      
                                                  
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
