"""Landscape 1920x1080 renderer. Usage:
  render.py stills OUT_DIR [keys...]   -> QA stills (mid-scene, 3D onset/contact/settle frames)
  render.py segment A B OUT.mp4        -> frames [A,B) encoded with burned captions (video only)"""
import os, sys, json, bisect, time, subprocess, math
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import WORK, FPS, FONTS, PAPER, INK, RUST, GOLD, WHITE, ease, spring, glyph, blit, text, line, make_bg
import scene as SC
W, H = 1920, 1080; BAND_Y = 900
P = json.load(open(os.path.join(WORK, 'plan.json'))); S = P['scenes']; CH = P['chapters']; VO = P['vo_end']; TOTAL = P['total']; starts = [s['start'] for s in S]
BG = make_bg(W, H)
for d in (False, True): cv2.line(BG[d], (90, 139), (1830, 139), (40, 47, 52) if d else (228, 235, 240), 1, cv2.LINE_AA)
END = cv2.resize(cv2.imread(os.path.join(WORK, 'assets', 'subscribe-end-card.jpeg')), (W, H), interpolation=cv2.INTER_LANCZOS4)
def title_glyph(s, fg):
    feat = s['layout'] == 'feature'; sz = 90 if feat else 82; mw = 1720 if feat else 805; im = glyph(s['title'], sz, fg, mw, 'Black')
    while im.shape[0] > 225 and sz > 54: sz -= 2; im = glyph(s['title'], sz, fg, mw, 'Black')
    return im
def scene_frame(i, t):
    s = S[i]; r = t - s['start']; dark = s['dark']; f = BG[dark].copy(); fg = WHITE if dark else INK; feat = s['layout'] == 'feature'
    tx = 100 if (feat or s['layout'] == 'right') else 1035
    text(f, 'WHY WE BECOME', 90, 62, 26, fg, 470, weight='Black'); text(f, f"{s['chapter']:02d} / {CH[s['chapter'] - 1]['name'].upper()}", 790, 65, 24, RUST, 1040)
    im = title_glyph(s, fg); a = spring(r / .55); blit(f, im, tx, 214 + (1 - a) * 22, a); line(f, (tx, 440), (tx + 150, 440), RUST, 5, ease((r - .18) / .7))
    if feat: SC.draw_hero(f, s, t, 340, 665, 490, 410, -1)
    else: SC.draw_hero(f, s, t, 1405 if s['layout'] == 'right' else 515, 548, 890, 610, 1 if s['layout'] == 'right' else -1)
    if s.get('fx'):
        ox = 660 if feat else tx; SC.draw_fx(f, s, t, ox, 470, BAND_Y); lw = 1810 - (ox + 470) if feat else 330; SC.fx_labels(f, s, t, ox + 470, 500, lw)
    else: SC.diagram(f, s, t, 660 if feat else tx, 502, 1150 if feat else 790, 320)
    line(f, (90, 1025), (1830, 1025), (54, 61, 66) if dark else (216, 225, 232), 2); line(f, (90, 1025), (1830, 1025), RUST, 3, t / TOTAL)
    return f
def frame(t):
    if t >= VO:
        a = ease((t - VO) / .65); f = cv2.addWeighted(scene_frame(len(S) - 1, VO - .01), 1 - a, END, a, 0) if a < 1 else END.copy(); return f
    i = max(0, bisect.bisect_right(starts, t) - 1); f = scene_frame(i, t); r = t - S[i]['start']
    if i and r < .24:
        prev = scene_frame(i - 1, S[i]['start'] - .02); a = ease(r / .24)
        if i % 4 == 0 and S[i]['dark'] == S[i - 1]['dark'] and not S[i]['chapter_start']:
            b = int(W * a); f[:, b:] = prev[:, b:]; cv2.line(f, (b, 0), (b, H), RUST, 3)
        else: f = cv2.addWeighted(prev, 1 - a, f, a, 0)
    return f
def stills(out, keys=None):
    os.makedirs(out, exist_ok=True); n = 0
    for i, s in enumerate(S):
        if keys and s['key'] not in keys: continue
        ts = {'mid': min(s['end'] - .06, s['start'] + max(.7, (s['end'] - s['start']) * .66))}
        if s.get('fx'):
            m = SC.fx_meta(s['fx']); ph = m.get('physics') or {}; j = json.load(open(os.path.join(WORK, 'fx_jobs', s['fx'] + '.json')))
            c0 = j['params']['cues'][0]; ts['onset'] = s['start'] + max(0, c0 - .25); tg = sorted((ph.get('contacts') or {}).values())
            if tg: ts['contact'] = s['start'] + tg[-1] / FPS
            ts['peak'] = s['start'] + c0 + j['params'].get('dur', 0.6) * .6
            if ph.get('settle'): ts['settle'] = s['start'] + ph['settle'] / FPS
            ts['end'] = s['end'] - .05
        for nm, tt in ts.items():
            tt = min(max(tt, s['start']), s['end'] - 1 / FPS); cv2.imwrite(os.path.join(out, f"{i:03d}_{s['key']}_{nm}.jpg"), frame(tt), [cv2.IMWRITE_JPEG_QUALITY, 88]); n += 1
    print('stills', n)
def segment(a, b, out):
    vf = f"setpts=PTS+{a / FPS:.6f}/TB,ass={os.path.join(WORK, 'captions.ass')}:fontsdir={FONTS},setpts=PTS-STARTPTS"
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-vf', vf,
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-threads', '2', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
    try:
        for n in range(a, b):
            p.stdin.write(frame(n / FPS).tobytes())
            if (n - a) % 900 == 0: print(f'{n - a}/{b - a} {time.time() - t0:.0f}s', flush=True)
    finally: p.stdin.close()
    rc = p.wait(); log = os.path.splitext(out)[0] + '.fxlog.json'
    json.dump({'frames': [a, b], 'seconds': round(time.time() - t0, 1), 'fx': SC.FX_LOG[::3]}, open(log, 'w')); print('DONE', out, rc, round(time.time() - t0, 1), flush=True); sys.exit(rc)
if __name__ == '__main__':
    if sys.argv[1] == 'stills': stills(sys.argv[2], set(sys.argv[3:]) or None)
    elif sys.argv[1] == 'segment': segment(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
