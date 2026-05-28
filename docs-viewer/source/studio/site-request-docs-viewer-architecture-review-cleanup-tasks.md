---
doc_id: site-request-docs-viewer-architecture-review-cleanup-tasks
title: Docs Viewer Architecture Review And Cleanup Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14187
viewable: true
---
# Docs Viewer Architecture Review And Cleanup Tasks

This is the review and cleanup child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture). It follows the structural slices that introduced or clarified app session, service boundaries, app composition, runtime API shape, public/manage contexts, and controller/hosted-view lifecycle.

This tracker exists so cleanup notes from those slices have an explicit owner:
- Compatibility paths, broad callbacks, and legacy-style handoffs are red flags until they are removed, narrowed behind a named current owner contract, or converted into named follow-up tasks that specify the owner and removal/narrowing target.
- If a reviewed pattern is actually current architecture, stop describing it as compatibility and document the named owner contract instead.

The purpose of this cleanup is removal-led. "Fenced compatibility path" is not a final state for this work.
If a compatibility path is still present after a slice, the tracker must say why it could not be removed in that slice, which named owner will replace it, which task removes or narrows it, and what verification proves the replacement.
Tests, fixtures, and helper convenience do not define the scope of this cleanup.
They follow the architecture decision: when a test or helper depends on compatibility shape, retarget it to the current owner contract before or with the runtime change.

The cleanup pass should find them now, while the architecture request is active, rather than letting them surface later during unrelated feature work. It should review:
- JavaScript and server-side patterns,
- compatibility scaffolding,
- tests,
- durable docs,
- generated payload status, and
- remaining architecture risks.

## Status

### closeout note

Completed 2026-05-28.

- The final compatibility review found one removable runtime alias: `createDocsViewerCompatibilityHostedViews()`. Active runtime code and focused smokes already use `createDocsViewerBuiltInHostedViews()`, so the alias was removed rather than fenced.
- Durable Docs Viewer docs now describe `docs-viewer-app-runtime.js` as the private app runtime coordinator with an explicit owner contract. It remains a high-risk file for future feature placement, but it is no longer documented as an unresolved compatibility API.
- Public-safe hosted-view constraints and manage-only/write-authority constraints were rechecked against current runtime/service boundaries. Public contexts omit management services, backend probes, local generated-read service base URLs, write-capable handles, and management assets. Manage UI visibility still does not imply write authority; writes/imports/settings/scope lifecycle/source-open actions continue through `docs-viewer-management-client.js` and server-side management endpoints.
- The final scan found one separate compatibility fence outside the completed app-architecture slices: legacy sidebar local-storage migration in `docs-viewer-index-panel.js` / `docs-viewer-panel-layout.js`. It is tracked below as `FU-1` instead of being left implicit.
- Structured docs-log entry: `change-2026-05-28-closed-docs-viewer-architecture-cleanup`.

