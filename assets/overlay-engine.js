/* RENKON overlay engine — the shared overlay asset library (single source of
 * truth) plus a standalone rasterizer. Consumed by both the Overlay Asset
 * Customizer (proc-gen/parametric-generators) and Mockup Studio.
 *
 * window.RENKON_OVERLAYS : the asset array. Each asset's svg(rid, speedMult)
 *   returns a self-contained SVG string using CSS-var colours + --t-mult /
 *   --s-mult / --r-mult, so it renders anywhere the vars are provided.
 * window.OverlayEngine    : preRenderFrames() etc. for canvas consumers.
 *
 * No build step, no dependencies — a plain global-attaching script, loaded
 * before each host page's own script.
 */

window.RENKON_OVERLAYS = [
    {
      id: "flow-straight", name: "Straight Run", file: "flow_straight.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "smil", loop: true, durationMs: 1100,
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const pat = "fst_pat_" + rid;
        const dur = (1.1 / speedMult).toFixed(3);
        return `<svg viewBox="0 0 480 100" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<defs>
<style>
  .fst_pipe { stroke: var(--c-structural); stroke-width: calc(3 * var(--t-mult,1)); fill: none; }
  .fst_fill { fill: url(#${pat}); }
</style>
<pattern id="${pat}" width="40" height="60" patternUnits="userSpaceOnUse">
  <rect width="40" height="60" fill="#12151700" />
  <path d="M4,10 L20,30 L4,50" fill="none" stroke="var(--c-fluid)" stroke-width="calc(6 * var(--t-mult,1))"
        stroke-linecap="round" stroke-linejoin="round" opacity="0.9" />
  <animateTransform xlink:href="#${pat}" attributeName="patternTransform"
    attributeType="XML" type="translate" from="0 0" to="40 0"
    dur="${dur}s" repeatCount="indefinite" />
</pattern>
</defs>
<line class="fst_pipe" x1="0" y1="20" x2="480" y2="20" />
<line class="fst_pipe" x1="0" y1="80" x2="480" y2="80" />
<rect x="0" y="20" width="480" height="60" class="fst_fill" />
</svg>`;
      }
    },
    {
      id: "flow-elbow", name: "Elbow / Curved Run", file: "flow_elbow.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 900,
      svg(rid) {
        return `<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fel_wall { fill: none; stroke: var(--c-structural); stroke-width: calc(34 * var(--t-mult,1)); stroke-linecap: round; }
  .fel_dash { fill: none; stroke: var(--c-fluid); stroke-width: calc(10 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 0.05 0.055; animation: fel_march_${rid} 0.9s linear infinite;
    animation-duration: calc(0.9s / var(--s-mult,1)); }
  @keyframes fel_march_${rid} { to { stroke-dashoffset: -0.21; } }
</style></defs>
<path class="fel_wall" d="M40,260 L40,140 Q40,40 140,40 L260,40" />
<path class="fel_dash" pathLength="1" d="M40,260 L40,140 Q40,40 140,40 L260,40" />
</svg>`;
      }
    },
    {
      id: "flow-pulse-wave", name: "Traveling Pulse", file: "flow_pulse_wave.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "smil", loop: true, durationMs: 1800,
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const grad = "fpw_grad_" + rid;
        const dur = (1.8 / speedMult).toFixed(3);
        return `<svg viewBox="0 0 400 100" xmlns="http://www.w3.org/2000/svg">
<defs>
<radialGradient id="${grad}" cx="50%" cy="50%" r="50%">
  <stop offset="0%" style="stop-color:#8FE3E0; stop-opacity:0.95" />
  <stop offset="100%" style="stop-color:var(--c-fluid); stop-opacity:0" />
</radialGradient>
<style>
  .fpw_tube { fill: none; stroke: var(--c-structural); stroke-width: calc(40 * var(--t-mult,1)); stroke-linecap: round; }
  .fpw_inner { fill: none; stroke: #001A33; stroke-width: calc(30 * var(--t-mult,1)); stroke-linecap: round; }
</style>
</defs>
<path id="fpw_path_${rid}" class="fpw_tube" d="M20,50 L380,50" />
<path class="fpw_inner" d="M20,50 L380,50" />
<ellipse data-role="motion-target" rx="26" ry="13" fill="url(#${grad})">
  <animateMotion dur="${dur}s" repeatCount="indefinite" path="M20,50 L380,50" rotate="auto" />
</ellipse>
</svg>`;
      }
    },
    {
      id: "flow-chevron-unit", name: "Static Chevron", file: "flow_chevron_unit.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "static", loop: false, durationMs: 0,
      svg() {
        return `<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
<path d="M14,10 L44,30 L14,50" fill="none" style="stroke:var(--c-fluid)"
      stroke-width="calc(8 * var(--t-mult,1))" stroke-linecap="round" stroke-linejoin="round" />
</svg>`;
      }
    },
    {
      id: "flow-spiral-vortex", name: "Spiral Vortex", file: "flow_spiral_vortex.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 3000,
      svg(rid) {
        return `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fsv_ring { fill: none; stroke: var(--c-fluid); stroke-width: calc(3 * var(--t-mult,1)); stroke-dasharray: 10 14;
    transform-box: fill-box; transform-origin: center; animation: fsv_spin_${rid} 3s linear infinite;
    animation-duration: calc(3s / var(--s-mult,1)); }
  .fsv_ring2 { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); stroke-dasharray: 6 10;
    transform-box: fill-box; transform-origin: center; animation: fsv_spinrev_${rid} 1.8s linear infinite;
    animation-duration: calc(1.8s / var(--s-mult,1)); }
  .fsv_core { fill: var(--c-accent); transform-box: fill-box; transform-origin: center;
    animation: fsv_pulse_${rid} 1.2s ease-in-out infinite; animation-duration: calc(1.2s / var(--s-mult,1)); }
  @keyframes fsv_spin_${rid} { to { transform: rotate(360deg); } }
  @keyframes fsv_spinrev_${rid} { to { transform: rotate(-360deg); } }
  @keyframes fsv_pulse_${rid} { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(0.35); opacity: 0.4; } }
</style></defs>
<circle class="fsv_ring" cx="60" cy="60" r="40" />
<circle class="fsv_ring2" cx="60" cy="60" r="24" />
<circle class="fsv_core" cx="60" cy="60" r="5" />
</svg>`;
      }
    },
    {
      id: "flow-branch-split", name: "Branch Split", file: "flow_branch_split.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 900,
      svg(rid) {
        return `<svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fbs_wall { fill: none; stroke: var(--c-structural); stroke-width: calc(22 * var(--t-mult,1)); stroke-linecap: round; }
  .fbs_dash { fill: none; stroke: var(--c-fluid); stroke-width: calc(7 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 0.05 0.06; animation: fbs_march_${rid} 0.9s linear infinite;
    animation-duration: calc(0.9s / var(--s-mult,1)); }
  @keyframes fbs_march_${rid} { to { stroke-dashoffset: -0.22; } }
</style></defs>
<path class="fbs_wall" d="M100,150 L100,90 Q100,68 80,54 L38,22" />
<path class="fbs_wall" d="M100,90 Q100,68 120,54 L162,22" />
<path class="fbs_dash" pathLength="1" d="M100,150 L100,90 Q100,68 80,54 L38,22" />
<path class="fbs_dash" pathLength="1" d="M100,90 Q100,68 120,54 L162,22" />
</svg>`;
      }
    },
    {
      id: "flow-surge-pulse-bar", name: "Surge Pulse Bar", file: "flow_surge_pulse_bar.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2000, roundable: true,
      svg(rid) {
        return `<svg viewBox="0 0 60 140" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fpb_frame { fill: none; stroke: var(--c-structural); stroke-width: calc(3 * var(--t-mult,1));
    rx: var(--r-mult,0); ry: var(--r-mult,0); }
  .fpb_fill { fill: var(--c-fluid); rx: var(--r-mult,0); ry: var(--r-mult,0);
    transform-box: fill-box; transform-origin: bottom;
    animation: fpb_surge_${rid} 2s ease-in-out infinite; animation-duration: calc(2s / var(--s-mult,1)); }
  .fpb_tick { stroke: var(--c-leader); stroke-width: calc(1.5 * var(--t-mult,1)); }
  @keyframes fpb_surge_${rid} { 0%,100% { transform: scaleY(0.28); } 50% { transform: scaleY(0.85); } }
</style></defs>
<rect class="fpb_frame" x="10" y="10" width="40" height="120" />
<rect class="fpb_fill" x="14" y="14" width="32" height="112" />
<line class="fpb_tick" x1="4" y1="70" x2="10" y2="70" />
<line class="fpb_tick" x1="50" y1="70" x2="56" y2="70" />
</svg>`;
      }
    },
    {
      id: "flow-droplet-stream", name: "Droplet Stream", file: "flow_droplet_stream.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "smil", loop: true, durationMs: 1500,
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const dur = (1.5 / speedMult).toFixed(3);
        const path = "M10,40 Q60,10 110,40 T210,40";
        const begins = [0, dur / 3, (2 * dur) / 3];
        const particle = (i) => `<g class="fds_p" data-role="motion-target">
  <path d="M-7,-6 L5,0 L-7,6 Z" />
  <animateMotion dur="${dur}s" repeatCount="indefinite" begin="${begins[i]}s" path="${path}" rotate="auto" />
</g>`;
        return `<svg viewBox="0 0 220 80" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fds_guide { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); stroke-dasharray: 3 5; opacity: 0.5; }
  .fds_p path { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1)); }
</style></defs>
<path class="fds_guide" d="${path}" />
${particle(0)}${particle(1)}${particle(2)}
</svg>`;
      }
    },
    {
      id: "flow-manifold-merge", name: "Manifold Merge", file: "flow_manifold_merge.svg", category: "Fluid Flow",
      tags: { fn: ["flow", "direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1000,
      svg(rid) {
        // Converse of Branch Split: three inlets collect into one header run.
        return `<svg viewBox="0 0 210 160" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fmm_wall { fill: none; stroke: var(--c-structural); stroke-width: calc(16 * var(--t-mult,1)); stroke-linecap: round; }
  .fmm_head { fill: none; stroke: var(--c-structural); stroke-width: calc(22 * var(--t-mult,1)); stroke-linecap: round; }
  .fmm_dash { fill: none; stroke: var(--c-fluid); stroke-width: calc(5 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 0.05 0.06; animation: fmm_m_${rid} 1s linear infinite; animation-duration: calc(1s / var(--s-mult,1)); }
  .fmm_dash.hd { stroke-width: calc(8 * var(--t-mult,1)); }
  @keyframes fmm_m_${rid} { to { stroke-dashoffset: -0.22; } }
</style></defs>
<path class="fmm_wall" d="M10,25 C70,25 78,80 120,80" />
<path class="fmm_wall" d="M10,80 L120,80" />
<path class="fmm_wall" d="M10,135 C70,135 78,80 120,80" />
<path class="fmm_head" d="M120,80 L200,80" />
<path class="fmm_dash" pathLength="1" d="M10,25 C70,25 78,80 120,80" />
<path class="fmm_dash" pathLength="1" d="M10,80 L120,80" />
<path class="fmm_dash" pathLength="1" d="M10,135 C70,135 78,80 120,80" />
<path class="fmm_dash hd" pathLength="1" d="M120,80 L200,80" />
</svg>`;
      }
    },
    {
      id: "callout-leader-label", name: "Leader + Label", file: "callout_leader_label.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 950, roundable: true,
      hasText: true, textDefault: "LABEL_01", textHint: "Leader label text",
      svg(rid) {
        return `<svg viewBox="0 0 320 120" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cll_anchor { fill: var(--c-accent); }
  .cll_tick { stroke: var(--c-accent); stroke-width: calc(2 * var(--t-mult,1)); }
  .cll_leader { fill: none; stroke: var(--c-leader); stroke-width: calc(2 * var(--t-mult,1));
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: cll_draw_${rid} 0.6s ease-out forwards;
    animation-duration: calc(0.6s / var(--s-mult,1)); }
  .cll_panel { fill: var(--c-panel); stroke: var(--c-leader); stroke-width: calc(1 * var(--t-mult,1));
    rx: var(--r-mult,0); ry: var(--r-mult,0);
    opacity: 0; animation: cll_fadeUp_${rid} 0.4s ease-out 0.5s forwards;
    animation-duration: calc(0.4s / var(--s-mult,1)); animation-delay: calc(0.5s / var(--s-mult,1)); }
  .cll_label { font-family: "Space Mono","Courier New",monospace; font-size: 14px; fill: var(--c-label);
    opacity: 0; animation: cll_fadeUp_${rid} 0.4s ease-out 0.55s forwards;
    animation-duration: calc(0.4s / var(--s-mult,1)); animation-delay: calc(0.55s / var(--s-mult,1)); }
  @keyframes cll_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes cll_fadeUp_${rid} { from { opacity:0; transform: translateY(6px);} to { opacity:1; transform: translateY(0);} }
</style></defs>
<circle class="cll_anchor" cx="20" cy="100" r="4" />
<line class="cll_tick" x1="12" y1="92" x2="28" y2="108" />
<path class="cll_leader" pathLength="1" d="M20,100 L70,60 L140,60" />
<rect class="cll_panel" x="140" y="38" width="150" height="44" />
<text class="cll_label" data-text-slot="true" x="152" y="65">LABEL_01</text>
</svg>`;
      }
    },
    {
      id: "callout-ping-marker", name: "Ping Marker", file: "callout_ping_marker.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1600,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cpm_ring { fill: none; stroke: var(--c-accent); stroke-width: calc(2 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center; animation: cpm_ping_${rid} 1.6s ease-out infinite;
    animation-duration: calc(1.6s / var(--s-mult,1)); }
  .cpm_r2 { animation-delay: calc(0.53s / var(--s-mult,1)); }
  .cpm_r3 { animation-delay: calc(1.06s / var(--s-mult,1)); }
  .cpm_dot { fill: var(--c-accent); }
  @keyframes cpm_ping_${rid} { 0% { transform: scale(0.3); opacity: 0.9; } 100% { transform: scale(2.2); opacity: 0; } }
</style></defs>
<circle class="cpm_ring" cx="50" cy="50" r="10" />
<circle class="cpm_ring cpm_r2" cx="50" cy="50" r="10" />
<circle class="cpm_ring cpm_r3" cx="50" cy="50" r="10" />
<circle class="cpm_dot" cx="50" cy="50" r="4" />
</svg>`;
      }
    },
    {
      id: "callout-numbered-badge", name: "Numbered Badge", file: "callout_numbered_badge.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 850, roundable: true,
      hasText: true, textDefault: "01", textHint: "Badge number — keep short, it's a small chip",
      svg(rid) {
        return `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cnb_anchor { fill: var(--c-accent); }
  .cnb_leader { fill: none; stroke: var(--c-leader); stroke-width: calc(2 * var(--t-mult,1));
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: cnb_draw_${rid} 0.5s ease-out forwards;
    animation-duration: calc(0.5s / var(--s-mult,1)); }
  .cnb_badge { fill: var(--c-accent); stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1));
    rx: var(--r-mult,0); ry: var(--r-mult,0);
    transform-box: fill-box; transform-origin: center; transform: scale(0); opacity: 0;
    animation: cnb_pop_${rid} 0.35s cubic-bezier(.2,1.4,.4,1) 0.45s forwards;
    animation-duration: calc(0.35s / var(--s-mult,1)); animation-delay: calc(0.45s / var(--s-mult,1)); }
  .cnb_num { font-family: "Space Mono","Courier New",monospace; font-size: 16px; font-weight: 600;
    fill: var(--c-structural); text-anchor: middle; dominant-baseline: central;
    opacity: 0; animation: cnb_fadeIn_${rid} 0.2s linear 0.65s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.65s / var(--s-mult,1)); }
  @keyframes cnb_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes cnb_pop_${rid} { to { transform: scale(1); opacity: 1; } }
  @keyframes cnb_fadeIn_${rid} { to { opacity: 1; } }
