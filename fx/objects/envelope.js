// wwb-3d-v1-envelope — an invitation that drops and lands on its cue (Rapier).
export const meta = { id: 'wwb-3d-v1-envelope', version: 1, name: 'envelope', tags: ['invitation', 'declining', 'social pressure'],
  metaphor: 'An invitation being turned down or set aside.', physics: true,
  view: { center: [0, 0.16, 0], height: 0.78, elev: 36, azim: -8 } };
const DIM = { w: 0.36, t: 0.014, d: 0.24 };
function xs(P) { const n = P.count || 1; return Array.from({ length: n }, (_, i) => (i - (n - 1) / 2) * (P.spacing || 0.42)); }
export function build(T, S, P) {
  const root = new T.Group(); const parts = {};
  xs(P).forEach((x, i) => {
    const g = new T.Group(); g.userData.ground = true;
    const body = S.inked(new T.BoxGeometry(DIM.w, DIM.t, DIM.d, 3, 1, 3), S.toon(0xF3EBDD), { jitter: 0.003 });
    g.add(body);
    const y = DIM.t / 2 + 0.0015, hw = DIM.w / 2 - 0.01, hd = DIM.d / 2 - 0.01;
    g.add(S.inkLine([[-hw, y, -hd], [0, y, 0.02], [hw, y, -hd]], { linePx: 1.8 }));   // flap
    g.add(S.inkLine([[-hw, y, hd], [-0.05, y, 0.01]], { linePx: 1.4 }));
    g.add(S.inkLine([[hw, y, hd], [0.05, y, 0.01]], { linePx: 1.4 }));
    const seal = S.inked(new T.CylinderGeometry(0.032, 0.034, 0.008, 18), S.toon(S.PALETTE.rust), { edges: false, hullPx: 1.6 });
    seal.position.set(0, DIM.t / 2 + 0.004, 0.02); g.add(seal);
    g.position.set(x, 0.6, 0); root.add(g); parts['env' + i] = g;
  });
  return { root, parts };
}
// Releases are solved so each envelope's first contact lands on cues[i] (±1 frame).
export function physics(R, world, P) {
  const bodies = {}; const drops = [];
  xs(P).forEach((x, i) => {
    const rb = world.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(x, 0.34, 0).setRotation(quat(0.35 + 0.1 * i, 0.2 - 0.25 * i, 0.12)).setCcdEnabled(true).setLinearDamping(0.4).setAngularDamping(0.8));
    world.createCollider(R.ColliderDesc.cuboid(DIM.w / 2, DIM.t / 2, DIM.d / 2).setDensity(320).setFriction(0.7).setRestitution(0.06).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), rb);
    bodies['env' + i] = rb; drops.push({ body: 'env' + i, cue: (P.cues || [])[i] ?? P.cues?.[0], fall: 0.26 });
  });
  return { bodies, drops };
}
function quat(ax, ay, az) { const c1 = Math.cos(ax / 2), s1 = Math.sin(ax / 2), c2 = Math.cos(ay / 2), s2 = Math.sin(ay / 2), c3 = Math.cos(az / 2), s3 = Math.sin(az / 2);
  return { x: s1 * c2 * c3 + c1 * s2 * s3, y: c1 * s2 * c3 - s1 * c2 * s3, z: c1 * c2 * s3 + s1 * s2 * c3, w: c1 * c2 * c3 - s1 * s2 * s3 }; }
export function animate(parts, t, P, job) { xs(P).forEach((_, i) => job.S.reveal(parts['env' + i], t - (job.appear?.['env' + i] ?? 0))); }
