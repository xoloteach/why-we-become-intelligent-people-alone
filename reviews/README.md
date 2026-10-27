# Delivery review — do not infer playback from stills

Run 40492903025 passed its automated checks, but later frame inspection found a clipped two-envelope layer and background blocks in Short 2. That release is not final-approved.

The corrected source at c1a5d6b includes camera framing, four reviewed Short 2 source crops, shared word-width fitting, a whole-plan typography regression, all-frame bake-edge checks and a deterministic sample re-bake. Replacement review run: 40497873055. Final publication is held until required review is recorded. Runner exports on ci-logs are review files, not production approval.

A review record `reviews/<render-run-id>.json` must name the exact run ID and 40-character render SHA and record actual PASS for `all_layouts`, `all_effect_states`, and `finished_motion_with_sound`. Never mark the latter from screenshots or metrics. Current agent tools do not establish a full playback/listening pass.

Once a supported reviewer actually completes these checks, committing the review record triggers `publish-reviewed.yml`, which validates the run/SHA, restores the exact runner export, verifies every checksum, scans files and archive members, and publishes a new release without overwriting the previous version. No rerender or separate publication approval is needed when all QA criteria genuinely pass.
