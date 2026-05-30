---
doc_id: thumbnail-quality-page
title: Thumbnail Quality Page
added_date: 2026-05-12
last_updated: 2026-05-30
parent_id: catalogue
---
# Thumbnail Quality Page

This page has been retired from active Studio routing.
`/studio/thumbnail-quality/?mode=manage` and `POST /studio/api/catalogue/thumbnail-quality-preview` intentionally no longer resolve through the Local Studio app.
The page script, CSS, UI text, and preview builder were archived under `studio/retired/thumbnail-quality/` so the old comparison tooling remains available as reference code without being public Jekyll output or active local-app runtime.

## Purpose

The page compares thumbnail WebP output settings using source images from:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/thumbnail-quality-preview/
```

The comparison was isolated from production thumbnails.
It wrote preview images and page data under `studio/data/generated/thumbnail-quality/`, which is no longer served by the Studio static allowlist.

## Inputs

The generator reads all supported image files in the preview source folder.

Supported source extensions:

- `.avif`
- `.heic`
- `.heif`
- `.jpeg`
- `.jpg`
- `.png`
- `.tif`
- `.tiff`
- `.webp`

## Settings

The current pipeline baseline is read from `_data/pipeline.json`.

The page currently compares:

- current pipeline thumbnail settings at the configured largest thumbnail size
- `q:v 70` at `192x192`
- `q:v 62` at `192x192`
- `q:v 54` at `192x192`
- `q:v 62` at `160x160`
- `q:v 62` at `96x96`
- `q:v 54` at `96x96`

All variants keep the configured codec, WebP preset, and compression level so the comparison stays focused on practical thumbnail-size tradeoffs.

Preview images are rendered at the same `48x48` CSS-pixel display size used by the live work index thumbnails.

The page also renders the `q:v 62` at `96x96` variants together in a series-style gallery row.
That row uses the public `.seriesGrid`, `.seriesGrid__item`, and `.seriesGrid__img` styling so the preview matches the way thumbnails expand to fill the content width on `/series/` pages.

## Refresh Command

The retired `Refresh` button called the local Catalogue endpoint:

```text
POST /studio/api/catalogue/thumbnail-quality-preview
```

The endpoint has been removed from active Studio.
The archived builder is `studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py`.

## Manual Command

Preview planned writes:

```bash
./studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py
```

Write preview assets and data:

```bash
./studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py --write
```

Write only missing preview images while refreshing the JSON:

```bash
./studio/retired/thumbnail-quality/build_thumbnail_quality_preview.py --write --missing-only
```

## Boundaries

The page does not change:

- `assets/works/img/`
- `assets/work_details/img/`
- production thumbnail configuration
- catalogue source JSON
- remote media storage
