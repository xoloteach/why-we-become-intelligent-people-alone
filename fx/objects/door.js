// wwb-3d-v1-door — an empty room is not a threat: the door swings open and warm light spills out (deliberate).
import { ease, clamp01 } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-door', version: 1, name: 'open door', tags: ['solitude', 'quiet room', 'fear', 'openness', 'invitation'],
  metaphor: 'Stepping into a quiet room: the door opens and the empty space is warm, not frightening.', physics: false,
  view: { center: [0, 0.46, 0.05], height: 1.12, elev: 8, azim: -24 } };
const DW = 0.42, DH = 0.82, FT = 0.045;
const backOut = (u) => { u = clamp01(u); const s = 1.4; return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2; };
export function build(T, S, P) {
  const root = new T.Group(); root.userData.ground = true; root.userData.shadowOpacity = 0.16; const parts = { door: root };
  const fc = 0xE2D9CA; const box = (w, h, d, c, x, y, z, o = {}, par = root) => { const m = S.inked(new T.BoxGeometry(w, h, d), S.toon(c), o); m.position.set(x, y, z); par.add(m); return m; };
  box(FT, DH + FT, 0.09, fc, -(DW / 2 + FT / 2), (DH + FT) / 2, 0); box(FT, DH + FT, 0.09, fc, DW / 2 + FT / 2, (DH + FT) / 2, 0); box(DW + 2 * FT, FT, 0.09, fc, 0, DH + FT / 2, 0);
  box(DW + 2 * FT + 0.04, 0.012, 0.11, 0xB9B1A3, 0, 0.006, 0.005);
  const gm = S.flat(0xF6DDA0); gm.userData.keepOpacity = true; const glow = new T.Mesh(new T.PlaneGeometry(DW, DH), gm); glow.position.set(0, DH / 2 + 0.012, -0.03); root.add(glow);
  const sm = S.flat(0xF6DDA0); sm.userData.keepOpacity = true; const sh = new T.Shape(); sh.moveTo(-DW / 2, 0); sh.lineTo(DW / 2, 0); sh.lineTo(DW / 2 + 0.16, -0.46); sh.lineTo(-DW / 2 + 0.06, -0.46); sh.lineTo(-DW / 2, 0);
  const spill = new T.Mesh(new T.ShapeGeometry(sh), sm); spill.rotation.x = -Math.PI / 2; spill.position.set(0, 0.0125, 0.045); root.add(spill);
  const side = P.hinge ?? -1; const hinge = new T.Group(); hinge.position.set(side * DW / 2, 0, 0.0); root.add(hinge);
  const slab = box(DW - 0.008, DH - 0.006, 0.028, 0xD8CDBB, -side * DW / 2, DH / 2 + 0.012, 0, { jitter: 0.0012 }, hinge);
  const z = 0.0145, px = -side * DW / 2; const rect = (x0, y0, x1, y1) => hinge.add(S.inkLine([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z], [x0, y0, z]], { linePx: 1.6 }));
  rect(px - 0.14, 0.47, px + 0.14, 0.76); rect(px - 0.14, 0.07, px + 0.14, 0.38);
  const knob = S.inked(new T.SphereGeometry(0.019, 14, 10), S.toon(S.PALETTE.gold), { edges: false, hullPx: 1.4 }); knob.position.set(-side * (DW - 0.05), 0.43, 0.03); hinge.add(knob);
  root.userData.fx = { hinge, gm, sm, side }; return { root, parts };
}
export function animate(parts, t, P, job) {
  const root = parts.door, ud = root.userData.fx; job.S.reveal(root, t - (P.appear ?? 0)); const ro = root.userData.revealOpacity ?? 0;
  const c = (P.cues || [0.8])[0], dur = P.dur ?? 1.1, A = P.angle ?? 1.15; const u = backOut((t - c) / dur);
  ud.hinge.rotation.y = ud.side * A * u; const open = clamp01(u);
  ud.gm.opacity = ro * clamp01(open * 4); ud.gm.transparent = true; ud.sm.opacity = ro * 0.62 * open; ud.sm.transparent = true;
}
