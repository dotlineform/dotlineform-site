---
doc_id: site-request-portable-docs-viewer
title: Portable Docs Viewer Request
added_date: 2026-05-11
last_updated: "2026-05-11 20:05"
ui_status: in-progress
parent_id: change-requests
sort_order: 27
hidden: false
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
- Keeping compatibility with existing `/docs/`, `/library/`, and `/analysis/` routes may require adapters inside an implementation slice, but those adapters should not survive that slice if they only bridge old and new ownership.
- A minimal portable boundary may still expose hidden dotlineform assumptions until tested in a fixture repo.

## Cleanup Rule

Each implementation slice must retire the transitional surface it replaces before the slice is accepted.
The project should not keep a separate final cleanup phase that leaves old routes, links, or ownership bridges behind after the replacement is already live.

Immediate cleanup already implied by the current decisions:

- retire the global `/search/` page and route instead of preserving a merged-search surface (completed in the Catalogue search route cleanup)
- keep Catalogue search as a Catalogue-owned concern, with any future dedicated Catalogue route handled outside Docs Viewer portability
- retire the standalone `/studio/docs-import/` page and route after Studio links open the Docs Viewer management modal directly (completed in the initial cleanup)
- remove stale Studio links to `/studio/docs-import/` (completed in the initial cleanup)
- update docs that still describe `/search/` as an aggregate or docs-scope search surface

## Ordered Implementation Plan

### 1. Freeze The Current Install Contract And Remove Superseded Entrypoints

Use [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) as the live install page.
Keep it focused on what a user must copy, configure, run, and verify.

Tasks:

- keep the install page free of architecture debate
- link from the install page to this request for extraction status
- treat each later slice as reducing the current copy/setup burden
- remove links from Studio dashboards or nav surfaces that still open `/studio/docs-import/` (done)
- remove the standalone `/studio/docs-import/` page once the modal entry links are in place (done)
- retire the global `/search/` route rather than keeping it as a cross-domain search bridge (done)
- update Search docs that still describe direct `/search/` as aggregate, global, or docs-scope search (done for current contract docs)

Acceptance:

- the install page says what to do now
- this request says what to improve next
- Docs Import is reached from `/docs/?scope=<scope>&mode=manage&import=1`
- no public/global search route claims ownership of Docs search

### 2. Define File Ownership And Portable Layout

Before scope config, CSS, search, or import ownership is changed, define the file layout that makes the Docs Viewer boundary visible in the repo.
The goal of this slice is to separate portable Docs Viewer files from Studio-only files without attempting a broad Studio or Catalogue reorganisation.

Target direction:

```text
assets/
  docs-viewer/
    js/
    css/
    data/
      docs-viewer-config.json
      ui-text.json
  js/
    site/public shared JS only
  studio/
    js/
      studio-only app/runtime code
    data/
      studio-only config, generated Studio payloads, UI text
scripts/
  docs/
    Docs Viewer build, scope config, management server, import
  search/
    Catalogue/public search until docs search moves out
  catalogue/
  studio/
  media/
  checks/
```

Ownership decisions for this slice:

