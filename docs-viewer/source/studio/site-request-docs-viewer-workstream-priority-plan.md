---
doc_id: site-request-docs-viewer-workstream-priority-plan
title: Docs Viewer Workstream Priority Plan
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Workstream Priority Plan

Status:

- needs rewriting following the app refactor of Docs Viewer
- remove completed work
- existing change requests need to be linked to, with minimal description here.
- new change requests need creating where policy and proposals go

## Summary

Coordinate the active Docs Viewer architecture and product workstreams so implementation can proceed in useful slices without losing the larger direction.

Current active or near-active workstreams:

- panel architecture with hosted module support
- `docs-viewer.js` risk reduction and focused ownership extraction
- JavaScript frontend / explicit backend app-shell direction
- manage-mode Markdown source editor for semantic-reference insertion
- repo-specific Studio/dotlineform semantic-reference expansion and infrastructure
- portable Docs Viewer packaging and installation
- local/uncommitted Docs Viewer data storage outside the public repo publishing path

These workstreams overlap, but they should not be merged into one large rewrite.
The aim is to define dependencies, sequencing, and decision points so each slice can land independently while moving toward the same product architecture.

## Guiding Principles

- Keep browser UI composition, panel/view state, client-side reads, and view modules in JavaScript where practical.
- Prefer direct browser reads for browser-safe repo artifacts; do not route reads through local server contracts just because a module boundary exists.
- Keep source writes, rebuilds, filesystem access, backups, validation, and local operational capabilities behind explicit backend endpoints.
- Keep public presentation and local manage mode as two contexts of the same Docs Viewer app.
- Use manage mode to incubate operational, experimental, dependency-heavy, or still-uncertain modules before promoting them to public presentation.
- Avoid a broad `docs-viewer.js` refactor as a prerequisite; extract focused ownership as implementation slices require it.
- Keep generated docs/search/reference payloads as the main public-safe read contract.
- Keep true local/uncommitted data work aligned with a workspace/data-root abstraction, not ad hoc path exceptions.

## Workstream Map

| Workstream | Current artifact | Role | Dependency posture |
| --- | --- | --- | --- |
| App shell frontend/backend boundary | [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell) | Defines the browser app, generated data/config, and backend boundary. | Current enabling slice. Do this now before adding panel, source editor, third-party module, or portability runtime surface. |
| Portable Docs Viewer | [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) | Reduces host integration work and documents portable install shape. | Outcome track; should consume proven app-shell and config/data contracts. |
| Workspace/local data roots | [Docs Viewer Workspace Mount Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-workspace-mount-architecture) | Defines repo-backed and external/local data workspaces. | Foundation for true local/uncommitted data. Can proceed in parallel with UI work but affects backend/build paths. |
| Panel architecture and hosted modules | [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell) | Adds index/document/info panel model and pragmatic optional module hosting. | Should follow the app-shell enabling slice, but does not require a full JS shell migration. |
| Focused Markdown source editor | [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor) | Adds this repo's manage-only source editing and semantic token insertion. | Depends on management source read/write/rebuild endpoints and Studio semantic support data. Does not require full panel architecture. Not portable Docs Viewer core. |
| Semantic references v1 | [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references) | Existing dotlineform/Studio token grammar, builder parsing, and generated reference artifacts. | Implemented v1; not portable Docs Viewer core. |
| Semantic references v2 | [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2) | Reviews v1 against the clarified architecture and defines editor/panel support data. | Prerequisite for semantic editor target support and richer reference modules. |
| `docs-viewer.js` risk reduction | [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) | Tracks shared runtime risk and extraction opportunities. | Should happen through focused owner modules required by product slices, not as a standalone rewrite first. |

## Semantic Reference Expansion Request

The semantic-reference expansion request now exists as [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2).
It should cover:

