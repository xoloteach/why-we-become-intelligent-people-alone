"""Still-only text regression sweep; no video rendering."""
import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import common as C
import scene as SC
import numpy as np
p=json.loads((Path(C.WORK)/'plan.json').read_text()); bad=[];scenes=0
for fmt,ss in [('landscape',p['scenes'])]+[(s['id'],s['scenes']) for s in p['shorts']]:
 for s in ss:
  scenes+=1;feat=fmt=='landscape' and s['layout']=='feature'
  width=1720 if feat else 805;size=(90 if feat else 82) if fmt=='landscape' else 86
  limit=225 if fmt=='landscape' else 244;floor=54 if fmt=='landscape' else 62
  g=C.glyph(s['title'],size,C.INK,width,'Black')
  while g.shape[0]>limit and size>floor:
   size-=2;g=C.glyph(s['title'],size,C.INK,width,'Black')
  if g.shape[0]>limit:bad.append(f'{fmt}:{s["key"]}: headline height {g.shape[0]}>{limit}')
  f=np.full((1200,1920,3),245,np.uint8)
  if s.get('fx'):SC.fx_labels(f,s,s['end']+1,30,30,680 if feat else (330 if fmt=='landscape' else 400))
  else:SC.diagram(f,s,s['end']+1,30,60,1150 if feat else 790,320)
for e in C.TEXT_FIT_LOG:
 if e['actual']<22:bad.append(f'Auto-fit below 22px: {e}')
z=SC.fit('Overwhelming',46,310,max_lines=3)
if not (C.text_w('Overwhelming',z)<=310 and z>=22):bad.append('Overwhelming width regression')
g=C.glyph('Overwhelming',46,C.INK,310,'ExtraBold','center')
if g[:,:,3][:,:2].any() or g[:,:,3][:,-2:].any():bad.append('word touches glyph boundary')
r={'schema':'wwb-typography/1','pass':not bad,'scenes':scenes,'width_regression_font':z,'auto_fits':C.TEXT_FIT_LOG,'failures':bad}
(Path(C.WORK)/'typography.json').write_text(json.dumps(r,indent=1));print('Typography',r['pass'],scenes,'scenes;',len(r['auto_fits']),'safe word fits;',bad)
sys.exit(bool(bad))
