# Checkpoint v1.2.3 — Complete Mounted Pod Fleet

## Scope completed

- Corrected assets: `water-pod`, `bulk-foam-pod`, `rescue-pod`, `command-pod`, `welfare-pod`, `basu-pod`, `misting-pod`, `osu-pod`
- MissionChief slots: 42–48 and 50
- Vehicle configuration: role-specific module mounted on three-axle prime mover
- Static/animated pairs changed from v1.2.2: 8
- Mounted carrier family after release: 9
- Response lights per carrier: 4
- MissionChief slot mapping changes: none
- Legacy v1.0 source changes: none

## Preserved production gates

- 117 transparent static PNGs
- 117 twelve-frame APNGs
- frame-one/static identity
- all v1.2.1 clean-roofline protections
- v1.2.2 Hazardous Materials Pod export identity
- helicopter rotor-underlay regression
- satellite contrast and grounding-shadow thresholds
- 100%, 75% and 50% map-scale evidence

## Carrier gate

The deterministic build must preserve each distinct pod module, the PM cab and the complete three-axle chassis. `data/v1.2.3-qa-report.json` must report exactly nine mounted carriers, four response lights on every carrier and `"all_passed": true`.

The release-scope gate compares the built exports to `v1.2.2` and must report exactly eight changed static/APNG pairs with no unrelated fleet drift.
