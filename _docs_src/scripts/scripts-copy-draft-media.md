---
doc_id: scripts-copy-draft-media
title: Copy Draft Media
last_updated: 2026-04-01
parent_id: scripts
sort_order: 30
---

# Copy Draft Media

Script:

```bash
python3 ./scripts/copy_draft_media_files.py
```

Unified script with mode flags:

```bash
python3 ./scripts/copy_draft_media_files.py --mode work --ids-file /tmp/work_ids.txt --copied-ids-file /tmp/copied_work_ids.txt --write
python3 ./scripts/copy_draft_media_files.py --mode work_details --ids-file /tmp/detail_uids.txt --copied-ids-file /tmp/copied_detail_uids.txt --write
python3 ./scripts/copy_draft_media_files.py --mode moment --ids-file /tmp/moment_ids.txt --copied-ids-file /tmp/copied_moment_ids.txt --write
```

## Flags

- `--mode work|work_details|moment`
- `--ids-file`: optional filter manifest, one ID per line
- `--copied-ids-file`: optional output manifest of successfully copied IDs
- `--write`: perform the copy; omit for dry-run
- `--keep-ext` or `--no-ext`: keep or remove the source extension in the copied filename

## Source And Target Artifacts

Source artifacts:

- workbook:
  - `data/works.xlsx` for `work` and `work_details`
- source media roots resolved from `_data/pipeline.json` and local env vars:
  - works:
    - `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<project_folder>/<project_filename>`
  - work details:
    - `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<project_folder>/<project_subfolder>/<project_filename>`
  - moments:
    - source records come from `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md`
    - source image lookup defaults to `<DOTLINEFORM_PROJECTS_BASE_DIR>/moments/images/<moment_id>.jpg`
    - if front matter sets `image_file`, source image lookup uses that filename instead

Target artifacts:

- staged srcset inputs under `DOTLINEFORM_MEDIA_BASE_DIR`:
  - `works/make_srcset_images/`
  - `work_details/make_srcset_images/`
  - `moments/make_srcset_images/`
- optional copied-ID manifest written by `--copied-ids-file`

The script prepares source files for the later srcset step. It does not generate site JSON or page files itself.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
