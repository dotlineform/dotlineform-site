---
doc_id: site-request-canonical-static-site-root-tasks
title: Canonical Static Site Root Migration Tasks
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-canonical-static-site-root
viewable: true
---
# Canonical Static Site Root Migration Tasks

This is the delivery specification for Batch 1 in [Canonical Static Site Root Request](/docs/?scope=studio&doc=site-request-canonical-static-site-root).

Purpose: migrate the public site to tracked `site/` source and move public-site tooling to validation-only `site-tools/`.

## Steer For These Tasks

- Keep the migration direct: no aliases, compatibility layers, redirects, or old command shims.
- Treat `site/` as the static document root. Filesystem path `site/assets/...` serves public URL `/assets/...`.
- Prefer config retargeting over call-site edits when apps already resolve public paths through config.
- Keep `bin/site-validate` limited to deploy-artifact readiness. Do not mix site content audits into deploy validation.
- Keep site audit checks available as separate design-time or general audit responsibilities.
- Keep `site-tools/` simpler than the current public-site build package, while still modularizing Python validation code by responsibility when needed.
- Do not introduce a new generated-payload review or gating copy outside `site/`.

## Deliverables

- Tracked canonical static site root at `site/`.
- Validation-only tooling under `site-tools/`.
- `bin/site-validate` command.
- Direct static preview that serves `site/`.
- Studio, Docs Viewer, Analytics, Data Sharing, Admin audit, and workflow paths retargeted away from root-level `assets/` and `_public_site/`.
- GitHub Actions workflow that validates and uploads `site/`.
- Stable documentation updated for the new public-site root and validation workflow.

## Implementation And Policy Guidance

- The parent request owns the design decisions and should not duplicate implementation task state.
- Public route HTML is canonical source under `site/`; do not add build-time shell generation in this migration.
- Public URLs remain unchanged unless a separate request approves route changes.
- Keep canonical source data outside `site/`; only deployable public files belong there.
- If a hardcoded root-level `assets/` filesystem path is found, either move it into owning config, remove it, or document the reason it remains.
- If an existing test or fixture depends on retired paths, retarget the test rather than adding compatibility.

## Proposed Verification Set

- Focused tests for `bin/site-validate` against `site/`.
- Focused tests for Studio catalogue output path configuration.
- Focused tests for Docs Viewer public publish paths and route config paths.
- Focused tests for Analytics and Data Sharing reads of public catalogue indexes.
- Admin projection-contract or public-surface audit updated for `site/`.
- GitHub Actions workflow syntax or dry-run validation where practical.
- Representative public route smoke checks only when touched implementation warrants browser verification.

## Tasks

### Batch 1: Canonical Static Site Root Migration

| ID | status | action |
| --- | --- | --- |
| 1.1 | planned | Audit root-level `assets/` path ownership: identify config-driven reads/writes, hardcoded defaults, and path configs that must retarget public outputs to `site/assets/...`. |
| 1.2 | planned | Move `_public_site/` to `site/` as tracked canonical source and delete `_public_site/.public-site-artifact` rather than replacing it. |
| 1.3 | planned | Move public-site tooling from `public-site/` to `site-tools/`, simplifying it to validation/audit responsibilities only. |
| 1.4 | planned | Replace `bin/public-site-build` with `bin/site-validate`, with no command alias or compatibility shim. |
| 1.5 | planned | Update preview tooling so it serves `site/` directly and does not rebuild or copy the public tree. |
| 1.6 | planned | Retarget Studio catalogue generators and cleanup paths from root `assets/...` to `site/assets/...`. |
| 1.7 | planned | Retarget catalogue search generation and policy paths to `site/assets/data/search/...`. |
| 1.8 | planned | Retarget Docs Viewer public publish paths from root `assets/...` to `site/assets/...`. |
| 1.9 | planned | Retarget Docs Viewer public route config, browser config, and interactive asset paths for the `site/` root. |
| 1.10 | planned | Retarget Analytics and Data Sharing reads that currently use public catalogue indexes under root `assets/data/...`. |
| 1.11 | planned | Update Admin projection contract and public-surface audits for `site/`. |
| 1.12 | planned | Remove or rename root-level `assets/` once no active consumer remains. |
| 1.13 | planned | Update GitHub Actions to validate and upload `site/`, with no retired build/copy command. |
| 1.14 | planned | Update stable docs that still describe `_public_site/`, `public-site/build/`, or root `assets/` as the public deploy surface. |

## Completed Verification

- Not started.

## Follow-On Tasks

- None yet.

## Batch Close

- When complete, update this task tracker with verification results, remaining risks, and any follow-on tasks discovered during implementation.
- Mark `ui_status` and task statuses only after the corresponding implementation and verification are complete.

