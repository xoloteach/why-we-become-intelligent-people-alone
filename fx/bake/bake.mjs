#!/usr/bin/env node
// Bake harness: node bake/bake.mjs --out DIR [--workers 3] job1.json job2.json ...
// Physics (Rapier, Node) -> visual bake (Three.js in headless Chromium, software WebGL) -> PNG frames + manifest.
import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto'; import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { simulate } from '../physics/simulate.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2); let out = 'fx-out', workers = 3; const jobs = [];
for (let i = 0; i < args.length; i++) { if (args[i] === '--out') out = args[++i]; else if (args[i] === '--workers') workers = +args[++i]; else jobs.push(args[i]); }
const sha = (b) => crypto.createHash('sha256').update(b).digest('hex');
const ver = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, 'node_modules', p, 'package.json'))).version;
const VERSIONS = { three: ver('three'), rapier: ver('@dimforge/rapier3d-compat'), playwright: ver('playwright'), node: process.version };
const MIME = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.wasm': 'application/wasm', '.json': 'application/json' };
const t0 = Date.now();
const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
VERSIONS.chromium = browser.version();
async function bakeOne(file) {
  const job = JSON.parse(fs.readFileSync(file, 'utf8')); const id = job.effect_id; const dir = path.join(out, id); const raw = path.join(dir, 'raw');
  fs.mkdirSync(raw, { recursive: true }); const ts = Date.now();
  const mod = await import(pathToFileURL(path.join(ROOT, 'objects', job.object + '.js')).href);
  let track = null;
  const usesPhysics = mod.usesPhysics ? mod.usesPhysics(job.params || {}) : mod.meta.physics;
  if (usesPhysics && mod.physics) { track = await simulate(mod, job.params || {}, job); fs.writeFileSync(path.join(dir, 'track.json'), JSON.stringify(track)); }
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error(id, 'pageerror', e.message)); page.on('console', (m) => { if (m.type() === 'error') console.error(id, m.text()); });
  await page.route('http://fx.local/**', async (route) => {
    const u = new URL(route.request().url()); let p = decodeURIComponent(u.pathname);
    const f = p.startsWith('/nm/') ? path.join(ROOT, 'node_modules', p.slice(4)) : path.join(ROOT, p.slice(1));
    if (!f.startsWith(ROOT) || !fs.existsSync(f)) return route.fulfill({ status: 404, body: 'nf' });
    route.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': MIME[path.extname(f)] || 'application/octet-stream' } });
  });
  await page.goto('http://fx.local/bake/index.html'); await page.waitForFunction(() => typeof window.fxSetup === 'function');
  const info = await page.evaluate(([j, tr]) => window.fxSetup(j, tr), [job, track]);
  const hashes = [], shadows = [];
  for (let k = 0; k < job.frames; k++) {
    const r = await page.evaluate((kk) => window.fxFrame(kk), k);
    const buf = Buffer.from(r.png.split(',')[1], 'base64'); const fn = path.join(raw, `f${String(k).padStart(4, '0')}.png`);
    fs.writeFileSync(fn + '.tmp', buf); fs.renameSync(fn + '.tmp', fn); hashes.push(sha(buf)); shadows.push(r.shadows);
  }
  await page.close();
  const secs = (Date.now() - ts) / 1000;
  const manifest = { schema: 'wwb-fx-bake/1', effect_id: id, object: job.object, object_id: mod.meta.id, frames: job.frames, size_raw: [info.W, info.H], supersample: job.supersample || 2,
    inputs_sha256: sha(JSON.stringify(job)), versions: VERSIONS, raw_sha256: hashes, shadows,
    physics: track ? { contacts: track.contacts, targets: track.targets, cueError: track.cueError, release: track.release, appear: track.appear, settle: track.settle, events: track.events.slice(0, 200) } : null,
    perf: { seconds: +secs.toFixed(2), fps: +(job.frames / secs).toFixed(2) } };
  fs.writeFileSync(path.join(dir, 'bake.json'), JSON.stringify(manifest, null, 1));
  console.log(`baked ${id} ${job.frames}f ${secs.toFixed(1)}s ${(job.frames / secs).toFixed(1)}fps` + (track ? ` contacts=${JSON.stringify(track.cueError)} settle=${track.settle}` : ''));
  return manifest;
}
const queue = [...jobs]; const results = [];
await Promise.all(Array.from({ length: Math.max(1, workers) }, async () => { while (queue.length) { const f = queue.shift(); try { results.push(await bakeOne(f)); } catch (e) { console.error('FAILED', f, e.stack || e); process.exitCode = 1; } } }));
await browser.close();
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'bake-perf.json'), JSON.stringify({ seconds: (Date.now() - t0) / 1000, workers, versions: VERSIONS, jobs: results.map((r) => ({ id: r.effect_id, frames: r.frames, ...r.perf })) }, null, 1));
process.exit(process.exitCode || 0);
