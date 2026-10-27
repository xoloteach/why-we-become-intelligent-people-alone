"""Music + SFX mix under the locked narration (narration samples are never altered, only summed with the bed).
Pad: synthesized Am-F-C-G; ducking from a 100 Hz voice envelope (-23 dB under speech, -17 dB in pauses, rel. voice RMS).
SFX (ffmpeg-synthesized, fallback set while a Tone.js stem is not verified): whoosh on chapter starts and paper wipes,
soft ticks on list/chip reveals and deliberate 3D onsets, thuds on 3D physics contacts (exact baked contact frames), buzz on phone.
Two-pass loudnorm to -16 LUFS; the report records measured integrated loudness and every SFX time."""
import os, sys, json, subprocess, wave, glob
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import WORK, FPS, atomic_json
SR = 44100
def ff(*a): subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', *a], check=True)
def readf32(path, ss=None, to=None):
    cmd = ['ffmpeg', '-loglevel', 'error'] + (['-ss', f'{ss:.3f}'] if ss is not None else []) + (['-to', f'{to:.3f}'] if to is not None else []) + ['-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-']
    return np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout, dtype=np.float32).copy()
def sfx_bank():
    d = os.path.join(WORK, 'sfx'); os.makedirs(d, exist_ok=True)
    ff('-f', 'lavfi', '-i', 'anoisesrc=d=0.9:c=pink:r=44100:a=0.9', '-af', 'highpass=f=300,lowpass=f=4800,afade=t=in:d=0.42,afade=t=out:st=0.42:d=0.48', f'{d}/whoosh.wav')
    ff('-f', 'lavfi', '-i', 'sine=f=1318:d=0.3:r=44100', '-af', 'afade=t=out:st=0.015:d=0.28,volume=0.8', f'{d}/tick.wav')
    ff('-f', 'lavfi', '-i', 'sine=f=150:d=0.5:r=44100', '-af', 'afade=t=in:d=0.004,afade=t=out:st=0.03:d=0.45,lowpass=f=900', f'{d}/thud.wav')
    ff('-f', 'lavfi', '-i', 'sine=f=196:d=0.45:r=44100', '-af', 'tremolo=f=22:d=0.9,afade=t=in:d=0.02,afade=t=out:st=0.3:d=0.15,volume=0.8', f'{d}/buzz.wav')
    return {k: readf32(f'{d}/{k}.wav') for k in ('whoosh', 'tick', 'thud', 'buzz')}
def pad(N, seed=0):
    t = np.arange(N, dtype=np.float32) / SR; out = np.zeros(N, np.float32)
    chords = [[220.00, 261.63, 329.63, 440.00], [174.61, 220.00, 261.63, 349.23], [261.63, 329.63, 392.00, 523.25], [196.00, 246.94, 293.66, 392.00]]
    SEG, XF = 8.0, 3.0
    for s in range(int(N / SR / SEG) + 2):
        ch = chords[(s + seed) % 4]; t0 = s * SEG - XF / 2; t1 = (s + 1) * SEG + XF / 2; i0, i1 = max(int(t0 * SR), 0), min(int(t1 * SR), N)
        if i1 <= i0: continue
        tt = t[i0:i1]; env = np.sin(np.minimum(np.clip((tt - t0) / XF, 0, 1), np.clip((t1 - tt) / XF, 0, 1)) * np.pi / 2) ** 2; sig = np.zeros_like(tt)
        for k, f in enumerate(ch):
            for det in (-0.6, 0.0, 0.7):
                ph = k * 1.7 + det; v = np.sin(2 * np.pi * (f + det) * tt + ph) + 0.25 * np.sin(4 * np.pi * (f + det) * tt + ph); sig += v * (0.5 + 0.5 * np.sin(2 * np.pi * (0.07 + 0.02 * k) * tt + k))
        sig += 1.2 * np.sin(2 * np.pi * ch[0] / 2 * tt); out[i0:i1] += sig * env
    out /= np.sqrt(np.mean(out ** 2)) + 1e-9; return out * (0.85 + 0.15 * np.sin(2 * np.pi * t / 4.0))
def duck_gain(vo, N, speech_rms, vo_end):
    hop = SR // 100; n = N // hop + 1; v = np.zeros(n * hop, np.float32); v[:len(vo)] = vo[:n * hop]
    env = np.sqrt((v.reshape(n, hop) ** 2).mean(1)); env = np.convolve(env, np.ones(25) / 25, mode='same')  # 100 Hz envelope, 250 ms window
    speaking = (env > speech_rms * 0.25).astype(np.float32); k = np.hanning(35); sm = np.convolve(speaking, k / k.sum(), mode='same')
    tc = np.arange(n) / 100.0; db = -23 + (1 - sm) * 6; ramp = np.clip((tc - vo_end) / 1.5, 0, 1); db = db * (1 - ramp) - 12 * ramp
    g = speech_rms * 10 ** (db / 20); return np.interp(np.arange(N) / SR, tc, g).astype(np.float32)
def fx_events(fx_dir, scene_start, eid, obj, P):
    """Return [(kind, abs_time, note)] from a baked effect's physics contacts / deliberate cues."""
    out = []; bj = os.path.join(fx_dir, eid, 'bake.json')
    if not os.path.exists(bj): return out
    B = json.load(open(bj)); ph = B.get('physics') or {}
    for body, fr in (ph.get('contacts') or {}).items():
        if body in ('beam',) or fr is None: continue
        out.append(('thud', scene_start + fr / FPS, f'{eid}:{body} contact f{fr}'))
    if obj in ('door', 'clock', 'globe', 'battery', 'window') or (obj == 'phone' and P.get('mode') == 'scroll'):
        for c in P.get('cues', []): out.append(('tick', scene_start + c, f'{eid}: deliberate onset'))
    if obj == 'phone' and P.get('mode') == 'drop':
        for c in P.get('cues', []): out.append(('buzz', scene_start + c, f'{eid}: notification buzz'))
    return out
