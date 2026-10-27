"""Thumbnail (1280x720) + Shorts covers (1080x1920) from the dedicated Flow art (plan/flow_map.json: thumb, covers)
with the recommended hook text from plans/bundle1_production.txt. Art is used as generated (no retouching).
Usage: thumbs.py OUT_DIR"""
import os, sys, json
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, WORK, INK, RUST, GOLD, WHITE, glyph, blit, text_w, font
MAP = json.load(open(os.path.join(ROOT, 'plan', 'flow_map.json'))); FLOW = json.load(open(os.path.join(ROOT, 'plan', 'flow_files.json')))
def art(key):
    a = cv2.imread(os.path.join(WORK, 'flow', FLOW[key])); g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32); H, W = g.shape
    if g[H // 4:3 * H // 4, W // 4:3 * W // 4].mean() < 100:  # dark art: trim the light frame/margin Flow sometimes adds
        rows = np.where(g.mean(1) < 150)[0]; cols = np.where(g.mean(0) < 150)[0]; m = 4
        a = a[rows.min() + m:rows.max() + 1 - m, cols.min() + m:cols.max() + 1 - m]
    return a
def cover_fit(a, W, H):
    s = max(W / a.shape[1], H / a.shape[0]); b = cv2.resize(a, (round(a.shape[1] * s), round(a.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    y0 = (b.shape[0] - H) // 2; x0 = (b.shape[1] - W) // 2; return b[y0:y0 + H, x0:x0 + W].copy()
def halo(im, col, r=10):
    """Soft backing behind hook text so it stays readable over strings/texture (same colour as the local paper)."""
    a = cv2.GaussianBlur(cv2.dilate(im[:, :, 3], np.ones((r, r), np.uint8)), (0, 0), r / 2)
    h = np.zeros_like(im); h[:, :, :3] = col; h[:, :, 3] = np.clip(a.astype(np.float32) * .85, 0, 255).astype(np.uint8); return h
def hook(f, words, x, y, size, cols, width, backing=None, center=False):
    """words: list of (text, colour) lines, Montserrat Black."""
    yy = y
    for t, c in zip(words, cols):
        sz = size
        while text_w(t, sz, 'Black') > width and sz > 40: sz -= 4
        g = glyph(t, sz, c, width + 40, 'Black'); gx = x - g.shape[1] / 2 if center else x
        if backing is not None: hb = halo(g, backing, 18); blit(f, hb, gx, yy); blit(f, hb, gx, yy)
        blit(f, g, gx, yy); yy += round(sz * 1.08)
    return yy
def thumbnail(out):
    f = cover_fit(art(MAP['thumb']), 1280, 720)  # L01: obsidian room, left 35% kept empty for hook text
    y = hook(f, ['NOT', 'EMPTY'], 64, 210, 168, [WHITE, GOLD], 430)
    cv2.line(f, (70, y + 14), (250, y + 14), RUST, 10, cv2.LINE_AA)
    cv2.imwrite(os.path.join(out, 'thumbnail.jpg'), f, [cv2.IMWRITE_JPEG_QUALITY, 92])
    small = cv2.resize(f, (160, 90), interpolation=cv2.INTER_AREA); cv2.imwrite(os.path.join(out, 'thumbnail_160x90_check.png'), small)
COVERS = {'SH1': ('SH1-A', ['ALONE', '≠ LONELY'], [INK, RUST], None),
          'SH2': ('SH2-A', ['PEACE', 'OR FEAR?'], [WHITE, GOLD], None),
          'SH3': ('SH3-A', ['WHOSE', 'DREAM?'], [INK, RUST], (238, 244, 247))}
def covers(out):
    for sid, (ck, words, cols, back) in COVERS.items():
        a = art(MAP['covers'][ck]); f = cover_fit(a, 1080, 1920)
        y0 = 330 if sid == 'SH3' else 250  # upper third below the platform UI; SH3 sits between the puppeteer hands and the head
        hook(f, words, 540, y0, 150, cols, 900, back, center=True)
        cv2.imwrite(os.path.join(out, f'cover_{sid}.jpg'), f, [cv2.IMWRITE_JPEG_QUALITY, 92])
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); thumbnail(out); covers(out); print('thumbs ok', sorted(os.listdir(out)))
