# v1.3.0 — Fleet Quality Overhaul

This release rebuilds the complete 117-vehicle Modern Command Clarity fleet around real-world scale, cleaner source art, more credible movement and substantially lighter lossless APNGs. It incorporates approved upgrades 1–14 and 16 while preserving the live v1.2.7 ALB correction, all helicopter-tail fixes and every v1.2.6 emergency-light anchor.

## Fleet-wide visual improvements

- Recalibrated all 117 body widths to 13 pixels per metre of declared real length.
- Achieved 0.285% mean scale-rounding error and 0.855% maximum error across non-exempt assets.
- Preserved the approved ALB exception at exactly 169×84 px.
- Rebuilt twenty role-specific source masters with command, ANPR, medical, drone, CBRN and EOD equipment baked into the artwork.
- Standardised 123,679 existing high-visibility livery pixels without adding protected service marks.
- Replaced one-size-fits-all edges with compact, standard and large-vehicle outline classes.
- Added light, heavy, trailer, marine and separated-aerial grounding-shadow classes.
- Applied half-scale detail reinforcement and alpha cleanup to every asset; no isolated alpha noise remains.

## Lighting and movement

- Retained all 196 audited emergency-light anchors across 61 previously corrected vehicles.
- Replaced generic flash points with fixture-shaped lightbar, grille and rear LED cores.
- Added subtle steady response headlights and rear lamps to 91 suitable road assets.
- Added semi-transparent elliptical main-rotor blur and aviation-light rhythms to all four helicopters.
- Added visible movement to both preserved Coastguard external tail rotors without deleting their structural blades.
- Improved ILB and ALB red/green navigation lights, bow spray, stern turbulence and wake strength independently.
- Added fixture-aligned wheel motion to six suitable cycle, ATV, recovery and airport vehicles.

## Performance

All 117 APNGs are saved with pixel-exact delta-frame optimisation and automatically fall back to the safer full-frame disposal mode whenever required. Every output is decoded and compared against its generated frames before the build can pass.

- v1.2.7 animated fleet: 18,718,182 bytes
- v1.3.0 animated fleet: 9,034,343 bytes
- Reduction: 51.73%
- Pixel-exact APNG verification: 117/117
- Frame count and timing: unchanged at twelve deterministic frames per asset

## Validation

- 117/117 static PNGs passed.
- 117/117 animated APNGs passed.
- Exact release scope: all 117 static/APNG pairs and no undeclared export paths.
- 196/196 audited flash anchors passed with a maximum 1.41 px body distance.
- Four-theme QA passed at 100%, 75% and 50% scale.
- All twenty baked masters retain visible role detail at 50% scale.
- All four complete helicopter tails passed structural and clearance gates.
- All ten mounted specialist carriers passed chassis, cab, module and lighting gates.
- Repeated release packages must produce the same SHA-256 before publication.
- Reproducible numbered-package SHA-256: `000bab9753c681e06ab03c12923eeee8fc469090c6da64284032729c4f1064b7`.

## Deployment

This is a complete-fleet release. Deploy both the static and animated image for all 117 MissionChief slots to pack `5897`, keep APNG enabled for every response file, update the public description to `v1.3.0`, then verify live dimensions and APNG state before completing the rollout.