| Area | Current examples | Target owner | Decision |
| --- | --- | --- | --- |
| Docs Viewer shell | `_includes/docs_viewer_shell.html`, `_includes/docs_import_shell.html` | Docs Viewer package plus consuming route adapter | Keep includes as the route integration boundary until the route-adapter slice defines templates. |
| Docs Viewer runtime JS | `assets/docs-viewer/js/docs-viewer*.js` | Docs Viewer | Runtime modules live under `assets/docs-viewer/js/`. |
| Docs Viewer CSS | `assets/docs-viewer/css/docs-viewer-management.css`, `.docsViewer*` rules in `assets/css/main.css` | Docs Viewer | Management CSS lives under `assets/docs-viewer/css/`; public CSS extraction is still a later slice. |
| Docs Viewer browser config | `scripts/docs/docs_scopes.json`, `assets/studio/data/studio_config.json`, hardcoded route maps | Docs Viewer | Keep `scripts/docs/docs_scopes.json` as source config; add a browser-facing config under `assets/docs-viewer/data/`. |
| Docs Viewer UI text | `assets/docs-viewer/data/ui-text.json`, Docs Import copy in `assets/studio/data/ui_text/docs-html-import.json` | Docs Viewer | Viewer copy lives under `assets/docs-viewer/data/`; Docs Import copy remains Studio-owned until the import/config slices. |
| Generated docs payloads | `assets/data/docs/scopes/<scope>/...` | Docs Viewer output, consuming site storage | Keep the current output path for compatibility; treat it as generated output, not package source. |
| Inline docs search | `assets/data/search/<scope>/index.json`, `scripts/search/build_search.rb`, `scripts/search/build_config.json` | Docs Viewer after the search slice | Leave in the search subsystem until Docs search ownership moves in its dedicated slice. |
| Docs management server | `scripts/docs/docs_management_server.py` and adjacent `scripts/docs/docs_*` modules | Docs Viewer | Keep under `scripts/docs/`; this is already the right domain boundary. |
| Studio application code | `assets/studio/js/*`, `assets/studio/data/studio_config.json`, Studio generated payloads | Studio | Do not reorganise broad Studio files in this request; only extract Docs Viewer dependencies. |
| Catalogue and tag tools | `assets/studio/js/catalogue-*`, `assets/studio/js/tag-*`, `scripts/catalogue/`, `scripts/analytics/` | Catalogue, Analytics, Studio | Out of scope except where Docs Viewer currently imports them by mistake. |
| Public site JS | `assets/js/work.js`, `assets/js/moment.js`, `assets/js/site-nav.js`, `assets/js/theme-toggle.js` | Consuming site/shared public site | Leave in `assets/js/`; this directory should become public site/shared JS after Docs Viewer moves out. |

The file-move implementation slice should move or introduce only:

- `assets/docs-viewer/js/` for the Docs Viewer runtime modules
- `assets/docs-viewer/css/` for Docs Viewer-owned CSS
- `assets/docs-viewer/data/` for browser config and Docs Viewer UI text
- include path updates needed by `_includes/docs_viewer_shell.html` and route pages

The next implementation slice should not move:

- `assets/studio/js/catalogue-*`
- `assets/studio/js/tag-*`
- `assets/studio/js/data-*`
- `assets/studio/data/catalogue*`
- `assets/studio/data/tag_*`
- `scripts/catalogue/`, `scripts/analytics/`, `scripts/media/`, or broad `scripts/studio/` services

Tasks:

- document which current files are portable Docs Viewer files, consuming-site route/theme files, Studio-only files, Catalogue files, or shared site files
- define the target locations for Docs Viewer runtime JS, CSS, browser config, UI text, generated docs payloads, and local management scripts
- keep `scripts/docs/docs_scopes.json` as the source-side docs scope registry unless a later slice intentionally replaces it
- define a browser-facing Docs Viewer config location such as `assets/docs-viewer/data/docs-viewer-config.json`
- define a Docs Viewer UI text location such as `assets/docs-viewer/data/ui-text.json`
- identify which files should move in the next implementation slice and which broader Studio/Catalogue files should stay put for now
- update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) only if the current install instructions need a terminology or ownership clarification

Acceptance:

- the next implementation slice has an agreed target layout for Docs Viewer-owned files
- portable files are no longer described as belonging under `assets/studio/`
- Studio may consume Docs Viewer, but Docs Viewer does not consume Studio-owned config or UI text in the target architecture
- broad reorganisation of unrelated Studio, Catalogue, tag, export, or media files is explicitly out of scope for this slice

### 3. Move Docs Viewer Files Into Portable Paths

Status: implemented.

Move the Docs Viewer-owned files into the layout agreed in slice 2 before changing scope behavior, search ownership, or import scope rules.
This slice is mostly mechanical, but it should leave the live routes working from the new locations.

Tasks:

