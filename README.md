# TKB UK Emergency Fleet — Animated

A complete original UK-themed vehicle graphics pack for MissionChief UK.

## Release status

Release **v1.0.0** covers all **117** slots in the live MissionChief UK vehicle-graphics editor.

- 117 transparent map-scale static PNGs
- 117 six-frame APNGs
- 87 emergency assets with restrained alternating blue-light animation
- 30 trailers, boats, support assets and non-blue-light vehicles with aligned static APNG frames
- 117 full-resolution transparent masters
- 117 archived chroma-key source images
- Complete live-slot mapping for private MissionChief pack **5897**

All release checks pass, including source decoding, alpha transparency, ordered slot coverage, unique asset IDs, real-world relative scale, APNG frame count, static/APNG alignment, and expected flashing behaviour.

## Visual standard

The pack uses realistic, isolated side-elevation product artwork with UK emergency-service colour language and no copied agency logos or readable branding. New production sources were generated individually on a flat `#FF00FF` chroma background, then converted to transparent RGBA masters by the repeatable build pipeline.

## Structure

- `assets/sources/` — representative full-resolution chroma-key source artwork
- `assets/exports/standard/static/` — MissionChief-ready transparent PNGs
- `assets/exports/standard/animated/` — MissionChief-ready six-frame APNGs
- `assets/previews/` — browser-friendly map-scale, animation-frame and selected artwork QA sheets
- `data/vehicle-slots.json` — authoritative 117-slot live editor mapping
- `data/prototypes.json` — production specification and light placement manifest
- `data/final-pack-validation.json` — release-level validation report
- `scripts/` — repeatable preparation, packaging and QA tools
- `docs/` — standards and release checkpoints

The complete 117-file chroma source set, all 117 full-resolution transparent masters and the complete high-resolution QA set are included in the **full production archive** attached to the GitHub [`v1.0.0` release](https://github.com/Conroy1988/missionchief-uk-animated-graphics/releases/tag/v1.0.0). Keeping the large working artwork in a release asset avoids duplicating hundreds of megabytes of binary history in every Git clone.

## Release downloads

- **Recommended for MissionChief upload:** `TKB-UK-Emergency-Fleet-MissionChief-Numbered-Upload-Ready-v1.0.0.zip`
  - Separate `01 - Static` and `02 - Animated` folders
  - Files ordered and named `001` through `117`
  - Exact MissionChief vehicle labels, with only Windows-invalid filename characters normalised
  - Includes `UPLOAD-GUIDE.csv`, `UPLOAD-MANIFEST.json` and SHA-256 verification
- `TKB-UK-Emergency-Fleet-MissionChief-Upload-Ready-v1.0.0.zip` — original compact deployment package using production asset IDs
- `TKB-UK-Emergency-Fleet-v1.0.0.zip` — complete production project containing sources, transparent masters, exports, previews, mappings, documentation and build tools

## Rebuild and validate

```bash
python scripts/build_prototypes.py
python scripts/build_source_qa.py
python scripts/validate_final_pack.py
python scripts/build_numbered_upload_package.py --version v1.0.0
```

`build_prototypes.py` regenerates all static and animated exports plus the map-scale and APNG-frame QA sheets. `validate_final_pack.py` is the final artwork release gate and must report `"all_passed": true`. `build_numbered_upload_package.py` copies the validated exports byte-for-byte into the numbered deployment structure, verifies all 117 static and animated pairs, creates the upload guide and validates ZIP integrity.

## MissionChief deployment

Use the numbered upload-ready archive for the private working pack `TKB UK Fleet — Animated WIP` (pack ID `5897`). Work from slot `001` to slot `117`; each numbered static file and animated file corresponds directly to the same one-based row in the live MissionChief editor.
