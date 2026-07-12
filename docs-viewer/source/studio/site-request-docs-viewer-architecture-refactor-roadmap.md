---
doc_id: site-request-docs-viewer-architecture-refactor-roadmap
title: Docs Viewer Architecture Assessment And Refactor Roadmap
added_date: 2026-07-10
last_updated: 2026-07-12
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Docs Viewer Architecture Assessment And Refactor Roadmap

## Status

Assessment complete; roadmap accepted for implementation, D0, W0's Data Sharing/review slice, phases 0-5, the Docs Review readiness checkpoint, and the validated-package Docs Review phase 6 consumer are complete. Phase 7 is active with Slices 7.1 through 7.5 complete.

The `studio` corpus remains the single reference scope for development and maintenance documentation. Separate product and shared-development documentation scopes are not part of this roadmap.

Implementation should be planned as behavior-preserving refactor slices before work resumes on [Docs Review](/docs/?scope=studio&doc=docs-viewer-review).

## Decision

Pause Docs Review implementation while Docs Viewer receives a standalone architecture assessment and a limited foundation refactor.

Docs Review is a useful pressure test because it needs the existing tree, document renderer, source editor, route state, build pipeline, and local services without inheriting all canonical management behavior. Those requirements expose real architectural constraints, but the fixes should be implemented and verified as Docs Viewer platform work rather than hidden inside a review feature branch.

The sequence is:

1. establish a documentation authority map, current contracts, and baseline checks
2. separate user, operator, architecture, reference, and historical concerns through ownership and entry points within the existing `studio` scope
3. replace the binary public/manage model with explicit app context and capabilities
4. introduce a generated-data/source provider boundary
5. make route features and startup phases explicit
6. centralize view, display-mode, and toolbar-control projection
7. reduce only the coordinator responsibilities touched by those changes
8. reassess Docs Review against the new contracts
9. implement Docs Review as a separate product slice
10. continue the broader documentation rewrite and non-blocking maintainability work as separately tracked workstreams

Do not mix full-package export, review-package endpoints, review UI, or returned-package editing into the foundation refactor.

## Scope

This assessment covers:

- public, manage, and future review app contexts
- boot, app composition, app session, and private runtime coordination
- route/access/service context
- generated-data and source-service authority
- panel views, document display modes, and toolbar controls
- controller construction and state-domain boundaries
- management orchestration
- local service routing and capability projection
- scope lifecycle and canonical mutation planning
- config ownership
- runtime, staging, preview, and user-workspace path authority
- test architecture
- user, operator, architecture, reference, and change-request documentation

It does not propose a whole-system rewrite.

## Current Strengths

Docs Viewer already has useful architectural foundations:

- separate public and manage entrypoints
- a shared app boot and shell contract
- route-config and access projection
- named app-session state domains
- a generated-data runtime owner
- focused route, document, search, bookmark, sidebar, info-panel, and panel-layout controllers
- lazy management loading that protects public routes
- hosted-view records and lifecycle helpers
- document display-mode hosting
- explicit public/manage import-boundary tests
- backend source revision checks and write/rebuild helpers
- focused services for many import, export, report, data-sharing, and source operations

The problem is not absence of structure. The runtime is midway through a transition from large coordinators and broad shared state to focused owners and explicit contracts.

## Assessment Summary

The highest-value refactors are not determined by file size alone. They are the areas where one decision currently controls several unrelated concerns or where a feature must receive broader authority than it needs.

| priority | area | evidence | Docs Review prerequisite |
| --- | --- | --- | --- |
| 1 | app context and capability model | public/manage behavior is derived mainly from `allowManagement` | yes |
| 2 | data/source provider boundary | generated reads and source services assume configured scopes and management | yes |
| 3 | explicit route features and startup | config, search, recent, bookmarks, and scope startup are broadly constructed | yes |
| 4 | view/mode/control projection | availability and toolbar decisions are split across registries, hosts, renderers, and controllers | yes |
| 5 | private runtime coordinator | `docs-viewer-app-runtime.js` remains a large callback bridge and feature assembler | partial |
| 6 | management coordinator | `docs-viewer-management.js` still coordinates several independent workflows | partial |
| 7 | state-domain enforcement | named domains exist, but fields and mutable facades still overlap | partial |
| 8 | management/backend lifecycle structure | scope lifecycle, manifest, mutation, and HTTP dispatch have broad surfaces | no |
| cross-cutting | documentation authority and information architecture | 63 directly related Docs Viewer/request documents have no clear user-guide entrypoint and mix current behavior, implementation inventory, future design, and historical decisions | the authority map is required; the full rewrite is not |
| cross-cutting | user-workspace artifact roots | Data Sharing, Docs import, review-session, and media-preview paths are currently contracted under repo-local `var/` | external Data Sharing/review roots are required before Docs Review |
| 9 | config/test/CSS consolidation | several declarative layers and tests describe overlapping models | no |

## Finding 1: Binary Public/Manage Context

The current runtime treats `allowManagement` as the main dividing line for:

- app mode
- service base URLs
- local generated-read authority
- source-editor service availability
- management controller loading
- hosted-view access
- visibility of manage-oriented metadata
- route behavior

Relevant owners include:

- `site/docs-viewer/runtime/js/shared/docs-viewer-access.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-service-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-view-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-composition.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js`

This produces a false choice:

```text
public static reader
or
full local management
```

Docs Review needs a third combination:

```text
local generated reads
+ temporary source writes
+ review build
+ package manifest and asset reads
- general canonical management
```

The target is an explicit app-context and service-capability model. Route identity controls composition and presentation; backend capability responses control actual authority.

## Finding 2: Service Authority Is Coupled To Presentation

`docs-viewer-service-context.js` currently exposes the local generated-read base URL only when management is allowed. Source-editor services are similarly projected only through management-capable view contexts.

This couples:

- local service reachability
- local generated reads
- source reads and writes
- canonical management UI

These should be separate named service surfaces.

Suggested service-context shape:

```text
generatedData
source
management
review
reports
```

Each surface may be absent. Its presence does not imply that another surface is available.

## Finding 3: Configured Scope Is Too Central To Startup

The config controller expects a browser config with at least one scope and normal index, recent, and search URLs. It also owns scope selection, route projection, UI status policy, recently-added limits, and some management config handoff.

This makes temporary or non-scope collections harder than necessary and gives config loading several responsibilities:

- collection discovery
- active collection projection
- UI text/settings
- route state
- scope picker presentation
- feature defaults

The target should distinguish:

- route/app configuration
- active collection identity
- data provider
- optional viewer settings
- configured-scope discovery, when the route supports it

Public and manage routes should continue to behave identically after this separation.

## Finding 4: Shared Startup Constructs Too Much By Default

The private runtime constructs search, recent, bookmarks, configuration, document, route, info-panel, main-view, display-mode, sidebar, management-lazy, and status behavior in one startup path.

Several features tolerate missing controls, but tolerance is not the same as an explicit feature contract.

