"""Word-highlight ASS captions from the aligned script tokens (one event per spoken-word state).
Landscape: Montserrat ExtraBold 60, outline 4, shadow 1.5, Alignment 2, MarginV 82.
Shorts: same face, MarginV 420 / L80 / R200, groups of <=5 words and <=2 lines; words starting at or after end-0.04 are withheld."""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__)); from common import WORK, text_w, atomic_json
WHITE, RUST = '&H00FFFFFF&', '&H003C62C8&'
def ts(t):
    t = max(0.0, t); cs = int(round(t * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100); return f'{h}:{m:02d}:{s:02d}.{cs:02d}'
def header(W, H, mv, ml, mr):
    return ('[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n'
            'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
            'Style: Default,Montserrat ExtraBold,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,1.5,2,%d,%d,%d,1\n\n[Events]\n'
            'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n') % (W, H, ml, mr, mv)
def groups(toks, max_words, max_w, max_lines):
    out, cur = [], []
    for i, t in enumerate(toks):
        cur.append(t); nxt = toks[i + 1] if i + 1 < len(toks) else None
        brk = nxt is None or re.search(r'[.!?;:,—]$', t['w']) or (nxt['start'] - t['end'] > 0.24) or len(cur) >= max_words
        if not brk and nxt is not None:
            trial = ' '.join(x['w'] for x in cur + [nxt])
            if lines_needed(trial, max_w) > max_lines: brk = True
        if brk: out.append(cur); cur = []
    return out
def lines_needed(s, max_w):
    n, cur = 1, ''
    for w in s.split():
        z = (cur + ' ' + w).strip()
        if text_w(z, 60) > max_w and cur: n += 1; cur = w
        else: cur = z
    return n
def build(toks, W, H, mv, ml, mr, max_words, max_lines, path, t0=0.0, t_end=None):
    ev = []
    if t_end is not None: toks = [t for t in toks if t['start'] < t_end - 0.04]
    G = groups(toks, max_words, W - ml - mr - 40, max_lines)
    for gi, g in enumerate(G):
        nxt = G[gi + 1][0]['start'] if gi + 1 < len(G) else None
        g_end = g[-1]['end'] + 0.35 if nxt is None else min(g[-1]['end'] + 0.35, nxt)
        if t_end is not None: g_end = min(g_end, t_end)
        for k, t in enumerate(g):
            a = t['start']; b = g[k + 1]['start'] if k + 1 < len(g) else g_end
            if b - a < 0.01: continue
            txt = ' '.join((f'{{\\c{RUST}}}{x["w"]}{{\\c{WHITE}}}' if j == k else x['w']) for j, x in enumerate(g))
            ev.append(f'Dialogue: 0,{ts(a - t0)},{ts(b - t0)},Default,,0,0,0,,{txt}')
    with open(path, 'w', encoding='utf-8') as f: f.write(header(W, H, mv, ml, mr) + '\n'.join(ev) + '\n')
    return {'path': os.path.basename(path), 'events': len(ev), 'groups': len(G), 'max_group_words': max(len(g) for g in G)}
def main():
    A = json.load(open(os.path.join(WORK, 'align.json'))); P = json.load(open(os.path.join(WORK, 'plan.json'))); toks = A['tokens']; rep = {}
    rep['landscape'] = build(toks, 1920, 1080, 82, 120, 120, 7, 1, os.path.join(WORK, 'captions.ass'))
    for s in P['shorts']:
        st = [t for t in toks if t['start'] >= s['t0'] and t['start'] < s['t1']]
        rep[s['id']] = build(st, 1080, 1920, 420, 80, 200, 5, 2, os.path.join(WORK, f"captions_{s['id']}.ass"), t0=s['t0'], t_end=s['t1'])
    atomic_json(os.path.join(WORK, 'captions_report.json'), rep); print(rep)
if __name__ == '__main__': main()
