# Why We Become — "Why Intelligent People Enjoy Being Alone"

Automated production repo: 1 landscape episode (1920×1080) + 3 native Shorts (1080×1920).

* **Narration** — the user's Google AI Studio take, locked (script and audio never edited; vocal chain recorded in `inputs/manifest.json`). Stored as verified base85 chunks on `inputs-*` branches.
* **Art** — the user's Google Flow images (hash-verified), panel extraction + FSRCNN ×4 (`src/extract.py`).
* **3D objects** — Three.js r186 visuals + Rapier 0.21 physics, baked headless in CI (`fx/`), composited by `src/scene.py`. Style tests: `fx/tests/style_tests.json`.
* **Renders run only on GitHub Actions** (`.github/workflows/render.yml`): prep → fx bakes (≤3 workers) + style tests → audio → 6 landscape segments + 3 Shorts → assemble → QA gates (`src/qa.py`) → versioned release.
* Trigger: edit `render/trigger.json` (or run the workflow manually). Diagnostics and library previews: `ci-logs` branch.