The target is a route feature projection such as:

```text
scopeSelection
search
recentlyAdded
bookmarks
reports
sourceEditing
management
```

Only enabled features should be constructed, initialized, bound, and given required payload URLs.

## Finding 5: View, Mode, And Toolbar Decisions Are Split

The current concepts are valid:

- panels host views
- the document main view has display modes
- active view/mode determines relevant toolbar controls
- access and backend capabilities determine availability
- route policy may narrow public presentation

The decisions are spread across:

- `docs-viewer-hosted-views.js`
- `docs-viewer-main-view-host.js`
- `docs-viewer-document-display-mode-host.js`
- `docs-viewer-panel-layout.js`
- `docs-viewer-main-view-renderer.js`
- bookmark and info controllers
- management document-action renderers
- management coordinator state
- source-editor state
- route config

Phase 4 implemented the accepted code-owned projection described below.

## View, Mode, And Control Projection Assessment

Retain these requirements from the current request:

- one normalization and lookup owner
- document display modes registered under the document view
- central eligibility and toolbar projection
- management contributions merged only through the manage entrypoint
- public runtime rejects management-only modes
- route policy can hide known public controls
- executable handlers remain runtime-owned
- no generic plugin/module-loader behavior

Change these parts of the proposed approach:

- Do not add a browser JSON registry as a second definition authority for built-in views, modes, and controls.
- Do not place executable handler ids in browser config.
- Do not make route config responsible for registering lifecycle implementations.
- Do not model live states such as pressed, dirty, busy, or pending as registry availability.
- Do not implement the registry before app context and capability inputs are explicit, or it will encode the current binary public/manage limitation.

Preferred target:

```text
code-owned definitions
+ entrypoint contributions
+ route feature policy
+ app context
+ backend capabilities
+ active view/mode state
= view/mode/control projection
```

Definitions answer what exists and where it belongs.
Policy can hide or narrow known definitions.
Controllers own handlers and live interaction state.
Renderers consume projected control records.

The former view/mode registry request is now the focused Phase 4 child task. Its earlier browser-JSON registry and handler-id design is superseded.

## Finding 6: Private Runtime Coordinator Remains Broad

`site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js` is currently about 996 lines and contains roughly 73 local construction or bridge functions.

Its legitimate responsibility is private application coordination:

- construct focused controllers
- connect their explicit command/service contracts
- bind top-level route events
- apply route-global changes
- return the small app handle

It also currently owns or constructs bridges for:

- source-editor services
- generated reload behavior
- status and busy projection
- pane switching
- bookmark/search command adapters
- toolbar/mode coordination
- management lazy context
- config route globals

Do not split the file mechanically. Extract complete responsibilities only when a named owner and stable contract are clear.

High-value extraction candidates:

- route feature/controller factory
- source-service composition
- status/busy controller
- main-view/display-mode toolbar coordinator
- service-adapter composition

New Docs Review lifecycle must not be added directly to this file.

## Finding 7: Management Coordinator Remains Broad

`docs-viewer/runtime/js/management/docs-viewer-management.js` is currently about 1,027 lines and contains roughly 67 local functions.

It already delegates capability, interaction, modal, and action work to child controllers, but it still coordinates:

- import initialization
- settings and metadata modal handoff
- capability and action projection
- route reloads
- scope and sub-scope lifecycle lazy loading
- draft/viewability state
- keyboard/root bindings
- context-menu behavior
- broad management-state facade construction

Further work should split by workflow ownership, not by helper size.

Priority candidates:

- import workflow controller
- metadata/settings workflow composition
- scope lifecycle controller
- management shell event router
- management view-model/projection owner

`docs-viewer-management-actions.js` may remain the command owner until individual command families gain independent state or lifecycle.

## Finding 8: State Domains Are Descriptive More Than Enforced

`docs-viewer-app-session.js` provides useful named domains, but several fields are reachable through more than one domain or are remapped into a broad management facade.

Examples include:

- management capabilities used by management and generated-read logic
- reload nonce/expected document used by selected-document and generated-data behavior
- expanded document ids used by document-index and panel-view behavior
- management context projected through route-session and management behavior

The next state refactor should:

- assign one owner per mutable field
- expose queries or commands to consumers instead of duplicating field authority
- remove facade fields when child controllers receive narrow domains
- keep browser-only view state separate from data and backend capability state
- avoid a global event bus or generic store rewrite

## Finding 9: Backend Hotspots Exist But Are Not All Review Blockers

Significant backend surfaces include:

- `docs_viewer_service.py`: local service config, static serving, HTTP dispatch, capability shaping, and server lifecycle
- `docs_scope_manifest.py`: manifest storage, create/delete planning, path policy, apply, build commands, and publish sync
- `docs_management_mutations.py`: canonical mutation planning
- `docs_write_rebuild.py`: source-write/rebuild orchestration and targeted/full fallback
- `docs_scope_config.py`: source config parsing, path resolution, external roots, publishing paths, and sub-scope config

Recommended priorities:

1. keep HTTP route dispatch thin and move feature behavior to focused services
2. split scope-manifest storage from create/delete workflow planning and apply
3. keep canonical mutations plan-first and centralize batch mutation execution
4. retain source write/rebuild as the single canonical rebuild boundary
5. narrow capability payload construction into feature-owned projections

Docs Review does not require all backend cleanup first. It requires a clean review route family, capability surface, returned-package provider, and isolated build/source services. The staged-JSONL collection import belongs to managed Docs Viewer Import rather than Docs Review or Data Sharing.

## Finding 10: Config Has Multiple Legitimate But Overlapping Layers

Current configuration includes:

- canonical scope config
- generated browser scope config
- local/manage route config
- public route config
- service config
- report registry
- hosted-view records and capability metadata

These layers have different security and deployment purposes, so consolidation should not mean putting everything in one file.

The goal is instead to define projection ownership:

- canonical scope config owns source/output/publish/build paths
- browser scope config owns browser-safe generated-data and presentation metadata
- route config owns route identity, app context, feature policy, panels, and browser-safe config URLs
- service config owns loopback service availability and server features
- code-owned definitions own lifecycle implementations and handlers

Avoid copying derivable data across layers when the owning builder or service can project it.

## Finding 11: Test Coverage Is Broad But Uneven

Docs Viewer has extensive Python and browser smoke coverage, including important public import-boundary tests. Some tests still prove architecture by reading source text or asserting hardcoded strings rather than exercising pure owner contracts.

Refactor testing should prefer:

- pure JavaScript module checks for access, feature, view/mode/control, state, and provider projections
- direct Python service tests for capability, path, mutation, and rebuild contracts
- static module-graph tests for public/manage/review asset boundaries
- route/service smokes only for boot and network integration boundaries
- minimal browser workflow coverage

Do not expand permanent tests around modal timing, control copy, focus choreography, or internal implementation strings.

## Finding 12: Documentation Needs Its Own Workstream