- supported Studio/dotlineform semantic types beyond current v1
- generated/browser-safe support data for target picker/search UI
- client-side Studio semantic support reads and option normalization
- validation and warning policy for unsupported semantic types and actions
- relationship between semantic references, broken-link audits, reports, and future graph/panel modules
- public versus manage-only promotion criteria for richer reference views
- explicit statement that semantic links are not portable Docs Viewer core unless a later host-extension contract is defined
- a prerequisite review/refactor of v1 before editor or panel modules depend on expanded semantic-reference behavior

## Dependency Order

This is the recommended order for implementation decisions, not a requirement that every item fully complete before the next starts.

### 1. Implement The App-Shell Enabling Slice

Use the JavaScript app-shell request as the current prerequisite implementation slice.
This is no longer only a north-star document.
It is the work needed now so panels, hosted modules, source editing, semantic-reference v2, and portable Docs Viewer can share the same runtime direction.

Immediate decisions:

- browser modules own UI state, view registration, generated-data reads, and panel/module lifecycle
- backend owns source writes, rebuilds, filesystem access, and protected capabilities
- public and manage mode stay one app with access-gated views/actions
- browser-safe repo data should be read directly by browser modules from generated/static artifacts
- local service reads are reserved for source files, protected/local data, external workspaces, capability checks, and data that is not available or should not be exposed as static browser assets

This should guide every slice below.
It does not require a full shell rewrite before product work starts, but it does require enough concrete app-shell structure to stop the next features from inventing their own boundaries.

Immediate tasks:

- keep the app-shell request as the owning implementation reference for this enabling slice
- inventory current Docs Viewer read paths enough to identify which reads are browser-safe repo artifacts, which are protected/source reads, and which are service-backed only for local workspace reasons
- define the minimal optional-module registration shape needed by the panel/source-editor work, including how a missing or disabled module is omitted without breaking route boot
- define the public/manage/manage-local access flags used by views, panel actions, and optional modules
- list the source-editor data surfaces before implementation: source Markdown read/write via backend, target-picker support data via browser-safe generated/config reads where practical, and rebuild/capability checks via backend
- identify the first `docs-viewer.js` orchestration seams that must call focused owners without moving unrelated route/search/bookmark behavior
- decide whether the first code slice needs a new app boot/orchestration module or can safely start with focused owners called by the existing runtime entrypoint

Acceptance:

- the panel and semantic-editor slices can name their browser-owned state, read data, backend calls, and access gates before code is written
- no new local server read endpoint is added for browser-safe repo data without a documented reason
- optional repo-specific modules can be absent or disabled without route boot failure
- the app-shell request creates enough durable guidance that later portable Docs Viewer docs do not mistake dotlineform-only features for core package features

### Browser-Safe Repo Reads

For this repo, avoid calling another local server endpoint just to read data that is already available in the same repo as a browser-safe artifact.

Default rule:

- use direct browser reads for generated/static JSON, browser config, UI text, report registries, semantic support data, and other public-safe repo artifacts
- use focused browser modules to normalize and shape those reads for panels, modals, pickers, and route views
- use backend endpoints for writes, rebuilds, source Markdown reads, filesystem access, protected/local-only data, capability checks, external workspace roots, and anything that cannot or should not be exposed as static generated data

This is a repo-specific implementation preference, not a claim that every future portable install must expose the same artifacts statically.
Workspace-mounted or external local data may require service-backed reads, but repo-backed browser-safe data should not be forced through local HTTP contracts only to maintain a theoretical boundary.

### 2. Keep `docs-viewer.js` Refactoring Enabling-Only

Do not start with a broad cleanup of `docs-viewer/runtime/js/docs-viewer.js`.

Preferred approach:

- define focused owner modules when a slice needs them
- keep the entry runtime as boot/orchestration adapter
- move complete responsibilities out when they become clear, such as panel projection, source editor orchestration, semantic target reads, or toolbar rendering
- add focused module tests for extracted behavior

This keeps momentum while reducing risk over time.

### 3. Add A Minimal Panel/View Host Slice

Add the smallest useful panel architecture before the source editor so the editor can prove the panel model instead of creating a parallel source-editing surface.

Initial panel work should include:

