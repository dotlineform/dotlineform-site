# Backlog

This file tracks deferred improvements and follow-up work.

## Now

- Keep `schema` warnings as backlog (do not fail workflow on warnings).
- Continue using audit checks locally before publish/generation changes.

## Next

- Add CI job(s) to run `scripts/audit_site_consistency.py` on pull requests.
- Decide CI policy for warnings vs errors (`--strict` currently errors-only).
- Add a short contributor checklist for when to run scoped vs full audit checks.
- Implement CSS audit script v1 from spec: `docs/css-audit-spec.md`.

## Later

- Optional JSON content-integrity check:
  - recompute/verify JSON `version`/checksum fields in `assets/data/series_index.json`, `assets/data/works_index.json`, and `assets/works/index/*.json`.
- Extend orphan checks to additional content domains (`_themes`, `_research`, optional media domains).
- Add automated tests for audit script behaviors (fixtures + expected findings).

## Decisions

- 2026-02-21: Treat `schema` warnings as backlog (not blockers).
- 2026-02-21: `media` audit assumes primaries are remote-hosted and checks local thumbs/downloads only.