Follow-up `FU-1` completed 2026-05-28.
The legacy sidebar local-storage migration window is closed: `buildLegacySidebarStorageKey(...)`, `legacyStorageKey` reads, `legacySidebarState` projection, `data-sidebar-state` rendering/CSS fallback, and focused smoke assertions for `dotlineform-docs-viewer-sidebar:<scope>` were removed.
Current index-panel storage remains `dotlineform-docs-viewer-index-panel:<scope>` and focused smokes cover collapsed, normal, and expanded projection through that key.

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
| Runtime coordinator still assembles focused controllers | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` still constructs route workflow, config, sidebar, document, info panel, search/recent, bookmark, and management controller surfaces. It also owns event binding wrappers, route-global updates, private startup callbacks, pane callbacks, and management reload/startup handoffs. | Resolved as current architecture by final closeout wording: this is the private app runtime coordinator, not a public compatibility API or place for new feature ownership. Future feature behavior must land in focused owners. | Current owner contract documented |
| App session formerly exposed broad compatibility aliases | Resolved 2026-05-28 by `IT-7`: `docs-viewer/runtime/js/docs-viewer-app-session.js` no longer returns `compatibilityBridge`, and `docs-viewer/runtime/js/docs-viewer-app-composition.js` no longer returns `composition.state`. | The app session still returns the broad `state` object for runtime-internal controller handoffs that have not yet moved to explicit domains, but tests no longer freeze the removed aliases. | IT-7 done |
| Route workflow remains private but callback-heavy | `docs-viewer/runtime/js/docs-viewer-route-workflow.js` owns URL/history/index/payload flow, while `docs-viewer-app-runtime.js` keeps private wrapper functions such as `loadDoc`, `loadIndex`, `applyCurrentRoute`, `setHistory`, and route-global update handoffs. | The private wrappers preserve the small public app handle, but they still encourage function-scoped bridge growth if future features add one-off route callbacks. | Tasks 3, 4, and 5 should classify route workflow callbacks and name the state-domain/service contract for future route changes. |
| Search/recent callback handoffs | Resolved 2026-05-28 by `IT-1`: `docs-viewer-search-controller.js` now consumes generated-data runtime plus explicit search/recent, document-index, selected-document, route-command, and pane-command inputs. | The broad state and fallback direct context callbacks were removed from this controller. | IT-1 done |
| Bookmark callback handoffs | Resolved 2026-05-28 by `IT-2`: `docs-viewer-bookmarks.js` now consumes explicit bookmark, document-index, selected-document, search/recent, route-command, and search-reset command inputs. | Broad state, route callback fallback, and direct search input reset authority were removed from this controller. | IT-2 done |
| Management lazy boundary context | Resolved 2026-05-28 by `IT-4`: `docs-viewer-app-runtime.js` no longer passes broad runtime `state` into the lazy management context. `docs-viewer-management.js` receives named management state-domain, service-client, and route-reload contracts and builds a management-local facade. | The lazy adapter remains current public/manage architecture and continues to gate management imports behind route access. | IT-4 done |
| Hosted-view compatibility records remained compatibility-named | Resolved 2026-05-28 by `IT-5` plus final closeout: built-in hosted-view records are exposed through `createDocsViewerBuiltInHostedViews()`, and `createDocsViewerCompatibilityHostedViews()` was removed after active callers and smokes moved to the built-in factory. | Built-in hosted-view records are current architecture, not migration shims. | IT-5 done; Task 9 done |
| Route-config migration fallback remains compatibility-named | Resolved 2026-05-28 by `IT-6`: `docs-viewer/runtime/js/docs-viewer-route-config.js` no longer reads inline route-config scripts or legacy `#docsViewerRoot` route data attributes. | Route config registry and explicit route config are the current owner contract. App-shell helpers receive route context explicitly rather than recreating it from shell attributes. | IT-6 done |
| Focused app-shell smoke tests still asserted compatibility surfaces | Resolved 2026-05-28 by `IT-7` for app-session/composition aliases and by final closeout for the hosted-view alias path. Focused app-shell smoke coverage now asserts state-domain projections, composition public/manage contracts, the small returned app handle, and built-in hosted-view contracts. | Tests follow the current owner contracts and no longer preserve compatibility aliases for convenience. | IT-7 done; Task 9 done |
| Durable docs described compatibility surfaces | Resolved by `IT-11` and final closeout. Durable docs now describe the private app runtime coordinator, built-in hosted-view records, public/manage service boundaries, generated-read owner, and management write authority as current architecture contracts. | The separate legacy sidebar local-storage migration found during final scan is tracked as `FU-1`. | IT-11 done; FU-1 planned |

### Task 2 audit

Completed 2026-05-28.
This pass audited legacy JavaScript and server-side patterns that could encourage future code to land in the wrong module or bypass the target Docs Viewer app architecture.
No runtime or server behavior was changed in this task; each finding should be classified in task 3 before removal, renaming, or follow-up task creation.

