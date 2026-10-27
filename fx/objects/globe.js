// wwb-3d-v1-globe — the world shrinking or growing: a slowly spinning desk globe scales on its cue (deliberate).
import { easeInOut, spring, lerp } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-globe', version: 1, name: 'desk globe', tags: ['world', 'society', 'participation', 'isolation', 'perspective'],
  metaphor: 'Your world getting smaller when you withdraw, or bigger when you take part.', physics: false,
  view: { center: [0, 0.3, 0], height: 0.8, elev: 10, azim: -20 } };
const GR = 0.19, GY = 0.36;
export function build(T, S, P) {
  const root = new T.Group(); root.userData.ground = true; root.userData.shadowOpacity = 0.2; const parts = { globe: root };
  const base = S.inked(new T.CylinderGeometry(0.1, 0.115, 0.03, 30), S.toon(0xB9B1A3), { edgeAngle: 40 }); base.position.y = 0.015; root.add(base);
  const post = S.inked(new T.CylinderGeometry(0.012, 0.016, GY - GR - 0.01, 10), S.toon(0x4A4740), { edges: false, hullPx: 1.4 }); post.position.y = 0.03 + (GY - GR - 0.01) / 2 - 0.01; root.add(post);
  const tilt = new T.Group(); tilt.position.y = GY; tilt.rotation.z = -0.41; root.add(tilt);
  const arc = S.inked(new T.TorusGeometry(GR + 0.024, 0.0075, 6, 48, Math.PI * 1.15), S.toon(0x4A4740), { edges: false, hullPx: 1.4 }); arc.rotation.z = -Math.PI * 0.075 + Math.PI / 2; arc.position.z = -0.004; tilt.add(arc);
  const spin = new T.Group(); tilt.add(spin);
  spin.add(S.inked(new T.SphereGeometry(GR, 40, 28), S.toon(0xF3EBDD), { edges: false, hullPx: 2.6 }));
  const land = S.toon(0xB9B1A3); [[0.3, 0.9, 0.42], [0.62, 1.1, 0.3], [0.1, 1.35, 0.26], [2.3, 0.8, 0.36], [2.55, 1.15, 0.3], [3.9, 1.5, 0.4], [4.25, 1.2, 0.24], [5.3, 0.55, 0.28]].forEach(([lon, colat, r]) => {
    const m = new T.Mesh(new T.SphereGeometry(GR * 1.004, 18, 6, 0, Math.PI * 2, 0, r), land); m.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), new T.Vector3(Math.sin(colat) * Math.cos(lon), Math.cos(colat), Math.sin(colat) * Math.sin(lon))); spin.add(m); });
  const circ = (r, y, n = 64) => Array.from({ length: n + 1 }, (_, i) => { const a = i / n * Math.PI * 2; return [r * Math.cos(a), y, r * Math.sin(a)]; });
  const R1 = GR * 1.008;
  for (let k = 0; k < 4; k++) { const a = k * Math.PI / 4; spin.add(S.inkLine(Array.from({ length: 65 }, (_, i) => { const b = i / 64 * Math.PI * 2; return [R1 * Math.cos(b) * Math.cos(a), R1 * Math.sin(b), R1 * Math.cos(b) * Math.sin(a)]; }), { linePx: 1.2 })); }
  for (const lat of [-0.62, 0.62]) spin.add(S.inkLine(circ(R1 * Math.cos(lat), R1 * Math.sin(lat)), { linePx: 1.2 }));
  spin.add(S.inkLine(circ(R1 * 1.002, 0), { linePx: 2.6, color: S.PALETTE.rust }));
  const pin = S.inked(new T.SphereGeometry(0.012, 12, 8), S.toon(S.PALETTE.gold), { edges: false, hullPx: 1.2 }); pin.position.y = GR + 0.024; tilt.add(pin);
  root.userData.fx = { spin }; return { root, parts };
}
export function animate(parts, t, P, job) {
  const root = parts.globe; job.S.reveal(root, t - (P.appear ?? 0));
  root.userData.fx.spin.rotation.y = (P.spin0 ?? 0.4) + t * (P.spinRate ?? 0.35);
  const c = (P.cues || [0.8])[0], dur = P.dur ?? 1.6; const u = (P.from ?? 1) < (P.to ?? 0.55) ? spring((t - c) / dur) : easeInOut((t - c) / dur);
  root.scale.setScalar(lerp(P.from ?? 1, P.to ?? 0.55, u));
}
