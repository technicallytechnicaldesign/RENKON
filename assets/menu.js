/* RENKON unified nav — one self-contained script, dropped into every page.
 *
 * - Resolves all links relative to the repo root from its own <script src>,
 *   so it works at any page depth AND both locally (file://) and under the
 *   /RENKON/ GitHub Pages base.
 * - Injects its own styles + DOM; no external CSS, no dependencies.
 * - Home is always one click (accent button) or the `H` hotkey. Other areas
 *   live behind a playful pop-out menu. Esc / click-outside closes it.
 *
 * Add to a page with:  <script src="<path-to>/assets/menu.js"></script>
 */
(function () {
  if (window.__renkonNav) return;            // guard against double-inject
  window.__renkonNav = true;

  var me = document.currentScript;
  var root = new URL("..", new URL(".", me.src)); // assets/ -> repo root
  var u = function (p) { return new URL(p, root).href; };

  // --- icons (inline SVG, currentColor) ---------------------------------
  var I = {
    home:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11.5 12 4l8 7.5"/><path d="M6 10v9h12v-9"/><path d="M10 19v-5h4v5"/></svg>',
    paramgen:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="7" x2="21" y2="7"/><circle cx="8" cy="7" r="2.4" fill="var(--panel-bg,#0d1520)"/><line x1="3" y1="12" x2="21" y2="12"/><circle cx="15" cy="12" r="2.4" fill="var(--panel-bg,#0d1520)"/><line x1="3" y1="17" x2="21" y2="17"/><circle cx="11" cy="17" r="2.4" fill="var(--panel-bg,#0d1520)"/></svg>',
    keyshot: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M12 3 L20 7.5 V16 L12 21 L4 16 V7.5 Z"/><path d="M12 3 V12 M12 12 L20 7.5 M12 12 L4 7.5" opacity="0.5"/></svg>',
    github:  '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.85 9.73.5.1.68-.22.68-.49l-.01-1.7c-2.79.62-3.38-1.222-3.38-1.222-.45-1.18-1.11-1.494-1.11-1.494-.91-.635.07-.622.07-.622 1 .072 1.53 1.05 1.53 1.05.9 1.573 2.36 1.118 2.93.855.09-.665.35-1.119.63-1.376-2.22-.259-4.56-1.138-4.56-5.065 0-1.119.39-2.034 1.03-2.75-.1-.26-.45-1.303.1-2.716 0 0 .84-.275 2.75 1.05a9.34 9.34 0 0 1 2.5-.343c.85.004 1.71.117 2.5.343 1.91-1.325 2.75-1.05 2.75-1.05.55 1.413.2 2.456.1 2.716.64.716 1.03 1.631 1.03 2.75 0 3.937-2.34 4.803-4.57 5.057.36.32.68.947.68 1.909l-.01 2.831c0 .27.18.6.69.49A10.02 10.02 0 0 0 22 12.25C22 6.58 17.52 2 12 2Z"/></svg>',
    grid:    '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="7" cy="7" r="1.8"/><circle cx="17" cy="7" r="1.8"/><circle cx="7" cy="17" r="1.8"/><circle cx="17" cy="17" r="1.8"/></svg>',
    ext:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 5h5v5"/><path d="M19 5l-8 8"/><path d="M18 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4"/></svg>'
  };

  // --- destinations ------------------------------------------------------
  var LINKS = [
    { key: "home",     label: "Homebase",              href: u("index.html"),                                icon: I.home },
    { key: "paramgen", label: "Parametric Generators", href: u("proc-gen/parametric-generators/index.html"), icon: I.paramgen },
    { key: "keyshot",  label: "KeyShot",               href: u("keyshot/index.html"),                        icon: I.keyshot },
    { key: "github",   label: "GitHub",                href: "https://github.com/technicallytechnicaldesign/RENKON", icon: I.github, external: true }
  ];
  var homeHref = LINKS[0].href;

  var norm = function (p) { return p.replace(/index\.html$/, "").replace(/\/$/, ""); };
  var here = norm(location.pathname);
  LINKS.forEach(function (l) {
    if (!l.external) try { l.current = norm(new URL(l.href).pathname) === here; } catch (e) {}
  });

  // --- styles ------------------------------------------------------------
  var css = ''
    + '.rk-nav{position:fixed;top:14px;right:16px;z-index:9999;'
    + 'font-family:"IBM Plex Mono","Courier New",monospace;display:flex;gap:8px;align-items:flex-start}'
    + '.rk-nav *{box-sizing:border-box}'
    + '.rk-btn{-webkit-appearance:none;appearance:none;cursor:pointer;border:1px solid var(--line,#1c2733);'
    + 'background:var(--panel-bg,#0d1520);color:var(--text,#e8e8e0);width:40px;height:40px;padding:8px;'
    + 'display:flex;align-items:center;justify-content:center;border-radius:0;'
    + 'transition:transform .18s cubic-bezier(.34,1.56,.64,1),background .15s,border-color .15s,box-shadow .15s}'
    + '.rk-btn svg{width:22px;height:22px;display:block}'
    + '.rk-btn:hover{transform:translateY(-2px)}'
    + '.rk-btn:active{transform:translateY(0) scale(.92)}'
    + '.rk-btn:focus-visible{outline:2px solid var(--c-accent,#E8792E);outline-offset:2px}'
    + '.rk-home{background:var(--c-accent,#E8792E);border-color:var(--c-accent,#E8792E);color:#0a0f16}'
    + '.rk-home:hover{box-shadow:0 6px 18px -6px var(--c-accent,#E8792E)}'
    + '.rk-home svg{transition:transform .18s cubic-bezier(.34,1.56,.64,1)}'
    + '.rk-home:hover svg{transform:translateY(-2px)}'
    + '.rk-menu-btn[aria-expanded="true"]{border-color:var(--c-accent,#E8792E);color:var(--c-accent,#E8792E)}'
    + '.rk-pop{position:absolute;top:48px;right:0;min-width:220px;background:var(--panel-bg,#0d1520);'
    + 'border:1px solid var(--line,#1c2733);transform-origin:top right;'
    + 'opacity:0;transform:scale(.9) translateY(-6px);pointer-events:none;'
    + 'transition:opacity .16s ease,transform .18s cubic-bezier(.34,1.56,.64,1)}'
    + '.rk-pop.open{opacity:1;transform:scale(1) translateY(0);pointer-events:auto}'
    + '.rk-item{display:flex;align-items:center;gap:12px;padding:11px 14px;color:var(--text,#e8e8e0);'
    + 'text-decoration:none;font-size:12px;letter-spacing:.04em;border-top:1px solid var(--line,#1c2733);'
    + 'transition:background .12s,color .12s,padding-left .12s}'
    + '.rk-item:first-child{border-top:none}'
    + '.rk-item .ic{width:18px;height:18px;color:var(--muted,#7a7f83);flex:none;transition:color .12s}'
    + '.rk-item .ic svg{width:18px;height:18px;display:block}'
    + '.rk-item .lbl{flex:1}'
    + '.rk-item .ext{width:13px;height:13px;color:var(--muted,#7a7f83);opacity:.6}'
    + '.rk-item .ext svg{width:13px;height:13px;display:block}'
    + '.rk-item:hover,.rk-item:focus-visible{background:var(--panel-bg-raised,#101a27);outline:none;padding-left:18px}'
    + '.rk-item:hover .ic,.rk-item:focus-visible .ic{color:var(--c-accent,#E8792E)}'
    + '.rk-item.current{color:var(--c-accent,#E8792E)}'
    + '.rk-item.current .ic{color:var(--c-accent,#E8792E)}'
    + '.rk-item .dot{width:6px;height:6px;border-radius:50%;background:var(--c-accent,#E8792E);flex:none;'
    + 'box-shadow:0 0 8px var(--c-accent,#E8792E)}'
    + '.rk-hint{padding:9px 14px;border-top:1px solid var(--line,#1c2733);color:var(--muted,#7a7f83);'
    + 'font-size:9px;letter-spacing:.1em;text-transform:uppercase}'
    + '.rk-hint kbd{border:1px solid var(--line,#1c2733);padding:1px 5px;color:var(--text,#e8e8e0);'
    + 'font-family:inherit;font-size:9px}'
    + '@media (prefers-reduced-motion:reduce){.rk-btn,.rk-home svg,.rk-pop,.rk-item{transition:none}'
    + '.rk-btn:hover,.rk-home:hover svg{transform:none}}'
    + '@media (max-width:480px){.rk-nav{top:10px;right:10px}}';

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // --- DOM ---------------------------------------------------------------
  var nav = document.createElement("nav");
  nav.className = "rk-nav";
  nav.setAttribute("aria-label", "RENKON navigation");

  var home = document.createElement("a");
  home.className = "rk-btn rk-home";
  home.href = homeHref;
  home.title = "Homebase (H)";
  home.setAttribute("aria-label", "Go to homebase");
  home.innerHTML = I.home;
  if (LINKS[0].current) home.setAttribute("aria-current", "page");

  var toggle = document.createElement("button");
  toggle.className = "rk-btn rk-menu-btn";
  toggle.type = "button";
  toggle.title = "Menu";
  toggle.setAttribute("aria-label", "Open menu");
  toggle.setAttribute("aria-expanded", "false");
  toggle.setAttribute("aria-haspopup", "true");
  toggle.innerHTML = I.grid;

  var pop = document.createElement("div");
  pop.className = "rk-pop";
  pop.setAttribute("role", "menu");

  LINKS.forEach(function (l) {
    var a = document.createElement("a");
    a.className = "rk-item" + (l.current ? " current" : "");
    a.href = l.href;
    a.setAttribute("role", "menuitem");
    if (l.external) { a.target = "_blank"; a.rel = "noopener"; }
    if (l.current) a.setAttribute("aria-current", "page");
    a.innerHTML =
      '<span class="ic" aria-hidden="true">' + l.icon + "</span>" +
      '<span class="lbl">' + l.label + "</span>" +
      (l.current ? '<span class="dot" aria-hidden="true"></span>'
                 : l.external ? '<span class="ext" aria-hidden="true">' + I.ext + "</span>" : "");
    pop.appendChild(a);
  });

  var hint = document.createElement("div");
  hint.className = "rk-hint";
  hint.innerHTML = "<kbd>H</kbd> homebase &middot; <kbd>Esc</kbd> close";
  pop.appendChild(hint);

  var wrap = document.createElement("div");
  wrap.style.position = "relative";
  wrap.appendChild(toggle);
  wrap.appendChild(pop);

  nav.appendChild(home);
  nav.appendChild(wrap);

  // --- behavior ----------------------------------------------------------
  var open = false;
  function setOpen(v) {
    open = v;
    pop.classList.toggle("open", v);
    toggle.setAttribute("aria-expanded", v ? "true" : "false");
    toggle.setAttribute("aria-label", v ? "Close menu" : "Open menu");
  }
  toggle.addEventListener("click", function (e) { e.stopPropagation(); setOpen(!open); });
  document.addEventListener("click", function (e) { if (open && !nav.contains(e.target)) setOpen(false); });
  document.addEventListener("keydown", function (e) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
    var t = e.target, tag = t && t.tagName;
    var typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable);
    if (e.key === "Escape") { if (open) setOpen(false); return; }
    if (typing) return;
    if (e.key === "h" || e.key === "H") { location.href = homeHref; }
  });

  // On the toolkit page, hide its header's right-side mark so the pill sits clean.
  function mount() {
    document.body.appendChild(nav);
    var mark = document.querySelector("#app-header .mark");
    if (mark) mark.style.display = "none";
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
