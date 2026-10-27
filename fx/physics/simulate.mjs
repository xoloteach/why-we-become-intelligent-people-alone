// Rapier 3D physics for effect jobs (Node, WASM). Fixed 1/60 s step, two steps per 30 fps frame.
// Drop bodies are parked off-stage, appear (kinematic) at their hold pose, then release; release
// frames are solved iteratively so each body's first contact lands exactly on its narration cue.
import RAPIER from '@dimforge/rapier3d-compat';
let ready = null;
export async function initRapier() { if (!ready) ready = RAPIER.init(); await ready; return RAPIER; }
export async function simulate(mod, P, job) {
  const R = await initRapier();
  const N = job.frames, FPS = job.fps || 30;
  function run(release) {
    const world = new R.World({ x: 0, y: -9.81, z: 0 }); world.timestep = 1 / 60;
    const g = world.createRigidBody(R.RigidBodyDesc.fixed().setTranslation(0, -0.05, 0));
    world.createCollider(R.ColliderDesc.cuboid(8, 0.05, 8).setFriction(0.9).setRestitution(0.05).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), g);
    const spec = mod.physics(R, world, P, job);
    const names = new Map(); for (const [n, rb] of Object.entries(spec.bodies)) names.set(rb.handle, n);
    const colName = new Map(); world.forEachCollider((c) => { const p = c.parent(); colName.set(c.handle, p ? (names.get(p.handle) ?? 'ground') : 'ground'); });
    const drops = spec.drops || []; const hold = {}, appear = {};
    for (const d of drops) {
      const rb = spec.bodies[d.body]; const t = rb.translation(); hold[d.body] = { x: t.x, y: t.y, z: t.z };
      const r = release[d.body]; appear[d.body] = Math.max(0, r - (d.reveal ?? 14));
      if (appear[d.body] > 0) rb.setTranslation({ x: t.x + 60, y: t.y + 20, z: t.z }, true);
    }
    const eq = new R.EventQueue(true); const frames = [], contacts = {}, events = [];
    for (let k = 0; k < N; k++) {
      for (const d of drops) {
        const rb = spec.bodies[d.body];
        if (k === appear[d.body] && appear[d.body] > 0) { rb.setTranslation(hold[d.body], true); rb.setNextKinematicTranslation(hold[d.body]); }
        if (d.align && k >= appear[d.body] && k <= release[d.body]) { const a = d.align(spec.bodies); rb.setTranslation(a.pos, true); rb.setNextKinematicTranslation(a.pos); if (a.rot) { rb.setRotation(a.rot, true); rb.setNextKinematicRotation(a.rot); } }
        if (k === release[d.body]) { rb.setBodyType(R.RigidBodyType.Dynamic, true); if (d.linvel) rb.setLinvel(d.linvel, true); if (d.angvel) rb.setAngvel(d.angvel, true); }
      }
      if (spec.onFrame) spec.onFrame(k, k / FPS, R);
      const fr = {};
      for (const [n, rb] of Object.entries(spec.bodies)) { const p = rb.translation(), q = rb.rotation(); fr[n] = [p.x, p.y, p.z, q.x, q.y, q.z, q.w].map((v) => +v.toFixed(6)); }
      frames.push(fr);
      for (let s = 0; s < 2; s++) {
        world.step(eq);
        eq.drainCollisionEvents((h1, h2, started) => {
          if (!started) return; const a = colName.get(h1), b = colName.get(h2);
          events.push({ frame: k + 1, type: 'contact', a, b });
          for (const n of [a, b]) if (n && n !== 'ground' && contacts[n] === undefined && k + 1 > (release[n] ?? -1)) contacts[n] = k + 1;
        });
      }
    }
    // settle: all dynamic bodies quiet for 6 consecutive frames after the last contact
    let settle = null; const last = Math.max(0, ...Object.values(contacts));
    for (let k = last + 1; k < N - 6 && settle === null; k++) {
      let quiet = true;
      for (let j = k; j < k + 6 && quiet; j++) for (const n of Object.keys(spec.bodies)) {
        const a = frames[j - 1][n], b = frames[j][n]; const dv = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]) * FPS; const dq = Math.hypot(b[3] - a[3], b[4] - a[4], b[5] - a[5], b[6] - a[6]) * FPS;
        if (dv > 0.03 || dq > 0.06) { quiet = false; break; }
      }
      if (quiet) settle = k;
    }
    world.free();
    return { frames, contacts, events, appear, release: { ...release }, settle, hold };
  }
  const spec0 = (() => { const w = new R.World({ x: 0, y: -9.81, z: 0 }); const s = mod.physics(R, w, P, job); const d = s.drops || []; w.free(); return d; })();
  const release = {}; const target = {};
  for (const d of spec0) { target[d.body] = Math.round(d.cue * FPS); release[d.body] = Math.max(0, target[d.body] - Math.round((d.fall ?? 0.35) * FPS)); }
  let res = run(release);
  for (let it = 0; it < 8; it++) {
    let ok = true;
    for (const d of spec0) { const c = res.contacts[d.body]; if (c === undefined) { ok = false; release[d.body] = Math.max(0, release[d.body] - 3); continue; } const e = target[d.body] - c; if (Math.abs(e) > 0) { ok = false; release[d.body] = Math.max(0, release[d.body] + e); } }
    if (ok) break; res = run(release);
  }
  res.targets = target; res.cueError = Object.fromEntries(spec0.map((d) => [d.body, res.contacts[d.body] === undefined ? null : res.contacts[d.body] - target[d.body]]));
  return res;
}
