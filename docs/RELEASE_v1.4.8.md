# v1.4.8 — ARV duplicate roof-light repair

This targeted release corrects the Armed Response Vehicle at MissionChief slot 14. No other vehicle artwork changes.

## Corrected defect

The v1.4.6 repair removed the raised equipment locker and added a low-profile replacement lightbar, but the standard source artwork's original anti-aliased blue roof strip remained above it. The two fixtures stacked into the detached double light visible in both static and animated MissionChief graphics.

## Permanent repair

- Erases the original detached blue source strip before drawing replacement roof geometry.
- Draws one integrated single-row dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the command canvas from 74×34 to 74×33 without moving its bottom-centre map anchor.
- Strengthens the dedicated ARV gate to inspect the complete roof region and reject stacked rows, extra saturated-blue pixels, joined lenses, incorrect fixtures, frame-zero drift or missing flashes.

## Release scope

Against v1.4.7, the only changed MissionChief exports are:

- `assets/exports/command/static/armed-response-vehicle.png`
- `assets/exports/command/animated/armed-response-vehicle.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.7.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 14, keep animation enabled for the APNG, and leave every other row untouched.
