// Browser side of the bake harness: builds one object, applies physics track / deliberate animation,
// renders each frame to a transparent canvas (software WebGL). Never reads a real clock.
import * as T from 'three';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { makeStyle } from '/lib/style.js';
import { mulberry32 } from '/lib/presets.js';
let R = null;
window.fxSetup = async (job, track) => {
  Math.random = mulberry32(job.seed || 1);
  const mod = await import(`/objects/${job.object}.js`);
  const ss = job.supersample || 2, W = job.region.w * ss, H = job.region.h * ss;
  const canvas = document.getElementById('c'); canvas.width = W; canvas.height = H;
  const renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true, premultipliedAlpha: true });
  renderer.setPixelRatio(1); renderer.localClippingEnabled = true; renderer.setSize(W, H, false); renderer.setClearColor(0x000000, 0); renderer.outputColorSpace = T.SRGBColorSpace;
  const S = makeStyle(T, { LineSegments2, LineSegmentsGeometry, LineMaterial, mergeVertices }, { width: W, height: H, pixelScale: ss * (job.lineScale || 1), seed: job.seed || 1 });
  const P = { ...(job.params || {}) };
  const view = { ...mod.meta.view, ...(mod.viewFor ? mod.viewFor(P) : {}), ...(job.view || {}) };
  const scene = new T.Scene();
  const aspect = W / H, h = view.height, w = h * aspect;
  const cam = new T.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 0.01, 50);
  const el = view.elev * Math.PI / 180, az = view.azim * Math.PI / 180, d = 10, c = new T.Vector3(...view.center);
  cam.position.set(c.x + d * Math.cos(el) * Math.sin(az), c.y + d * Math.sin(el), c.z + d * Math.cos(el) * Math.cos(az)); cam.lookAt(c);
  const key = new T.DirectionalLight(0xffffff, 2.4); key.position.set(-2.2, 3.2, 2.4); scene.add(key);
  const fill = new T.HemisphereLight(0xfffaf0, 0xd9d0c0, 1.15); scene.add(fill);
  const built = mod.build(T, S, P); scene.add(built.root);
  R = { T, renderer, scene, cam, built, mod, P, job: { ...job, S, appear: {} }, track, W, H, ss, view };
  if (track && track.appear) for (const [n, f] of Object.entries(track.appear)) R.job.appear[n] = f / (job.fps || 30);
  return { W, H, parts: Object.keys(built.parts) };
};
window.fxFrame = (k) => {
  const { T, renderer, scene, cam, built, mod, P, job, track } = R; const t = k / (job.fps || 30);
  if (track && track.frames && track.frames[k]) for (const [n, v] of Object.entries(track.frames[k])) { const o = built.parts[n]; if (!o) continue; if (v[1] > 15) { o.visible = false; continue; } o.position.set(v[0], v[1], v[2]); o.quaternion.set(v[3], v[4], v[5], v[6]); }
  mod.animate(built.parts, t, P, job, track ? track.frames[k] : null, k);
  renderer.render(scene, cam);
  // contact shadows for grounded parts (drawn in Python): screen-space ellipse under each part
  const shadows = [];
  for (const [n, o] of Object.entries(built.parts)) {
    if (!o.userData.ground || !o.visible) continue;
    const box = new T.Box3().setFromObject(o); if (box.isEmpty()) continue;
    const lift = Math.max(0, box.min.y); const ctr = new T.Vector3((box.min.x + box.max.x) / 2, 0, (box.min.z + box.max.z) / 2);
    const a = new T.Vector3(box.min.x, 0, ctr.z).project(cam), b = new T.Vector3(box.max.x, 0, ctr.z).project(cam), p = ctr.clone().project(cam);
    shadows.push({ part: n, x: (p.x + 1) / 2 * job.region.w, y: (1 - p.y) / 2 * job.region.h, w: Math.abs(b.x - a.x) / 4 * job.region.w, lift: +lift.toFixed(4), op: +(Math.max(0, 1 - lift / 0.6) * (o.userData.shadowOpacity ?? 0.2) * (o.userData.revealOpacity ?? 1)).toFixed(4) });
  }
  return { png: renderer.domElement.toDataURL('image/png'), shadows };
};
