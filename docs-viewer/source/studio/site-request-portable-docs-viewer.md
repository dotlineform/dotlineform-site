---
doc_id: site-request-portable-docs-viewer
title: Portable Docs Viewer Request
added_date: 2026-05-11
last_updated: 2026-05-27
ui_status: paused
parent_id: change-requests
sort_order: 1000
viewable: true
---
# Portable Docs Viewer Request

Status:

- In progress

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

[Docs Viewer Shell Extraction Request](/docs/?scope=studio&doc=site-request-docs-viewer-shell-extraction) completed the first shell/service extraction after Studio localization and source-tree reorganization work.

Current clarification:

- Docs Viewer runtime, server/services, source config, UI text, CSS, assets, build scripts, and Docs Viewer source Markdown now live under the tracked top-level `docs-viewer/` boundary
- Local Studio is now a peer integration that links to the configured Docs Viewer service; it does not host the Docs Viewer shell or proxy Docs Viewer APIs
- canonical publishing Markdown such as `_docs_catalogue/` is Studio-owned site source, not Docs Viewer-owned source
- generated docs/search JSON consumed by public installs remains in the public Jekyll site output paths
- public read-only scope routes such as `/library/` and `/analysis/` remain host/Jekyll-owned route adapters that consume Docs Viewer runtime/config/generated-data contracts
- the remaining portable work should reduce host integration work and packaging friction from the current `docs-viewer/` boundary, not move files out of Studio
- Docs Viewer is technically portable now, but it still requires too much manual setup and does not yet have a repeatable fixture proving the portable install contract outside dotlineform
- the JavaScript app-shell boundary will improve the portability story, but it is not strictly required for Docs Viewer to be portable

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
| Docs Viewer shell | `_includes/docs_viewer_shell.html` | Docs Viewer package plus consuming route adapter | Keep the viewer shell include as the route integration boundary until the route-adapter slice defines templates. Docs Import modal markup lives inside that shell rather than a migrated standalone-page include. |
| Docs Viewer runtime JS | `docs-viewer/runtime/js/docs-viewer*.js` | Docs Viewer | Runtime modules live under `docs-viewer/runtime/js/`. |
| Docs Viewer CSS | `docs-viewer/static/css/docs-viewer-management.css`, `.docsViewer*` rules in `assets/css/main.css` | Docs Viewer | Management CSS lives under `docs-viewer/static/css/`; public CSS extraction is still a later slice. |
| Docs Viewer browser config | `docs-viewer/config/scopes/docs_scopes.json`, `docs-viewer/config/defaults/docs-viewer-config.json`, `docs-viewer/config/defaults/docs-viewer-public-config.json` | Docs Viewer | Keep `docs-viewer/config/scopes/docs_scopes.json` as source config; generate browser-facing defaults through the Docs Viewer builder. |
| Docs Viewer UI text | `docs-viewer/config/ui-text/ui-text.json` | Docs Viewer | Viewer and Docs Import copy lives under Docs Viewer config. |
| Generated docs payloads | `assets/data/docs/scopes/<scope>/...` | Docs Viewer output, consuming site storage | Keep the current output path for compatibility; treat it as generated output, not package source. |
| Inline docs search | `assets/data/search/<scope>/index.json`, `scripts/search/build_search.rb`, `scripts/search/build_config.json` | Docs Viewer after the search slice | Leave in the search subsystem until Docs search ownership moves in its dedicated slice. |
| Docs Viewer local service | `docs-viewer/services/docs_viewer_service.py`, `docs-viewer/services/docs_management_service.py`, and adjacent Docs Viewer service modules | Docs Viewer | Keep the standalone service and management dispatcher under `docs-viewer/services/`; the old `docs_management_server.py` entrypoint is removed. |
| Studio application code | `assets/studio/js/*`, `assets/studio/data/studio_config.json`, Studio generated payloads | Studio | Do not reorganise broad Studio files in this request; only extract Docs Viewer dependencies. |
| Catalogue and tag tools | `assets/studio/js/catalogue-*`, `assets/studio/js/tag-*`, `scripts/catalogue/`, `scripts/analytics/` | Catalogue, Analytics, Studio | Out of scope except where Docs Viewer currently imports them by mistake. |
| Public site JS | `assets/js/work.js`, `assets/js/moment.js`, `assets/js/site-nav.js`, `assets/js/theme-toggle.js` | Consuming site/shared public site | Leave in `assets/js/`; this directory should become public site/shared JS after Docs Viewer moves out. |

