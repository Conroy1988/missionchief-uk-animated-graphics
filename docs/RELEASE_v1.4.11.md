# v1.4.11 — Armed Traffic Car roof-pod repair

This targeted release corrects the Armed Traffic Car at MissionChief slot 26. No other vehicle artwork changes.

## Corrected defect

The baked role cue added two raised circular ANPR-style roof pods and a beacon mast above an estate police car that already had a clean roof contour. At MissionChief scale, the modules looked like detached blue blobs and obscured the intended Armed Traffic Car silhouette in both static and animated graphics.

## Permanent repair

- Removes both generated circular roof pods and the beacon mast completely.
- Re-inks the roof position as one shallow integrated single-row dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the command canvas from 74×36 to 74×34 without moving its bottom-centre map anchor.
- Adds a dedicated Armed Traffic Car gate that rejects any return of raised pod or mast geometry, unexpected roof blue pixels, joined lenses, incorrect fixtures, frame-zero drift, partial APNG frames or missing independent flashes.

## Release scope

Against v1.4.10, the only changed MissionChief exports are:

- `assets/exports/command/static/armed-traffic-car.png`
- `assets/exports/command/animated/armed-traffic-car.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.10.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 26, keep animation enabled for the APNG, and leave every other row untouched.
