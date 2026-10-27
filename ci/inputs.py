"""Reassemble the user's locked inputs from base85 chunks stored on inputs-* branches and verify every hash.
Usage: python3 ci/inputs.py WORK_DIR  (run inside the checkout after fetching origin/inputs-*)."""
import os, sys, json, base64, hashlib, subprocess, zipfile
W = sys.argv[1]; os.makedirs(W, exist_ok=True); M = json.load(open('inputs/manifest.json'))
sha = lambda b: hashlib.sha256(b).hexdigest()
for f in M['files']:
    buf = bytearray()
    for c in f['chunks']:
        enc = subprocess.run(['git', 'show', f"origin/{c['branch']}:inputs/chunks/{c['name']}"], check=True, capture_output=True).stdout
        raw = base64.b85decode(enc.strip())
        assert sha(raw) == c['sha256'], f"chunk {c['name']} hash mismatch"; buf += raw
    assert len(buf) == f['bytes'] and sha(bytes(buf)) == f['sha256'], f"{f['name']} hash mismatch"
    open(os.path.join(W, f['name']), 'wb').write(buf); print('ok', f['name'], f['bytes'], f['sha256'][:16])
nar = os.path.join(W, 'narration.wav')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(W, 'narration_processed.flac'), '-c:a', 'pcm_s16le', nar], check=True)
pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', nar, '-f', 's16le', '-'], check=True, capture_output=True).stdout
assert sha(pcm) == M['narration_pcm_s16le_sha256'], 'narration PCM hash mismatch'
print('ok narration PCM', len(pcm) // 2 / 44100, 's', M['narration_pcm_s16le_sha256'][:16])
os.makedirs(os.path.join(W, 'flow'), exist_ok=True)
with zipfile.ZipFile(os.path.join(W, 'flow_images.zip')) as z:
    for n in z.namelist():
        b = z.read(n); exp = M['flow_sha256'].get(os.path.basename(n))
        assert exp and sha(b) == exp, f'flow image {n} hash mismatch'; open(os.path.join(W, 'flow', os.path.basename(n)), 'wb').write(b)
print('ok flow images', len(M['flow_sha256']))
json.dump({k: M[k] for k in ('narration_pcm_s16le_sha256', 'narration_raw_wav_sha256', 'narration_processed_wav_sha256', 'processing_chain')}, open(os.path.join(W, 'inputs_manifest.json'), 'w'), indent=1)
