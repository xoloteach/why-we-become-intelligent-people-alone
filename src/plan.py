"""Scene plan: resolves every scene, label and 3D-object cue from the aligned narration.
Outputs work/plan.json (landscape + 3 Shorts), work/fx_jobs/*.json (bake jobs, scene-local cue seconds),
work/chapters.txt and a warnings list. A label whose cue cannot be resolved inside its scene is withheld."""
import os, sys, json, math, re
sys.path.insert(0, os.path.dirname(__file__)); from common import ROOT, WORK, FPS, atomic_json
from align import norm
from extract import darkset
VO_END = 1226.515; END_CARD = 5.0; SHORT_END = 2.5; LEAD = 0.10
CHAPTERS = ['Why some people enjoy being alone', 'Being alone vs. being lonely', 'How you process the world', 'Do intelligent people prefer solitude?',
            'Deep work needs uninterrupted time', 'Joy without an audience', 'Hearing your own thoughts', 'When reflection becomes rumination',
            'The emotional work of socialising', 'Preference or fear?', 'Choosing solitude vs. hiding in it', 'Depth over frequency',
            "Independence isn't the absence of others", 'Why solitude grows with self-knowledge', 'The value of quiet']
REGION = {'landscape': {'w': 440, 'h': 410}, 'portrait': {'w': 420, 'h': 320}}
def load_align():
    a = json.load(open(os.path.join(WORK, 'align.json'))); return a['tokens'], a['lines'], a