The file-move implementation slice should move or introduce only:

- `docs-viewer/runtime/js/` for the Docs Viewer runtime modules
- `docs-viewer/static/css/` for Docs Viewer-owned CSS
- `docs-viewer/config/defaults/` and `docs-viewer/config/ui-text/` for browser config defaults and Docs Viewer UI text
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
- keep `docs-viewer/config/scopes/docs_scopes.json` as the source-side docs scope registry unless a later slice intentionally replaces it
- define a browser-facing Docs Viewer config location such as `docs-viewer/config/defaults/docs-viewer-config.json`
- define a Docs Viewer UI text location such as `docs-viewer/config/ui-text/ui-text.json`
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

- create `docs-viewer/runtime/js/`, `docs-viewer/static/css/`, `docs-viewer/config/defaults/`, and `docs-viewer/config/ui-text/` (done)
- move existing `assets/js/docs-viewer*.js` modules into `docs-viewer/runtime/js/` (done)
- move `assets/css/docs-viewer-management.css` into `docs-viewer/static/css/` (done)
- add a Docs Viewer-owned public CSS file under `docs-viewer/static/css/` only if a small extracted stylesheet is needed to keep includes coherent before the full CSS extraction slice (not needed in this slice)
- move Docs Viewer UI text needed by the current runtime into `docs-viewer/config/ui-text/` (done)
- update `_includes/docs_viewer_shell.html`, route pages, and module imports to load from the new Docs Viewer paths (done through the shared include)
- keep generated docs payloads under `assets/data/docs/scopes/` and docs-search payloads under `assets/data/search/` for compatibility (done)
- do not move broad Studio, Catalogue, tag, export, media, or public-site files in this slice (done)
- update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) so the current copy list points at the new Docs Viewer-owned paths (done)

Acceptance:

- `/docs/`, `/library/`, and `/analysis/` load Docs Viewer runtime modules from `docs-viewer/runtime/js/`
- management mode loads Docs Viewer management CSS from `docs-viewer/static/css/`
- no `assets/js/docs-viewer*.js` source modules remain as the active runtime path
- the old file locations are not kept as compatibility duplicates unless a specific route still requires them and the reason is documented
- no unrelated Studio or Catalogue reorganisation is included

### 4. Make Scope Config The Single Source Of Truth

Status: implemented.

Current scope data is split between `docs-viewer/config/scopes/docs_scopes.json`, `_includes/docs_viewer_shell.html`, `docs-viewer/runtime/js/docs-viewer.js`, search config, and import-service allowlists.

Tasks:

- create a Docs Viewer-owned browser config (done)
- generate or load the management scope list from scope config (done)
- remove hardcoded scope options from `_includes/docs_viewer_shell.html` (done)
- remove hardcoded `DOCS_ROUTE_SCOPES` entries from `docs-viewer/runtime/js/docs-viewer.js` (done)
- make generated data URLs, search URLs, default doc ids, route bases, and `include_scope_param` scope-config driven (done)
- remove remaining hardcoded scope lists that the generated config replaces in the same slice (done for viewer runtime, Docs Import scope options, management URLs, docs-source validation, docs rebuild loops, live rebuild watching, and broken-link route parsing)

Acceptance:

- adding a new docs scope does not require editing the viewer shell or runtime route map
- `/docs/?scope=<scope>` can manage any configured scope supported by the local server
- no compatibility scope list remains as a second source of truth

### 5. Extract Docs Viewer CSS And UI Text

Status: implemented.

Current read-only Docs Viewer styling lives partly in `assets/css/main.css`.
Management mode also loads `assets/studio/css/studio.css` for importer and modal/control styling.

Target CSS cascade:

- the consuming Jekyll layout continues to load the host stylesheet, currently `assets/css/main.css`
- the Docs Viewer include always loads `docs-viewer/static/css/docs-viewer.css`
- management mode also loads `docs-viewer/static/css/docs-viewer-management.css`
- management mode no longer loads `assets/studio/css/studio.css`

The host stylesheet remains responsible for site tokens, base typography, prose/document rules, responsive media defaults, and the `.content` contract used by generated docs HTML.
Docs Viewer styles should define the viewer shell, index, controls, search, results, bookmarks, status pills, and management surfaces while consuming host tokens through CSS custom properties with portable fallbacks.

