# QA report — Why Intelligent People Enjoy Being Alone

Run 40497873055 @ c1a5d6bd31b37dcd991b1098d1b722646f023aff: **FAIL** ({'PASS': 46, 'FAIL': 1, 'NOT CHECKED': 0})

| Gate | Status | Detail |
|---|---|---|
| final.mp4 geometry | PASS | h264 1920x1080 30.000fps yuv420p |
| final.mp4 duration | PASS | 1231.515s vs plan 1231.515s |
| final.mp4 audio stream | PASS | aac 44100 2ch |
| final.mp4 loudness | PASS | -16.0 LUFS integrated, true peak -2.2 dBFS (target -16, -17.5..-14.5, TP<=-1) |
| final.mp4 faststart | PASS | moov atom at file start |
| SH1.mp4 geometry | PASS | h264 1080x1920 30.000fps yuv420p |
| SH1.mp4 duration | PASS | 49.880s vs plan 49.880s |
| SH1.mp4 audio stream | PASS | aac 44100 2ch |
| SH1.mp4 loudness | PASS | -16.0 LUFS integrated, true peak -4.3 dBFS (target -16, -17.5..-14.5, TP<=-1) |
| SH1.mp4 faststart | PASS | moov atom at file start |
| SH2.mp4 geometry | PASS | h264 1080x1920 30.000fps yuv420p |
| SH2.mp4 duration | PASS | 43.910s vs plan 43.910s |
| SH2.mp4 audio stream | PASS | aac 44100 2ch |
| SH2.mp4 loudness | PASS | -16.1 LUFS integrated, true peak -4.2 dBFS (target -16, -17.5..-14.5, TP<=-1) |
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
| 3D bakes complete + hashed | FAIL | 23 effects, objects ['battery', 'books', 'briefcase', 'clock', 'door', 'envelope', 'globe', 'phone', 'scale', 'stairs', 'window']; L-S01-6: object alpha touches bake boundary in 16 frames; L-S06-4: object alpha touches bake boundary in 16 frames; L-S12-9: object alpha touches bake boundary in 18 frames; L-S26-4: object alpha touches bake boundary in 20 frames; SH1-SH1C-2: object alpha touches bake boundary in 10 frames; SH3-SH3A-1: object alpha touches bake boundary in 18 frames |
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
| perf recorded | PASS | assemble: 28.9s, AMD EPYC 9V45 96-Core Processor, 15.6 GB, maxrss 50.4 MB; audio: 56.7s, AMD EPYC 9V74 80-Core Processor, 15.6 GB, maxrss 2356.3 MB; fx: 115.4s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 523.4 MB; prep: 251.4s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 666.8 MB; render-0: 123.6s, INTEL(R) XEON(R) PLATINUM 8573C, 15.6 GB, maxrss 339.9 MB; render-1: 122.7s, AMD EPYC 9V74 80-Core Processor, 15.6 GB, maxrss 359.6 MB; render-2: 161.7s, Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz, 15.6 GB, maxrss 369.2 MB; render-3: 135.6s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 334.4 MB; render-4: 141.8s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 337.3 MB; render-5: 130.3s, AMD EPYC 9V74 80-Core Processor, 15.6 GB, maxrss 489.2 MB; short-SH1: 28.4s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 455.7 MB; short-SH2: 26.7s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 536.0 MB; short-SH3: 13.2s, AMD EPYC 9V45 96-Core Processor, 15.6 GB, maxrss 413.6 MB; style: 108.8s, AMD EPYC 7763 64-Core Processor, 15.6 GB, maxrss 442.6 MB |
| credential scan | PASS | no key patterns or secret values in repo or release files |
| QA stills from final renders | PASS | 30 stills extracted from the released files |
