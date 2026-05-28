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

- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) for runtime ownership, controller/view lifecycle, public/manage boundaries, service boundaries, and "this is current architecture" contracts.
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview) for the concise app architecture story.
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for file-specific owner notes and "do not add X here" guidance.
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

### Task 1 inventory

Completed 2026-05-28.
This pass inventoried the remaining compatibility scaffolding and broad-state dependencies after the structural app architecture slices.
No runtime behavior was changed in this task; classification, removal, and durable wording cleanup remain owned by later review tasks.

| finding | current owner/dependency | migration-debt note | next review |
| --- | --- | --- | --- |
| Runtime coordinator still assembles focused controllers | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` still constructs route workflow, config, sidebar, document, info panel, search/recent, bookmark, and management controller surfaces. It also owns event binding wrappers, route-global updates, private startup callbacks, pane callbacks, and management reload/startup handoffs. | This remains a compatibility coordinator, not a place for new feature ownership. The returned app handle is already narrow, but the file still passes broad state and callback bundles into controller families. | Tasks 3, 7, 8, and 9 should classify which controller families can move to explicit state-domain and service inputs. |
| App session exposes the broad compatibility state | `docs-viewer/runtime/js/docs-viewer-app-session.js` returns `state`, named `domains`, and `compatibilityBridge.state`. `docs-viewer/runtime/js/docs-viewer-app-composition.js` also keeps `composition.state` as an internal alias for controller construction. | The bridge is explicit and temporary. Existing controllers still receive the broad `state` object instead of complete domain inputs, and tests assert the bridge/state alias. | Tasks 3, 4, 6, and 8 should decide whether test assertions should target domains only and which controller family narrows first. |
| Route workflow remains private but callback-heavy | `docs-viewer/runtime/js/docs-viewer-route-workflow.js` owns URL/history/index/payload flow, while `docs-viewer-app-runtime.js` keeps private wrapper functions such as `loadDoc`, `loadIndex`, `applyCurrentRoute`, `setHistory`, and route-global update handoffs. | The private wrappers preserve the small public app handle, but they still encourage function-scoped bridge growth if future features add one-off route callbacks. | Tasks 3, 7, and 8 should classify route workflow callbacks and name the state-domain/service contract for future route changes. |
| Search/recent callbacks are still compatibility handoffs | `docs-viewer/runtime/js/docs-viewer-search-controller.js` owns search/recent behavior and exports `createDocsViewerSearchRouteCallbacks(...)`, but the controller still consumes broad `state`, `routeCallbacks`, and `paneCallbacks`; it also keeps fallback direct context callbacks. | Search/recent ownership is focused, but the broad state and fallback callback surface remain migration debt until the complete controller family receives explicit search/recent, route, pane, and generated-data inputs. | Tasks 3, 4, 7, and 8 should classify the callback bundle and test contract. |
| Bookmark callbacks are still compatibility handoffs | `docs-viewer/runtime/js/docs-viewer-bookmarks.js` owns bookmark behavior and exports `createDocsViewerBookmarkRouteCallbacks(...)`, but the controller still consumes broad `state`, route callbacks, search input refs, and route-reset behavior. | Bookmark behavior is focused, but opening a bookmark still resets search route state through private callbacks and broad state fields. | Tasks 3, 4, 7, and 8 should classify the callback bundle and decide the bookmark/search route-state contract. |
| Management lazy boundary is clean but context is broad | `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js` gates management import behind route access, but `docs-viewer-app-runtime.js` assembles a large management context including broad `state`, route workflow callbacks, config reload, generated-read reload, status/render callbacks, and management shell refs. `docs-viewer/runtime/js/docs-viewer-management.js` then passes `state` and callback bundles into management action, modal, and scope-lifecycle modules. | The lazy adapter is the current public/manage boundary and should not be removed blindly. The broad management context remains migration debt because it mixes route workflow, management UI projection, and write-flow callback authority. | Tasks 2, 3, 7, 8, 9, and 11 should classify management context pieces against explicit management controller/service contracts. |
| Hosted-view compatibility records remain compatibility-named | `docs-viewer/runtime/js/docs-viewer-hosted-views.js` exposes `createDocsViewerCompatibilityHostedViews()`, and app-composition registers those built-in records before route-hosted records. Focused tests still refer to compatibility views. | These may be current built-in view records rather than migration debt, but the compatibility naming needs classification so future info-panel views do not inherit unclear ownership. | Tasks 3, 5, and 10 should decide whether to rename the pattern as current architecture or create a removal/rename task. |
| Route-config migration fallback remains compatibility-named | `docs-viewer/runtime/js/docs-viewer-route-config.js` retains inline and legacy `#docsViewerRoot` data-attribute fallback behavior for migration/testing compatibility. | This is outside the main runtime callback bridge, but it is still compatibility scaffolding that can encourage new shell data attributes if left unexplained. | Tasks 2, 3, and 5 should classify whether the fallback remains test-only, gets removed, or is documented as an intentional migration path. |
| Focused app-shell smoke tests still assert compatibility surfaces | `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` asserts `compatibilityBridge.state === session.state`, `composition.appSession.state === composition.state`, the absence of broad state/session bridges from the returned app handle, search/bookmark route callback contracts, management runtime adapter context, and hosted-view compatibility records. | Some assertions are useful guards for the current architecture, while others may freeze temporary compatibility shape. | Tasks 4 and 6 should retarget tests toward owner contracts before any removal. |
| Durable docs still describe compatibility surfaces | `docs-viewer/source/studio/docs-viewer-runtime-boundary.md`, `docs-viewer/source/studio/docs-viewer-overview.md`, and `docs-viewer/source/studio/docs-viewer-javascript-inventory.md` describe the compatibility runtime, temporary state bridge, private callback bridges, built-in compatibility hosted views, and route-config migration fallback. The JavaScript inventory also contains wording to review around whether `docs-viewer-app-runtime.js` returns app-session internals after the app handle was narrowed. | Documentation is doing useful warning work, but compatibility wording should not remain the final architecture description after classification. | Task 5 should update durable docs after task 3 classifications are made. |

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory remaining compatibility scaffolding after the structural app architecture slices. Include `docs-viewer-app-runtime.js`, `docs-viewer-app-session.js`, private route/search/bookmark callback bundles, management runtime adapter callbacks, and any tests or docs that still depend on broad compatibility state. Treat each finding as migration debt until reviewed. |
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
