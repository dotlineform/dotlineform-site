---
doc_id: scripts-srcset-builder
title: Srcset Builder
added_date: 2026-03-31
last_updated: 2026-07-13
parent_id: studio
viewable: true
---
# Srcset Builder

Python entrypoint:

```bash
$HOME/miniconda3/bin/python3 studio/services/media/make_srcset_images.py
```

The current Studio scoped build path for work and work-detail images no longer requires this standalone entrypoint. It stages source images under `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/`, generates primary and thumbnail derivatives there, and copies thumbnails into `site/assets/` automatically. This script remains available for explicit/manual srcset runs.

Works example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_work_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/work_success_ids.txt \
$HOME/miniconda3/bin/python3 studio/services/media/make_srcset_images.py \
  "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/works/make_srcset_images" \
  "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/works/srcset_images" \
  4
```

Moments example:

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_moment_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/moment_success_ids.txt \
$HOME/miniconda3/bin/python3 studio/services/media/make_srcset_images.py \
  "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/moments/make_srcset_images" \
  "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/moments/srcset_images" \
  4
```

Moment source discovery uses the configured moments images directory plus a fixed source filename of `<moment_id>.jpg`.
If that source file is missing, the copy step skips it.

## Flags And Arguments

Entrypoint arguments:

- positional `INPUT_DIR`
  - source images folder
- positional `OUTPUT_DIR`
  - derivative output root
- positional `JOBS`
  - parallel worker count
- `--dry-run`
  - preview derivative writes and source cleanup only

Runtime defaults are resolved from `_data/pipeline.json` plus `.env.local`, especially:

- `MAKE_SRCSET_JOBS`
- `MAKE_SRCSET_WORK_IDS_FILE`
- `MAKE_SRCSET_SUCCESS_IDS_FILE`

## Source And Target Artifacts

Source artifacts:

- staged source files under `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/`
  - `works/make_srcset_images/`
  - `work_details/make_srcset_images/`
  - `moments/make_srcset_images/`
- optional selected-ID manifest via `MAKE_SRCSET_WORK_IDS_FILE`

Target artifacts:

- derivative image trees under `$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/`
  - `works/srcset_images/`
  - `work_details/srcset_images/`
  - `moments/srcset_images/`
- optional success-ID manifest via `MAKE_SRCSET_SUCCESS_IDS_FILE`

The builder writes image derivatives only. It does not update workbook rows or generate page/JSON artifacts directly.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
