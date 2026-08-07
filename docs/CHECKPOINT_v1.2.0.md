# Checkpoint v1.2.0 — Role and Satellite Clarity

## Scope completed

- Role-differentiated assets: 15
- Role-confusion groups covered: 5
- Satellite-contrast boosted assets: 15
- Static/animated pairs changed: 27 (the full 117-pair fleet was rebuilt and verified)
- MissionChief slot mapping changes: none

## Measured outcome

| Gate | v1.1.1 baseline | v1.2.0 |
|---|---:|---:|
| Weakest targeted satellite contrast | 24.36 | 47.19 |
| JRU / IRV silhouette distance | 9 | 21 |
| RRV / Specialist RRV silhouette distance | 13 | 27 |
| Armed Traffic / ARV silhouette distance | 13 | 38 |

All five configured confusion groups exceed the required silhouette distance of 18.

## Production totals

- Static transparent PNGs: 117
- Animated APNGs: 117
- Frames per APNG: 12
- Unique animation timing signatures: 117
- Preview themes: light, dark, grayscale and satellite
- Preview scales: 100%, 75% and 50%

## Automated QA

`data/v1.2-qa-report.json` reports `"all_passed": true`. The gate checks exact slot coverage, role-cue configuration, reinforced-edge configuration, targeted satellite contrast, role-group silhouettes, animation stability and the existing helicopter rotor-underlay regression.

## Reversibility

The v1.1.1 profile, reports and previews remain unchanged. The 27 modified static/animated pairs can be rolled back without changing the other 90 vehicle pairs or the authoritative MissionChief slot mapping.
