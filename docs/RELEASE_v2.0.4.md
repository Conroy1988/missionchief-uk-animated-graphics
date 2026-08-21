# v2.0.4 — Complete mounted pod carriers

v2.0.4 corrects all ten fire-service container graphics that appeared to travel without a driver or front cab. Every pod and the HVP module now travels on the complete direction-neutral prime mover at MissionChief's native 110×110 map scale.

## Corrected slots

- 42 — Water Pod
- 43 — Bulk Foam Pod
- 44 — Rescue Pod
- 45 — Command Pod
- 46 — Welfare Pod
- 47 — BASU Pod
- 48 — Misting Pod
- 49 — Hazardous Materials Pod
- 50 — OSU Pod
- 51 — HVP

Each corrected static PNG and twelve-frame APNG now contains the original role-specific module, an unmistakable windscreen and cab, powered three-axle road chassis, front wheel, grille and bumper. Slot 41 remains the unloaded PM.

## Deterministic construction

- Uses the preserved v2.0.0 PM and module masters as the only artwork sources.
- Removes only the empty raised hook-lift boom before mounting each module.
- Restores the approved PM cab as the foreground layer so its glazing and front-end geometry remain unchanged.
- Keeps every carrier on the fixed lower-right raised three-quarter canvas.
- Rebuilds physically calibrated blue response lights on the common cab lightbar and front/rear carrier positions.

## Preserved corrections

- F/WrC, WrL CAFS and RP CAFS retain the complete v2.0.3 driven-appliance cabs.
- HEMS, Police and both Coastguard helicopters retain the calibrated v2.0.2 main and tail rotor motion.
- All 117 static and 117 animated mappings remain in authoritative MissionChief slot order.
- The v1.4.14 command-profile exports remain unchanged.

## Validation evidence

- `mounted-carrier-before-after.png` — all ten module-only sources beside the complete loaded carriers;
- `mounted-carrier-live-map.png` — all corrected 110×110 exports at native pixels on light, satellite and dark maps;
- `v2.0.4-mounted-carrier-report.json` — fail-closed source, cab, glazing, module, width and export-provenance checks;
- complete static, APNG, scale, fixture, archive and release-integrity reports.

The numbered deployment archive contains 117 static PNGs and 117 animated APNGs plus the exact slot guide, manifest and SHA-256 verification.
