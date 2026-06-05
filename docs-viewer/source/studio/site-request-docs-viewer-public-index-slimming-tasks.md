---
doc_id: site-request-docs-viewer-public-index-slimming-tasks
title: Docs Viewer Public Index Slimming Tasks
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: planned
parent_id: site-request-docs-viewer-public-index-slimming
viewable: true
---
# Docs Viewer Public Index Slimming Tasks

This is the tracker for implementing [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming).

When the work is complete, move durable architecture notes into the owning Docs Viewer docs, then close out this tracker and the parent request.

### baseline verification set

Run only the checks warranted by the touched slice.
The final cutover should include:

- Core checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick`.
- Docs Viewer smoke checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`.
- Public Jekyll build check: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`.
- Public route checks for `/library/` and `/analysis/` when route config, generated payload locations, route shells, or public Docs Viewer runtime behavior changes.
- Focused Python syntax/import checks for changed builders, services, smoke scripts, and tests.
- Focused JavaScript syntax/import checks for changed Docs Viewer runtime modules.
- Focused tests for generated-output contracts, search build inputs, scope lifecycle, by-id payload shaping, and Docs Viewer route loading when those areas change.

Codex sandbox note: local service, browser, and temporary localhost checks will need elevated permissions even when the product code is healthy.

### general steer

- Keep public Docs Viewer routes read-only and free of management/tooling metadata.
- Move public and manage navigation to build-time `index-tree.json` payloads with the same data structure.
- Move recently-added to a small build-time payload; do not add date-only fields to tree rows to support recently-added.
- Hydrate info-panel metadata from selected by-id payloads, not public tree/index rows.
- Retire public flat `index.json` from the Docs Viewer route contract only after tree, selected-document, search, and recently-added dependencies have moved.
- Preserve the public/manage entrypoint boundary; do not move management controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared public adapters.
- Follow [Development Checklist](/docs/?scope=studio&doc=development-checklist). Compatibility aliases, dual-read fallbacks, and old-path shims are not acceptable end states.
- Source docs should be updated; generated Docs Viewer payloads should not be rebuilt unless an implementation or verification step explicitly requires that follow-through.

## Implementation Tasks

Work through the batch table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

Each batch is described in its own sibling document.
Task rows inside each batch use scoped IDs such as `1.1`, `1.2`, and `2.1`.

| Batch ID | status | title |
| --- | --- | --- |
| 1 | done | [Batch 1: Discovery and Contract Lock](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-1) |
| 2 | done | [Batch 2: Builder Outputs](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-2) |
| 3 | done | [Batch 3: Runtime Loading and Boundary Check](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-3) |
| 3a | done | [Batch 3a: Smoke Test Diet](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-3a) |
| 4 | done | [Batch 4: Info Panel Hydration and Rendering](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-4) |
| 5 | planned | [Batch 5: Public Flat Index Retirement](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-5) |
| 6 | planned | [Batch 6: Verification](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-6) |
| 7 | planned | [Batch 7: Documentation and Closeout](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-batch-7) |

### closeout coverage

Batch 7 owns the template closeout duties:

- update docs
- cleanup confirmation
- final verification record
- close out this tracker and the parent request

## Closeout Notes

- Batch 1 completed discovery and contract lock. Generated payloads were not rebuilt.
- Batch 2 added build-time compact tree/recent payload generation, scope lifecycle manifest records for those outputs, and search builder source-root inputs that no longer read retired public docs `index.json`. Codex did not manually run a write rebuild; the running docs watcher regenerated affected Studio payloads after source-doc edits.
- Batch 4 moved info-panel metadata hydration to selected by-id payloads, split public reader metadata rendering from manage metadata rendering, and narrowed public by-id payload metadata without rebuilding generated payloads.

## Verification Log

- 2026-06-05: Batch 1 source review and scoped `rg` audit completed; no executable code changed.
- 2026-06-05: Batch 2 syntax checks, focused pytest, Studio docs dry run, and Studio search dry run passed.
- 2026-06-05: Batch 3 syntax checks, focused pytest, Docs Viewer app-shell smoke, service manage smoke, management workflows smoke, and Studio docs dry run passed.
- 2026-06-05: Batch 3a syntax checks and reduced Docs Viewer smoke profile passed.
- 2026-06-05: Batch 4 syntax checks, focused generated-output pytest, metadata info module smoke, and reduced Docs Viewer smoke profile passed.
