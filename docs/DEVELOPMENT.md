# Development and maintenance

[Project home](../README.md) · [Technical overview](FLEET_TECHNICAL_OVERVIEW.md)

## Source of truth

`data/vehicle-slots.json` defines the published fleet mapping. `scripts/v2_profile.py` defines the current graphics release. `gallery/vehicles.json` is generated, not hand-maintained. Historical reports and release checkpoints record their original release and should retain that context.

## Gallery workflow

Use Python 3 and Node.js 24. Fetch the release tags before validating historical comparisons:

```sh
git fetch --tags
python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site
node --test tests/gallery.test.mjs
node --check gallery/app.mjs
python -m http.server 8000 --directory dist/gallery-site
```

Open `http://localhost:8000` to preview. Check desktop and mobile widths, keyboard focus, search, service filters, vehicle details, static/animated switching and release comparison. The staged output includes the current assets; opening `gallery/index.html` directly does not provide its expected asset paths.

## Graphics changes

See the full [rebuild sequence](FLEET_TECHNICAL_OVERVIEW.md#rebuild-and-validate). Production image tools use Pillow and NumPy; the pinned build environment is in `.github/workflows/build-numbered-upload-package.yml`. All release-integrity gates must pass before changing production graphics.

A presentation-only change does not require a fleet version bump or regenerating PNGs. Preserve original masters and published release files.

## TKB presentation

Use charcoal/black surfaces, white primary text, red actions and the two horizontal red bars. Keep service colours within vehicle labels and previews, where they communicate a service. UI copy should help players find, inspect and install graphics. See [presentation standard](PRESENTATION.md).

## Hosting

The public gallery route is maintained by the TKB website. This repository builds its deployable source; its validation workflow does not publish the website. Coordinate the staged `dist/gallery-site` payload with that site's deployment when updating the public gallery.
