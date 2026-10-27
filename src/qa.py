"""Release QA gates. Usage: qa.py DIST_DIR  (reads WWB_WORK for plan/bakes/reports, DIST for final media, PERF_DIR for job perf).
Writes DIST/qa_report.json + DIST/qa_report.md (PASS / FAIL / NOT CHECKED per gate) and QA stills/contact sheets.
Exit 1 if any gate FAILs."""
import os, sys, json, glob, re, subprocess, hashlib
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import ROOT, WORK, FPS, sha256_file
DIST = sys.argv[1]; PERF = os.environ.get('PERF_DIR', os.path.join(WORK, 'perf')); R = []
P = json.load(open(os.path.join(WORK, 'plan.json')))
def gate(name, status, detail): R.append({'gate': name, 'status': status, 'detail': detail}); print(f'[{status}] {name}: {detail}', flush=True)
def ok(c): return 'PASS' if c else 'FAIL'
def probe(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p], capture_output=True, text=True); return json.loads(r.stdout)
def loud(p):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', p, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    t = r[r.rindex('Summary:'):]; return float(t.split('I:')[1].split('LUFS')[0]), float(t.split('Peak:')[1].split('dBFS')[0])
VIDEOS = {'final.mp4': (1920, 1080, P['total'], 'landscape')} | {f"{S['id']}.mp4": (1080, 1920, S['total'], S['id']) for S in P['shorts']}
# 1-3: container, geometry, fps, duration, audio, loudness
for fn, (w, h, dur, key) in VIDEOS.items():
    p = os.path.join(DIST, fn)
    if not os.path.exists(p): gate(f'{fn} exists', 'FAIL', 'missing'); continue
    j = probe(p); v = [s for s in j['streams'] if s['codec_type'] == 'video']; a = [s for s in j['streams'] if s['codec_type'] == 'audio']
    fr = v[0]['r_frame_rate'].split('/'); fps = float(fr[0]) / float(fr[1]); d = float(j['format']['duration'])
    gate(f'{fn} geometry', ok(v[0]['width'] == w and v[0]['height'] == h and abs(fps - FPS) < .01 and v[0]['pix_fmt'] == 'yuv420p' and v[0]['codec_name'] == 'h264'),
         f"{v[0]['codec_name']} {v[0]['width']}x{v[0]['height']} {fps:.3f}fps {v[0]['pix_fmt']}")
    gate(f'{fn} duration', ok(abs(d - dur) <= .5), f'{d:.3f}s vs plan {dur:.3f}s')
    gate(f'{fn} audio stream', ok(len(a) == 1 and a[0]['codec_name'] == 'aac' and int(a[0]['sample_rate']) == 44100), f"{a[0]['codec_name'] if a else 'none'} {a[0].get('sample_rate') if a else ''} {a[0].get('channels') if a else ''}ch")
    I, tp = loud(p); gate(f'{fn} loudness', ok(-17.5 <= I <= -14.5 and tp <= -1.0), f'{I:.1f} LUFS integrated, true peak {tp:.1f} dBFS (target -16, -17.5..-14.5, TP<=-1)')
    gate(f'{fn} faststart', ok(open(p, 'rb').read(64 * 1024).find(b'moov') != -1), 'moov atom at file start' )
# 4: narration integrity (input hash chain)
man = os.path.join(WORK, 'inputs_manifest.json')
if os.path.exists(man):
    M = json.load(open(man)); got = subprocess.run(f"ffmpeg -loglevel error -i {os.path.join(WORK, 'narration.wav')} -f s16le -ac 1 -ar 44100 - | sha256sum", shell=True, capture_output=True, text=True).stdout.split()[0]
    gate('narration PCM hash', ok(got == M['narration_pcm_s16le_sha256']), f'{got[:16]}… vs manifest {M["narration_pcm_s16le_sha256"][:16]}… (user Google AI Studio take, processed chain; script/audio unchanged)')
