---
doc_id: site-request-docs-viewer-foundation-refactor-implementation
title: Docs Viewer Foundation Refactor Implementation
added_date: 2026-07-11
last_updated: 2026-07-11
ui_status: in-progress
summary: Implementation tracker, preserved-behavior baseline, owner map, and focused checks for Docs Viewer architecture roadmap phases 0-5.
parent_id: change-requests
viewable: true
---
# Docs Viewer Foundation Refactor Implementation

## Status

Phases 0-4 complete. The public/manage baseline, explicit app-context contract, independent service surfaces, configured-scope provider, route-feature policy, startup sequence, and code-owned view/mode/control projection are recorded below. Focused module, service, lifecycle, public, and manage checks pass.

Phase 5, coordinator reduction for the touched areas, is next.

This tracker implements phases 0-5 of [Docs Viewer Architecture Assessment And Refactor Roadmap](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap). It contains no Docs Review feature behavior.

## Scope And Guardrails

The foundation work is behavior-preserving for current public and manage routes.

- Public routes remain static readers without management imports, service URLs, capability probes, write handles, or manage-only UI.
- The manage route retains current scope selection, local generated reads, management capability checks, source editing, imports, reports, settings, and scope lifecycle behavior.
- Each phase replaces its old API in the same slice. No compatibility aliases or duplicate config fields remain.
- Route config describes route identity and policy; it does not register executable modules or handlers.
- Backend capability responses authorize operations. Browser visibility and code registration do not authorize them.
- New provider, feature, and projection behavior must not become lifecycle code in `docs-viewer-app-runtime.js`.
- Tests protect owner contracts, service responses, module boundaries, and boot integration rather than UI choreography.

## Phase 0 Preserved-Behavior Baseline

### Entrypoint And Module Graph

The browser URL `/docs-viewer/runtime/js/shared/` is served from `site/docs-viewer/runtime/js/shared/` for both public and manage routes. The manage source tree therefore imports the shared boot URL even though there is no duplicate `docs-viewer/runtime/js/shared/` directory.

Current static graph snapshot:

| graph | modules | contract |
| --- | ---: | --- |
| Public entry shim rooted at `site/docs-viewer/runtime/js/public/docs-viewer-public.js` | 4 | Imports asset-version projection and public document-report contributions, then dynamically imports shared app boot. |
| Shared app-boot graph rooted at `site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js` | 43 | Contains shared boot, composition, session, route, controller, panel, view, data, config, search, bookmark, and renderer modules. It has no static manage-owned import. |
| Effective public graph after dynamic boot | 46 unique modules | Public entry contributions plus shared app boot; the shared asset-URL module is the one overlap. |
| Manage entry contributions rooted at `docs-viewer/runtime/js/management/docs-viewer-manage.js` | 9 | Adds manage document actions, hosted views, shell composition/rendering, and report services. |
| Effective manage boot graph before later lazy workflows | 52 unique modules | Shared app-boot graph plus the nine manage entry contributions. |

Current dynamic boundaries:

- public entry dynamically loads shared app boot after applying the asset version
- the shared metadata-info hosted view loads only when requested
- shared boot can load the manage theme module only when route access allows management
- the neutral runtime lazy controller loads `docs-viewer-management.js` only when management initialization is allowed
- the private runtime loads the management client only for management source-service composition
- manage hosted-view contributions lazy-load Markdown source and semantic-token-picker lifecycles
- manage orchestration lazy-loads Docs Import and scope lifecycle workflows
- manage report definitions lazy-load individual report modules

The permanent public import-boundary test currently follows the public entry's static graph. The baseline also records the separately resolved shared app-boot graph so later changes do not hide manage imports behind the public entry's intentional dynamic boot boundary.

### Route, Access, And Service Context

Current routes:

