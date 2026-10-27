import sys,json,os
w=sys.argv[1];a=json.load(open(w+'/fx_out/L-S01-6/bake.json'));b=json.load(open('/tmp/rebake/L-S01-6/bake.json'))
r={'sample':'L-S01-6','pass':a['final_sha256']==b['final_sha256'],'frames':len(a['final_sha256'])}
json.dump(r,open(w+'/determinism.json','w'));print(r);assert r['pass'],'sample re-bake differs'