The runtime boundary, module ownership, panel hosts, toolbar model, info panel, view capability contract, JavaScript inventory, and view/mode registry request describe different stages of the ongoing extraction.

This is larger than identifying a few stale requests. The current cluster contains 63 directly related Docs Viewer and Docs Viewer request documents. Several current-state documents exceed 300 lines, the overview includes a long implementation inventory, and there is no obvious task-oriented Docs Viewer user-guide entrypoint.

The documents currently serve several legitimate but poorly separated purposes:

- user guidance: how to browse, search, edit, import, export, rebuild, and manage documents
- operator workflow: routes, services, setup, publishing, troubleshooting, and safe local operations
- architecture: current boundaries, ownership, state, data flow, authority, and invariants
- reference and inventory: files, fields, endpoints, generated payloads, and module catalogues
- change requests and history: proposed behavior, implementation sequence, tradeoffs, and superseded decisions

These purposes should not be collapsed into one large guide. They need explicit entrypoints and cross-links, with one current owner for each subject.

Examples of likely drift include:

- whether Markdown source is a main view or a document display mode
- whether hosted-view records represent lifecycle modules or renderer metadata
- which toolbar owns the index view toggle
- how public/manage access relates to backend authority
- whether a future registry is code-owned or config-owned

Each refactor slice must update the affected user guidance and durable architecture owner in the same change. Historical requests should not remain the only explanation of current architecture.

The first deliverable is an inventory and authority map, not a bulk rewrite. It should record, for every related document:

- document type and intended audience
- whether it describes current behavior, a proposal, or history
- the subject for which it is authoritative, if any
- overlapping or contradictory documents
- disposition: keep, focus, split, merge, supersede, or remove
- user-facing task coverage and known gaps

The companion subject map should answer `subject -> current durable owner -> user workflow guide -> relevant historical request`. This gives Codex and maintainers a reliable starting point while the longer rewrite proceeds.

The current Studio index exposes 13 top-level subject roots, including Docs Viewer, Analytics, Data Sharing, Admin, shared architecture, search, testing, UI, local setup, and change requests. The documentation problem is bigger than just Docs Viewer.

### Search

The current docs search is not literally title-only, but its indexed search terms are limited to document ID, title, parent title, and last-updated value. The builder does not currently include the existing front-matter `summary`, headings, or document body text in the docs search index.

Content-aware documentation search should be a separate change request, not hidden inside the documentation reorganisation. Its minimum requirements should include:

- `summary` as a first-class indexed and ranked field, below title matches but above broad body matches
- a decision on heading and body-text indexing, index size, result excerpts, and ranking
- summary coverage and quality reporting so missing or weak summaries are visible

Data Sharing already provides a route for externally enriching documents and populating summary fields. The documentation rewrite can improve summaries at source, while the search change request should own how those summaries are indexed, ranked, displayed, and handled when absent.

## Finding 13: User Workspace Artifacts Are Repo-Rooted

At assessment time, several user-facing workflow artifacts were hardcoded or schema-contracted beneath the repository's untracked `var/` tree:

- Data Sharing exports, returned-package staging, metadata, and review output under `var/analytics/data-sharing/`
- Docs source-import staging under `var/docs/import-staging/`
- Docs Review sessions under `var/analytics/data-sharing/import-preview/`
- catalogue source-media and generated-derivative previews under `var/catalogue/media/`

This was not just a display-path issue. Data Sharing's schema fixed its runtime roots to repo-relative `var/analytics/data-sharing/...` values, adapter validation repeated those exact paths, and several services resolved them with `repo_root / configured_path`. The completed Data Sharing/review W0 slice replaces that contract with registry v3 marker paths and one shared external workspace resolver.

Because `var/` is untracked, these artifacts are caught between two ownership models:

- repository-relative paths make them appear application-owned and couple them to a checkout
- source control provides no persistence, migration, backup, or cleanup lifecycle for them
- moving or recreating the checkout can strand user work
- multiple checkouts can create separate, conflicting copies of the same user workflow state
- a true installed local app would not normally store user staging and preview files inside its application directory

The target boundary is:

| artifact class | target authority |
| --- | --- |
| canonical source and tracked config | repository |
| tracked generated/public output | repository where the existing publish contract requires it |
| user-facing exports, imports, staging, returned review packages, and preview media | `$DOTLINEFORM_PROJECTS_BASE_DIR` workspace roots |
| short-lived process state, logs, locks, test runs, and operational reports | separately classified runtime/cache roots; not automatically part of this migration |

Use a shared workspace-root resolver rather than allowing each feature to join paths onto `repo_root`. Configuration should store marker-rooted or logical workspace paths, never user-specific absolute paths. Services should receive resolved roots explicitly and validate containment against the resolved workflow root.

The first required migration slice is Data Sharing and Docs Review:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/
  exports/
  import-staging/
  import-preview/
  meta/
```

The Docs Import staging slice is complete and documented by [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec): every Docs Import format reuses `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` through the same W0 workspace adapter. Catalogue media staging remains a later separately defined root.

Rules:

- do not fall back to old repo-local `var/` paths when the workspace root is unavailable
- advertise affected capabilities as unavailable with actionable setup guidance when `DOTLINEFORM_PROJECTS_BASE_DIR` is missing, invalid, unreadable, or unwritable
- preserve traversal, suffix, symlink, and containment checks against the external workflow root
- store artifact-relative filenames or marker-rooted display paths in manifests and metadata rather than checkout-relative or absolute user paths
- keep reviewed-package Docs Import explicitly repo-authorized even though its source provider reads from an external workspace
- use temporary project-base roots in tests instead of treating a temporary repository's `var/` directory as the production contract
- treat old `var/` workflow artifacts as disposable/manual-migration input; do not add compatibility reads or duplicate writes

This is a cross-app path-authority change involving Analytics, Data Sharing, Docs Viewer, Studio, and later media workflows. The completed Data Sharing/review slice is recorded in the active full-document-package work instead of a separate historical tracker. The complete audit of remaining `var/` usage is not a Docs Review prerequisite.

## Target Architecture

The target remains a small modular application, not a framework or plugin system.

```text
route config
  -> app context and route feature policy
  -> service context and backend capabilities
  -> data/source provider
  -> app composition
  -> focused controllers and hosts
  -> view/mode/control projection
  -> shell renderers
