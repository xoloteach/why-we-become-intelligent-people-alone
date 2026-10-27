"""3D Object Library previews from the CI style-test bakes: per object, final frame front + three-quarter on warm paper and obsidian.
Usage: library_previews.py STYLE_OUT LIB_DIR  -> LIB_DIR/<object>/<test>_{paper,obsidian}_{front,threequarter}.png + LIB_DIR/<object>/<test>_preview.png + index.json"""
import os, sys, json, glob
import cv2, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src')); import fx_post as F
out, lib = sys.argv[1], sys.argv[2]; idx = {}
for q in sorted(glob.glob(os.path.join(out, 'style-*-q'))):
    tid = os.path.basename(q)[6:-2]; f = q[:-1] + 'f'
    for d in (q, f):
        if not os.path.exists(os.path.join(d, 'f0000.png')): F.post(d)
    m = json.load(open(os.path.join(q, 'bake.json'))); obj = m['object']; od = os.path.join(lib, obj); os.makedirs(od, exist_ok=True); tiles = {}
    for view, d in (('threequarter', q), ('front', f)):
        mm = json.load(open(os.path.join(d, 'bake.json'))); k = mm['frames'] - 1; im = cv2.imread(os.path.join(d, f'f{k:04d}.png'), cv2.IMREAD_UNCHANGED)
        for bgname, col in (('paper', F.PAPER), ('obsidian', F.OBS)):
            bg = np.full((im.shape[0], im.shape[1], 3), col, np.uint8)
            for s in mm['shadows'][k]: F.shadow(bg, s)
            F.over(bg, im); p = os.path.join(od, f'{tid}_{bgname}_{view}.png'); cv2.imwrite(p, bg); tiles[(bgname, view)] = bg
    sheet = np.vstack([np.hstack([tiles[('paper', 'front')], tiles[('paper', 'threequarter')]]), np.hstack([tiles[('obsidian', 'front')], tiles[('obsidian', 'threequarter')]])])
    cv2.imwrite(os.path.join(od, f'{tid}_preview.png'), sheet)
    ph = m.get('physics') or {}
    idx.setdefault(obj, []).append({'test': tid, 'object_id': m['object_id'], 'frames': m['frames'], 'versions': m['versions'], 'physics': {k: ph.get(k) for k in ('contacts', 'cueError', 'settle')} if ph else None,
                                    'perf': m.get('perf'), 'run_id': os.environ.get('GITHUB_RUN_ID'), 'alpha_peak': m.get('alpha_peak')})
json.dump(idx, open(os.path.join(lib, 'index.json'), 'w'), indent=1); print('library previews', {k: len(v) for k, v in idx.items()})