| finding | current owner/dependency | placement risk | next review |
| --- | --- | --- | --- |
| Broad runtime coordinator remains the easiest place to add behavior | `docs-viewer/runtime/js/docs-viewer-app-runtime.js` still sees almost every controller, broad state, DOM ref, route workflow callback, generated-data runtime, and management context field. | Even after focused owner extraction, the file still has enough visibility that a future feature could be added there instead of in route workflow, document controller, search/recent, bookmarks, info panel, generated-data runtime, or management controller modules. | Tasks 3, 4, 5, and 9 should classify whether this remains a temporary coordinator and name the first complete controller family to narrow. |
| Management controller is still a broad route-local coordinator | `docs-viewer/runtime/js/docs-viewer-management.js` owns DOM lookup, management capability startup, render projection, action/modal/scope-lifecycle controller construction, import modal lazy loading, config application, status-pill projection, and route reload handoff. | The child modules exist, but this file can still attract new management features because it has the full management state, route callbacks, shell refs, and service client options. New write behavior should not be added directly here unless it only wires an existing focused owner. | Tasks 2, 3, 4, 5, 9, and 11 should classify management lifecycle, action, modal, import, and scope-lifecycle surfaces into explicit owner contracts. |
| Management service client is centralized, but report modules bypass it | Resolved 2026-05-28 by `IT-8`: `docs-viewer/runtime/js/docs-viewer-report-service.js` now owns local report endpoint access for source-config, generated docs-log, and broken-links audit requests. Manage/local report modules consume `context.reportService` instead of `managementBaseUrl` or direct `window.fetch(...)`. | Report modules keep presentation and report-specific UI context; endpoint paths, request options, envelope differences, and local-server missing-base errors are owned by the report service adapter. | IT-8 done |
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
| `docs-viewer-app-runtime.js` private app coordinator | rename as current architecture | Runtime may continue as the private app coordinator only for controller construction, event binding, route-global updates, and private callback handoff. New feature behavior must land in focused owners. | Current owner contract documented |
| `docs-viewer-app-session.js` broad state and `compatibilityBridge.state` | remove now / named follow-up | Resolved 2026-05-28 by `IT-7` for the test-only aliases: `compatibilityBridge` and `composition.state` were removed. The remaining broad `state` object is runtime-internal controller migration debt and should shrink only through complete controller-family domain-input slices. | IT-7 done; future controller-family tasks as needed |
| Private route workflow wrapper callbacks | resolved | Resolved 2026-05-28 by `IT-3`: route workflow owns URL/history/index/payload commands through a private command contract consumed by search, bookmarks, startup index loading, and management reloads. One-off runtime wrappers were removed. | IT-3 done |
| Search/recent broad state, route callbacks, pane callbacks, and fallback direct callbacks | create named follow-up | Search/recent controller owns generated search reads, query state, result/recent rendering, debounce, and pane requests. Replacement contract is explicit search/recent state-domain plus route and pane command inputs. | IT-1 |
| Bookmark broad state, route callbacks, search reset, and fallback direct callbacks | create named follow-up | Bookmark controller owns browser bookmark storage, list/toggle UI, selected-document projection, and bookmark open behavior. Replacement contract is explicit bookmark state-domain plus route and search-reset command inputs. | IT-2 |
| Management lazy adapter | rename as current architecture | The lazy adapter is current architecture: it gates management controller import behind route access so public routes avoid management-only JS. Do not remove it. | IT-11 for durable docs wording |
| Broad management controller/context and child callback bundles | create named follow-up | Management owns manage-mode capability checks, UI projection, action/modal/scope-lifecycle coordination, and write orchestration. Replacement contract is narrower management action, modal, scope lifecycle, route reload, and service-client inputs. | IT-4 |
| Built-in hosted-view compatibility records | Resolved 2026-05-28: these are now named built-in hosted-view records through `createDocsViewerBuiltInHostedViews()`, and the old compatibility factory alias was removed during final closeout. | These are built-in hosted-view records, not migration shims. | IT-5 done; Task 9 done |
| Route-config inline and legacy dataset fallback | remove now | Resolved 2026-05-28 by `IT-6`: route config registry and explicit route config are now the only route-config sources. Inline route-config scripts and legacy route data attributes are no longer read as route config. | IT-6 done |
| Focused tests asserting compatibility state aliases and compatibility names | remove now / named follow-up | Resolved 2026-05-28 by `IT-7` for app-session/composition aliases. Tests now guard named domain projections, composition contracts, app handle shape, public/manage separation, and DOM behavior without freezing `compatibilityBridge` or `composition.state`. | IT-7 done |
| Durable docs compatibility wording | resolved | Durable docs distinguish temporary migration debt from current architecture. The final scan found the separate legacy sidebar storage migration and created `FU-1` with owner and removal criteria. | IT-11 done; FU-1 planned |
| Direct local report endpoint fetches | Resolved 2026-05-28: endpoint access moved behind `docs-viewer-report-service.js`. | Reports remain self-contained presentation modules, but local source-config, generated docs-log, and broken-links audit endpoint paths are not report-owned fetch code. | IT-8 done |
| Low-level generated-data helper exports | create named follow-up | `docs-viewer-generated-data-runtime.js` is the feature-facing generated-read owner. Low-level fetch/reload helpers should stay internal or be documented as runtime-only primitives. | IT-9 |
| Standalone Docs HTML Import route app | create named follow-up | Standalone import route remains a separate Studio import app for now. Its relationship to the Docs Viewer management modal import flow needs an explicit owner contract. | IT-10 |
| Local service request handler | rename as current architecture | The service handler is current architecture for standalone shell rendering, static serving, route-config injection, loopback/CORS enforcement, and coarse management/generated-read gating. Endpoint behavior belongs in dispatcher/service modules. | IT-11 |
| Docs management route dispatcher and path constants | rename as current architecture | The dispatcher is current architecture for mapping endpoint constants to focused services. New endpoint behavior should be implemented in service modules before being wired here. | IT-11 |
| Generated-read server services | rename as current architecture | `docs_management_read_service.py` and `docs_generated_reads.py` are the server-side generated-read owner for local generated JSON access with scope/id/path validation. | IT-11 |
| Management mutation, backup, watcher suppression, and rebuild execution | rename as current architecture | Mutation plans plus `docs_management_mutation_service.py` and `docs_write_rebuild.py` are the current write/rebuild authority. Direct source edits or rebuilds from route handlers should remain out of bounds. | IT-11 |

