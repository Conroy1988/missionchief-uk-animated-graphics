# v1.2.6 — Accurate Emergency-Light Placement

This release corrects the flashing-light geometry across the Modern Command Clarity fleet. A fleet-wide visual audit found that a later production batch had inherited one generic three-point flash layout even when its lightbar, cab, grille lights, rear lamps or vehicle orientation differed.

## What changed

- Re-anchored **196 individual emergency-light effects across 61 vehicles**.
- Aligned roof flashes to the visible lightbars and beacon units on every corrected asset.
- Moved grille, nose and rear flashes onto the corresponding rendered fittings instead of empty space beyond the body.
- Corrected the left-facing ambulance, SAR, fire-investigation and EOD vehicles independently rather than assuming every vehicle faced right.
- Moved the fourth response point on the prime mover, mounted pod family and HVP from the wheel/chassis area to the rear warning-light position.
- Removed misplaced helicopter effects from rotor hubs, landing gear and empty space while retaining the complete-tail and rotor-motion protections from v1.2.5.
- Preserved all 117 static PNGs unchanged; only the 61 audited APNGs differ from v1.2.5.

## New regression protection

`scripts/validate_light_placement.py` now checks every audited anchor against the rendered vehicle body and verifies that each anchor produces a visible flash in at least one APNG frame.

The v1.2.6 gate covers:

- 61 audited assets
- 196 audited light anchors
- maximum anchor distance of 1.0 pixel against a 1.5-pixel limit
- visible animation at every anchor
- exact 61-APNG release scope against tag `v1.2.5`
- 117/117 static PNG and twelve-frame APNG pairs through the full map, animation, helicopter-tail and mounted-carrier QA suite

`data/v1.2.6-light-placement-report.json` and `data/v1.2.6-qa-report.json` must both report `"all_passed": true` before publication.

## Deployment

The numbered release archive remains the safest complete-pack deployment package. For an incremental update to MissionChief pack `5897`, only the animated files for the 61 slots declared in `data/v1.2.6-scope.json` need replacement; the static graphics are byte-identical to v1.2.5.
