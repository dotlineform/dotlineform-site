---
draft: false
doc_id: d-20261017-000000-c6a58d
title: Index Child Sorting
added_date: "2026-10-17"
last_updated: "2026-10-17"
parent_id: d-20260428-000000-f5ff18
---
# Index Child Sorting

Parent: [Planned Features](../Planned_Features.md). Durable owners: [Runtime](../Docs_Viewer_Runtime.md) for actions and [Builder](../Builder.md) for generation boundaries.

## Current And Next State

Implemented and reviewed on 2026-10-17; awaiting user normal-use acceptance. The user approved Sort Children A–Z, a shared navigation-only path for same-parent Position, retained reparenting effects and omission of the child-membership audit.

Next: restart the Docs Viewer service and reload Manage, then exercise sorting, same-parent Position and reparenting through normal use. Live document/queue writes and Publish were not exercised by Codex.

## Requirements And Deliverables

- [x] Add Sort Children A–Z beside Position in the ordinary Index context menu. Sort immediate children, including collapsed branches, preserving each complete subtree. Use English case/accent-insensitive natural numeric title order and preserve existing order for equivalent titles. The operation saves a one-off order; later authoring does not automatically resort.
- [x] The browser owns selection, sorting, fewer-than-two-children availability and busy/Source-editing gates. Send one exact parent and complete ordered child-ID list. Python owns configured hierarchy/navigation persistence, with request parsing and path confinement but no child-membership audit, title reads or server sorting.
- [x] Share navigation-only completion with same-parent Position. Reorder saved management/public trees using existing public membership; queue only changed public navigation and preserve pending selections. Unchanged order performs no writes. Keep by-ID, Markdown, rendering, media, policy, Selected, Search and Recent work out of this path.
- [x] Reparenting retains parent-field projection and affected public eligibility/document preparation. Preserve source bytes/dates and content HTML unless newly eligible content requires its owning renderer. Position does not change Selected rows, so omit its unnecessary Selected read/queue for reparenting too.
- [x] Preserve the displayed document, Index selection/expansion and focus restoration through the existing Index refresh owner. Surface persistence/navigation/display failures without rollback, retries or a new ledger.

## Delivery Steps

### ICS.0 — Readiness

- [x] Confirm existing menu/action availability, browser child/title state, canonical hierarchy and completed navigation/publication owners.

Record: ready. The browser has the complete child group and titles. Position currently loads rendering configuration and the moved by-ID payload even when its parent stays unchanged. Saved public membership can be preserved for ordering. Reparenting remains the boundary where eligibility can change. No test specification was requested or approved.

### ICS.1 — Implementation And Focused Evidence

- [x] Implement the action, narrow ordered-child endpoint and shared navigation completion.
- [x] Split same-parent Position from reparenting and update current documentation.
- [x] Run focused static checks.

Verification budget: changed-path JavaScript/Python lint, Python compilation, whitespace, the existing service CLI's `--help` import/startup diagnostic and bounded source/diff review. These check syntax, imports/style and operation wiring at small local cost; compilation/lint may write ignored caches, with no live document, queue, media or network writes. The CLI diagnostic parses help and exits before binding a port or loading the workspace. All changed runtime modules are management-only and outside the public projection inventory. Tests, fixtures, temporary regression scripts, browser automation, live management actions and Publish are outside this evidence. Manual acceptance covers menu availability, title order/ties, subtree preservation, same-parent Position, reparenting eligibility and retained reading/Index state.

Record: `bin/lint-js` passed for all six changed management modules. `bin/lint-python` and `python3 -m py_compile` passed for navigation completion, Position, routes, dispatcher and write follow-through; the review corrections passed focused lint/compilation again for navigation completion, Position and hierarchy helpers, covering all six changed Python files. `git diff --check` passed. `python3 docs-viewer/services/docs_viewer_service.py --help` passed with the configured environment and no service startup. The shared path reads each saved navigation tree once, changes only the selected sibling array and reads/saves the queue only for a changed public projection. Rendering setup and Markdown/by-ID/Selected reads remain outside it. These are static/import results, not executed mutation or UI evidence.

### ICS.2 — Code Review

- [x] Review the final bounded diff and reused helpers after static evidence.
- [x] Complete the mandatory Redundancy And Defensive Behavior Review and record findings, resolutions and retained safeguards.

Record: the separate post-evidence review traced menu dispatch, busy/Source/count gates, canonical lookup/insertion, root and nested sibling groups, excluded public parents/children, unchanged order, queue merging, Index refresh/focus and conditional reparenting. No membership, title, duplicate-ID, freshness or corpus audits were added to sorting. Existing node lookups resolve the exact selected parent and map supplied IDs to existing nodes; file parsing, authoring/route/origin authority and configured path/symlink confinement remain at their actual boundaries. Destination/cycle checks remain Position's existing placement boundary. Saved aggregate trees must be read/serialized to persist their changed child array; this is no corpus source scan or content rebuild. Per-file atomic writes and invalidation of an affected complete-build receipt preserve existing persistence behavior, without multi-file rollback, retry state or a new ledger.

Review findings resolved: remove the now-unused move wrapper after confirming it has no callers; reuse the resolved sibling list and placement result instead of repeating node lookup; skip the unrelated source-directory existence preflight; consume successful Position handoffs without a duplicate browser response audit; omit Selected reads/requeueing for all Position operations because its rows do not change. Reuse the narrow JSON serializer and label same-parent failure completion as navigation. Changed code contains no compatibility aliases. These findings have source/diff evidence; mutation, failure and presentation scenarios remain manual and unexercised.

### ICS.3 — Closeout

- [x] Reconcile implementation and evidence claims; record remaining manual gates.
- [ ] Record user normal-use acceptance.

Record: implementation and review complete; manual acceptance remains. No tests were created, changed or run. No live management action, Build, Search refresh, media work, Publish, public runtime projection, commit or push ran. Only management modules changed, so no `site-code-update` projection is required. Repository documentation is maintained directly and was not regenerated into Working output.
