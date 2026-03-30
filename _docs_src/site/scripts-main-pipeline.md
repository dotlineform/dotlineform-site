---
doc_id: scripts-main-pipeline
title: Main Draft Pipeline
last_updated: 2026-03-30
parent_id: scripts-overview
sort_order: 20
---

# Main Draft Pipeline

Script:

```bash
./scripts/run_draft_pipeline.py
```

Run everything:

```bash
./scripts/run_draft_pipeline.py --dry-run
./scripts/run_draft_pipeline.py
```

## Useful Flags

- `--dry-run`: preview only, with no workbook writes or deletes
- `--force-generate`: pass `--force` through to `generate_work_pages.py`
- `--jobs N`: srcset parallel jobs; default `4`, or `MAKE_SRCSET_JOBS`
- `--mode work|work_details|moment`: run only selected flow(s); repeat flag to run multiple
- `--work-ids`, `--work-ids-file`: limit work and work-details scope
- `--series-ids`, `--series-ids-file`: pass series scope to generation
- `--moment-ids`, `--moment-ids-file`: limit moment scope
- `--xlsx PATH`: workbook path override
- `--input-dir`, `--output-dir`: works source and derivative dirs
- `--detail-input-dir`, `--detail-output-dir`: work-details source and derivative dirs
- `--moment-input-dir`, `--moment-output-dir`: moments source and derivative dirs

## Mode Examples

```bash
./scripts/run_draft_pipeline.py --mode moment --dry-run
./scripts/run_draft_pipeline.py --mode work --mode work_details --dry-run
./scripts/run_draft_pipeline.py --mode moment --moment-ids blue-sky,compiled --dry-run
./scripts/run_draft_pipeline.py --mode work --work-ids 00456 --dry-run
```

When `--mode work` is used and no `--series-ids*` flags are provided, draft series are auto-included in generation.

## Logging

Per-script logs are written to repo-root log directories and are auto-created as needed.

Current logged scripts:

- `scripts/run_draft_pipeline.py` -> `logs/run_draft_pipeline.log`
- `scripts/generate_work_pages.py` -> `logs/generate_work_pages.log`
- `scripts/delete_work.py` -> `logs/delete_work.log`
- `scripts/studio/tag_write_server.py` -> `var/studio/logs/tag_write_server.log`

Log format:

- JSON Lines, one JSON object per line

Retention policy:

- keep entries from the last 30 days
- if no entries fall inside the last 30 days, keep the latest 1 day's worth based on the newest entry

## Related References

- [Scripts Overview](/docs/?scope=studio&doc=scripts-overview)
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