- create `assets/docs-viewer/js/`, `assets/docs-viewer/css/`, and `assets/docs-viewer/data/` (done)
- move existing `assets/js/docs-viewer*.js` modules into `assets/docs-viewer/js/` (done)
- move `assets/css/docs-viewer-management.css` into `assets/docs-viewer/css/` (done)
- add a Docs Viewer-owned public CSS file under `assets/docs-viewer/css/` only if a small extracted stylesheet is needed to keep includes coherent before the full CSS extraction slice (not needed in this slice)
- move or copy Docs Viewer UI text needed by the current runtime into `assets/docs-viewer/data/`, while leaving any Studio-only source in place until callers are switched (done for viewer UI text)
- update `_includes/docs_viewer_shell.html`, route pages, and module imports to load from the new Docs Viewer paths (done through the shared include)
- keep generated docs payloads under `assets/data/docs/scopes/` and docs-search payloads under `assets/data/search/` for compatibility (done)
- do not move broad Studio, Catalogue, tag, export, media, or public-site files in this slice (done)
- update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) so the current copy list points at the new Docs Viewer-owned paths (done)

Acceptance:

- `/docs/`, `/library/`, and `/analysis/` load Docs Viewer runtime modules from `assets/docs-viewer/js/`
- management mode loads Docs Viewer management CSS from `assets/docs-viewer/css/`
- no `assets/js/docs-viewer*.js` source modules remain as the active runtime path
- the old file locations are not kept as compatibility duplicates unless a specific route still requires them and the reason is documented
- no unrelated Studio or Catalogue reorganisation is included

### 4. Make Scope Config The Single Source Of Truth

Status: implemented.

Current scope data is split between `scripts/docs/docs_scopes.json`, `_includes/docs_viewer_shell.html`, `assets/docs-viewer/js/docs-viewer.js`, search config, and import-service allowlists.

Tasks:

- create a Docs Viewer-owned browser config (done)
- generate or load the management scope list from scope config (done)
- remove hardcoded scope options from `_includes/docs_viewer_shell.html` (done)
- remove hardcoded `DOCS_ROUTE_SCOPES` entries from `assets/docs-viewer/js/docs-viewer.js` (done)
- make generated data URLs, search URLs, default doc ids, route bases, and `include_scope_param` scope-config driven (done)
- remove remaining hardcoded scope lists that the generated config replaces in the same slice (done for viewer runtime, Docs Import scope options, management URLs, docs-source validation, docs rebuild loops, live rebuild watching, and broken-link route parsing)

Acceptance:

- adding a new docs scope does not require editing the viewer shell or runtime route map
- `/docs/?scope=<scope>` can manage any configured scope supported by the local server
- no compatibility scope list remains as a second source of truth

### 5. Extract Docs Viewer CSS And UI Text

Current read-only Docs Viewer styling lives partly in `assets/css/main.css`.
Management mode also loads `assets/studio/css/studio.css` for importer and modal/control styling.

Target CSS cascade:

- the consuming Jekyll layout continues to load the host stylesheet, currently `assets/css/main.css`
- the Docs Viewer include always loads `assets/docs-viewer/css/docs-viewer.css`
- management mode also loads `assets/docs-viewer/css/docs-viewer-management.css`
- management mode no longer loads `assets/studio/css/studio.css`

The host stylesheet remains responsible for site tokens, base typography, prose/document rules, responsive media defaults, and the `.content` contract used by generated docs HTML.
Docs Viewer styles should define the viewer shell, index, controls, search, results, bookmarks, status pills, and management surfaces while consuming host tokens through CSS custom properties with portable fallbacks.

Tasks:

- create `assets/docs-viewer/css/docs-viewer.css` for public Docs Viewer shell/component styles
- move read-only `.docsViewer*` CSS out of `assets/css/main.css` into `assets/docs-viewer/css/docs-viewer.css`
- keep management-only styles in `assets/docs-viewer/css/docs-viewer-management.css`
- copy the narrow `tagStudio*` form/control styles used by Docs Import into Docs Viewer management CSS as a transitional dependency
- remove `assets/studio/css/studio.css` from `_includes/docs_viewer_shell.html`
- keep generic host styles such as font tokens, `.content`, document typography, and responsive image defaults in `assets/css/main.css`
- allow intentional visual drift from Studio UI primitives where it improves Docs Viewer identity
- move Docs Viewer UI text/config out of `assets/studio/data/`
- remove public-route CSS/JS includes made redundant by the extracted Docs Viewer CSS/config