### Task 4 feature-module access review

Completed 2026-05-28.
This pass reviewed feature-module access paths against the target rule: feature modules should consume owner-specific callbacks, state-domain inputs, hosted-view context, generated-data runtime, or management service/controller contracts rather than app/runtime handles.
No runtime behavior was changed.

| access path | current pattern | result | follow-up |
| --- | --- | --- | --- |
| Returned app handle | Feature modules do not consume the returned `startDocsViewerApp(...)` handle. The focused smoke checks inspect the handle shape and confirm it exposes only `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`. | Current architecture. Preserve the small handle and do not add feature escape hatches. | Task 6 should keep this as a contract assertion, not a feature dependency. |
| Runtime/app internals | Feature modules do not import `docs-viewer-app-runtime.js`, `docs-viewer-app-session.js`, or `docs-viewer-app-composition.js` directly. App boot and app composition remain the only runtime owners importing those surfaces. | Current architecture. No feature module is bypassing the app shell through app/runtime imports. | IT-11 should document this as an owner boundary. |
| Search/recent controller | Resolved 2026-05-28 by `IT-1`: `docs-viewer-search-controller.js` now consumes generated-data runtime plus explicit search/recent, document-index, selected-document, route-command, and pane-command inputs. | Current owner contract for this family. The broad state and fallback direct context callbacks were removed from this controller. | IT-1 done |
| Bookmark controller | Resolved 2026-05-28 by `IT-2`: `docs-viewer-bookmarks.js` now consumes browser bookmark storage helpers plus explicit bookmark, document-index, selected-document, search/recent, route-command, and search-reset command inputs. | Current owner contract for this family. Broad state, route callback fallback, and search reset through direct state/search-input mutation were removed from this controller. | IT-2 done |
| Route workflow owner | Resolved 2026-05-28 by `IT-3`: `docs-viewer-route-workflow.js` owns low-level route application, history, index load, and payload load through a private command contract. Search, bookmarks, startup index loading, and management reloads consume that contract directly instead of one-off runtime wrappers. | Current owner contract for this family. The route workflow is backed by explicit route-session, scope-config, document-index, selected-document, search/recent, and status inputs. | IT-3 done |
| Document controller and reports | `docs-viewer-document-controller.js` exposes a report context with generated-data methods such as `fetchDocsIndex`, `fetchDocsReferencesIndex`, and `fetchDocsReferenceTarget`, plus a `reportService` adapter for local report endpoints. Public/read-only reports use generated-data callbacks; manage/local reports use the report service for source-config, generated docs-log, and broken-links audit requests. | Current owner contract after `IT-8`: document controller shapes report context; generated reads stay behind generated-data runtime; local report endpoint access stays behind `docs-viewer-report-service.js`. Low-level generated-data helper caller limits remain tracked separately. | IT-9 |
| Info panel hosted views | Resolved 2026-05-28 by `IT-13`: `docs-viewer-info-panel-controller.js`, `docs-viewer-view-context.js`, and `docs-viewer-metadata-info-view.js` use hosted-view context and selected-document projection from explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs. The metadata view does not consume management services, generated-read service base URLs, or app/runtime handles. | Current architecture for public-safe info hosted views. | Task 10 should verify public-safe constraints; IT-5 handles built-in view naming. |
| Management child modules | Management action, modal, capability, interaction, and scope-lifecycle modules use management client functions and parent-provided callbacks. They do not consume app/runtime handles directly, but they still receive broad management state and callback bundles. | Migration debt. The service-client path is mostly correct; state/callback boundaries need narrowing. | IT-4 |
| Standalone Docs HTML Import | `docs-html-import.js` and `docs-html-import-workflow.js` use the management client for import/open-source calls and maintain their own route-readiness state. They do not consume app/runtime handles. | Separate current route app with ownership risk. It needs an explicit boundary relative to the Docs Viewer management modal import flow before future import features are added. | IT-10 |
| Low-level generated-data helpers | `docs-viewer-generated-data-runtime.js` correctly owns feature-facing generated reads. Low-level helpers in `docs-viewer-data.js` are still imported by runtime owners and report registry/config code, so future feature modules could bypass generated-data runtime if those helpers remain broadly available without a named owner contract. | Migration risk. Current callers must either move behind generated-data runtime methods or be documented as current runtime/config primitives with an explicit allowed caller set. Helper convenience does not justify keeping feature-facing bypasses. | IT-9 and IT-11 |

