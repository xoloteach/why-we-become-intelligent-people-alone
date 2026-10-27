"""Style-test sheets: per test, three-quarter timeline on paper + obsidian, and front/three-quarter final frames.
Usage: python3 src/fx_style_sheet.py BAKE_OUT SHEET_DIR"""
import os, sys, json, glob
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import fx_post as F
def key_frames(m):
    n = m['frames']; ph = m.get('physics') or {}; tg = sorted((ph.get('targets') or {}).values())
    if tg: return [8, max(0, tg[0] - 4), tg[0] + 1, tg[len(tg) // 2] + 2 if len(tg) > 2 else tg[-1] + 1, tg[-1] + 3, n - 1]
    return [8, int(n * .3), int(n * .45), int(n * .6), int(n * .75), n - 1]
def tile(d, k, dark):
    m = json.load(open(os.path.join(d, 'bake.json'))); k = min(k, m['frames'] - 1)
    im = cv2.imread(os.path.join(d, f'f{k:04d}.png'), cv2.IMREAD_UNCHANGED)
    bg = np.full((im.shape[0], im.shape[1], 3), F.OBS if dark else F.PAPER, np.uint8)
    for s in m['shadows'][k]: F.shadow(bg, s)
    F.over(bg, im); cv2.putText(bg, f'f{k}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, (60, 98, 200), 2); return bg
def sheet(out_dir, tid, dst):
    q, f = os.path.join(out_dir, f'style-{tid}-q'), os.path.join(out_dir, f'style-{tid}-f')
    for d in (q, f):
        if not os.path.exists(os.path.join(d, 'f0000.png')): F.post(d)
    m = json.load(open(os.path.join(q, 'bake.json'))); ks = key_frames(m); last = m['frames'] - 1
    r1 = np.hstack([tile(q, k, False) for k in ks]); r2 = np.hstack([tile(q, k, True) for k in ks])
    r3 = np.hstack([tile(f, last, False), tile(f, last, True), tile(q, last, False), tile(q, last, True), tile(f, ks[2], False), tile(f, ks[3], True)])
    img = np.vstack([r1, r2, r3]); cv2.putText(img, tid, (10, img.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, .8, (60, 98, 200), 2)
    cv2.imwrite(dst, img, [cv2.IMWRITE_JPEG_QUALITY, 82]); return dst
if __name__ == '__main__':
    out, sd = sys.argv[1], sys.argv[2]; os.makedirs(sd, exist_ok=True)
    ids = sorted({os.path.basename(p)[6:-2] for p in glob.glob(os.path.join(out, 'style-*-q'))})
    for tid in ids: print(sheet(out, tid, os.path.join(sd, f'{tid}.jpg')))
