# Delivery review — do not infer playback from stills

Run 40492903025 passed its automated checks, but later frame inspection found a clipped two-envelope layer and background blocks in Short 2. That release is not final-approved.

Commit b86370e corrects the camera framing and the affected masks, adds all-frame edge checks and a deterministic sample re-bake, and holds final publication until required review is recorded. Runner exports on ci-logs are review files, not production approval.

A review record `reviews/<render-run-id>.json` must name the exact run ID and 40-character render SHA and record actual PASS for `all_layouts`, `all_effect_states`, and `finished_motion_with_sound`. Never mark the latter from screenshots or metrics. Current agent tools do not establish a full playback/listening pass.

Once a supported reviewer actually completes these checks, committing the review record triggers `publish-reviewed.yml`, which validates the run/SHA, restores the exact runner export, verifies every checksum, scans files and archive members, and publishes a new release without overwriting the previous version. No rerender or separate publication approval is needed when all QA criteria genuinely pass.
