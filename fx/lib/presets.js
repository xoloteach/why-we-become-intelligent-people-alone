// Shared motion presets — identical maths to v2/render_motion.py (ease, spring) so baked 3D motion
// matches the Python-drawn motion. Seeded RNG replaces Math.random everywhere.
export const clamp01 = (u) => Math.min(1, Math.max(0, u));
export const ease = (u) => { u = clamp01(u); return 1 - (1 - u) ** 3; };            // cubic ease-out
export const spring = (u) => { u = clamp01(u); return (1 - (1 + 7 * u) * Math.exp(-7 * u)) / (1 - 8 * Math.exp(-7)); }; // normalized critically damped
export const easeInOut = (u) => { u = clamp01(u); return u < 0.5 ? 4 * u * u * u : 1 - (-2 * u + 2) ** 3 / 2; };
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const FPS = 30;
export const PALETTE = { paper: 0xF7F4EE, paperShade: 0xE9E1D3, warmGrey: 0xB9B1A3, midGrey: 0x8E877C, charcoal: 0x16150F, rust: 0xC8623C, gold: 0xE8B33A, glow: 0xF6DDA0 };
export function quatFromEuler(ax, ay, az) { const c1 = Math.cos(ax / 2), s1 = Math.sin(ax / 2), c2 = Math.cos(ay / 2), s2 = Math.sin(ay / 2), c3 = Math.cos(az / 2), s3 = Math.sin(az / 2);
  return { x: s1 * c2 * c3 + c1 * s2 * s3, y: c1 * s2 * c3 - s1 * c2 * s3, z: c1 * c2 * s3 + s1 * s2 * c3, w: c1 * c2 * c3 - s1 * s2 * s3 }; }
export const lerp = (a, b, u) => a + (b - a) * u;