```

Ownership rules:

- route config describes; it does not execute
- entrypoints contribute code-owned local capabilities and modules
- backend capabilities authorize; browser visibility does not authorize
- providers adapt data/source authorities to viewer-facing methods
- controllers own workflow and live interaction state
- registries normalize definitions and availability
- renderers consume projections and emit refs/events
- coordinators connect owners but do not acquire feature behavior

## Roadmap Overview

| phase | title | relationship to Docs Review |
| --- | --- | --- |
| D0 | documentation inventory and authority map | prerequisite to foundation planning; not a full rewrite |
| W0 | external user-workspace artifact roots | separate cross-app change; Data Sharing/review slice required before Docs Review backend work |
| P0 | Data Sharing full document package | separate Data Sharing project; consumer package interface required before Docs Review, real export/intake required before end-to-end completion |
| 0 | runtime baseline and prerequisite contract reconciliation | prerequisite assessment |
| 1 | app context and authority | required |
| 2 | provider boundary | required |
| 3 | route feature/startup projection | required |
| 4 | view/mode/control projection | required |
| 5 | touched coordinator reduction | required only where phases 1-4 expose ownership |
| checkpoint | Docs Review readiness reassessment | complete; foundation sufficient |
| 6 | Docs Review implementation | separate feature project |
| 7 | management coordinator roadmap | general maintainability |
| 8 | backend lifecycle roadmap | general maintainability |
| 9 | config/test/CSS cleanup | ongoing/general maintainability |
| D1-D4 | documentation entrypoints, restructure, and rewrite | separate cross-cutting workstream within the `studio` reference scope |
| search request | summary-aware documentation search | separate follow-up; D0 records the requirement but does not implement it |

## Documentation Workstream D0: Inventory And Authority Map

Purpose: create reliable navigation through the current material before rewriting it.

Initial deliverable: [Docs Viewer Documentation Register And Authority Map](/docs/?scope=studio&doc=docs-viewer-documentation-register).

Tasks:

- create a Docs Viewer documentation register covering durable docs and related change requests
- classify each document as user guide, operator workflow, architecture, reference/inventory, or change request/history
- record current/proposed/historical status separately from `ui_status`
- create the subject-to-owner map described in Finding 12
- flag contradictions, mixed audiences, excessive scope, missing user workflows, and stale request decisions
- record summary presence and obvious summary-quality gaps for the later search/rewrite work
- identify the small set of current owner documents needed for phases 1-5
- propose focused batches for keep/split/merge/supersede/remove actions without performing the rewrite in this task

Acceptance:

- a maintainer or Codex can find the current owner for every phase 1-5 architecture subject without deriving it from a historical request
- user-facing workflow gaps are explicit rather than hidden inside technical notes
- every audited document has a proposed disposition
- no broad code refactor or documentation rewrite is mixed into the inventory task

## Workspace Workstream W0: External User-Workspace Artifact Roots

Purpose: remove checkout-relative authority from user-facing staging, preview, and exchange artifacts before Docs Review relies on those paths.

The Data Sharing/review slice is implemented inside the active full-document-package work so completed path work does not require another historical tracker. Later workspace-root slices remain separate cross-app work. The Data Sharing/review slice had to complete before Docs Review returned-package services could be implemented.

Data Sharing/review slice status: complete. The follow-on Docs Import staging migration is also complete and documented by [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec).

First-slice tasks:

- define one shared `DOTLINEFORM_PROJECTS_BASE_DIR` workspace-root resolver and marker-path convention
- migrate Data Sharing exports, returned staging, metadata, and returned review packages to `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`
- no folder paths should be hardcoded. general principle is that paths are editable in a config.
- remove schema constants and adapter validation that require repo-local `var/analytics/data-sharing/...`
- update Analytics, Data Sharing, and Docs Viewer services to consume explicit resolved workspace roots instead of joining runtime paths onto `repo_root`
- update capability projection and UI guidance for missing or invalid workspace roots
- update manifests, metadata, activity summaries, and API responses to use artifact-relative or marker-rooted paths
- update tests to provide isolated temporary project-base roots
- update current user/operator and architecture documents when the runtime contract changes
- inventory Docs import staging, catalogue media staging, and other preview folders as later slices

Follow-on Docs Import slice:

- treat `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` as the consistent user drop-zone for every Docs Import format
- reuse `configured_workspace_paths(repo_root).import_staging` and marker-path projection from `data-sharing/services/paths.py`
- migrate staged-file listing, containment, Markdown packages, interactive companions, and `staging_manual` media output together
- disable Docs Import cleanly when the workspace root is unavailable
- do not add a Docs-specific resolver, config path, repo-local fallback, or duplicate writes

Acceptance:

- the complete export -> external edit -> returned staging -> validated package workflow operates without writing user artifacts inside the repository
- Docs Review can list, build, and edit a validated folder resolved from the external workspace root
- Docs Review exposes no canonical source-write or promotion capability
- a missing workspace root disables only the affected capabilities and produces actionable guidance
- services have no fallback reads or duplicate writes to the retired repo-local Data Sharing/review paths
- remaining `var/` paths are explicitly classified rather than assumed to share one lifecycle

## Phase 0: Runtime Baseline And Prerequisite Contract Reconciliation

Purpose: establish the behavior that refactors must preserve and reconcile only the architecture contracts required for phases 1-5.

Phase 0 is complete. Its preserved baseline and checks are recorded here so later maintenance does not depend on a separate completed-work tracker.

Tasks:

- inventory current public and manage entrypoint module graphs
- record current route, startup, controller, service, state-domain, and toolbar contracts
- use the D0 authority map to name the current durable owner for every prerequisite contract
- correct contradictions in those prerequisite owner docs; leave unrelated consolidation to D1-D4
- define baseline public and manage checks
- rewrite the view/mode registry request into the target projection model or create a child implementation task and retire the request — complete
- document which changes are prerequisites for Docs Review
- remove no code unless an already-orphaned compatibility/prototype path has an unambiguous current owner

Acceptance:

- public/manage runtime boundaries are described consistently
- phase 1-5 work does not depend on deriving current behavior from a historical request
- baseline checks pass
- implementation tasks have named owners and no review feature behavior

### Phase 0 Preserved Baseline

Recorded on 2026-07-11 before the foundation changes:

- the public entry shim had four modules; the shared app-boot graph had 43 modules and no static manage-owned import
- the effective public graph had 46 unique modules; the effective manage boot graph had 52 before later lazy workflows
- `/library/`, `/analysis/`, and `/moments/` were fixed-scope public readers; `/docs/` was the scope-selecting local manage route
- app kind, generated reads, management UI, source-service exposure, and manage view access were inferred through a combined management-oriented authority chain
- startup declared event binding, config loading, viewer settings, bookmark initialization, optional management initialization, initial index/route loading, and optional import opening
- the state-domain audit identified duplicated panel expansion, UI-status lookup, non-viewable presentation, route identity, capability, reload, and management status fields

Baseline verification:

- focused public-boundary, static-asset, and service-config tests: 17 passed
- `docs-viewer-smoke`: three baseline checks passed
- baseline summary: `var/admin/test-runs/docs-viewer-foundation-phase-0-baseline/summary.md`

## Phase 1: Explicit App Context And Authority

Purpose: replace binary access inference with an explicit context that can later support review without granting management.

Implementation complete.

Proposed context shape:

```text
kind: public | manage | review
routeAccess
featurePolicy
serviceAvailability
backendCapabilities
```

The behavior-preserving implementation should introduce the model while exercising only current public and manage routes.

Tasks:

- separate app kind from `allowManagement`
- separate visibility/access projection from backend capability truth
- separate local generated-read availability from management availability
- replace `publicReadOnly: !allowManagement` assumptions with explicit context queries
- preserve manage-only lazy loading and public asset isolation
- provide compatibility-free current APIs and update all callers in the same slice

Acceptance:

- public and manage behavior is unchanged
- local generated-read authority is not structurally tied to general management
- contexts express the local non-management Docs Review route without adding a new boolean combination
- public entrypoint module graph remains free of local write modules

### Phase 1 Outcome

Implemented on 2026-07-11.

- route records and entrypoints use explicit matching `public`, `manage`, or future `review` app kinds
- app context exposes named route access, feature policy, service availability, and an initially empty backend-capability slot
- generated-data, source, management, and browser-safe config service surfaces are independent; URL presence does not authorize operations
- management shell and lazy startup require manage UI composition plus a management surface; source-editor services depend on the source surface rather than a combined management boolean
- public metadata projection remains narrow and public graphs contain no management or review modules
- the former binary management/read-only browser fields and combined generated/management URL fields were removed without aliases

## Phase 2: Data And Source Provider Boundary

Purpose: let the viewer consume a collection without assuming it is a configured scope.

Initial configured-scope provider methods should cover:

```text
readIndex
readDocument
readSearch
readRecentlyAdded
readReferences
readSource, when supplied by a local source service
writeSource, when supplied by an authorized local source service
```

Tasks:

- define the smallest provider interface from current call sites
- implement the existing configured-scope provider
- route feature-facing reads through the generated-data runtime/provider owner
- remove direct assumptions about management fallback paths from feature controllers
- keep source write methods absent unless explicitly supplied
- retain current retry, reload, and targeted capability behavior

Acceptance:

- existing public/manage routes use the configured-scope provider with unchanged behavior
- document, index, search, recent, and source consumers depend on named provider methods
- no returned-package provider exists yet
- provider presence does not grant backend authority

### Phase 2 Outcome

Implemented on 2026-07-11.

- Current public and manage collection reads use `docs-viewer-configured-scope-provider.js`.
- Route, document, search/recent, manage-report, and Markdown source consumers use named provider methods.
- The provider owns configured-scope URL and reference-target projection; `docs-viewer-generated-data-runtime.js` retains static/local transport, retry, reload, capability, and payload-normalization behavior.
- Read-only providers omit `readSource` and `writeSource`. A source-service adapter may explicitly supply either method, while backend capabilities remain authoritative.
- No returned-package provider or Docs Review behavior was added.

## Phase 3: Route Feature And Startup Projection

Purpose: construct only the controllers and payload requirements a route needs.

Tasks:

- define normalized route features
- separate configured-scope discovery from general app settings loading
- make search, recent, bookmarks, reports, scope selection, source editing, and management initialization explicit
- skip disabled startup phases and bindings
- make route config reject unknown feature ids
- preserve current public/manage defaults

Acceptance:

- current routes behave unchanged through explicit feature projections
- a route can omit search/recent/bookmarks/scope selection without fake URLs or hidden controller initialization
- startup authority records reflect actual enabled features

### Phase 3 Outcome

Implemented on 2026-07-11.

- Phase 3 introduced `docs_viewer_route_config_v3` with an explicit allowlisted `features` array; Phase 4 subsequently moved current records to v4 for route-only view policy.
- Current public routes enable configured-scope discovery, search, recently added, bookmarks, and reports. The manage route additionally enables scope selection, source editing, and management.
- Unknown features and invalid scope-selection dependencies fail normalization.
- Disabled search, recently-added, and report features do not require placeholder URLs.
- Disabled search/recent, bookmark, and management controllers are not constructed or bound; related hosted views, source modes, shell controls, startup phases, and theme loading are filtered by the same policy.
- Configured-scope discovery and general viewer-settings loading are independent operations over the browser-safe config envelope.
- No review route, returned-package provider, or Docs Review behavior was added.

## Phase 4: View, Mode, And Control Projection

Purpose: implement code-owned view, mode, and control projection without introducing a second config authority.

Tasks:

- add a shared code-owned definition/normalization owner
- register panel views and document display modes with their owning relationships
- accept shared definitions plus entrypoint contributions
- combine definitions with app context, backend capabilities, route policy, and active state
- project eligible toolbar controls for the active view/mode
- migrate `bookmark`, `info`, `edit`, `markdown-source`, and `save-markdown-source` first
- keep control handlers and live state in current focused controllers
- keep management toolbar/admin actions outside the document-view control registry

Acceptance:

- Markdown source remains a display mode of the document view
- public contexts cannot resolve management-only modes or controls
- manage mode retains current controls
- route policy can hide known public controls without runtime view-id branches
- no config file can invent handlers or modules
- no empty toolbar is rendered when no projected controls remain

### Phase 4 Outcome

Implemented on 2026-07-11.

- One code-owned registry now normalizes and resolves panel views, document modes, and document controls from shared definitions, manage entrypoint contributions, app context, features, backend capability inputs, route narrowing, and active view/mode state.
- Route records moved to `docs_viewer_route_config_v4`. Route policy can hide only registered ids and cannot define modules, handlers, views, modes, or controls.
- `bookmark`, `info`, `edit`, `markdown-source`, and `save-markdown-source` consume the shared eligibility projection while their focused controllers retain live behavior state.
- Markdown source remains a document mode under `rendered-document`; public contexts cannot resolve manage-only contributions.
- The superseded hosted-view registry and access helper were removed. Renderers omit the document toolbar when no projected controls remain.

## Phase 5: Coordinator Reduction For Touched Areas

Purpose: prevent phases 1-4 from adding more callback bridges to large coordinators.

Only extract responsibilities directly exposed by the foundation work.

Likely tasks:

- move service/provider construction into app composition or a focused service-composition owner
- move feature-controller construction into a focused factory
- move view/mode toolbar coordination into a focused controller
- give status/busy projection one owner if multiple new contexts need it
- remove obsolete function-scoped bridges after callers use named commands
- narrow management state facade fields used by migrated control projection

Acceptance:

- no review-specific code exists
- new app context/provider/feature/registry behavior is not owned by `docs-viewer-app-runtime.js`
- removed bridges have no aliases
- public/manage baseline behavior remains unchanged

### Phase 5 Outcome

Implemented on 2026-07-11.

- `docs-viewer-document-view-coordinator.js` now constructs and coordinates the main-view host, document display-mode host, info-panel controller, active view/mode state, control eligibility queries, info defaults, and rendered/search/recent view transitions.
- `docs-viewer-status-controller.js` owns viewer status text/error projection and nested busy-state accounting.
- `docs-viewer-app-runtime.js` no longer owns Phase 4 host construction, active control projection, mode/default-info synchronization, status DOM mutation, busy counting, or repeated mode-to-view transition chains. Its size fell from about 996 lines at assessment to about 834 lines.
- App-session domains no longer expose `expandedDocIds`, `uiStatusByValue`, `docNonViewableEmoji`, `managementContext`, management capabilities, reload state, management messages, or the view registry through duplicate facades. Generated-read capability payloads now live in `generatedDataCapabilities`, separate from management capability state.
- At the Phase 5 checkpoint, the management state facade read route identity only from `routeSession` and reload state only from `selectedDocument`; Slice 7.5 later removed that cross-domain facade entirely.
- Service/provider construction remains in app composition because Phase 2 had already established the correct owner.
- No review-specific code or generic event/store rewrite was added.

### Foundation Verification Record

| phase | focused proof | integration proof |
| --- | --- | --- |
| 0 | 17 public-boundary, static-asset, and service-config tests | baseline profile passed; `var/admin/test-runs/docs-viewer-foundation-phase-0-baseline/summary.md` |
| 1 | app/route/service-context and metadata-context module smokes; focused test sets passed | 4-check profile passed; `var/admin/test-runs/docs-viewer-foundation-phase-1-final/summary.md` |
| 2 | 22 focused tests and configured-scope provider/router smoke | 4-check profile passed; `var/admin/test-runs/docs-viewer-foundation-phase-2-final-entrypoint/summary.md` |
| 3 | 37 focused tests and route feature/config/startup/toolbar smoke | 4-check profile passed; `var/admin/test-runs/docs-viewer-foundation-phase-3-final/summary.md` |
| 4 | 25 focused tests and registry/router browser module smoke | 4-check profile passed; `var/admin/test-runs/docs-viewer-phase4-view-registry-final/summary.md` |
| 5 | 30 focused tests and router/runtime-owner browser module smoke | 4-check profile passed; `var/admin/test-runs/docs-viewer-phase5-coordinator-reduction-final/summary.md` |

## Docs Review Readiness Checkpoint

Checkpoint completed on 2026-07-11: passed.

Before resuming Docs Review, confirm:

- `review` can be expressed as an app context without `allowManagement`
- a route can supply a non-scope provider
- local generated reads and temporary source services can be supplied independently
- search/recent/bookmarks/scope selection can be omitted cleanly
- Markdown source and its toolbar controls can be registered for an authorized non-manage context
- public routes do not load review or management assets
- adding the review route requires no new lifecycle behavior in the private runtime coordinator
- Docs Review has an agreed validated-package consumer interface containing package-rooted Markdown, a trusted manifest, and optional package-local asset inventories; a fixture or manually seeded package may exercise that interface before the full export/intake producer exists

If these are true, the foundation refactor is sufficient. Do not delay Docs Review for unrelated scope lifecycle, CSS, report, or import cleanup.

Checkpoint evidence:

| criterion | result | evidence |
| --- | --- | --- |
| review context without management authority | pass | `review` is a first-class app kind; access projection forces `managementUi: false` outside `manage` |
| non-scope provider | pass | app composition accepts a code-owned `createCollectionProvider` factory and retains the configured-scope provider as its default |
| independent generated/source services | pass | review context can expose local generated reads and source service access while omitting the management service |
| optional route features | pass | an empty feature policy omits configured-scope discovery, search, recent, bookmarks, reports, scope selection, and management startup |
| review read-only package boundary | pass | the review entrypoint contributes no source mode or save controls, loads no management source-editor assets, and the focused backend exposes no package source capabilities or routes |
| public asset isolation | pass | public entrypoints retain public/shared imports only; review contributions are owned by the local review entrypoint |
| coordinator boundary | pass | provider, view, source, and shell contributions enter through existing boot/composition seams; no review lifecycle is added to the private runtime coordinator |
| package dependency | pass with sequencing clarification | preview may start from a representative package fixture; the real Data Sharing producer remains required before round-trip acceptance |

The checkpoint exposed and closed one foundation gap: app composition previously instantiated `createDocsViewerConfiguredScopeProvider` unconditionally. The new provider-factory seam is deliberately code-owned and validates the minimal `readIndex` and `readDocument` interface. It is not configured through browser JSON and grants no backend authority.

Verification evidence:

- focused router module smoke passed with custom-provider injection, provider-interface rejection, optional-feature startup, independent service surfaces, and review-only Markdown control projection
- the four-check `docs-viewer-smoke` profile passed at `var/admin/test-runs/docs-review-readiness-checkpoint/summary.md`
- the three-check docs test/build/search profile passed at `var/admin/test-runs/docs-review-readiness-checkpoint-docs/summary.md`

The fixture-backed Phase 6 consumer work identified at this checkpoint is now complete. The implemented `document-content` producer and managed collection importer provide the real reviewed round trip. The full source-and-asset export proceeds independently and is not a Docs Review dependency.

## Phase 6: Docs Review

Implement [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) as its own feature project after the readiness checkpoint.

Status: complete for the validated-package consumer and local review application, with the real `document-content` producer connected. The separate full source-and-asset request is export-only and does not block Docs Review.

Its implementation should consume:

- review app context
- review route feature policy
- returned-package provider
- shared view/mode/control projection
- shared tree, document, and source-editor primitives
- focused package-listing, manifest/asset-read, build, generated-read, and temporary source services

Docs Review must not receive configured-source import or promotion services. The planned transition from a returned package is a separate managed Docs Viewer collection import with explicit create, overwrite, or skip choices.

Docs Review must not be used as an excuse to complete unrelated roadmap items.

Delivered outcomes:

- independent review service authority and `/docs-review/` shell
- focused package, manifest, inventory, build, generated-read, asset-read, and temporary source services
- a returned-package provider selected by package identity rather than configured scope
- package-preserving navigation, rendered/source modes, revision-checked edits, hierarchy edits, Build, inventory visibility, and canonical comparison
- package-aware inventoried media rendering and sandboxed interactive HTML
- no canonical management, import, promotion, publish, or configured-scope mutation authority

Verification evidence:

- returned-package Python contract tests cover validation, containment, builds, generated reads, source revision/write, hierarchy cycles, media, and sandboxed interactive HTML
- the focused `/docs-review/` browser smoke covers route boot, automatic build, package identity, rendered/source switching, source save/rebuild, and canonical comparison
- the existing `/docs/` manage browser smoke remains green
- public runtime import-boundary tests exclude review and management modules

## Phase 7: Broader Management Coordinator Work

This phase is not a Docs Review prerequisite unless a touched workflow blocks a clean integration.

Status: active. Slices 7.1 through 7.5 are complete; command-family splitting remains demand-driven.

Candidate slices:

- extract import initialization and modal handoff — Slice 7.1 complete
- separate metadata and settings workflow composition — Slice 7.2 complete
- give scope/sub-scope lifecycle a focused controller — Slice 7.3 complete
- narrow the management event router — Slice 7.4 complete
- replace remaining broad management facade fields with explicit domains/queries — Slice 7.5 complete
- split action command families only when they have independent state or lifecycle

Each slice should preserve behavior and have its own task definition and verification set.

### Slice 7.1: Import Initialization And Modal Handoff

Task definition:

- move lazy Docs Import initialization state, module validation, retry handling, and boot-error projection out of `docs-viewer-management.js`
- give the management-side import action and modal handoff one focused controller
- preserve the existing import host, initial-scope projection, service/config URLs, first-open focus timing, and import preview/write owners
- do not widen import authority or move preview/write behavior out of the existing `docs-html-import*` modules

Delivered outcome:

- `docs-viewer-management-import-controller.js` owns the single in-flight lazy initialization and post-failure retry boundary
- the management coordinator supplies explicit host refs, service/config values, and scope/modal callbacks instead of retaining import lifecycle state
- the generic management modal controller remains the import modal-shell owner, while the focused import controller owns the management action-to-modal handoff
- public startup remains isolated because the new owner is reachable only through the lazy manage entrypoint graph

Verification set:

- JavaScript syntax checks for the focused owner and changed coordinator
- public runtime import-boundary tests
- focused manage-route smoke covering lazy management boot, import-module handoff, and service authority
- `git diff --check`

### Slice 7.2: Metadata And Settings Workflow Composition

Task definition:

- move metadata parent projection, form validation, payload shaping, and confirmed-save handoff out of `docs-viewer-management.js`
- move settings service loading, editable-field selection, and modal load/error handoff out of the coordinator
- compose metadata and settings workflow owners with the existing modal UI-state controller through explicit callbacks
- replace the action controller's broad modal-controller access with a narrow settings field/change/close contract
- preserve existing metadata and settings writes, route reloads, modal focus/visibility behavior, service authority, and import-modal behavior

Delivered outcome:

- `docs-viewer-management-metadata-workflow.js` owns metadata selection, validation, payload shaping, config refresh, and action delegation
- `docs-viewer-management-settings-workflow.js` owns the settings read/load boundary and exposes only the field-state, changes, and close commands required by settings writes
- `docs-viewer-management-modal-composition.js` resolves management shell refs and assembles the focused workflows with `docs-viewer-management-modals.js`
- `docs-viewer-management-actions.js` no longer receives a general modal controller; settings writes and post-write reloads remain with the existing action owner
- `docs-viewer-management.js` no longer owns metadata/settings refs or workflow behavior and is reduced from 1,009 to 851 lines across Slices 7.1 and 7.2

Verification set:

- JavaScript syntax checks for the new workflow/composition owners and changed management modules
- focused manage-route smoke covering metadata selection and settings service-read handoff without writes
- public runtime import-boundary and static-asset tests
- `git diff --check`

### Slice 7.3: Focused Scope And Sub-Scope Lifecycle Controller

Task definition:

- move lifecycle control projection, event wiring, lazy flow loading, flow-option composition, failure projection, and post-apply refresh out of `docs-viewer-management.js`
- keep `docs-viewer-scope-lifecycle.js` as the create/delete modal, preview, confirmation, apply, and result owner
- preserve capability-gated visibility, management busy/message projection, service-client authority, and config/capability refresh timing
- do not split create/delete flows or change backend manifest planning/apply ownership in this slice

Delivered outcome:

- `docs-viewer-management-scope-lifecycle-controller.js` owns the four scope/sub-scope lifecycle controls and the complete coordinator-side lifecycle contract
- the heavy lifecycle flow module remains lazy and is validated before the focused controller invokes it
- flow modules now receive only root, capabilities, client options, parent scope where required, and explicit lifecycle callbacks; the unused broad management-state handoff was removed
- `docs-viewer-management.js` no longer imports lifecycle capability helpers, resolves lifecycle controls, retains lifecycle loader state, wires lifecycle actions, or builds lifecycle callbacks
- the management coordinator is reduced from 1,009 to 695 lines across Slices 7.1 through 7.3

Verification set:

- JavaScript syntax checks for the focused lifecycle controller and changed management coordinator
- focused manage-route smoke proving the lifecycle flow is absent at boot, lazily loaded by New Scope, and cancellable before preview or write
- public runtime import-boundary and static-asset tests
- `git diff --check`

### Slice 7.4: Narrow Management Event Router

Task definition:

- move stable management-control binding and Actions-menu toggle/dismissal behavior out of `docs-viewer-management.js`
- move ordered root-click and document-keydown delegation into a focused router
- dispatch only named commands to existing action, import, metadata, settings, interaction, modal, and scope-lifecycle owners
- preserve event ordering, dismissal behavior, control event types, and the small management runtime handle
- do not introduce a generic event bus or move command/workflow behavior into the router

Delivered outcome:

- `docs-viewer-management-event-router.js` owns stable control binding, named command dispatch, Actions-menu behavior, and interaction/modal root and keyboard delegation
- the router consumes focused controller getters and command callbacks rather than management state or backend services
- `docs-viewer-management.js` no longer defines root/keyboard routers, Actions-menu behavior, or the management `bind()` function and is reduced from 1,009 to 612 lines across Slices 7.1 through 7.4
- the focused smoke exposed and the slice fixed a pre-existing settings-modal focus race by snapshotting the loaded field type before the scheduled focus callback

Verification set:

- JavaScript syntax checks for the event router, coordinator, and focused modal race fix
- focused manage-route smoke covering Actions-menu outside-click/Escape dismissal plus import, metadata, settings, and scope-lifecycle control routing
- public runtime import-boundary and static-asset tests
- `git diff --check`

### Slice 7.5: Explicit Management Domains And Queries

Task definition:

- remove the management-local cross-domain property facade rather than moving it to another module
- pass document-index, selected-document, search/recent, route-session, scope-config, and management domains only to consumers that use them
- keep current-selected-document and current-context-menu lookups as explicit coordinator queries
- remove management capability writes to generated-read state and preserve the generated-data runtime as its sole owner
- preserve route reload, search/reset, metadata, settings, interaction, lifecycle, and action behavior

Delivered outcome:

- `docs-viewer-management.js` consumes the six named management domains directly and no longer defines proxy properties or remaps mutable fields
- capability, interaction, action, config, metadata, settings, modal, and scope-lifecycle controllers receive only their required named domains
- the metadata parent picker dropped an unused state argument rather than retaining a compatibility-shaped handoff
- management capability checks now mutate only management capability state and route-session context; `docs-viewer-generated-data-runtime.js` remains the sole generated-read capability owner
- unused management-client generated-read/search capability helpers were removed after their ownership moved entirely to the generated-data runtime
- the focused capability smoke now asserts the positive management/route-session domain contract without synthetic generated-read fields
- the management coordinator is reduced from 1,009 to 574 lines across Slices 7.1 through 7.5

Verification set:

- JavaScript syntax checks across every changed management-domain consumer
- focused management-capability module smoke for management and route-session projection
- focused manage-route smoke covering management boot and the previously exercised import, metadata, settings, event-router, and lifecycle boundaries
- public runtime import-boundary and static-asset tests
- `git diff --check`

## Phase 8: Backend Lifecycle And Mutation Work

Candidate slices:

- split `docs_scope_manifest.py` into manifest repository, create plan/apply, and delete plan/apply owners
- split scope/sub-scope frontend lifecycle by create/delete workflow
- project management capabilities from feature-owned helpers
- separate local static serving and API family dispatch where that reduces service-handler branching
- centralize batch canonical mutation execution around existing plan-first models
- keep rebuild orchestration in `docs_write_rebuild.py`
- review source-config and manifest duplication only after owner contracts are explicit

These are general maintainability improvements. Implement them according to churn, feature pressure, and failure risk rather than file length alone.

## Phase 9: Config, Tests, And CSS

Ongoing work:

- document canonical, browser, route, service, and code-definition config ownership
- remove duplicated derived fields when one owner can project them
- keep public browser config allowlisted
- replace source-string tests with owner-contract tests where practical
- retain public import-graph tests
- prefer pure module/service checks over browser choreography
- audit base/manage/report CSS after toolbar and view ownership stabilizes
- consolidate CSS only around clear component ownership

## Documentation Workstream D1-D4: Rewrite

This workstream follows D0 in separately reviewable documentation batches. It spans the architecture roadmap but is not a single gate on Docs Review.

### D1: Entry Points And Information Architecture

- create a short user-facing Docs Viewer entrypoint organized by tasks rather than modules
- create a short maintainer entrypoint that points to current architecture owners
- separate user guidance, operator workflow, architecture, reference, and history in navigation
- add a concise scope statement to each retained document

### D2: User And Operator Guidance

- document actual user workflows independently of implementation notes
- cover browsing, search, source editing, rebuilding, import, export, scope management, and troubleshooting as applicable
- link to architecture only where it helps an operator understand a constraint
- keep planned Docs Review behavior out of current user guidance until it ships

### D3: Current Architecture Consolidation

- keep the overview short and move file-by-file detail to focused reference documents
- consolidate overlapping runtime, panel, view/mode/control, service, and config explanations around named owners
- split documents that serve multiple audiences or unrelated responsibilities
- remove superseded current-state prose only after its replacement owner is present and linked

### D4: Change-Request Hygiene And Automated Checks

- distinguish proposed, active, completed, and superseded requests
- transfer implemented decisions into current owner docs before closing a request
- link requests to their durable outcome without making the request the current authority
- add mechanical checks for duplicate IDs, invalid parents, broken internal doc links, and required classification metadata if D0 proves metadata is useful
- treat document length and heading breadth as review signals, not hard failure limits

### Separate Change Request: Documentation Search Discovery And Relevance

Create a dedicated change request after D0 has confirmed the scope model. It should own search summary-aware indexing and ranking, result presentation, and the possible later use of headings or body text.

## Recommended Implementation Sequence

Recommended order of work (to be reviewed after each step):

1. create the D0 documentation register and authority map as a dedicated assessment task — initial register complete and ready for review
2. create the separate Documentation Search Discovery And Relevance change request
3. implement the W0 Data Sharing/review root slice inside the active full-document-package work — complete
4. record the phases 0-5 baseline, outcomes, and verification evidence directly in this roadmap — complete
5. complete the runtime baseline and reconcile only prerequisite contracts — complete
6. begin D2 user/maintainer entrypoint work as a separate documentation batch
7. implement explicit app context and authority — complete
8. implement the configured-scope provider boundary — complete
9. implement explicit route features and startup — complete
10. implement the code-owned view/mode/control projection — complete
11. reduce only coordinator bridges made obsolete by steps 8-11 — complete
12. update affected user guidance and architecture owners with each slice
13. complete the W0 Data Sharing/review path slice, which may run in parallel with phases 0-5 — complete
14. approve the validated-package consumer interface; continue the full source-and-asset export independently — consumer interface complete, export request active and not a review dependency
15. run the Docs Review readiness checkpoint — complete
16. update the Docs Review spec only if the platform or package contracts materially changed — checkpoint sequencing clarified
17. implement Docs Review through its active request, beginning with a fixture-backed preview vertical slice — complete for the validated-package consumer
18. continue D1-4, the search request, later W0 slices, and phases 7-9 according to current risk and feature demand

## What Not To Refactor Yet

Avoid broad rewrites of these areas until after the docs-preview work:

- `DocsDataBuilder` and its mixin pipeline
- self-contained report implementations
- tree rendering
- established document URL/history behavior
- focused import/export modules
- semantic-reference helpers
- public route shells beyond the context/feature changes required above
- CSS
- Large files are maintenance-issue signals.

## Verification Strategy

Baseline and phase checks are recorded above and should run only where a slice touches their contract.

Potential focused checks:

- pure module checks for access/app context
- pure module checks for view/mode/control projection
- provider contract checks using current generated payload fixtures
- route-config normalization checks
- public module-graph boundary tests
- management capability and route tests
- current Docs Viewer route/router module checks
- focused `/docs/` service smoke after any local route composition changes
- public `/library/`, `/analysis/`, and `/moments/` checks after any public config/runtime changes
- `bin/site-validate` after any tracked public assets change

Do not use a full browser smoke as the default proof for pure refactor contracts.

## Refactor Guardrails

- Preserve public/manage behavior unless a separate product request changes it.
- Do not add compatibility aliases for moved modules, routes, fields, or config keys.
- Move callers and tests with the current owner in the same slice.
- Do not add new feature lifecycle ownership to either large coordinator.
- Do not let browser config grant backend write authority.
- Do not let a repo-relative `var/` path stand in for user-workspace authority merely because the path is ignored by Git.
- Do not let review providers or workflow services derive external artifact roots by joining paths onto `repo_root`.
- Do not turn hosted views or control definitions into a plugin system.
- Do not mix Docs Review product behavior into phases 0-5.
- Do not combine a broad documentation rewrite with a code refactor slice.
- Do not delete or supersede a document until its current responsibilities have a named replacement owner.
- Keep user instructions about shipped behavior separate from proposals and architecture rationale.
- Keep each slice independently reviewable and reversible through ordinary version control.
- Update affected user guidance and durable architecture owners with each completed slice.

## Success Criteria

The foundation roadmap is complete when:

- app context is not a synonym for `allowManagement`
- local read and write service surfaces are independently expressible
- configured scopes are one provider implementation rather than a viewer-wide assumption
- route features control startup and payload requirements explicitly
- views, document modes, and active toolbar controls use one code-owned projection model
- public/manage behavior and asset boundaries remain intact
- touched callback bridges and duplicate state authority are removed
- the D0 authority map identifies the current documentation owners for the foundation contracts
- the W0 Data Sharing/review slice provides an explicit external workspace-root contract for Docs Review
- Docs Review can begin without adding review behavior to the private runtime or management coordinator

The broader architecture, D1-D4 documentation, documentation-search, and later W0 workspace-path workstreams remain active after that checkpoint; they are not blanket gates on the Docs Review feature.
