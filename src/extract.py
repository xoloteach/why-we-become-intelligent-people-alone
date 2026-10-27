"""Panel extraction: detect real grid gutters/borders near the expected divisions, trim border remnants,
4x FSRCNN reconstruction (+ mild Lanczos blend and sharpen), soft alpha matte from the paper estimate,
speck removal and pale-interior preservation. Writes work/layers/*.png, work/upscale_report.json, QA overlays."""
import os, sys, json, zipfile, glob
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import ROOT, WORK, atomic_write_png, atomic_json
FLOW = json.load(open(os.path.join(ROOT, 'plan', 'flow_files.json'))); MAP = json.load(open(os.path.join(ROOT, 'plan', 'flow_map.json')))
def load(key):
    p = os.path.join(WORK, 'flow', FLOW[key]); return cv2.imread(p)
def gutter(g, axis, k, n, search):
    """Find the gutter/border band nearest k/n of the axis. Uniform columns (black border or white gutter) have low std."""
    prof_std = g.std(axis=axis).astype(np.float32); prof_mean = g.mean(axis=axis).astype(np.float32)
    size = len(prof_std); c = round(size * k / n); lo, hi = max(1, c - search), min(size - 1, c + search)
    score = prof_std[lo:hi] + 0.15 * np.minimum(np.abs(prof_mean[lo:hi] - 0), np.abs(prof_mean[lo:hi] - 255))
    j = lo + int(np.argmin(cv2.GaussianBlur(score.reshape(1, -1), (1, 5), 0).ravel()))
    thr = max(10.0, float(prof_std[j]) * 2.5 + 4); a = j; b = j
    while a > lo - search // 2 and a > 1 and prof_std[a - 1] < thr: a -= 1
    while b < hi + search // 2 and b < size - 2 and prof_std[b + 1] < thr: b += 1
    return a, b
def edge_band(g, axis, side, maxw=14):
    """Outer border/frame thickness at one sheet edge."""
    prof = g.std(axis=axis); size = len(prof); w = 0
    idx = range(size) if side == 0 else range(size - 1, -1, -1)
    for i in idx:
        if prof[i] < 12 and w < maxw: w += 1
        else: break
    return w
def trim_cell(c):
    """Remove leftover border lines / gutter strips (uniform dark or bright rows/cols) at the crop edges."""
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY).astype(np.float32); t = [0, 0, 0, 0]
    for side in range(4):
        for k in range(16):
            row = (g[k] if side == 0 else g[-1 - k] if side == 1 else g[:, k] if side == 2 else g[:, -1 - k])
            if row.std() < 9 and (row.mean() < 90 or row.mean() > 236): t[side] = k + 1
            elif row.mean() < 60: t[side] = k + 1
            else: break
    h, w = c.shape[:2]; return c[t[0] + 2:h - t[1] - 2, t[2] + 2:w - t[3] - 2]
def grid(img, rows, cols, search):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32); H, W = g.shape
    xs = [(0, edge_band(g, 0, 0))] + [gutter(g, 0, k, cols, search) for k in range(1, cols)] + [(W - 1 - edge_band(g, 0, 1), W - 1)]
    ys = [(0, edge_band(g, 1, 0))] + [gutter(g, 1, k, rows, search) for k in range(1, rows)] + [(H - 1 - edge_band(g, 1, 1), H - 1)]
    cells = []
    for r in range(rows):
        for c in range(cols):
            x0, x1 = xs[c][1] + 1, xs[c + 1][0]; y0, y1 = ys[r][1] + 1, ys[r + 1][0]; cells.append((x0, y0, x1, y1))
    return cells, xs, ys
def qa_overlay(img, cells, out):
    o = img.copy()
    for i, (x0, y0, x1, y1) in enumerate(cells): cv2.rectangle(o, (x0, y0), (x1, y1), (0, 0, 255), 2); cv2.putText(o, str(i + 1), (x0 + 6, y0 + 22), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 0, 255), 2)
    cv2.imwrite(out, o, [cv2.IMWRITE_JPEG_QUALITY, 80])
_sr = None
def upscale(a):
    global _sr
    if _sr is None:
        try:
            _sr = cv2.dnn_superres.DnnSuperResImpl_create(); _sr.readModel(os.environ.get('FSRCNN_MODEL', '/data/sr_models/FSRCNN_x4.pb')); _sr.setModel('fsrcnn', 4)
        except Exception as e:
            if os.environ.get('WWB_REQUIRE_SR') == '1': raise
            print('WARN: FSRCNN unavailable, Lanczos stand-in (local test only):', e); _sr = False
    l = cv2.resize(a, (a.shape[1] * 4, a.shape[0] * 4), interpolation=cv2.INTER_LANCZOS4)
    if not _sr: return l, 'lanczos-test'
    b = _sr.upsample(a); b = cv2.addWeighted(b, .78, l, .22, 0); b = cv2.addWeighted(b, 1.12, cv2.GaussianBlur(b, (0, 0), .8), -.12, 0); return b, 'fsrcnn-x4'
