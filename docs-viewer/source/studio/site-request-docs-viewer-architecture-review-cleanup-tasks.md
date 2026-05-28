---
doc_id: site-request-docs-viewer-architecture-review-cleanup-tasks
title: Docs Viewer Architecture Review And Cleanup Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: planned
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14187
viewable: true
---
# Docs Viewer Architecture Review And Cleanup Tasks

This is the review and cleanup child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture). It follows the structural slices that introduced or clarified app session, service boundaries, app composition, runtime API shape, public/manage contexts, and controller/hosted-view lifecycle.

This tracker exists so cleanup notes from those slices have an explicit owner:
- Compatibility paths, broad callbacks, and legacy-style handoffs are red flags until they are removed or converted into named follow-up tasks.
- If a reviewed pattern is actually current architecture, stop describing it as compatibility and document the named owner contract instead.

The cleanup pass should find them now, while the architecture request is active, rather than letting them surface later during unrelated feature work. It should review:
- JavaScript and server-side patterns,
- compatibility scaffolding,
- tests,
- durable docs,
- generated payload status, and
- remaining architecture risks.

## Status

### steer for this task

- Treat this as architecture review and cleanup, not a new feature slice.
- Treat every remaining compatibility path, broad callback bridge, broad state dependency, or legacy JS/server structuring pattern as migration debt until reviewed.
- Resolve reviewed migration debt in this slice when the owner contract is clear; otherwise create a named follow-up task in this document immediately.
- Keep the review grounded in the target Docs Viewer app architecture, not in historical compatibility paths.
- Do not preserve compatibility wording as a neutral description. Name the owner, the replacement contract, and the removal task; if no removal is needed, rename the pattern as current architecture and document why it is not compatibility.
- Do not remove a path blindly; first identify the current callers, replacement owner contract, and focused verification required for removal.
- Do not replace compatibility callbacks with direct endpoint calls from feature modules.
- The cleanup analysis should specifically question whether any legacy JavaScript or server pattern remains that might encourage future developers to add code in the wrong module for its intended purpose.
- Keep public read-only and local manage boundaries explicit while reviewing docs, tests, and runtime contracts.

### cleanup notes from controller/view lifecycle slice

The controller/view lifecycle slice identified these unresolved compatibility paths:

- `docs-viewer-app-runtime.js` remains the compatibility coordinator for focused controller construction, callback handoff, route-global updates, private management startup callbacks, and the intentionally small returned app handle.
- `docs-viewer-app-session.js` keeps `compatibilityBridge.state` because existing controllers still consume the broad state object.
- Route workflow callbacks, search/bookmark route callback bundles, and management runtime adapter callbacks remain private handoffs until a later slice narrows complete controller families to domain and service inputs.

No compatibility fields or lifecycle methods were removed in that slice because it was a documentation and lifecycle-inventory pass. It was not a complete cleanup review. That does not make the remaining paths acceptable as a long-term shape. This review must either:

- remove them,
- create specific cleanup tasks for their removal, or
- rename the pattern as current architecture with a clear owner contract because it is not actually compatibility.

**Additional tasks created as part of this cleanup review should be tracked in the 'Implementation tasks' table below.**

Follow-up decisions to review and expand upon here:

- When a future feature needs an info-panel view, first decide whether it is public metadata, manage metadata, local diagnostics, semantic/reference info, or another separately-shaped view contract.
- When a future controller change touches broad state, narrow one complete controller family to explicit state-domain and service inputs rather than adding another route-runtime callback.

### durable documentation

Record any architecture/ownership changes in the durable owning reference doc, not only in this cleanup tracker.

For this request, the default destinations are:

- [Docs Viewer Runtime Boundary](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/docs-viewer-runtime-boundary.md) for runtime ownership, controller/view lifecycle, public/manage boundaries, service boundaries, and “this is current architecture” contracts.
- [Docs Viewer Overview](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/docs-viewer-overview.md) for the concise app architecture story.
- [Docs Viewer JavaScript Inventory](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/docs-viewer-javascript-inventory.md) for file-specific owner notes and “do not add X here” guidance.
- A service/script-specific doc if the owner contract is server-side, endpoint, generated-read, or write-flow related.

