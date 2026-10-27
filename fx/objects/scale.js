// wwb-3d-v1-scale — beam balance on a Rapier revolute hinge with a pendulum pointer: weights land on their
// cues; one side tips the beam, matched weights return it to level and it settles.
import { quatFromEuler } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-scale', version: 1, name: 'balance scale', tags: ['balance', 'needs', 'equilibrium', 'priorities'],
  metaphor: 'Finding balance: different needs weighed until the beam sits level.', physics: true,
  view: { center: [0, 0.36, 0], height: 0.98, elev: 12, azim: -14 } };
const PIV = 0.43, ARM = 0.38, CUBE = 0.092;
const COLORS = { rust: 0xC8623C, gold: 0xE8B33A, paper: 0xF3EBDD, grey: 0xB9B1A3, charcoal: 0x4A4740 };
const HALF = 0.0545;
function twoPer(P) { const sides = P.sides || [-1, 1]; return sides.filter((q) => q === -1).length > 1 || sides.filter((q) => q === 1).length > 1; }
function cubeSize(P) { return twoPer(P) ? 0.082 : CUBE; }
function slots(P) { const sides = P.sides || [-1, 1]; const cnt = { '-1': 0, '1': 0 }; const two = twoPer(P); return sides.map((s) => { const n = cnt[s]++; return { s, x: s * ARM + (two ? (n ? -s : s) * HALF : 0) }; }); }
export function build(T, S, P) {
  const root = new T.Group(); const parts = {};
  const base = new T.Group(); base.userData.ground = true;
  const b = S.inked(new T.CylinderGeometry(0.13, 0.14, 0.035, 28), S.toon(S.PALETTE.warmGrey), { edgeAngle: 40 }); b.position.y = 0.0175; base.add(b);
  const post = S.inked(new T.BoxGeometry(0.045, PIV - 0.035, 0.045), S.toon(0xE2D9CA)); post.position.y = 0.035 + (PIV - 0.035) / 2; base.add(post);
  const cap = S.inked(new T.SphereGeometry(0.026, 16, 12), S.toon(S.PALETTE.gold), { edges: false, hullPx: 1.8 }); cap.position.set(0, PIV, 0.03); base.add(cap);
  root.add(base); parts.base = base;
  const beam = new T.Group();
  const bar = S.inked(new T.BoxGeometry(ARM * 2 + 0.16, 0.028, 0.07), S.toon(0xEFE7DA), { jitter: 0.0015 }); beam.add(bar);
  for (const s of [-1, 1]) { const tr = S.inked(new T.BoxGeometry(0.23, 0.018, 0.16), S.toon(S.PALETTE.rust)); tr.position.set(s * ARM, 0.03, 0); beam.add(tr);
    const st = S.inked(new T.BoxGeometry(0.02, 0.03, 0.02), S.toon(0xE2D9CA)); st.position.set(s * ARM, 0.014, 0); beam.add(st);
    for (const e of (twoPer(P) ? [-1, 0, 1] : [-1, 1])) { const lip = S.inked(new T.BoxGeometry(0.012, e ? 0.032 : 0.024, 0.16), S.toon(S.PALETTE.rust), { hullPx: 1.8 }); lip.position.set(s * ARM + e * 0.109, e ? 0.052 : 0.048, 0); beam.add(lip); } }
  const needle = S.inked(new T.BoxGeometry(0.012, 0.2, 0.012), S.toon(S.PALETTE.midGrey), { hullPx: 1.6 }); needle.position.set(0, -0.11, 0.05); beam.add(needle);
  const bob = S.inked(new T.SphereGeometry(0.02, 14, 10), S.toon(S.PALETTE.rust), { edges: false, hullPx: 1.6 }); bob.position.set(0, -0.215, 0.05); beam.add(bob);
  beam.position.y = PIV; root.add(beam); parts.beam = beam;
  slots(P).forEach((sl, i) => { const c = (P.colors || ['rust', 'gold', 'paper', 'grey'])[i % 4]; const cs = cubeSize(P); const w = S.inked(new T.BoxGeometry(cs, cs, cs, 2, 2, 2), S.toon(COLORS[c] ?? COLORS.paper), { jitter: 0.002 }); w.position.set(sl.x, 0.8, 0); root.add(w); parts['w' + i] = w; });
  return { root, parts };
}
export function physics(R, world, P) {
  const bodies = {}; const fixed = world.createRigidBody(R.RigidBodyDesc.fixed().setTranslation(0, PIV, 0));
  const beam = world.createRigidBody(R.RigidBodyDesc.dynamic().setTranslation(0, PIV, 0).setRotation(quatFromEuler(0, 0, P.tilt ?? 0)).setAngularDamping(P.damping ?? (twoPer(P) ? 30.0 : 11.0)).setCanSleep(false));
  world.createCollider(R.ColliderDesc.cuboid(ARM + 0.08, 0.014, 0.035).setDensity(250).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), beam);
  for (const s of [-1, 1]) { world.createCollider(R.ColliderDesc.cuboid(0.115, 0.009, 0.08).setTranslation(s * ARM, 0.03, 0).setDensity(250).setFriction(1.2).setRestitution(0.02).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), beam);
    for (const e of (twoPer(P) ? [-1, 0, 1] : [-1, 1])) world.createCollider(R.ColliderDesc.cuboid(0.006, e ? 0.016 : 0.012, 0.08).setTranslation(s * ARM + e * 0.109, e ? 0.052 : 0.048, 0).setDensity(250).setFriction(1.2), beam); }
  world.createCollider(R.ColliderDesc.ball(0.02).setTranslation(0, -0.215, 0.05).setDensity(P.bobDensity ?? (twoPer(P) ? 270000 : 90000)).setSensor(true), beam);
  const j = world.createImpulseJoint(R.JointData.revolute({ x: 0, y: 0, z: 0 }, { x: 0, y: 0, z: 0 }, { x: 0, y: 0, z: 1 }), fixed, beam, true);
  if (j.setLimits) j.setLimits(-(P.limit ?? 0.2), P.limit ?? 0.2);
  bodies.beam = beam; const drops = [];
  slots(P).forEach((sl, i) => { const rb = world.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(sl.x, 0.74, 0).setCcdEnabled(true).setAngularDamping(0.6));
    world.createCollider(R.ColliderDesc.cuboid(cubeSize(P) / 2, cubeSize(P) / 2, cubeSize(P) / 2).setDensity(P.weightDensity ?? 900).setFriction(1.2).setRestitution(0.03).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), rb);
    bodies['w' + i] = rb; drops.push({ body: 'w' + i, cue: (P.cues || [])[i], fall: 0.2,
      // hold each weight above its compartment on the beam's current pose so it lands seated, not on a lip
      align: (B) => { const q = B.beam.rotation(); const th = 2 * Math.atan2(q.z, q.w); const ht = 0.075, h = 0.74 - PIV - ht; // weights fall straight down, so offset only by the tray height
        return { pos: { x: sl.x * Math.cos(th) - ht * Math.sin(th), y: PIV + sl.x * Math.sin(th) + ht * Math.cos(th) + h, z: 0 }, rot: { x: 0, y: 0, z: Math.sin(th / 2), w: Math.cos(th / 2) } }; } }); });
  return { bodies, drops };
}
export function animate(parts, t, P, job) {
  job.S.reveal(parts.base, t - (P.appear ?? 0)); job.S.reveal(parts.beam, t - (P.appear ?? 0));
  Object.keys(parts).filter((n) => n[0] === 'w').forEach((n) => job.S.reveal(parts[n], t - (job.appear?.[n] ?? 99)));
}