</style></defs>
<circle class="cnb_anchor" cx="15" cy="80" r="4" />
<path class="cnb_leader" pathLength="1" d="M15,80 L60,30 L100,30" />
<rect class="cnb_badge" x="100" y="15" width="30" height="30" />
<text class="cnb_num" data-text-slot="true" x="115" y="31">01</text>
</svg>`;
      }
    },
    {
      id: "callout-bracket-dimension", name: "Bracket Dimension", file: "callout_bracket_dimension.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 800, roundable: true,
      hasText: true, textDefault: "250 L/MIN", textHint: "Dimension value, e.g. a flow rate or diameter",
      svg(rid) {
        return `<svg viewBox="0 0 300 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cbd_tick { stroke: var(--c-leader); stroke-width: calc(2 * var(--t-mult,1)); opacity: 0;
    animation: cbd_fadeIn_${rid} 0.2s linear 0.55s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.55s / var(--s-mult,1)); }
  .cbd_line { fill: none; stroke: var(--c-leader); stroke-width: calc(2 * var(--t-mult,1));
    stroke-dasharray: 0.5; stroke-dashoffset: 0.5; animation: cbd_drawOut_${rid} 0.5s ease-out forwards;
    animation-duration: calc(0.5s / var(--s-mult,1)); }
  .cbd_bg { fill: var(--c-panel); rx: var(--r-mult,0); ry: var(--r-mult,0); opacity: 0;
    animation: cbd_fadeIn_${rid} 0.15s linear 0.5s forwards;
    animation-duration: calc(0.15s / var(--s-mult,1)); animation-delay: calc(0.5s / var(--s-mult,1)); }
  .cbd_label { font-family: "Space Mono","Courier New",monospace; font-size: 14px; fill: var(--c-label);
    text-anchor: middle; opacity: 0; animation: cbd_fadeIn_${rid} 0.2s linear 0.6s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.6s / var(--s-mult,1)); }
  @keyframes cbd_drawOut_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes cbd_fadeIn_${rid} { to { opacity: 1; } }
