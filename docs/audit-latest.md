# Audit Report

- Run at: `2026-03-05T10:36:25+00:00`
- Duration: `79ms`
- Checks: `cross_refs, json_schema, links`
- Errors: `0`
- Warnings: `2`

## Flags

| flag | value | default? |
| --- | --- | --- |
| `--site-root` | `.` | `yes` |
| `--checks` | `links,cross_refs,json_schema` | `no` |
| `--check-only` | `(none)` | `yes` |
| `--series-ids` | `(empty)` | `yes` |
| `--work-ids` | `(empty)` | `yes` |
| `--strict` | `False` | `yes` |
| `--json-out` | `(empty)` | `yes` |
| `--md-out` | `docs/audit-latest.md` | `yes` |
| `--max-samples` | `20` | `yes` |
| `--orphans-media` | `False` | `yes` |

## Check Summary

- `cross_refs`: errors=0 warnings=0
- `json_schema`: errors=0 warnings=0
- `links`: errors=0 warnings=2

## Findings

### cross_refs

- none

### json_schema

- none

### links

- `works curator index`: sitemap url has no known static target: /works_curator/ (`_data/sitemap.yml`)
- `studio series index`: sitemap url has no known static target: /studio/studio-series/ (`_data/sitemap.yml`)
