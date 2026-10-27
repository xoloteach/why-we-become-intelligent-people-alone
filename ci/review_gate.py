"""A technical PASS must never imply that full motion/audio playback was inspected."""
import os,sys,json,urllib.request
from pathlib import Path
D=Path(sys.argv[1]);run=os.environ['GITHUB_RUN_ID'];sha=os.environ['GITHUB_SHA'];repo=os.environ['GITHUB_REPOSITORY']
url=f'https://raw.githubusercontent.com/{repo}/main/reviews/{run}.json'
try:r=json.load(urllib.request.urlopen(url,timeout=20))
except Exception:r={}
keys=['all_layouts','all_effect_states','finished_motion_with_sound']
gates=[{'gate':k,'status':'PASS' if r.get(k)=='PASS' and r.get('sha')==sha else 'NOT CHECKED'} for k in keys]
result={'run_id':run,'sha':sha,'pass':all(x['status']=='PASS' for x in gates),'gates':gates,'review_url':url}
(D/'delivery_review.json').write_text(json.dumps(result,indent=2))
for g in gates:print(g['status'],g['gate'])
if not result['pass']:print('HOLD FINAL RELEASE: required playback/review not complete. Review files remain available; no final-quality claim.')
sys.exit(0 if result['pass'] else 1)
