---
doc_id: scripts-fix-missing-title-sort
title: "Legacy Title Sort Fix"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: scripts
sort_order: 140
---
# Legacy Title Sort Fix

Script:

```bash
python3 ./scripts/fix_missing_title_sort.py
```

Generated site JSON no longer persists `title_sort`.
This helper remains only for older or hand-authored `_works` front matter that still uses that field.

Dry-run:

```bash
python3 ./scripts/fix_missing_title_sort.py
```

Write changes:

```bash
python3 ./scripts/fix_missing_title_sort.py --write
```

Scope to selected IDs or ranges:

```bash
python3 ./scripts/fix_missing_title_sort.py \
  --work-ids 66-74,38,40 \
  --write
```

## Flags

- `--site-root PATH`
  - override site-root path
- `--work-ids LIST`
  - comma-separated work IDs or ranges
- `--write`
  - apply changes; omit for dry-run
- `--max-samples N`
  - limit sample IDs printed in the summary

## Source And Target Artifacts

Source artifacts:

- `_works/*.md`

Target artifacts:

- updated `_works/*.md` front matter where numeric-title rows are missing `title_sort`

This helper does not touch generated JSON, workbook data, or other collections.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