</style></defs>
<line class="cbd_tick" x1="20" y1="40" x2="20" y2="60" />
<line class="cbd_tick" x1="280" y1="40" x2="280" y2="60" />
<path class="cbd_line" pathLength="0.5" d="M20,50 L124,50" />
<path class="cbd_line" pathLength="0.5" d="M176,50 L280,50" />
<rect class="cbd_bg" x="122" y="36" width="56" height="28" />
<text class="cbd_label" data-text-slot="true" x="150" y="55">250 L/MIN</text>
</svg>`;
      }
    },
    {
      id: "callout-underline-emphasis", name: "Underline Emphasis", file: "callout_underline_emphasis.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 400,
      svg(rid) {
        return `<svg viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cue_tick { stroke: var(--c-accent); stroke-width: calc(2.5 * var(--t-mult,1)); }
  .cue_line { fill: none; stroke: var(--c-accent); stroke-width: calc(4 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: cue_draw_${rid} 0.4s ease-out forwards;
    animation-duration: calc(0.4s / var(--s-mult,1)); }
  @keyframes cue_draw_${rid} { to { stroke-dashoffset: 0; } }
</style></defs>
<line class="cue_tick" x1="20" y1="14" x2="20" y2="26" />
<path class="cue_line" pathLength="1" d="M20,34 L180,34" />
</svg>`;
      }
    },
    {
      id: "callout-magnify-lens", name: "Magnify Lens", file: "callout_magnify_lens.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 600,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cml_grp { transform-box: fill-box; transform-origin: 42px 42px; transform: scale(0); opacity: 0;
    animation: cml_pop_${rid} 0.4s cubic-bezier(.2,1.6,.4,1) forwards; animation-duration: calc(0.4s / var(--s-mult,1)); }
  .cml_lens { fill: none; stroke: var(--c-accent); stroke-width: calc(4 * var(--t-mult,1)); }
  .cml_handle { stroke: var(--c-accent); stroke-width: calc(5 * var(--t-mult,1)); stroke-linecap: round; }
  .cml_glint { stroke: var(--c-label); stroke-width: calc(2.5 * var(--t-mult,1)); stroke-linecap: round;
    opacity: 0; animation: cml_flash_${rid} 0.5s ease-out 0.35s forwards; animation-duration: calc(0.5s / var(--s-mult,1));
    animation-delay: calc(0.35s / var(--s-mult,1)); }
  @keyframes cml_pop_${rid} { to { transform: scale(1); opacity: 1; } }
  @keyframes cml_flash_${rid} { 0% { opacity: 0; } 40% { opacity: 0.9; } 100% { opacity: 0; } }
</style></defs>
<g class="cml_grp">
<circle class="cml_lens" cx="42" cy="42" r="26" />
<line class="cml_handle" x1="62" y1="62" x2="86" y2="86" />
<path class="cml_glint" d="M28,20 L36,28" />
</g>
</svg>`;
      }
    },
    {
      id: "callout-flag-marker", name: "Flag Marker", file: "callout_flag_marker.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1600,
      svg(rid) {
        return `<svg viewBox="0 0 60 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .cfm_pole { stroke: var(--c-structural); stroke-width: calc(3 * var(--t-mult,1)); stroke-linecap: round; }
  .cfm_base { fill: var(--c-structural); }
  .cfm_flag { fill: var(--c-accent); transform-box: fill-box; transform-origin: left center;
    animation: cfm_wave_${rid} 1.6s ease-in-out infinite; animation-duration: calc(1.6s / var(--s-mult,1)); }
  @keyframes cfm_wave_${rid} { 0%,100% { transform: skewY(0deg); } 50% { transform: skewY(9deg); } }
</style></defs>
<line class="cfm_pole" x1="14" y1="10" x2="14" y2="90" />
<circle class="cfm_base" cx="14" cy="92" r="3" />
<path class="cfm_flag" d="M14,12 L44,20 L14,28 Z" />
</svg>`;
      }
    },
    {
      id: "callout-tooltip-bubble", name: "Tooltip Bubble", file: "callout_tooltip_bubble.svg", category: "Callouts",
      tags: { fn: ["label", "point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 600, roundable: true,
      hasText: true, textDefault: "TOOLTIP", textHint: "Short tooltip text",
      svg(rid) {
        return `<svg viewBox="0 0 220 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .ctb_grp { transform-box: fill-box; transform-origin: 40px 80px; transform: scale(0); opacity: 0;
    animation: ctb_pop_${rid} 0.35s cubic-bezier(.2,1.5,.4,1) forwards; animation-duration: calc(0.35s / var(--s-mult,1)); }
  .ctb_tail { fill: var(--c-panel); }
  .ctb_bubble { fill: var(--c-panel); stroke: var(--c-leader); stroke-width: calc(1 * var(--t-mult,1));
    rx: var(--r-mult,6); ry: var(--r-mult,6); }
  .ctb_label { font-family: "Space Mono","Courier New",monospace; font-size: 15px; fill: var(--c-label); text-anchor: middle; }
</style></defs>
<g class="ctb_grp">
<path class="ctb_tail" d="M40,70 L26,92 L54,70 Z" />
<rect class="ctb_bubble" x="20" y="14" width="180" height="56" />
<text class="ctb_label" data-text-slot="true" x="110" y="47">TOOLTIP</text>
</g>
</svg>`;
      }
    },
    {
      id: "callout-status-chip", name: "Status Chip", file: "callout_status_chip.svg", category: "Callouts",
      tags: { fn: ["label", "point", "state"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1600, roundable: true,
      hasText: true, textDefault: "STATUS: OK", textHint: "Chip text",
      svg(rid) {
        return `<svg viewBox="0 0 220 60" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .csc_chip { fill: var(--c-panel); stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1));
    rx: var(--r-mult,0); ry: var(--r-mult,0); }
  .csc_led { fill: var(--c-caution); animation: csc_blink_${rid} 1.6s ease-in-out infinite;
    animation-duration: calc(1.6s / var(--s-mult,1)); }
  .csc_halo { fill: none; stroke: var(--c-caution); stroke-width: calc(1.5 * var(--t-mult,1));
    animation: csc_halo_${rid} 1.6s ease-out infinite; animation-duration: calc(1.6s / var(--s-mult,1));
    transform-box: fill-box; transform-origin: center; }
  .csc_txt { fill: var(--c-label); font: 600 15px "Courier New", monospace; letter-spacing: 1px; }
  @keyframes csc_blink_${rid} { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }
  @keyframes csc_halo_${rid} { 0% { transform: scale(1); opacity: 0.8; } 100% { transform: scale(2.4); opacity: 0; } }
</style></defs>
<rect class="csc_chip" x="8" y="12" width="204" height="36" />
<circle class="csc_halo" cx="30" cy="30" r="5" />
<circle class="csc_led" cx="30" cy="30" r="5" />
<text class="csc_txt" data-text-slot="true" x="48" y="35">STATUS: OK</text>
</svg>`;
      }
    },
    {
      id: "arrow-directional-single", name: "Directional Single", file: "arrow_directional_single.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 650,
      svg(rid) {
        return `<svg viewBox="0 0 160 80" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .ads_shaft { fill: none; stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: ads_draw_${rid} 0.45s ease-out forwards;
    animation-duration: calc(0.45s / var(--s-mult,1)); }
  .ads_head { fill: none; stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round; stroke-linejoin: round;
    transform-box: fill-box; transform-origin: center; transform: scale(0); opacity: 0;
    animation: ads_pop_${rid} 0.25s cubic-bezier(.2,1.5,.4,1) 0.4s forwards;
    animation-duration: calc(0.25s / var(--s-mult,1)); animation-delay: calc(0.4s / var(--s-mult,1)); }
  @keyframes ads_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes ads_pop_${rid} { to { transform: scale(1); opacity: 1; } }
</style></defs>
<path class="ads_shaft" pathLength="1" d="M10,40 L112,40" />
<path class="ads_head" d="M104,20 L134,40 L104,60" />
</svg>`;
      }
    },
    {
      id: "arrow-curved-redirect", name: "Curved Redirect", file: "arrow_curved_redirect.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 800,
      svg(rid) {
        return `<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .acr_shaft { fill: none; stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: acr_draw_${rid} 0.6s ease-out forwards;
    animation-duration: calc(0.6s / var(--s-mult,1)); }
  .acr_head { fill: none; stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round; stroke-linejoin: round;
    transform-box: fill-box; transform-origin: center; transform: scale(0); opacity: 0;
    animation: acr_pop_${rid} 0.25s cubic-bezier(.2,1.5,.4,1) 0.55s forwards;
    animation-duration: calc(0.25s / var(--s-mult,1)); animation-delay: calc(0.55s / var(--s-mult,1)); }
  @keyframes acr_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes acr_pop_${rid} { to { transform: scale(1); opacity: 1; } }
</style></defs>
<path class="acr_shaft" pathLength="1" d="M30,130 Q30,30 120,30" />
<path class="acr_head" d="M100,14 L128,30 L108,52" />
</svg>`;
      }
    },
    {
      id: "arrow-bidirectional", name: "Bidirectional", file: "arrow_bidirectional.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1600,
      svg(rid) {
        return `<svg viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .ab_grp { transform-box: fill-box; transform-origin: center; animation: ab_breathe_${rid} 1.6s ease-in-out infinite;
    animation-duration: calc(1.6s / var(--s-mult,1)); }
  .ab_shaft { stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round; }
  .ab_head { fill: none; stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round; stroke-linejoin: round; }
  @keyframes ab_breathe_${rid} { 0%,100% { transform: scaleX(1); } 50% { transform: scaleX(1.06); } }
</style></defs>
<g class="ab_grp">
<line class="ab_shaft" x1="42" y1="30" x2="158" y2="30" />
<path class="ab_head" d="M52,14 L26,30 L52,46" />
<path class="ab_head" d="M148,14 L174,30 L148,46" />
</g>
</svg>`;
      }
    },
    {
      id: "arrow-spin-orbit", name: "Spin Orbit", file: "arrow_spin_orbit.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2400,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .aso_spin { transform-box: fill-box; transform-origin: center; animation: aso_rotate_${rid} 2.4s linear infinite;
    animation-duration: calc(2.4s / var(--s-mult,1)); }
  .aso_arc { fill: none; stroke: var(--c-accent); stroke-width: calc(6 * var(--t-mult,1)); stroke-linecap: round; }
  .aso_head { fill: var(--c-accent); }
  @keyframes aso_rotate_${rid} { to { transform: rotate(360deg); } }
</style></defs>
<g class="aso_spin">
<path class="aso_arc" d="M50,14 A36,36 0 1,1 17.5,68" />
<path class="aso_head" d="M8,60 L22,70 L27,54 Z" />
</g>
</svg>`;
      }
    },
    {
      id: "arrow-cluster-fan", name: "Cluster Fan", file: "arrow_cluster_fan.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 700,
      svg(rid) {
        const arrow = (angle, delay) => `<g transform="translate(24,60) rotate(${angle})">
  <path class="acf_shaft" pathLength="1" d="M0,0 L70,0"
    style="animation-delay: calc(${delay}s / var(--s-mult,1));" />
  <path class="acf_head" d="M60,-11 L80,0 L60,11 Z"
    style="animation-delay: calc(${delay + 0.15}s / var(--s-mult,1));" />
</g>`;
        return `<svg viewBox="0 0 140 120" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .acf_shaft { fill: none; stroke: var(--c-accent); stroke-width: calc(5 * var(--t-mult,1)); stroke-linecap: round;
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: acf_draw_${rid} 0.35s ease-out forwards;
    animation-duration: calc(0.35s / var(--s-mult,1)); }
  .acf_head { fill: var(--c-accent); opacity: 0; transform-box: fill-box; transform-origin: center; transform: scale(0);
    animation: acf_pop_${rid} 0.2s ease-out forwards; animation-duration: calc(0.2s / var(--s-mult,1)); }
  @keyframes acf_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes acf_pop_${rid} { to { transform: scale(1); opacity: 1; } }
</style></defs>
${arrow(-30, 0)}${arrow(0, 0.1)}${arrow(30, 0.2)}
</svg>`;
      }
    },
    {
      id: "arrow-zigzag-path", name: "Zigzag Path", file: "arrow_zigzag_path.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 650,
      svg(rid) {
        return `<svg viewBox="0 0 160 80" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .azp_shaft { fill: none; stroke: var(--c-accent); stroke-width: calc(5 * var(--t-mult,1));
    stroke-linecap: round; stroke-linejoin: miter;
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: azp_draw_${rid} 0.45s ease-out forwards;
    animation-duration: calc(0.45s / var(--s-mult,1)); }
  .azp_head { fill: var(--c-accent); transform-box: fill-box; transform-origin: center; transform: scale(0); opacity: 0;
    animation: azp_pop_${rid} 0.2s cubic-bezier(.2,1.6,.4,1) 0.4s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.4s / var(--s-mult,1)); }
  @keyframes azp_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes azp_pop_${rid} { to { transform: scale(1); opacity: 1; } }
</style></defs>
<path class="azp_shaft" pathLength="1" d="M10,60 L40,20 L70,60 L100,20 L122,44" />
<path class="azp_head" d="M116,30 L136,44 L116,58 Z" />
</svg>`;
      }
    },
    {
      id: "arrow-chevron-stack", name: "Chevron Stack", file: "arrow_chevron_stack.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1200,
      svg(rid) {
        return `<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .acs_c { fill: none; stroke: var(--c-accent); stroke-width: calc(7 * var(--t-mult,1));
    stroke-linecap: round; stroke-linejoin: round; opacity: 0.25;
    animation: acs_pulse_${rid} 1.2s ease-in-out infinite; animation-duration: calc(1.2s / var(--s-mult,1)); }
  .acs_c2 { animation-delay: calc(0.15s / var(--s-mult,1)); }
  .acs_c3 { animation-delay: calc(0.3s / var(--s-mult,1)); }
  @keyframes acs_pulse_${rid} { 0%,100% { opacity: 0.25; } 50% { opacity: 1; } }
</style></defs>
<path class="acs_c" d="M20,20 L40,40 L20,60" />
<path class="acs_c acs_c2" d="M32,20 L52,40 L32,60" />
<path class="acs_c acs_c3" d="M44,20 L64,40 L44,60" />
</svg>`;
      }
    },
    {
      id: "arrow-press-fit", name: "Press Fit", file: "arrow_press_fit.svg", category: "Arrows",
      tags: { fn: ["direction"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2200,
      svg(rid) {
        // Opposed arrows converge on a seam, squash on contact, reset. Assembly / press-fit / clamping.
        return `<svg viewBox="0 0 240 80" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .apf_seam { stroke: var(--c-leader); stroke-width: calc(1.5 * var(--t-mult,1)); stroke-dasharray: 5 4; }
  .apf_a { fill: var(--c-accent); animation-duration: calc(2.2s / var(--s-mult,1)) !important; }
  .apf_l { transform-box: fill-box; transform-origin: right center; animation: apf_left_${rid} 2.2s ease-in-out infinite; }
  .apf_r { transform-box: fill-box; transform-origin: left center; animation: apf_right_${rid} 2.2s ease-in-out infinite; }
  @keyframes apf_left_${rid} {
    0% { transform: translateX(-42px); opacity: 0; } 18% { opacity: 1; }
    38% { transform: translateX(0) scaleX(1); } 48% { transform: translateX(0) scaleX(0.8); }
    62% { transform: translateX(0) scaleX(1); } 85% { opacity: 1; } 100% { transform: translateX(-42px); opacity: 0; } }
  @keyframes apf_right_${rid} {
    0% { transform: translateX(42px); opacity: 0; } 18% { opacity: 1; }
    38% { transform: translateX(0) scaleX(1); } 48% { transform: translateX(0) scaleX(0.8); }
    62% { transform: translateX(0) scaleX(1); } 85% { opacity: 1; } 100% { transform: translateX(42px); opacity: 0; } }
</style></defs>
<line class="apf_seam" x1="120" y1="8" x2="120" y2="72" />
<path class="apf_a apf_l" d="M20,32 L84,32 L84,22 L112,40 L84,58 L84,48 L20,48 Z" />
<path class="apf_a apf_r" d="M220,32 L156,32 L156,22 L128,40 L156,58 L156,48 L220,48 Z" />
</svg>`;
      }
    },
    {
      id: "ping-crosshair", name: "Crosshair", file: "ping_crosshair.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2200,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .pcr_ring { fill: none; stroke: var(--c-accent); stroke-width: calc(2 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center; animation: pcr_pulse_${rid} 2.2s ease-in-out infinite;
    animation-duration: calc(2.2s / var(--s-mult,1)); }
  .pcr_tick { stroke: var(--c-accent); stroke-width: calc(2 * var(--t-mult,1)); }
  .pcr_dot { fill: var(--c-accent); }
  @keyframes pcr_pulse_${rid} { 0%,100% { opacity:.55; transform: scale(1);} 50% { opacity:1; transform: scale(1.05);} }
</style></defs>
<circle class="pcr_ring" cx="50" cy="50" r="22" />
<line class="pcr_tick" x1="50" y1="18" x2="50" y2="28" />
<line class="pcr_tick" x1="50" y1="72" x2="50" y2="82" />
<line class="pcr_tick" x1="18" y1="50" x2="28" y2="50" />
<line class="pcr_tick" x1="72" y1="50" x2="82" y2="50" />
<circle class="pcr_dot" cx="50" cy="50" r="3" />
</svg>`;
      }
    },
    {
      id: "ping-scan-sweep", name: "Scan Sweep", file: "ping_scan_sweep.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2000,
      svg(rid) {
        const grad = "pss_grad_" + rid;
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs>
<radialGradient id="${grad}" cx="0%" cy="0%" r="100%">
  <stop offset="0%" style="stop-color:var(--c-fluid); stop-opacity:0.85" />
  <stop offset="100%" style="stop-color:var(--c-fluid); stop-opacity:0" />
</radialGradient>
<style>
  .pss_ring { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); }
  .pss_sweep { transform-box: fill-box; transform-origin: 50px 50px; animation: pss_rotate_${rid} 2s linear infinite;
    animation-duration: calc(2s / var(--s-mult,1)); }
  .pss_dot { fill: var(--c-accent); }
  @keyframes pss_rotate_${rid} { to { transform: rotate(360deg); } }
</style>
</defs>
<circle class="pss_ring" cx="50" cy="50" r="38" />
<g class="pss_sweep">
<path d="M50,50 L50,12 A38,38 0 0,1 76.9,23.1 Z" fill="url(#${grad})" />
</g>
<circle class="pss_dot" cx="50" cy="50" r="3" />
</svg>`;
      }
    },
    {
      id: "ping-corner-brackets", name: "Corner Brackets", file: "ping_corner_brackets.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 400,
      svg(rid) {
        return `<svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .pcb_bracket { fill: none; stroke: var(--c-accent); stroke-width: calc(4 * var(--t-mult,1)); stroke-linecap: square;
    transform-box: fill-box; transform-origin: center; opacity: 0;
    animation-duration: calc(0.4s / var(--s-mult,1)); animation-timing-function: ease-out; animation-fill-mode: forwards; }
  .pcb_tl { animation-name: pcb_tl_${rid}; }
  .pcb_tr { animation-name: pcb_tr_${rid}; }
  .pcb_bl { animation-name: pcb_bl_${rid}; }
  .pcb_br { animation-name: pcb_br_${rid}; }
  @keyframes pcb_tl_${rid} { from { opacity:0; transform: translate(-22px,-22px);} to { opacity:1; transform: translate(0,0);} }
  @keyframes pcb_tr_${rid} { from { opacity:0; transform: translate(22px,-22px);} to { opacity:1; transform: translate(0,0);} }
  @keyframes pcb_bl_${rid} { from { opacity:0; transform: translate(-22px,22px);} to { opacity:1; transform: translate(0,0);} }
  @keyframes pcb_br_${rid} { from { opacity:0; transform: translate(22px,22px);} to { opacity:1; transform: translate(0,0);} }
</style></defs>
<path class="pcb_bracket pcb_tl" d="M10,36 L10,10 L36,10" />
<path class="pcb_bracket pcb_tr" d="M164,10 L190,10 L190,36" />
<path class="pcb_bracket pcb_bl" d="M10,104 L10,130 L36,130" />
<path class="pcb_bracket pcb_br" d="M190,104 L190,130 L164,130" />
</svg>`;
      }
    },
    {
      id: "ping-radar-blip", name: "Radar Blip", file: "ping_radar_blip.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 3000,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .prb_ring { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); opacity: 0.6; }
  .prb_blip { fill: var(--c-accent); transform-box: fill-box; transform-origin: center;
    animation: prb_blip_${rid} 3s steps(1,end) infinite; animation-duration: calc(3s / var(--s-mult,1)); }
  @keyframes prb_blip_${rid} {
    0%, 3% { opacity: 0; transform: scale(0.6); }
    4% { opacity: 1; transform: scale(1.3); }
    10% { opacity: 0; transform: scale(0.6); }
    48% { opacity: 0; transform: scale(0.6); }
    50% { opacity: 1; transform: scale(1.3); }
    56% { opacity: 0; transform: scale(0.6); }
    100% { opacity: 0; transform: scale(0.6); }
  }
</style></defs>
<circle class="prb_ring" cx="50" cy="50" r="30" />
<circle class="prb_blip" cx="50" cy="50" r="5" />
</svg>`;
      }
    },
    {
      id: "ping-target-lock", name: "Target Lock", file: "ping_target_lock.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 500,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .ptl_diamond { fill: none; stroke: var(--c-accent); stroke-width: calc(3 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center; opacity: 0;
    animation: ptl_snap_${rid} 0.4s cubic-bezier(.2,2.2,.3,1) forwards; animation-duration: calc(0.4s / var(--s-mult,1)); }
  .ptl_flash { fill: none; stroke: var(--c-accent); stroke-width: calc(1.5 * var(--t-mult,1)); opacity: 0;
    transform-box: fill-box; transform-origin: center;
    animation: ptl_flash_${rid} 0.5s ease-out forwards; animation-duration: calc(0.5s / var(--s-mult,1)); }
  @keyframes ptl_snap_${rid} { 0% { transform: scale(1.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
  @keyframes ptl_flash_${rid} { 0% { transform: scale(0.5); opacity: 0.9; } 100% { transform: scale(1.7); opacity: 0; } }
</style></defs>
<g transform="rotate(45 50 50)">
<rect class="ptl_diamond" x="35" y="35" width="30" height="30" />
</g>
<circle class="ptl_flash" cx="50" cy="50" r="22" />
</svg>`;
      }
    },
    {
      id: "ping-star-burst", name: "Star Burst", file: "ping_star_burst.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 1400,
      svg(rid) {
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .psb_star { fill: var(--c-accent); stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center;
    animation: psb_twinkle_${rid} 1.4s ease-in-out infinite; animation-duration: calc(1.4s / var(--s-mult,1)); }
  @keyframes psb_twinkle_${rid} { 0%,100% { transform: scale(0.7) rotate(0deg); opacity: 0.6; } 50% { transform: scale(1.15) rotate(12deg); opacity: 1; } }
</style></defs>
<path class="psb_star" d="M50,20 L56,44 L80,50 L56,56 L50,80 L44,56 L20,50 L44,44 Z" />
</svg>`;
      }
    },
    {
      id: "ping-underglow-pulse", name: "Underglow Pulse", file: "ping_underglow_pulse.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2600,
      svg(rid) {
        const grad = "pug_grad_" + rid;
        return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<defs>
<radialGradient id="${grad}" cx="50%" cy="50%" r="50%">
  <stop offset="0%" style="stop-color:var(--c-fluid); stop-opacity:0.8" />
  <stop offset="100%" style="stop-color:var(--c-fluid); stop-opacity:0" />
</radialGradient>
<style>
  .pug_glow { transform-box: fill-box; transform-origin: center;
    animation: pug_breathe_${rid} 2.6s ease-in-out infinite; animation-duration: calc(2.6s / var(--s-mult,1)); }
  .pug_dot { fill: var(--c-fluid); }
  @keyframes pug_breathe_${rid} { 0%,100% { transform: scale(0.7); opacity: 0.5; } 50% { transform: scale(1.15); opacity: 1; } }
</style>
</defs>
<ellipse class="pug_glow" cx="50" cy="50" rx="34" ry="20" fill="url(#${grad})" />
<circle class="pug_dot" cx="50" cy="50" r="3" />
</svg>`;
      }
    },
    {
      id: "ping-hex-lock", name: "Hex Lock", file: "ping_hex_lock.svg", category: "Pings",
      tags: { fn: ["point"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2400,
      svg(rid) {
        // Hexagonal reticle: static hex frame + one rotating dashed hex segment + breathing core.
        return `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .phl_frame { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); }
  .phl_orbit { fill: none; stroke: var(--c-accent); stroke-width: calc(3 * var(--t-mult,1));
    stroke-dasharray: 0.16 0.84; stroke-linecap: round; transform-box: fill-box; transform-origin: center;
    animation: phl_spin_${rid} 2.4s linear infinite; animation-duration: calc(2.4s / var(--s-mult,1)); }
  .phl_core { fill: var(--c-fluid); transform-box: fill-box; transform-origin: center;
    animation: phl_core_${rid} 2.4s ease-in-out infinite; animation-duration: calc(2.4s / var(--s-mult,1)); }
  @keyframes phl_spin_${rid} { to { transform: rotate(360deg); } }
  @keyframes phl_core_${rid} { 0%,100% { transform: scale(1); } 50% { transform: scale(1.5); } }
</style></defs>
<polygon class="phl_frame" points="60,14 100,37 100,83 60,106 20,83 20,37" />
<polygon class="phl_orbit" pathLength="1" points="60,24 91,42 91,78 60,96 29,78 29,42" />
<circle class="phl_core" cx="60" cy="60" r="4" />
</svg>`;
      }
    },
    {
      id: "frame-corner-brackets-full", name: "Full HUD Corners", file: "frame_corner_brackets_full.svg", category: "Frame",
      tags: { fn: ["chrome"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 800,
      svg(rid) {
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fcb_bracket { fill: none; stroke: var(--c-accent); stroke-width: calc(3 * var(--t-mult,1)); stroke-linecap: square;
    stroke-dasharray: 1; stroke-dashoffset: 1; animation: fcb_draw_${rid} 0.5s ease-out forwards;
    animation-duration: calc(0.5s / var(--s-mult,1)); }
  .fcb_b2 { animation-delay: calc(0.08s / var(--s-mult,1)); }
  .fcb_b3 { animation-delay: calc(0.16s / var(--s-mult,1)); }
  .fcb_b4 { animation-delay: calc(0.24s / var(--s-mult,1)); }
  .fcb_tick { stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); opacity: 0;
    animation: fcb_fadeIn_${rid} 0.3s linear 0.5s forwards;
    animation-duration: calc(0.3s / var(--s-mult,1)); animation-delay: calc(0.5s / var(--s-mult,1)); }
</style></defs>
<path class="fcb_bracket" pathLength="1" d="M20,60 L20,20 L60,20" />
<path class="fcb_bracket fcb_b2" pathLength="1" d="M580,20 L620,20 L620,60" />
<path class="fcb_bracket fcb_b3" pathLength="1" d="M20,300 L20,340 L60,340" />
<path class="fcb_bracket fcb_b4" pathLength="1" d="M620,300 L620,340 L580,340" />
<line class="fcb_tick" x1="20" y1="180" x2="20" y2="200" />
<line class="fcb_tick" x1="620" y1="180" x2="620" y2="200" />
<line class="fcb_tick" x1="300" y1="20" x2="320" y2="20" />
<line class="fcb_tick" x1="300" y1="340" x2="320" y2="340" />
</svg>`;
      }
    },
    {
      id: "divider-technical-rule", name: "Technical Rule", file: "divider_technical_rule.svg", category: "Frame",
      tags: { fn: ["chrome", "transition"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 800, roundable: true,
      hasText: true, textDefault: "SECTION_02", textHint: "Section / transition label",
      svg(rid) {
        return `<svg viewBox="0 0 400 40" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .dtr_line { fill: none; stroke: var(--c-leader); stroke-width: calc(1.5 * var(--t-mult,1));
    stroke-dasharray: 0.5; stroke-dashoffset: 0.5; animation: dtr_draw_${rid} 0.5s ease-out forwards;
    animation-duration: calc(0.5s / var(--s-mult,1)); }
  .dtr_tick { stroke: var(--c-leader); stroke-width: calc(1.5 * var(--t-mult,1)); opacity: 0;
    animation: dtr_fadeIn_${rid} 0.2s linear 0.5s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.5s / var(--s-mult,1)); }
  .dtr_bg { fill: var(--c-panel); rx: var(--r-mult,0); ry: var(--r-mult,0); opacity: 0;
    animation: dtr_fadeIn_${rid} 0.15s linear 0.45s forwards;
    animation-duration: calc(0.15s / var(--s-mult,1)); animation-delay: calc(0.45s / var(--s-mult,1)); }
  .dtr_label { font-family: "Space Mono","Courier New",monospace; font-size: 11px; letter-spacing: 0.08em;
    fill: var(--c-label); text-anchor: middle; opacity: 0; animation: dtr_fadeIn_${rid} 0.2s linear 0.55s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.55s / var(--s-mult,1)); }
  @keyframes dtr_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes dtr_fadeIn_${rid} { to { opacity: 1; } }
</style></defs>
<path class="dtr_line" pathLength="0.5" d="M20,20 L155,20" />
<path class="dtr_line" pathLength="0.5" d="M245,20 L380,20" />
<line class="dtr_tick" x1="20" y1="14" x2="20" y2="26" />
<line class="dtr_tick" x1="380" y1="14" x2="380" y2="26" />
<rect class="dtr_bg" x="160" y="6" width="80" height="28" />
<text class="dtr_label" data-text-slot="true" x="200" y="24">SECTION_02</text>
</svg>`;
      }
    },
    {
      id: "badge-spec-tag", name: "Spec Tag", file: "badge_spec_tag.svg", category: "Frame",
      tags: { fn: ["chrome"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 650, roundable: true,
      hasText: true, textDefault: "SPEC_TAG", textHint: "Short spec text — rating, material, standard",
      svg(rid) {
        return `<svg viewBox="0 0 140 44" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .bst_tick { stroke: var(--c-accent); stroke-width: calc(2 * var(--t-mult,1)); stroke-dasharray: 1; stroke-dashoffset: 1;
    animation: bst_draw_${rid} 0.25s ease-out forwards;
    animation-duration: calc(0.25s / var(--s-mult,1)); }
  .bst_chip { fill: var(--c-panel); stroke: var(--c-accent); stroke-width: calc(1.5 * var(--t-mult,1));
    rx: var(--r-mult,0); ry: var(--r-mult,0);
    transform-box: fill-box; transform-origin: left center; transform: scaleX(0); opacity: 0;
    animation: bst_pop_${rid} 0.3s ease-out 0.2s forwards;
    animation-duration: calc(0.3s / var(--s-mult,1)); animation-delay: calc(0.2s / var(--s-mult,1)); }
  .bst_label { font-family: "Space Mono","Courier New",monospace; font-size: 13px; letter-spacing: 0.06em;
    fill: var(--c-label); opacity: 0; animation: bst_fadeIn_${rid} 0.2s linear 0.45s forwards;
    animation-duration: calc(0.2s / var(--s-mult,1)); animation-delay: calc(0.45s / var(--s-mult,1)); }
  @keyframes bst_draw_${rid} { to { stroke-dashoffset: 0; } }
  @keyframes bst_pop_${rid} { to { transform: scaleX(1); opacity: 1; } }
  @keyframes bst_fadeIn_${rid} { to { opacity: 1; } }
</style></defs>
<line class="bst_tick" pathLength="1" x1="4" y1="22" x2="18" y2="22" />
<rect class="bst_chip" x="18" y="8" width="118" height="28" />
<text class="bst_label" data-text-slot="true" x="28" y="27">SPEC_TAG</text>
</svg>`;
      }
    },
    {
      id: "frame-scan-line-sweep", name: "Scan Line Sweep", file: "frame_scan_line_sweep.svg", category: "Frame",
      tags: { fn: ["chrome"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 2200,
      svg(rid) {
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fss_border { fill: none; stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1)); opacity: 0.5; }
  .fss_sweep { stroke: var(--c-accent); stroke-width: calc(2 * var(--t-mult,1));
    animation: fss_scan_${rid} 2.2s linear infinite; animation-duration: calc(2.2s / var(--s-mult,1)); }
  @keyframes fss_scan_${rid} {
    0% { transform: translateY(0); opacity: 0; }
    8% { opacity: 0.85; }
    92% { opacity: 0.85; }
    100% { transform: translateY(360px); opacity: 0; }
  }
</style></defs>
<rect class="fss_border" x="4" y="4" width="632" height="352" />
<line class="fss_sweep" x1="0" y1="0" x2="640" y2="0" />
</svg>`;
      }
    },
    {
      id: "frame-vignette-pulse", name: "Vignette Pulse", file: "frame_vignette_pulse.svg", category: "Frame",
      tags: { fn: ["chrome"], vibe: ["precise"] },
      engine: "css", loop: true, durationMs: 3200,
      svg(rid) {
        const grad = "fvp_grad_" + rid;
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs>
<radialGradient id="${grad}" cx="50%" cy="50%" r="50%">
  <stop offset="0%" stop-color="#000000" stop-opacity="0.55" />
  <stop offset="100%" stop-color="#000000" stop-opacity="0" />
</radialGradient>
<style>
  .fvp_corner { fill: url(#${grad}); transform-box: fill-box; transform-origin: center;
    animation: fvp_breathe_${rid} 3.2s ease-in-out infinite; animation-duration: calc(3.2s / var(--s-mult,1)); }
  @keyframes fvp_breathe_${rid} { 0%,100% { transform: scale(0.85); opacity: 0.6; } 50% { transform: scale(1.05); opacity: 1; } }
</style>
</defs>
<ellipse class="fvp_corner" cx="0" cy="0" rx="220" ry="160" />
<ellipse class="fvp_corner" cx="640" cy="0" rx="220" ry="160" />
<ellipse class="fvp_corner" cx="0" cy="360" rx="220" ry="160" />
<ellipse class="fvp_corner" cx="640" cy="360" rx="220" ry="160" />
</svg>`;
      }
    },
    {
      id: "frame-grid-overlay", name: "Grid Overlay", file: "frame_grid_overlay.svg", category: "Frame",
      tags: { fn: ["chrome"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 1200,
      svg(rid) {
        const vLines = [];
        for (let x = 80; x < 640; x += 80) vLines.push(`<line class="fgo_line" x1="${x}" y1="0" x2="${x}" y2="360" />`);
        const hLines = [];
        for (let y = 60; y < 360; y += 60) hLines.push(`<line class="fgo_line" x1="0" y1="${y}" x2="640" y2="${y}" />`);
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fgo_line { stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1)); opacity: 0;
    animation: fgo_fade_${rid} 1.2s ease-out forwards; animation-duration: calc(1.2s / var(--s-mult,1)); }
  @keyframes fgo_fade_${rid} { to { opacity: 0.45; } }
</style></defs>
${vLines.join("")}
${hLines.join("")}
</svg>`;
      }
    },
    {
      id: "frame-title-card-bar", name: "Title Card Bar", file: "frame_title_card_bar.svg", category: "Frame",
      tags: { fn: ["chrome"], vibe: ["precise"] },
      engine: "css", loop: false, durationMs: 550, roundable: true,
      hasText: true, textDefault: "TITLE_CARD", textHint: "Lower-third title text",
      svg(rid) {
        return `<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .ftb_slide { transform: translateX(-460px); animation: ftb_in_${rid} 0.55s ease-out forwards;
    animation-duration: calc(0.55s / var(--s-mult,1)); }
  .ftb_bar { fill: var(--c-panel); rx: var(--r-mult,0); ry: var(--r-mult,0); }
  .ftb_accent { stroke: var(--c-accent); stroke-width: calc(5 * var(--t-mult,1)); }
  .ftb_label { font-family: "Space Mono","Courier New",monospace; font-size: 20px; letter-spacing: 0.04em; fill: var(--c-label); }
  @keyframes ftb_in_${rid} { to { transform: translateX(0); } }
</style></defs>
<g class="ftb_slide">
<rect class="ftb_bar" x="0" y="70" width="400" height="50" />
<line class="ftb_accent" x1="0" y1="70" x2="0" y2="120" />
<text class="ftb_label" data-text-slot="true" x="24" y="102">TITLE_CARD</text>
</g>
</svg>`;
      }
    },
    {
      id: "splash-droplet-fall", name: "Droplet Fall", file: "splash_droplet_fall.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: true, durationMs: 1400,
      svg(rid) {
        return `<svg viewBox="0 0 100 140" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .sdf_surface { stroke: var(--c-structural); stroke-width: calc(3 * var(--t-mult,1)); }
  .sdf_drop { transform-box: fill-box; transform-origin: center;
    animation: sdf_fall_${rid} 1.4s cubic-bezier(.55,0,.85,.35) infinite;
    animation-duration: calc(1.4s / var(--s-mult,1)); }
  .sdf_drop path { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1)); }
  .sdf_ripple { fill: none; stroke: var(--c-fluid); stroke-width: calc(2 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center;
    animation: sdf_ripple_${rid} 1.4s ease-out infinite;
    animation-duration: calc(1.4s / var(--s-mult,1)); }
  @keyframes sdf_fall_${rid} {
    0%   { transform: translateY(16px) scale(0.6); opacity: 0; }
    8%   { transform: translateY(16px) scale(0.85); opacity: 1; }
    68%  { transform: translateY(96px) scale(1); opacity: 1; }
    86%  { transform: translateY(112px) scaleY(0.5) scaleX(1.3); opacity: 1; }
    96%  { transform: translateY(114px) scaleY(0.15) scaleX(0.5); opacity: 0; }
    100% { transform: translateY(16px) scale(0.6); opacity: 0; }
  }
  @keyframes sdf_ripple_${rid} {
    0%, 80% { opacity: 0; transform: scaleX(0.3); }
    88%     { opacity: 0.8; transform: scaleX(1); }
    100%    { opacity: 0; transform: scaleX(1.7); }
  }
</style></defs>
<line class="sdf_surface" x1="14" y1="118" x2="86" y2="118" />
<ellipse class="sdf_ripple" cx="50" cy="118" rx="16" ry="5" />
<g transform="translate(50,0)">
  <g class="sdf_drop">
    <path d="M0,-23 C15,-4 18,10 18,18 A18,18 0 1,1 -18,18 C-18,10 -15,-4 0,-23 Z" />
  </g>
</g>
</svg>`;
      }
    },
    {
      id: "splash-impact-burst", name: "Impact Burst", file: "splash_impact_burst.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: false, durationMs: 600,
      svg(rid) {
        const angles = [0, 72, 144, 216, 288];
        const particles = angles.map((deg, i) => `
<g transform="translate(60,60) rotate(${deg})">
  <g class="sib_particle sib_p${i}">
    <path d="M0,-9 C6,-1.5 7,4 7,7 A7,7 0 1,1 -7,7 C-7,4 -6,-1.5 0,-9 Z" />
  </g>
</g>`).join("");
        return `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .sib_core { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center; opacity: 0;
    animation: sib_core_${rid} 0.45s ease-out forwards;
    animation-duration: calc(0.45s / var(--s-mult,1)); }
  .sib_particle { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1.2 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center; opacity: 0;
    animation: sib_burst_${rid} 0.5s ease-out forwards;
    animation-duration: calc(0.5s / var(--s-mult,1)); }
  .sib_p1, .sib_p3 { animation-delay: calc(0.03s / var(--s-mult,1)); }
  .sib_p2, .sib_p4 { animation-delay: calc(0.06s / var(--s-mult,1)); }
  @keyframes sib_core_${rid} { 0% { transform: scale(0.2); opacity: 0.9; } 100% { transform: scale(1.7); opacity: 0; } }
  @keyframes sib_burst_${rid} { 0% { transform: translateY(-10px) scale(0.5); opacity: 1; } 100% { transform: translateY(-42px) scale(0.15); opacity: 0; } }
</style></defs>
<ellipse class="sib_core" cx="60" cy="60" rx="14" ry="7" />
${particles}
</svg>`;
      }
    },
    {
      id: "splash-ripple-rings", name: "Ripple Rings", file: "splash_ripple_rings.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: true, durationMs: 1800,
      svg(rid) {
        return `<svg viewBox="0 0 100 60" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .srr_ring { fill: none; stroke: var(--c-fluid); stroke-width: calc(2 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center;
    animation: srr_ripple_${rid} 1.8s ease-out infinite;
    animation-duration: calc(1.8s / var(--s-mult,1)); }
  .srr_r2 { animation-delay: calc(0.6s / var(--s-mult,1)); }
  .srr_r3 { animation-delay: calc(1.2s / var(--s-mult,1)); }
  .srr_dot { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1)); }
  @keyframes srr_ripple_${rid} { 0% { transform: scale(0.2,0.1); opacity: 0.85; } 100% { transform: scale(2.6,0.8); opacity: 0; } }
</style></defs>
<ellipse class="srr_ring" cx="50" cy="30" rx="14" ry="5" />
<ellipse class="srr_ring srr_r2" cx="50" cy="30" rx="14" ry="5" />
<ellipse class="srr_ring srr_r3" cx="50" cy="30" rx="14" ry="5" />
<ellipse class="srr_dot" cx="50" cy="30" rx="3" ry="1.6" />
</svg>`;
      }
    },
    {
      id: "splash-puddle-form", name: "Puddle Form", file: "splash_puddle_form.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: true, durationMs: 2800,
      svg(rid) {
        return `<svg viewBox="0 0 100 60" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .spf_puddle { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center;
    animation: spf_grow_${rid} 2.8s ease-in-out infinite; animation-duration: calc(2.8s / var(--s-mult,1)); }
  .spf_shine { fill: var(--c-label); opacity: 0.35; }
  @keyframes spf_grow_${rid} {
    0% { transform: scale(0.05); opacity: 0; }
    20% { transform: scale(1); opacity: 1; }
    75% { transform: scale(1); opacity: 1; }
    100% { transform: scale(0.05); opacity: 0; }
  }
</style></defs>
<ellipse class="spf_puddle" cx="50" cy="40" rx="34" ry="12" />
<ellipse class="spf_shine" cx="38" cy="35" rx="7" ry="2.5" />
</svg>`;
      }
    },
    {
      id: "splash-mist-spray", name: "Mist Spray", file: "splash_mist_spray.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: false, durationMs: 950,
      svg(rid) {
        return `<svg viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .smt_dot { fill: var(--c-fluid); opacity: 0; transform-box: fill-box; transform-origin: center;
    animation-duration: calc(0.9s / var(--s-mult,1)); animation-timing-function: ease-out; animation-fill-mode: forwards; }
  .smt_p1 { animation-name: smt_k1_${rid}; }
  .smt_p2 { animation-name: smt_k2_${rid}; animation-delay: calc(0.04s / var(--s-mult,1)); }
  .smt_p3 { animation-name: smt_k3_${rid}; animation-delay: calc(0.08s / var(--s-mult,1)); }
  .smt_p4 { animation-name: smt_k4_${rid}; animation-delay: calc(0.02s / var(--s-mult,1)); }
  .smt_p5 { animation-name: smt_k5_${rid}; animation-delay: calc(0.06s / var(--s-mult,1)); }
  .smt_p6 { animation-name: smt_k6_${rid}; animation-delay: calc(0.1s / var(--s-mult,1)); }
  @keyframes smt_k1_${rid} { 0% { opacity:0; transform: translate(0,0) scale(0.4);} 30% { opacity:0.9;} 100% { opacity:0; transform: translate(-30px,-42px) scale(1);} }
  @keyframes smt_k2_${rid} { 0% { opacity:0; transform: translate(0,0) scale(0.4);} 30% { opacity:0.9;} 100% { opacity:0; transform: translate(12px,-52px) scale(1);} }
  @keyframes smt_k3_${rid} { 0% { opacity:0; transform: translate(0,0) scale(0.4);} 30% { opacity:0.9;} 100% { opacity:0; transform: translate(-46px,-22px) scale(1);} }
  @keyframes smt_k4_${rid} { 0% { opacity:0; transform: translate(0,0) scale(0.4);} 30% { opacity:0.9;} 100% { opacity:0; transform: translate(38px,-34px) scale(1);} }
  @keyframes smt_k5_${rid} { 0% { opacity:0; transform: translate(0,0) scale(0.4);} 30% { opacity:0.9;} 100% { opacity:0; transform: translate(-10px,-58px) scale(1);} }
  @keyframes smt_k6_${rid} { 0% { opacity:0; transform: translate(0,0) scale(0.4);} 30% { opacity:0.9;} 100% { opacity:0; transform: translate(46px,-14px) scale(1);} }
</style></defs>
<circle class="smt_dot smt_p1" cx="60" cy="70" r="4" />
<circle class="smt_dot smt_p2" cx="60" cy="70" r="3" />
<circle class="smt_dot smt_p3" cx="60" cy="70" r="5" />
<circle class="smt_dot smt_p4" cx="60" cy="70" r="3" />
<circle class="smt_dot smt_p5" cx="60" cy="70" r="4" />
<circle class="smt_dot smt_p6" cx="60" cy="70" r="3" />
</svg>`;
      }
    },
    {
      id: "splash-drip-trail", name: "Drip Trail", file: "splash_drip_trail.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: true, durationMs: 1600,
      svg(rid) {
        const drop = (cls, delay) => `<g transform="translate(30,0)">
  <g class="sdt_drop ${cls}" style="animation-delay: calc(${delay}s / var(--s-mult,1));">
    <path d="M0,-18 C12,-3 14,8 14,14 A14,14 0 1,1 -14,14 C-14,8 -12,-3 0,-18 Z" />
  </g>
</g>`;
        return `<svg viewBox="0 0 60 160" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .sdt_drop { transform-box: fill-box; transform-origin: center;
    animation: sdt_fall_${rid} 1.6s cubic-bezier(.5,0,.9,.4) infinite; animation-duration: calc(1.6s / var(--s-mult,1)); }
  .sdt_drop path { fill: var(--c-fluid); stroke: var(--c-structural); stroke-width: calc(1.3 * var(--t-mult,1)); }
  .sdt_surface { stroke: var(--c-structural); stroke-width: calc(2.5 * var(--t-mult,1)); }
  @keyframes sdt_fall_${rid} {
    0% { transform: translateY(10px) scale(0.5); opacity: 0; }
    10% { transform: translateY(10px) scale(0.8); opacity: 1; }
    75% { transform: translateY(120px) scale(1); opacity: 1; }
    92% { transform: translateY(134px) scaleY(0.4) scaleX(1.3); opacity: 1; }
    100% { transform: translateY(10px) scale(0.5); opacity: 0; }
  }
</style></defs>
<line class="sdt_surface" x1="6" y1="146" x2="54" y2="146" />
${drop("sdt_d1", 0)}${drop("sdt_d2", 0.53)}${drop("sdt_d3", 1.06)}
</svg>`;
      }
    },
    {
      id: "splash-wave-crest", name: "Wave Crest", file: "splash_wave_crest.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic", "playful"] },
      engine: "css", loop: true, durationMs: 2400,
      svg(rid) {
        return `<svg viewBox="0 0 160 60" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .swc_wave { fill: var(--c-fluid); animation: swc_scroll_${rid} 2.4s linear infinite;
    animation-duration: calc(2.4s / var(--s-mult,1)); }
  .swc_crest { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1));
    animation: swc_scroll_${rid} 2.4s linear infinite; animation-duration: calc(2.4s / var(--s-mult,1)); }
  @keyframes swc_scroll_${rid} { 0% { transform: translateX(0); } 100% { transform: translateX(-60px); } }
</style></defs>
<path class="swc_wave" d="M-60,30 C-50,15 -40,15 -30,30 C-20,45 -10,45 0,30 C10,15 20,15 30,30 C40,45 50,45 60,30 C70,15 80,15 90,30 C100,45 110,45 120,30 C130,15 140,15 150,30 C160,45 170,45 180,30 C190,15 200,15 210,30 L210,60 L-60,60 Z" />
<path class="swc_crest" d="M-60,30 C-50,15 -40,15 -30,30 C-20,45 -10,45 0,30 C10,15 20,15 30,30 C40,45 50,45 60,30 C70,15 80,15 90,30 C100,45 110,45 120,30 C130,15 140,15 150,30 C160,45 170,45 180,30 C190,15 200,15 210,30" />
</svg>`;
      }
    },
    {
      id: "splash-bubble-rise", name: "Bubble Rise", file: "splash_bubble_rise.svg", category: "Splashes",
      tags: { fn: ["flow"], vibe: ["organic"] },
      engine: "smil", loop: true, durationMs: 3000,
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const dur = 3 / speedMult;
        const bubbles = [
          { p: "M60,150 Q48,100 62,50 Q70,20 58,-10",  r: 6, b: 0 },
          { p: "M90,150 Q102,95 88,45 Q80,15 92,-10",  r: 4, b: dur * 0.35 },
          { p: "M120,150 Q110,90 124,40 Q132,15 118,-10", r: 5, b: dur * 0.6 },
          { p: "M75,150 Q85,105 72,55 Q64,25 78,-10",  r: 3, b: dur * 0.8 }
        ];
        const g = bubbles.map(bb => `<g data-role="motion-target">
  <circle class="sbr_b" r="${bb.r}" />
  <animateMotion dur="${dur.toFixed(3)}s" repeatCount="indefinite" begin="${bb.b.toFixed(3)}s" path="${bb.p}" />
</g>`).join("\n");
        return `<svg viewBox="0 0 180 160" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .sbr_b { fill: none; stroke: var(--c-fluid); stroke-width: calc(2 * var(--t-mult,1)); opacity: 0.85; }
  .sbr_surface { stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); stroke-dasharray: 6 4; opacity: 0.6; }
</style></defs>
<line class="sbr_surface" x1="20" y1="150" x2="160" y2="150" />
${g}
</svg>`;
      }
    },
    /* ---------- BACKGROUNDS — ambient full-frame layers (640x360, 16:9) ----------
       Design rules: slow tempo (8-24s loops), edge-weighted composition
       (center stays clear for the render subject), accent color quarantined,
       default opacity preset well below 1. One geometry + one technique each. */
    {
      id: "bg-blueprint-drift", name: "Blueprint Drift", file: "bg_blueprint_drift.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient"] },
      engine: "smil", loop: true, durationMs: 20000, paramPreset: { opacity: 0.45 },
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const pat = "bgd_pat_" + rid;
        const dur = (20 / speedMult).toFixed(3);
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<defs>
<style>
  .bgd_minor { stroke: var(--c-structural); stroke-width: calc(0.6 * var(--t-mult,1)); opacity: 0.55; }
  .bgd_major { stroke: var(--c-structural); stroke-width: calc(1.4 * var(--t-mult,1)); }
</style>
<pattern id="${pat}" width="100" height="100" patternUnits="userSpaceOnUse">
  <line class="bgd_minor" x1="20" y1="0" x2="20" y2="100" /><line class="bgd_minor" x1="40" y1="0" x2="40" y2="100" />
  <line class="bgd_minor" x1="60" y1="0" x2="60" y2="100" /><line class="bgd_minor" x1="80" y1="0" x2="80" y2="100" />
  <line class="bgd_minor" x1="0" y1="20" x2="100" y2="20" /><line class="bgd_minor" x1="0" y1="40" x2="100" y2="40" />
  <line class="bgd_minor" x1="0" y1="60" x2="100" y2="60" /><line class="bgd_minor" x1="0" y1="80" x2="100" y2="80" />
  <line class="bgd_major" x1="0" y1="0" x2="0" y2="100" /><line class="bgd_major" x1="0" y1="0" x2="100" y2="0" />
  <animateTransform xlink:href="#${pat}" attributeName="patternTransform" attributeType="XML"
    type="translate" from="0 0" to="100 100" dur="${dur}s" repeatCount="indefinite" />
</pattern>
</defs>
<rect width="640" height="360" fill="url(#${pat})" />
</svg>`;
      }
    },
    {
      id: "bg-topo-contours", name: "Topo Contours", file: "bg_topo_contours.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient", "organic"] },
      engine: "css", loop: true, durationMs: 12000, paramPreset: { opacity: 0.5 },
      svg(rid) {
        // Nested irregular contour loops, breathing scale at phase offsets. Off-center: keeps subject area clear.
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .bgt_c { fill: none; stroke: var(--c-structural); stroke-width: calc(1.2 * var(--t-mult,1));
    transform-box: fill-box; transform-origin: center;
    animation: bgt_breathe_${rid} 12s ease-in-out infinite; animation-duration: calc(12s / var(--s-mult,1)); }
  .bgt_c.i2 { animation-delay: -3s; opacity: 0.8; }
  .bgt_c.i3 { animation-delay: -6s; opacity: 0.6; }
  .bgt_c.i4 { animation-delay: -9s; stroke: var(--c-fluid); opacity: 0.7; }
  @keyframes bgt_breathe_${rid} { 0%,100% { transform: scale(1); } 50% { transform: scale(1.045); } }
</style></defs>
<path class="bgt_c"    d="M60,240 C40,170 90,110 170,105 C260,100 310,160 295,230 C280,300 190,330 120,305 C75,288 72,272 60,240 Z" />
<path class="bgt_c i2" d="M85,235 C70,180 110,130 175,127 C248,123 285,172 272,228 C260,283 188,306 132,286 C98,272 94,260 85,235 Z" />
<path class="bgt_c i3" d="M112,230 C102,192 132,152 182,150 C238,147 262,185 252,226 C243,268 188,284 146,268 C122,258 118,250 112,230 Z" />
<path class="bgt_c i4" d="M142,224 C136,198 156,172 190,171 C226,169 240,194 234,222 C228,250 192,260 164,250 C148,244 146,238 142,224 Z" />
</svg>`;
      }
    },
    {
      id: "bg-particle-drift", name: "Particle Drift", file: "bg_particle_drift.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient", "organic"] },
      engine: "smil", loop: true, durationMs: 14000, paramPreset: { opacity: 0.55 },
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const dur = 14 / speedMult;
        // Six dust motes rising on curved paths; size/opacity vary = cheap parallax depth.
        const motes = [
          { p: "M70,380 Q110,180 60,-20",  r: 2.2, o: 0.85, b: 0 },
          { p: "M180,380 Q150,190 200,-20", r: 1.4, o: 0.5,  b: dur * 0.32 },
          { p: "M330,380 Q370,170 320,-20", r: 1.8, o: 0.65, b: dur * 0.55 },
          { p: "M460,380 Q430,200 480,-20", r: 1.2, o: 0.4,  b: dur * 0.14 },
          { p: "M560,380 Q600,180 550,-20", r: 2.6, o: 0.9,  b: dur * 0.72 },
          { p: "M250,380 Q280,160 240,-20", r: 1.0, o: 0.35, b: dur * 0.88 }
        ];
        const g = motes.map(m => `<g data-role="motion-target" opacity="${m.o}">
  <circle r="${m.r}" class="bgp_mote" />
  <animateMotion dur="${dur.toFixed(3)}s" repeatCount="indefinite" begin="${m.b.toFixed(3)}s" path="${m.p}" />
</g>`).join("\n");
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>.bgp_mote { fill: var(--c-leader); }</style></defs>
${g}
</svg>`;
      }
    },
    {
      id: "bg-hex-cell-glow", name: "Hex Cell Glow", file: "bg_hex_cell_glow.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient"] },
      engine: "css", loop: true, durationMs: 9000, paramPreset: { opacity: 0.4 },
      svg(rid) {
        // Lattice built in JS; a handful of cells pulse fill in sequence.
        const s = 30, hx = 45, hy = 52;
        const hexPts = (cx, cy) => {
          let pts = [];
          for (let i = 0; i < 6; i++) { const a = Math.PI / 3 * i; pts.push((cx + s * Math.cos(a)).toFixed(1) + "," + (cy + s * Math.sin(a)).toFixed(1)); }
          return pts.join(" ");
        };
        let cells = "", glowIdx = new Set(["1_0", "4_2", "9_1", "12_5", "6_6", "14_3"]), gi = 0;
        for (let c = 0; c < 16; c++) for (let r = 0; r < 8; r++) {
          const cx = c * hx - 15, cy = r * hy + (c % 2 ? hy / 2 : 0) - 20;
          const key = c + "_" + r;
          cells += glowIdx.has(key)
            ? `<polygon class="bgh_cell bgh_glow" style="animation-delay:${(gi++ * 1.5).toFixed(1)}s" points="${hexPts(cx, cy)}" />\n`
            : `<polygon class="bgh_cell" points="${hexPts(cx, cy)}" />\n`;
        }
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .bgh_cell { fill: none; stroke: var(--c-structural); stroke-width: calc(0.8 * var(--t-mult,1)); opacity: 0.5; }
  .bgh_glow { animation: bgh_pulse_${rid} 9s ease-in-out infinite; animation-duration: calc(9s / var(--s-mult,1)); }
  @keyframes bgh_pulse_${rid} { 0%,12%,100% { fill: transparent; opacity: 0.5; } 6% { fill: var(--c-fluid); opacity: 0.9; } }
</style></defs>
${cells}</svg>`;
      }
    },
    {
      id: "bg-laminar-streams", name: "Laminar Streams", file: "bg_laminar_streams.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient"] },
      engine: "css", loop: true, durationMs: 8000, paramPreset: { opacity: 0.5 },
      svg(rid) {
        // Three depth planes: far = thin/slow/faint, near = thick/fast/bright. Dash-march parallax.
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .bgl_s { fill: none; stroke: var(--c-fluid); stroke-linecap: round; }
  .bgl_far  { stroke-width: calc(1 * var(--t-mult,1)); opacity: 0.3; stroke-dasharray: 0.10 0.06;
    animation: bgl_m_${rid} 8s linear infinite; animation-duration: calc(8s / var(--s-mult,1)); }
  .bgl_mid  { stroke-width: calc(1.8 * var(--t-mult,1)); opacity: 0.55; stroke-dasharray: 0.13 0.07;
    animation: bgl_m_${rid} 5s linear infinite; animation-duration: calc(5s / var(--s-mult,1)); }
  .bgl_near { stroke-width: calc(2.8 * var(--t-mult,1)); opacity: 0.85; stroke-dasharray: 0.16 0.09;
    animation: bgl_m_${rid} 3.2s linear infinite; animation-duration: calc(3.2s / var(--s-mult,1)); }
  @keyframes bgl_m_${rid} { to { stroke-dashoffset: -0.5; } }
</style></defs>
<path class="bgl_s bgl_far"  pathLength="1" d="M-10,40  C160,34  480,46  650,38" />
<path class="bgl_s bgl_mid"  pathLength="1" d="M-10,70  C180,62  460,80  650,68" />
<path class="bgl_s bgl_far"  pathLength="1" d="M-10,105 C150,98  500,112 650,102" />
<path class="bgl_s bgl_near" pathLength="1" d="M-10,300 C200,288 440,312 650,296" />
<path class="bgl_s bgl_mid"  pathLength="1" d="M-10,330 C170,322 470,340 650,326" />
<path class="bgl_s bgl_far"  pathLength="1" d="M-10,352 C190,346 450,358 650,350" />
</svg>`;
      }
    },
    {
      id: "bg-sonar-corner", name: "Sonar Corner", file: "bg_sonar_corner.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient", "retro-tech"] },
      engine: "css", loop: true, durationMs: 16000, paramPreset: { opacity: 0.5 },
      svg(rid) {
        // Quarter-rings expanding from the bottom-left corner. transform-origin in view-box units (no fill-box).
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .bgs_ring { fill: none; stroke: var(--c-structural); stroke-width: calc(1.6 * var(--t-mult,1));
    transform-origin: 0px 360px;
    animation: bgs_x_${rid} 16s linear infinite; animation-duration: calc(16s / var(--s-mult,1)); }
  .bgs_ring.i2 { animation-delay: calc(-5.33s / var(--s-mult,1)); }
  .bgs_ring.i3 { animation-delay: calc(-10.66s / var(--s-mult,1)); stroke: var(--c-fluid); }
  .bgs_hub { fill: var(--c-fluid); }
  @keyframes bgs_x_${rid} { 0% { transform: scale(0.05); opacity: 0.9; } 100% { transform: scale(1.3); opacity: 0; } }
</style></defs>
<circle class="bgs_ring"    cx="0" cy="360" r="340" />
<circle class="bgs_ring i2" cx="0" cy="360" r="340" />
<circle class="bgs_ring i3" cx="0" cy="360" r="340" />
<circle class="bgs_hub" cx="0" cy="360" r="6" />
</svg>`;
      }
    },
    {
      id: "bg-instrument-tape", name: "Instrument Tape", file: "bg_instrument_tape.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient"] },
      engine: "smil", loop: true, durationMs: 6000, paramPreset: { opacity: 0.6 },
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const pat = "bgi_pat_" + rid;
        const dur = (6 / speedMult).toFixed(3);
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<defs>
<style>
  .bgi_rail { stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1)); }
  .bgi_t { stroke: var(--c-leader); stroke-width: calc(1 * var(--t-mult,1)); }
</style>
<pattern id="${pat}" width="24" height="40" patternUnits="userSpaceOnUse">
  <line class="bgi_t" x1="0" y1="4"  x2="18" y2="4" />
  <line class="bgi_t" x1="0" y1="14" x2="8"  y2="14" opacity="0.6" />
  <line class="bgi_t" x1="0" y1="24" x2="8"  y2="24" opacity="0.6" />
  <line class="bgi_t" x1="0" y1="34" x2="8"  y2="34" opacity="0.6" />
  <animateTransform xlink:href="#${pat}" attributeName="patternTransform" attributeType="XML"
    type="translate" from="0 0" to="0 -40" dur="${dur}s" repeatCount="indefinite" />
</pattern>
</defs>
<rect x="16"  y="0" width="24" height="360" fill="url(#${pat})" />
<rect x="600" y="0" width="24" height="360" fill="url(#${pat})" />
<line class="bgi_rail" x1="14"  y1="0" x2="14"  y2="360" />
<line class="bgi_rail" x1="626" y1="0" x2="626" y2="360" />
</svg>`;
      }
    },
    {
      id: "bg-oscilloscope-strip", name: "Oscilloscope Strip", file: "bg_oscilloscope_strip.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient"] },
      engine: "smil", loop: true, durationMs: 4000, paramPreset: { opacity: 0.65 },
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const pat = "bgo_pat_" + rid;
        const dur = (4 / speedMult).toFixed(3);
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<defs>
<style>
  .bgo_base { stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1)); opacity: 0.6; }
  .bgo_wave { fill: none; stroke: var(--c-fluid); stroke-width: calc(1.8 * var(--t-mult,1)); }
