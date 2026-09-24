# Installation and troubleshooting

[Project home](../README.md) · [Fleet gallery](../GALLERY.md)

## Use the public pack

1. Sign in to MissionChief UK and open [TKB UK Fleet — Animated, pack 5897](https://www.missionchief.co.uk/vehicle_graphics/5897).
2. Select the graphics pack for your account.
3. Enable animated vehicle graphics in your game settings if you want response animations.

Players do not need a ZIP, extension or userscript. Static images remain available where animation is disabled.

## Download individual files

Browse the [gallery](../GALLERY.md), open the static or animated image, then download the original PNG. APNG animation uses the `.png` extension; do not convert it to JPEG or resize it with an editor that discards animation.

## Upload a private copy

Download the numbered ZIP from the [v2.2.0 release](https://github.com/Conroy1988/missionchief-uk-animated-graphics/releases/tag/v2.2.0). Extract it and follow its slot guide. Match the vehicle name and slot, then use the static and animated files in their respective fields. Files in this release have a 110×110 transparent canvas. Follow [LICENSE.md](../LICENSE.md) when redistributing or adapting artwork.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Nothing animates | Enable animated vehicle graphics; check the response file is the original APNG. |
| Old graphics remain | Confirm the selected pack and any individual vehicle graphic override; reload the game. |
| A preview is static | Some viewers display only the first APNG frame. Check in an APNG-capable browser or the game. |
| A vehicle is missing | This published release maps 117 slots. Include the new vehicle name and game slot when reporting additions. |
| Wrong vehicle shown | Compare the name and slot against `data/vehicle-slots.json`; do not assume filename order equals a new game slot order. |

For a report, include the vehicle, pack ID, browser, static/animated state and a screenshot. Remove account details first. Use [repository issues](https://github.com/Conroy1988/missionchief-uk-animated-graphics/issues).

## Companion mission markers

[V5 mission markers, pack 539](https://www.missionchief.co.uk/mission_graphics/539), cover 884 mission rows. They are selected separately from the vehicle pack.
