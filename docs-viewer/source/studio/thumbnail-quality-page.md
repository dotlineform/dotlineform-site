---
doc_id: thumbnail-quality-page
title: Thumbnail Quality Page
added_date: 2026-05-12
last_updated: 2026-05-22
parent_id: catalogue
---
# Thumbnail Quality Page

This document describes the Studio page at `/studio/thumbnail-quality/?mode=manage`.
The route shell is served by the local Studio app, not by a Jekyll Studio page.

## Purpose

The page compares thumbnail WebP output settings using source images from:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/thumbnail-quality-preview/
```

The comparison is isolated from production thumbnails. It writes preview images under `assets/studio/img/thumbnail-quality/` and page data to `assets/studio/data/thumbnail_quality_preview.json`.

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

The `Refresh` button calls the local Catalogue Write Server endpoint:

```text
POST /studio/api/catalogue/thumbnail-quality-preview
```

The endpoint reruns `scripts/media/build_thumbnail_quality_preview.py` and rewrites the preview JSON and referenced preview images.

If the local Studio app catalogue API is unavailable, the page still loads the last generated preview data when present, but the refresh command reports that the service must be started.
The old sibling catalogue refresh URL is no longer used by the local app route.

## Manual Command

Preview planned writes:

```bash
./scripts/media/build_thumbnail_quality_preview.py
```

Write preview assets and data:

```bash
./scripts/media/build_thumbnail_quality_preview.py --write
```

Write only missing preview images while refreshing the JSON:

```bash
./scripts/media/build_thumbnail_quality_preview.py --write --missing-only
```

## Boundaries

The page does not change:

- `assets/works/img/`
- `assets/work_details/img/`
- production thumbnail configuration
- catalogue source JSON
- remote media storage