</style>
<pattern id="${pat}" width="80" height="60" patternUnits="userSpaceOnUse">
  <path class="bgo_wave" d="M0,30 C10,10 30,10 40,30 C50,50 70,50 80,30" />
  <animateTransform xlink:href="#${pat}" attributeName="patternTransform" attributeType="XML"
    type="translate" from="0 0" to="-80 0" dur="${dur}s" repeatCount="indefinite" />
</pattern>
</defs>
<line class="bgo_base" x1="0" y1="330" x2="640" y2="330" />
<rect x="0" y="300" width="640" height="60" fill="url(#${pat})" />
</svg>`;
      }
    },
    {
      id: "bg-hatch-sweep", name: "Hatch Sweep", file: "bg_hatch_sweep.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere", "transition"], vibe: ["ambient"] },
      engine: "css", loop: true, durationMs: 9000, paramPreset: { opacity: 0.35 },
      svg(rid) {
        const pat = "bgx_pat_" + rid, grad = "bgx_grad_" + rid;
        // Static engineering hatch + a light band sweeping through, then a long rest.
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
  .bgx_band { animation: bgx_sweep_${rid} 9s ease-in-out infinite; animation-duration: calc(9s / var(--s-mult,1)); }
  @keyframes bgx_sweep_${rid} { 0% { transform: translateX(-360px); } 55%,100% { transform: translateX(880px); } }
</style>
<pattern id="${pat}" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <line x1="0" y1="0" x2="0" y2="14" stroke="var(--c-structural)" stroke-width="calc(1 * var(--t-mult,1))" />
</pattern>
<linearGradient id="${grad}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0"   stop-color="var(--c-leader)" stop-opacity="0" />
  <stop offset="0.5" stop-color="var(--c-leader)" stop-opacity="0.35" />
  <stop offset="1"   stop-color="var(--c-leader)" stop-opacity="0" />
</linearGradient>
</defs>
<rect width="640" height="360" fill="url(#${pat})" />
<rect class="bgx_band" x="-120" y="0" width="240" height="360" fill="url(#${grad})" transform="skewX(-12)" />
</svg>`;
      }
    },
    {
      id: "bg-node-mesh", name: "Node Mesh", file: "bg_node_mesh.svg", category: "Backgrounds",
      tags: { fn: ["atmosphere"], vibe: ["ambient", "retro-tech"] },
      engine: "css", loop: true, durationMs: 14000, paramPreset: { opacity: 0.5 },
      svg(rid) {
        // Constellation near the frame edges; link groups fade in/out in a phased cycle, nodes stay lit.
        return `<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .bgn_link { stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1));
    animation: bgn_fade_${rid} 14s ease-in-out infinite; animation-duration: calc(14s / var(--s-mult,1)); opacity: 0; }
  .bgn_link.g2 { animation-delay: calc(-4.66s / var(--s-mult,1)); }
  .bgn_link.g3 { animation-delay: calc(-9.33s / var(--s-mult,1)); }
  .bgn_node { fill: var(--c-fluid); }
  @keyframes bgn_fade_${rid} { 0%,40%,100% { opacity: 0; } 12%,26% { opacity: 0.7; } }
</style></defs>
<line class="bgn_link"    x1="60"  y1="50"  x2="150" y2="90" /><line class="bgn_link"    x1="150" y1="90"  x2="110" y2="180" />
<line class="bgn_link g2" x1="540" y1="60"  x2="600" y2="140" /><line class="bgn_link g2" x1="600" y1="140" x2="520" y2="200" />
<line class="bgn_link g3" x1="120" y1="300" x2="220" y2="330" /><line class="bgn_link g3" x1="480" y1="320" x2="580" y2="290" />
<line class="bgn_link g2" x1="60"  y1="50"  x2="110" y2="180" /><line class="bgn_link g3" x1="520" y1="200" x2="580" y2="290" />
<circle class="bgn_node" cx="60"  cy="50"  r="3" /><circle class="bgn_node" cx="150" cy="90"  r="2.2" />
<circle class="bgn_node" cx="110" cy="180" r="2.6" /><circle class="bgn_node" cx="540" cy="60"  r="2.4" />
<circle class="bgn_node" cx="600" cy="140" r="3" /><circle class="bgn_node" cx="520" cy="200" r="2" />
<circle class="bgn_node" cx="120" cy="300" r="2.4" /><circle class="bgn_node" cx="220" cy="330" r="2" />
<circle class="bgn_node" cx="480" cy="320" r="2.6" /><circle class="bgn_node" cx="580" cy="290" r="3" />
</svg>`;
      }
    },
    /* ---------- WILDCARDS — loud, cinematic FX (foreground energy) ----------
       Opposite discipline to Backgrounds: fast, theatrical, accent allowed.
       Still one geometry + one signature technique each. */
    {
      id: "fx-glitch-slice", name: "Glitch Slice", file: "fx_glitch_slice.svg", category: "Wildcards",
      tags: { fn: ["state"], vibe: ["dramatic", "retro-tech"] },
      engine: "css", loop: true, durationMs: 2200,
      svg(rid) {
        const clips = ["fxg_ct_" + rid, "fxg_cm_" + rid, "fxg_cb_" + rid];
        // Abstract mark sliced into 3 bands; bands jitter on steps(), RGB-style ghosts flicker.
        const mark = `<rect x="60" y="30" width="80" height="12" /><rect x="60" y="54" width="80" height="12" /><rect x="60" y="78" width="50" height="12" />`;
        return `<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
  .fxg_mark rect { fill: var(--c-label); }
  .fxg_ghost rect { fill: var(--c-fluid); }
  .fxg_ghost.a rect { fill: var(--c-accent); }
  .fxg_ghost { opacity: 0; animation: fxg_ghost_${rid} 2.2s steps(1) infinite; animation-duration: calc(2.2s / var(--s-mult,1)); }
  .fxg_ghost.a { animation-delay: calc(-1.1s / var(--s-mult,1)); }
  .fxg_band { animation: 2.2s steps(1) infinite; animation-duration: calc(2.2s / var(--s-mult,1)); }
  .fxg_band.t { animation-name: fxg_jt_${rid}; }
  .fxg_band.m { animation-name: fxg_jm_${rid}; }
  .fxg_band.b { animation-name: fxg_jb_${rid}; }
  @keyframes fxg_ghost_${rid} { 0%,100% { opacity: 0; } 84% { opacity: 0.55; } 90% { opacity: 0; } 93% { opacity: 0.45; } 96% { opacity: 0; } }
  @keyframes fxg_jt_${rid} { 0%,100% { transform: translateX(0); } 85% { transform: translateX(-7px); } 89% { transform: translateX(3px); } 93% { transform: translateX(0); } }
  @keyframes fxg_jm_${rid} { 0%,100% { transform: translateX(0); } 86% { transform: translateX(6px); } 91% { transform: translateX(-4px); } 95% { transform: translateX(0); } }
  @keyframes fxg_jb_${rid} { 0%,100% { transform: translateX(0); } 87% { transform: translateX(-5px); } 92% { transform: translateX(5px); } 96% { transform: translateX(0); } }
</style>
<clipPath id="${clips[0]}"><rect x="0" y="0" width="200" height="50" /></clipPath>
<clipPath id="${clips[1]}"><rect x="0" y="50" width="200" height="26" /></clipPath>
<clipPath id="${clips[2]}"><rect x="0" y="76" width="200" height="44" /></clipPath>
</defs>
<g class="fxg_ghost" transform="translate(-3,0)">${mark}</g>
<g class="fxg_ghost a" transform="translate(3,0)">${mark}</g>
<g class="fxg_band t" clip-path="url(#${clips[0]})"><g class="fxg_mark">${mark}</g></g>
<g class="fxg_band m" clip-path="url(#${clips[1]})"><g class="fxg_mark">${mark}</g></g>
<g class="fxg_band b" clip-path="url(#${clips[2]})"><g class="fxg_mark">${mark}</g></g>
</svg>`;
      }
    },
    {
      id: "fx-hologram-beam", name: "Hologram Beam", file: "fx_hologram_beam.svg", category: "Wildcards",
      tags: { fn: ["atmosphere"], vibe: ["dramatic", "retro-tech"] },
      engine: "css", loop: true, durationMs: 3000,
      svg(rid) {
        const clip = "fxh_clip_" + rid;
        // Emitter → flickering light cone with rising scanlines, bobbing wireframe subject.
        let scan = "";
        for (let y = 20; y <= 178; y += 14) scan += `<line class="fxh_scan" x1="20" y1="${y}" x2="140" y2="${y}" />\n`;
        return `<svg viewBox="0 0 160 180" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
  .fxh_cone { animation: fxh_flick_${rid} 3s linear infinite; animation-duration: calc(3s / var(--s-mult,1)); }
  .fxh_fill { fill: var(--c-fluid); opacity: 0.14; }
  .fxh_edge { stroke: var(--c-fluid); stroke-width: calc(1.2 * var(--t-mult,1)); opacity: 0.6; }
  .fxh_scan { stroke: var(--c-fluid); stroke-width: calc(1 * var(--t-mult,1)); opacity: 0.35; }
  .fxh_rise { animation: fxh_rise_${rid} 1.2s linear infinite; animation-duration: calc(1.2s / var(--s-mult,1)); }
  .fxh_subj { fill: none; stroke: var(--c-label); stroke-width: calc(1.6 * var(--t-mult,1));
    animation: fxh_bob_${rid} 3s ease-in-out infinite; animation-duration: calc(3s / var(--s-mult,1)); }
  .fxh_base { fill: var(--c-structural); }
  .fxh_lens { fill: var(--c-accent); }
  @keyframes fxh_flick_${rid} { 0%,100% { opacity: 1; } 7% { opacity: 0.55; } 9% { opacity: 1; } 46% { opacity: 0.8; } 48% { opacity: 1; } 74% { opacity: 0.6; } 76% { opacity: 1; } }
  @keyframes fxh_rise_${rid} { to { transform: translateY(-14px); } }
  @keyframes fxh_bob_${rid} { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
</style>
<clipPath id="${clip}"><polygon points="70,150 90,150 130,20 30,20" /></clipPath>
</defs>
<g class="fxh_cone">
  <polygon class="fxh_fill" points="70,150 90,150 130,20 30,20" />
  <line class="fxh_edge" x1="70" y1="150" x2="30" y2="20" />
  <line class="fxh_edge" x1="90" y1="150" x2="130" y2="20" />
  <g clip-path="url(#${clip})"><g class="fxh_rise">${scan}</g></g>
  <path class="fxh_subj" d="M80,32 L104,52 L80,72 L56,52 Z M80,32 L80,72 M56,52 L104,52" />
</g>
<rect class="fxh_base" x="58" y="150" width="44" height="12" />
<circle class="fxh_lens" cx="80" cy="150" r="4" />
</svg>`;
      }
    },
    {
      id: "fx-warp-tunnel", name: "Warp Tunnel", file: "fx_warp_tunnel.svg", category: "Wildcards",
      tags: { fn: ["transition"], vibe: ["dramatic"] },
      engine: "css", loop: true, durationMs: 2000,
      svg(rid) {
        // Rings accelerating outward from center — hyperspace zoom.
        return `<svg viewBox="0 0 240 160" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxw_ring { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1));
    transform-origin: 120px 80px;
    animation: fxw_zoom_${rid} 2s cubic-bezier(0.5,0,0.9,0.4) infinite; animation-duration: calc(2s / var(--s-mult,1)); }
  .fxw_ring.i2 { animation-delay: calc(-0.5s / var(--s-mult,1)); }
  .fxw_ring.i3 { animation-delay: calc(-1s / var(--s-mult,1)); stroke: var(--c-fluid); }
  .fxw_ring.i4 { animation-delay: calc(-1.5s / var(--s-mult,1)); }
  .fxw_core { fill: var(--c-fluid); }
  @keyframes fxw_zoom_${rid} { 0% { transform: scale(0.06); opacity: 0; } 15% { opacity: 0.9; } 100% { transform: scale(1.35); opacity: 0; } }
</style></defs>
<rect class="fxw_ring"    x="20" y="14" width="200" height="132" rx="10" />
<rect class="fxw_ring i2" x="20" y="14" width="200" height="132" rx="10" />
<rect class="fxw_ring i3" x="20" y="14" width="200" height="132" rx="10" />
<rect class="fxw_ring i4" x="20" y="14" width="200" height="132" rx="10" />
<circle class="fxw_core" cx="120" cy="80" r="2.5" />
</svg>`;
      }
    },
    {
      id: "fx-cardiac-trace", name: "Cardiac Trace", file: "fx_cardiac_trace.svg", category: "Wildcards",
      tags: { fn: ["state"], vibe: ["dramatic", "retro-tech"] },
      engine: "css", loop: true, durationMs: 2400,
      svg(rid) {
        const ecg = "M0,55 L70,55 L80,48 L88,55 L96,55 L104,14 L112,86 L120,55 L140,55 L152,44 L164,55 L320,55";
        // A hot window travels the PQRST trace; wide faint duplicate fakes a glow.
        return `<svg viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxc_base { fill: none; stroke: var(--c-structural); stroke-width: calc(1 * var(--t-mult,1)); opacity: 0.4; }
  .fxc_hot, .fxc_glow { fill: none; stroke-linecap: round; stroke-dasharray: 0.22 0.78;
    animation: fxc_run_${rid} 2.4s linear infinite; animation-duration: calc(2.4s / var(--s-mult,1)); }
  .fxc_hot { stroke: var(--c-accent); stroke-width: calc(2.5 * var(--t-mult,1)); }
  .fxc_glow { stroke: var(--c-accent); stroke-width: calc(8 * var(--t-mult,1)); opacity: 0.2; }
  @keyframes fxc_run_${rid} { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
</style></defs>
<path class="fxc_base" d="${ecg}" />
<path class="fxc_glow" pathLength="1" d="${ecg}" />
<path class="fxc_hot"  pathLength="1" d="${ecg}" />
</svg>`;
      }
    },
    {
      id: "fx-hazard-strobe", name: "Hazard Strobe", file: "fx_hazard_strobe.svg", category: "Wildcards",
      tags: { fn: ["state"], vibe: ["dramatic"] },
      engine: "css", loop: true, durationMs: 1600,
      svg(rid) {
        // Marching hazard tape + a double-flash alarm overlay, then rest.
        let stripes = "";
        for (let x = -32; x < 352; x += 32) stripes += `<path class="fxz_s" d="M${x},40 L${x + 16},8 L${x + 32},8 L${x + 16},40 Z" />\n`;
        return `<svg viewBox="0 0 320 48" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxz_s { fill: var(--c-caution); }
  .fxz_march { animation: fxz_march_${rid} 0.8s linear infinite; animation-duration: calc(0.8s / var(--s-mult,1)); }
  .fxz_frame { fill: none; stroke: var(--c-structural); stroke-width: calc(2 * var(--t-mult,1)); }
  .fxz_flash { fill: var(--c-caution); opacity: 0; animation: fxz_flash_${rid} 1.6s linear infinite;
    animation-duration: calc(1.6s / var(--s-mult,1)); }
  @keyframes fxz_march_${rid} { to { transform: translateX(-32px); } }
  @keyframes fxz_flash_${rid} { 0%,15%,100% { opacity: 0; } 3% { opacity: 0.45; } 7% { opacity: 0; } 10% { opacity: 0.45; } }
</style>
<clipPath id="fxz_clip_${rid}"><rect x="6" y="8" width="308" height="32" /></clipPath>
</defs>
<g clip-path="url(#fxz_clip_${rid})"><g class="fxz_march">${stripes}</g></g>
<rect class="fxz_flash" x="6" y="8" width="308" height="32" />
<rect class="fxz_frame" x="6" y="8" width="308" height="32" />
</svg>`;
      }
    },
    {
      id: "fx-spark-shower", name: "Spark Shower", file: "fx_spark_shower.svg", category: "Wildcards",
      tags: { fn: ["state"], vibe: ["dramatic"] },
      engine: "smil", loop: true, durationMs: 1400,
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const dur = 1.4 / speedMult;
        // Ballistic sparks off a contact point — gravity arcs, streak heads.
        const sparks = [
          { p: "M100,22 Q60,30 40,120",   b: 0 },
          { p: "M100,22 Q140,28 165,110", b: dur * 0.18 },
          { p: "M100,22 Q75,45 62,130",   b: dur * 0.36 },
          { p: "M100,22 Q128,42 142,132", b: dur * 0.5 },
          { p: "M100,22 Q95,60 88,135",   b: dur * 0.64 },
          { p: "M100,22 Q152,20 185,90",  b: dur * 0.8 },
          { p: "M100,22 Q52,24 25,95",    b: dur * 0.9 }
        ];
        const g = sparks.map((s, i) => `<g data-role="motion-target">
  <line class="fxs_sp${i % 2 ? " alt" : ""}" x1="-6" y1="0" x2="0" y2="0" />
  <animateMotion dur="${dur.toFixed(3)}s" repeatCount="indefinite" begin="${s.b.toFixed(3)}s" path="${s.p}" rotate="auto" />
</g>`).join("\n");
        return `<svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxs_sp { stroke: var(--c-accent); stroke-width: calc(2.5 * var(--t-mult,1)); stroke-linecap: round; }
  .fxs_sp.alt { stroke: var(--c-leader); stroke-width: calc(1.8 * var(--t-mult,1)); }
  .fxs_pt { fill: var(--c-accent); }
</style></defs>
<circle class="fxs_pt" cx="100" cy="22" r="3.5" />
${g}
</svg>`;
      }
    },
    {
      id: "fx-arc-discharge", name: "Arc Discharge", file: "fx_arc_discharge.svg", category: "Wildcards",
      tags: { fn: ["state"], vibe: ["dramatic"] },
      engine: "css", loop: true, durationMs: 1200,
      svg(rid) {
        // Three jagged bolt variants flicker in sequence between two terminals, then a dead gap.
        const bolts = [
          "M32,50 L64,38 L88,58 L118,36 L142,54 L168,50",
          "M32,50 L58,60 L92,40 L122,62 L150,44 L168,50",
          "M32,50 L70,46 L96,64 L110,34 L146,58 L168,50"
        ];
        const layer = (d, cls) => `<g class="${cls}"><path class="fxa_glow" d="${d}" /><path class="fxa_core" d="${d}" /></g>`;
        return `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxa_core { fill: none; stroke: var(--c-label); stroke-width: calc(1.8 * var(--t-mult,1)); stroke-linejoin: round; }
  .fxa_glow { fill: none; stroke: var(--c-fluid); stroke-width: calc(6 * var(--t-mult,1)); stroke-linejoin: round; opacity: 0.35; }
  .fxa_term { fill: var(--c-structural); }
  .fxa_tip { fill: var(--c-fluid); }
  .fxa_b { opacity: 0; animation: 1.2s steps(1) infinite; animation-duration: calc(1.2s / var(--s-mult,1)); }
  .fxa_b.v1 { animation-name: fxa_f1_${rid}; }
  .fxa_b.v2 { animation-name: fxa_f2_${rid}; }
  .fxa_b.v3 { animation-name: fxa_f3_${rid}; }
  @keyframes fxa_f1_${rid} { 0% { opacity: 1; } 14% { opacity: 0; } 22% { opacity: 1; } 30%,100% { opacity: 0; } }
  @keyframes fxa_f2_${rid} { 0%,34% { opacity: 0; } 35% { opacity: 1; } 48% { opacity: 0; } 54% { opacity: 1; } 62%,100% { opacity: 0; } }
  @keyframes fxa_f3_${rid} { 0%,66% { opacity: 0; } 67% { opacity: 1; } 84%,100% { opacity: 0; } }
</style></defs>
<rect class="fxa_term" x="12" y="38" width="20" height="24" />
<rect class="fxa_term" x="168" y="38" width="20" height="24" />
<circle class="fxa_tip" cx="32" cy="50" r="3" />
<circle class="fxa_tip" cx="168" cy="50" r="3" />
${layer(bolts[0], "fxa_b v1")}
${layer(bolts[1], "fxa_b v2")}
${layer(bolts[2], "fxa_b v3")}
</svg>`;
      }
    },
    {
      id: "fx-terminal-type", name: "Terminal Type", file: "fx_terminal_type.svg", category: "Wildcards",
      tags: { fn: ["label"], vibe: ["retro-tech", "playful"] },
      engine: "css", loop: true, durationMs: 4000, roundable: true,
      hasText: true, textDefault: "> RUN DIAG_", textHint: "Terminal line",
      svg(rid) {
        const clip = "fxt_clip_" + rid;
        // Typewriter reveal on steps(); block cursor rides the reveal edge, blinks during hold.
        return `<svg viewBox="0 0 280 60" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
  .fxt_panel { fill: var(--c-panel); stroke: var(--c-structural); stroke-width: calc(1.5 * var(--t-mult,1));
    rx: var(--r-mult,0); ry: var(--r-mult,0); }
  .fxt_txt { fill: var(--c-label); font: 600 16px "Courier New", monospace; letter-spacing: 1px; }
  .fxt_reveal { transform-origin: 14px 0px;
    animation: fxt_type_${rid} 4s steps(16) infinite; animation-duration: calc(4s / var(--s-mult,1)); }
  .fxt_cursor { fill: var(--c-accent);
    animation: fxt_ride_${rid} 4s steps(16) infinite, fxt_blink_${rid} 0.5s steps(1) infinite;
    animation-duration: calc(4s / var(--s-mult,1)), calc(0.5s / var(--s-mult,1)); }
  @keyframes fxt_type_${rid} { 0% { transform: scaleX(0); } 55% { transform: scaleX(1); } 88% { transform: scaleX(1); } 89%,100% { transform: scaleX(0); } }
  @keyframes fxt_ride_${rid} { 0% { transform: translateX(0); } 55% { transform: translateX(238px); } 88% { transform: translateX(238px); } 89%,100% { transform: translateX(0); } }
  @keyframes fxt_blink_${rid} { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }
</style>
<clipPath id="${clip}"><rect class="fxt_reveal" x="14" y="10" width="238" height="40" /></clipPath>
</defs>
<rect class="fxt_panel" x="6" y="8" width="268" height="44" />
<g clip-path="url(#${clip})"><text class="fxt_txt" data-text-slot="true" x="18" y="36">&gt; RUN DIAG_</text></g>
<rect class="fxt_cursor" x="16" y="22" width="9" height="18" />
</svg>`;
      }
    },
    {
      id: "fx-redline-gauge", name: "Redline Gauge", file: "fx_redline_gauge.svg", category: "Wildcards",
      tags: { fn: ["state"], vibe: ["dramatic"] },
      engine: "css", loop: true, durationMs: 3000,
      svg(rid) {
        // Needle slams from rest into the redline zone, shakes there, drops back.
        return `<svg viewBox="0 0 160 120" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxd_arc { fill: none; stroke: var(--c-structural); stroke-width: calc(5 * var(--t-mult,1)); }
  .fxd_red { fill: none; stroke: var(--c-caution); stroke-width: calc(5 * var(--t-mult,1)); }
  .fxd_needle { stroke: var(--c-label); stroke-width: calc(3 * var(--t-mult,1)); stroke-linecap: round;
    transform-origin: 80px 88px;
    animation: fxd_swing_${rid} 3s ease-in-out infinite; animation-duration: calc(3s / var(--s-mult,1)); }
  .fxd_hub { fill: var(--c-structural); }
  .fxd_pin { fill: var(--c-caution); }
  @keyframes fxd_swing_${rid} {
    0%,10% { transform: rotate(-110deg); }
    38% { transform: rotate(96deg); } 44% { transform: rotate(84deg); }
    50% { transform: rotate(92deg); } 55% { transform: rotate(86deg); }
    60% { transform: rotate(91deg); } 66% { transform: rotate(87deg); }
    72% { transform: rotate(90deg); }
    92%,100% { transform: rotate(-110deg); } }
</style></defs>
<path class="fxd_arc" d="M27.4,107.2 A56,56 0 1 1 132.6,107.2" />
<path class="fxd_red" d="M122.9,52 A56,56 0 0 1 132.6,107.2" />
<line class="fxd_needle" x1="80" y1="88" x2="80" y2="40" />
<circle class="fxd_hub" cx="80" cy="88" r="7" />
<circle class="fxd_pin" cx="80" cy="88" r="2.5" />
</svg>`;
      }
    },
    {
      id: "fx-orbit-atoms", name: "Orbit Atoms", file: "fx_orbit_atoms.svg", category: "Wildcards",
      tags: { fn: ["point"], vibe: ["playful", "retro-tech"] },
      engine: "smil", loop: true, durationMs: 4400,
      svg(rid, speedMult) {
        speedMult = speedMult || 1;
        const ell = "M125,70 A55,20 0 1 1 15,70 A55,20 0 1 1 125,70";
        const orbit = (tilt, dur, begin, r) => `<g transform="rotate(${tilt} 70 70)">
  <path class="fxo_ring" d="${ell}" />
  <g data-role="motion-target"><circle class="fxo_e" r="${r}" />
    <animateMotion dur="${(dur / speedMult).toFixed(3)}s" repeatCount="indefinite" begin="${(begin / speedMult).toFixed(3)}s" path="${ell}" />
  </g>
</g>`;
        return `<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">
<defs><style>
  .fxo_ring { fill: none; stroke: var(--c-structural); stroke-width: calc(1.2 * var(--t-mult,1)); opacity: 0.7; }
  .fxo_e { fill: var(--c-fluid); }
  .fxo_n { fill: var(--c-accent); }
  .fxo_n2 { fill: none; stroke: var(--c-accent); stroke-width: calc(1 * var(--t-mult,1)); opacity: 0.5; }
</style></defs>
${orbit(0, 2.2, 0, 3)}
${orbit(60, 3.1, 0.7, 2.4)}
${orbit(120, 4.4, 1.5, 2.7)}
<circle class="fxo_n" cx="70" cy="70" r="5" />
<circle class="fxo_n2" cx="70" cy="70" r="9" />
</svg>`;
      }
    }
  ];

