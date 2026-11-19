---
draft: false
doc_id: d-20260331-154730-b019e0
title: Catalogue Media Pipeline Config
added_date: "2026-03-31 15:47:30"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6

---

# Catalogue Media Pipeline Config

`_data/pipeline.json` owns logical Work-media roots, staging subpaths, rendition names and encoding. `studio/shared/python/pipeline_config.py` loads that policy. The Catalogue resolver applies `paths.media.root_subdir` relative to `$DOTLINEFORM_PROJECTS_BASE_DIR/dotlineform-site/`. The Docs workspace separately owns Working/Preview assets and public destinations. [Pipeline source](../../_data/pipeline.json) · [Loader](../../studio/shared/python/pipeline_config.py) · [Destination configuration](../../docs-viewer/config/workspace/docs-workspace.json)

## Work Media Sources

The logical identities `projects` and `processing` resolve beneath `DOTLINEFORM_PROJECTS_BASE_DIR/projects/` and `processing/`. Canonical Work source omits `media_source_id` for the default `projects` identity. A supplied identity must match configuration. The shared resolver confines the selected folder/file path and rejects symlink traversal. The source identity changes original lookup while generated Work IDs and rendition names stay stable. [Source resolver](../../studio/shared/python/catalogue_work_media_sources.py)

## Save And Refresh

Normal Save calls `catalogue_build_media.py` to prepare the selected original's configured renditions in temporary files. `catalogue_output_media.py` supplies Projects staging as the destination and the current flag-selected staging/Working bytes for comparison. `catalogue_media_version.py` commits the prepared bytes, dimensions, version and flags through the transaction owner.

The editor reads staged bytes when `image_staged` or the download's `staged` flag is true. Refresh hands those exact selected bytes to Working, clears flags and removes the copied staging files. Regenerate and Publish carry the completed version and selection onward. [Save trace](Catalogue_Services.md#follow-a-work-save-and-refresh) · [Media/version lifecycle](Catalogue_Save_And_Refresh.md#work-media-authoring)

The checked primary widths are 800, 1200 and 1600 px, with a 96 px thumbnail and WebP encoding. The pipeline and its consumers own the complete policy. A change to variants can affect generation, filenames, browser references and public transfers, so trace those owners together.

## Thumbnail Colour Conversion

Both active `catalogue_build_media.run_ffmpeg_thumb` and the standalone `make_srcset_images.make_thumb` choose `yuv420p|yuva420p` between Lanczos scaling and the square crop. This avoids the BGRA intermediate involved in the recorded green tint and retains the alpha-capable path. Existing affected images require deliberate image confirmation, Save and Refresh before normal publication. [Converters](../../studio/services/catalogue/catalogue_build_media.py) · [Diagnosis and evidence](../deliveries/Studio_And_Catalogue_Ownership_Review.md#thumbnail-colour-diagnosis)

## Derivative Builder

The standalone utility prepares derivatives from staged inputs for explicit maintenance.

```bash
python3 studio/services/media/make_srcset_images.py INPUT_DIR OUTPUT_DIR JOBS
```

Use `--dry-run` to inspect intended writes/cleanup. Omitted directories use its configured staging paths. Selected/success-ID manifests and the default job count are defined by the pipeline. The utility owns conversion and staged-input cleanup. Normal canonical Save/version completion uses the owners above. [Utility](../../studio/services/media/make_srcset_images.py) · [Separate maintenance transport](Publish_Media_To_R2.md)
