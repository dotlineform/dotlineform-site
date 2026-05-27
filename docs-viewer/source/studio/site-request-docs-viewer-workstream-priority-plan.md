---
doc_id: site-request-docs-viewer-workstream-priority-plan
title: Docs Viewer Workstream Priority Plan
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: draft
parent_id: change-requests
sort_order: 12170
viewable: true
---
# Docs Viewer Workstream Priority Plan

Status:

- proposed

## Summary

Coordinate the active Docs Viewer architecture and product workstreams so implementation can proceed in useful slices without losing the larger direction.

Current active or near-active workstreams:

- panel architecture with hosted module support
- `docs-viewer.js` risk reduction and focused ownership extraction
- JavaScript frontend / explicit backend app-shell direction
- manage-mode Markdown source editor for semantic-reference insertion
- semantic-reference expansion and infrastructure
- portable Docs Viewer packaging and installation
- local/uncommitted Docs Viewer data storage outside the public repo publishing path

These workstreams overlap, but they should not be merged into one large rewrite.
The aim is to define dependencies, sequencing, and decision points so each slice can land independently while moving toward the same product architecture.

## Guiding Principles

- Keep browser UI composition, panel/view state, client-side reads, and view modules in JavaScript where practical.
- Keep source writes, rebuilds, filesystem access, backups, validation, and local operational capabilities behind explicit backend endpoints.
- Keep public presentation and local manage mode as two contexts of the same Docs Viewer app.
- Use manage mode to incubate operational, experimental, dependency-heavy, or still-uncertain modules before promoting them to public presentation.
- Avoid a broad `docs-viewer.js` refactor as a prerequisite; extract focused ownership as implementation slices require it.
- Keep generated docs/search/reference payloads as the main public-safe read contract.
- Keep true local/uncommitted data work aligned with a workspace/data-root abstraction, not ad hoc path exceptions.

## Workstream Map

| Workstream | Current artifact | Role | Dependency posture |
| --- | --- | --- | --- |
| App shell frontend/backend boundary | [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell) | Defines the browser app, generated data/config, and backend boundary. | Architectural parent for panel, source editor, third-party modules, and portability. |
| Portable Docs Viewer | [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) | Reduces host integration work and documents portable install shape. | Outcome track; should consume proven app-shell and config/data contracts. |
| Workspace/local data roots | [Docs Viewer Workspace Mount Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-workspace-mount-architecture) | Defines repo-backed and external/local data workspaces. | Foundation for true local/uncommitted data. Can proceed in parallel with UI work but affects backend/build paths. |
| Panel architecture and hosted modules | [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell) | Adds index/document/info panel model and module host lifecycle. | Should build on app-shell principles but can start before full JS shell migration. |
| Focused Markdown source editor | [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor) | Adds manage-only source editing and semantic token insertion. | Depends on management source read/write/rebuild endpoints and semantic target data. Does not require full panel architecture. |
| Semantic references v1 | [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references) | Existing token grammar, builder parsing, and generated reference artifacts. | Implemented v1; expansion needs a new request before broader registry/editor work. |
| `docs-viewer.js` risk reduction | [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) | Tracks shared runtime risk and extraction opportunities. | Should happen through focused owner modules required by product slices, not as a standalone rewrite first. |

## Missing Request

Create a separate change request for semantic-reference expansion and infrastructure before implementation beyond v1.

That request should cover:

- supported target registries beyond current v1
- generated/browser-safe semantic target lookup data
- client-side semantic target registry reads and option normalization
- validation and warning policy for unresolved or non-public targets
- relationship between semantic references, broken-link audits, reports, and future graph/panel modules
- public versus manage-only promotion criteria for richer reference views
- downstream portability expectations for custom registries

Until that request exists, keep semantic-reference expansion decisions inside existing v1 behavior or the focused editor request.

## Dependency Order

This is the recommended order for implementation decisions, not a requirement that every item fully complete before the next starts.

### 1. Stabilize The App/Backend Boundary

Use the JavaScript app-shell request as the north star.

Immediate decisions:

- browser modules own UI state, view registration, generated-data reads, and panel/module lifecycle
- backend owns source writes, rebuilds, filesystem access, and protected capabilities
- public and manage mode stay one app with access-gated views/actions

This should guide every slice below.
It does not require a full shell rewrite before product work starts.

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

This keeps token controls out of an overloaded document toolbar and gives the panel architecture an immediate proving workflow.

### 5. Define Semantic-Reference Expansion Infrastructure

Before adding many target kinds or rich reference modules, create the missing semantic-reference expansion request.

Then decide:

- what target registries are supported first
- what generated lookup artifacts the browser can read
- what remains manage-only until stable
- how reference data powers reports, info panels, graph modules, and audits

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
- generated semantic-reference data contracts
- workspace/read/write configuration
- optional module asset declarations

Portable docs should not become the place where uncertain local-only experiments are documented as public install requirements.

## Practical Priority

Recommended near-term priority:

1. Keep app-shell boundary guidance updated as architecture decisions are made.
2. Implement a minimal panel/view host slice with document and info panel hosts.
3. Implement the focused Markdown source editor as the first hosted manage-mode workflow.
4. Create the semantic-reference expansion/infrastructure request.
5. Extract only the `docs-viewer.js` responsibilities needed by the panel, editor, and target lookup modules.
6. Broaden the hosted-module architecture after the first workflow proves the shape.
7. Continue workspace-mount design for local/uncommitted data roots.
8. Update portable setup after contracts are proven.

This order gives the project the panel foundation first, then immediately validates it with a useful authoring workflow while avoiding premature public UI, visualization-library, or standalone packaging commitments.

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

### Source Editing

Default rule:

- source editing is manage-only
- source writes happen once through explicit `Rebuild doc`
- backend validates front matter and source contract, not all Markdown body content
- builder diagnostics report semantic-reference warnings

### Local Data

Default rule:

- public/generated site data can remain in static repo output paths
- manage-only/generated local data should move toward service-backed reads
- true local/uncommitted data should resolve through workspace roots

## Risks

- implementing product slices directly inside `docs-viewer.js` could increase the highest-risk runtime file
- panel, editor, and semantic-reference work could invent incompatible target lookup or module registration patterns
- local/uncommitted data work could become scattered path exceptions instead of a workspace abstraction
- portable Docs Viewer docs could expose experimental manage-only modules as public requirements
- semantic-reference expansion could outgrow the v1 request without a clear registry/data contract

Mitigations:

- require each slice to name its focused owner modules
- keep `docs-viewer.js` as orchestration where possible
- create the semantic-reference expansion request before expanding registries or graph/reference modules
- use manage mode as the incubation context for uncertain features
- update portable docs only after implementation contracts are stable
- keep workspace-root decisions centralized in the workspace mount request

## Open Questions

- What is the smallest panel/view host slice that lets the semantic editor use document and info panels without overbuilding the panel architecture?
- What is the smallest browser-readable target registry needed for work/series/moment token insertion?
- Should the semantic-reference expansion request cover graph visualization modules, or should graph modules get their own later request?
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