| route | route id | scope selection | current access projection | generated reads | management |
| --- | --- | --- | --- | --- | --- |
| `/library/` | `library` | fixed `library`; scope query disabled | public/read-only | static public payloads | absent |
| `/analysis/` | `analysis` | fixed `analysis`; scope query disabled | public/read-only | static public payloads | absent |
| `/moments/` | `moments` | fixed `moments`; scope query disabled | public/read-only | static public payloads | absent |
| `/docs/` | `docs-manage` | configured scopes; scope query enabled | manage when route config enables management | local generated-read service when configured, otherwise generated asset URL | capability-gated local backend |

The current pre-refactor authority chain is:

```text
route path + route config
  -> allowManagement
  -> publicReadOnly / canLoadManagementUi
  -> app dataset mode and service label
  -> local generated-read base URL
  -> management service context
  -> source-service exposure
  -> manage hosted-view access
  -> management startup and lazy loading
```

At the Phase 0 baseline, `startDocsViewerPublicApp()` and `startDocsViewerManageApp()` passed an `appKind` option, but route-context creation did not retain it. Effective app kind was inferred from `access.allowManagement`.

At that baseline, `docs-viewer-service-context.js` exposed:

- browser-safe config for every route
- generated reads as static assets for public routes
- local generated-read base URL only when `allowManagement` is true
- a management service surface only when `allowManagement` is true

This is the preserved pre-refactor baseline. The implemented Phase 1 contract is recorded below.

### Startup And Construction

Current declared startup phases:

| order | phase | public | manage | authority |
| ---: | --- | :---: | :---: | --- |
| 1 | bind events | yes | yes | browser route/config context |
| 2 | load Docs Viewer config | yes | yes | browser-safe config asset |
| 3 | load UI text/viewer config | yes | yes | browser-safe config asset |
| 4 | initialize bookmarks | yes | yes | browser storage |
| 5 | initialize management | no | yes | management capability endpoint |
| 6 | load initial index and route | yes | yes | generated asset or local generated-read service |
| 7 | open import requested by URL | no | yes | management write endpoint |

Before these phases run, app composition constructs the service context, hosted-view registry, panel layout, app session, document-index state, generated-data runtime, and config service. The private runtime then constructs the current route, config, search/recent, bookmark, document, main-view, display-mode, info-panel, sidebar, management-lazy, and status coordination surfaces.

Several features tolerate missing DOM controls, but there is no normalized route-feature contract. Search, recent, bookmarks, scope discovery, and their state/controller surfaces are still broadly constructed for current routes.

### State Domains

Current app-session domains are useful descriptive boundaries, but these fields have more than one mutable facade:

| field or concern | current domains | Phase 1-5 treatment |
| --- | --- | --- |
| `expandedDocIds` | `documentIndex`, `panelView` | Assign expansion mutation to one owner and expose a query/command to the other consumer. |
| `uiStatusByValue` | `scopeConfig`, `documentIndex` | Keep config authority in `scopeConfig`; document index consumes a read-only query/input. |
| `docNonViewableEmoji` | `scopeConfig`, `management` | Keep presentation config authority outside management state. |
| `managementContext` | `routeSession`, `management` | Replace route-derived management identity with explicit app context; management owns backend lifecycle state only. |
| `managementCapabilities` | `management`, `generatedData` | Split generated-read capability from general management capability state. |
| `reloadNonce`, `reloadExpectedDocId` | `selectedDocument`, `generatedData` | Keep reload request state with generated-data/provider workflow and expose selected-document commands. |
| management message/status fields | `management`, `busyStatus` | Give status/busy projection one owner if touched by the new contexts. |

No global store or event-bus rewrite is planned.

### View, Display Mode, And Toolbar Contract

Current relationships are valid:

```text
panel -> hosted view
document main view -> document display mode
active view/mode -> relevant toolbar controls
```

Before Phase 4, decisions were split:

- `docs-viewer-hosted-views.js` normalized panel views and checked access/availability
- `docs-viewer-document-display-mode-host.js` separately normalizes and resolves document modes
- `docs-viewer-main-view-renderer.js` creates shared `bookmark` and `info` controls
- bookmark and info controllers independently project visibility and live state
- the manage document-action renderer injects `edit`, `markdown-source`, and `save-markdown-source`
- management orchestration projects selection, capability, busy, and active-mode visibility/disabled state
- the source-editor lifecycle separately projects bookmark/info/source control changes
- route UI policy can hide the whole main-view toolbar, as used by the public Moments route

