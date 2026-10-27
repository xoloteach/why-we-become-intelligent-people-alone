"""Shared drawing + motion primitives (derived from the verified v2 renderer, release v2-motion-37044793527)."""
import os, math, functools, json, hashlib
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
cv2.setNumThreads(1)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WORK = os.environ.get('WWB_WORK', os.path.join(ROOT, 'work'))
FONTS = os.environ.get('WWB_FONTS', '/data/fonts')
FPS = 30
# BGR palette
PAPER = (238, 244, 247); INK = (15, 21, 22); RUST = (60, 98, 200); GOLD = (58, 179, 232); WHITE = (244, 247, 250)
MUTED = {False: (114, 121, 127), True: (155, 164, 174)}; SOFT = {False: (221, 231, 239), True: (40, 49, 55)}
def ease(u): u = min(1, max(0, u)); return 1 - (1 - u) ** 3
def spring(u): u = max(0, min(1, u)); return (1 - (1 + 7 * u) * math.exp(-7 * u)) / (1 - 8 * math.exp(-7))
def clamp(u, a=0.0, b=1.0): return min(b, max(a, u))
def sha256_file(p, bs=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(bs), b''): h.update(b)
    return h.hexdigest()
def atomic_write_png(path, img):
    ok, buf = cv2.imencode('.png', img); assert ok
    with open(path + '.tmp', 'wb') as f: f.write(buf.tobytes())
    os.replace(path + '.tmp', path)
def atomic_json(path, obj):
    with open(path + '.tmp', 'w') as f: json.dump(obj, f, indent=1)
    os.replace(path + '.tmp', path)
@functools.lru_cache(maxsize=2000)
def font(size, weight='ExtraBold'): return ImageFont.truetype(os.path.join(FONTS, f'Montserrat-{weight}.ttf'), size)
TEXT_FIT_LOG = []
@functools.lru_cache(maxsize=1500)
def glyph(t, size=34, col=INK, width=800, weight='ExtraBold', align='left'):
    # Never truncate an unbreakable word to the image width. Shrink it first;
    # multi-line/cell sizing remains the caller's responsibility.
    requested_size = size
    longest = max((text_w(w, size, weight) for w in t.split()), default=0)
    while longest > width and size > 1:
        size -= 1
        longest = max((text_w(w, size, weight) for w in t.split()), default=0)
    if size != requested_size:
        TEXT_FIT_LOG.append({'text': t, 'requested': requested_size, 'actual': size, 'width': width})
    f = font(size, weight); d = ImageDraw.Draw(Image.new('RGBA', (1, 1))); ls = []
    for part in t.split('\n'):
        cur = ''
        for word in part.split():
            z = (cur + ' ' + word).strip()
            if d.textlength(z, font=f) > width and cur: ls.append(cur); cur = word
            else: cur = z
        if cur: ls.append(cur)
    if not ls: ls = [' ']
    ht = round(size * 1.18); ww = min(width, math.ceil(max(d.textlength(z, font=f) for z in ls))) + 10
    im = Image.new('RGBA', (ww, len(ls) * ht + 14)); d = ImageDraw.Draw(im)
    for i, z in enumerate(ls):
        x = 3 if align == 'left' else (ww - d.textlength(z, font=f)) / 2
        d.text((x, i * ht - size * .1), z, font=f, fill=col[::-1] + (255,))
    return np.ascontiguousarray(np.asarray(im)[:, :, [2, 1, 0, 3]])
def text_w(t, size, weight='ExtraBold'): return ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(t, font=font(size, weight))
def blit(f, im, x, y, alpha=1.0):
    if alpha <= 0.003: return
    H, W = f.shape[:2]; x, y = int(round(x)), int(round(y)); h, w = im.shape[:2]
    xa, ya = max(0, x), max(0, y); xb, yb = min(W, x + w), min(H, y + h)
    if xb <= xa or yb <= ya: return
    src = im[ya - y:yb - y, xa - x:xb - x]; a = src[:, :, 3:4].astype(np.float32) * (min(1.0, alpha) / 255)
    dst = f[ya:yb, xa:xb]; dst[:] = (dst * (1 - a) + src[:, :, :3] * a).astype(np.uint8)
