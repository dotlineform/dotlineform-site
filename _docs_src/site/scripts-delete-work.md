---
doc_id: scripts-delete-work
title: Delete Work
last_updated: 2026-03-30
parent_id: scripts-overview
sort_order: 60
---

# Delete Work

Script:

```bash
./scripts/delete_work.py --work-id 00123
./scripts/delete_work.py --work-id 00123 --write
```

## Behavior

- dry-run by default; pass `--write` to apply changes
- requires exactly one `--work-id`
- only proceeds when worksheet `Works` in `data/works.xlsx` has `status=delete` for that work
- on successful `--write`, updates `Works.status` to `deleted`
- deletes:
  - `_works/<work_id>.md`
  - `_work_details/<work_id>-*.md`
  - `assets/works/index/<work_id>.json`
  - removes the work from `assets/data/series_index.json`
  - removes the work from `assets/data/works_index.json`
  - removes per-work overrides from `assets/studio/data/tag_assignments.json`
- if a deleted work is referenced by a series `primary_work_id`, that field is set to `null`

Intentionally left untouched:

- `assets/work_details/img/*`
- canonical work prose under `<DOTLINEFORM_PROJECTS_BASE_DIR>/projects/<project_folder>/<paths.source_subdirs.prose>/<work_prose_file>`
- staged media under `$DOTLINEFORM_MEDIA_BASE_DIR/works/files/<work_id>-*`

## Backups

- `--write` creates timestamped backups under `var/delete_work/backups/YYYYMMDD-HHMMSS/`
- backups preserve repo-relative paths for modified and deleted files so they can be restored manually if needed

## Related References

- [Scripts Overview](/docs/?scope=studio&doc=scripts-overview)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
