# v1.4.2 — Full-Fleet Light-Box Elimination

This release replaces the incomplete v1.4.1 emergency-light patch with a full audit and rebuild of every animated vehicle in both production profiles.

## Root cause

The old renderer combined oversized filled light shapes with APNG delta rectangles. In the v1.4.1 command fleet, 1,359 of 1,476 animation controls updated only a rectangular subregion. MissionChief could expose those update bounds as pale boxes around the vehicles. The previous QA decoded the artwork but did not reject partial frame controls or rectangular optical footprints.

## Corrections

- Rebuilt all 117 standard and all 117 command APNGs; no animated asset retains the old encoder output.
- Replaced broad rectangle and ellipse flashes with compact bar or point emitters.
- Clipped emergency-light effects to the vehicle silhouette with a maximum one-pixel optical allowance.
- Encoded every frame at the full canvas size with zero offsets, source blending and no delta rectangle.
- Normalised transparent pixels so invisible RGB cannot appear as a light-coloured fringe in another decoder.
- Preserved all 234 static PNGs with no visible change from v1.4.1.

## Full-fleet audit

- 468 production files audited: 234 static PNGs and 234 animated APNGs.
- 2,178 animation frames decoded and 2,178 APNG frame controls inspected.
- 0 partial update frames.
- 0 box-shaped light components.
- 0 blue pixels outside the one-pixel silhouette allowance.
- 0 hidden RGB pixels under transparent animation pixels.
- 234/234 animated files changed from v1.4.1; 234/234 static files remain visually unchanged.
- All 117 vehicles inspected on light, dark, satellite and grayscale contact sheets.
- Existing 228 fixture anchors remain valid; maximum distance to vehicle artwork is 1.41 px.

The machine-readable evidence is in `data/v1.4.2-full-fleet-lighting-report.json`. Contact sheets are under `assets/previews/v1.4.2/`.

## Deployment

Deploy all 117 animated command-profile APNGs to MissionChief pack `5897`. This is deliberately a complete animated-fleet replacement: selectively uploading only the 15 v1.4.1 specialist files would leave the faulty APNG structure in the other vehicles.
