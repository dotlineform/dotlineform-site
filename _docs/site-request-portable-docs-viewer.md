---
doc_id: site-request-portable-docs-viewer
title: Portable Docs Viewer Request
added_date: "2026-05-11"
last_updated: "2026-05-11"
parent_id: change-requests
sort_order: 27
---
# Portable Docs Viewer Request

Status:

- proposed

## Summary

Turn the current Docs Viewer into a portable, Jekyll-friendly module that can be copied into another project with a predictable install path.

The first target is pragmatic rather than package-manager perfect:

- one read-only public Docs Viewer route per document corpus
- one local management route at `/docs/` that can switch scopes
- Docs Viewer-owned document search
- Docs Viewer-owned import modal and local management server
- a clear split between reusable Docs Viewer files and project-local route/theme/content files

This request is narrower and more implementation-oriented than [Docs Toolkit Extraction Request](/docs/?scope=studio&doc=site-request-docs-toolkit-extraction).
It uses the current dotlineform implementation as the first consumer and focuses on making the Docs Viewer self-contained enough to copy into another Jekyll repo.

## Product Boundary

Docs Viewer owns:

- document source scope configuration
- generated docs index and payload format
- public read-only viewer shell
- local management shell and write server contract
- document-domain search engine, search policy, and search build output
- Docs Import as a management modal
- viewer CSS and management CSS
- viewer UI text and browser config

Docs Viewer does not own:

- Catalogue search
- Catalogue record/editor workflows
- global or merged-result site search
- consuming-site page layout beyond the viewer include contract
- consuming-site content, routes, and theme decisions

`/analysis/` is a Docs Viewer corpus architecturally.
Its subject matter may concern Catalogue, but its source model is documents, so it belongs to document search.

## Benefits And Risks

Benefits:

- A new docs corpus should be added by editing one scope config and adding route/source files, not by patching several hardcoded runtime lists.
- Docs Viewer portability will not drag the Catalogue/public search product into downstream repos.
- Viewer CSS can develop its own identity instead of staying tied to Studio UI primitives.
- The install guide can become more accurate after each extraction slice lands.

Risks:

- Allowing Docs Viewer CSS to drift from Studio primitives creates two UI systems to maintain.
- Moving docs search under Docs Viewer may temporarily duplicate low-level search helper behavior.
- Keeping compatibility with existing `/docs/`, `/library/`, and `/analysis/` routes may require short-lived adapters.
- A minimal portable boundary may still expose hidden dotlineform assumptions until tested in a fixture repo.

## Ordered Implementation Plan

### 1. Freeze The Current Install Contract

Use [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) as the live install page.
Keep it focused on what a user must copy, configure, run, and verify.

Tasks:

- keep the install page free of architecture debate
- link from the install page to this request for extraction status
- treat each later slice as reducing the current copy/setup burden

Acceptance:

- the install page says what to do now
- this request says what to improve next

### 2. Make Scope Config The Single Source Of Truth

Current scope data is split between `scripts/docs/docs_scopes.json`, `_includes/docs_viewer_shell.html`, `assets/js/docs-viewer.js`, search config, and import-service allowlists.

Tasks:

- extend `scripts/docs/docs_scopes.json` or create a Docs Viewer-owned browser config derived from it
- generate or load the management scope list from scope config
- remove hardcoded scope options from `_includes/docs_viewer_shell.html`
- remove hardcoded `DOCS_ROUTE_SCOPES` entries from `assets/js/docs-viewer.js`
- make generated data URLs, search URLs, default doc ids, route bases, and `include_scope_param` scope-config driven

Acceptance:

- adding a new docs scope does not require editing the viewer shell or runtime route map
- `/docs/?scope=<scope>` can manage any configured scope supported by the local server

### 3. Extract Docs Viewer CSS And UI Text

Current read-only Docs Viewer styling lives partly in `assets/css/main.css`.
Management mode also loads `assets/studio/css/studio.css` for importer and modal/control styling.

Tasks:

- move read-only `.docsViewer*` CSS into a Docs Viewer-owned stylesheet
- keep management-only styles in Docs Viewer-owned management CSS
- decide which modal/control styles are copied into Docs Viewer management CSS
- allow intentional visual drift from Studio UI primitives where it improves Docs Viewer identity
- move Docs Viewer UI text/config out of `assets/studio/data/`

Acceptance:

