# Checkpoint v1.1.0 — Modern Command Visibility

## Scope completed

The v1.1 profile implements selected in-game improvements 1, 2, 3, 5, 6, 7, 9, 12, 13 and 15 across the complete 117-slot MissionChief UK fleet.

- Independent emergency-light rhythms: complete
- Per-vehicle desynchronised timing: complete
- Command Visibility sizing: complete
- Light/dark map visibility edge: complete
- Helicopter rotor animation: 4/4
- Specialist visual distinction: complete
- Modern UK colour/detail treatment: 117/117
- Appropriate non-emergency motion: 19 assets
- Rare-unit showcase treatment: 33 assets
- Automated busy-map validation: complete

## Production totals

- Static transparent PNGs: 117
- Animated APNGs: 117
- Frames per APNG: 12
- Unique timing signatures: 117
- Maximum vehicles sharing one timing signature: 1
- Minimum command body width: 72 px
- Maximum command body width: 296 px
- New high-resolution replacement sources: 1

## Automated QA

All 117 assets were tested at 100%, 75% and 50% icon scale against light, dark, satellite-style and grayscale map backgrounds.

- Exact ordered slot coverage: passed
- Transparent RGBA corners: passed
- Static/APNG frame-one identity: passed
- Required animation present: passed
- Static-policy assets stable: passed
- Body-centroid stability: passed
- Half-zoom visible-pixel threshold: passed
- Four-theme edge-contrast threshold: passed
- Rare silhouette separation: passed
- Numbered ZIP integrity and 117-pair count: passed
- Final report: `data/v1.1-qa-report.json`
- Result: `all_passed: true`

## Reversibility

The v1.0 True Scale files under `assets/exports/standard/` are unchanged. The new live candidate is isolated under `assets/exports/command/`, so a rollback is a deterministic re-upload of the v1.0 numbered package.