def text(f, t, x, y, size=34, col=INK, width=800, alpha=1, weight='ExtraBold', center=False):
    a = glyph(t, size, col, width, weight, 'center' if center else 'left'); blit(f, a, x - a.shape[1] / 2 if center else x, y, alpha); return a.shape[0], a.shape[1]
def line(f, a, b, col=RUST, th=4, p=1):
    if p <= 0: return
    a = np.array(a, float); b = a + (np.array(b, float) - a) * min(1, p); cv2.line(f, tuple(a.astype(int)), tuple(b.astype(int)), col, th, cv2.LINE_AA)
def path(f, pts, col=RUST, th=5, p=1, arrow=False):
    if p <= 0: return
    pts = np.array(pts, float); lens = np.linalg.norm(np.diff(pts, axis=0), axis=1); left = lens.sum() * min(1, p); out = [pts[0]]
    for i, L in enumerate(lens):
        if left >= L: out.append(pts[i + 1]); left -= L
        else: out.append(pts[i] + (pts[i + 1] - pts[i]) * (left / max(L, .001))); break
    out = np.array(out); cv2.polylines(f, [out.astype(np.int32)], False, col, th, cv2.LINE_AA)
    if arrow and len(out) > 1 and p > .94:
        v = out[-1] - out[-2]; v = v / max(np.linalg.norm(v), .001); n = np.array([-v[1], v[0]]); tip = out[-1]
        cv2.fillConvexPoly(f, np.array([tip + v * 4, tip - v * 20 + n * 11, tip - v * 20 - n * 11], np.int32), col, cv2.LINE_AA)
def rect(f, x, y, w, h, col, r=13, alpha=1.0):
    if alpha <= 0.003 or w <= 2 or h <= 2: return
    x, y, w, h = map(int, (x, y, w, h)); r = min(r, w // 2, h // 2)
    tgt = f if alpha >= .999 else f.copy()
    cv2.rectangle(tgt, (x + r, y), (x + w - r, y + h), col, -1); cv2.rectangle(tgt, (x, y + r), (x + w, y + h - r), col, -1)
    for cx, cy in [(x + r, y + r), (x + w - r, y + r), (x + r, y + h - r), (x + w - r, y + h - r)]: cv2.circle(tgt, (cx, cy), r, col, -1, cv2.LINE_AA)
    if alpha < .999:
        y0, y1, x0, x1 = max(0, y - 2), min(f.shape[0], y + h + 2), max(0, x - 2), min(f.shape[1], x + w + 2)
        f[y0:y1, x0:x1] = cv2.addWeighted(f[y0:y1, x0:x1], 1 - alpha, tgt[y0:y1, x0:x1], alpha, 0)
def make_bg(W, H, seed=12):
    rng = np.random.default_rng(seed); grain = rng.normal(0, .55, (H, W, 1))
    return {False: np.clip(np.array(PAPER)[None, None, :] + grain, 0, 255).astype(np.uint8), True: np.clip(np.array(INK)[None, None, :] + grain * .45, 0, 255).astype(np.uint8)}
def over_rgba(f, rgba, x, y, alpha=1.0):
    """Composite a straight-alpha BGRA layer (fx frames)."""
    blit(f, rgba, x, y, alpha)
def contact_shadow(f, s, ox, oy, dark):
    if not s or s['op'] <= 0.002: return
    w = max(4, s['w'] * (1 - min(.5, s['lift'])) * .92); cx, cy = ox + s['x'], oy + s['y']
    x0, y0 = int(cx - w - 12), int(cy - w * .16 - 12); x1, y1 = int(cx + w + 12), int(cy + w * .16 + 12)
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(f.shape[1], x1), min(f.shape[0], y1)
    if x1 <= x0 or y1 <= y0: return
    lay = np.zeros((y1 - y0, x1 - x0), np.float32)
    cv2.ellipse(lay, (int(cx - x0), int(cy - y0)), (int(w), max(3, int(w * .16))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 3.5) * s['op'] * (0.55 if dark else 1.0)
    shade = np.array((0, 0, 0) if dark else INK, np.float32)
    roi = f[y0:y1, x0:x1]; roi[:] = (roi * (1 - lay[:, :, None]) + shade * lay[:, :, None]).astype(np.uint8)
