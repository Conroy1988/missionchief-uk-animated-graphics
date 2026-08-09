# v1.4.6 — ARV roof-light repair

This targeted release corrects the Armed Response Vehicle at MissionChief slot 14. No other vehicle artwork changes.

## Corrected defect

The original ARV artwork already contained a usable slim roof lightbar. The v1.3 role-differentiation pass then added a tall police-blue outlined “equipment locker” directly above it. At native MissionChief size the box frame, blue lower strip and animated lamp visually merged into the detached roof lump visible in both the static and animated graphics.

## Permanent repair

- Removes the raised equipment box from the ARV roofline.
- Re-inks the original lamp position as one low-profile dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the ARV command canvas from 74×36 to 74×34 without moving its bottom-centre map anchor.
- Adds a dedicated regression gate that rejects a tall roof module, joined lens pixels, incorrect fixture coordinates, frame-zero drift, missing flashes or any return of the box geometry.

## Release scope

Against v1.4.5, the only changed MissionChief exports are:

- `assets/exports/command/static/armed-response-vehicle.png`
- `assets/exports/command/animated/armed-response-vehicle.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.5.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 14, keep animation enabled for the APNG, and leave every other row untouched.