Markdown source is a display mode of the rendered-document view, not a peer main view. Handlers, dirty state, pressed state, busy state, and pending state remain owned by the focused runtime controllers.

[Docs Viewer View, Mode, And Control Projection](/docs/?scope=studio&doc=site-request-docs-viewer-view-mode-registry) is the Phase 4 child task. It replaces the earlier browser-JSON registry design with code-owned definitions and explicit projection inputs.

## Baseline Checks

Baseline recorded on 2026-07-11:

| check | purpose | result |
| --- | --- | --- |
| `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py docs-viewer/tests/python/test_docs_viewer_static_assets.py docs-viewer/tests/python/test_docs_viewer_service_config.py` | Public static-import isolation, static route mapping, route/service config projection | pass: 17 tests |
| `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs-viewer-smoke --run-id docs-viewer-foundation-phase-0-baseline` | Static-site validation, manage route boot/service boundary, public Library/Analysis read-only boundary | pass: 3 checks; `var/admin/test-runs/docs-viewer-foundation-phase-0-baseline/summary.md` |

Slice-specific checks must add the lowest-layer contract proof described below. The browser profile is required only when a slice changes route boot, module mapping, or public/manage network boundaries.

## Implementation Slices

| phase | target owner after the slice | primary change | focused proof |
| --- | --- | --- | --- |
| 1. App context and authority — complete | `docs-viewer-app-context.js` for normalized app context; `docs-viewer-access.js` for route visibility; `docs-viewer-service-context.js` for named service presence | Explicit `kind: public | manage | review`, feature policy, service availability, and backend capability inputs; old binary browser APIs removed. | Direct module projection checks plus public static graph, service-config, lifecycle, and route smokes pass. |
| 2. Configured-scope provider — complete | `docs-viewer-configured-scope-provider.js`; `docs-viewer-generated-data-runtime.js` remains transport/retry owner | Named index/document/search/recent/reference reads and optional source methods without granting authority. | Pure provider module smoke, focused source-service pytest, and public/manage smoke profile pass. |
| 3. Route features and startup — complete | `docs-viewer-route-features.js`; app composition and focused constructors consume the normalized projection | Validate known feature ids, preserve current behavior, and construct/initialize only enabled search, recent, bookmark, report, scope-selection, source-edit, and management surfaces. | Feature/config/startup module smoke, focused lifecycle/config pytest, and public/manage smoke profile pass. |
| 4. View/mode/control projection | new shared `docs-viewer-view-registry.js` for code-owned definition normalization and eligibility projection | Combine shared definitions, manage entrypoint contributions, app context, backend capabilities, route policy, and active view/mode state. | Pure registry/projection tests; public graph proof; narrow renderer DOM proof. |
| 5. Touched coordinator reduction | focused `docs-viewer-service-composition.js`, route-feature factory, or view-toolbar coordinator only where phases 1-4 establish a complete contract | Move construction and coordination out of the private runtime without mechanical splitting; remove obsolete bridges and broad facade fields. | Owner-contract tests plus unchanged baseline checks for affected boundaries. |

Names for new owner modules may change only if the implementation establishes a clearer single responsibility before editing. A different name must not change the ownership boundary or introduce a compatibility alias.

## Phase 1 Task: Explicit App Context And Authority

Target context:

```text
kind
routeAccess
featurePolicy
serviceAvailability
backendCapabilities
```

Current public and manage routes exercise only `public` and `manage`. The shape must be capable of expressing a future local non-management context without adding a boolean matrix, but no `review` route or behavior is added in this slice.

Tasks:

