---
doc_id: docs-viewer-documentation-register
title: Documentation Register And Authority Map
added_date: 2026-07-11
last_updated: 2026-07-11
ui_status: review
summary: Audit register, authority map, overlap findings, and proposed dispositions for the Docs Viewer documentation set and its active change requests.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Documentation Register And Authority Map

## Purpose

This is the D0 documentation authority map for the [Docs Viewer Architecture Assessment And Refactor Roadmap](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap).

It identifies the current owner documents needed by refactor phases 1-5, classifies the existing Docs Viewer material, and records focused follow-up dispositions. It is an assessment and navigation aid, not a rewrite of the audited documents.

The `studio` corpus remains the single reference scope for development and maintenance documentation. The documentation workstream will improve classification, entry points, and ownership within that scope; it will not create separate product and shared-development documentation scopes.

## Audit Boundary And Vocabulary

The baseline set contains 70 documents:

- the `docs-viewer` root and its 63 pre-existing descendants in the Studio index
- six adjacent Docs Viewer or Docs Review change requests under `change-requests`

This register is not counted in that baseline. Repo-wide owners such as [Development Checklist](/docs/?scope=studio&doc=development-checklist), [Testing](/docs/?scope=studio&doc=testing), [Public Route Model](/docs/?scope=studio&doc=public-route-model), and [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) appear in the subject map where they constrain Docs Viewer work, but are not reclassified here.

Document types:

- **user guide**: task-oriented product usage
- **operator workflow**: setup, commands, services, publishing, and troubleshooting
- **architecture**: current boundaries, ownership, state, authority, and invariants
- **reference**: fields, files, endpoints, generated payloads, reports, or inventories
- **change request**: proposed work, implementation decisions, or retained history

Status describes the prose, independently of `ui_status`:

- **current**: intended to describe the implemented system
- **proposed**: describes unimplemented or not-yet-accepted behavior
- **historical**: retained outcome or superseded design context
- **mixed**: combines more than one of those states or more than one audience

Dispositions are proposals for later focused batches. `Focus` means narrow the document to one audience or subject. `Split` and `merge` require a replacement owner before prose is removed. `Supersede` retains history through a change-request link after current decisions are transferred.

## Phase 1-5 Subject Authority Map

| subject | current durable owner | workflow or reference support | historical or proposed context | D0 finding |
| --- | --- | --- | --- | --- |
| Docs Viewer entry point | [Docs Viewer](/docs/?scope=studio&doc=docs-viewer) | [Overview](/docs/?scope=studio&doc=docs-viewer-overview) | architecture roadmap | Current entry is maintainer-oriented; no short task-oriented user entry exists. |
| Public/manage entrypoints and import boundary | [Runtime](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) | [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership), [Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces), [Static Route Template](/docs/?scope=studio&doc=docs-viewer-static-route-template) | architecture roadmap | These are the phase 0 baseline owners. Keep the public graph free of local service and write modules. |
| App kind, route access, and visibility | [Runtime](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) | [Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts), [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract) | architecture roadmap | Current prose still derives several decisions from public/manage access. Phase 1 needs an explicit app-context owner. |
| Service availability and backend authority | [Runtime](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) | [Health And Capabilities Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-health-capabilities), [Generated Read Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-generated-reads) | architecture roadmap | Browser visibility, service reachability, and backend capability truth are not yet described by one focused contract. |
| Generated-data reads and provider boundary | [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts) | [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership), [Builder](/docs/?scope=studio&doc=scripts-docs-builder) | architecture roadmap | Payload authority is documented; the phase 2 viewer-facing provider contract does not exist yet. |
| Source reads and writes | [Source Editor Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-editor) | [Source Editor Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-source-editor), [Management Operations](/docs/?scope=studio&doc=scripts-docs-management-server-operations) | Docs Review request | Current owners describe manage authority. Phase 2 must document source methods as optional provider capabilities, not as app-kind implications. |
| Route config and configured-scope discovery | [Config](/docs/?scope=studio&doc=config-docs-viewer) | [Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces), [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) | architecture roadmap | Canonical, browser, route, and service config purposes need a concise projection-ownership table. |
| Startup phases and route features | [Overview](/docs/?scope=studio&doc=docs-viewer-overview) | [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) | architecture roadmap | No focused current owner explains enabled features, constructed controllers, and required payloads. Phase 3 must create or focus one. |
| App-session state domains | [Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts) | [Overview](/docs/?scope=studio&doc=docs-viewer-overview) | architecture roadmap | Named domains are described inside broader documents; mutable-field ownership is not a focused contract. |
| Panel hosts and hosted views | [Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts) | [Info Panel](/docs/?scope=studio&doc=docs-viewer-info-panel), [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract) | `docs-viewer-view-registry.js` | Panel/layout and eligibility owners are explicit; keep capability prose scoped to layout. |
| Document display modes and toolbar controls | [Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model) | [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract), [Info Panel](/docs/?scope=studio&doc=docs-viewer-info-panel) | `docs-viewer-view-registry.js`, architecture roadmap | The code-owned registry is the current projection owner. |
| Runtime and management coordinator ownership | [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) | [Overview](/docs/?scope=studio&doc=docs-viewer-overview), [Management Scripts Overview](/docs/?scope=studio&doc=scripts-docs-management-scripts) | architecture roadmap | Phase 5 should update module ownership only for responsibilities actually extracted. |
| CSS surfaces | [CSS Cascade Design](/docs/?scope=studio&doc=docs-viewer-css-cascade-design) | [Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces) | architecture roadmap phase 9 | Current owner exists; no broad CSS consolidation is a phase 1-5 prerequisite. |
| Refactor checks and public isolation | [Development Checklist](/docs/?scope=studio&doc=development-checklist) and [Testing](/docs/?scope=studio&doc=testing) | [Runtime](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) | architecture roadmap | Use pure module contracts, static module graphs, and focused service checks; avoid UI choreography coverage. |
| Docs Review product boundary | [Docs Review Workflow](/docs/?scope=studio&doc=site-request-docs-review-workflow) | [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) | architecture roadmap | Remains paused until the readiness checkpoint; it is not a current Docs Viewer workflow. |

