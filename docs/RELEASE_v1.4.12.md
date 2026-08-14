# v1.4.12 — SAR Control Van roof-equipment repair

This targeted release corrects the Control Van (SAR) at MissionChief slot 86. No other vehicle artwork changes.

## Corrected defect

The baked specialist cue added a deep orange-edged command cabinet and a second dish mast above a source van that already carried an emergency lightbar and rear communications mast. At MissionChief scale the artificial cabinet dominated the van, while the duplicate mast made the roof equipment look detached and implausible in both the static and animated graphics.

## Permanent repair

- Removes the oversized command cabinet and duplicate dish mast.
- Preserves the source van's front roof lightbar, single rear communications mast, SAR livery and exact map anchor.
- Adds one shallow 21-pixel command rail with exactly three isolated amber status pixels.
- Retains two independently flashing roof emitters plus the front and rear response emitters.
- Retains the 102×65 command canvas and full-frame 12-frame APNG encoding.
- Adds a dedicated fail-closed gate that permits master changes only on the approved command-rail row and rejects any cabinet, duplicate mast, indicator drift, fixture drift, frame-zero drift or partial APNG frame.

## Release scope

Against v1.4.11, the only changed MissionChief exports are:

- `assets/exports/command/static/control-van-sar.png`
- `assets/exports/command/animated/control-van-sar.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.11.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 86 (edit index 85), keep animation enabled for the APNG, and leave every other row untouched.