- panel state/projection module
- document and info panel view hosts
- basic toolbar/view selection
- info panel show/hide behavior
- lifecycle shape for hosted modules
- access gating for public, manage, and manage-local views

Do not try to solve every future visualization or external-library question in this slice.
The aim is to create just enough structure for document and info panel modules to coordinate.

### 4. Build Manage-Mode Source Editing As The First Hosted Workflow

The semantic-reference editor is a high-value near-term workflow because it has a clear purpose and limited public impact.
It should become the first practical consumer of the panel/view host model.

Recommended shape:

- document panel hosts the editable Markdown source view
- info panel hosts available token kinds, target search/results, selected target details, and insertion controls
- backend provides source read and full-source write/rebuild endpoints
- client-side modules handle source editing, token insertion, and target lookup
- target lookup reads browser-safe repo/generated data directly where practical

This keeps token controls out of an overloaded document toolbar and gives the panel architecture an immediate proving workflow.

### 5. Define Semantic-Reference Expansion Infrastructure

Before adding many target kinds or rich reference modules, complete the v2 prerequisite review in [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2).

Then decide:

- what target registries are supported first
- what generated lookup artifacts the browser can read
- what remains manage-only until stable
- how reference data powers reports, info panels, graph modules, and audits
- how to keep dotlineform semantic-link behavior separate from portable Docs Viewer core

This work supports both the source editor and hosted panel modules.

### 6. Broaden The Generic Panel / Hosted Module Architecture

After the minimal panel slice and source editor have proven the shape, broaden the hosted-module architecture.

Follow-on work can include:

- richer info-panel views such as metadata and references
- module asset/import metadata
- stronger mount/update/unmount/dispose lifecycle conventions
- support for external libraries such as D3.js or Cytoscape.js where justified
- downstream portable module extension patterns

The architecture should be ready for D3.js, Cytoscape.js, and downstream modules, but it should not choose those libraries in the first slice.
Modules should start as clearly identifiable optional folders with a small registration surface, not a tight adapter framework.
If a module folder is absent or disabled, Docs Viewer core should omit the related feature instead of failing route boot.

### 7. Advance Workspace Mounts For True Local Data

Local/uncommitted data storage needs the workspace-mount architecture.

Near-term split:

- repo-backed local/committed or local/uncommitted paths can use current shape with careful ignore and preview warnings
- true external application data needs workspace roots, service-backed reads, and builder/search/rebuild path abstraction

Do not solve this by adding special-case paths to each endpoint.
Use the workspace request to preserve a future standalone Docs Viewer path.

### 8. Fold Proven Contracts Into Portable Docs Viewer

Portable Docs Viewer should consume stable contracts after they are proven:

- app-shell boot/config boundary
- panel/module host conventions
- public/manage access gates
- workspace/read/write configuration
- optional module asset declarations

Portable docs should not become the place where uncertain local-only experiments are documented as public install requirements.
Dotlineform semantic links and the manage-mode semantic editor should not be documented as portable Docs Viewer core unless a future host-extension contract is explicitly added.

## Practical Priority

Recommended near-term priority:

1. Implement the app-shell enabling slice: route context/config normalization, access gates, optional-module registration shape, read-path classification, and first focused `docs-viewer.js` ownership seams.
2. Implement a minimal panel/view host slice with document and info panel hosts.
3. Implement the focused Markdown source editor as the first hosted manage-mode workflow.
4. Complete the semantic-reference v2 prerequisite review before expanding target support or richer reference modules.
5. Extract only the `docs-viewer.js` responsibilities needed by the panel, editor, and target lookup modules.
6. Broaden the hosted-module architecture after the first workflow proves the shape.
7. Continue workspace-mount design for local/uncommitted data roots.
8. Update portable setup after contracts are proven.

This order gives the project the app-shell boundary first, then the panel foundation, then immediately validates both with a useful authoring workflow while avoiding premature public UI, visualization-library, or standalone packaging commitments.

## Cross-Workstream Decisions

