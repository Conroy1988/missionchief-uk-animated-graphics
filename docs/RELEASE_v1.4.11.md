# v1.4.11 — Armed Traffic Car and CBRN roof-equipment repairs

This targeted release corrects the Armed Traffic Car at MissionChief slot 26 and the CBRN Vehicle at slot 33. No other vehicle artwork changes.

## Corrected defects

### Armed Traffic Car

The baked role cue added two raised circular ANPR-style roof pods and a beacon mast above an estate police car that already had a clean roof contour. At MissionChief scale, the modules looked like detached blue blobs and obscured the intended Armed Traffic Car silhouette in both static and animated graphics.

### CBRN Vehicle

The baked specialist cue added a deep, full-width detector cabinet and separate mast above an ambulance roof that already carried its physical response-light fixtures. At MissionChief scale, the cabinet dominated the vehicle and read as a giant illuminated box rather than compact detection equipment.

## Permanent repairs

- Removes both Armed Traffic Car roof pods and its beacon mast, then re-inks one shallow integrated dark housing with exactly two separated one-pixel blue lenses.
- Removes the raised CBRN detector cabinet and separate mast, then replaces them with one single-row detector rail containing exactly three isolated amber sensor pixels.
- Aligns two independently flashing Armed Traffic Car roof emitters and four independently phased CBRN body-mounted emitters to their exact physical fixtures.
- Retains both vehicles' front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the Armed Traffic Car command canvas from 74×36 to 74×34 and the CBRN command canvas from 96×57 to 96×54 without moving either bottom-centre map anchor.
- Adds dedicated fail-closed gates for both repairs, rejecting raised boxes, pods or masts; incorrect sensor or lens geometry; fixture drift; frame-zero drift; partial APNG frames; or missing independent flashes.

## Release scope

Against v1.4.10, the only changed MissionChief exports are:

- `assets/exports/command/static/armed-traffic-car.png`
- `assets/exports/command/animated/armed-traffic-car.png`
- `assets/exports/command/static/cbrn-vehicle.png`
- `assets/exports/command/animated/cbrn-vehicle.png`

The standard profile and the other 115 command-profile vehicle pairs remain byte-identical to v1.4.10.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 26 and both files at slot 33, keep animation enabled for the APNGs, and leave every other row untouched.
