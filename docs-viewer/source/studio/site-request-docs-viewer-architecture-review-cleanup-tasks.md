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
| Runtime coordinator still assembles focused controllers | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` still constructs route workflow, config, sidebar, document, info panel, search/recent, bookmark, and management controller surfaces. It also owns event binding wrappers, route-global updates, private startup callbacks, pane callbacks, and management reload/startup handoffs. | This remains a compatibility coordinator, not a place for new feature ownership. The returned app handle is already narrow, but the file still passes broad state and callback bundles into controller families. | Tasks 3, 4, 5, and 9 should classify which controller families can move to explicit state-domain and service inputs. |
| App session exposes the broad compatibility state | `docs-viewer/runtime/js/docs-viewer-app-session.js` returns `state`, named `domains`, and `compatibilityBridge.state`. `docs-viewer/runtime/js/docs-viewer-app-composition.js` also keeps `composition.state` as an internal alias for controller construction. | The bridge is explicit and temporary. Existing controllers still receive the broad `state` object instead of complete domain inputs, and tests assert the bridge/state alias. | Tasks 3, 5, 6, and 7 should decide whether test assertions should target domains only and which controller family narrows first. |
| Route workflow remains private but callback-heavy | `docs-viewer/runtime/js/docs-viewer-route-workflow.js` owns URL/history/index/payload flow, while `docs-viewer-app-runtime.js` keeps private wrapper functions such as `loadDoc`, `loadIndex`, `applyCurrentRoute`, `setHistory`, and route-global update handoffs. | The private wrappers preserve the small public app handle, but they still encourage function-scoped bridge growth if future features add one-off route callbacks. | Tasks 3, 4, and 5 should classify route workflow callbacks and name the state-domain/service contract for future route changes. |
| Search/recent callbacks are still compatibility handoffs | `docs-viewer/runtime/js/docs-viewer-search-controller.js` owns search/recent behavior and exports `createDocsViewerSearchRouteCallbacks(...)`, but the controller still consumes broad `state`, `routeCallbacks`, and `paneCallbacks`; it also keeps fallback direct context callbacks. | Search/recent ownership is focused, but the broad state and fallback callback surface remain migration debt until the complete controller family receives explicit search/recent, route, pane, and generated-data inputs. | Tasks 3, 4, 5, and 6 should classify the callback bundle and test contract. |
| Bookmark callbacks are still compatibility handoffs | `docs-viewer/runtime/js/docs-viewer-bookmarks.js` owns bookmark behavior and exports `createDocsViewerBookmarkRouteCallbacks(...)`, but the controller still consumes broad `state`, route callbacks, search input refs, and route-reset behavior. | Bookmark behavior is focused, but opening a bookmark still resets search route state through private callbacks and broad state fields. | Tasks 3, 4, 5, and 6 should classify the callback bundle and decide the bookmark/search route-state contract. |
| Management lazy boundary is clean but context is broad | `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js` gates management import behind route access, but `docs-viewer-app-runtime.js` assembles a large management context including broad `state`, route workflow callbacks, config reload, generated-read reload, status/render callbacks, and management shell refs. `docs-viewer/runtime/js/docs-viewer-management.js` then passes `state` and callback bundles into management action, modal, and scope-lifecycle modules. | The lazy adapter is the current public/manage boundary and should not be removed blindly. The broad management context remains migration debt because it mixes route workflow, management UI projection, and write-flow callback authority. | Tasks 2, 3, 4, 5, 9, and 11 should classify management context pieces against explicit management controller/service contracts. |
| Hosted-view compatibility records remain compatibility-named | `docs-viewer/runtime/js/docs-viewer-hosted-views.js` exposes `createDocsViewerCompatibilityHostedViews()`, and app-composition registers those built-in records before route-hosted records. Focused tests still refer to compatibility views. | These may be current built-in view records rather than migration debt, but the compatibility naming needs classification so future info-panel views do not inherit unclear ownership. | Tasks 3, 8, and 10 should decide whether to rename the pattern as current architecture or create a removal/rename task. |
| Route-config migration fallback remains compatibility-named | `docs-viewer/runtime/js/docs-viewer-route-config.js` retains inline and legacy `#docsViewerRoot` data-attribute fallback behavior for migration/testing compatibility. | This is outside the main runtime callback bridge, but it is still compatibility scaffolding that can encourage new shell data attributes if left unexplained. | Tasks 2, 3, and 8 should classify whether the fallback remains test-only, gets removed, or is documented as an intentional migration path. |
| Focused app-shell smoke tests still assert compatibility surfaces | `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` asserts `compatibilityBridge.state === session.state`, `composition.appSession.state === composition.state`, the absence of broad state/session bridges from the returned app handle, search/bookmark route callback contracts, management runtime adapter context, and hosted-view compatibility records. | Some assertions are useful guards for the current architecture, while others may freeze temporary compatibility shape. | Tasks 6 and 7 should retarget tests toward owner contracts before any removal. |
| Durable docs still describe compatibility surfaces | `docs-viewer/source/studio/docs-viewer-runtime-boundary.md`, `docs-viewer/source/studio/docs-viewer-overview.md`, and `docs-viewer/source/studio/docs-viewer-javascript-inventory.md` describe the compatibility runtime, temporary state bridge, private callback bridges, built-in compatibility hosted views, and route-config migration fallback. The JavaScript inventory also contains wording to review around whether `docs-viewer-app-runtime.js` returns app-session internals after the app handle was narrowed. | Documentation is doing useful warning work, but compatibility wording should not remain the final architecture description after classification. | Task 8 should update durable docs after task 3 classifications are made. |

