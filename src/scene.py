"""Shared 2D scene engine (landscape + portrait): hero cutouts with ink-then-fill reveal and parallax planes,
diagram kinds (quote, list, chips, vs, strike, arrow, big, question) and the baked 3D-object compositor."""
import os, json, math, functools
import cv2, numpy as np
from common import (WORK, FPS, PAPER, INK, RUST, GOLD, WHITE, MUTED, SOFT, ease, spring, clamp, glyph, text_w, blit, text, line, path, rect, contact_shadow)
REPORT = None
def report():
    global REPORT
    if REPORT is None: REPORT = json.load(open(os.path.join(WORK, 'upscale_report.json')))
    return REPORT
def premul_resize(a, size):
    al = a[:, :, 3:4].astype(np.float32) / 255; pm = a[:, :, :3].astype(np.float32) * al
    interp = cv2.INTER_AREA if size[0] < a.shape[1] else cv2.INTER_CUBIC
    pm = cv2.resize(pm, size, interpolation=interp); al = np.clip(cv2.resize(al, size, interpolation=interp), 0, 1)[:, :, None]
    rgb = np.where(al > 1e-3, pm / np.maximum(al, 1e-3), 0)
    return np.dstack([np.clip(rgb, 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8)
@functools.lru_cache(maxsize=10)
def hero(art, bw, bh):
    a = cv2.imread(os.path.join(WORK, 'layers', art + '.png'), cv2.IMREAD_UNCHANGED)
    x0, y0, x1, y1 = report()[art]['bbox']; x0, y0 = max(0, x0 - 8), max(0, y0 - 8); x1, y1 = min(a.shape[1], x1 + 8), min(a.shape[0], y1 + 8); a = a[y0:y1, x0:x1]
    h, w = a.shape[:2]; sc = min(bw / w, bh / h); a = premul_resize(a, (max(1, round(w * sc)), max(1, round(h * sc))))
    al = a[:, :, 3]; ns, lab, st, _ = cv2.connectedComponentsWithStats((al > 80).astype(np.uint8), 8)
    for j in range(1, ns):
        if st[j, cv2.CC_STAT_AREA] < 28: al[lab == j] = 0
    a[:, :, 3] = al; gray = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2GRAY); ink = a.copy(); ink[:, :, :3] = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    ink[:, :, 3] = (a[:, :, 3] * np.clip((220 - gray.astype(np.float32)) / 80, 0, 1)).astype(np.uint8)
    ah, aw = a.shape[:2]; yy, xx = np.mgrid[0:ah, 0:aw]; d = np.minimum(np.minimum(xx, aw - 1 - xx), np.minimum(yy, ah - 1 - yy)).astype(np.float32)
    a[:, :, 3] = (a[:, :, 3] * np.clip(d / 22.0, 0, 1)).astype(np.uint8); ink[:, :, 3] = (ink[:, :, 3] * np.clip(d / 22.0, 0, 1)).astype(np.uint8)  # feather panel-edge cuts
    colmax = a[:, :, 3].max(0); lo, hi = int(aw * .28), int(aw * .72); parts = [(0, aw)]
    empty = np.convolve((colmax < 6).astype(np.int32), np.ones(9, np.int32), mode='same') == 9  # >=9 fully empty columns
    cand = [c for c in range(lo, hi) if empty[c]]
    if cand: cut = cand[len(cand) // 2]; parts = [(0, cut), (cut, aw)]  # split only at a genuinely empty mask gap
    return a, ink, parts
def draw_hero(f, s, t, cx, cy, bw, bh, side, instant=False):
    a, ink, parts = hero(s['art'], bw, bh); ah, aw = a.shape[:2]; r = t - s['start']; D = max(0.5, s['end'] - s['start']); u = clamp(r / D)
    if instant: r = max(r, 1.2)
    x = cx - aw / 2; y = cy - ah / 2; ent = spring(r / .85); px = (1 - ent) * 46 * side; drift = (ease(u) - .5) * 14 * (1 if s['i'] % 2 == 0 else -1)
    reveal = ease(r / .72); fill = ease((r - .18) / .82)
    for j, (o0, o1) in enumerate(parts):
        dy = (1 - spring(max(0, r - j * .1) / .85)) * (24 if j == 0 else -26) + (ease(u) - .5) * (4 if j == 0 else -6); dx = px + drift * (.8 if j == 0 else 1.0)
        cap = min(o1, int(aw * reveal))
        if cap > o0:
            if fill < .999: blit(f, ink[:, o0:cap], x + o0 + dx, y + dy, 1 - fill)
            blit(f, a[:, o0:cap], x + o0 + dx, y + dy, fill)
    return (int(x), int(y), aw, ah)
# ---------------------------------------------------------------- diagrams
def _rev(s, t): return [spring((t - lb['t']) / .5) if lb.get('t') is not None else 0.0 for lb in s['labels']]
def _cur(s, t):
    c = -1
    for i, lb in enumerate(s['labels']):
        if lb.get('t') is not None and t >= lb['t']: c = i
    return c
def fit(txt, size, width, weight='ExtraBold', min_size=22, max_lines=2):
    while size > min_size:
        wide = max((text_w(w, size, weight) for w in txt.split()), default=0) > width
        g = glyph(txt, size, INK, width, weight) if not wide else None
        if not wide and g.shape[0] <= max_lines * round(size * 1.18) + 14: break
        size -= 2
    return size
def diagram(f, s, t, x, y, w=790, h=320):
    kind = s['kind']; L = s['labels']; n = len(L); dark = s['dark']; fg = WHITE if dark else INK; mu = MUTED[dark]; so = SOFT[dark]
    rev = _rev(s, t); cur = _cur(s, t); r = t - s['start']
    if n == 0: return
    if kind == 'quote':
        a0 = max(rev[0], 0); text(f, '\u201c', x - 6, y - 46, 170, RUST, 200, alpha=a0, weight='Black')
        sz = 54 if n == 1 else (46 if n == 2 else 38); yy = y + 30
        for i, lb in enumerate(L):
            a = rev[i]; z = fit(lb['text'], sz, w - 110, max_lines=2 if n < 3 else 1)
            if a > 0:
                hh, ww = text(f, lb['text'], x + 92 + (1 - a) * 24, yy, z, RUST if (i == cur and n > 1) else fg, w - 110, alpha=a)
                line(f, (x + 96, yy + hh + 2), (x + 96 + min(ww, w - 120), yy + hh + 2), GOLD, 3, ease((t - lb['t'] - .2) / .7)) if i == cur else None
            else: hh = round(z * 1.18) * (1 if n > 1 else 2) + 14
            yy += max(hh, round(z * 1.18) + 14) + 18
        cv2.line(f, (x + 62, y + 34), (x + 62, int(y + 34 + (min(yy, y + h) - y - 40) * ease(r / .6))), RUST, 4, cv2.LINE_AA)
    elif kind in ('list', 'strike'):
        gap = 12; rh = min(88, (h - (n - 1) * gap) / n); z = 38 if rh >= 72 else (33 if rh >= 58 else 28)
        for i, lb in enumerate(L):
            a = rev[i]
            if a <= 0: continue
            yy = y + i * (rh + gap); xx = x + (1 - a) * 50
            if kind == 'list':
                act = i == cur; rect(f, xx, yy, w - 8, rh, RUST if act else so, r=12, alpha=a); text(f, f'{i + 1:02d}', xx + 20, yy + rh / 2 - 17, 24, WHITE if act else mu, 70, alpha=a, weight='Black')
                text(f, lb['text'], xx + 86, yy + rh / 2 - z * .72, z, WHITE if act else fg, w - 110, alpha=a)
            else:
                keep = lb.get('keep'); rect(f, xx, yy, w - 8, rh, so, r=12, alpha=a)
                ty = yy + rh / 2 - z * .72; hh, ww = text(f, lb['text'], xx + 28, ty, z, RUST if keep else fg, w - 60, alpha=a)
                if keep: cv2.circle(f, (int(xx + w - 40), int(yy + rh / 2)), 11, RUST, -1, cv2.LINE_AA)
                else:
                    p = ease((t - lb['t'] - .45) / .35); ym = yy + rh / 2 + 2
                    # Mark sits just under the words (baseline + small gap), never through the letters.
                    uy = min(yy + rh - 7, ty + z * 1.04 + 4)
                    line(f, (xx + 20, uy + 2), (xx + 36 + ww, uy - 2), RUST, 5, p)
                    if p > .98: cv2.line(f, (int(xx + w - 50), int(ym - 12)), (int(xx + w - 26), int(ym + 12)), RUST, 5, cv2.LINE_AA); cv2.line(f, (int(xx + w - 26), int(ym - 12)), (int(xx + w - 50), int(ym + 12)), RUST, 5, cv2.LINE_AA)
    elif kind == 'chips':
        z = 40 if n <= 3 else 34; ph = round(z * 2.1); cx, cy = x, y + 10
        for i, lb in enumerate(L):
            tw = text_w(lb['text'], z) + 56
            if cx + tw > x + w and cx > x: cx = x; cy += ph + 18
            a = rev[i]
            if a > 0:
                act = i == cur; sc = .82 + .18 * a; ww, hh = tw * sc, ph * sc; ox, oy = cx + (tw - ww) / 2, cy + (ph - hh) / 2
                rect(f, ox, oy, ww, hh, RUST if act else so, r=int(hh / 2), alpha=min(1, a * 1.3)); text(f, lb['text'], cx + 28, cy + ph / 2 - z * .7, z, WHITE if act else fg, int(tw), alpha=a)
            cx += tw + 18
    elif kind == 'vs':
        cw = (w - 90) / 2; ch = min(h - 70 if n > 2 else h - 10, 230)
        for i in range(min(n, 2)):
            a = rev[i]; xx = x + i * (cw + 90)
            if a <= 0: continue
            act = i == cur; yy = y + 10 + (1 - a) * 30; rect(f, xx, yy, cw, ch, so, r=16, alpha=a)
            cv2.rectangle(f, (int(xx), int(yy + ch - 8)), (int(xx + cw * ease((t - L[i]['t']) / .6)), int(yy + ch)), RUST if act else mu, -1)
            z = fit(L[i]['text'], 46, int(cw - 40), max_lines=3); g = glyph(L[i]['text'], z, RUST if act else fg, int(cw - 40), 'ExtraBold', 'center')
            blit(f, g, xx + (cw - g.shape[1]) / 2, yy + (ch - g.shape[0]) / 2 - 4, a)
        pv = ease(r / .5); cx0, cy0 = int(x + cw + 45), int(y + 10 + ch / 2)
        if pv > 0: cv2.circle(f, (cx0, cy0), int(34 * pv), RUST, -1, cv2.LINE_AA); text(f, 'VS', cx0, cy0 - 17, 26, WHITE, 80, alpha=pv, weight='Black', center=True)
        if n > 2 and rev[2] > 0: text(f, L[2]['text'], x + w / 2, y + ch + 30, 40, RUST, w, alpha=rev[2], center=True); line(f, (x + w / 2 - 90, y + ch + 84), (x + w / 2 + 90, y + ch + 84), GOLD, 4, ease((t - L[2]['t'] - .2) / .6))
    elif kind == 'arrow':
        bw_ = (w - 120) / 2; bh_ = 170; yy = y + 40
        if rev[0] > 0:
            rect(f, x, yy, bw_, bh_, so, r=16, alpha=rev[0]); g = glyph(L[0]['text'], fit(L[0]['text'], 40, int(bw_ - 36), max_lines=3), mu if n > 1 and cur >= 1 else fg, int(bw_ - 36), 'ExtraBold', 'center'); blit(f, g, x + (bw_ - g.shape[1]) / 2, yy + (bh_ - g.shape[0]) / 2, rev[0])
        if n > 1:
            p = ease((t - L[1]['t'] + .35) / .5) if L[1].get('t') is not None else 0
            path(f, [(x + bw_ + 14, yy + bh_ / 2), (x + bw_ + 60, yy + bh_ / 2 - 26), (x + bw_ + 106, yy + bh_ / 2)], RUST, 6, p, True)
            if rev[1] > 0:
                x2 = x + bw_ + 120; rect(f, x2, yy, bw_, bh_, RUST, r=16, alpha=rev[1]); g = glyph(L[1]['text'], fit(L[1]['text'], 40, int(bw_ - 36), max_lines=3), WHITE, int(bw_ - 36), 'ExtraBold', 'center'); blit(f, g, x2 + (bw_ - g.shape[1]) / 2, yy + (bh_ - g.shape[0]) / 2, rev[1])
        for i in range(2, n):
            if rev[i] > 0: text(f, L[i]['text'], x, yy + bh_ + 30 + (i - 2) * 50, 30, RUST, w, alpha=rev[i])
    elif kind == 'big':
        z = 124
        while z > 56 and (text_w(L[0]['text'].upper(), z, 'Black') > w - 20): z -= 4
        a = rev[0]
        if a > 0:
            g = glyph(L[0]['text'].upper(), z, RUST, w, 'Black'); sc = .9 + .1 * a; gg = cv2.resize(g, (max(1, int(g.shape[1] * sc)), max(1, int(g.shape[0] * sc))), interpolation=cv2.INTER_AREA)
            blit(f, gg, x, y + 20 + (g.shape[0] - gg.shape[0]) / 2, a); line(f, (x + 4, y + 30 + g.shape[0]), (x + 4 + min(w - 20, text_w(L[0]['text'].upper(), z, 'Black')), y + 30 + g.shape[0]), GOLD, 6, ease((t - L[0]['t'] - .15) / .6))
            yy = y + 60 + g.shape[0]
            for i in range(1, n):
                if rev[i] > 0: text(f, L[i]['text'], x + (1 - rev[i]) * 20, yy, 42, fg, w, alpha=rev[i]); yy += 64
    elif kind == 'question':
        pv = rev[0]; cx0, cy0 = x + 78, y + 100
        if pv > 0:
            cv2.circle(f, (int(cx0), int(cy0)), int(74 * (.7 + .3 * pv)), RUST, -1, cv2.LINE_AA); text(f, '?', cx0, cy0 - 64, 110, WHITE, 140, alpha=pv, weight='Black', center=True)
            for i, lb in enumerate(L):
                if rev[i] > 0: text(f, lb['text'], x + 190 + (1 - rev[i]) * 24, y + 46 + i * 84, fit(lb['text'], 48, w - 200, max_lines=2), fg if i else (RUST if dark else INK), w - 200, alpha=rev[i])
def fx_labels(f, s, t, x, y, w):
    dark = s['dark']; fg = WHITE if dark else INK; rev = _rev(s, t); cur = _cur(s, t); yy = y
    for i, lb in enumerate(s['labels']):
        a = rev[i]; z = fit(lb['text'], 38, w - 40, max_lines=2)
        if a > 0:
            cv2.circle(f, (int(x + 10), int(yy + z * .62)), int(9 * a), RUST if i == cur else MUTED[dark], -1, cv2.LINE_AA)
            hh, _ = text(f, lb['text'], x + 32 + (1 - a) * 20, yy, z, RUST if i == cur else fg, w - 40, alpha=a)
        else: hh = glyph(lb['text'], z, fg, w - 40).shape[0]
        yy += hh + 16
# ---------------------------------------------------------------- 3D compositor
@functools.lru_cache(maxsize=4)
def fx_meta(eid): return json.load(open(os.path.join(WORK, 'fx_out', eid, 'bake.json')))
_fx_cache = {}
def fx_frame(eid, k):
    key = (eid, k)
    if key not in _fx_cache:
        if len(_fx_cache) > 24: _fx_cache.clear()
        _fx_cache[key] = cv2.imread(os.path.join(WORK, 'fx_out', eid, f'f{k:04d}.png'), cv2.IMREAD_UNCHANGED)
    return _fx_cache[key]
FX_LOG = []
def draw_fx(f, s, t, ox, oy, band_y):
    m = fx_meta(s['fx']); k = min(m['frames'] - 1, max(0, int(round((t - s['start']) * FPS)))); im = fx_frame(s['fx'], k)
    for sh in m['shadows'][k]: contact_shadow(f, sh, ox, oy, s['dark'])
    blit(f, im, ox, oy); a = im[:, :, 3]; ys = np.where(a.max(1) > 0)[0]
    bottom = int(oy + ys.max()) if len(ys) else oy
    FX_LOG.append((s['fx'], k, bottom, bottom < band_y))
    return k