### Public Versus Manage Mode

Default rule:

- uncertain modules start in manage mode
- public promotion requires explicit generated/public-safe data, accessibility, performance, visual design, and portability decisions

### Third-Party Libraries

Default rule:

- visualization libraries belong in browser panel/view modules
- heavy libraries are lazy-loaded
- modules mount, update, unmount, and dispose inside app-owned containers
- backend/generator provides explicit data artifacts, not browser rendering instructions
- portable Docs Viewer may support optional visualization modules conceptually, but host projects must provide the data and integration contract unless Docs Viewer later defines a document-derived data class
- portable Docs Viewer should not ship third-party visualization libraries or user-facing config for them until that contract exists

### Source Editing

Default rule:

- source editing is manage-only
- source writes happen once through explicit `Rebuild doc`
- backend validates front matter and source contract, not all Markdown body content
- builder diagnostics report unsupported semantic types/actions
- semantic-reference target ids are opaque host ids, not Docs Viewer-validated objects
- semantic editing is this repo's manage-mode integration, not portable Docs Viewer core

### Local Data

Default rule:

- public/generated site data can remain in static repo output paths
- manage-only/generated local data should move toward service-backed reads
- true local/uncommitted data should resolve through workspace roots

### Existing Read-Path Review

This direction should trigger a focused review of existing Docs Viewer read paths.

Review goal:

- identify local-server reads that only proxy browser-safe repo artifacts
- keep or add service reads where data is source/private/local-only, external-workspace-backed, capability-gated, or unavailable as static generated output
- prefer browser module reads for generated repo JSON and config where public/manage safety allows it

This review should start with the app-shell enabling slice, then continue as implementation work touches affected surfaces.
It should not become a broad blocking audit, but it is part of doing the app-shell work now.

## Risks

- implementing product slices directly inside `docs-viewer.js` could increase the highest-risk runtime file
- panel, editor, and semantic-reference work could invent incompatible target lookup or module registration patterns
- local/uncommitted data work could become scattered path exceptions instead of a workspace abstraction
- portable Docs Viewer docs could expose experimental manage-only modules as public requirements
- semantic-reference expansion could outgrow the v1 request without a clear registry/data contract
- repo-specific semantic links could be mistaken for portable Docs Viewer functionality
- optional modules could become over-abstracted before there is a real downstream extension need
- local server read contracts could spread into places where direct browser reads of repo-generated data are simpler and clearer

Mitigations:

- require each slice to name its focused owner modules
- keep optional module boundaries pragmatic: clear folders, clear registration, and graceful absence
- keep `docs-viewer.js` as orchestration where possible
- complete the semantic-reference v2 review before expanding registries or graph/reference modules
- use manage mode as the incubation context for uncertain features
- update portable docs only after implementation contracts are stable
- keep workspace-root decisions centralized in the workspace mount request
- document dotlineform semantic-link features as repo-specific integrations, not generic Docs Viewer capabilities
- review affected read paths during implementation and prefer direct browser reads for browser-safe repo artifacts

## Open Questions

- What is the smallest panel/view host slice that lets the semantic editor use document and info panels without overbuilding the panel architecture?
- What is the smallest browser-readable Studio support data needed for work/series/moment token insertion?
- Should the semantic-reference v2 request cover graph visualization modules, or should graph modules get their own later request?
- Which `docs-viewer.js` responsibility should be extracted first as evidence of the app-shell direction?
- What minimum workspace-root abstraction is needed before true local/uncommitted data can be implemented safely?
- Which portable fixture should prove public/manage/module behavior once panel modules exist?

## Verification

Each implementation slice should define its own focused checks.
At the coordination level, verify that new work:

- links back to this plan and the owning request
- updates app-shell, inventory, or portable docs when ownership contracts change
- keeps public and manage behavior covered where relevant
- documents whether generated payload rebuilds were performed or intentionally deferred

## Related References

- [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
- [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references)
- [Docs Viewer Workspace Mount Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-workspace-mount-architecture)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
