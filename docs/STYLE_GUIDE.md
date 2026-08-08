# TKB UK Emergency Fleet — Visual Standard

## Master view

- Perfect right-facing side elevation.
- Level wheel baseline with no three-quarter perspective.
- Original generic UK fleet designs: no manufacturer marks, registration numbers, service crests, or copied photographs.
- Neutral daylight rendering with realistic materials and crisp technical edges.
- Emergency lights remain visibly blue when inactive but emit no glow in static graphics.

## Service language

- Fire: red bodywork, fluorescent yellow-red conspicuity, operational equipment appropriate to the vehicle role.
- Police: white base, blue-fluorescent-yellow Battenburg, low-profile blue warning equipment.
- Ambulance: fluorescent yellow base, green-yellow markings, blue warning equipment.
- Specialist services will retain their recognisable UK colour and conspicuity conventions without reproducing protected service crests.

## Scale

The Modern Command Clarity profile uses 13 pixels per metre of real vehicle length. Every target width is calculated from the declared real length rather than inherited source-pixel width. The only deliberate exception is the approved 159 px ALB body (169×84 px final canvas), retained to prevent lifeboat clusters dominating the map.

Large masters are retained independently from exports. All map assets are rebuilt from the masters so the standard can be adjusted later without damaging source artwork.

## Animation

- Six-frame APNG loop for the True Scale profile; twelve frames for Modern Command Clarity.
- Alternating A/B blue-light groups with deliberate dark intervals.
- Modern Command Clarity distributes blue-light vehicles across all eleven active phase offsets; individual fittings also receive deterministic sub-phases so crowded incidents do not flash in lockstep.
- Short bright core and restrained bloom; no whole-vehicle neon glow.
- Light effects follow the rendered shape of the actual lightbar, grille unit or rear fixture; generic floating points are prohibited.
- Animated road-response graphics may use subtle steady headlights and red rear lamps. Frame one remains byte-equivalent to the static graphic.
- Animation geometry is composited onto the approved static master so the vehicle body never shifts between frames.
- Helicopters use per-aircraft hub geometry. Baked source blades are removed before a semi-transparent elliptical rotor blur is composited, preventing a static blade from showing underneath the animation.
- Coastguard external tail rotors retain their complete structural artwork and receive a restrained moving blur. Enclosed HEMS and police fenestrons do not receive a second synthetic rotor cross.
- Helicopters use restrained navigation, tail and anti-collision rhythms independent of emergency lighting.
- Operational lifeboats use role-weighted bow spray, stern turbulence, water shimmer and red/green navigation lights. Trailer-mounted craft remain road assets and do not receive water wakes.
- Wheel animation is limited to declared cycle, ATV, recovery and airport assets with per-asset wheel-centre geometry.

## Role clarity and map contrast

- Role clarity must come from the original vehicle artwork, proportions, livery and authentic built-in equipment—not programmatically generated roof bars.
- Synthetic roof blocks, generic equipment boxes and colour-coded silhouette markers are prohibited.
- If a role needs stronger differentiation, create or revise its source master and review it at map scale; do not bolt generated geometry onto an export.
- The weakest satellite-map assets receive a stronger light inner edge, dark outer edge and shadow while retaining transparent corners.
- Visibility outlines use compact, standard and large-vehicle classes. Small assets receive a single-pixel treatment; large vehicles never inherit an oversized small-icon halo.
- Every asset receives a compact contact shadow rather than a full-body floating halo. Light road vehicles, heavy vehicles, trailers, marine assets and aircraft use distinct grounding treatments.
- The 40-asset corrected-roofline inventory must retain zero generated top padding.
- Role and specialist differentiation must be baked into a deterministic source master. Runtime-generated roof equipment remains prohibited.

## Quality gates

- RGBA transparency with fully transparent corners.
- No chroma colour at map scale.
- Correct real-world relative width.
- Mean fleet scale error must remain below 2%, with no non-exempt asset exceeding 3%.
- Exactly six APNG frames in True Scale and twelve in Modern Command Clarity.
- Static and animated files share identical dimensions and vehicle alignment.
- The fleet must occupy all eleven emergency-light phase buckets and clear the configured light-activity diversity gates.
- Corrected rooflines and grounding shadows must remain valid at 50% scale.
- All targeted satellite assets clear the boosted edge-contrast threshold.
- Every APNG must decode pixel-for-pixel to its generated frames after optimisation; compression must never alter appearance, timing or frame count.
- All source masters, exports, reports and release packages must reproduce byte-for-byte on a second build.
