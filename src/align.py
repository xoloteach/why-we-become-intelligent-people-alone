"""Word-level alignment of the locked script to the narration.
Source of word times: Deepgram nova-3 on the processed narration when DEEPGRAM_API_KEY is set (runner),
otherwise the provisional faster-whisper estimates in voiceover.json. Script tokens are aligned to ASR words
with difflib on normalised tokens; unmatched script tokens are interpolated inside their matched neighbours.
The script text is never changed: captions show the script tokens, only their times come from ASR."""
import os, sys, re, json, difflib, subprocess, urllib.request
sys.path.insert(0, os.path.dirname(__file__)); from common import ROOT, WORK, atomic_json
NUM = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '20': 'twenty', '30': 'thirty', '100': 'hundred'}
def norm(w):
    w = w.lower().replace('’', "'").replace('‘', "'")
    w = re.sub(r"[^a-z0-9']", '', w).strip("'")
    return NUM.get(w, w)
def script_lines():
    out = []
    for ln in open(os.path.join(ROOT, 'transcript_timed.txt'), encoding='utf-8'):
        m = re.match(r'\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)', ln.rstrip('\n'))
        if m: out.append(m.group(3))
    return out
def deepgram(audio):
    key = os.environ.get('DEEPGRAM_API_KEY')
    if not key: return None
    data = open(audio, 'rb').read(); ctype = 'audio/flac' if audio.endswith('.flac') else 'audio/wav'
    url = 'https://api.deepgram.com/v1/listen?model=nova-3&language=en&punctuate=true&smart_format=false&numerals=false'
    req = urllib.request.Request(url, data=data, headers={'Authorization': f'Token {key}', 'Content-Type': ctype})
    with urllib.request.urlopen(req, timeout=600) as r: res = json.load(r)
    ws = res['results']['channels'][0]['alternatives'][0]['words']
    return [{'w': x.get('punctuated_word', x['word']), 'start': float(x['start']), 'end': float(x['end']), 'conf': float(x.get('confidence', 1))} for x in ws], 'deepgram-nova-3'
def main(audio):
    src = None
    try: src = deepgram(audio)
    except Exception as e: print('WARN deepgram failed, using provisional words:', repr(e)[:300])
    if src is None:
        v = json.load(open(os.path.join(ROOT, 'voiceover.json'))); src = (v['words'], 'faster-whisper-small.en (provisional)')
    words, engine = src
    lines = script_lines(); toks = []
    for li, ln in enumerate(lines):
        for w in ln.split(): toks.append({'w': w, 'line': li})
    a = [norm(t['w']) for t in toks]; b = [norm(w['w']) for w in words]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False); matched = 0
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            t = toks[blk.a + k]; w = words[blk.b + k]; t['start'], t['end'], t['matched'] = w['start'], w['end'], True; matched += 1
    # replace-opcodes of equal length: take times positionally (e.g. "20" vs "twenty", "self-knowledge" splits)
    for op, i0, i1, j0, j1 in sm.get_opcodes():
        if op == 'replace' and i1 > i0 and j1 > j0:
            span0, span1 = words[j0]['start'], words[j1 - 1]['end']; L = sum(len(toks[i]['w']) + 1 for i in range(i0, i1)); acc = 0
            for i in range(i0, i1):
                c = len(toks[i]['w']) + 1; toks[i]['start'] = span0 + (span1 - span0) * acc / L; toks[i]['end'] = span0 + (span1 - span0) * (acc + c) / L; toks[i]['matched'] = 'span'; acc += c
    # interpolate remaining gaps between timed neighbours
    n = len(toks); i = 0
    while i < n:
        if 'start' in toks[i]: i += 1; continue
        j = i
        while j < n and 'start' not in toks[j]: j += 1
        t0 = toks[i - 1]['end'] if i else 0.0; t1 = toks[j]['start'] if j < n else words[-1]['end']
        L = sum(len(toks[k]['w']) + 1 for k in range(i, j)); acc = 0
        for k in range(i, j):
            c = len(toks[k]['w']) + 1; toks[k]['start'] = t0 + (t1 - t0) * acc / L; toks[k]['end'] = t0 + (t1 - t0) * (acc + c) / L; toks[k]['matched'] = False; acc += c
        i = j
    for k in range(1, n):  # monotonic, minimum 40 ms
        toks[k]['start'] = max(toks[k]['start'], toks[k - 1]['start'] + 0.04)
        if toks[k - 1]['end'] > toks[k]['start']: toks[k - 1]['end'] = toks[k]['start']
    for t in toks: t['end'] = max(t['end'], t['start'] + 0.04); t['start'] = round(t['start'], 3); t['end'] = round(t['end'], 3)
    L = [{'i': li, 'text': ln, 'start': None, 'end': None} for li, ln in enumerate(lines)]
    for t in toks:
        d = L[t['line']]; d['start'] = t['start'] if d['start'] is None else d['start']; d['end'] = t['end']
    exact = sum(1 for t in toks if t['matched'] is True)
    rep = {'schema': 'wwb-align/1', 'engine': engine, 'script_tokens': n, 'asr_words': len(words), 'matched_exact': exact, 'matched_span': sum(1 for t in toks if t['matched'] == 'span'),
           'interpolated': sum(1 for t in toks if t['matched'] is False), 'match_ratio': round(exact / n, 4), 'tokens': toks, 'lines': L}
    os.makedirs(WORK, exist_ok=True); atomic_json(os.path.join(WORK, 'align.json'), rep)
    print('align', engine, 'tokens', n, 'exact', exact, 'ratio', rep['match_ratio'], 'interp', rep['interpolated'])
    return rep
if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'narration.flac'))
