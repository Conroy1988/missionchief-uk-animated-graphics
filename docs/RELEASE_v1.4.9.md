# v1.4.9 — OTL roof-mast repair

This targeted release corrects the Operational Team Leader vehicle at MissionChief slot 21. No other vehicle artwork changes.

## Corrected defect

The baked OTL role cue added a tall green command box and beacon mast above a source vehicle that already carried a correctly positioned roof light. At MissionChief scale, the generated equipment looked detached and obscured the intended estate-car silhouette in both static and animated graphics.

## Permanent repair

- Removes the generated command box and beacon mast completely.
- Re-inks the source roof-light position as one integrated single-row dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the command canvas from 73×39 to 73×35 without moving its bottom-centre map anchor.
- Adds a dedicated OTL gate that rejects any return of the raised mast, unexpected saturated green or blue roof pixels, joined lenses, incorrect fixtures, frame-zero drift or missing flashes.

## Release scope

Against v1.4.8, the only changed MissionChief exports are:

- `assets/exports/command/static/otl.png`
- `assets/exports/command/animated/otl.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.8.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 21, keep animation enabled for the APNG, and leave every other row untouched.
