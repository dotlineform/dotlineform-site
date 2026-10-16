---
draft: false
doc_id: d-20261016-105517-a6c392
title: Discovery Refresh And Maintenance Rebuild
added_date: "2026-10-16 10:55:17"
last_updated: "2026-10-16"
parent_id: d-20260428-000000-f5ff18
---
# Discovery Refresh And Maintenance Rebuild

Parent: [Planned Features](../Planned_Features.md). Durable operation ownership: [Builder](../Builder.md#working-rebuild).

## Current And Next State

Implemented and reviewed on 2026-10-16; active pending manual normal-use acceptance. Manage replaces broad Rebuild with Refresh Search and Recent; complete Working regeneration uses an explicit maintenance CLI. Exact displayed-document Rebuild remains. Pending publication selections survive unchanged generation.

Next: restart the Docs Viewer service, reload the reader and exercise normal-use acceptance. No test work was authorised or performed; live generation, publication, commit and deployment were outside the selected implementation evidence.

## Requirements

- Refresh shares saved metadata selection and Search's selected source reads with Recent. Preserve configured coverage, inherited Draft/unpublishable exclusion and Recent's exact exclusions/limit. Ordinary Index metadata lacks dates, so carry already parsed ordinary source dates into Recent rather than adding another file/read pass.
- The browser owns the action, busy lifetime and Search/Recent cache refresh. Python owns indexing and persistence. Refresh does not render documents, run media producers, regenerate Catalogue, refresh Index/document display, project browser configuration or record a complete-build receipt.
- Maintenance retains complete ordinary/non-Catalogue source/media/relationship/document generation, exact affected dependencies, Selected, discovery, browser configuration and completion. Catalogue's normal generation and Work queue remain Regenerate-owned.
- Complete builds select changed document output, required additions/withdrawals/dependencies and media-only changes. Compare exact referenced Working media against local Preview bytes only where unchanged document output has not already selected the unit. Carry writer comparisons forward, preserve pending entries and avoid a hash ledger, remote scan or normal-Save media comparison.
- Queue shared output only when its contents change; timestamp-only discovery generation must not cause publication work. Publish remains queue-only.

## Deliverables And Process

Manage sends one empty-object `POST /docs/refresh-discovery`, awaits saved Search/Recent and refreshes only those browser caches. The broad `/docs/rebuild` endpoint/action is retired without an alias. `python3 docs-viewer/build/rebuild_working.py --write` runs full maintenance; explicit `--write` is required and no dry-run planner is added.

## Delivery Steps

### [x] DR.0 — Readiness

Current owners support one shared discovery selection and exact document writer comparisons. Public index/manifests already queue only changes. Media producers report completed identities rather than changed bytes, so maintenance uses the existing local Preview boundary for exact referenced-media comparison. No source/destination inventory or new publication ledger is needed.

Gate: user approved the UI/maintenance split and changed-output queue selection; no separate test specification was approved.

### [x] DR.1 — Implementation And Focused Evidence

- [x] Replace the workspace action/request with discovery refresh and remove broad UI reload plumbing.
- [x] Expose full maintenance through a CLI; preserve document Rebuild and Catalogue boundaries.
- [x] Carry changed document IDs and actual shared-output changes into queue selection; handle media-only changes and preserve pending selections.
- [x] Finish static/import checks and durable ownership updates.

Verification budget: changed Python/JavaScript lint and Python compilation address syntax/import/unused wiring, with CLI/service `--help` diagnostics for entrypoint imports; expected seconds and local bytecode only. Source/diff review covers queue effects and frontend/server responsibilities. All JavaScript changes are local management files outside the public projection inventory, so no public artifact copy is needed. No tests, browser automation, live builds or publication are included.

Record: explicit lint passed for thirteen changed/new Python files and six local management JavaScript files; all thirteen Python files compiled. `rebuild_working.py --help`, `build_search.py --help` and direct management/discovery service imports passed, without running generation. `git diff --check` passed. Builder, endpoint, Search/Recent contract, source workflow, M.20/M.21, README and durable checklist now describe the split. These are static/import diagnostics, not executed refresh/rebuild behavior.

### [x] DR.2 — Code Review

Apply [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) to empty/unchanged paths, media-only changes, pending entries, withdrawals/restorations, exact dependencies, partial failures and the reused Search/Recent writers. Record findings and the necessary retained boundaries here.

Record: distinct bounded source/diff review traced the frontend request and cache refresh, shared discovery selection, stable-content writes, full/targeted generation handoffs, eligibility effects and existing Catalogue boundaries. It removed unused broad Index/document reload callbacks and Search's unnecessary import through the complete document-builder facade. Recent reuses known ordinary source dates instead of introducing another saved index or read pass. Changed Selected completion now queues immediately before later discovery phases, retaining its completed effect on a later failure. Existing pending units are carried forward; newly eligible documents and actual withdrawals remain selected even when document bytes match. Targeted Save/Rebuild retain their media-read-free queue handoff.

Retained boundaries: decoded saved JSON and selected source parsing; configured owners and confined paths/symlinks; required-input failures; existing producer sanitization/verification and transfer checks. The only new media-byte reads compare exact unchanged-document references with local Preview during maintenance, in bounded chunks and without cross-document caching, remote access, a ledger or directory scan. Missing Preview media selects publication; missing Working media fails. No downstream content/schema audit, freshness check, compatibility alias or recovery layer was added. Tests referencing the retired broad action/route remain unchanged and unrun; their migration needs its own specification.

### [ ] DR.3 — Closeout

- [x] Record completed static/import evidence at its actual scope.
- [ ] Obtain user manual acceptance: refresh visible Search/Recent, repeat unchanged refresh, maintenance with unchanged output and media-only changes, eligibility effects and subsequent Publish.

No live generation, tests or Publish has run. Restart the Docs Viewer service and reload its reader before manual review; Git actions and deployment remain separate.
