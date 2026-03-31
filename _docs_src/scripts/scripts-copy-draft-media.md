---
doc_id: scripts-copy-draft-media
title: Copy Draft Media
last_updated: 2026-03-30
parent_id: scripts
sort_order: 30
---

# Copy Draft Media

Script:

```bash
./scripts/copy_draft_media_files.py
```

Unified script with mode flags:

```bash
./scripts/copy_draft_media_files.py --mode work --ids-file /tmp/work_ids.txt --copied-ids-file /tmp/copied_work_ids.txt --write
./scripts/copy_draft_media_files.py --mode work_details --ids-file /tmp/detail_uids.txt --copied-ids-file /tmp/copied_detail_uids.txt --write
./scripts/copy_draft_media_files.py --mode moment --ids-file /tmp/moment_ids.txt --copied-ids-file /tmp/copied_moment_ids.txt --write
```

## Flags

- `--mode work|work_details|moment`
- `--ids-file`: optional filter manifest, one ID per line
- `--copied-ids-file`: optional output manifest of successfully copied IDs
- `--write`: perform the copy; omit for dry-run
- `--keep-ext` or `--no-ext`: keep or remove the source extension in the copied filename

## Related References

- [Scripts Overview](/docs/?scope=studio&doc=scripts-overview)
- [Main Draft Pipeline](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
