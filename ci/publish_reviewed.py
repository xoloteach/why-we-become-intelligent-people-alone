"""Publish the exact runner export only after recorded delivery-review PASS."""
import os,sys,re,json,hashlib,urllib.request,subprocess,zipfile
from pathlib import Path
review=json.load(open(sys.argv[1]));run=str(review['run_id']);sha=review['sha'];repo=os.environ['GITHUB_REPOSITORY']
assert re.fullmatch(r'[0-9]+',run) and re.fullmatch(r'[0-9a-f]{40}',sha)
for k in ('all_layouts','all_effect_states','finished_motion_with_sound'):assert review.get(k)=='PASS',f'{k} not passed'
base=f'https://raw.githubusercontent.com/{repo}/ci-logs/runs/{run}/review/review_export/'
m=json.load(urllib.request.urlopen(base+'manifest.json'));assert str(m['run_id'])==run and m['sha']==sha
runmeta=json.load(urllib.request.urlopen(f'https://api.github.com/repos/{repo}/actions/runs/{run}'));assert runmeta['head_sha']==sha
D=Path('reviewed_dist');D.mkdir(exist_ok=True)
for name,v in m['files'].items():
 assert re.fullmatch(r'[A-Za-z0-9_.-]+',name);data=bytearray()
 for part in v['parts']:
  assert re.fullmatch(r'[A-Za-z0-9_.-]+',part)
  with urllib.request.urlopen(base+part) as r:data.extend(r.read())
 assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256'],name
 (D/name).write_bytes(data)
q=json.load(open(D/'qa_report.json'));assert q['pass'] and q['sha']==sha and str(q['run_id'])==run
assert q['counts']['FAIL']==0 and q['counts']['NOT CHECKED']==0
pat=re.compile(rb'(AIza[0-9A-Za-z_-]{35}|gh[pousr]_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{40,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
for p in D.iterdir():
 if p.suffix.lower() in ('.mp4','.jpg','.png','.wav','.flac'):continue
 if p.suffix=='.zip':
  with zipfile.ZipFile(p) as z:
   for item in z.infolist():
    if Path(item.filename).suffix.lower() in ('.mp4','.jpg','.png','.wav','.flac'):continue
    assert not pat.search(z.read(item)),f'Credential pattern in {p.name}/{item.filename}'
 else:assert not pat.search(p.read_bytes()),f'Credential pattern in {p.name}'
(D/'delivery_review.json').write_text(json.dumps(review,indent=2))
notes=Path('reviewed_notes.md');notes.write_text(f'# Why Intelligent People Enjoy Being Alone\n\nReviewed render run {run} @ `{sha}`.\n\nAutomated technical checks and recorded delivery-review criteria PASS.\n\nNarration and supplied artwork preserved. 11 Three.js objects; Rapier physics. All rendering on GitHub Actions.\n')
tag=f'v1.0.1-run{run}'
subprocess.run(['gh','release','create',tag,'--target',sha,'--title',f'Why Intelligent People Enjoy Being Alone — {tag}','--notes-file',str(notes),*[str(p) for p in D.iterdir() if p.is_file()]],check=True)
print('Published',tag)
