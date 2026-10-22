                                                                             
                                                                           
                                                      
                                                                       
                                                                       
                                                                           
                                                                      
                                                                           
                                                       
   
(function () {
  if (window.__renkonTheme) return;
  window.__renkonTheme = true;

  var KEY = "renkon-theme";
  var root = document.documentElement;

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function prefersLight() {
    try { return matchMedia("(prefers-color-scheme: light)").matches; } catch (e) { return false; }
  }
  function resolve() {
    var s = stored();
    return (s === "light" || s === "dark") ? s : (prefersLight() ? "light" : "dark");
  }
  function apply(theme) { root.setAttribute("data-theme", theme); }

                                                                                 
  apply(resolve());
  var css =
    ':root[data-theme="light"]{' +
      '--bg:#f4f6f8;--panel-bg:#ffffff;--panel-bg-raised:#eef1f4;' +
      '--line:#d3dbe2;--text:#16202b;--muted:#5c666e;' +
      '--c-structural:#002F67;--c-fluid:#1f8b93;--c-accent:#c6591a;' +
                                                                           
      '--c-leader:#3a4653;--c-panel-base:#e7edf3;--c-panel:rgba(231,237,243,0.92);--c-label:#16202b;' +
    '}' +
                                                                       
    ':root{--stage-bg:#060a10}' +
    ':root[data-theme="light"]{--stage-bg:#0d1520}' +
                                                                      
                                                                         
                                                           
    'button.rk-item{background:none;border:none;-webkit-appearance:none;appearance:none;' +
      'margin:0;width:100%;text-align:left;font:inherit;cursor:pointer;display:flex;' +
      'align-items:center;gap:12px;padding:11px 14px;color:var(--text,#e8e8e0);font-size:12px;' +
      'letter-spacing:.04em;border-top:1px solid var(--line,#1c2733);' +
      'transition:background .12s,color .12s,padding-left .12s}' +
    'button.rk-item:first-child{border-top:none}' +
    'button.rk-item:hover,button.rk-item:focus-visible{background:var(--panel-bg-raised,#101a27);' +
      'outline:none;padding-left:18px}' +
    'button.rk-item:hover .ic,button.rk-item:focus-visible .ic{color:var(--c-accent,#E8792E)}';
  var st = document.createElement("style");
  st.id = "rk-theme-style";
  st.textContent = css;
  (document.head || root).appendChild(st);

  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>';
  function isLight() { return root.getAttribute("data-theme") === "light"; }
  function toggleTheme() {
    var next = isLight() ? "dark" : "light";
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
  }

                                                                          
                                                                  
                                                                          
                                                         
  function mountBtn() {
    var pop = document.querySelector(".rk-pop");
    var nav = document.querySelector(".rk-nav");

    if (pop) {
      var item = document.createElement("button");
      item.type = "button";
      item.className = "rk-item rk-theme-item";
      item.setAttribute("role", "menuitem");
      function paintItem() {
        item.innerHTML =
          '<span class="ic" aria-hidden="true">' + (isLight() ? MOON : SUN) + '</span>' +
          '<span class="lbl">' + (isLight() ? "Switch to dark mode" : "Switch to light mode") + '</span>';
      }
      paintItem();
      item.addEventListener("click", function (e) { e.stopPropagation(); toggleTheme(); paintItem(); });
      pop.insertBefore(item, pop.firstChild);
      return;
    }

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "rk-btn rk-theme-btn";                                   
    btn.setAttribute("aria-label", "Toggle light / dark theme");
    btn.title = "Toggle theme";
    function paintBtn() { btn.innerHTML = isLight() ? MOON : SUN; }
    paintBtn();
    btn.addEventListener("click", function () { toggleTheme(); paintBtn(); });
    if (nav) nav.appendChild(btn);
    else {
      btn.style.cssText = "position:fixed;top:10px;right:12px;z-index:9999";
      document.body.appendChild(btn);
    }
  }
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", mountBtn);
  else mountBtn();
})();
