// wwb-3d-v1-clock — time slipping away: the minute hand sweeps and a glowing wedge marks the lost minutes (deliberate).
import { easeInOut, ease, clamp01 } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-clock', version: 1, name: 'alarm clock', tags: ['time', 'lost time', 'distraction', 'hours', 'routine'],
  metaphor: 'Minutes disappearing: the hand sweeps and the lost time lights up.', physics: false,
  view: { center: [0, 0.28, 0], height: 0.7, elev: 6, azim: -18 } };
const RR = 0.2, CY = 0.29;
export function build(T, S, P) {
  const root = new T.Group(); root.userData.ground = true; root.userData.shadowOpacity = 0.18; const parts = { clock: root };
  const c = new T.Group(); c.position.y = CY; root.add(c);
  const rim = S.inked(new T.CylinderGeometry(RR, RR, 0.07, 44, 1), S.toon(S.PALETTE.rust), { edgeAngle: 50 }); rim.rotation.x = Math.PI / 2; c.add(rim);
  const face = new T.Mesh(new T.CircleGeometry(RR - 0.022, 48), S.flat(0xF7F1E6)); face.position.z = 0.0385; c.add(face);
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2, r0 = i % 3 ? 0.152 : 0.138, r1 = 0.166; c.add(S.inkLine([[Math.sin(a) * r0, Math.cos(a) * r0, 0.041], [Math.sin(a) * r1, Math.cos(a) * r1, 0.041]], { linePx: i % 3 ? 1.6 : 2.6 })); }
  const wm = S.flat(S.PALETTE.gold); wm.userData.keepOpacity = true; const wedge = new T.Mesh(new T.CircleGeometry(0.13, 2), wm); wedge.position.z = 0.0395; c.add(wedge);
  const hand = (len, wid, z) => { const p = new T.Group(); const m = S.inked(new T.BoxGeometry(wid, len, 0.006), S.toon(0x2A2823), { hullPx: 1.2, edges: false }); m.position.y = len / 2 - 0.018; p.add(m); p.position.z = z; c.add(p); return p; };
  const hourH = hand(0.1, 0.017, 0.044), minH = hand(0.148, 0.011, 0.05);
  const cap = S.inked(new T.SphereGeometry(0.014, 14, 10), S.toon(S.PALETTE.gold), { edges: false, hullPx: 1.4 }); cap.position.z = 0.056; c.add(cap);
  for (const s of [-1, 1]) {
    const bell = S.inked(new T.SphereGeometry(0.058, 18, 10, 0, Math.PI * 2, 0, Math.PI / 2), S.toon(0xB9B1A3), { edgeAngle: 60 }); bell.position.set(s * 0.13, RR * 0.86, 0); bell.rotation.z = -s * 0.55; c.add(bell);
    const foot = S.inked(new T.CylinderGeometry(0.014, 0.02, 0.07, 10), S.toon(0x4A4740), { edges: false, hullPx: 1.4 }); foot.position.set(s * 0.12, -RR - 0.012, 0); foot.rotation.z = s * 0.35; c.add(foot);
  }
  const bar = S.inked(new T.CylinderGeometry(0.008, 0.008, 0.2, 8), S.toon(0x4A4740), { edges: false, hullPx: 1.2 }); bar.rotation.z = Math.PI / 2; bar.position.y = RR + 0.052; c.add(bar);
  root.userData.fx = { c, wedge, hourH, minH, T };
  return { root, parts };
}
export function animate(parts, t, P, job) {
  const root = parts.clock, ud = root.userData.fx, T = ud.T; job.S.reveal(root, t - (P.appear ?? 0));
  const cue = (P.cues || [0.8])[0], dur = P.dur ?? 1.8, sweep = (P.sweep ?? 120) * Math.PI / 180, m0 = (P.startMin ?? 0) / 60 * Math.PI * 2, h0 = (P.startHour ?? 10) / 12 * Math.PI * 2 + m0 / 12;
  const u = easeInOut((t - cue) / dur); const a = sweep * u;
  ud.minH.rotation.z = -(m0 + a); ud.hourH.rotation.z = -(h0 + a / 12);
  const len = Math.max(0.0001, a); ud.wedge.geometry.dispose(); ud.wedge.geometry = new T.CircleGeometry(0.13, Math.max(2, Math.ceil(len / 0.06)), Math.PI / 2 - m0 - len, len);
  ud.wedge.material.opacity = (root.userData.revealOpacity ?? 0) * 0.55 * clamp01(a / 0.05); ud.wedge.material.transparent = true; ud.wedge.visible = root.visible && a > 0.001;
  const w = clamp01((t - cue - dur) / 0.45); ud.c.rotation.z = 0.05 * Math.sin(w * Math.PI * 3) * (1 - w) * (w > 0 ? 1 : 0);
}
