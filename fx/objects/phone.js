// wwb-3d-v1-phone — attention pulled away. mode 'drop': phone lands face-up (Rapier), then on the cue the
// screen lights, it buzzes and a notification slides in. mode 'scroll': upright phone, feed flicks on and on.
import { quatFromEuler, ease, spring, clamp01 } from '../lib/presets.js';
export const meta = { id: 'wwb-3d-v1-phone', version: 1, name: 'phone', tags: ['distraction', 'notification', 'social media', 'scrolling', 'attention'],
  metaphor: 'Attention pulled away: a notification buzzes, or the feed keeps scrolling.', physics: true,
  view: { center: [0, 0.05, 0.02], height: 0.62, elev: 42, azim: -12 } };
export const usesPhysics = (P) => (P.mode || 'drop') === 'drop';
export const viewFor = (P) => (P.mode === 'scroll' ? { center: [0, 0.25, 0], height: 0.62, elev: 6, azim: -16 } : {});
const PH = { w: 0.21, t: 0.02, l: 0.42 }; const SW = PH.w - 0.024, SL = PH.l - 0.06, SY = PH.t / 2 + 0.0012;
const OFF = 0x2B2925;
function card(T, S, w, h, img, planes) {
  const g = new T.Group(); const mk = (c) => { const m = S.flat(c); m.clippingPlanes = planes; m.userData.baseOpacity = 1; return m; };
  const add = (gw, gh, c, x, z, y = 0) => { const m = new T.Mesh(new T.PlaneGeometry(gw, gh), mk(c)); m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); g.add(m); return m; };
  add(w, h, 0xF7F1E6, 0, 0); if (img) add(w - 0.016, h * 0.5, img, 0, -h * 0.17, 0.0004);
  add(w * 0.55, 0.008, 0x4A4740, -w * 0.15, h * 0.18, 0.0004); add(w * 0.35, 0.008, 0x8E877C, -w * 0.25, h * 0.33, 0.0004);
  const dot = new T.Mesh(new T.CircleGeometry(0.009, 16), mk(0xC8623C)); dot.rotation.x = -Math.PI / 2; dot.position.set(w * 0.36, 0.0006, h * 0.26); g.add(dot);
  return g;
}
export function build(T, S, P) {
  const root = new T.Group(); const holder = new T.Group(); const g = new T.Group(); g.userData.ground = true; g.userData.shadowOpacity = 0.2;
  const body = S.inked(new T.BoxGeometry(PH.w, PH.t, PH.l, 2, 1, 3), S.toon(0x6E685F), { jitter: 0.001 }); g.add(body);
  const scrMat = S.flat(OFF); const scr = new T.Mesh(new T.PlaneGeometry(SW, SL), scrMat); scr.rotation.x = -Math.PI / 2; scr.position.y = SY; g.add(scr);
  g.add(S.inkLine([[-0.025, SY, -PH.l / 2 + 0.016], [0.025, SY, -PH.l / 2 + 0.016]], { linePx: 2.2 }));
  g.add(S.inkLine([[-0.03, SY + 0.0004, PH.l / 2 - 0.016], [0.03, SY + 0.0004, PH.l / 2 - 0.016]], { linePx: 1.6, color: 0xB9B1A3 }));
  const parts = { phone: g }; const ud = { scrMat };
  const planes = [new T.Plane(), new T.Plane()]; ud.planes = planes; ud.local = [new T.Plane(new T.Vector3(0, 0, 1), SL / 2), new T.Plane(new T.Vector3(0, 0, -1), SL / 2)];
  if ((P.mode || 'drop') === 'drop') {
    const n = card(T, S, SW - 0.02, 0.07, null, []); n.position.set(0, SY + 0.0008, -SL / 2 + 0.05); g.add(n); ud.note = n;
    const buzz = new T.Group();
    for (const s of [-1, 1]) for (const r of [0.03, 0.055]) { const pts = []; for (let a = -0.6; a <= 0.61; a += 0.2) pts.push([s * (PH.w / 2 + 0.012 + r * Math.cos(a)), 0.0, -0.06 + r * Math.sin(a) * 1.4]); buzz.add(S.inkLine(pts, { linePx: 2.0, color: 0xC8623C })); }
    g.add(buzz); ud.buzz = buzz; g.position.set(0, 0.3, 0);
  } else {
    const feed = new T.Group(); feed.position.y = SY + 0.0006; g.add(feed); ud.feed = feed; ud.cards = [];
    const imgs = [0xB9B1A3, 0xC8623C, 0xE9E1D3, 0xE8B33A, 0x8E877C, 0xB9B1A3, 0xC8623C, 0xE9E1D3];
    for (let i = 0; i < 8; i++) { const c = card(T, S, SW - 0.02, 0.115, imgs[i], planes); feed.add(c); ud.cards.push(c); }
    g.rotation.x = Math.PI / 2 - 0.12; holder.rotation.y = -0.18; holder.position.y = PH.l / 2 + 0.05;
  }
  g.userData.fx = ud; holder.add(g); root.add(holder); return { root, parts };
}
export function physics(R, world, P) {
  const rb = world.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(0, 0.17, 0.0).setRotation(quatFromEuler(0.22, -0.3, 0.12)).setCcdEnabled(true).setAngularDamping(0.6));
  world.createCollider(R.ColliderDesc.cuboid(PH.w / 2, PH.t / 2, PH.l / 2).setDensity(700).setFriction(0.8).setRestitution(0.08).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS), rb);
  const c = (P.cues || [1])[0]; return { bodies: { phone: rb }, drops: [{ body: 'phone', cue: P.land ?? Math.max(0.5, c - (P.lead ?? 0.7)), fall: 0.2 }] };
}
const lerpHex = (T, a, b, u) => new T.Color(a).lerp(new T.Color(b), u);
export function animate(parts, t, P, job) {
  const g = parts.phone, ud = g.userData.fx, T = job.T || null; const c = (P.cues || [1])[0];
  job.S.reveal(g, t - (job.appear?.phone ?? P.appear ?? 0)); const ro = g.userData.revealOpacity ?? 0;
  const lit = ease((t - c) / 0.18);
  ud.scrMat.color.setRGB(...mix(OFF, 0xF6DDA0, (P.mode === 'scroll') ? 1 : lit));
  if ((P.mode || 'drop') === 'drop') {
    const u = spring((t - c - 0.05) / 0.45); ud.note.visible = g.visible && u > 0.01; ud.note.position.z = -SL / 2 + 0.05 - 0.04 * (1 - u);
    ud.note.traverse((o) => { if (o.material) { o.material.opacity = ro * clamp01(u * 1.4); o.material.transparent = true; } });
    const b = t - c; const on = b >= 0 && b < (P.buzz ?? 0.7); const dec = on ? 1 - b / (P.buzz ?? 0.7) : 0;
    if (on) { g.rotateY(0.045 * Math.sin(b * 2 * Math.PI * 22) * dec); g.translateX(0.005 * Math.sin(b * 2 * Math.PI * 22 + 1) * dec); }
    ud.buzz.visible = g.visible && on && Math.floor(b * 10) % 2 === 0; ud.buzz.traverse((o) => { if (o.material) o.material.opacity = ro; });
  } else {
    const flick = P.flick ?? 0.62, step = P.step ?? 0.27; let off = 0; const n0 = Math.floor(Math.max(0, t - c) / flick);
    for (let j = 0; j <= n0 + 1; j++) off += step * ease((t - c - j * flick) / 0.42);
    const L = ud.cards.length * 0.13; g.parent.position.y = PH.l / 2 + 0.05 + 0.008 * Math.sin(t * 2.1);
    ud.cards.forEach((cd, i) => { let z = i * 0.13 - off; z = ((z + SL / 2 + 0.07) % L + L) % L - SL / 2 - 0.07; cd.position.z = z; });
    g.updateMatrixWorld(true); ud.planes.forEach((p, i) => p.copy(ud.local[i]).applyMatrix4(g.matrixWorld));
  }
}
function mix(a, b, u) { const A = [(a >> 16) & 255, (a >> 8) & 255, a & 255], B = [(b >> 16) & 255, (b >> 8) & 255, b & 255];
  return A.map((v, i) => { const s = (v + (B[i] - v) * u) / 255; return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; }); }