Acceptance:

- public read-only viewer routes load host CSS plus Docs Viewer CSS, without Studio CSS
- `/docs/` management mode loads only Docs Viewer-owned management CSS for viewer/import controls
- generated docs content continues to inherit host `.content` prose/media styles
- transitional `tagStudio*` selectors may remain only inside Docs Viewer management CSS until a later rename/refactor
- public routes no longer need `studio_config.json` for normal viewer copy/settings

### 6. Move Docs Search Under Docs Viewer Ownership

Current docs search artifacts are generated by the generic search pipeline.
That makes portable Docs Viewer installs depend on a search product that is actually Catalogue-oriented.

Direction:

- Catalogue search and Docs search are separate data-domain products
- Docs Viewer owns document-domain search for `/docs/`, `/library/`, and `/analysis/`
- the top-level `/search/` route should not remain as a global or merged-result search product

Tasks:

- move docs-search scope config out of `scripts/search/build_config.json`
- move docs-search build logic into a Docs Viewer-owned builder or builder mode
- keep generated docs-search output compatible during transition
- make docs-search policy explicit inside Docs Viewer runtime/config
- share only genuinely domain-neutral text helpers with Catalogue search
- remove docs-scope entries from the generic/public search policy in the same slice
- remove docs-search generation from the generic search config once the Docs Viewer builder owns it
- update Search docs so Catalogue and Docs search ownership is reflected consistently

Acceptance:

- a portable Docs Viewer install can build inline docs search without copying Catalogue/public search files
- Catalogue search continues to build and run independently
- `/analysis/` uses Docs search because it is document-domain content
- the public/global search runtime no longer has docs-scope responsibilities

### 7. Package The Route Adapter Pattern

Current route pages are simple but hand-written.
They should become the documented adapter layer for downstream Jekyll projects.

Tasks:

- define read-only route template inputs
- define local management route template inputs
- document canonical URL behavior for `scope`, `doc`, `q`, and `mode`
- make public routes normalize away manage mode
- keep `/docs/` as the only management-capable shell
- remove any public-route management hooks or query affordances superseded by the route templates

Acceptance:

- adding a read-only route is a small route file plus scope config
- adding local management support does not require public routes to expose management payload

### 8. Make Docs Import Scope-Config Driven

Docs Import now lives inside the Docs Viewer management modal, and its scope picker reads the generated Docs Viewer browser config.
The remaining import work is ownership and packaging: the import runtime still lives under Studio paths, and the import/media behavior has not been tested as a standalone Docs Viewer package.

Tasks:

- make the import modal read configured docs scopes (done for the picker)
- remove `studio`, `library`, and `analysis` hardcoding from import scope normalization (done for the picker and management result URLs)
- ensure imported media token paths and target source roots come from scope config
- keep filename-collision modal behavior intact
- delete the old `/studio/docs-import/` wrapper as part of the same slice if it still exists
- remove route defaults, activity-contract references, tests, and docs that assume `/studio/docs-import/` is the user-facing import surface

Acceptance:

- Docs Import works for any configured writable docs scope
- the Docs Viewer management modal is the only user-facing Docs Import surface

### 9. Consolidate Local Management Server Packaging

The local server is already docs-specific but still feels like a collection of repo scripts.

Tasks:

- define the minimal server file set
- keep loopback binding and write allowlists explicit
- make generated-data reads, source writes, backups, rebuilds, and import endpoints use the same scope config
- define a project-local way to start the server outside `bin/dev-studio`
- document required Python/Ruby/Jekyll assumptions for downstream projects
- remove server configuration branches that only support retired import/search routes

Acceptance:

- a downstream Jekyll repo can start local Docs Viewer management with one documented command
- public/static builds do not need or expose the server

### 10. Build A Minimal Fixture Install

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
