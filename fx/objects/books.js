// wwb-3d-v1-books — quiet projects stacking up: each pursuit lands as a book on the pile (Rapier).
import { quatFromEuler } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-books', version: 1, name: 'book stack', tags: ['learning', 'study', 'deep work', 'projects', 'growth'],
  metaphor: 'Private pursuits piling up one by one: each one lands as a book on the stack.', physics: true,
  view: { center: [0, 0.24, 0], height: 0.74, elev: 20, azim: -24 } };
const B = { w: 0.30, h: 0.05, d: 0.21 };
const COL = [0xC8623C, 0xEFE7DA, 0x8E877C, 0xE8B33A, 0xB9B1A3];
function layout(P) { const n = P.count || 4; return Array.from({ length: n }, (_, i) => ({ x: [0, 0.018, -0.014, 0.01, -0.006][i % 5], y: B.h / 2 + i * B.h + 0.17, ry: [0.05, -0.16, 0.12, -0.07, 0.15][i % 5], rx: i % 2 ? 0.07 : -0.06, rz: [0.05, -0.04, 0.06, -0.05, 0.03][i % 5] })); }
export function build(T, S, P) {
  const root = new T.Group(); const parts = {};
  layout(P).forEach((L, i) => {
    const g = new T.Group(); g.userData.ground = i === 0; g.userData.shadowOpacity = 0.22;
    const c = COL[((P.colorOffset || 0) + i) % COL.length];
    for (const s of [-1, 1]) { const bd = S.inked(new T.BoxGeometry(B.w, 0.008, B.d), S.toon(c), { jitter: 0.0012 }); bd.position.y = s * (B.h / 2 - 0.004); g.add(bd); }
    const spine = S.inked(new T.BoxGeometry(B.w, B.h, 0.012), S.toon(c)); spine.position.z = B.d / 2 - 0.006; g.add(spine);
    const pages = S.inked(new T.BoxGeometry(B.w - 0.014, B.h - 0.016, B.d - 0.014), S.toon(0xF7F1E6), { edgeAngle: 40, hullPx: 1.6 }); pages.position.z = -0.004; g.add(pages);
    const z = B.d / 2 + 0.0008, ink = c === 0x8E877C || c === 0xC8623C ? 0xF7F1E6 : 0x16150F;
    g.add(S.inkLine([[-0.09, 0, z], [0.05, 0, z]], { linePx: 2.2, color: ink }));
    for (const xx of [-0.125, 0.125]) g.add(S.inkLine([[xx, -B.h / 2 + 0.01, z], [xx, B.h / 2 - 0.01, z]], { linePx: 1.4, color: ink }));
    for (const yy of [-0.008, 0.0, 0.008]) g.add(S.inkLine([[-B.w / 2 + 0.006, yy, -B.d / 2 + 0.012], [-B.w / 2 + 0.006, yy, B.d / 2 - 0.016]], { linePx: 1.0 }));
    g.position.set(L.x, L.y, 0); root.add(g); parts['b' + i] = g;
  });
  return { root, parts };
}
export function physics(R, world, P) {
  const bodies = {}, drops = [];
  layout(P).forEach((L, i) => {
    const rb = world.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(L.x, L.y, 0).setRotation(quatFromEuler(L.rx, L.ry, L.rz)).setCcdEnabled(true).setAngularDamping(0.5));
    world.createCollider(R.ColliderDesc.cuboid(B.w / 2, B.h / 2, B.d / 2).setDensity(600).setFriction(0.85).setRestitution(0.02).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), rb);
    bodies['b' + i] = rb; drops.push({ body: 'b' + i, cue: (P.cues || [])[i] ?? (P.cues || [0.8])[0] + i * 0.6, fall: 0.2 });
  });
  return { bodies, drops };
}
export function animate(parts, t, P, job) { Object.keys(parts).forEach((n) => job.S.reveal(parts[n], t - (job.appear?.[n] ?? 0))); }
