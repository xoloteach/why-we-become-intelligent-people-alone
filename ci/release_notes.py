import sys, json, os
d = sys.argv[1]; q = json.load(open(os.path.join(d, 'qa_report.json')))
print(f"Automated render of **Why Intelligent People Enjoy Being Alone** (landscape 1920×1080 + three native 1080×1920 Shorts).\n")
print(f"Render run: https://github.com/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ.get('GITHUB_RUN_ID')} @ `{os.environ.get('GITHUB_SHA', '')[:12]}`\n")
print(f"QA: **{'PASS' if q['pass'] else 'FAIL'}** — {q['counts']}\n\n| Gate | Status | Detail |\n|---|---|---|")
for r in q['gates']: print(f"| {r['gate']} | {r['status']} | {r['detail'][:180].replace('|', '/')} |")
print('\n| File | Bytes | SHA-256 |\n|---|---|---|')
for f, v in q['files'].items(): print(f"| {f} | {v['bytes']} | `{v['sha256']}` |")
print('\nNarration: the user\'s Google AI Studio take, unchanged script and audio (processed vocal chain only). Visual art: the user\'s Google Flow images. 3D objects: Three.js r186 + Rapier 0.21 bakes (see QA gates).')
