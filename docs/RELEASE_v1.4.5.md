# v1.4.5 — RRV roof-light repair

This targeted release corrects the Rapid Response Vehicle at MissionChief slot 11. No other vehicle artwork changes.

## Corrected defect

The original RRV artwork already contained a usable slim blue roof lightbar. The v1.3 role-differentiation pass then added a large ambulance-green equipment box and white medical cross directly above it. At native MissionChief size the box, cross and lamp visually merged into the odd roof lump visible in both the static and animated graphics.

## Permanent repair

- Removes the oversized green medical box and white cross from the RRV roofline.
- Re-inks the original lamp position as one low-profile dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front response emitter and full-frame 12-frame APNG encoding.
- Reduces the RRV command canvas from 72×32 to 72×31 without moving its bottom-centre map anchor.
- Adds a dedicated regression gate that rejects a tall roof module, joined lens pixels, incorrect fixture coordinates, frame-zero drift, missing flashes or any return of the box geometry.

## Release scope

Against v1.4.4, the only changed MissionChief exports are:

- `assets/exports/command/static/rapid-response-vehicle.png`
- `assets/exports/command/animated/rapid-response-vehicle.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.4.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 11, keep animation enabled for the APNG, and leave every other row untouched.
