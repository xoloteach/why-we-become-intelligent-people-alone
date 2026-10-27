// wwb-3d-v1-stairs — quiet progress: steps drop into place one by one, a flag rises on the last (Rapier).
import { quatFromEuler, spring } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-stairs', version: 1, name: 'progress steps', tags: ['progress', 'goals', 'growth', 'quiet achievement', 'steps'],
  metaphor: 'Steady progress built step by step without an audience; the flag marks the goal.', physics: true,
  view: { center: [0, 0.28, 0], height: 0.82, elev: 14, azim: -28 } };
const BW = 0.14, BD = 0.2, GAP = 0.014;
function hs(P) { const n = P.count || 4; return Array.from({ length: n }, (_, i) => 0.11 * (i + 1)); }
function xs(P) { const n = (P.count || 4); return hs(P).map((_, i) => (i - (n - 1) / 2) * (BW + GAP)); }
export function build(T, S, P) {
  const root = new T.Group(); const parts = {}; const H = hs(P), X = xs(P);
  H.forEach((h, i) => {
    const g = new T.Group(); g.userData.ground = true; g.userData.shadowOpacity = 0.18;
    const body = S.inked(new T.BoxGeometry(BW, h - 0.02, BD, 1, Math.max(1, Math.round(h / 0.11)), 1), S.toon(0xEFE7DA), { jitter: 0.0015 }); body.position.y = -0.01; g.add(body);
    const top = S.inked(new T.BoxGeometry(BW, 0.02, BD), S.toon(S.PALETTE.rust)); top.position.y = h / 2 - 0.01; g.add(top);
    if (i === H.length - 1 && P.flag !== false) {
      const flag = new T.Group(); flag.position.y = h / 2;
      const pole = S.inked(new T.CylinderGeometry(0.0055, 0.0055, 0.17, 8), S.toon(0x4A4740), { edges: false, hullPx: 1.4 }); pole.position.y = 0.085; flag.add(pole);
      const sh = new T.Shape(); sh.moveTo(0, 0); sh.lineTo(0.095, -0.032); sh.lineTo(0, -0.064); sh.lineTo(0, 0);
      const fm = S.toon(S.PALETTE.rust, { side: T.DoubleSide }); const fl = new T.Mesh(new T.ShapeGeometry(sh), fm); fl.position.set(0.005, 0.168, 0); flag.add(fl);
      flag.add(S.inkLine([[0.005, 0.168, 0.001], [0.1, 0.136, 0.001], [0.005, 0.104, 0.001]], { linePx: 1.8 }));
      g.add(flag); g.userData.flag = flag;
    }
    g.position.set(X[i], h / 2 + 0.1, 0); root.add(g); parts['s' + i] = g;
  });
  return { root, parts };
}
export function physics(R, world, P) {
  const bodies = {}, drops = []; const H = hs(P), X = xs(P);
  H.forEach((h, i) => {
    const rb = world.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(X[i], h / 2 + 0.1, 0).setRotation(quatFromEuler(0, 0.03 * (i % 2 ? 1 : -1), 0)).setCcdEnabled(true).setAngularDamping(3.0));
    world.createCollider(R.ColliderDesc.cuboid(BW / 2, h / 2, BD / 2).setDensity(420).setFriction(1.0).setRestitution(0.0).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), rb);
    bodies['s' + i] = rb; drops.push({ body: 's' + i, cue: (P.cues || [])[i] ?? (P.cues || [0.8])[0] + i * 0.5, fall: 0.15 });
  });
  return { bodies, drops };
}
export function animate(parts, t, P, job) {
  const names = Object.keys(parts); names.forEach((n) => job.S.reveal(parts[n], t - (job.appear?.[n] ?? 0)));
  const last = parts[names[names.length - 1]]; const flag = last.userData.flag;
  if (flag) { const cl = (P.cues || [])[names.length - 1] ?? 1; const u = spring((t - cl - 0.15) / 0.55); flag.visible = last.visible && u > 0.01; flag.scale.set(1, Math.max(0.001, u), 1); }
}