### Task 5 controller-family cleanup task review

Completed 2026-05-28.
This pass converted the remaining broad-state controller findings into focused implementation tasks with named replacement contracts.
No runtime behavior was changed.

| controller family | broad dependency still present | replacement owner contract | implementation task |
| --- | --- | --- | --- |
| Search and recent | Resolved 2026-05-28: `docs-viewer-search-controller.js` no longer receives `context.state` or fallback direct route/pane callbacks. | Explicit search/recent state-domain, generated-data runtime, route command inputs, and pane command inputs. | IT-1 done |
| Bookmarks | Resolved 2026-05-28: `docs-viewer-bookmarks.js` no longer receives `context.state`, fallback route callbacks, or direct search input reset authority. | Explicit bookmark state-domain, browser bookmark storage owner, route command input, and search-reset command input. | IT-2 done |
| Route workflow | Resolved 2026-05-28: `docs-viewer-route-workflow.js` no longer receives the broad runtime state and now exposes the private command contract for index load, document load, URL/history, route resolution, and URL creation. | Route workflow command contract backed by explicit route-session, scope-config, document-index, selected-document, search/recent, and status inputs. | IT-3 done |
| Management | Resolved 2026-05-28: `docs-viewer-app-runtime.js` no longer passes broad runtime `state` into the lazy management context. `docs-viewer-management.js` receives named management state-domain, service-client, and route-reload contracts and builds an internal management facade for existing child modules. | Management action, modal, scope-lifecycle, route reload, render-projection, and service-client contracts. | IT-4 done |
| Document, sidebar, and reports | Resolved 2026-05-28: `docs-viewer-document-controller.js` receives explicit route-session, scope-config, selected-document, generated-data, and status command inputs; `docs-viewer-sidebar.js` receives explicit document-index, selected-document, and scope-config projections. Report context exposes generated-read methods through generated-data runtime and local endpoint access through `docs-viewer-report-service.js`. | Document payload owner plus document-index/sidebar projection inputs; report context adapter that exposes generated reads and local-report service access intentionally. | IT-12 done; IT-8 done |
| Info panel hosted views | Resolved 2026-05-28: `docs-viewer-info-panel-controller.js` no longer receives broad state and now reads selected doc, document maps, payload cache, UI status labels, and `viewState` projection through explicit document-index, selected-document, scope-config, panel-view, route-access, URL, and trail inputs. | Hosted-view projection input built from selected-document, document-index, payload-cache, UI-status, route-access, and view-state domains; no management or write-capable handles. | IT-13 done |
| Config and scope routing | Resolved 2026-05-28: `docs-viewer-config-controller.js` no longer receives broad state and now reads config-load promise/cache, scope config maps, default scope, route globals, UI text, recent limit, and status/management copy through explicit scope-config, document-index, search/recent, route-session, config-service, and route-command inputs. | Scope-config state-domain plus route-config registry command input and config-load service input. | IT-14 done |
| Standalone import route | `docs-html-import.js` and `docs-html-import-workflow.js` maintain their own route-readiness and import state outside the viewer app. | Separate import route app contract with explicit boundary to the Docs Viewer management modal import flow. | IT-10 |

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory remaining compatibility scaffolding after the structural app architecture slices. Include `docs-viewer-app-runtime.js`, `docs-viewer-app-session.js`, private route/search/bookmark callback bundles, management runtime adapter callbacks, and any tests or docs that still depend on broad compatibility state. Treat each finding as migration debt until reviewed. |
| 2 | done | Audit legacy JavaScript and server-side patterns that might encourage future developers to place code in the wrong module or bypass the target app architecture. Include broad route/controller files, local service endpoints, management write paths, generated-read paths, and any helper that hides unclear ownership. |
| 3 | done | Classify each compatibility path or legacy pattern as: remove now, create a named follow-up task with the replacement owner and removal/narrowing target, or rename it as current architecture with a clear owner contract because it is not actually compatibility. Do not leave unresolved compatibility language as an implicit future concern. |
| 4 | done | Review feature-module access paths. Feature modules should use owner-specific callbacks, state-domain inputs, hosted-view context, generated-data runtime, or management service/controller contracts rather than app/runtime handles. |
| 5 | done | Create focused cleanup tasks for any controller family that still needs broad state narrowed to explicit state-domain and service inputs. Candidate tasks should avoid widening `docs-viewer-app-runtime.js` and should name the replacement owner contract. |
| 6 | done | Reviewed focused tests for historical compatibility assumptions and retargeted app-session/composition alias assertions to current owner contracts, state-domain behavior, app handle shape, and public/manage composition contracts. Tests follow the architecture contract; they do not preserve compatibility scope. |
| 7 | done | Removed runtime fields kept only for tests in this slice: `compatibilityBridge` and `composition.state`. Retargeted tests before removing those fields; runtime API is not kept solely for test convenience. |
| 8 | done | Reviewed durable Docs Viewer docs for compatibility fields described as current public API. Stale `compatibilityBridge`, built-in hosted-view alias, compatibility runtime, and compatibility panel wording was checked against runtime code and updated to current owner contracts or tracked follow-up language. |
| 9 | done | Removed the remaining hosted-view compatibility alias `createDocsViewerCompatibilityHostedViews()` after active runtime code and focused smokes were confirmed to use `createDocsViewerBuiltInHostedViews()`. The separate legacy sidebar storage migration was found during the final scan and tracked as `FU-1`. |
| 10 | done | Verified public-safe hosted-view constraints still hold in the current contracts: public hosted-view context is built from selected-document, route/access, payload, viewer-scope, URL, trail, and display-label inputs, and omits management services, backend probes, local generated-read service base URLs, write-capable handles, and management assets. |
| 11 | done | Verified manage-only and management action constraints still hold in the current contracts: route/manage UI visibility does not imply backend write authority, and writes/imports/settings/scope lifecycle/source-open actions go through `docs-viewer-management-client.js` and server-side management endpoints. |
| 12 | done | Updated owning docs after review: this tracker, the parent request, Docs Viewer Runtime Boundary, Docs Viewer Overview, and Docs Viewer JavaScript Inventory. Docs Viewer Portable File Manifest was not touched because runtime copy sets did not change. |
| 13 | done | Ran targeted verification for the touched runtime/doc slice and recorded results below. Generated docs/search payloads were left to the docs watcher; any watcher-generated updates should remain if present. |
| 14 | done | Created structured docs-log entry `change-2026-05-28-closed-docs-viewer-architecture-cleanup` for final cleanup closeout. |

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| IT-1 | done | Narrow the search/recent controller family to explicit search/recent state-domain, generated-data runtime, route command, and pane command inputs. Remove fallback direct context callbacks from `docs-viewer-search-controller.js` after focused app-shell smoke coverage is retargeted. |
| IT-2 | done | Narrow the bookmark controller family to explicit bookmark state-domain plus route and search-reset command inputs. Remove fallback direct context callbacks from `docs-viewer-bookmarks.js` after bookmark route-state smoke coverage is retargeted. |
| IT-3 | done | Define the route workflow command contract consumed by controllers and management reloads. Back it with explicit route-session, scope-config, document-index, selected-document, search/recent, and status inputs. Keep `applyCurrentRoute`, `loadIndex`, `loadDoc`, and `setHistory` private to route workflow/runtime handoff, and remove any one-off runtime wrappers once consumers use the contract directly. Completed 2026-05-28. |
| IT-4 | done | Narrow the management controller context into explicit management action, modal, scope-lifecycle, route reload, and service-client contracts. Keep writes behind management endpoints and avoid adding new write behavior directly to `docs-viewer-management.js` or `docs-viewer-app-runtime.js`. Completed 2026-05-28 for the lazy management context: runtime now passes named management state-domain, service-client, and route-reload contracts, while existing child modules consume a management-local facade built from those domains. |
| IT-5 | done | Rename built-in hosted-view compatibility records as current built-in hosted-view records, or keep a temporary alias with a removal note. Update focused hosted-view tests and durable docs in the same slice. Completed 2026-05-28 with `createDocsViewerBuiltInHostedViews()`; the temporary `createDocsViewerCompatibilityHostedViews()` alias was removed during final cleanup after active callers and smokes were confirmed to use the built-in factory. |
| IT-6 | done | Removed route-config inline and legacy `#docsViewerRoot` dataset fallback after route-shell tests and smoke fixtures were retargeted to explicit route config, explicit route context, or the browser-safe route-config registry. Completed 2026-05-28. |
| IT-7 | done | Retargeted focused app-shell smoke tests away from temporary app-session/composition compatibility internals. Assertions now cover the small returned app handle, state-domain behavior, public/manage composition contracts, and user-visible DOM behavior; `compatibilityBridge` and `composition.state` were removed. Completed 2026-05-28. |
| IT-8 | done | Classified local report endpoint access and report context ownership. Source-config, change-history, and broken-links endpoint access now goes through `docs-viewer-report-service.js`; report modules consume `context.reportService` and no longer receive `managementBaseUrl` or own direct endpoint fetches. Completed 2026-05-28. |
| IT-9 | done | Narrow low-level generated-data helper use so feature modules consume `docs-viewer-generated-data-runtime.js` named read methods rather than assembling generated-read endpoint paths or reload options directly. Completed 2026-05-28 by moving asset-version URL helpers to `docs-viewer-asset-url.js`, config/UI-text asset reads to `docs-viewer-config-service.js`, and focused smoke coverage to the current import boundary: direct `docs-viewer-data.js` imports are reserved for `docs-viewer-generated-data-runtime.js` and `docs-viewer-config-service.js`. |
| IT-10 | done | Define the ownership boundary between the standalone Docs HTML Import route app and the Docs Viewer management modal import flow. Completed 2026-05-28 as a durable ownership documentation slice: Docs Import is a management-modal app, `docs-html-import.js` owns modal state and route-ready projection, `docs-html-import-workflow.js` owns preview/write orchestration, and import writes stay behind management endpoints through `docs-viewer-management-client.js`. |
| IT-11 | done | Update durable Docs Viewer docs and JavaScript/server inventory notes with the task 3 classifications: temporary bridges, current architecture contracts, public/manage boundaries, generated-read owner, management write/rebuild authority, and transport/dispatcher limits. Completed 2026-05-28 for the implementation-task classifications in Docs Viewer Runtime Boundary, Docs Viewer Overview, Docs Viewer JavaScript Inventory, Studio Python And Ruby Script Inventory, and Docs Viewer Portable File Manifest. |
| IT-12 | done | Narrow the document/sidebar/report controller family to explicit document payload, selected-document, document-index/sidebar projection, scope-config, status, and report-context inputs. Generated report reads stay behind generated-data runtime, and local report endpoint access is now exposed intentionally through the `IT-8` report service adapter. Completed 2026-05-28. |
| IT-13 | done | Narrow the info-panel hosted-view controller to a hosted-view projection input built from selected-document, document-index, payload-cache, UI-status, route-access, and view-state domains. Preserve the public-safe hosted-view constraint by excluding management services, local generated-read base URLs, and write-capable handles. Completed 2026-05-28. |
| IT-14 | done | Narrow the config/scope controller to explicit scope-config state-domain, config-load service, route-config registry command, and UI-text inputs. Keep route globals and root dataset projection as shell/config responsibilities rather than new feature behavior in `docs-viewer-app-runtime.js`. Completed 2026-05-28. |