Tasks:

- create `docs-viewer/static/css/docs-viewer.css` for public Docs Viewer shell/component styles (done)
- move read-only `.docsViewer*` CSS out of `assets/css/main.css` into `docs-viewer/static/css/docs-viewer.css` (done)
- keep management-only styles in `docs-viewer/static/css/docs-viewer-management.css` (done)
- copy the narrow `tagStudio*` form/control styles used by Docs Import into Docs Viewer management CSS as a transitional dependency (done)
- remove `assets/studio/css/studio.css` from `_includes/docs_viewer_shell.html` (done)
- keep generic host styles such as font tokens, `.content`, document typography, and responsive image defaults in `assets/css/main.css` (done)
- allow intentional visual drift from Studio UI primitives where it improves Docs Viewer identity (done through Docs Viewer-owned CSS variables and fallbacks)
- move Docs Viewer UI text/config out of `assets/studio/data/` (done for viewer UI text and viewer settings; Docs Import copy remains Studio-owned until the import slice)
- remove public-route CSS/JS includes made redundant by the extracted Docs Viewer CSS/config (done for Studio CSS and Studio config)

Acceptance:

- public read-only viewer routes load host CSS plus Docs Viewer CSS, without Studio CSS
- `/docs/` management mode loads only Docs Viewer-owned management CSS for viewer/import controls
- generated docs content continues to inherit host `.content` prose/media styles
- transitional `tagStudio*` selectors may remain only inside Docs Viewer management CSS until a later rename/refactor
- public routes no longer need `studio_config.json` for normal viewer copy/settings

### 6. Move Docs Search Under Docs Viewer Ownership

Status: implemented.

Before this slice, docs search artifacts were generated by the generic search pipeline.
That made portable Docs Viewer installs depend on a search product that is actually Catalogue-oriented.

Direction:

- Catalogue search and Docs search are separate data-domain products
- Docs Viewer owns document-domain search for `/docs/`, `/library/`, and `/analysis/`
- the stable public command shape can remain `./docs-viewer/build/build_search.rb --scope <scope> --write`
- the shared command should dispatch to domain adapters, not force Catalogue and Docs into one universal builder
- Catalogue search remains Catalogue-owned behind its adapter
- Docs search becomes Docs Viewer-owned behind its adapter
- the top-level `/search/` route should not remain as a global or merged-result search product

Owner-command direction:

- call the Catalogue search builder at `studio/services/catalogue/search/build_search.rb`
- call the Docs Viewer search builder at `docs-viewer/build/build_search.rb`
- share only domain-neutral helper code such as text normalization, deterministic JSON writing, and basic validation
- do not generalize Catalogue joins, tag enrichment, docs `viewable` filtering, or docs route policy into a single abstract schema engine in this slice

Tasks:

- move docs-search scope config out of `scripts/search/build_config.json` (done)
- move docs-search build logic into a Docs Viewer-owned builder/adapter (done)
- keep the top-level search command as a thin adapter dispatcher (done)
- make docs scopes derive from `docs-viewer/config/scopes/docs_scopes.json` instead of hardcoded `studio`, `library`, and `analysis` lists (done)
- keep generated docs-search output compatible during transition (done)
- make docs-search policy explicit inside Docs Viewer runtime/config (done)
- keep Catalogue search behavior stable while routing it through the Catalogue adapter (done)
- remove docs-scope entries from the generic/public search policy in the same slice (done)
- remove docs-search generation from the generic search config once the Docs Viewer builder owns it (done)
- update Search docs so Catalogue and Docs search ownership is reflected consistently (done)

Acceptance:

- `./docs-viewer/build/build_search.rb --scope <scope> --write` still works for Catalogue and docs scopes
- the command dispatches through domain adapters rather than one mixed Catalogue/docs implementation
- a portable Docs Viewer install can build inline docs search without copying Catalogue/public search files
- Catalogue search continues to build and run independently
- `/analysis/` uses Docs search because it is document-domain content
- the public/global search runtime no longer has docs-scope responsibilities

### 7. Package The Route Adapter Pattern

Status: implemented.

Current route pages are simple but hand-written.
They should become the documented adapter layer for downstream Jekyll projects.

