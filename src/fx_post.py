"""Post-process baked effect frames: premultiplied 2x->1x area downsample, atomic writes, manifest hashes.
Also builds style-test previews on warm paper and obsidian."""
import os, sys, json, glob, hashlib
import cv2, numpy as np
PAPER = (238, 244, 247); OBS = (15, 21, 22)  # BGR of #F7F4EE / #16150F
def load_rgba_1x(path, ss=2):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32)
    al = a[:, :, 3:4] / 255.0; pm = a[:, :, :3] * al
    h, w = a.shape[:2]; size = (w // ss, h // ss)
    pm = cv2.resize(pm, size, interpolation=cv2.INTER_AREA); al = cv2.resize(al, size, interpolation=cv2.INTER_AREA)[:, :, None]
    rgb = np.where(al > 1e-4, pm / np.maximum(al, 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8)
def over(bg, rgba, x=0, y=0):
    h, w = rgba.shape[:2]; a = rgba[:, :, 3:4].astype(np.float32) / 255
    roi = bg[y:y + h, x:x + w]; roi[:] = (roi * (1 - a) + rgba[:, :, :3] * a).astype(np.uint8); return bg
def shadow(bg, s, ox=0, oy=0):
    if not s or s['op'] <= 0.002: return
    lay = np.zeros(bg.shape[:2], np.float32); w = max(4, s['w'] * (1 - min(.5, s['lift'])) * .92)
    cv2.ellipse(lay, (int(ox + s['x']), int(oy + s['y'])), (int(w), max(3, int(w * .16))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 3.5) * s['op']; bg[:] = (bg * (1 - lay[:, :, None]) + np.array(OBS) * lay[:, :, None]).astype(np.uint8)
def post(effect_dir):
    m = json.load(open(os.path.join(effect_dir, 'bake.json'))); ss = m['supersample']; hashes = []; alpha_peak = 0
    for k in range(m['frames']):
        src = os.path.join(effect_dir, 'raw', f'f{k:04d}.png'); dst = os.path.join(effect_dir, f'f{k:04d}.png')
        im = load_rgba_1x(src, ss); alpha_peak = max(alpha_peak, int(im[:, :, 3].max()))
        ok, buf = cv2.imencode('.png', im); open(dst + '.tmp', 'wb').write(buf.tobytes()); os.replace(dst + '.tmp', dst); hashes.append(hashlib.sha256(buf.tobytes()).hexdigest())
    m['final_sha256'] = hashes; m['final_size'] = list(im.shape[:2][::-1]); m['alpha_peak'] = alpha_peak
    json.dump(m, open(os.path.join(effect_dir, 'bake.json'), 'w'), indent=1); return m
def strip(effect_dir, frames, out, dark=False):
    m = json.load(open(os.path.join(effect_dir, 'bake.json'))); tiles = []
    for k in frames:
        k = min(k, m['frames'] - 1); im = cv2.imread(os.path.join(effect_dir, f'f{k:04d}.png'), cv2.IMREAD_UNCHANGED)
        bg = np.full((im.shape[0], im.shape[1], 3), OBS if dark else PAPER, np.uint8)
        for s in m['shadows'][k]: shadow(bg, s)
        over(bg, im); cv2.putText(bg, f'f{k}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, (60, 98, 200), 2); tiles.append(bg)
    cv2.imwrite(out, np.hstack(tiles))
if __name__ == '__main__':
    for d in sys.argv[1:]: post(d)
