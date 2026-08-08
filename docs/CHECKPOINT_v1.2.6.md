# Checkpoint v1.2.6 — Accurate Emergency-Light Placement

## Production status

- Fleet-wide light-placement audit: complete
- Corrected animated assets: 61
- Audited emergency-light anchors: 196
- Static assets changed: 0
- Twelve-frame APNGs rebuilt: 117
- Exact release scope against v1.2.5: passed

## Placement gate

- Maximum allowed anchor-to-vehicle distance: 1.5 px
- Measured maximum anchor-to-vehicle distance: 1.0 px
- Minimum measured flash difference at an audited anchor: 179
- Anchors outside normalised body coordinates: 0
- Audited anchors without visible animation: 0

## Full-pack gate

- Static PNGs: 117/117
- Animated APNGs: 117/117
- Frames per APNG: 12
- Unique timing signatures: 117
- Emergency-light phase buckets: 11
- Visible flash-activity signatures: 56
- Preview themes: light, dark, satellite and grayscale
- Zoom factors: 100%, 75% and 50%
- Mounted specialist-carrier checks: passed
- Complete helicopter-tail checks: passed
- Final result: `all_passed: true`

The release must not be published if the light-placement report, full QA report or exact-scope gate fails.
