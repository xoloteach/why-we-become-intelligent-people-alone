"""seo.md for the release: real chapter times from the final plan (processed-narration alignment) + Shorts copy."""
import os, sys, re, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); W = os.environ.get('WWB_WORK', os.path.join(ROOT, 'work')); out = sys.argv[1]
s = open(os.path.join(ROOT, 'seo.md'), encoding='utf-8').read(); ch = open(os.path.join(W, 'chapters.txt'), encoding='utf-8').read().strip()
s = re.sub(r'## Chapters.*?(?=\n## )', '## Chapters (final render timestamps)\n' + ch + '\n', s, flags=re.S)
P = json.load(open(os.path.join(W, 'plan.json')))
s += '\n## Shorts\n' + ''.join(f"- **{S['id']} — {S['title']}** ({S['total']:.1f}s; narration {S['t0']:.2f}–{S['t1']:.2f}s of the main episode)\n" for S in P['shorts'])
sp = os.path.join(ROOT, 'shorts_scripts.md')
if os.path.exists(sp): s += '\n' + open(sp, encoding='utf-8').read()
open(os.path.join(out, 'seo.md'), 'w', encoding='utf-8').write(s); print(ch)
