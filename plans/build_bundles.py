import re, json
OPEN={'L':'[L]','R':'[R]','T':'[T]','TL':'[TL]','TR':'[TR]'}
def tele(d):
    d=re.sub(r"\b(a|an|the)\s+","",d,flags=re.I)
    d=re.sub(r"^Stickman's ","His ",d); d=re.sub(r"^Stickman ","",d)
    return d[0].upper()+d[1:]
def panel(code, desc, vertical=False):
    dark=code.startswith('D:'); code=code[2:] if dark else code
    t=tele(desc)+'.'+(' Obsidian.' if dark else '')
    if not vertical: t+=' '+OPEN[code]
    return t
STY=("Ink doodle, warm paper #F7F4EE, charcoal lines, rust #C8623C watercolor wash; obsidian panels #16150F, warm rim light. "
     "Canonical stickman from reference (round white head, charcoal hoodie, rust lining) in every panel unless noted; others faceless grey figures. ")
HEAD16="16:9 1920x1080, exact 3x3 grid, thin black borders. "+STY+"Bracket = side kept 40% empty (L/R/T/TL/TR). Bottom 20% clean. No text.\n"
HEAD9="9:16 1080x1920, exact 2x2 grid of four 9:16 panels, thin black ink borders. "+STY+"Each panel: subject mid-frame, top 40% empty, bottom 25% clean. No text.\n"
POS=['Top-left','Top-right','Bottom-left','Bottom-right']
wc=lambda s: len(s.split())
def read(fn):
    out=[];cur=None
    for ln in open(fn):
        ln=ln.rstrip('\n')
        if not ln or ln.startswith('#'): continue
        if ln.startswith('=='): cur={'title':ln[3:].strip(),'rows':[]}; out.append(cur); continue
        cur['rows'].append(ln.split('|'))
    return out
L=[];stats=[]
for n,s in enumerate(read('landscape_beats.txt'),1):
    sid,name=s['title'].split(' ',1)
    body=HEAD16+'\n'.join(f"P{i+1}: "+panel(c,d) for i,(c,d) in enumerate(s['rows']))
    L.append({'id':sid,'name':name,'file':f'sheet-{n:02d}.png','prompt':body,'panels':[{'code':c,'desc':d} for c,d in s['rows']]}); stats.append((sid,wc(body)))
SH=[]
for s in read('shorts_beats.txt'):
    sid=s['title'].split(' ',1)[0]; nm,rng=[x.strip() for x in s['title'].split(' ',1)[1].split('|')]
    groups={}
    for k,c,d in s['rows']: groups.setdefault(k,[]).append((c,d))
    for k,ps in groups.items():
        body=HEAD9+'\n'.join(f"P{i+1} {POS[i]}: "+panel(c,d,True) for i,(c,d) in enumerate(ps))
        SH.append({'short':sid,'name':nm,'range':rng,'sheet':k,'file':f'{sid.lower()}-sheet-{k}.png','prompt':body,'panels':[{'code':c,'desc':d} for c,d in ps]}); stats.append((sid+k,wc(body)))
json.dump({'landscape':L,'shorts':SH,'stats':stats},open('prompts_generated.json','w'),indent=1)
st=stats; print(sorted(st,key=lambda x:-x[1])[:10]); print('over16',[k for k,w in st if not k.startswith('SH') and w>=150]); print('over9',[k for k,w in st if k.startswith('SH') and w>=140])
