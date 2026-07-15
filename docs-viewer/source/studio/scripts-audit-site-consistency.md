---
doc_id: scripts-audit-site-consistency
title: Site Consistency Audit
added_date: 2026-03-31
last_updated: 2026-07-15
parent_id: admin
---
# Site Consistency Audit

## Question It Answers

Does the generated public catalogue still agree with its canonical indexes, route contracts, links, and media expectations?

This is a read-only maintenance audit, not a generator and not a complete browser test.

## Run It

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_site_consistency.py --strict
```

Narrow by check, series, or work when investigating a finding:

```bash
$HOME/miniconda3/bin/python3 admin-app/checks/audit_site_consistency.py \
  --check-only cross_refs \
  --series-ids collected-1989-1998 \
  --work-ids 66-74
```

Use `--json-out` or `--md-out` only when a durable local snapshot helps the investigation. The default Markdown snapshot, when requested by the runner profile, is operational output under `var/`, not Docs Viewer source.

## Check Families

- `cross_refs` — catalogue indexes, per-work payloads, series membership, and Analytics tag assignments agree.
- `schema` — route IDs and generated catalogue contracts use valid, mutually consistent identifiers.
- `json_schema` — generated series, work, and per-work detail payloads have the expected structure and counts.
- `links` — generated destinations exist and catalogue navigation query keys match the destination contract.
- `media` — expected local catalogue thumbnails are present.
- `orphans` — generated catalogue routes/payloads are still owned; optional media scanning is available through `--orphans-media`.

The functions and constants in `audit_site_consistency.py` are the exact current inventory. This page deliberately does not duplicate every artifact or query key.

## Interpretation

- `--strict` fails on errors; warnings remain backlog evidence.
- link checks are static contract checks, not executed navigation.
- JSON checks validate structure and cross-artifact agreement, not every semantic rule or content hash.
- media checks cover the local variants the public catalogue expects; remote/staged publishing has separate validation.
- an old name in an internal finding is not evidence that the old source collection still exists; trace the loader and current generated artifact before acting.

## Change Method

When the public catalogue contract changes:

1. update the generator or canonical source owner;
2. update the corresponding audit loader/check;
3. run the narrow check against current `site/` output;
4. update this summary only if the audit's responsibility or interpretation changes.

Do not paste a fresh exhaustive artifact list here. That simply creates another catalogue schema to maintain.