Tasks:

- define read-only route template inputs (done)
- define local management route template inputs (done)
- document canonical URL behavior for `scope`, `doc`, `q`, and `mode` (done)
- make public routes normalize away manage mode (done)
- keep `/docs/` as the only management-capable shell (done)
- remove any public-route management hooks or query affordances superseded by the route templates (done)

Acceptance:

- adding a read-only route is a small route file plus scope config
- adding local management support does not require public routes to expose management payload

### 8. Make Docs Import Scope-Config Driven

Status: implemented.

Docs Import now lives inside the Docs Viewer management modal, and its scope picker reads the generated Docs Viewer browser config.
The import runtime and UI text now live under Docs Viewer paths, and imported media token paths derive from scope config.

Tasks:

- make the import modal read configured docs scopes (done)
- remove `studio`, `library`, and `analysis` hardcoding from import scope normalization (done)
- ensure imported media token paths and target source roots come from scope config (done)
- keep filename-collision modal behavior intact (done)
- delete the old `/studio/docs-import/` wrapper as part of the same slice if it still exists (already removed)
- remove route defaults, activity-contract references, tests, and docs that assume `/studio/docs-import/` is the user-facing import surface (done for current contract docs and runtime references)

Acceptance:

- Docs Import works for any configured writable docs scope
- the Docs Viewer management modal is the only user-facing Docs Import surface

### 9. Consolidate Local Management Server Packaging

Status: implemented.

The local server is already docs-specific but still feels like a collection of repo scripts.

Tasks:

- define the minimal server file set (done)
- keep loopback binding and write allowlists explicit (done)
- make generated-data reads, source writes, backups, rebuilds, and import endpoints use the same scope config (done)
- define a project-local way to start the server outside the old integrated local runner (done)
- document required Python/Ruby/Jekyll assumptions for downstream projects (done)
- remove server configuration branches that only support retired import/search routes (done for active packaging docs; no runtime-only retired branch was left in this slice)

Acceptance:

- a downstream Jekyll repo can start local Docs Viewer management with one documented command
- public/static builds do not need or expose the server

### 10. Local vs R2 Config And Config Document

Status: implemented.

This slice prepares Docs Viewer configuration for new installs.
The current dotlineform environment is moving toward R2-backed media for larger media workflows, but a downstream Docs Viewer install cannot be assumed to have R2, credentials, or any remote object store.
New installs need clear guidance for local repo-owned media saves first.

The current environment already uses `assets/docs/<topic>/...` for repo-local docs assets such as small screenshots and reference images; see [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images).
That convention is topic-oriented rather than scope-oriented, so the portable Docs Viewer config should define a default local media convention for new installs without breaking existing `/assets/docs/...` references.

This environment also uses `var/docs/import-staging/` as a staging area for media and files that are then manually copied to the configured media location.
The importer creates wrapper Markdown and reports the expected media path, but it does not upload media.
Automatic upload to R2 is being developed separately and is currently outside this slice; see [R2 Media Upload Automation Request](/docs/?scope=studio&doc=site-request-r2-media-upload-automation).

Docs Viewer import media config should be able to represent these scenarios:

- `repo_assets`: save imported media into a repo-owned public assets folder and write docs links that resolve locally
- `staging_manual`: save extracted media into `var/docs/import-staging/` and report the configured media path for manual copying
- `r2_upload`: future backend for direct upload to R2 once Docs-domain R2 upload support exists

Only `repo_assets` and `staging_manual` are operational in this slice.
`r2_upload` is represented in config shape and documentation as a future backend, but this slice does not implement Docs-domain R2 upload or handle credentials.
No other external file stores currently need to be supported, but the config should avoid naming R2 as the only possible remote backend forever.

The config ownership should be explicit:

- source/local write behavior belongs in source-side Docs Viewer config, currently `docs-viewer/config/scopes/docs_scopes.json`, or in a small adjacent local/server config if the settings should not be published
- generated browser config, currently `docs-viewer/config/defaults/docs-viewer-config.json`, should only expose browser-safe read/display settings
- R2 credentials and other secrets must stay out of tracked config and generated browser config
- `_config.yml` continues to own site-wide media resolution such as `media_base` for rendered <code>&#91;&#91;media:...&#93;&#93;</code> tokens

