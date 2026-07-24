/* RENKON reveal — "technical document coming alive" on load.
 *
 * Loaded in <head> (synchronously) so its CSS is in the CSSOM before the body
 * paints — no flash of un-animated content. Each heading gets a short accent
 * connector line that draws downward, then the heading fades up; cards/tiles
 * fade in on the same staggered timeline, in document order.
 *
 * Fail-safe: <main> is hidden only under html.rk-anim, and a CSS keyframe force-
 * reveals it after 2.5s, so if this script errors or is blocked, content still
 * appears. Respects prefers-reduced-motion (no hiding, no animation).
 *
 * Coordination: exposes window.__rkRunReveal(); auto-runs on DOMContentLoaded
 * unless window.__rkDeferReveal is set (the landing splash sets it, then calls
 * __rkRunReveal() when the portal finishes).
 */
(function () {
  var reduce = false;
  try { reduce = matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  if (!reduce) {
    document.documentElement.className += " rk-anim";
    var css =
      "html.rk-anim main{opacity:0;animation:rkFail .01s linear 2.5s forwards}" +
      "html.rk-anim main.rk-ready{opacity:1;animation:none}" +
      "@keyframes rkFail{to{opacity:1}}" +
      "html.rk-anim [data-rk-reveal]{opacity:0;transform:translateY(8px)}" +
      "html.rk-anim [data-rk-reveal].rk-in{opacity:1;transform:none;" +
      "transition:opacity .5s ease,transform .55s cubic-bezier(.2,.7,.3,1)}" +
      ".rk-conn{display:block;width:1px;height:0;background:var(--c-accent,#E8792E);" +
      "margin:0 0 10px 1px;opacity:.85}" +
      ".rk-conn.rk-grow{height:22px;transition:height .3s cubic-bezier(.4,0,.2,1)}";
    var style = document.createElement("style");
    style.textContent = css;
    (document.head || document.documentElement).appendChild(style);
  }

  var ran = false;
  function run() {
    if (ran) return; ran = true;
    var main = document.querySelector("main");
    if (!main) return;
    if (reduce) { main.classList.add("rk-ready"); return; }

    // Headings get a connector line; cards/tiles just fade in. Only the page
    // title reveals — headings that live inside a tool's control panel/columns
    // (e.g. hydroform's in-panel "Water Generator" h2) are skipped so every
    // generator gets the same single title-connector intro instead of an
    // inconsistent extra line where a panel happens to use an <h2>.
    var heads = [].slice.call(main.querySelectorAll("h1,h2,h3"))
      .filter(function (el) { return !el.closest(".tile,.card,.panel,.controls,.col,.param-panel"); });
    var cards = [].slice.call(main.querySelectorAll(".tile,.card"));

    heads.forEach(function (h) {
      h.setAttribute("data-rk-reveal", "");
      var c = document.createElement("i");
      c.className = "rk-conn";
      c.setAttribute("aria-hidden", "true");
      h.parentNode.insertBefore(c, h);
      h._rkConn = c;
    });
    cards.forEach(function (c) { c.setAttribute("data-rk-reveal", ""); });

    main.classList.add("rk-ready"); // reveal the container (children still hidden)

    var items = heads.map(function (el) { return { kind: "h", el: el }; })
      .concat(cards.map(function (el) { return { kind: "c", el: el }; }));
    items.sort(function (a, b) {
      return (a.el.compareDocumentPosition(b.el) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
    });

    items.forEach(function (it, i) {
      setTimeout(function () {
        if (it.kind === "h") {
          it.el._rkConn.classList.add("rk-grow");
          setTimeout(function () { it.el.classList.add("rk-in"); }, 240);
        } else {
          it.el.classList.add("rk-in");
        }
      }, i * 90);
    });
  }

  window.__rkRunReveal = run;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      if (!window.__rkDeferReveal) run();
    });
  } else if (!window.__rkDeferReveal) {
    run();
  }
})();