## Contradictions, Overlaps, And Gaps

### Prerequisite Contract Issues

- `docs-viewer-overview` mixes a user-facing overview with a long runtime module inventory. Runtime detail should resolve through `docs-viewer-runtime-boundary`, `docs-viewer-runtime-module-ownership`, and `docs-viewer-runtime-surfaces`.
- `docs-viewer-panel-hosts` records current owners and the history of several extraction slices. Its current panel/app-session contract needs separating from implementation chronology.
- `docs-viewer-view-capability-contract` and `docs-viewer-toolbar-model` overlap on current availability and control placement. Phase 0 converted the old registry request into the code-owned Phase 4 projection task; browser config cannot invent lifecycle modules or handler ids.
- Current service documentation describes local generated reads and source services mainly through the management route. Phase 1 must distinguish service presence from management UI composition and backend authorization.
- Generated payloads have a durable owner, but no current document owns the configured-scope provider interface proposed for phase 2.
- Startup construction is described in overview and module-inventory prose, but no current contract maps route features to controllers, bindings, and required URLs.

### Audience And Navigation Gaps

- There is no short Docs Viewer user guide organized around browse, navigate, search, recent, bookmarks, display modes, and information panels.
- Source editing, rebuild, import, export, scope management, reports, and troubleshooting are distributed across user, endpoint, script, and architecture documents without an operator entry point.
- Portable setup, new-scope creation, public scopes, config, and shell-template documents overlap on route and scope setup.
- Semantic references are described by a report, editor guide, implementation document, and draft request; their current versus proposed boundaries need explicit cross-links.
- The completed Markdown-export request and existing export/import reference documents do not yet point to one concise durable package-contract owner.

### Summary Coverage

At the start of D0, only 2 of the 70 audited documents had a front-matter `summary`: `docs-viewer-dependencies` and `docs-viewer-public-route-shell-template`.

Phase 0 added summaries to eight prerequisite owner documents and the converted view/mode/control child task. Current audited-set coverage is therefore 11 of 70. The D0 register and architecture roadmap also have summaries but are outside the original 70-document baseline.

The first summary batch should cover the Docs Viewer entry point, the phase 1-5 durable owners in the subject map, user guides, and active change requests. Endpoint and file-inventory summaries can follow as a mechanical reference batch. Summary writing alone does not change search until the separate search request implements summary indexing and ranking.