def strip_frame_lines(a8):
    """Remove Flow panel border strokes: thin straight runs (>=50% of the side, <=1.4% thick) in the outer 14% band
    that are ISOLATED (both flanks mostly empty along the run) - so edges of filled shapes (chair sides, walls, door
    frames) are never cut. Anything outside a full-length isolated border (>=80% of the side, outer 8%) is margin."""
    H, W = a8.shape; m = (a8 > 40).astype(np.uint8); K = cv2.getStructuringElement; out = a8.copy(); occ = (a8 > 150).astype(np.float32)  # strong matte only: pale gutters/margins (white vs paper) do not count as art
    hl = cv2.morphologyEx(m, cv2.MORPH_OPEN, K(cv2.MORPH_RECT, (max(3, int(W * .5)), 1)))
    vl = cv2.morphologyEx(m, cv2.MORPH_OPEN, K(cv2.MORPH_RECT, (1, max(3, int(H * .5)))))
    hl &= ~cv2.dilate(cv2.morphologyEx(hl, cv2.MORPH_OPEN, K(cv2.MORPH_RECT, (1, max(3, int(H * .014))))), K(cv2.MORPH_RECT, (5, 5))) & 1
    vl &= ~cv2.dilate(cv2.morphologyEx(vl, cv2.MORPH_OPEN, K(cv2.MORPH_RECT, (max(3, int(W * .014)), 1))), K(cv2.MORPH_RECT, (5, 5))) & 1
    by, bx = int(H * .14), int(W * .14); hl[by:H - by, :] = 0; vl[:, bx:W - bx] = 0
    keep = np.zeros_like(m); cuts = {'top': [], 'bot': [], 'lf': [], 'rt': []}; off = 14
    for mask, horiz in ((hl, True), (vl, False)):
        n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
        for k in range(1, n):
            x, y, w, h = st[k, :4]
            if horiz:
                ya, yb = y - off, y + h + off; fl = (occ[ya, x:x + w].mean() if ya >= 0 else 0.0, occ[yb, x:x + w].mean() if yb < H else 0.0); L = w / W; pos = y + h / 2; side = 'top' if pos < H / 2 else 'bot'; edge = min(y, H - y - h) < H * .08
            else:
                xa, xb = x - off, x + w + off; fl = (occ[y:y + h, xa].mean() if xa >= 0 else 0.0, occ[y:y + h, xb].mean() if xb < W else 0.0); L = h / H; pos = x + w / 2; side = 'lf' if pos < W / 2 else 'rt'; edge = min(x, W - x - w) < W * .08
            if max(fl) < .35:  # isolated stroke, not the edge of a drawn shape
                keep[lab == k] = 1
                if L >= .8 and edge: cuts[side].append((y, y + h) if horiz else (x, x + w))
    out[cv2.dilate(keep, K(cv2.MORPH_RECT, (9, 9))) > 0] = 0; pad = 6
    if cuts['top']: out[:max(b for a, b in cuts['top']) + pad] = 0
    if cuts['bot']: out[min(a for a, b in cuts['bot']) - pad:] = 0
    if cuts['lf']: out[:, :max(b for a, b in cuts['lf']) + pad] = 0
    if cuts['rt']: out[:, min(a for a, b in cuts['rt']) - pad:] = 0
    return out
def matte(b, dark):
    hh, ww = b.shape[:2]; o = int(.03 * min(hh, ww)); t = max(8, int(.05 * min(hh, ww)))  # inner band: skips gutters and border strokes
    sample = np.median(np.concatenate([b[o:o + t, o:ww - o].reshape(-1, 3), b[hh - o - t:hh - o, o:ww - o].reshape(-1, 3), b[o:hh - o, o:o + t].reshape(-1, 3), b[o:hh - o, ww - o - t:ww - o].reshape(-1, 3)]), axis=0)
    delta = np.max(np.abs(b.astype(np.float32) - sample), axis=2); alpha = np.clip((delta - 9) / 35, 0, 1).astype(np.float32)
    e = max(6, int(.015 * min(hh, ww))); alpha[:e] = 0; alpha[-e:] = 0; alpha[:, :e] = 0; alpha[:, -e:] = 0  # Flow panel frame strokes hug the trimmed cell edge
    alpha = strip_frame_lines((alpha * 255).astype(np.uint8)).astype(np.float32) / 255  # strip borders BEFORE hull fill (closed frame = full fill)
    solid = (alpha > .4).astype(np.uint8) * 255; ct, _ = cv2.findContours(solid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); hull = np.zeros_like(solid)
    for x in ct:
        if cv2.contourArea(x) > 120 * 4: cv2.drawContours(hull, [x], -1, 255, -1)
    alpha = np.maximum(alpha, cv2.GaussianBlur(hull, (5, 5), 0) / 255)
    a8 = strip_frame_lines((alpha * 255).astype(np.uint8)); ns, lab, st, _ = cv2.connectedComponentsWithStats((a8 > 80).astype(np.uint8), 8)
    for j in range(1, ns):
        if st[j, cv2.CC_STAT_AREA] < 110: a8[lab == j] = 0
    return a8, sample.tolist()
