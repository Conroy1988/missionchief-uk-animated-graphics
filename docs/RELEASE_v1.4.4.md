# v1.4.4 — IRV roof-light repair

This targeted release corrects the Police Incident Response Vehicle at MissionChief slot 9. No other vehicle artwork changes.

## Corrected defect

The IRV source already contained a usable slim roof lightbar, but the v1.3 role-differentiation pass added two oversized police-blue ANPR modules above it. At native MissionChief size, their filled outlines visually joined into the blue blobs visible in both the static and animated command graphics.

## Permanent repair

- Replaces the twin oversized modules with one low-profile dark roof housing.
- Uses exactly two separated one-pixel blue lenses in the baked master and command static graphic.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front response emitter and full-frame 12-frame APNG encoding.
- Reduces the IRV command canvas from 72×32 to 72×30 without moving its bottom-centre map anchor.
- Adds a dedicated regression gate that rejects joined roof-light pixels, incorrect fixture coordinates, frame-zero drift, missing flashes or any return of the blob geometry.

## Release scope

Against v1.4.3, the only changed MissionChief exports are:

- `assets/exports/command/static/police-incident-response-vehicle.png`
- `assets/exports/command/animated/police-incident-response-vehicle.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.3.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 9, keep animation enabled for the APNG, and leave every other row untouched.
