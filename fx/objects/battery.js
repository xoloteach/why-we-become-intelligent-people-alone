// wwb-3d-v1-battery — social battery: drains on "exhausted", recharges on "recharge" (deliberate, preset easing).
import { ease, easeInOut, spring, clamp01, lerp } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-battery', version: 1, name: 'battery', tags: ['energy', 'social battery', 'recharge', 'exhaustion'],
  metaphor: 'Social energy draining in company and refilling in solitude.', physics: false,
  view: { center: [0, 0.25, 0], height: 0.66, elev: 10, azim: -22 } };
const H = 0.42, WIN = { x: 0.085, y0: 0.045, y1: 0.375 };
export function build(T, S, P) {
  const root = new T.Group(); root.userData.ground = true; const parts = { battery: root };
  const casing = S.inked(new T.BoxGeometry(0.24, H, 0.15, 2, 3, 2), S.toon(0xEFE7DA), { jitter: 0.002 }); casing.position.y = H / 2; root.add(casing);
  const nub = S.inked(new T.BoxGeometry(0.09, 0.035, 0.07), S.toon(S.PALETTE.warmGrey)); nub.position.y = H + 0.0175; root.add(nub);
  const z = 0.0765;
  root.add(S.inkLine([[-WIN.x, WIN.y0, z], [WIN.x, WIN.y0, z], [WIN.x, WIN.y1, z], [-WIN.x, WIN.y1, z], [-WIN.x, WIN.y0, z]], { linePx: 2.2 }));
  const lvlMat = S.toon(S.PALETTE.rust); const lvl = new T.Mesh(new T.BoxGeometry(WIN.x * 2 - 0.016, 1, 0.01), lvlMat); lvl.position.z = z - 0.002; root.add(lvl); parts.level = lvl;
  for (let i = 1; i < 4; i++) { const yy = WIN.y0 + (WIN.y1 - WIN.y0) * i / 4; root.add(S.inkLine([[-WIN.x, yy, z + 0.001], [WIN.x, yy, z + 0.001]], { linePx: 1.2 })); }
  const bolt = new T.Shape(); [[0.02, 0.06], [-0.03, -0.005], [0.0, -0.005], [-0.02, -0.06], [0.03, 0.005], [0.0, 0.005]].forEach(([x, y], i) => i ? bolt.lineTo(x, y) : bolt.moveTo(x, y));
  const boltMesh = new T.Mesh(new T.ShapeGeometry(bolt), S.flat(S.PALETTE.gold)); boltMesh.position.set(0, (WIN.y0 + WIN.y1) / 2, z + 0.004); root.add(boltMesh); parts.bolt = boltMesh;
  root.userData.lvlMat = lvlMat; return { root, parts };
}
export function animate(parts, t, P, job) {
  const root = parts.battery; job.S.reveal(root, t - (P.appear ?? 0));
  const c = (P.cues || [0.6])[0], dur = P.dur ?? 1.4; const from = P.from ?? 0.85, to = P.to ?? 0.12;
  const u = P.mode === 'charge' ? spring((t - c) / dur) : easeInOut((t - c) / dur);
  const level = lerp(from, to, u); const h = (WIN.y1 - WIN.y0 - 0.012) * Math.max(0.02, level);
  parts.level.scale.y = h; parts.level.position.y = WIN.y0 + 0.006 + h / 2;
  const full = P.mode === 'charge' ? clamp01((level - 0.82) / 0.1) : 0; parts.bolt.visible = root.visible && full > 0.5; if (parts.bolt.material) parts.bolt.material.opacity = full;
  if (P.mode === 'charge') { const pop = Math.sin(clamp01((t - c - dur * 0.8) / 0.35) * Math.PI) * 0.035; root.scale.setScalar(1 + pop); root.rotation.z = lerp(-0.07, 0, ease((t - c) / 0.8)); }
  else root.rotation.z = -0.07 * easeInOut((t - c - dur * 0.6) / 0.8);
}