- retain route identity and path normalization in route config/context
- make entrypoint app kind explicit and validate it against route composition
- project public/manage visibility from named route-access rules rather than from backend reachability
- project `generatedData`, `source`, and `management` service presence independently
- keep backend capabilities absent/unknown until the owning service response supplies them
- update hosted-view and display-mode access checks to consume named app kinds or access requirements
- update app session, view context, route workflow, runtime lazy loading, boot datasets, and report access callers in the same slice
- preserve management-only dynamic loading and public graph isolation
- remove `allowManagement` and derived `publicReadOnly` from current browser APIs after callers move; do not keep aliases

Acceptance:

- current public and manage behavior and checks remain unchanged
- local generated-read availability is not structurally conditional on general management UI
- service presence does not authorize backend operations
- app kind is not inferred from service reachability or one management boolean
- a future local non-management composition is representable without adding behavior for it
- public routes receive no management/review modules, source services, capability probes, or local base URLs

## Phase 1 Outcome

Implemented on 2026-07-11.

### Current Contract

- Phase 3 introduced `docs_viewer_route_config_v3` for explicit features; Phase 4 moved current records to v4 for code-owned definitions and route-only narrowing.
- Every route record declares `app_kind` and narrow `access.allow_scope_query` / `access.management_ui` policy.
- Public and manage entrypoints provide their expected app kind; route normalization rejects mismatches.
- App context supports `public`, `manage`, and future `review` kinds. No review route, entrypoint, provider, or product behavior was added.
- App context exposes `kind`, `routeAccess`, `featurePolicy`, `serviceAvailability`, and a `backendCapabilities` slot initialized to `null`.
- Service context exposes independent `generatedData`, `source`, `management`, and browser-safe `config` surfaces.
- `generatedData` always exists and chooses static assets or an optional local generated-read URL.
- `source` and `management` are absent unless their own service records provide base URLs.
- Management shell/lazy startup requires explicit manage UI composition and an available management surface.
- Source-editor service slots depend on source-service presence, not on app kind or management-service presence.
- Hosted-view and document-mode access consume explicit app kind and route composition policy.
- Public versus richer metadata projection consumes `appContext.kind`.
- Backend capability responses remain the authority for operations; service URL presence does not authorize writes.

Removed browser contract fields include the former management/read-only booleans and combined generated/management URL fields. No aliases remain.

### Phase 1 Checks

| check | result |
| --- | --- |
| Focused public-boundary, static-asset, and service-config pytest set | pass: 18 tests |
| Scope lifecycle and management-route pytest set | pass: 25 tests |
| Direct app/route/service-context module smoke | pass |
| Metadata hosted-view context module smoke | pass |
| `docs-viewer-smoke` profile | pass: 4 checks; see `var/admin/test-runs/docs-viewer-foundation-phase-1-final/summary.md` |

## Phase 2 Outcome

The current configured-scope implementation now exposes one collection-facing contract:

```text
readIndex
readDocument
readSearch
readRecentlyAdded
readReferences
readSource       optional
writeSource      optional
```

- `docs-viewer-configured-scope-provider.js` owns active/explicit scope resolution, configured payload URLs, reference-index paths, and targeted reference-bucket paths.
- `docs-viewer-generated-data-runtime.js` remains the static/local generated-read transport, capability-cache, retry, reload, and payload-normalization owner.
- App composition constructs the provider and an optional source-service adapter; no provider lifecycle was added to the private runtime coordinator.
- Route workflow, search/recent, document extras, manage reports, and Markdown source editing consume named provider methods.
- Providers without an explicit source adapter do not contain `readSource` or `writeSource` keys.
- Supplying a source adapter creates callable methods, not authority. Backend capability and endpoint validation remain authoritative.
- No returned-package provider, review route, or Docs Review behavior exists in this phase.

### Phase 2 Checks

| check | result |
| --- | --- |
| Focused public-boundary, static-asset, service-config, and source-service pytest set | pass: 22 tests |
| Configured-scope provider/router module smoke | pass |
| `docs-viewer-smoke` profile | pass: 4 checks; see `var/admin/test-runs/docs-viewer-foundation-phase-2-final-entrypoint/summary.md` |
| Studio docs and search dry-run | clean: 0 writes, 0 removals, 0 warnings |