else: gate('narration PCM hash', 'NOT CHECKED', 'no inputs_manifest.json')
d = abs(P['vo_end'] - 1226.515); gate('narration duration', ok(d < .01), f"vo_end {P['vo_end']}s")
# 5: captions
cr = json.load(open(os.path.join(WORK, 'captions_report.json')))
for k, v in cr.items():
    txt = open(os.path.join(WORK, v['path']), encoding='utf-8').read(); ev = txt.count('\nDialogue:')
    tot = P['total'] if k == 'landscape' else next(S['total'] for S in P['shorts'] if S['id'] == k)
    ends = [l.split(',')[2] for l in txt.splitlines() if l.startswith('Dialogue:')]; last = max(sum(float(x) * m for x, m in zip(e.split(':'), (3600, 60, 1))) for e in ends) if ends else 0
    lim = 7 if k == 'landscape' else 5
    gate(f'captions {k}', ok(ev > 0 and ev == v['events'] and v['max_group_words'] <= lim and last <= tot), f"{ev} events, {v['groups']} groups, max {v['max_group_words']} words, last end {last:.2f}s ≤ {tot:.2f}s")
al = json.load(open(os.path.join(WORK, 'align.json'))); gate('word alignment', ok(al['match_ratio'] >= .9), f"{al['engine']}: {al['matched_exact']}/{al['script_tokens']} exact ({al['match_ratio']:.2%}), {al['interpolated']} interpolated")
# 6-9: 3D effects
fx_scenes = [(s['fx'], s, 'landscape') for s in P['scenes'] if s.get('fx')] + [(s['fx'], s, S['id']) for S in P['shorts'] for s in S['scenes'] if s.get('fx')]
bad, cue_bad, objs, vers = [], [], set(), set()
for eid, s, fmt in fx_scenes:
    d = os.path.join(WORK, 'fx_out', eid); bj = os.path.join(d, 'bake.json')
    if not os.path.exists(bj): bad.append(f'{eid}: no bake'); continue
    m = json.load(open(bj)); job = json.load(open(os.path.join(WORK, 'fx_jobs', eid + '.json'))); objs.add(m['object']); vers.add(json.dumps(m['versions'], sort_keys=True))
    files = sorted(glob.glob(os.path.join(d, 'f[0-9][0-9][0-9][0-9].png')))
    if len(files) != job['frames'] or len(m.get('final_sha256', [])) != job['frames']: bad.append(f'{eid}: {len(files)}/{job["frames"]} frames'); continue
    hs = [hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in files]
    if hs != m['final_sha256']: bad.append(f'{eid}: frame hash mismatch')
    if m.get('edge_violations'): bad.append(f'{eid}: object alpha touches bake boundary in {len(m["edge_violations"])} frames')
    if m.get('alpha_peak', 0) < 200: bad.append(f'{eid}: alpha peak {m.get("alpha_peak")}')
    ce = (m.get('physics') or {}).get('cueError') or {}
    for b, e in ce.items():
        if e is None or abs(e) > 1: cue_bad.append(f'{eid}:{b}={e}')
gate('3D bakes complete + hashed', ok(not bad), f"{len(fx_scenes)} effects, objects {sorted(objs)}; " + ('; '.join(bad) if bad else 'all frame counts and sha256 manifests match'))
gate('3D toolchain versions', ok(len(vers) == 1), '; '.join(sorted(vers)))
gate('physics cue error ≤ ±1 frame', ok(not cue_bad), ', '.join(cue_bad) if cue_bad else 'all contact targets hit on cue')
th = P['fx_summary']; spread_ok = th['landscape'] >= 8 and all(x > 0 for x in th['thirds']) and th['max_run'] <= 2 and all(1 <= v <= 3 for v in th['shorts'].values())
gate('3D scene spread (§3G/§4I)', ok(spread_ok), f"landscape {th['landscape']} (thirds {th['thirds']}, max run {th['max_run']}); shorts {th['shorts']}")
# caption band exclusion
logs = glob.glob(os.path.join(WORK, 'segments', '*.fxlog.json')) + glob.glob(os.path.join(DIST, '..', 'fxlogs', '*.fxlog.json'))
if logs:
    viol = sum(1 for L in logs for e in json.load(open(L))['fx'] if not e[3]); n = sum(len(json.load(open(L))['fx']) for L in logs)
    gate('3D alpha clear of caption band', ok(viol == 0), f'{n} sampled fx frames across {len(logs)} renders, {viol} with alpha inside the caption band')
