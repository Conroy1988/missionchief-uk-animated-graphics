# v1.4.14 — Complete trailer towing units

This release fixes the self-propelled trailer effect across every standalone trailer slot in the MissionChief UK fleet. MissionChief moves each assigned graphic as one map object, so a trailer-only image appears to drive itself. Each affected graphic now represents the complete road-going unit: service-appropriate tow vehicle, connected hitch and the original role-specific trailer.

## Corrected fleet

| Slot | MissionChief vehicle | Complete towing unit |
|---:|---|---|
| 62 | Flood Rescue Unit (Trailer) | Coastguard 4×4 + flood-rescue equipment trailer |
| 68 | Inland Rescue Boat (Trailer) | Coastguard 4×4 + inland rescue boat trailer |
| 71 | Rescue Watercraft (Trailer) | Lifeboat transporter + rescue-watercraft trailer |
| 72 | Hovercraft (Trailer) | Lifeboat transporter + hovercraft trailer |
| 75 | Boat Trailer | Fire 4×4 + boat trailer |
| 82 | Medical equipment trailer | Airfield operations pickup + medical equipment trailer |
| 85 | Pump Trailer | SAR 4×4 + pump trailer |
| 88 | Operational Support Trailer | SAR 4×4 + operational support trailer |
| 89 | SAR Flood Rescue (Trailer) | SAR 4×4 + flood-rescue trailer |

## Production behaviour

- All hitches are visibly connected and preserve the original trailer artwork.
- Combined road lengths are recalibrated at the fleet standard of 13 pixels per metre.
- Eight tow vehicles use three fixture-aligned point emitters plus steady head/rear lamps.
- The airfield towing unit uses its amber beacon rather than blue response lights.
- Rear marker motion is placed at the trailer rear, not on the towing end.
- Every APNG retains 12 full-canvas frames, frame-zero identity and a stable bottom-centre map anchor.
- A deterministic master builder and a dedicated fail-closed validator require exactly nine complete towing units and zero bare trailers.

## Release scope

Against v1.4.13, exactly 18 command-profile exports change: static PNG and animated APNG files for the nine slots above. The standard profile and the other 108 command-profile vehicle pairs remain byte-identical to v1.4.13.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slots 62, 68, 71, 72, 75, 82, 85, 88 and 89. Their zero-based edit indices are 61, 67, 70, 71, 74, 81, 84, 87 and 88 respectively. Keep animation enabled for the APNG upload and leave every other row untouched.