- public read-only viewer routes load Docs Viewer CSS without Studio CSS
- `/docs/` management mode loads only Docs Viewer-owned management CSS for viewer/import controls
- public routes no longer need `studio_config.json` for normal viewer copy/settings

### 4. Move Docs Search Under Docs Viewer Ownership

Current docs search artifacts are generated by the generic search pipeline.
That makes portable Docs Viewer installs depend on a search product that is actually Catalogue-oriented.

Direction:

- Catalogue search and Docs search are separate data-domain products
- Docs Viewer owns document-domain search for `/docs/`, `/library/`, and `/analysis/`
- any top-level `/search/` route should be a chooser or dispatcher, not the owner of merged policy

Tasks:

- move docs-search scope config out of `scripts/search/build_config.json`
- move docs-search build logic into a Docs Viewer-owned builder or builder mode
- keep generated docs-search output compatible during transition
- make docs-search policy explicit inside Docs Viewer runtime/config
- share only genuinely domain-neutral text helpers with Catalogue search

Acceptance:

- a portable Docs Viewer install can build inline docs search without copying Catalogue/public search files
- Catalogue search continues to build and run independently
- `/analysis/` uses Docs search because it is document-domain content

### 5. Package The Route Adapter Pattern

Current route pages are simple but hand-written.
They should become the documented adapter layer for downstream Jekyll projects.

Tasks:

- define read-only route template inputs
- define local management route template inputs
- document canonical URL behavior for `scope`, `doc`, `q`, and `mode`
- make public routes normalize away manage mode
- keep `/docs/` as the only management-capable shell

Acceptance:

- adding a read-only route is a small route file plus scope config
- adding local management support does not require public routes to expose management payload

### 6. Make Docs Import Scope-Config Driven

Docs Import now lives inside the Docs Viewer management modal, but import scope support is still hardcoded to the current known scopes.

Tasks:

- make the import modal read configured docs scopes
- remove `studio`, `library`, and `analysis` hardcoding from import scope normalization
- ensure imported media token paths and target source roots come from scope config
- keep filename-collision modal behavior intact
- keep the old `/studio/docs-import/` wrapper only until links are moved

Acceptance:

- Docs Import works for any configured writable docs scope
- the compatibility route can be retired safely

### 7. Consolidate Local Management Server Packaging

The local server is already docs-specific but still feels like a collection of repo scripts.

Tasks:

- define the minimal server file set
- keep loopback binding and write allowlists explicit
- make generated-data reads, source writes, backups, rebuilds, and import endpoints use the same scope config
- define a project-local way to start the server outside `bin/dev-studio`
- document required Python/Ruby/Jekyll assumptions for downstream projects

Acceptance:

- a downstream Jekyll repo can start local Docs Viewer management with one documented command
- public/static builds do not need or expose the server

### 8. Build A Minimal Fixture Install

The copy boundary should be tested outside dotlineform before it is treated as stable.

Tasks:

- create or designate a minimal Jekyll fixture repo/project
- install the Docs Viewer file set into it
- add one read-only docs corpus
- add `/docs/` management for that corpus
- verify search, import initialization, create/edit/move, and generated-data reads

Acceptance:

- the fixture proves the install guide works without dotlineform-only routes or data
- any remaining hidden assumptions are added back to this request as follow-up tasks

### 9. Retire Transitional Couplings

After the portable boundary works, remove compatibility code that only exists because the viewer was still embedded in Studio/search infrastructure.

Tasks:

- retire `/studio/docs-import/` after callers move to the Docs Viewer modal
- remove docs-search generation from generic search config
- remove public Docs Viewer dependencies on Studio config/data paths
- update Search docs so Catalogue and Docs search ownership is reflected consistently
- update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) to the reduced file set

Acceptance:

- the install page is shorter because the module owns its runtime, CSS, config, search, import, and management files
- remaining project-local steps are route placement, source content, theme choices, and local command wiring

## Verification Strategy

For each implementation slice:

- run targeted syntax checks for changed JavaScript/Python/Ruby files
- rebuild only affected docs scopes and docs-search outputs
- run a Jekyll build to a separate destination
- smoke `/docs/?scope=studio`, `/docs/?scope=library`, `/library/`, and `/analysis/` when viewer behavior changes
- smoke public routes for absence of management CSS/JS when payload boundaries change
- update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) when the install steps change

## Related Docs

- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Toolkit Extraction Request](/docs/?scope=studio&doc=site-request-docs-toolkit-extraction)