Changing media storage mode should not migrate existing files automatically.
If a site changes mode later, assume existing media files and existing docs links are manually migrated or updated unless a separate migration tool is explicitly built.

The slice should also decide the link semantics for local saves.
Current remote media uses <code>&#91;&#91;media:...&#93;&#93;</code> tokens that the docs builder resolves against `_config.yml media_base`.
Repo-local docs assets currently use literal `/assets/docs/...` paths.
Decision:

- `repo_assets` writes literal public paths under `/assets/docs/<scope>/...`
- `staging_manual` keeps writing <code>&#91;&#91;media:...&#93;&#93;</code> tokens and reports the configured media path for manual copying
- future `r2_upload` should also use <code>&#91;&#91;media:...&#93;&#93;</code> tokens, with upload handled by the future backend

Recommended local folder convention for new installs:

- `assets/docs/<scope>/img/<filename>`
- `assets/docs/<scope>/files/<filename>`

Example `repo_assets` output:

```md
![Example](/assets/docs/library/img/example.png)
[Download Example](/assets/docs/library/files/example.pdf)
```

Example `staging_manual` or future `r2_upload` output:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.png&#93;&#93;)</code></pre>

Tasks:

- define the Docs Viewer media storage config shape for `repo_assets`, `staging_manual`, and future `r2_upload` (done)
- define the default local repo folder convention for new installs, using current Docs Viewer scopes (`studio`, `library`, `analysis`) as examples and avoiding Catalogue ownership language (done)
- document that `repo_assets` writes literal `/assets/docs/<scope>/...` links while `staging_manual` and future `r2_upload` use media tokens (done)
- implement only the currently deliverable media-save behavior needed for new installs, expected to be `repo_assets` plus the existing `staging_manual` flow (done)
- keep direct R2 upload implementation out of scope; document `r2_upload` as a reserved/future mode that must fail closed or be unavailable until the backend exists (done)
- describe all Docs Viewer config settings in a new focused Docs Viewer Config document, grouped by config file and purpose (done)
- update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) to point new installs at the config document for setup decisions (done)

Acceptance:

- new installs have clear guidance for configuring local repo-owned media saves without R2
- current `staging_manual` behavior remains supported and documented
- config shape can represent future direct R2 upload without exposing credentials or requiring R2 for new installs
- the implementation does not claim direct R2 upload is complete unless a separate Docs-domain R2 backend is implemented
- the config options are documented in a new Docs Viewer Config document

### 11. Prove Portable Install Fixtures

Status: proposed.

Docs Viewer is technically portable already.
The remaining gap is not whether it can run outside dotlineform in principle, but whether the install contract can be proven repeatably without relying on dotlineform's incidental setup.

Use two fixture proof levels.

#### Portable Public Fixture

This should be the first portability fixture.
It proves the static/read-only Docs Viewer contract for a host project that is not dotlineform.

Task tracker: [Portable Docs Viewer Public Fixture Tasks](/docs/?scope=studio&doc=site-request-portable-docs-viewer-public-fixture-tasks).

Scope:

- minimal Jekyll fixture project or generated test fixture
- one public read-only route
- one generated docs scope with a small parent/child tree
- generated docs payloads
- generated search payload if inline search remains part of the public portable contract
- generated route config record
- no Studio semantic references
- no dotlineform-specific modules
- no manage-mode-only features
- no private/local install support

Acceptance:

- the fixture boots without dotlineform-only routes, data, semantic references, or modules
- the app reads declared config and generated payloads rather than relying on hardcoded dotlineform route assumptions
- public search, routing, index tree, and document rendering work in the fixture

#### Portable Local Manage Fixture

This is a later fixture once the local backend/write boundary is stable.
It proves the local editing install contract, including private/local generated output expectations.

Scope:

- local source docs
- local Docs Viewer backend reachable
- source write and rebuild operation
- generated output root
- private/local generated output path
- no public route requirement
- no dotlineform Studio semantic-link editing requirement

Acceptance:

- the fixture can run a local manage workflow without dotlineform-specific Studio services
- writes and rebuilds use the declared Docs Viewer source/output config
- private/local generated outputs are supported without requiring public publication

Acceptance:

- fixture failures identify hidden setup assumptions in the portable contract
- any remaining hidden assumptions are added back to this request as follow-up tasks
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) can be validated against at least the public fixture before the install contract is considered low-friction

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