def open_sides():
    sides = {}; sheet = None; i = 0
    for ln in open(os.path.join(ROOT, 'plans', 'landscape_beats.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if ln.startswith('== '): sheet = ln[3:6]; i = 0; continue
        if not ln or ln.startswith('#'): continue
        i += 1; code = ln.split('|')[0].replace('D:', ''); sides[f'{sheet}-{i}'] = code
    return sides
def parse_dsl(path):
    rows, groups = [], []
    for ln in open(path, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'): continue
        if ln.startswith('== '):
            p = ln[3:].split('|'); groups.append({'id': p[0], 'start': float(p[1]), 'end': float(p[2]), 'title': p[3], 'topic': p[4], 'rows': []}); continue
        p = ln.split('|'); chap = p[0].startswith('*'); key = p[0].lstrip('*')
        labels = []
        for it in (p[4].split(';') if len(p) > 4 and p[4] else []):
            txt, _, cue = it.rpartition('@'); labels.append({'text': txt.lstrip('+'), 'cue_word': cue, 'keep': txt.startswith('+')})
        r = {'key': key, 'anchor': p[1], 'kind': p[2], 'title': p[3], 'labels': labels, 'chapter_start': chap}
        (groups[-1]['rows'] if groups else rows).append(r)
    return rows, groups
def anchor_time(toks, lines, anchor, warn, key):
    li, _, phrase = anchor.partition(':'); li = int(li); lt = [t for t in toks if t['line'] == li]
    if not phrase: return lt[0]['start']
    ph = [norm(w) for w in phrase.split()]; seq = [norm(t['w']) for t in lt]
    for k in range(len(seq) - len(ph) + 1):
        if seq[k:k + len(ph)] == ph: return lt[k]['start']
    warn.append(f'{key}: phrase "{phrase}" not found in line {li}; using line start'); return lt[0]['start']
def find_word(toks, word, t0, t1, after=-1.0):
    w = norm(word)
    for t in toks:
        if t['start'] < t0 - 0.25 or t['start'] < after: continue
        if t['start'] > t1: break
        n = norm(t['w']); parts = [norm(x) for x in t['w'].split('-')]
        if n == w or w in parts or (len(w) >= 4 and n.startswith(w)): return t
    return None
def resolve_scenes(rows, toks, lines, t_begin, t_end, warn, prefix=''):
    sc = []
    for i, r in enumerate(rows):
        s = dict(r); s['anchor_t'] = anchor_time(toks, lines, r['anchor'], warn, r['key']); sc.append(s)
    for i, s in enumerate(sc): s['start'] = t_begin if i == 0 else max(sc[i - 1]['anchor_t'] + 0.5, s['anchor_t'] - LEAD)
    for i, s in enumerate(sc): s['end'] = sc[i + 1]['start'] if i + 1 < len(sc) else t_end
    for s in sc:
        after = -1.0; cues = []
        for lb in s['labels']:
            t = find_word(toks, lb['cue_word'], s['start'], s['end'], after) or find_word(toks, lb['cue_word'], s['start'], s['end'])
            if t is None or t['start'] >= s['end'] - 0.04:
                warn.append(f"{prefix}{s['key']}: cue '{lb['cue_word']}' not spoken inside scene {s['start']:.2f}-{s['end']:.2f}; label withheld"); lb['t'] = None; continue
            lb['t'] = round(max(s['start'], t['start'] - 0.06), 3); after = max(after, t['start']); cues.append(lb['t'])
        s['start'] = round(s['start'], 3); s['end'] = round(s['end'], 3)
    return sc
def fx_job(s, spec, toks, fmt, eid, warn):
    P = dict(spec.get('params', {})); cues = []; after = -1.0
    for w in spec['cues']:
        t = find_word(toks, w, s['start'], s['end'], after)
        if t is None: warn.append(f"{eid}: fx cue '{w}' not found; 3D object falls back to 2D diagram"); return None
        cues.append(t['start'] + spec.get('cue_shift', 0.0)); after = t['start']
    loc = [max(0.3, c - s['start']) for c in cues]
    if 'dur_to' in spec:
        t = find_word(toks, spec['dur_to'], s['start'], s['end'], after)
        if t is None: warn.append(f"{eid}: dur_to '{spec['dur_to']}' not found; default duration")
        else: P['dur'] = round(max(0.6, t['start'] + spec.get('dur_pad', 0.0) - cues[0]), 3)
    P['cues'] = [round(c, 3) for c in loc]
    dur = s['end'] - s['start']; frames = int(math.ceil((dur + 0.3) * FPS))
    return {'schema': 'wwb-fx-job/1', 'effect_id': eid, 'object': spec['object'], 'fps': FPS, 'frames': frames, 'region': REGION[fmt], 'supersample': 2,
            'seed': sum(map(ord, eid)) % 997, 'params': P, 'format': fmt, 'scene_key': s['key'], 'scene_start': s['start'],
            'cue_words': spec['cues'], 'cue_times_abs': [round(c, 3) for c in cues]}
def main():
    toks, lines, A = load_align(); warn = []; dark = darkset(); sides = open_sides(); specs = json.load(open(os.path.join(ROOT, 'plan', 'fx_specs.json')))
    rows, _ = parse_dsl(os.path.join(ROOT, 'plan', 'scenes.dsl'))
    L = resolve_scenes(rows, toks, lines, 0.0, VO_END, warn)
    ch = 0; chapters = []; jobs = []
    for i, s in enumerate(L):
        if s['chapter_start']: ch += 1; chapters.append({'n': ch, 'name': CHAPTERS[ch - 1], 'start': s['start'] if i else 0.0})
        s['chapter'] = ch; s['dark'] = s['key'] in dark; side = sides.get(s['key'], 'L')
        s['layout'] = 'feature' if side == 'T' else ('right' if side in ('L', 'TL', 'BL') else 'left'); s['art'] = s['key']; s['i'] = i
        if s['kind'] == 'fx':
            j = fx_job(s, specs['landscape'][s['key']], toks, 'landscape', f"L-{s['key']}", warn)
            s['fx'] = j['effect_id'] if j else None
            if j: jobs.append(j)
            else: s['kind'] = 'list'
    _, groups = parse_dsl(os.path.join(ROOT, 'plan', 'shorts.dsl')); shorts = []
    for g in groups:
        prev = max([t['end'] for t in toks if t['end'] <= g['start'] + 0.01] or [0.0]); nxt = min([t['start'] for t in toks if t['start'] >= g['end'] - 0.01] or [VO_END])
        t0 = round(max(prev, g['start'] - 0.10), 3); t1 = round(min(nxt - 0.02, g['end'] + 0.15), 3)  # clean cut points, never mid-word
        sc = resolve_scenes(g['rows'], toks, lines, t0, t1, warn, g['id'] + ':')
        for i, s in enumerate(sc):
            s['dark'] = s['key'] in dark; s['art'] = s['key']; s['i'] = i; s['layout'] = 'portrait'
            if s['kind'] == 'fx':
                j = fx_job(s, specs['shorts'][s['key']], toks, 'portrait', f"{g['id']}-{s['key']}", warn)
                s['fx'] = j['effect_id'] if j else None
                if j: j['short'] = g['id']; jobs.append(j)
                else: s['kind'] = 'list'
        shorts.append({'id': g['id'], 'title': g['title'], 'topic': g['topic'], 'start': g['start'], 'end': g['end'], 't0': t0, 't1': t1, 'vo_dur': round(t1 - t0, 3), 'end_card': SHORT_END, 'total': round(t1 - t0 + SHORT_END, 3), 'scenes': sc})
    # 3D distribution check (thirds, max two in a row)
    fx_idx = [s['i'] for s in L if s.get('fx')]; thirds = [sum(1 for s in L if s.get('fx') and k * VO_END / 3 <= s['start'] < (k + 1) * VO_END / 3) for k in range(3)]
    run = mx = 0
    for s in L: run = run + 1 if s.get('fx') else 0; mx = max(mx, run)
    plan = {'schema': 'wwb-plan/1', 'align_engine': A['engine'], 'vo_end': VO_END, 'end_card': END_CARD, 'total': round(VO_END + END_CARD, 3), 'fps': FPS,
            'chapters': chapters, 'scenes': L, 'shorts': shorts, 'fx_summary': {'landscape': len(fx_idx), 'thirds': thirds, 'max_run': mx,
            'shorts': {g['id']: sum(1 for s in g['scenes'] if s.get('fx')) for g in shorts}}, 'warnings': warn}
    atomic_json(os.path.join(WORK, 'plan.json'), plan)
    jd = os.path.join(WORK, 'fx_jobs'); os.makedirs(jd, exist_ok=True)
    for f in os.listdir(jd): os.remove(os.path.join(jd, f))
    for j in jobs: json.dump(j, open(os.path.join(jd, j['effect_id'] + '.json'), 'w'))
    with open(os.path.join(WORK, 'chapters.txt'), 'w') as f:
        for c in chapters: m, sec = divmod(int(c['start']), 60); f.write(f"{m:02d}:{sec:02d} {c['name']}\n")
    print('scenes', len(L), 'fx', plan['fx_summary'], 'jobs', len(jobs), 'warnings', len(warn))
    for w in warn: print('WARN', w)
if __name__ == '__main__': main()
