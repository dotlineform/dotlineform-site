# Scripts Overview

Use this interpreter for all commands:

```bash
/Users/dlf/miniconda3/bin/python3
```

All commands below assume you are in `dotlineform-site/`.

## Main Pipeline

Run everything (copy -> srcset -> page generation):

```bash
/Users/dlf/miniconda3/bin/python3 scripts/run_draft_pipeline.py --dry-run
/Users/dlf/miniconda3/bin/python3 scripts/run_draft_pipeline.py
```

Useful flags:

- `--dry-run`: preview only (no workbook writes/deletes)
- `--force-generate`: pass `--force` through to `generate_work_pages.py`
- `--jobs N`: srcset parallel jobs
- `--mode work|work_details|moment`: run only selected flow(s). Repeat flag to run multiple.
- `--work-ids`, `--work-ids-file`: limit work + work_details scope
- `--series-ids`, `--series-ids-file`: pass series scope to generation
- `--moment-ids`, `--moment-ids-file`: limit moment scope
- `--xlsx PATH`: workbook path override
- `--input-dir`, `--output-dir`: works source/derivative dirs
- `--detail-input-dir`, `--detail-output-dir`: work_details source/derivative dirs
- `--moment-input-dir`, `--moment-output-dir`: moments source/derivative dirs

Mode examples:

```bash
/Users/dlf/miniconda3/bin/python3 scripts/run_draft_pipeline.py --mode moment --dry-run
/Users/dlf/miniconda3/bin/python3 scripts/run_draft_pipeline.py --mode work --mode work_details --dry-run
/Users/dlf/miniconda3/bin/python3 scripts/run_draft_pipeline.py --mode moment --moment-ids blue-sky,compiled --dry-run
/Users/dlf/miniconda3/bin/python3 scripts/run_draft_pipeline.py --mode work --work-ids 00456 --dry-run
```

## Individual Scripts

### 1) Copy draft source images from workbook

Unified script with mode flags:

```bash
/Users/dlf/miniconda3/bin/python3 scripts/copy_draft_media_files.py --mode work --ids-file /tmp/work_ids.txt --copied-ids-file /tmp/copied_work_ids.txt --write
/Users/dlf/miniconda3/bin/python3 scripts/copy_draft_media_files.py --mode work_details --ids-file /tmp/detail_uids.txt --copied-ids-file /tmp/copied_detail_uids.txt --write
/Users/dlf/miniconda3/bin/python3 scripts/copy_draft_media_files.py --mode moment --ids-file /tmp/moment_ids.txt --copied-ids-file /tmp/copied_moment_ids.txt --write
```

Flags:

- `--mode work|work_details|moment`
- `--ids-file`: optional filter manifest (one ID per line)
- `--copied-ids-file`: optional output manifest of successfully copied IDs
- `--write`: perform copy (omit for dry-run)
- `--keep-ext` / `--no-ext`: keep/remove source extension in copied filename

### 2) Build srcset derivatives

```bash
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_work_ids.txt \
MAKE_SRCSET_2400_IDS_FILE=/tmp/work_2400_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/work_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/works/make_srcset_images" \
  "/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/works/srcset_images" \
  4
```

Moments example (no 2400):

```bash
: > /tmp/empty_2400_ids.txt
MAKE_SRCSET_WORK_IDS_FILE=/tmp/copied_moment_ids.txt \
MAKE_SRCSET_2400_IDS_FILE=/tmp/empty_2400_ids.txt \
MAKE_SRCSET_SUCCESS_IDS_FILE=/tmp/moment_success_ids.txt \
bash scripts/make_srcset_images.sh \
  "/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/moments/make_srcset_images" \
  "/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/moments/srcset_images" \
  4
```

### 3) Generate Jekyll pages from workbook

```bash
/Users/dlf/miniconda3/bin/python3 scripts/generate_work_pages.py data/works.xlsx
/Users/dlf/miniconda3/bin/python3 scripts/generate_work_pages.py data/works.xlsx --write
```

Common scoped runs:

```bash
/Users/dlf/miniconda3/bin/python3 scripts/generate_work_pages.py data/works.xlsx --work-ids 00456 --write
/Users/dlf/miniconda3/bin/python3 scripts/generate_work_pages.py data/works.xlsx --work-ids-file /tmp/work_ids.txt --write
/Users/dlf/miniconda3/bin/python3 scripts/generate_work_pages.py data/works.xlsx --series-ids curve-poems,dots --write
```

Useful flags:

- `--write`: persist file/workbook changes
- `--force`: regenerate even when checksums match
- `--work-ids`, `--work-ids-file`
- `--series-ids`, `--series-ids-file`
- `--moment-ids`, `--moment-ids-file`
- `--moments-sheet` (default `Moments`)
- `--moments-output-dir` (default `_moments`)
- `--moments-prose-dir` (default `_includes/moments_prose`)
- `--projects-base-dir`: base path used for source-image dimension reads
