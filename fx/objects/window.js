// wwb-3d-v1-window — two identical lit windows: from outside, two lives look exactly the same (deliberate).
import { ease, spring, clamp01 } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-window', version: 1, name: 'lit windows', tags: ['outside view', 'appearances', 'same but different', 'home', 'privacy'],
  metaphor: 'From the outside two lives look the same: identical lit windows, one figure in each.', physics: false,
  view: { center: [0, 0, 0], height: 0.66, elev: 4, azim: -16 } };
const FW = 0.26, FH = 0.34, BAR = 0.024, DEP = 0.05;
function xs(P) { const n = P.count || 2; return Array.from({ length: n }, (_, i) => (i - (n - 1) / 2) * (P.spacing || 0.35)); }
export function build(T, S, P) {
  const root = new T.Group(); const parts = {};
  xs(P).forEach((x, i) => {
    const g = new T.Group(); const fr = 0xEFE7DA;
    const box = (w, h, d, c, px, py, pz, o = {}) => { const m = S.inked(new T.BoxGeometry(w, h, d), S.toon(c), o); m.position.set(px, py, pz); g.add(m); return m; };
    box(FW, BAR, DEP, fr, 0, FH / 2 - BAR / 2, 0); box(FW, BAR, DEP, fr, 0, -FH / 2 + BAR / 2, 0);
    box(BAR, FH - 2 * BAR, DEP, fr, -FW / 2 + BAR / 2, 0, 0); box(BAR, FH - 2 * BAR, DEP, fr, FW / 2 - BAR / 2, 0, 0);
    box(0.012, FH - 2 * BAR, 0.026, fr, 0, 0, 0.004, { hullPx: 1.4 }); box(FW - 2 * BAR, 0.012, 0.026, fr, 0, 0.03, 0.004, { hullPx: 1.4 });
    box(FW + 0.05, 0.022, 0.08, S.PALETTE.rust, 0, -FH / 2 - 0.011, 0.016);
    const pm = S.flat(0x2B2925); pm.userData.keepOpacity = true; const pane = new T.Mesh(new T.PlaneGeometry(FW - 2 * BAR + 0.004, FH - 2 * BAR + 0.004), pm); pane.position.z = -0.012; g.add(pane);
    const fig = new T.Group(); const fm = S.flat(0x2A2823); fm.userData.keepOpacity = true;
    const head = new T.Mesh(new T.CircleGeometry(0.026, 24), fm); head.position.set(0.035, -0.035, 0); fig.add(head);
    const sh = new T.Shape(); sh.moveTo(-0.055, -0.15); sh.quadraticCurveTo(-0.052, -0.07, 0.035, -0.068); sh.quadraticCurveTo(0.11, -0.07, 0.112, -0.15); sh.lineTo(-0.055, -0.15);
    fig.add(new T.Mesh(new T.ShapeGeometry(sh, 10), fm)); fig.position.z = -0.008; g.add(fig);
    g.userData.fx = { pm, fm, fig }; g.position.x = x; root.add(g); parts['win' + i] = g;
  });
  return { root, parts };
}
export function animate(parts, t, P, job) {
  const cues = P.cues || [0.8];
  Object.keys(parts).forEach((n, i) => {
    const g = parts[n], ud = g.userData.fx; job.S.reveal(g, t - (P.appear ?? 0) - i * (P.stagger ?? 0.12)); const ro = g.userData.revealOpacity ?? 0;
    const c = cues[i] ?? cues[0]; const lit = ease((t - c) / 0.3);
    ud.pm.color.setHex(0x2B2925).lerp(new ud.pm.color.constructor(0xF6DDA0), lit); ud.pm.opacity = ro; ud.pm.transparent = ro < 0.999;
    ud.fm.opacity = ro * clamp01((lit - 0.25) / 0.6); ud.fm.transparent = true; ud.fig.visible = g.visible && lit > 0.25;
    const pop = Math.sin(clamp01((t - c) / 0.4) * Math.PI) * 0.035; g.scale.setScalar(1 + pop);
  });
}
