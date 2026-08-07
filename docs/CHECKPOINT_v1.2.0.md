# Checkpoint v1.2.0 — Fleet Readability and Realism

## Scope completed

- Role-differentiated assets: 15
- Role-confusion groups covered: 5
- Additional specialist-equipment silhouettes: 25
- Satellite-contrast boosted assets: 15
- Emergency-light phase buckets: 11 across 87 blue-response assets
- Fleet grounding shadows: 117, with road, marine and aerial treatments
- Static/animated pairs changed: 117
- MissionChief slot mapping changes: none

## Measured outcome

| Gate | v1.1.1 baseline | v1.2.0 |
|---|---:|---:|
| Weakest targeted satellite contrast | 24.36 | 53.24 |
| JRU / IRV silhouette distance | 9 | 18 |
| RRV-family minimum silhouette distance | 13 | 22 |
| Armed Traffic / ARV silhouette distance | 13 | 36 |
| Emergency-light phase buckets | 5 | 11 |
| Visible light-activity signatures | not gated | 48 |

All five configured confusion groups exceed the required silhouette distance of 18.

## Production totals

- Static transparent PNGs: 117
- Animated APNGs: 117
- Frames per APNG: 12
- Unique animation timing signatures: 117
- Specialist equipment remaining visible at half zoom: minimum 30 added pixels
- Grounding shadow remaining visible at half zoom: minimum 96 pixels
- Preview themes: light, dark, grayscale and satellite
- Preview scales: 100%, 75% and 50%

## Automated QA

`data/v1.2-qa-report.json` reports `"all_passed": true`. The gate checks exact slot coverage, role and specialist-equipment configuration, fleet phase distribution, light-activity diversity, grounding shadows, reinforced edges, targeted satellite contrast, role-group silhouettes, animation stability and the existing helicopter rotor-underlay regression.

## Reversibility

The v1.1.1 profile, reports and previews remain unchanged. The complete v1.2 fleet can be rolled back to that deterministic baseline without changing the authoritative MissionChief slot mapping.
