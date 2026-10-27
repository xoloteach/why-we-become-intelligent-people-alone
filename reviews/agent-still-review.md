# Agent still review — first technical build

Build: run 40492903025 @ 8569a431502d021e0a89f47b4a51d45058f8326d.

Inspected: all 234 landscape scene-end frames, all 35 Shorts scene-end frames, 138 encoded final effect-state frames (six per 23 effects), thumbnail at full size and 160×90, and 16 isolated composite style sheets covering paper/obsidian and front/three-quarter views.

This is a **still review only**, not motion or audio playback approval.

## Defects found and source corrections

- L-S17-2: second envelope clipped to bake edge. Per-job camera height 0.9 for all two-envelope jobs, extra two-envelope style sample and every-frame boundary check.
- SH2-SH2B-1: disconnected dark floor block below windows. Reviewed P07 source crop + subject mask.
- SH2-SH2B-2: disconnected wall block above desk subjects. Reviewed P07 source crop + subject mask.
- S05-7: `Overwhelming` clipped inside comparison card; S19-9 `Independence` also clipped. Shared word-width fitting before rasterization, full-plan still typography test; regression font is 38 px for `Overwhelming`.
- SH2-SH2A-3 and SH2-SH2A-4: bright blank lower paper strips in otherwise dark cells. Reviewed P04 source crops exclude the blank strips while retaining the subject art.

Corrected source: c1a5d6bd31b37dcd991b1098d1b722646f023aff; replacement run 40497873055.

## Required final checks

1. Recheck all corrected final layouts and effect states against the replacement encoded output, not only local isolated tests.
2. Watch the finished videos and each effect clip with sound using a supported reviewer. Weight, smoothness, subtitle timing, narration dominance and contact/SFX sync require actual playback.
3. Only then record exact-run review PASS in `reviews/<run>.json`; current status is **NOT CHECKED**, not PASS.
