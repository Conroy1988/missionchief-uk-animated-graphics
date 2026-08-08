# v1.4.1 — Emergency-Light Fixture Accuracy

This patch corrects emergency-light placement and flash shape on 15 specialist response vehicles while preserving every vehicle silhouette, static image, role marking and equipment module from v1.4.0.

## Corrected vehicles

- ARV / Armed Response Vehicle, Joint Response Unit, OTL, Community First Responder and Armed Traffic Car
- CBRN Vehicle, Control Van (SAR), Drone Vehicle (Police Station) and Specialist Paramedic RRV
- EOD Commander, EOD Response Vehicle, EOD Medium Equipment Van and EOD Heavy Equipment Vehicle
- Marine EOD Response Vehicle and Marine EOD Equipment Van

## Accuracy changes

- Replaced oversized generic flash blocks with compact bar or point fixtures fitted to each vehicle's visible lamp hardware.
- Added exact vehicle-specific front and rear running-lamp coordinates instead of generic canvas-edge placement.
- Kept command screens, detector boards, green medical markings, drone cradles, EOD racks, marine equipment tubes and tow gear outside every flashing envelope.
- Removed the detached rear red pixel visible beyond the EOD Heavy Equipment Vehicle's tow assembly.
- Preserved all 117 static PNGs byte-for-byte from v1.4.0; only the 15 declared animated APNGs changed.

## Validation results

- 15/15 corrected APNGs differ from the defective v1.4.0 baseline and retain pixel-identical static frame 1.
- 15/15 specialist equipment modules remain stable across all frames.
- 0 floating lamp pixels and 0 changes outside declared fixture envelopes.
- 228 emergency-light anchors audited across 66 vehicles; maximum distance from visible vehicle artwork is 1.41 px.
- Every compact corrected flash remains within a 7×5 px envelope.
- All 117 static/APNG pairs retain fixed dimensions, frame counts and bottom-centre map anchors.
- Reproducible numbered-package SHA-256: `8ccd1013cd9031c1c0d336ee299ba9bfc2d9ee35fc8dc150d6944c73acc70f51`.

## Deployment

Deploy the animated APNG for the 15 corrected MissionChief slots to pack `5897`, keep APNG enabled, update the public description to `v1.4.1`, and verify each uploaded frame against `data/v1.4.1-fixture-accuracy-report.json`. The remaining 102 animated assets and all 117 static images are unchanged from v1.4.0.
