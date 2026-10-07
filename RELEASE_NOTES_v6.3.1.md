# Mirror Talk 6.3.1 — Fluid Viewport Correction

Release date: 2026-10-02

- Removed Astra's boxed site-content gutters and forced the public page canvas to span the complete viewport.
- Replaced fixed 1120–1180 px shells with fluid content architecture: up to 1680 px for immersive homepage sections and 1520 px for libraries and page layouts.
- Added proportional desktop/tablet gutters and a consistent 12 px mobile gutter.
- Expanded the Ask Mirror Talk container to 1440 px while retaining readable internal measures.
- Kept long-form prose intentionally narrow for comfortable reading while its background and imagery remain full bleed.
- Added explicit overflow containment and responsive one/two/three-column library behavior.

## Validation

- Full suite: 158 passed, 3 skipped.
- At 1920 px: 1680 px hero with balanced 120 px gutters and no overflow.
- At 390 px: 366 px hero with 12 px gutters and no overflow.
- Desktop and mobile layouts visually verified in-browser.

## Deployment package

`wordpress/astra-child-v6.3.1.zip`
