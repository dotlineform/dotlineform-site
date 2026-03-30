---
doc_id: scripts-fix-missing-title-sort
title: Legacy Title Sort Fix
last_updated: 2026-03-30
parent_id: scripts-overview
sort_order: 100
---

# Legacy Title Sort Fix

Script:

```bash
./scripts/fix_missing_title_sort.py
```

Generated site JSON no longer persists `title_sort`.
This helper remains only for older or hand-authored `_works` front matter that still uses that field.

Dry-run:

```bash
./scripts/fix_missing_title_sort.py
```

Write changes:

```bash
./scripts/fix_missing_title_sort.py --write
```

Scope to selected IDs or ranges:

```bash
./scripts/fix_missing_title_sort.py \
  --work-ids 66-74,38,40 \
  --write
```

## Related References

- [Scripts Overview](/docs/?doc=scripts-overview)
- [Generate Work Pages](/docs/?doc=scripts-generate-work-pages)