## Register: Entry Points, User Workflows, Architecture, And Reference

| document | type | status | present authority | disposition | summary |
| --- | --- | --- | --- | --- | --- |
| `docs-viewer` | architecture / entry point | mixed | Docs Viewer section entry and high-level boundaries | Focus as a short user/maintainer router; move runtime inventory to existing owners. | missing |
| `docs-broken-links` | reference / report | current | Generated broken-links report surface | Keep as generated report; link to the script/operator owner. | missing |
| `scripts-docs-broken-links` | operator workflow / reference | current | Broken-links command and report data source | Keep and add a concise summary. | missing |
| `scripts-docs-builder` | operator workflow / reference | mixed | Build mechanics and generated outputs | Focus command usage and builder contract; move broad payload explanation to generated-data contracts. | missing |
| `config-docs-viewer` | reference / architecture | current | Docs Viewer config layers | Focus around projection ownership and browser/server boundaries. | missing |
| `docs-viewer-css-cascade-design` | architecture | current | Stylesheet order and host responsibilities | Keep; defer consolidation work to phase 9. | missing |
| `docs-viewer-dependencies` | reference | current | Docs Viewer-specific dependency boundary | Keep. | present |
| `docs-data` | reference | mixed | Studio docs search data notes | Merge current payload facts into generated-data/search owners; retain only a focused data reference if distinct content remains. | missing |
| `user-guide-docs-images` | user guide | current | Docs images and asset workflows | Keep and add entry-point links. | missing |
| `user-guide-docs-html-import` | user guide / operator workflow | mixed | Import modal workflow and implementation detail | Focus on user workflow; move service/parser detail to import reference owners. | missing |
| `docs-viewer-public-route-shell-template` | architecture / reference | current | Generated public shell template contract | Keep. | present |
| `docs-viewer-static-route-template` | architecture / reference | current | Public/manage shell and ready-state contract | Focus on shared mount and entrypoint boundaries; cross-link the generated public template owner. | missing |
| `scripts-docs-export` | operator workflow / reference | current | Documents package preparation command | Keep; align terminology with the durable package contract. | missing |
| `scripts-docs-import` | operator workflow / reference | current | Returned package parser command | Keep; state clearly that parsing is not canonical apply/promotion. | missing |
| `site-request-docs-viewer-embedded-detail-documents` | change request / architecture | mixed | Implemented sub-scope detail behavior and retained decisions | Focus current behavior into a durable owner, then move or supersede the request-shaped document. | missing |
| `docs-viewer-export` | operator workflow / reference | mixed | Static HTML export and package inputs | Split user/operator steps from payload/file reference, or focus around one contract. | missing |
| `docs-viewer-import-source-registry-spec` | architecture / change request | proposed | Proposed import source registry | Keep as proposed until implementation status is reconciled; do not present it as current authority. | missing |
| `docs-viewer-info-panel` | architecture | current | Info-panel hosted-view behavior and context | Keep; narrow availability prose to the future shared projection owner. | missing |
| `library-documents` | reference / report | current | Generated Library documents report | Keep as generated report. | missing |
| `docs-viewer-media-handling` | operator workflow / architecture | mixed | Docs media paths, import staging, and copy behavior | Split workflow guidance from path/security architecture when the external workspace-path slice changes it. | missing |
| `docs-viewer-new-scopes-builder` | operator workflow / architecture | mixed | New scope creation and route/publish decisions | Split into task workflow plus focused config/route reference; no new documentation scope is implied. | missing |
| `docs-viewer-overview` | architecture / entry point | mixed | Current runtime overview and large module inventory | Split/trim; make runtime owners authoritative and leave a concise system overview. | missing |
| `docs-viewer-panel-hosts` | architecture | mixed | Panel hosts, app context, session domains, and extraction history | Focus on current panel/view/state contracts; remove chronology after replacements are linked. | missing |
| `docs-viewer-portable-setup` | operator workflow | current | Portable setup entry point | Keep as a short task router. | missing |
| `docs-viewer-portable-files` | reference | current | Portable file manifest | Keep; reconcile with current tracked/static ownership. | missing |
| `docs-viewer-portable-scope-setup` | operator workflow | current | Public and managed scope setup procedures | Focus around supported route types and config-driven paths. | missing |
| `docs-viewer-portable-source-shape` | reference | current | Minimum portable source document shape | Keep. | missing |
| `docs-viewer-public-scopes` | architecture / operator workflow | mixed | Public scope model and setup details | Focus on public scope architecture; move procedures to portable setup. | missing |
| `docs-viewer-reports` | architecture / reference | current | Report metadata, access, modules, and rendering | Keep; update capability terms with phase 1. | missing |
| `docs-viewer-runtime-boundary` | architecture | current | Public/manage install and shared-runtime boundary | Keep as the primary phase 0-1 runtime authority. | missing |
| `docs-viewer-generated-data-contracts` | architecture / reference | current | Generated payload ownership and schemas | Keep as primary payload authority; add provider links in phase 2. | missing |
| `docs-viewer-javascript-inventory` | reference | current | File-level browser module inventory | Keep as reference; do not use it as behavior authority. | missing |
| `docs-viewer-runtime-module-ownership` | architecture / reference | current | Grouped browser runtime owner map | Keep and update with each ownership-moving slice. | missing |
| `docs-viewer-runtime-surfaces` | architecture / reference | current | Route, shell, config, CSS, and payload surface matrix | Keep; add explicit app-context and route-feature rows in phases 1 and 3. | missing |
| `docs-viewer-semantic-references` | reference / report | current | Generated semantic references report | Keep as generated report. | missing |
| `docs-viewer-semantic-references-editor` | user guide / architecture | mixed | Current editor behavior and integration | Focus user workflow; move implementation ownership to the implementation document. | missing |
| `docs-viewer-semantic-references-implementation` | architecture / reference | current | Semantic-reference source, registry, builder, and runtime ownership | Keep as current implementation owner. | missing |
| `docs-viewer-source-config-report` | reference / report | current | Generated source-config report | Keep as generated report. | missing |
| `docs-viewer-source-organisation` | architecture / reference | current | Source roots, hierarchy, and ordering | Keep; preserve `studio` as the reference development/maintenance scope. | missing |
| `docs-viewer-toolbar-model` | architecture | current | Toolbar regions and present control placement | Focus on layout/ownership; transfer eligibility projection to the phase 4 owner. | missing |
| `doc-ui-status` | user guide / reference | current | UI-status options and config owner | Keep; shorten generated-config implementation detail where possible. | missing |
| `docs-viewer-view-capability-contract` | architecture | mixed | Hosted-view availability fields and route config | Merge accepted current rules into panel and phase 4 projection owners, then supersede this overlapping contract. | missing |
| `docs-viewer-viewable-field` | user guide / reference | current | Source `viewable` field and build/runtime effects | Keep. | missing |

