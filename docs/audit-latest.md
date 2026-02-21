# Audit Report

- Run at: `2026-02-21T11:48:40+00:00`
- Duration: `47ms`
- Checks: `links`
- Errors: `0`
- Warnings: `1`

## Flags

| flag | value | default? |
| --- | --- | --- |
| `--site-root` | `.` | `yes` |
| `--checks` | `sort_drift,cross_refs` | `yes` |
| `--check-only` | `links` | `no` |
| `--series-ids` | `(empty)` | `yes` |
| `--work-ids` | `(empty)` | `yes` |
| `--strict` | `False` | `yes` |
| `--json-out` | `(empty)` | `yes` |
| `--md-out` | `docs/audit-latest.md` | `yes` |
| `--max-samples` | `2` | `no` |
| `--orphans-media` | `False` | `yes` |

## Check Summary

- `links`: errors=0 warnings=1

## Findings

### links

- `work->details-index`: query contract mismatch; unsupported keys: details_page, details_section
