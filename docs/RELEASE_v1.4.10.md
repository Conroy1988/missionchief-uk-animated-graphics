# v1.4.10 — Community First Responder roof-cross repair

This targeted release corrects the Community First Responder vehicle at MissionChief slot 23. No other vehicle artwork changes.

## Corrected defect

The baked role cue added a raised green medical cross-box above a source response car that already carried a correctly positioned roof light. At MissionChief scale, the generated box looked detached and obscured the intended estate-car silhouette in both static and animated graphics.

## Permanent repair

- Removes the generated green medical cross-box completely.
- Re-inks the source roof-light position as one integrated single-row dark housing with exactly two separated one-pixel blue lenses.
- Aligns two independently flashing point emitters to those exact lens pixels.
- Retains the existing front and rear response emitters and full-frame 12-frame APNG encoding.
- Reduces the command canvas from 65×33 to 65×31 without moving its bottom-centre map anchor.
- Adds a dedicated Community First Responder gate that rejects any return of the raised cross-box, unexpected saturated green or blue roof pixels, joined lenses, incorrect fixtures, frame-zero drift or missing flashes.

## Release scope

Against v1.4.9, the only changed MissionChief exports are:

- `assets/exports/command/static/community-first-responder.png`
- `assets/exports/command/animated/community-first-responder.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.9.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 23, keep animation enabled for the APNG, and leave every other row untouched.
