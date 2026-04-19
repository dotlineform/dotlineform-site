---
doc_id: backlog
title: Backlog
last_updated: 2026-04-19
parent_id: ""
sort_order: 50
published: false
---
# Backlog

This file tracks active implementation backlog items that are not part of the current published docs set.

Use `_docs_src/ideas.md` for unplanned proposals and architecture directions.

Detailed UI and CSS work stays in:

- `_docs_src/design-backlog.md`

Detailed search architecture proposals stay in:

- `_docs_src/search-config-architecture.md`
- `_docs_src/search-config-implementation-note.md`
- `_docs_src/search-pipeline-target-architecture.md`
- `_docs_src/search-result-shaping.md`

## Active Backlog

- Add CI job(s) to run `scripts/audit_site_consistency.py` on pull requests.
- Decide CI policy for warnings vs errors (`--strict` currently errors-only).
- Add a short contributor checklist for when to run scoped vs full audit checks.
- Add a local front-end for selected repo scripts so common dry-run/write flows can be run without dropping to the terminal.
- Derive a public-facing recent-updates feed from the new build-activity journal, with separate filtering rules from the curator-facing Studio activity page.
- Add automated tests for audit script behaviors (fixtures plus expected findings).
- Extend orphan checks to additional optional media or content domains as needed.
- Review whether route-level shared values such as Studio `studio_page_doc` links should move out of page front matter if more shared route metadata is added.
- Review whether additional checked-in shared config files should move into the documented config layer once they affect normal repo workflows.
- Review the current search ranking and field-participation model once there is enough evidence to justify stronger field policy or tag-aware ranking.
- Decide whether the current search validation flow needs a dedicated schema or artifact-budget check beyond the existing pragmatic validation.
- Continue cleanup of historical and guidance docs so removed section names, legacy routes, and compatibility references do not reappear in the published docs set.

## Later

- Optional JSON content-integrity check:
  - recompute or verify JSON `version` or checksum fields in `assets/data/series_index.json`, `assets/data/works_index.json`, and `assets/works/index/*.json`
- Review whether prose search or additional search payloads are justified enough to expand beyond the current compact base artifacts.
- Review whether any standalone `/search/` scope beyond `catalogue` is warranted, or whether inline docs-viewer search remains the better fit for docs-domain scopes.

## Standing Decisions

- 2026-02-21: Treat `schema` warnings as backlog, not blockers.
- 2026-02-21: `media` audit assumes primaries are remote-hosted and checks local thumbs/downloads only.
- 2026-03-09: UI cleanup should fit the site to shared tokens and primitives rather than preserving local one-off values.