## Phase 3 Outcome

Phase 3 established the v3 feature contract. Current v4 route records retain the same feature array and declare only known feature ids:

```text
configured-scope-discovery
scope-selection
search
recently-added
bookmarks
reports
source-editing
management
```

- `docs-viewer-route-features.js` owns normalization, unknown-id rejection, the scope-selection dependency, feature queries, and filtering of code-owned hosted-view/mode records.
- Public routes declare configured-scope discovery, search, recently added, bookmarks, and reports. The manage route adds scope selection, source editing, and management.
- Route config requires search, recently-added, and report URLs only when the corresponding feature is enabled.
- App composition filters search/recent hosted views and startup records. The runtime omits disabled search/recent, bookmark, and management controller construction and binding.
- Shell composition omits disabled search/recent controls, scope selection, management shell/theme startup, and source-editing controls. Source display modes are filtered before host construction.
- Document extras are supplied only when reports are enabled.
- `loadConfiguredScopes` and `loadViewerSettings` are independent config-controller commands over one cached browser-safe envelope. Viewer settings can load from a payload without `scopes`.
- No route config can register executable modules or handlers, and feature presence does not grant backend authority.
- No review route, returned-package provider, or Docs Review behavior exists in this phase.

### Phase 3 Checks

| check | result |
| --- | --- |
| Focused public-boundary, static-asset, service-config, and scope-lifecycle pytest set | pass: 37 tests |
| Route feature/config/startup/toolbar module smoke | pass |
| `docs-viewer-smoke` profile | pass: 4 checks; see `var/admin/test-runs/docs-viewer-foundation-phase-3-final/summary.md` |
| Studio docs and search dry-run | clean: 0 writes, 0 removals, 0 warnings |

## Later Phase Acceptance

### Phase 2

- complete: current routes read through the configured-scope provider
- complete: consumers call named provider methods rather than reconstructing payload/service fallbacks
- complete: source methods are absent unless explicitly supplied
- complete: provider presence grants no write or management authority

### Phase 3

- complete: current route behavior is reproduced by explicit feature projections
- complete: unknown feature ids fail route normalization
- complete: disabled features have no controller, binding, startup phase, or required URL
- complete: configured-scope discovery is distinct from general viewer settings

### Phase 4

- complete: one code-owned projection resolves views, document modes, and eligible controls
- complete: shared definitions and manage entrypoint contributions remain separate at import boundaries
- complete: route policy can only narrow known definitions
- complete: Markdown source remains a document display mode
- complete: control handlers and live state remain controller-owned
- complete: no empty toolbar renders when every eligible control is hidden

### Phase 5

- new foundation ownership is not implemented by additional callback bridges in `docs-viewer-app-runtime.js`
- extracted owners have complete responsibilities and narrow inputs
- obsolete bridges and duplicate facade fields are removed without aliases
- no Docs Review code exists

## Docs Review Prerequisite Classification

Required before the Docs Review readiness checkpoint:

- explicit app context and independent service surfaces: phases 1 and 2
- non-scope provider support: phase 2
- optional route features/startup: phase 3
- authorized non-manage Markdown mode and control projection: phase 4
- only coordinator reductions needed to keep those responsibilities out of the private runtime: phase 5
- external returned-package workspace roots and validated exact-source package support: separate W0 and Data Sharing workstreams

Not required for Docs Review:

- broad management coordinator decomposition
- scope lifecycle or canonical mutation refactors
- general CSS consolidation
- unrelated report/import cleanup
- a split of the `studio` documentation corpus into additional documentation scopes

## Phase 0 Completion

- Public and manage entry/module boundaries are inventoried.
- Route, access, service, startup, controller, state, and toolbar contracts are recorded.
- Current durable owner documents are linked from the D0 authority map and this tracker.
- The view/mode request has been converted to the accepted code-owned projection task.
- Focused public/manage baseline checks pass.
- No code or compatibility path was removed in Phase 0.
