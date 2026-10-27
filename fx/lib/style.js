// Ink-and-paper style for Three.js objects (toolkit contract "3D object style: ink and paper").
// Flat 3-step toon fill, charcoal inverted-hull silhouette with screen-space pixel width,
// charcoal crease lines (LineSegments2), slight seeded irregularity, ink-first reveal.
import { PALETTE, ease, mulberry32 } from './presets.js';
export function makeStyle(T, addons, opts) {
  const { LineSegments2, LineSegmentsGeometry, LineMaterial, mergeVertices } = addons;
  const res = new T.Vector2(opts.width, opts.height);
  const px = opts.pixelScale || 1;               // supersampling factor
  const rng = mulberry32(opts.seed || 1);
  const grad = new T.DataTexture(new Uint8Array([150, 150, 150, 255, 205, 205, 205, 255, 255, 255, 255, 255]), 3, 1, T.RGBAFormat);
  grad.minFilter = grad.magFilter = T.NearestFilter; grad.needsUpdate = true;
  const fills = [], lines = [], hulls = [];
  function toon(color, extra = {}) {
    const m = new T.MeshToonMaterial({ color, gradientMap: grad, transparent: true, opacity: 1, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, ...extra });
    return m;
  }
  function flat(color) { return new T.MeshBasicMaterial({ color, transparent: true, opacity: 1, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 }); }
  function hullMaterial(widthPx) {
    return new T.ShaderMaterial({
      uniforms: { uPx: { value: widthPx * px }, uRes: { value: res }, uColor: { value: new T.Color(PALETTE.charcoal) }, uOpacity: { value: 1 } },
      vertexShader: `uniform float uPx; uniform vec2 uRes; varying float vF; void main(){ vec4 c = projectionMatrix * modelViewMatrix * vec4(position,1.0); vec3 n = normalize(normalMatrix * normal); c.xy += n.xy * uPx * 2.0 / uRes * c.w; c.z += 0.0005 * c.w; gl_Position = c; }`,
      fragmentShader: `uniform vec3 uColor; uniform float uOpacity; void main(){ gl_FragColor = vec4(uColor, uOpacity); }`,
      side: T.BackSide, transparent: true, depthWrite: true,
    });
  }
  function jitter(geo, amount) {
    if (!amount) return geo;
    const p = geo.attributes.position; const seen = new Map();
    for (let i = 0; i < p.count; i++) {
      const k = `${p.getX(i).toFixed(4)},${p.getY(i).toFixed(4)},${p.getZ(i).toFixed(4)}`;
      if (!seen.has(k)) seen.set(k, [(rng() - .5) * amount, (rng() - .5) * amount, (rng() - .5) * amount]);
      const d = seen.get(k); p.setXYZ(i, p.getX(i) + d[0], p.getY(i) + d[1], p.getZ(i) + d[2]);
    }
    p.needsUpdate = true; geo.computeVertexNormals(); return geo;
  }
  // Build an inked mesh: toon fill + silhouette hull + crease lines.
  function inked(geo, material, o = {}) {
    const g = jitter(geo, o.jitter ?? 0);
    const group = new T.Group();
    const mesh = new T.Mesh(g, material); group.add(mesh); fills.push(mesh.material);
    if (o.hull !== false) {
      const hg = mergeVertices(g.clone().deleteAttribute('normal').deleteAttribute('uv') || g.clone(), 1e-3); hg.computeVertexNormals();
      const hull = new T.Mesh(hg, hullMaterial(o.hullPx ?? 2.6)); hull.renderOrder = -1; group.add(hull); hulls.push(hull.material);
    }
    if (o.edges !== false) {
      const eg = new T.EdgesGeometry(g, o.edgeAngle ?? 28);
      const lg = new LineSegmentsGeometry().fromEdgesGeometry(eg);
      const lm = new LineMaterial({ color: PALETTE.charcoal, linewidth: (o.linePx ?? 2.4) * px, resolution: res, transparent: true, opacity: 1, worldUnits: false });
      const ls = new LineSegments2(lg, lm); group.add(ls); lines.push(lm);
    }
    group.userData.mesh = mesh; return group;
  }
  // Code-drawn ink polyline (e.g. clock ticks, globe meridians) as fat lines.
  function inkLine(points, o = {}) {
    const arr = []; for (let i = 0; i < points.length - 1; i++) arr.push(...points[i], ...points[i + 1]);
    const lg = new LineSegmentsGeometry().setPositions(arr);
    const lm = new LineMaterial({ color: o.color ?? PALETTE.charcoal, linewidth: (o.linePx ?? 2.0) * px, resolution: res, transparent: true, opacity: 1, worldUnits: false });
    lines.push(lm); return new LineSegments2(lg, lm);
  }
  // Ink-first reveal for one object subtree (r = seconds since its appearance).
  function reveal(root, r) {
    if (r < 0) { root.visible = false; return; }
    root.visible = true;
    const li = ease(r / 0.35), fi = ease((r - 0.18) / 0.62); root.userData.revealOpacity = fi;
    root.traverse((o) => {
      const m = o.material; if (!m) return;
      if (m.isLineMaterial) m.opacity = li;
      else if (m.uniforms && m.uniforms.uOpacity) m.uniforms.uOpacity.value = fi;
      else if (m.userData && m.userData.keepOpacity) {} else { m.opacity = fi * (m.userData.baseOpacity ?? 1); }
      if (!m.isLineMaterial && !(m.uniforms && m.uniforms.uOpacity)) m.transparent = m.opacity < 0.999;
    });
  }
  return { PALETTE, toon, flat, inked, inkLine, reveal, jitter, rng, res };
}
