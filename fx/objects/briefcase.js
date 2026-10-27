// wwb-3d-v1-briefcase — a career choice lands with weight: briefcase drops on a corner and rocks flat (Rapier).
import { quatFromEuler } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-briefcase', version: 1, name: 'briefcase', tags: ['career', 'work', 'expectations', 'path', 'choice'],
  metaphor: 'A career or path, set down with real weight.', physics: true,
  view: { center: [0, 0.19, 0], height: 0.62, elev: 14, azim: -24 } };
const C = { w: 0.38, h: 0.27, d: 0.11 };
export function build(T, S, P) {
  const root = new T.Group(); const g = new T.Group(); g.userData.ground = true; g.userData.shadowOpacity = 0.22;
  const body = S.inked(new T.BoxGeometry(C.w, C.h, C.d, 2, 2, 1), S.toon(P.color ?? 0x8E877C), { jitter: 0.0016 }); g.add(body);
  const yl = C.h * 0.22, z = C.d / 2 + 0.0008;
  g.add(S.inkLine([[-C.w / 2 + 0.004, yl, z], [C.w / 2 - 0.004, yl, z]], { linePx: 1.8 }));
  for (const s of [-1, 1]) g.add(S.inkLine([[s * (C.w / 2 + 0.0008), yl, C.d / 2 - 0.004], [s * (C.w / 2 + 0.0008), yl, -C.d / 2 + 0.004]], { linePx: 1.8 }));
  for (const s of [-1, 1]) { const cl = S.inked(new T.BoxGeometry(0.036, 0.026, 0.012), S.toon(S.PALETTE.gold), { hullPx: 1.6 }); cl.position.set(s * 0.11, yl, C.d / 2 + 0.006); g.add(cl); }
  const handle = S.inked(new T.TorusGeometry(0.056, 0.011, 8, 22, Math.PI), S.toon(0x4A4740), { edges: false, hullPx: 1.8 }); handle.position.y = C.h / 2 + 0.008; g.add(handle);
  for (const s of [-1, 1]) { const m = S.inked(new T.BoxGeometry(0.024, 0.016, 0.034), S.toon(0x4A4740), { hullPx: 1.4 }); m.position.set(s * 0.056, C.h / 2 + 0.008, 0); g.add(m); }
  g.position.set(0, 0.45, 0); root.add(g); return { root, parts: { case: g } };
}
export function physics(R, world, P) {
  const rb = world.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(0, P.holdY ?? 0.42, 0).setRotation(quatFromEuler(0, -0.22, P.tilt ?? 0.16)).setCcdEnabled(true).setAngularDamping(0.5));
  world.createCollider(R.ColliderDesc.cuboid(C.w / 2, C.h / 2, C.d / 2).setDensity(520).setFriction(0.85).setRestitution(0.05).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), rb);
  return { bodies: { case: rb }, drops: [{ body: 'case', cue: (P.cues || [0.9])[0], fall: 0.24 }] };
}
export function animate(parts, t, P, job) { job.S.reveal(parts.case, t - (job.appear?.case ?? 0)); }
