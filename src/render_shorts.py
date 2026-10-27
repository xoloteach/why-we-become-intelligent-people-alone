"""Native 1080x1920 Shorts renderer (thin portrait layer over the shared scene engine).
Usage: render_shorts.py SH1 video OUT.mp4 | render_shorts.py SH1 stills OUT_DIR"""
import os, sys, json, bisect, time, subprocess
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import WORK, FPS, FONTS, INK, RUST, WHITE, ease, spring, glyph, blit, text, text_w, line, make_bg
import scene as SC
W, H = 1080, 1920; BAND_Y = 1345
P = json.load(open(os.path.join(WORK, 'plan.json'))); SH = {s['id']: s for s in P['shorts']}
BG = make_bg(W, H, seed=21)
for d in (False, True):
    cv2.line(BG[d], (85, 181), (995, 181), (40, 47, 52) if d else (228, 235, 240), 1, cv2.LINE_AA); cv2.line(BG[d], (85, 1672), (995, 1672), (40, 47, 52) if d else (228, 235, 240), 1, cv2.LINE_AA)
card = cv2.imread(os.path.join(WORK, 'assets', 'subscribe-end-card.jpeg')); CW = 935; CH_ = round(card.shape[0] * CW / card.shape[1]); CARD = cv2.resize(card, (CW, CH_), interpolation=cv2.INTER_AREA)
def headline(t, fg):
    sz = 86; im = glyph(t, sz, fg, 805, 'Black')
    while im.shape[0] > 244 and sz > 62: sz -= 2; im = glyph(t, sz, fg, 805, 'Black')
    return im
def make(sid):
    S = SH[sid]; sc = S['scenes']; t0 = S['t0']; starts = [s['start'] for s in sc]; TOT = S['total']; VOD = S['vo_dur']
    def header(f, fg):
        text(f, 'WHY WE BECOME', 85, 119, 26, fg, 470, weight='Black'); tw = text_w(S['topic'], 21); text(f, S['topic'], 995 - tw - 6, 124, 21, RUST, 600)
    def scene_frame(i, tg):
        s = sc[i]; dark = s['dark']; f = BG[dark].copy(); fg = WHITE if dark else INK; first = i == 0; r = tg - s['start']
        header(f, fg); im = headline(s['title'], fg); a = 1.0 if first else spring(r / .45); blit(f, im, 87, 225 + (1 - a) * 18, a)
        line(f, (87, 490), (237, 490), RUST, 5, 1.0 if first else ease((r - .12) / .55))
        SC.draw_hero(f, s, tg, 540, 742, 830, 435, 1 if i % 2 else -1, instant=first)
        if s.get('fx'): SC.draw_fx(f, s, tg, 87, 1020, BAND_Y); SC.fx_labels(f, s, tg, 527, 1050, 400)
        else: SC.diagram(f, s, tg, 87, 1030, 790, 320)
        line(f, (87, 1620), (993, 1620), (54, 61, 66) if dark else (216, 225, 232), 2); line(f, (87, 1620), (993, 1620), RUST, 3, (tg - t0) / TOT)
        return f
    def end_frame():
        f = BG[False].copy(); header(f, INK); f[(H - CH_) // 2 - 40:(H - CH_) // 2 - 40 + CH_, (W - CW) // 2:(W - CW) // 2 + CW] = CARD; return f
    END = end_frame()
    def frame(tl):
        tg = tl + t0
        if tl >= VOD:
            a = ease((tl - VOD) / .4); return END.copy() if a >= 1 else cv2.addWeighted(scene_frame(len(sc) - 1, t0 + VOD - .01), 1 - a, END, a, 0)
        i = max(0, bisect.bisect_right(starts, tg) - 1); f = scene_frame(i, tg); r = tg - sc[i]['start']
        if i and r < .18:
            prev = scene_frame(i - 1, sc[i]['start'] - .02); a = ease(r / .18)
            if i % 4 == 0 and sc[i]['dark'] == sc[i - 1]['dark']: b = int(H * a); f[b:] = prev[b:]; cv2.line(f, (0, b), (W, b), RUST, 3)
            else: f = cv2.addWeighted(prev, 1 - a, f, a, 0)
        return f
    return S, frame
def video(sid, out):
    S, frame = make(sid); N = int(round(S['total'] * FPS)); ass = os.path.join(WORK, f'captions_{sid}.ass'); mix = os.path.join(WORK, f'mix_{sid}.wav')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', mix,
           '-vf', f'ass={ass}:fontsdir={FONTS}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
           '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-t', f"{S['total']:.3f}", '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
    try:
        for n in range(N): p.stdin.write(frame(n / FPS).tobytes())
    finally: p.stdin.close()
    rc = p.wait(); json.dump({'frames': N, 'seconds': round(time.time() - t0, 1), 'fx': SC.FX_LOG[::3]}, open(os.path.splitext(out)[0] + '.fxlog.json', 'w')); print('DONE', out, rc, round(time.time() - t0, 1)); sys.exit(rc)
def stills(sid, out):
    S, frame = make(sid); os.makedirs(out, exist_ok=True); t0 = S['t0']
    cv2.imwrite(os.path.join(out, f'{sid}_000_first.jpg'), frame(0.0), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for i, s in enumerate(S['scenes']):
        ts = {'mid': min(s['end'] - .06, s['start'] + max(.7, (s['end'] - s['start']) * .66))}
        if s.get('fx'):
            m = SC.fx_meta(s['fx']); ph = m.get('physics') or {}; j = json.load(open(os.path.join(WORK, 'fx_jobs', s['fx'] + '.json'))); c0 = j['params']['cues'][0]
            ts['onset'] = s['start'] + max(0, c0 - .25); tg = sorted((ph.get('contacts') or {}).values())
            if tg: ts['contact'] = s['start'] + tg[-1] / FPS
            if ph.get('settle'): ts['settle'] = s['start'] + ph['settle'] / FPS
            ts['end'] = s['end'] - .05
        for nm, tt in ts.items():
            tt = min(max(tt, s['start']), s['end'] - 1 / FPS); cv2.imwrite(os.path.join(out, f"{sid}_{i + 1:03d}_{s['key']}_{nm}.jpg"), frame(tt - t0), [cv2.IMWRITE_JPEG_QUALITY, 88])
    cv2.imwrite(os.path.join(out, f'{sid}_999_end.jpg'), frame(S['total'] - .5), [cv2.IMWRITE_JPEG_QUALITY, 88])
if __name__ == '__main__':
    sid, mode, out = sys.argv[1], sys.argv[2], sys.argv[3]
    (video if mode == 'video' else stills)(sid, out)