## Register: Management Services, Endpoints, And Script Inventory

| document | type | status | present authority | disposition | summary |
| --- | --- | --- | --- | --- | --- |
| `scripts-docs-live-rebuild-watcher` | operator workflow / reference | current | Live rebuild watcher behavior and commands | Keep. | missing |
| `scripts-docs-management-server` | operator workflow / reference | current | Management service entry and reference router | Keep as a concise router. | missing |
| `scripts-docs-management-endpoints` | reference | current | Management endpoint family index | Keep as endpoint router. | missing |
| `scripts-docs-management-endpoints-create-import` | reference | current | Create/import HTTP contracts | Keep; link user workflows separately. | missing |
| `scripts-docs-management-endpoints-generated-reads` | reference | current | Local generated-read HTTP contracts | Keep; update service-surface terms in phase 1. | missing |
| `scripts-docs-management-endpoints-health-capabilities` | reference | current | Health and capability payload contracts | Keep; distinguish backend authorization from browser projection in phase 1. | missing |
| `scripts-docs-management-endpoints-rebuild-audit` | reference | current | Rebuild and audit HTTP contracts | Keep. | missing |
| `scripts-docs-management-endpoints-scope-lifecycle` | reference | current | Scope create/delete HTTP contracts | Keep; not a phase 1-5 refactor prerequisite. | missing |
| `scripts-docs-management-endpoints-source-config` | reference | current | Source-config HTTP contracts | Keep. | missing |
| `scripts-docs-management-endpoints-source-editor` | reference | current | Source read/write/open HTTP contracts | Keep; link the optional source-provider methods in phase 2. | missing |
| `scripts-docs-management-endpoints-source-mutations` | reference | current | Metadata/viewability/mutation HTTP contracts | Keep. | missing |
| `scripts-docs-management-server-operations` | operator workflow | current | Security and operational service guidance | Keep and expose through the future operator entry point. | missing |
| `scripts-docs-management-scripts` | reference | current | Management Python module family index | Keep as a concise router. | missing |
| `scripts-docs-management-scripts-audit` | reference | current | Audit module ownership | Keep. | missing |
| `scripts-docs-management-scripts-import` | reference | current | Import module ownership | Keep. | missing |
| `scripts-docs-management-scripts-read-config` | reference | current | Read/config/capability module ownership | Keep; update capability projection ownership in phase 1. | missing |
| `scripts-docs-management-scripts-rebuild-follow-through` | reference | current | Write/rebuild/build/search boundary | Keep. | missing |
| `scripts-docs-management-scripts-route-dispatch` | reference | current | HTTP dispatch and service context modules | Keep; maintain thin dispatch. | missing |
| `scripts-docs-management-scripts-service-entrypoints` | reference | current | CLI/service entrypoints | Keep. | missing |
| `scripts-docs-management-scripts-source-editor` | reference | current | Source service module ownership | Keep; update provider linkage in phase 2. | missing |
| `scripts-docs-management-scripts-source-mutations` | reference | current | Mutation and scope-manifest module ownership | Keep; broader lifecycle cleanup belongs to phase 8. | missing |

