# Checkpoint v1.2.4 — HVP & Helicopter Tail Hotfix

## Scope completed

- Corrected assets: `hvp`, `hems`, `police-helicopter`, `coastguard-rescue-helicopter`, `coastguard-rescue-helicopter-large`
- MissionChief slots: 10, 12, 51, 65 and 66
- Vehicle configuration: original HVP pump/manifold module mounted on three-axle prime mover
- Static/animated pairs changed from v1.2.3: 5
- Mounted specialist-carrier family after release: 10
- Response lights on HVP carrier: 4
- MissionChief slot mapping changes: none
- Legacy v1.0 source changes: none
- Full-tail helicopter masters added: 2
- Safe edge allowance applied to all helicopters: 10 pixels
- Minimum tail margin across every static/APNG frame: 6 pixels

## Preserved production gates

- 117 transparent static PNGs
- 117 twelve-frame APNGs
- frame-one/static identity
- all v1.2.1 clean-roofline protections
- all nine v1.2.3 pod-carrier export identities
- helicopter rotor-underlay and full-tail margin regressions
- satellite contrast and grounding-shadow thresholds
- 100%, 75% and 50% map-scale evidence

## Carrier gate

The deterministic build must preserve the original HVP pump, hose-bank and manifold module, the PM cab and the complete three-axle chassis. It must also rebuild the complete HEMS and Police fenestron tails from retained sources and preserve safe tail clearance on all four helicopters. `data/v1.2.4-qa-report.json` must report exactly ten mounted carriers, four response lights on every carrier, a helicopter tail margin of at least six pixels and `"all_passed": true`.

The release-scope gate compares the built exports to `v1.2.3` and must report exactly five changed static/APNG pairs with no unrelated fleet drift.