## Follow-Up Tasks

These tasks were found by the final closeout scan and are not part of the completed app-architecture implementation path.

| ID | status | owner | action |
| --- | --- | --- | --- |
| FU-1 | done | `docs-viewer-index-panel.js`, `docs-viewer-panel-layout.js`, `docs-viewer-index-panel-renderer.js`, `docs-viewer.css`, `docs_viewer_index_panel_modules.py`, `docs_viewer_app_shell_modules.py` | Retired the legacy sidebar local-storage migration after intentionally closing the migration window. Removed `buildLegacySidebarStorageKey(...)`, `legacyStorageKey` reads, `legacySidebarState` projection, `data-sidebar-state` rendering/CSS fallback, and focused smoke assertions that preserved the old `dotlineform-docs-viewer-sidebar:<scope>` key. Verification requirement: focused index-panel module smoke plus app-shell smoke proving current `dotlineform-docs-viewer-index-panel:<scope>` storage still handles collapsed/normal/expanded projection. |

## closeout

The closeout for this review confirms:

- remaining compatibility paths and legacy JS/server patterns are inventoried, classified, and either removed, converted into named removal/narrowing tasks, or renamed as current architecture with a named owner contract because they are not actually compatibility
- tests assert current architecture contracts rather than historical compatibility; tests and helper convenience do not preserve compatibility paths
- durable docs do not leave compatibility wording as a vague future concern
- public-safe and manage-only boundaries remain explicit
- generated-data reads still use generated-data runtime and service-context projection rather than direct endpoint calls from feature modules
- no new source editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
- verification recorded for final cleanup: `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`, `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`, focused app-shell smoke, focused compatibility-reference scans, and `git diff --check`
- structured docs-log entry recorded: `change-2026-05-28-closed-docs-viewer-architecture-cleanup`