def loudnorm(src, dst, I=-16.0):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', src, '-af', f'loudnorm=I={I}:LRA=11:TP=-1.5:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = f"loudnorm=I={I}:LRA=11:TP=-1.5:measured_I={js['input_i']}:measured_LRA={js['input_lra']}:measured_TP={js['input_tp']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true"
    ff('-i', src, '-af', af, '-ar', str(SR), '-ac', '2', dst); return measure(dst)
def measure(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = r[r.rindex('Summary:'):]; I = float(tail.split('I:')[1].split('LUFS')[0]); tp = float(tail.split('Peak:')[1].split('dBFS')[0]) if 'Peak:' in tail else None
    return {'integrated_lufs': I, 'true_peak_dbfs': tp}
def mix(vo, total, events, bank, path_raw, path_out, vo_end, seed):
    N = int(round(total * SR)); vo_full = np.zeros(N, np.float32); vo_full[:min(len(vo), N)] = vo[:N]
    sr = float(np.sqrt(np.mean(vo[np.abs(vo) > 1e-4] ** 2))); bed = pad(N, seed) * duck_gain(vo_full, N, sr, vo_end)
    t = np.arange(N) / SR; bed *= np.clip(t / 2.0, 0, 1) * np.clip((total - t) / 2.5, 0, 1)
    sfx = np.zeros(N, np.float32); G = {'whoosh': 0.30, 'tick': 0.22, 'thud': 0.55, 'buzz': 0.30}
    for kind, at, _ in events:
        sig = bank[kind]; i = int(max(0, at - (0.32 if kind == 'whoosh' else 0.0)) * SR); j = min(N, i + len(sig))
        if j > i: sfx[i:j] += sig[:j - i] * G[kind] * sr
    m = vo_full + bed + sfx; pk = float(np.max(np.abs(m)))
    if pk > 0.98: m *= 0.98 / pk  # uniform scale only (narration timbre untouched)
    with wave.open(path_raw, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(m, -1, 1) * 32767).astype(np.int16).tobytes())
    return loudnorm(path_raw, path_out)
def main(which='all'):
    P = json.load(open(os.path.join(WORK, 'plan.json'))); nar = os.path.join(WORK, 'narration.wav'); fx_dir = os.path.join(WORK, 'fx_out'); bank = sfx_bank(); rep = {}
    jobs = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(WORK, 'fx_jobs', '*.json'))}
    if which in ('all', 'landscape'):
        vo = readf32(nar); ev = []
        for c in P['chapters'][1:]: ev.append(('whoosh', c['start'], f"chapter {c['n']}"))
        sc = P['scenes']
        for i, s in enumerate(sc):
            if i and i % 4 == 0 and s['dark'] == sc[i - 1]['dark'] and not s['chapter_start']: ev.append(('whoosh', s['start'], f"paper wipe {s['key']}"))
            if s['kind'] in ('list', 'chips'):
                for lb in s['labels']:
                    if lb.get('t') is not None: ev.append(('tick', lb['t'] + 0.05, f"{s['key']} item"))
            if s.get('fx'): j = jobs[s['fx']]; ev += fx_events(fx_dir, s['start'], s['fx'], j['object'], j['params'])
        ev.append(('thud', P['vo_end'] + 0.1, 'end card'))
        ev.sort(key=lambda e: e[1]); r = mix(vo, P['total'], ev, bank, os.path.join(WORK, 'mix_raw.wav'), os.path.join(WORK, 'mix.wav'), P['vo_end'], 0)
        rep['landscape'] = {**r, 'total': P['total'], 'events': [{'kind': k, 't': round(t, 3), 'note': n} for k, t, n in ev]}
    if which in ('all', 'shorts'):
        for S in P['shorts']:
            vo = readf32(nar, S['t0'], S['t1']); fade = int(0.015 * SR); vo[:fade] *= np.linspace(0, 1, fade); vo[-fade:] *= np.linspace(1, 0, fade)  # ~15 ms cut fades
            ev = []
            for i, s in enumerate(S['scenes']):
                if i and i % 4 == 0 and s['dark'] == S['scenes'][i - 1]['dark']: ev.append(('whoosh', s['start'] - S['t0'], f"paper wipe {s['key']}"))
                if s['kind'] in ('list', 'chips'):
                    for lb in s['labels']:
                        if lb.get('t') is not None: ev.append(('tick', lb['t'] + 0.05 - S['t0'], f"{s['key']} item"))
                if s.get('fx'): j = jobs[s['fx']]; ev += [(k, t - S['t0'], n) for k, t, n in fx_events(fx_dir, s['start'], s['fx'], j['object'], j['params'])]
            ev.append(('thud', S['vo_dur'] + 0.1, 'end card')); ev.sort(key=lambda e: e[1])
            r = mix(vo, S['total'], ev, bank, os.path.join(WORK, f"mix_{S['id']}_raw.wav"), os.path.join(WORK, f"mix_{S['id']}.wav"), S['vo_dur'], 1 + int(S['id'][-1]))
            rep[S['id']] = {**r, 'total': S['total'], 'events': [{'kind': k, 't': round(t, 3), 'note': n} for k, t, n in ev]}
    atomic_json(os.path.join(WORK, f'audio_report_{which}.json'), rep); print({k: (v['integrated_lufs'], v['true_peak_dbfs'], len(v['events'])) for k, v in rep.items()})
if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else 'all')