else: gate('3D alpha clear of caption band', 'NOT CHECKED', 'no fx logs found')
# SFX sync
ar = {}
for f in glob.glob(os.path.join(WORK, 'audio_report_*.json')): ar.update(json.load(open(f)))
if ar:
    worst, n = 0.0, 0
    for eid, s, fmt in fx_scenes:
        bj = os.path.join(WORK, 'fx_out', eid, 'bake.json')
        if not os.path.exists(bj): continue
        ph = json.load(open(bj)).get('physics') or {}; off = 0 if fmt == 'landscape' else next(S['t0'] for S in P['shorts'] if S['id'] == fmt)
        evs = [e for e in ar.get(fmt, {}).get('events', []) if e['kind'] == 'thud' and e['note'].startswith(eid + ':')]
        for b, fr in (ph.get('contacts') or {}).items():
            if b == 'beam' or fr is None: continue
            t = s['start'] - off + fr / FPS; best = min((abs(e['t'] - t) for e in evs), default=9); worst = max(worst, best); n += 1
    gate('SFX thud ±1 frame of contact', ok(worst <= 1 / FPS + 1e-3), f'{n} contacts, worst offset {worst * 1000:.1f} ms (Python/ffmpeg SFX set; Tone.js stem not built)')
    gate('mix loudness reports', ok(all(-17.5 <= v['integrated_lufs'] <= -14.5 for v in ar.values())), ', '.join(f"{k} {v['integrated_lufs']}" for k, v in ar.items()))
else: gate('SFX thud ±1 frame of contact', 'NOT CHECKED', 'no audio reports')
det = json.load(open(os.path.join(WORK, 'determinism.json')))
gate('deterministic sample re-bake', ok(det['pass']), f"{det['sample']}: {det['frames']} final frame hashes compared")
ty = json.load(open(os.path.join(WORK, 'typography.json')))
gate('Typography width + headline regression', ok(ty['pass']), f"{ty['scenes']} scene layouts; Overwhelming fitted at {ty['width_regression_font']}px; failures {ty['failures']}")
# 10: Shorts specifics
for S in P['shorts']:
    p = os.path.join(DIST, f"{S['id']}.mp4")
    if not os.path.exists(p): continue
    cap = cv2.VideoCapture(p); ok0, f0 = cap.read(); cap.release()
    if ok0:
        g = cv2.cvtColor(f0[200:480, 80:900], cv2.COLOR_BGR2GRAY); ink = float(((g < 90) | (g > 235) & (np.mean(f0[200:480, 80:900]) < 100)).mean())
        gate(f"{S['id']} first frame carries hook", ok(ink > .02), f'headline ink coverage {ink:.1%} in frame 0 ("{S["scenes"][0]["title"]}")')
    gate(f"{S['id']} length", ok(15 <= S['total'] <= 60), f"{S['total']:.2f}s incl. end card {S['end_card']}s")
# 11: chapters
ch = [l for l in open(os.path.join(WORK, 'chapters.txt')).read().splitlines() if l.strip()]
secs = [int(l[:2]) * 60 + int(l[3:5]) for l in ch]
gate('YouTube chapters', ok(secs[0] == 0 and len(secs) >= 3 and all(b - a >= 10 for a, b in zip(secs, secs[1:]))), f'{len(secs)} chapters from processed-narration alignment, first 00:00, min gap {min(b - a for a, b in zip(secs, secs[1:]))}s')
# 12: perf + workers
pf = sorted(glob.glob(os.path.join(PERF, '*.json')))
if pf:
    perf = [json.load(open(f)) for f in pf]; wk = [p.get('bake_workers') for p in perf if p.get('bake_workers') is not None]
    gate('bake workers ≤ 3', ok(wk and max(wk) <= 3), f'workers {wk}')
    gate('perf recorded', 'PASS', '; '.join(f"{p['job']}: {p.get('seconds', '?')}s, {p.get('cpu', '?')}, {p.get('ram_gb', '?')} GB, maxrss {p.get('max_rss_mb', '?')} MB" for p in perf))
else: gate('perf recorded', 'NOT CHECKED', 'no perf files')
# 13: credential scan of everything we publish
pat = re.compile(r'(AIza[0-9A-Za-z_\-]{35}|gh[pousr]_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{40,}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abp]-[0-9A-Za-z-]{10,})')
secrets = [v for k, v in os.environ.items() if k in ('DEEPGRAM_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY') and v and len(v) > 8]
hits = []
for root in (DIST, ROOT):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('.git', 'node_modules', 'work', 'inputs', '__pycache__', 'art', 'fxlogs')]
        for f in fn:
            fp = os.path.join(dp, f)
            if os.path.getsize(fp) > 50e6 or f.endswith(('.mp4', '.wav', '.png', '.jpg', '.flac', '.wasm')): continue
            try: t = open(fp, encoding='utf-8', errors='ignore').read()
            except Exception: continue
            if pat.search(t) or any(s in t for s in secrets): hits.append(os.path.relpath(fp, root))
