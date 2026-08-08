# v1.4.0 — Air, Marine and Redraw Overhaul

This release completes the approved next-stage upgrades 4, 5, 6, 7, 9 and 10: a weakest-artwork redraw wave, aircraft and marine overhauls, UK livery-language verification, fleet-wide map-anchor auditing and smoother specialist animation.

## Artwork redraw wave

- Redrawn 18 weaker ground assets with sharper compartments, panel seams, equipment, glazing, rails and structural detail.
- Re-inked both operational lifeboats with clearer hull, tube, cabin, window, rail and navigation-fixture detail.
- Preserved the exact alpha silhouette and dimensions of all 20 new masters, preventing scale or anchor drift.
- Preserved all twenty v1.3.0 role-specific masters and every earlier full-tail, carrier, ALB-scale and emergency-light correction.

## Aircraft and marine motion

- Upgraded HEMS, Police and both Coastguard helicopters from 12 to 18 frames.
- Added deeper multi-band main-rotor blur, a third rotor-depth arc, varied streak layers, smoother tail-rotor phases and refined aviation-light rhythms.
- Upgraded ILB and ALB from 12 to 18 frames.
- Added vessel-specific wake length, waterline shimmer, stern turbulence and bow-spray pulses.
- Re-anchored red, green and white navigation lamps to visible vessel fixtures.
- Upgraded six suitable cycle, ATV, recovery and airport assets to smoother 18-frame wheel rotation.
- Kept the remaining 105 assets at 12 frames to avoid unnecessary map load.

## UK livery-language audit

The palette pass retains original, non-branded artwork while normalising the established colour language used across UK emergency vehicles. It is grounded in the UK rules permitting emergency-service Battenburg and conspicuity markings, the RNLI's current official lifeboat references and Bristow's official HM Coastguard SAR fleet references:

- [Road Vehicles Lighting and Goods Vehicles (Plating and Testing) (Amendment) Regulations 2009](https://www.legislation.gov.uk/uksi/2009/3220/made)
- [RNLI official lifeboat fleet](https://rnli.org/what-we-do/lifeboats-and-stations/our-lifeboat-fleet)
- [Bristow UK Search and Rescue operations](https://www.bristowgroup.com/services/uk-search-and-rescue)

No official service logo, registration or protected service mark was added.

## Anchor and performance results

- 117/117 static graphics are byte-aligned with APNG frame 1.
- 117/117 animation canvases retain one fixed bottom-centre map anchor.
- Maximum bottom-anchor movement: 0 px.
- 196/196 audited emergency-light anchors pass; maximum body distance remains 1.41 px.
- 105 assets use 12 frames and 12 selected motion assets use 18 frames.
- v1.3.0 animated fleet: 9,034,343 bytes.
- v1.4.0 animated fleet: 9,962,762 bytes.
- v1.4.0 remains 46.77% smaller than v1.2.7 despite the new 18-frame cycles.
- Pixel-exact APNG verification: 117/117.

## Validation and deployment

- 117/117 static PNGs passed four-theme QA at 100%, 75% and 50% scale.
- 117/117 animated APNGs passed frame, timing, alpha, centroid and decode checks.
- All 20 new masters remain visibly changed at 50% scale; minimum changed-pixel result is 258.
- Exact release scope: all 117 static/APNG pairs and no undeclared export paths.
- Reproducible numbered-package SHA-256: `21fa70e625b71379abdc5a4e54b892d7c7d8edb3289b811cb015d95f233b03c5`.

Deploy both files for all 117 MissionChief slots to pack `5897`, keep APNG enabled, update the public description to `v1.4.0`, then verify filenames, dimensions, frame counts and APNG state against the release manifest.
