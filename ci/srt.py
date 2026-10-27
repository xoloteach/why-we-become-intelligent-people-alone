"""Plain SRT (script wording, aligned times) for upload as YouTube subtitles."""
import sys, json
A = json.load(open(sys.argv[1])); toks = A['tokens']; out = []; cur = []
def ts(t): ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000); return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
for i, t in enumerate(toks):
    cur.append(t); nxt = toks[i + 1] if i + 1 < len(toks) else None
    if nxt is None or t['w'][-1:] in '.!?' or (len(cur) >= 5 and t['w'][-1:] in ',;:—') or (len(cur) >= 12 and len(toks) - i > 3) or nxt['line'] != t['line'] or nxt['start'] - t['end'] > .5: out.append(cur); cur = []
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for k, g in enumerate(out, 1): f.write(f"{k}\n{ts(g[0]['start'])} --> {ts(g[-1]['end'])}\n{' '.join(x['w'] for x in g)}\n\n")
print('srt cues', len(out))