gate('credential scan', ok(not hits), f'hits: {hits}' if hits else 'no key patterns or secret values in repo or release files')
# QA stills from the final videos
qd = os.path.join(DIST, 'qa_stills'); os.makedirs(qd, exist_ok=True)
def grab(p, t, out):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', p, '-frames:v', '1', '-q:v', '3', out], check=False)
fp = os.path.join(DIST, 'final.mp4'); shots = []
if os.path.exists(fp):
    for eid, s, fmt in fx_scenes:
        if fmt != 'landscape': continue
        t = s['start'] + min(s['end'] - s['start'] - .1, 2.6); o = os.path.join(qd, f'final_{s["key"]}_{t:.1f}.jpg'); grab(fp, t, o); shots.append(o)
    for t in (0.05, P['total'] / 3, P['total'] * 2 / 3, P['vo_end'] + 3):
        o = os.path.join(qd, f'final_t{t:07.1f}.jpg'); grab(fp, t, o); shots.append(o)
for S in P['shorts']:
    p = os.path.join(DIST, f"{S['id']}.mp4")
    if os.path.exists(p):
        for t in (0.0, S['total'] * .5, S['total'] - 1.2): o = os.path.join(qd, f"{S['id']}_t{t:05.1f}.jpg"); grab(p, t, o); shots.append(o)
ex = [s for s in shots if os.path.exists(s)]
gate('QA stills from final renders', ok(len(ex) == len(shots) and ex), f'{len(ex)} stills extracted from the released files')
if ex:
    from PIL import Image as _I
    def sheet(L, cols, w, h, out, pad=3):
        rows = (len(L) + cols - 1) // cols; c = min(cols, len(L))
        im = _I.new('RGB', (c * (w + 2 * pad), rows * (h + 2 * pad)), (255, 255, 255))
        for i, f in enumerate(L):
            t = _I.open(f).convert('RGB'); t.thumbnail((w, h)); x = (i % cols) * (w + 2 * pad) + pad + (w - t.width) // 2; y = (i // cols) * (h + 2 * pad) + pad + (h - t.height) // 2
            im.paste(t, (x, y))
        im.save(out, quality=88)
    for pre, cols, w, h, name in (('final_', 5, 384, 216, 'qa_contact_landscape.jpg'), ('SH', 9, 216, 384, 'qa_contact_shorts.jpg')):
        L = [s for s in ex if os.path.basename(s).startswith(pre)]
        if L: sheet(L, cols, w, h, os.path.join(DIST, name))
fails = [r for r in R if r['status'] == 'FAIL']; nc = [r for r in R if r['status'] == 'NOT CHECKED']
rep = {'schema': 'wwb-qa/1', 'run_id': os.environ.get('GITHUB_RUN_ID'), 'sha': os.environ.get('GITHUB_SHA'), 'pass': not fails, 'counts': {'PASS': len(R) - len(fails) - len(nc), 'FAIL': len(fails), 'NOT CHECKED': len(nc)}, 'gates': R,
       'files': {f: {'bytes': os.path.getsize(os.path.join(DIST, f)), 'sha256': sha256_file(os.path.join(DIST, f))} for f in VIDEOS if os.path.exists(os.path.join(DIST, f))}}
json.dump(rep, open(os.path.join(DIST, 'qa_report.json'), 'w'), indent=1, ensure_ascii=False)
with open(os.path.join(DIST, 'qa_report.md'), 'w') as f:
    f.write(f"# QA report — Why Intelligent People Enjoy Being Alone\n\nRun {rep['run_id']} @ {rep['sha']}: **{'PASS' if rep['pass'] else 'FAIL'}** ({rep['counts']})\n\n| Gate | Status | Detail |\n|---|---|---|\n")
    for r in R: f.write(f"| {r['gate']} | {r['status']} | {r['detail'].replace('|', '/')} |\n")
print('QA', 'PASS' if rep['pass'] else 'FAIL', rep['counts']); sys.exit(0 if rep['pass'] else 1)
