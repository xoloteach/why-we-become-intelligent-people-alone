"""Export runner-built review files in git-safe chunks. Not a final release."""
import os,sys,json,hashlib,shutil,subprocess
from pathlib import Path
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);dst.mkdir(parents=True,exist_ok=True)
if (src/'qa_stills').exists():shutil.make_archive(str(src/'qa_stills'),'zip',src,'qa_stills')
subprocess.run(['git','archive','--format=zip','-o',str((src/'source.zip').resolve()),os.environ['GITHUB_SHA']],check=True)
manifest={'schema':'wwb-review-export/1','run_id':os.environ['GITHUB_RUN_ID'],'sha':os.environ['GITHUB_SHA'],'files':{}}
for p in sorted(src.iterdir()):
 if not p.is_file() or p.name.endswith('.fxlog.json'):continue
 data=p.read_bytes();record={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'parts':[]}
 if len(data)>32*1024*1024:
  for i,a in enumerate(range(0,len(data),16*1024*1024)):
   name=p.name+f'.part{i:03d}';(dst/name).write_bytes(data[a:a+16*1024*1024]);record['parts'].append(name)
 else:shutil.copy2(p,dst/p.name);record['parts']=[p.name]
 manifest['files'][p.name]=record
(dst/'manifest.json').write_text(json.dumps(manifest,indent=1));print('Review export',len(manifest['files']),'files; build',manifest['run_id'])