The cleanup tracker should then link to the durable section and mark the finding resolved. It should not be the only place where the owner contract lives.

### baseline verification set

Run only the checks warranted by touched files. Expected cleanup verification candidates:

- JavaScript syntax checks for any runtime modules touched by cleanup.
- Focused app-shell module smoke coverage when owner contracts, app handle shape, state domains, hosted-view lifecycle, or public/manage access contracts are reviewed or changed:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Management modal/service smokes when management lifecycle, lazy loading, generated reads, route state, status projection, import-open-on-load, post-write reload behavior, or write service contracts change.
- Public read-only smoke when public startup, hosted-view lifecycle, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes.
- Docs-only source review when no runtime behavior changes.
- `git diff --check`.

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.

## Review Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory remaining compatibility scaffolding after the structural app architecture slices. Include `docs-viewer-app-runtime.js`, `docs-viewer-app-session.js`, private route/search/bookmark callback bundles, management runtime adapter callbacks, and any tests or docs that still depend on broad compatibility state. Treat each finding as migration debt until reviewed. |
| 2 | planned | Audit legacy JavaScript and server-side patterns that might encourage future developers to place code in the wrong module or bypass the target app architecture. Include broad route/controller files, local service endpoints, management write paths, generated-read paths, and any helper that hides unclear ownership. |
| 3 | planned | Classify each compatibility path or legacy pattern as: remove now, create a named follow-up task now, or rename it as current architecture with a clear owner contract because it is not actually compatibility. Do not leave unresolved compatibility language as an implicit future concern. |
| 4 | planned | Review focused tests for historical compatibility assumptions. Prefer tests that assert current owner contracts, DOM/user-visible behavior, service boundaries, app handle shape, state-domain behavior, hosted-view context, and public/manage separation. |
| 5 | planned | Review durable Docs Viewer docs for compatibility fields described as current public API. Update wording so temporary bridges are named as migration debt, private implementation details, or tracked cleanup tasks. |
| 6 | planned | Review runtime fields kept only for tests. Remove or retarget tests before removing runtime fields; do not keep runtime API solely for test convenience. |
| 7 | planned | Review feature-module access paths. Feature modules should use owner-specific callbacks, state-domain inputs, hosted-view context, generated-data runtime, or management service/controller contracts rather than app/runtime handles. |
| 8 | planned | Create focused cleanup tasks for any controller family that still needs broad state narrowed to explicit state-domain and service inputs. Candidate tasks should avoid widening `docs-viewer-app-runtime.js` and should name the replacement owner contract. |
| 9 | planned | Remove any compatibility path that can be resolved in this review slice. Update focused smoke coverage before or with the removal. If removal is not in this slice, create a named task with the target owner and verification requirement. |
| 10 | planned | Verify public-safe hosted-view constraints still hold: public views mount without management services, backend probes, local generated-read service base URLs, write-capable handles, or management assets. |
| 11 | planned | Verify manage-only and management action constraints still hold: visibility and availability do not imply write authority, and backend writes remain behind management endpoints with server-side validation. |
| 12 | planned | Update owning docs after review: this tracker, the parent request, Docs Viewer Runtime Boundary, Docs Viewer Overview, Docs Viewer JavaScript Inventory, and Docs Viewer Portable File Manifest if runtime copy sets changed. |
| 13 | planned | Run the verification set warranted by touched files and record results, generated payload status, remaining risks, and created follow-up tasks. |
| 14 | planned | Create or update structured docs-log entries for meaningful cleanup or final request closure, then record entry ids here. |

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 |  |  |

## closeout

The closeout for this review should confirm:

- remaining compatibility paths and legacy JS/server patterns are inventoried, classified, and either removed, converted into named tasks, or renamed as current architecture with a named owner contract because they are not actually compatibility
- tests assert current architecture contracts rather than historical compatibility where practical
- durable docs do not leave compatibility wording as a vague future concern
- public-safe and manage-only boundaries remain explicit
- generated-data reads still use generated-data runtime and service-context projection rather than direct endpoint calls from feature modules
- no new source editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
