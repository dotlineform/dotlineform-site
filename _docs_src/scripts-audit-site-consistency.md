---
doc_id: scripts-audit-site-consistency
title: "Site Consistency Audit"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: scripts
sort_order: 130
---
# Site Consistency Audit

Script:

```bash
./scripts/audit_site_consistency.py --strict
```

Run an audit across generated pages and JSON:

```bash
./scripts/audit_site_consistency.py --strict
```

Scope and output options:

```bash
./scripts/audit_site_consistency.py \
  --checks cross_refs,schema,json_schema,links,media,orphans \
  --series-ids collected-1989-1998 \
  --json-out /tmp/site-audit.json \
  --md-out _docs_src/audit-latest.md \
  --strict
```

Single check:

```bash
./scripts/audit_site_consistency.py \
  --check-only schema \
  --max-samples 10
```

Multiple repeated checks:

```bash
./scripts/audit_site_consistency.py \
  --check-only cross_refs \
  --check-only json_schema \
  --series-ids collected-1989-1998
```

## Current Checks

- `cross_refs`: validates key references across `_works`, `_series`, `_work_details`, `assets/data/series_index.json`, and `assets/works/index/*.json`, including duplicate IDs
- `schema`: validates required front matter fields by collection and format and consistency checks
- `json_schema`: validates generated JSON structure and count consistency for:
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/works/index/*.json`
- `links`: validates sitemap source and URL-target query-contract sanity across generated pages
- `media`: validates expected local thumbs for published `_works` and `_work_details`
- `orphans`: reports orphan pages and JSON, with optional orphan media via `--orphans-media`

## `--strict`

- exits non-zero when audit errors are found
- warnings do not fail the run under `--strict`
- without `--strict`, the audit is informational and exits zero

## Query Contract Used By `links`

| flow | produced query keys | destination accepts |
| --- | --- | --- |
| `series -> work` | `series`, `series_page` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |
| `works index -> work` | `from`, `return_sort`, `return_dir`, `return_series` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |
| `work -> work_details index` | `from_work`, `from_work_title`, `section`, `section_label`, `series`, `series_page` | `sort`, `dir`, `from_work`, `from_work_title`, `section`, `section_label`, `series`, `series_page` |
| `work -> work_details page` | `from_work`, `from_work_title`, `section`, `details_section`, `details_page`, `series`, `series_page` | `from_work`, `from_work_title`, `section`, `series`, `series_page`, `details_section`, `details_page`, `section_label` |
| `work_details page -> work` | `series`, `series_page`, `details_section`, `details_page` | `series`, `series_page`, `from`, `return_sort`, `return_dir`, `return_series`, `details_section`, `details_page` |

Optional orphan-media scan:

```bash
./scripts/audit_site_consistency.py \
  --check-only orphans \
  --orphans-media
```

Markdown report defaults to `_docs_src/audit-latest.md`.

## Source And Target Artifacts

Source artifacts checked by the current audit include:

- `_works/*.md`
- `_series/*.md`
- `_work_details/*.md`
- `_moments/*.md`
- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/works/index/*.json`
- `assets/studio/data/tag_assignments.json`
- generated URLs and media paths referenced by those artifacts

Target artifacts:

- terminal report
- optional JSON report via `--json-out`
- optional Markdown report via `--md-out`

## Known Limits

- `media` assumes primaries and work download files are remote or staged and checks local thumbs only
- `json_schema` validates structure and counts, not recomputed payload hash integrity
- `links` query-contract checks are static sanity checks and do not execute browser flows
- orphan checks currently focus on works, series, and work-details artifacts

Warning policy:

- treat schema warnings as backlog by default

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