### Task 2 audit

Completed 2026-05-28.
This pass audited legacy JavaScript and server-side patterns that could encourage future code to land in the wrong module or bypass the target Docs Viewer app architecture.
No runtime or server behavior was changed in this task; each finding should be classified in task 3 before removal, renaming, or follow-up task creation.

| finding | current owner/dependency | placement risk | next review |
| --- | --- | --- | --- |
| Broad runtime coordinator remains the easiest place to add behavior | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` still sees almost every controller, broad state, DOM ref, route workflow callback, generated-data runtime, and management context field. | Even after focused owner extraction, the file still has enough visibility that a future feature could be added there instead of in route workflow, document controller, search/recent, bookmarks, info panel, generated-data runtime, or management controller modules. | Tasks 3, 4, 5, and 9 should classify whether this remains a temporary coordinator and name the first complete controller family to narrow. |
| Management controller is still a broad route-local coordinator | `docs-viewer/runtime/js/docs-viewer-management.js` owns DOM lookup, management capability startup, render projection, action/modal/scope-lifecycle controller construction, import modal lazy loading, config application, status-pill projection, and route reload handoff. | The child modules exist, but this file can still attract new management features because it has the full management state, route callbacks, shell refs, and service client options. New write behavior should not be added directly here unless it only wires an existing focused owner. | Tasks 2, 3, 4, 5, 9, and 11 should classify management lifecycle, action, modal, import, and scope-lifecycle surfaces into explicit owner contracts. |
| Management service client is centralized, but report modules bypass it | `docs-viewer/runtime/js/docs-viewer-management-client.js` owns named management endpoint calls for main management actions. Manage/local report modules such as `reports/source-config-report.js`, `reports/change-history-report.js`, and `reports/docs-broken-links-report.js` call `window.fetch(...)` against local endpoints directly. | Direct report fetches can become a parallel service adapter style unless documented as report-owned read/action contracts or moved behind named report/generated-data services. Broken-links also POSTs from a report module and needs explicit manage-only authority. | Tasks 3, 4, 10, and 11 should classify report endpoint access and decide whether report modules need a shared local-report service adapter. |
| Generated-data helpers expose lower-level fallback mechanics | `docs-viewer/runtime/js/docs-viewer-data.js` still exports generic fetch/retry helpers, generated reload helpers, and `managementReloadPath(...)`; `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` wraps these as the current generated-data owner. | Future modules could import low-level helpers and assemble generated-read endpoint paths themselves, bypassing generated-data runtime and service-context projection. | Tasks 3, 4, 8, and 10 should document or narrow low-level helper use so feature modules consume generated-data runtime methods. |
| Standalone Docs HTML Import owns a separate route app shape | `docs-viewer/runtime/js/docs-html-import.js` and `docs-html-import-workflow.js` maintain their own route readiness state, scope selection, management service calls, overwrite flow, and import result/source-open behavior. | This is a distinct Studio route/import tool, but it can encourage future import/write flows to grow outside the Docs Viewer management controller and client contracts. | Tasks 2, 3, 4, and 11 should classify standalone import ownership versus management modal import ownership. |
| Local service request handler is intentionally broad | `docs-viewer/services/docs_viewer_service.py` renders the standalone shell, injects route config, serves static assets, enforces loopback/base-url rules, gates generated reads and management POSTs, handles CORS, and dispatches GET/POST calls into docs-management services. | The handler is a boundary owner, but adding endpoint behavior directly here would bypass the shared route dispatcher and service modules. It should remain a transport/shell/static/gating layer. | Tasks 2, 3, 8, 10, and 11 should document this as current architecture or create a cleanup task if any endpoint logic should move. |
| Docs management route dispatcher is a central if/elif hub | `docs-viewer/services/docs_management_service.py` maps every Docs management path constant to read/write/import/scope/rebuild services. `docs-viewer/services/docs_management_routes.py` owns endpoint path constants and GET/POST allowlists. | A centralized dispatcher is useful, but adding endpoint behavior here without a focused service module would hide ownership and mix read, write, generated-read, import, and scope lifecycle concerns. | Tasks 2, 3, 8, and 11 should classify dispatcher ownership and require new endpoint behavior to land in focused services first. |
| Generated-read service is the server-side read owner | `docs-viewer/services/docs_management_read_service.py` dispatches generated-read GETs, and `docs-viewer/services/docs_generated_reads.py` resolves generated docs/search/docs-log/reference paths with scope and id validation. | This is the correct server owner for local generated reads. The risk is feature modules calling generated-read endpoints directly instead of using generated-data runtime, or adding generated-read path rules outside these modules. | Tasks 3, 4, and 10 should preserve this as the generated-read server contract and audit browser callers. |
| Management writes use a plan-and-rebuild execution path | `docs-viewer/services/docs_management_mutation_service.py` executes mutation plans from `docs_management_mutations.py`, writes source atomically, creates backups, suppresses watcher duplicates, and runs rebuilds through `docs_write_rebuild.py`. | This is the right current write boundary, but future write endpoints can bypass it if they directly edit source or run rebuilds from route handlers. Scope lifecycle currently shares the mutation service but has separate manifest planning. | Tasks 3, 8, 9, and 11 should document write authority and identify any write path that does not use this plan/rebuild contract. |
| Rebuild helper owns several operational concerns | `docs-viewer/services/docs_write_rebuild.py` handles Bundler command discovery, targeted/full docs build fallback, targeted search diagnostics, watcher suppression, and multi-scope rebuild orchestration. | The helper is a pragmatic service owner, but it mixes command execution, targeted-build policy, and watcher coordination; future rebuild behavior should not be duplicated in route handlers or mutation plans. | Tasks 3, 8, and 11 should classify it as current architecture or create a focused follow-up if targeted-build policy needs a separate owner. |

### Task 3 classification

Completed 2026-05-28.
This pass classified the task 1 and task 2 findings as current architecture, named follow-up work, or remove-now work.
No remove-now item was safe in this pass because the removable surfaces still need focused test retargeting, public/manage verification, or controller-family narrowing before code is deleted.

| finding | classification | owner contract or replacement path | named follow-up |
| --- | --- | --- | --- |
| `docs-viewer-app-runtime.js` compatibility coordinator | create named follow-up | Runtime may continue as the private app coordinator only for controller construction, event binding, route-global updates, and private callback handoff. New feature behavior must land in focused owners. | IT-1, IT-2, IT-3, IT-4 |
| `docs-viewer-app-session.js` broad state and `compatibilityBridge.state` | create named follow-up | App session owns state defaults and named state domains. Broad state is a temporary bridge until controller families consume explicit domains. | IT-1, IT-2, IT-4, IT-7 |
| Private route workflow wrapper callbacks | create named follow-up | Route workflow owns URL/history/index/payload commands. Private runtime wrappers are allowed only while search, bookmarks, and management reloads still need function-scoped handoff. | IT-3 |
| Search/recent broad state, route callbacks, pane callbacks, and fallback direct callbacks | create named follow-up | Search/recent controller owns generated search reads, query state, result/recent rendering, debounce, and pane requests. Replacement contract is explicit search/recent state-domain plus route and pane command inputs. | IT-1 |
| Bookmark broad state, route callbacks, search reset, and fallback direct callbacks | create named follow-up | Bookmark controller owns browser bookmark storage, list/toggle UI, selected-document projection, and bookmark open behavior. Replacement contract is explicit bookmark state-domain plus route and search-reset command inputs. | IT-2 |
| Management lazy adapter | rename as current architecture | The lazy adapter is current architecture: it gates management controller import behind route access so public routes avoid management-only JS. Do not remove it. | IT-11 for durable docs wording |
| Broad management controller/context and child callback bundles | create named follow-up | Management owns manage-mode capability checks, UI projection, action/modal/scope-lifecycle coordination, and write orchestration. Replacement contract is narrower management action, modal, scope lifecycle, route reload, and service-client inputs. | IT-4 |
| Built-in hosted-view compatibility records | rename as current architecture | These are built-in hosted-view records, not migration shims. The compatibility naming should be replaced or aliased after tests and docs are updated. | IT-5 |
| Route-config inline and legacy dataset fallback | create named follow-up | Route config registry is the durable app/shell contract. Inline/legacy dataset fallback is migration/testing support and should be removed or fenced as test-only after route-shell tests are retargeted. | IT-6 |
| Focused tests asserting compatibility state aliases and compatibility names | create named follow-up | Tests should guard current owner contracts, app handle shape, public/manage separation, and DOM behavior without freezing temporary bridge internals. | IT-7 |
| Durable docs compatibility wording | create named follow-up | Durable docs should distinguish temporary migration debt from current architecture and link each remaining bridge to an implementation task. | IT-11 |
| Direct local report endpoint fetches | create named follow-up | Reports may own report-specific read/action flows only if documented as report contracts; otherwise shared report/local-service adapters should own endpoint access. | IT-8 |
| Low-level generated-data helper exports | create named follow-up | `docs-viewer-generated-data-runtime.js` is the feature-facing generated-read owner. Low-level fetch/reload helpers should stay internal or be documented as runtime-only primitives. | IT-9 |
| Standalone Docs HTML Import route app | create named follow-up | Standalone import route remains a separate Studio import app for now. Its relationship to the Docs Viewer management modal import flow needs an explicit owner contract. | IT-10 |
| Local service request handler | rename as current architecture | The service handler is current architecture for standalone shell rendering, static serving, route-config injection, loopback/CORS enforcement, and coarse management/generated-read gating. Endpoint behavior belongs in dispatcher/service modules. | IT-11 |
| Docs management route dispatcher and path constants | rename as current architecture | The dispatcher is current architecture for mapping endpoint constants to focused services. New endpoint behavior should be implemented in service modules before being wired here. | IT-11 |
| Generated-read server services | rename as current architecture | `docs_management_read_service.py` and `docs_generated_reads.py` are the server-side generated-read owner for local generated JSON access with scope/id/path validation. | IT-11 |
| Management mutation, backup, watcher suppression, and rebuild execution | rename as current architecture | Mutation plans plus `docs_management_mutation_service.py` and `docs_write_rebuild.py` are the current write/rebuild authority. Direct source edits or rebuilds from route handlers should remain out of bounds. | IT-11 |

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory remaining compatibility scaffolding after the structural app architecture slices. Include `docs-viewer-app-runtime.js`, `docs-viewer-app-session.js`, private route/search/bookmark callback bundles, management runtime adapter callbacks, and any tests or docs that still depend on broad compatibility state. Treat each finding as migration debt until reviewed. |
| 2 | done | Audit legacy JavaScript and server-side patterns that might encourage future developers to place code in the wrong module or bypass the target app architecture. Include broad route/controller files, local service endpoints, management write paths, generated-read paths, and any helper that hides unclear ownership. |
| 3 | done | Classify each compatibility path or legacy pattern as: remove now, create a named follow-up task now, or rename it as current architecture with a clear owner contract because it is not actually compatibility. Do not leave unresolved compatibility language as an implicit future concern. |
| 4 | planned | Review feature-module access paths. Feature modules should use owner-specific callbacks, state-domain inputs, hosted-view context, generated-data runtime, or management service/controller contracts rather than app/runtime handles. |
| 5 | planned | Create focused cleanup tasks for any controller family that still needs broad state narrowed to explicit state-domain and service inputs. Candidate tasks should avoid widening `docs-viewer-app-runtime.js` and should name the replacement owner contract. |
| 6 | planned | Review focused tests for historical compatibility assumptions. Prefer tests that assert current owner contracts, DOM/user-visible behavior, service boundaries, app handle shape, state-domain behavior, hosted-view context, and public/manage separation. |
| 7 | planned | Review runtime fields kept only for tests. Remove or retarget tests before removing runtime fields; do not keep runtime API solely for test convenience. |
| 8 | planned | Review durable Docs Viewer docs for compatibility fields described as current public API. Update wording so temporary bridges are named as migration debt, private implementation details, or tracked cleanup tasks. |
| 9 | planned | Remove any compatibility path that can be resolved in this review slice. Update focused smoke coverage before or with the removal. If removal is not in this slice, create a named task with the target owner and verification requirement. |
| 10 | planned | Verify public-safe hosted-view constraints still hold: public views mount without management services, backend probes, local generated-read service base URLs, write-capable handles, or management assets. |
| 11 | planned | Verify manage-only and management action constraints still hold: visibility and availability do not imply write authority, and backend writes remain behind management endpoints with server-side validation. |
| 12 | planned | Update owning docs after review: this tracker, the parent request, Docs Viewer Runtime Boundary, Docs Viewer Overview, Docs Viewer JavaScript Inventory, and Docs Viewer Portable File Manifest if runtime copy sets changed. |
| 13 | planned | Run the verification set warranted by touched files and record results, generated payload status, remaining risks, and created follow-up tasks. |
| 14 | planned | Create or update structured docs-log entries for meaningful cleanup or final request closure, then record entry ids here. |

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| IT-1 | planned | Narrow the search/recent controller family to explicit search/recent state-domain, generated-data runtime, route command, and pane command inputs. Remove fallback direct context callbacks from `docs-viewer-search-controller.js` after focused app-shell smoke coverage is retargeted. |
| IT-2 | planned | Narrow the bookmark controller family to explicit bookmark state-domain plus route and search-reset command inputs. Remove fallback direct context callbacks from `docs-viewer-bookmarks.js` after bookmark route-state smoke coverage is retargeted. |
| IT-3 | planned | Define the route workflow command contract consumed by controllers and management reloads. Keep `applyCurrentRoute`, `loadIndex`, `loadDoc`, and `setHistory` private to route workflow/runtime handoff, and remove any one-off runtime wrappers once consumers use the contract directly. |
| IT-4 | planned | Narrow the management controller context into explicit management action, modal, scope-lifecycle, route reload, and service-client contracts. Keep writes behind management endpoints and avoid adding new write behavior directly to `docs-viewer-management.js` or `docs-viewer-app-runtime.js`. |
| IT-5 | planned | Rename built-in hosted-view compatibility records as current built-in hosted-view records, or keep a temporary alias with a removal note. Update focused hosted-view tests and durable docs in the same slice. |
| IT-6 | planned | Remove or fence route-config inline and legacy `#docsViewerRoot` dataset fallback after route-shell tests and smoke fixtures use explicit route config or the browser-safe route-config registry. |
| IT-7 | planned | Retarget focused app-shell smoke tests away from temporary compatibility internals. Keep assertions for the small returned app handle, state-domain behavior, public/manage separation, and user-visible DOM behavior; remove runtime fields kept only for test convenience. |
| IT-8 | planned | Classify local report endpoint access. Either document source-config, change-history, and broken-links reports as report-owned local contracts or move their endpoint access behind a shared local-report service adapter. |
| IT-9 | planned | Fence low-level generated-data helper use so feature modules consume `docs-viewer-generated-data-runtime.js` named read methods rather than assembling generated-read endpoint paths or reload options directly. |
| IT-10 | planned | Define the ownership boundary between the standalone Docs HTML Import route app and the Docs Viewer management modal import flow. Keep import writes behind management endpoints and avoid duplicating route/readiness/service patterns in future import features. |
| IT-11 | planned | Update durable Docs Viewer docs and JavaScript/server inventory notes with the task 3 classifications: temporary bridges, current architecture contracts, public/manage boundaries, generated-read owner, management write/rebuild authority, and transport/dispatcher limits. |

## closeout

The closeout for this review should confirm:

- remaining compatibility paths and legacy JS/server patterns are inventoried, classified, and either removed, converted into named tasks, or renamed as current architecture with a named owner contract because they are not actually compatibility
- tests assert current architecture contracts rather than historical compatibility where practical
- durable docs do not leave compatibility wording as a vague future concern
- public-safe and manage-only boundaries remain explicit
- generated-data reads still use generated-data runtime and service-context projection rather than direct endpoint calls from feature modules
- no new source editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