## Register: Related Change Requests

| document | type | status | present authority | disposition | summary |
| --- | --- | --- | --- | --- | --- |
| `site-request-data-sharing-full-document-package` | change request | proposed | Exact Markdown package and validated-return prerequisite | Keep active and separate from the runtime foundation refactor. | missing |
| `site-request-docs-document-content-markdown-export` | change request | historical | Completed Markdown-export decision and outcome | Transfer durable package behavior to export owners, then retain as superseded history. | missing |
| `site-request-docs-review-workflow` | change request | proposed | Planned Docs Review product boundary | Keep paused until the roadmap readiness checkpoint. | missing |
| `site-request-docs-viewer-architecture-refactor-roadmap` | change request | active | Foundation refactor sequence and guardrails | Keep durable outcomes and verification evidence directly in the roadmap. | missing |
| `site-request-docs-viewer-semantic-reference-editor` | change request | mixed | Draft V2 goals beside implemented V1 behavior | Reconcile with current editor/implementation owners, then retain only genuinely proposed work. | missing |
| `site-request-docs-viewer-view-mode-registry` | change request | implemented | Phase 4 code-owned view, mode, and control projection task | Outcomes are retained in the architecture roadmap; eligible for later retirement. | present |

## Proposed Documentation Batches

1. **Phase 0 prerequisite owners**: initial baseline reconciliation and summaries are complete for runtime boundary, module ownership, runtime surfaces, generated-data contracts, overview, panel hosts, toolbar model, and view capability prose; later entry-point work still needs to focus `docs-viewer` itself.
2. **User and operator entry points**: create task-oriented navigation for reading/search/bookmarks and for source edit/rebuild/import/export/scope operations/troubleshooting.
3. **Route and setup overlap**: focus config, static/public shell templates, portable setup, public scopes, and new-scope builder around distinct owners.
4. **Import/export/media**: separate workflow guidance from package, service, parser, and path/security reference.
5. **Semantic references**: reconcile report, editor, implementation, and request status.
6. **Management reference summaries**: add concise summaries to endpoint and script-inventory documents after their owner boundaries stabilize.
7. **Change-request hygiene**: transfer implemented outcomes, mark superseded requests, and keep Docs Review and full-package work explicitly separate from phases 1-5.

## D0 Completion Check

- The audit set and proposed disposition for every document are recorded above.
- The current owners and gaps for every phase 1-5 architecture subject are explicit.
- User and operator workflow gaps are listed separately from architecture contradictions.
- Summary coverage is measured without assuming that summaries are already searchable.
- The documentation corpus stays in the `studio` reference scope.
- No broad documentation rewrite or runtime refactor is included in this task.

Foundation phases 0-5 are complete and their durable evidence is consolidated into the architecture roadmap. The Docs Review readiness checkpoint is next. Documentation-search and external workspace-path requests remain separate workstreams and do not require a documentation-scope migration.
