# v1.2.7 — Correct ALB Map Scale

This release reduces the All-Weather Lifeboat (ALB) graphic by 30% so it no longer dominates the MissionChief map or vehicle list when multiple boats are present.

## What changed

- Reduced the ALB command-profile canvas from **241×118 px** to **169×84 px**.
- Reduced the rendered width by **29.9%** and height by **28.8%**, matching the requested approximate 30% correction while retaining readable detail.
- Rebuilt both the static PNG and twelve-frame animated APNG for slot **70**.
- Preserved the complete ALB silhouette, marine grounding shadow, navigation-light/wake animation, frame count and deterministic timing.
- Preserved all other 116 static and animated vehicle pairs byte-for-byte.
- Left the original v1.0 True Scale profile unchanged.

## Validation

The release must pass the full 117-vehicle dense-map and animation gate, the existing 196-anchor emergency-light audit and the exact two-file release-scope check against `v1.2.6`.

## Deployment

For an incremental update to MissionChief pack `5897`, replace only the normal and emergency-response images in slot **70 — ALB**, keeping APNG enabled for the response image.
