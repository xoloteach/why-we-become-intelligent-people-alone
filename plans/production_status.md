# Production status — Why Intelligent People Enjoy Being Alone

| Stage | Status | Evidence |
| --- | --- | --- |
| Narration received (Google AI Studio, Elio) | PASSED | 1289.4 s, 24 kHz mono PCM; sha256 in audio/raw.sha256 |
| 7-stage vocal chain | PASSED | processed 1226.515 s (silence trim −62.9 s); sha256 f1c137c0… |
| Transcript (= script) | PASSED | transcript.txt — faster-whisper small.en, 3,333 words, 39 low-confidence words reviewed (all sentence-initial function words) |
| Word alignment | PROVISIONAL | voiceover.json from local aligner; Deepgram nova-3 pass on runner pending DEEPGRAM_API_KEY repo secret |
| Art budget | PASSED | ceil((1226.5+4)/60×1.25) = 26 sheets × 9 = 234 panels |
| Prompt bundles | PASSED | plans/bundle1_production.txt, plans/bundle2_kit.txt |
| Flow artwork | BLOCKED | waiting for user-supplied images |
| Panel extraction / upscale / scene plan | PENDING | needs artwork |
| GitHub Actions render (16:9 + 3×9:16) | PENDING | needs artwork + push credential |
| QA gate + auto release | PENDING | |

Effects policy: only the verified Python/OpenCV/Pillow/FFmpeg renderer (release v2-motion-37044793527 / shorts-v1-37088064873) and its demonstrated engines, ink/watercolour reveals, damped entrances, paper wipes/crossfades, mask-gap parallax, FSRCNN 4× reconstruction, word captions, ducked music and Python SFX. All JS layers / 3D objects are Planned on the toolkit page and are excluded.
