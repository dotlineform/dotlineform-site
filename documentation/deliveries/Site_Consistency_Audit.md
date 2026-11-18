---
draft: false
doc_id: d-20260331-000000-cdc571
title: Site Consistency Audit
added_date: "2026-03-31 00:00:00"
last_updated: "2026-08-14 21:07:57"
parent_id: d-20261118-235200-9870c4
---
# Site Consistency Audit

Audit of the former standalone Catalogue site, retired with the site suite. The commands below are historical and include scope-era series, Detail and tag checks. [Current Catalogue workflow](../reference/Catalogue_Save_And_Refresh.md) · [Site test retirement](Review_Test_Policy_And_Checks.md#recovery)

## Question It Answers

Does the generated public catalogue still agree with its canonical indexes, route contracts, links, and media expectations?

This is a read-only maintenance audit, not a generator and not a complete browser test.

## Former Commands

```bash
$HOME/miniconda3/bin/python3 studio/tests/audits/catalogue_site_consistency.py --strict
```

The script could narrow findings by check, series or work:

```bash
$HOME/miniconda3/bin/python3 studio/tests/audits/catalogue_site_consistency.py \
  --check-only cross_refs \
  --series-ids collected-1989-1998 \
  --work-ids 66-74
```

The former `--json-out` and `--md-out` flags wrote local snapshots. The old runner put its Markdown snapshot under `var/`.

## Check Families

- `cross_refs` — catalogue indexes, per-work payloads, series membership, and Analytics tag assignments agree.
- `schema` — route IDs and generated catalogue contracts use valid, mutually consistent identifiers.
- `json_schema` — generated series, work, and per-work detail payloads have the expected structure and counts.
- `links` — generated destinations exist and catalogue navigation query keys match the destination contract.
- `media` — expected local catalogue thumbnails are present.
- `orphans` — generated catalogue routes/payloads are still owned; optional media scanning is available through `--orphans-media`.

The former `catalogue_site_consistency.py` is available at the recovery revision for the exact artifact and query rules.

## Interpretation

- `--strict` failed on errors and reported warnings separately.
- Link checks inspected static destinations. JSON checks inspected structure and cross-artifact agreement.
- Media checks inspected expected local variants. Remote transfers used separate validation.
