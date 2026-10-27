"""Expand tests/style_tests.json into bake jobs (three-quarter + front view per test)."""
import json, os, sys
spec = json.load(open(os.path.join(os.path.dirname(__file__), 'style_tests.json'))); out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for i, t in enumerate(spec['tests']):
    for v in ('q', 'f'):
        view = dict(t.get('view', {}));
        if v == 'f': view.update(t.get('front', spec['front']))
        job = {'schema': 'wwb-fx-job/1', 'effect_id': f"style-{t['id']}-{v}", 'object': t['object'], 'fps': 30, 'frames': t['frames'],
               'region': spec['region'], 'supersample': 2, 'seed': 11 + i, 'params': t['params']}
        if view: job['view'] = view
        json.dump(job, open(os.path.join(out, f"style-{t['id']}-{v}.json"), 'w'))
print(len(spec['tests']) * 2)