def bbox(a8):
    """Robust content box: ignore rows/columns with only a few stray matte pixels (edge specks, leftover border dots)."""
    m = cv2.morphologyEx((a8 > 128).astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)); H, W = m.shape  # opening drops hairline strokes/borders
    m = m > 0
    rows = np.where(m.sum(1) >= max(3, int(W * .006)))[0]; cols = np.where(m.sum(0) >= max(3, int(H * .006)))[0]
    return [max(0, int(cols.min()) - 10), max(0, int(rows.min()) - 10), min(W, int(cols.max()) + 11), min(H, int(rows.max()) + 11)] if len(rows) and len(cols) else [0, 0, W, H]
def darkset():
    """Dark panels from the beat plans (D: prefix)."""
    d = set(); sheet = None
    for ln in open(os.path.join(ROOT, 'plans', 'landscape_beats.txt')):
        ln = ln.rstrip('\n')
        if ln.startswith('== '): sheet = ln[3:6]; i = 0; continue
        if not ln or ln.startswith('#'): continue
        i += 1
        if ln.startswith('D:'): d.add(f'{sheet}-{i}')
    sh = None; cnt = {}
    for ln in open(os.path.join(ROOT, 'plans', 'shorts_beats.txt')):
        ln = ln.rstrip('\n')
        if ln.startswith('== '): sh = ln[3:6]; continue
        if not ln or ln.startswith('#'): continue
        s, code = ln.split('|')[:2]; k = f'{sh}{s}'; cnt[k] = cnt.get(k, 0) + 1
        if code.startswith('D:'): d.add(f'{k}-{cnt[k]}')
    return d
def main(only=None):
    os.makedirs(os.path.join(WORK, 'flow'), exist_ok=True)
    zp = os.path.join(WORK, 'flow.zip')
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as z:
            for n in z.namelist():
                if n.lower().endswith(('.jpg', '.jpeg', '.png')): open(os.path.join(WORK, 'flow', os.path.basename(n)), 'wb').write(z.read(n))
    for d in ('layers', 'native', 'qa_grid'): os.makedirs(os.path.join(WORK, d), exist_ok=True)
    dark = darkset(); report = {}
    jobs = [(k, v, 3, 3, 2.0) for k, v in MAP['landscape'].items()] + [(f'{sh}{s}', v, 2, 2, 3.0) for sh, d in MAP['shorts'].items() for s, v in d.items()]
    for key, fk, rows, cols, keep in jobs:
        if only and key not in only: continue
        img = load(fk); cells, xs, ys = grid(img, rows, cols, 40)
        qa_overlay(img, cells, os.path.join(WORK, 'qa_grid', f'{key}.jpg'))
        for p, (x0, y0, x1, y1) in enumerate(cells, 1):
            name = f'{key}-{p}'; a = trim_cell(img[y0:y1, x0:x1]); cv2.imwrite(os.path.join(WORK, 'native', name + '.png'), a)
            b, method = upscale(a); a8, bg = matte(b, name in dark)
            s = keep / 4.0; size = (round(b.shape[1] * s), round(b.shape[0] * s))
            lay = np.dstack([cv2.resize(b, size, interpolation=cv2.INTER_AREA), cv2.resize(a8, size, interpolation=cv2.INTER_AREA)])
            atomic_write_png(os.path.join(WORK, 'layers', name + '.png'), lay)
            report[name] = {'source': FLOW[fk], 'cell': [x0, y0, x1, y1], 'native': list(a.shape[:2][::-1]), 'upscaled': list(b.shape[:2][::-1]), 'layer': list(lay.shape[:2][::-1]),
                            'scale_vs_native': keep, 'method': method, 'bbox': bbox(lay[:, :, 3]), 'dark': name in dark, 'paper_bgr': bg}
        print(key, 'gutters x', xs, 'y', ys, flush=True)
    atomic_json(os.path.join(WORK, 'upscale_report.json'), report)
if __name__ == '__main__': main(set(sys.argv[1:]) or None)
