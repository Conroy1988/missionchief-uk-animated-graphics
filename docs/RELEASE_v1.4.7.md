# v1.4.7 — Joint Response Unit roof-light repair

This targeted release corrects the Joint Response Unit at MissionChief slot 20. No other vehicle artwork changes.

## Corrected defect

The source vehicle already contained a compact roof lamp. The v1.3 role-differentiation pass then added a tall green-and-cyan “dual-service command pod” and mast above it. At native MissionChief size the framed box and animated emitters merged into the detached blue block visible in both the static and animated graphics.

## Permanent repair

- Removes the oversized dual-service roof box and mast from the Joint Response Unit roofline.
- Re-inks the original lamp position as one low-profile dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the command canvas from 72×32 to 72×30 without moving its bottom-centre map anchor.
- Adds a dedicated regression gate that rejects a tall roof module, joined lens pixels, incorrect fixture coordinates, frame-zero drift, missing flashes or any return of the box geometry.

## Release scope

Against v1.4.6, the only changed MissionChief exports are:

- `assets/exports/command/static/joint-response-unit.png`
- `assets/exports/command/animated/joint-response-unit.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.6.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 20, keep animation enabled for the APNG, and leave every other row untouched.
