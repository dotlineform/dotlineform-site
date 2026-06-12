---
doc_id: public-static-site-build-batch-01-audit
title: Public Static Site Build Batch 1 Audit and Pre-Migration Decisions
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 1 Audit and Pre-Migration Decisions

This is the delivery specification for Batch 1 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: produce the inventories and decisions needed before static-builder implementation begins.

## Steer for these tasks

- This batch must resolve the flexible wording called out in [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build).
- No production deploy path changes belong in this batch.
- Do not delete active Jekyll-era files in this batch. Deletion of dead files requires audit evidence, a named file list, and proportional verification.
- The output must be compact decision/audit records consumed directly by later batches.
- The next batch must use this batch's audit output to refine builder module boundaries, copy allowlists, and verification commands.

## Deliverables

- A pre-implementation decision record in this batch document.
- A public-route inventory tied to [Public Route Model](/docs/?scope=studio&doc=public-route-model).
- A Jekyll responsibility inventory covering `_config.yml`, `_layouts/`, `_includes/`, Liquid route pages, wrappers, and GitHub Pages assumptions.
- A public artifact inventory covering route HTML outputs, public assets, generated public data, public Docs Viewer runtime/config/static files, root artifacts, and files that must never publish.
- A verification and source-leak audit seed list for later automation.
- A named list of small cleanup edits for dead files or stale docs. Batch 1 records this list but does not perform the cleanup.

## Implementation and policy guidance

- Start from current code and generated public inputs, not historical request text.
- Record decisions before implementation when current docs and source scans provide enough evidence.
- Record audit findings before implementation when the answer depends on current file usage.
- Keep GitHub Pages as the host and GitHub Actions artifact deployment as the production direction.
- Keep generated public output untracked on `main`.
- Do not introduce a parallel Jekyll fallback path.

## Proposed verification set

- `git diff --check -- docs-viewer/source/studio/public-static-site-build-implementation-plan.md docs-viewer/source/studio/public-static-site-build-batch-*.md`
- Focused scans used by the audit, recorded in the completed verification section.
- Public Jekyll build is required when this batch changes active public route templates, includes, layouts, or config.

## Tasks

### Batch 1: Audit and Pre-Migration Decisions

| ID | status | action |
| --- | --- | --- |
| 1.1 | planned | Inventory all public route pages and classify each route as static page, catalogue shell, Docs Viewer shell, search shell, root artifact, or intentionally excluded route. |
| 1.2 | planned | Compare the route inventory with [Public Route Model](/docs/?scope=studio&doc=public-route-model), and record any route exclusions or gaps that need a pre-implementation decision. |
| 1.3 | planned | Inventory `_layouts/`, `_includes/`, and Liquid-rendered public route pages; name the static-builder render helper or component that will replace each item. |
| 1.4 | planned | Inventory public-site values currently read from `_config.yml`; classify each as public-site config, domain-owned config, generated-data config, or obsolete Jekyll-only setting. |
| 1.5 | planned | Inventory public Docs Viewer files that must remain deployable from `/docs-viewer/...`, including runtime modules, static CSS, public defaults, public route config, and generated public docs/search payloads. |
| 1.6 | planned | Inventory public catalogue/search/moment/work payloads and media path config that the static builder must copy or reference. |
| 1.7 | planned | Inventory site-root publishing artifacts, including `CNAME`, favicon files, `apple-touch-icon` files, `safari-pinned-tab.svg`, `site.webmanifest`, and `404.html`; record missing or deliberately excluded artifacts explicitly. |
| 1.8 | planned | Inventory source-only paths that must never appear in the public artifact, including Studio, Analytics app internals, Docs Viewer services/source/build internals, logs, local config, caches, and generated private docs payloads. |
| 1.9 | planned | Decide whether file-based HTML snippets are allowed in the builder; if allowed, list the snippets and owners, otherwise record that rendering must use Python helpers only. |
| 1.10 | planned | Decide whether CI uses `_public_site/` or an isolated temporary output path; record the exact path policy for local build, preview, CI verification, and Pages artifact upload. |
| 1.11 | planned | Name the exact artifact-content validation command or audit script expected for the GitHub Actions workflow. |
| 1.12 | planned | Decide whether workflow permissions, Pages environment, deploy triggers, or concurrency differ from the request defaults; record each deviation or confirm no deviations. |
| 1.13 | planned | Identify stale Jekyll/Ruby/Liquid references in source docs, scripts, workflow files, and operator commands that need rewrite during closeout. |
| 1.14 | planned | Convert audit findings into follow-on task updates for Batches 2-6, adding detail where the current plan is intentionally coarse. |

## completed verification

- Not started.

## follow-on tasks

- Refine Batches 2-6 with exact module boundaries, copy allowlists, route lists, audit commands, and smoke targets after Batch 1 closes.

## batch close

- Add a handoff note to [Batch 2](/docs/?scope=studio&doc=public-static-site-build-batch-02-builder-skeleton).
- Set this batch status and front matter `ui_status` to `done` after decisions, inventories, and follow-on task updates are complete.
