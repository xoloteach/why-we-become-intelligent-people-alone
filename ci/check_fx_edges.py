"""Fail early on any opaque object touching any bake boundary at any frame."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]
for p in sorted(root.glob('*/bake.json')):
 m=json.loads(p.read_text()); bad=m.get('edge_violations')
 if bad is None: raise SystemExit(f'Missing every-frame edge check: {p}')
 rows.append({'id':m['effect_id'],'frames':m['frames'],'edge_violations':bad})
report={'schema':'wwb-fx-edges/1','pass':bool(rows) and all(not r['edge_violations'] for r in rows),'jobs':rows}
(root/'edge_report.json').write_text(json.dumps(report,indent=1))
for r in rows:
 if r['edge_violations']: print('FAIL',r['id'],r['edge_violations'])
print('Every-frame bake-edge check:',len(rows),'jobs,',sum(r['frames'] for r in rows),'frames, PASS' if report['pass'] else 'frames, FAIL')
raise SystemExit(0 if report['pass'] else 1)
