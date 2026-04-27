---
doc_id: scripts-srcset-builder
title: "Srcset Builder"
added_date: 2026-03-31
last_updated: 2026-04-27
parent_id: scripts
sort_order: 50
---
# Srcset Builder

Stable shell entrypoint:

```bash
bash scripts/make_srcset_images.sh
```

The shell entrypoint remains stable, but it delegates to the shared config-driven Python implementation.

The current Studio scoped build path for work and work-detail images no longer requires this standalone entrypoint. It stages source images under `var/catalogue/media/`, generates primary and thumbnail derivatives there, and copies thumbnails into `assets/` automatically. This script remains available for explicit/manual srcset runs and deprecated pipeline compatibility.

Works example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_work_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/work_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/works/srcset_images" \
  4
```

Moments example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_moment_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/moment_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/make_srcset_images" \
  "$DOTLINEFORM_MEDIA_BASE_DIR/moments/srcset_images" \
  4
```

Moment source discovery uses the configured moments images directory plus a fixed source filename of `<moment_id>.jpg`.
If that source file is missing, the copy step skips it.

## Flags And Arguments

Shell entrypoint arguments:

- positional `INPUT_DIR`
  - source images folder
- positional `OUTPUT_DIR`
  - derivative output root
- positional `JOBS`
  - parallel worker count
- `--dry-run`
  - preview derivative writes and source cleanup only

Runtime defaults are resolved from `_data/pipeline.json` plus env vars, especially:

- `DOTLINEFORM_MEDIA_BASE_DIR`
- `MAKE_SRCSET_JOBS`
- `MAKE_SRCSET_WORK_IDS_FILE`
- `MAKE_SRCSET_SUCCESS_IDS_FILE`

## Source And Target Artifacts

Source artifacts:

- staged source files under `DOTLINEFORM_MEDIA_BASE_DIR`
  - `works/make_srcset_images/`
  - `work_details/make_srcset_images/`
  - `moments/make_srcset_images/`
- optional selected-ID manifest via `MAKE_SRCSET_WORK_IDS_FILE`

Target artifacts:

- derivative image trees under `DOTLINEFORM_MEDIA_BASE_DIR`
  - `works/srcset_images/`
  - `work_details/srcset_images/`
  - `moments/srcset_images/`
- optional success-ID manifest via `MAKE_SRCSET_SUCCESS_IDS_FILE`

The builder writes image derivatives only. It does not update workbook rows or generate page/JSON artifacts directly.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