/* ---------------------------------------------------------------------------
 * OverlayEngine — rasterizes an overlay's animation loop to a set of cached
 * canvas frames, for consumers that composite overlays onto their own canvas
 * (e.g. Mockup Studio). The Overlay Asset Customizer has its own in-file
 * pipeline; this is the standalone port so overlays render anywhere.
 *
 * Colours are resolved from a supplied palette (role -> value) set as inline
 * CSS custom properties on the SVG root, so each frame's serialized markup is
 * self-resolving when loaded as an <img> (no document-context dependency).
 * ------------------------------------------------------------------------- */
(function () {
  var SVGNS = "http://www.w3.org/2000/svg";
  var RID = 0;

  // Overlay colour roles + sensible cross-scene defaults (white-ish structure,
  // teal flow, orange accent) — readable over most mockup backgrounds.
  var DEFAULT_PALETTE = {
    "--c-structural": "#E8EEF2",
    "--c-fluid": "#4FD1D9",
    "--c-accent": "#F08A3C",
    "--c-leader": "#E8E8E8",
    "--c-panel-base": "#001A33",
    "--c-panel": "rgba(0,26,51,0.85)",
    "--c-label": "#F5F7F8",
    "--c-caution": "#E0342B"
  };

  var HOLDER = null;
  function getHolder() {
    if (!HOLDER) {
      HOLDER = document.createElement("div");
      HOLDER.setAttribute("aria-hidden", "true");
      HOLDER.style.cssText = "position:fixed;left:-99999px;top:0;width:1200px;height:1200px;pointer-events:none;opacity:0;";
      document.body.appendChild(HOLDER);
    }
    return HOLDER;
  }

  function svgToImage(markup) {
    return new Promise(function (resolve, reject) {
      var blob = new Blob([markup], { type: "image/svg+xml;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var img = new Image();
      img.onload = function () { resolve(img); URL.revokeObjectURL(url); };
      img.onerror = function (e) { URL.revokeObjectURL(url); reject(e); };
      img.src = url;
    });
  }

  function matrixToString(m) { return "matrix(" + m.a + "," + m.b + "," + m.c + "," + m.d + "," + m.e + "," + m.f + ")"; }

  function bakeCssFreeze(svgEl) {
    var clone = svgEl.cloneNode(true);
    var liveAll = svgEl.querySelectorAll("*");
    var cloneAll = clone.querySelectorAll("*");
    liveAll.forEach(function (liveEl, i) {
      var cs = getComputedStyle(liveEl);
      if (cs.animationName && cs.animationName !== "none") {
        var t = cloneAll[i];
        t.style.animation = "none";
        t.style.opacity = cs.opacity;
        t.style.transform = cs.transform;
        if (cs.strokeDashoffset && cs.strokeDashoffset !== "none") t.style.strokeDashoffset = cs.strokeDashoffset;
      }
    });
    return clone;
  }

  function bakeSmilFreeze(svgEl) {
    var clone = svgEl.cloneNode(true);
    try {
      var livePatterns = svgEl.querySelectorAll("pattern");
      var clonePatterns = clone.querySelectorAll("pattern");
      livePatterns.forEach(function (liveP, i) {
        var cloneP = clonePatterns[i];
        var mat = liveP.patternTransform.baseVal.numberOfItems
          ? liveP.patternTransform.baseVal.consolidate().matrix : null;
        if (mat) cloneP.setAttribute("patternTransform", matrixToString(mat));
        var animEl = cloneP.querySelector("animateTransform");
        if (animEl) animEl.remove();
      });
      var liveMotion = svgEl.querySelectorAll('[data-role="motion-target"]');
      var cloneMotion = clone.querySelectorAll('[data-role="motion-target"]');
      var rootCtm = svgEl.getCTM();
      liveMotion.forEach(function (liveEl, i) {
        var cloneEl = cloneMotion[i];
        var elCtm = liveEl.getCTM();
        var mat = (rootCtm && elCtm) ? rootCtm.inverse().multiply(elCtm) : null;
        if (mat) cloneEl.setAttribute("transform", matrixToString(mat));
        var animEl = cloneEl.querySelector("animateMotion");
        if (animEl) animEl.remove();
      });
    } catch (e) { /* clone stays as an unfrozen fallback */ }
    return clone;
  }

  function rasterize(svgEl, w, h, scale, engine) {
    var frozen = engine === "css" ? bakeCssFreeze(svgEl)
      : engine === "smil" ? bakeSmilFreeze(svgEl)
      : svgEl.cloneNode(true);
    var markup = new XMLSerializer().serializeToString(frozen);
    return svgToImage(markup).then(function (img) {
      var cvs = document.createElement("canvas");
      cvs.width = Math.max(1, Math.round(w * scale));
      cvs.height = Math.max(1, Math.round(h * scale));
      cvs.getContext("2d").drawImage(img, 0, 0, cvs.width, cvs.height);
      return cvs;
    });
  }

  // Pre-render one animation loop to N canvas frames. Speed/size/rotation are
  // NOT baked here — the consumer applies playback speed via frame indexing and
  // size/rotation/opacity/position at draw time. Only thickness + colours (which
  // live inside the SVG) are baked.
  //   returns { frames:[canvas], w, h, durationMs }
  async function preRenderFrames(asset, opts) {
    opts = opts || {};
    var N = opts.frames || 24;
    var scale = opts.scale || 2;
    var thickness = opts.thickness != null ? opts.thickness : 1;
    var roundness = opts.roundness != null ? opts.roundness : 0;
    var palette = Object.assign({}, DEFAULT_PALETTE, opts.palette || {});

    var holder = getHolder();
    holder.innerHTML = asset.svg("ov" + (RID++), 1);
    var svgEl = holder.querySelector("svg");
    if (!svgEl) return { frames: [], w: 1, h: 1, durationMs: asset.durationMs || 1000 };

    Object.keys(palette).forEach(function (k) { svgEl.style.setProperty(k, palette[k]); });
    svgEl.style.setProperty("--t-mult", thickness);
    svgEl.style.setProperty("--s-mult", 1);
    if (asset.roundable) svgEl.style.setProperty("--r-mult", roundness + "px");

    var vb = svgEl.viewBox.baseVal;
    var w = (vb && vb.width) ? vb.width : 300;
    var h = (vb && vb.height) ? vb.height : 150;
    svgEl.setAttribute("width", w);
    svgEl.setAttribute("height", h);

    var dur = asset.durationMs || 1000;
    var frames = [];

    if (asset.engine === "css") {
      var anims = svgEl.getAnimations ? svgEl.getAnimations({ subtree: true }) : [];
      anims.forEach(function (a) { a.pause(); });
      for (var i = 0; i < N; i++) {
        anims.forEach(function (a) { a.currentTime = (dur / N) * i; });
        frames.push(await rasterize(svgEl, w, h, scale, "css"));
      }
      anims.forEach(function (a) { a.cancel(); });
    } else if (asset.engine === "smil") {
      svgEl.pauseAnimations();
      var motionBegins = Array.prototype.map.call(svgEl.querySelectorAll("animateMotion"),
        function (el) { return parseFloat(el.getAttribute("begin")) || 0; });
      var startOffset = motionBegins.length ? Math.max.apply(Math, motionBegins) : 0;
      for (var j = 0; j < N; j++) {
        svgEl.setCurrentTime(startOffset + (dur / 1000 / N) * j);
        frames.push(await rasterize(svgEl, w, h, scale, "smil"));
      }
      svgEl.unpauseAnimations();
    } else {
      frames.push(await rasterize(svgEl, w, h, scale, "static"));
    }

    holder.innerHTML = "";
    return { frames: frames, w: w, h: h, durationMs: dur };
  }

  function categories() {
    var seen = [], out = [];
    (window.RENKON_OVERLAYS || []).forEach(function (a) {
      if (seen.indexOf(a.category) === -1) { seen.push(a.category); out.push(a.category); }
    });
    return out;
  }

  window.OverlayEngine = {
    preRenderFrames: preRenderFrames,
    DEFAULT_PALETTE: DEFAULT_PALETTE,
    categories: categories,
    assets: function () { return window.RENKON_OVERLAYS || []; },
    byId: function (id) { return (window.RENKON_OVERLAYS || []).filter(function (a) { return a.id === id; })[0] || null; }
  };
})();

