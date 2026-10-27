# QA report — Why Intelligent People Enjoy Being Alone

Run 40500406007 @ ff79eed1fe0d16210d47c0a85b16028f9a08d821: **PASS** ({'PASS': 47, 'FAIL': 0, 'NOT CHECKED': 0})

| Gate | Status | Detail |
|---|---|---|
| final.mp4 geometry | PASS | h264 1920x1080 30.000fps yuv420p |
| final.mp4 duration | PASS | 1231.515s vs plan 1231.515s |
| final.mp4 audio stream | PASS | aac 44100 2ch |
| final.mp4 loudness | PASS | -16.0 LUFS integrated, true peak -4.2 dBFS (target -16, -17.5..-14.5, TP<=-1) |
| final.mp4 faststart | PASS | moov atom at file start |
| SH1.mp4 geometry | PASS | h264 1080x1920 30.000fps yuv420p |
| SH1.mp4 duration | PASS | 49.880s vs plan 49.880s |
| SH1.mp4 audio stream | PASS | aac 44100 2ch |
| SH1.mp4 loudness | PASS | -16.0 LUFS integrated, true peak -4.3 dBFS (target -16, -17.5..-14.5, TP<=-1) |
| SH1.mp4 faststart | PASS | moov atom at file start |
| SH2.mp4 geometry | PASS | h264 1080x1920 30.000fps yuv420p |
| SH2.mp4 duration | PASS | 43.910s vs plan 43.910s |
| SH2.mp4 audio stream | PASS | aac 44100 2ch |
| SH2.mp4 loudness | PASS | -16.1 LUFS integrated, true peak -4.4 dBFS (target -16, -17.5..-14.5, TP<=-1) |
| SH2.mp4 faststart | PASS | moov atom at file start |
| SH3.mp4 geometry | PASS | h264 1080x1920 30.000fps yuv420p |
| SH3.mp4 duration | PASS | 43.470s vs plan 43.470s |
| SH3.mp4 audio stream | PASS | aac 44100 2ch |
| SH3.mp4 loudness | PASS | -16.2 LUFS integrated, true peak -4.4 dBFS (target -16, -17.5..-14.5, TP<=-1) |
| SH3.mp4 faststart | PASS | moov atom at file start |
| narration PCM hash | PASS | bc51fe9a8064c669… vs manifest bc51fe9a8064c669… (user Google AI Studio take, processed chain; script/audio unchanged) |
| narration duration | PASS | vo_end 1226.515s |
| captions landscape | PASS | 3332 events, 686 groups, max 7 words, last end 1226.41s ≤ 1231.52s |
| captions SH1 | PASS | 127 events, 33 groups, max 5 words, last end 47.38s ≤ 49.88s |
| captions SH2 | PASS | 102 events, 29 groups, max 5 words, last end 41.41s ≤ 43.91s |
| captions SH3 | PASS | 125 events, 31 groups, max 5 words, last end 40.97s ≤ 43.47s |
| word alignment | PASS | faster-whisper-small.en (provisional): 3331/3332 exact (99.97%), 0 interpolated |
| 3D bakes complete + hashed | PASS | 23 effects, objects ['battery', 'books', 'briefcase', 'clock', 'door', 'envelope', 'globe', 'phone', 'scale', 'stairs', 'window']; all frame counts and sha256 manifests match |
| 3D toolchain versions | PASS | {"chromium": "156.0.8078.4", "node": "v24.21.0", "playwright": "1.64.1", "rapier": "0.21.0", "three": "0.186.1"} |
| physics cue error ≤ ±1 frame | PASS | all contact targets hit on cue |
| 3D scene spread (§3G/§4I) | PASS | landscape 17 (thirds [7, 6, 4], max run 2); shorts {'SH1': 2, 'SH2': 2, 'SH3': 2} |
| 3D alpha clear of caption band | PASS | 2354 sampled fx frames across 18 renders, 0 with alpha inside the caption band |
| SFX thud ±1 frame of contact | PASS | 27 contacts, worst offset 0.3 ms (Python/ffmpeg SFX set; Tone.js stem not built) |
| mix loudness reports | PASS | landscape -16.0, SH1 -16.0, SH2 -16.1, SH3 -16.1 |
| deterministic sample re-bake | PASS | L-S01-6: 114 final frame hashes compared |
| Typography width + headline regression | PASS | 269 scene layouts; Overwhelming fitted at 38px; failures [] |
| SH1 first frame carries hook | PASS | headline ink coverage 12.6% in frame 0 ("Alone Is Not Lonely") |
| SH1 length | PASS | 49.88s incl. end card 2.5s |
| SH2 first frame carries hook | PASS | headline ink coverage 9.0% in frame 0 ("Peace or Fear?") |
| SH2 length | PASS | 43.91s incl. end card 2.5s |
| SH3 first frame carries hook | PASS | headline ink coverage 12.6% in frame 0 ("Whose Life Is This?") |
| SH3 length | PASS | 43.47s incl. end card 2.5s |
| YouTube chapters | PASS | 15 chapters from processed-narration alignment, first 00:00, min gap 25s |
| bake workers ≤ 3 | PASS | workers [3, 3] |
| perf recorded | PASS | assemble: 53.6s, AMD EPYC 9V74 80-Core Processor, 15.6 GB, maxrss 53.5 MB; audio: 68.7s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 2330.3 MB; fx: 92.9s, INTEL(R) XEON(R) PLATINUM 8573C, 15.6 GB, maxrss 607.6 MB; prep: 229.8s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 634.5 MB; render-0: 87.5s, AMD EPYC 9V45 96-Core Processor, 15.6 GB, maxrss 352.5 MB; render-1: 148.6s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 356.9 MB; render-2: 126.0s, AMD EPYC 9V74 80-Core Processor, 15.6 GB, maxrss 367.7 MB; render-3: 126.9s, AMD EPYC 9V74 80-Core Processor, 15.6 GB, maxrss 368.9 MB; render-4: 82.2s, AMD EPYC 9V45 96-Core Processor, 15.6 GB, maxrss 368.8 MB; render-5: 76.8s, AMD EPYC 9V45 96-Core Processor, 15.6 GB, maxrss 484.6 MB; short-SH1: 28.0s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 422.9 MB; short-SH2: 27.3s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 398.2 MB; short-SH3: 24.6s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 423.8 MB; style: 105.7s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 521.6 MB |
| credential scan | PASS | no key patterns or secret values in repo or release files |
| QA stills from final renders | PASS | 30 stills extracted from the released files |
