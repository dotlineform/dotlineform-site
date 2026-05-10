---
doc_id: site-request-js-config-structural-review
title: JavaScript And Browser Config Structural Review Request
added_date: 2026-05-10
last_updated: "2026-05-10 17:20"
ui_status: in-progress
parent_id: change-requests
sort_order: 212
hidden: false
---
# JavaScript And Browser Config Structural Review Request

Status:

- Slice 1 implemented
- Slice 2 implemented
- Slice 3 implemented
- Catalogue editor execution plan created
- Catalogue editor Slice A implemented
- Catalogue editor Slice B implemented
- Catalogue editor Slice C implemented
- Catalogue editor Slice D implemented
- Catalogue editor Slice E implemented
- Catalogue editor Slice F implemented
- Catalogue editor Slice G implemented
- Catalogue editor execution sequence complete
- Slice 4 child doc created
- Slice 4 implemented
- Slice 5 child doc created
- Slice 5 implemented

## Active Execution Queue

The [Catalogue Editor Extraction Plan](/docs/?scope=studio&doc=site-request-js-config-structural-review-catalogue-editor-extraction-plan) is complete.
[Config Ownership Cleanup Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-config-ownership) is complete.
[Public Runtime Extraction Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-public-runtime-extraction) is complete.

## Summary

Review the browser-side JavaScript and associated JSON config used across the public site, Docs Viewer, and Studio routes.

The current runtime has useful first-generation boundaries: shared Studio config loading, transport helpers, route ready-state helpers, modal helpers, UI contracts, search policy parsing, and some catalogue/tag domain helpers.
The main issue is uneven ownership.
Some areas now have clear domain modules, while other route controllers still combine page orchestration, domain normalization, transport, generated-data reads, rendering, confirmation flows, and performance-sensitive data loading.

This request should become a spec and implementation plan if the priority areas below are accepted.

## Review Goals

- improve maintainability by giving repeated browser behavior a clear module owner
- improve modularity by splitting large route controllers only where a stable boundary exists
- improve extensibility by keeping route shell, domain rules, service transport, config policy, and rendering contracts separate
- improve ownership and domain alignment across public site, Docs Viewer, Studio, Search, Catalogue, Analytics, Library, and import/export workflows
- improve client-side performance by reducing unnecessary payload fetches, stale module risk, and route-local duplicate code

## Non-Goals

- do not rewrite all JavaScript into a framework
- do not bundle or transpile the site unless a later performance decision justifies the added build step
- do not split files only because they are long
- do not change route URLs, local service endpoint contracts, generated JSON schemas, or existing user workflows as part of the review
- do not fold the existing [Import/Export System Review Request](/docs/?scope=studio&doc=site-request-import-export-system-review) into this request; treat it as a related owner for that workflow

## Implementation Principles

- JS folder moves should follow an ownership boundary identified by an implementation slice.
- Do not make a standalone directory cleanup whose main result is changed import paths.
- When a slice extracts or moves JS, place new modules where the domain owner is obvious, such as shared Studio runtime, Catalogue, Analytics, Docs, Import/Export, Search, or public-site runtime.
- Keep route entry modules easy to find unless the slice deliberately changes the route-loading contract.

## Current Surface

Primary browser code:

- public site scripts under `assets/js/`
- public search modules under `assets/js/search/`
- Studio route modules under `assets/studio/js/`
- inline route scripts in layouts such as `_layouts/work.html`, `_layouts/work_details.html`, and `_layouts/series.html`

Primary browser-facing config and data:

- `assets/studio/data/studio_config.json`
- `assets/studio/data/export_import_adapters.json`
- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/catalogue_field_registry.json`
- `assets/studio/data/activity_contract.json`
- generated search indexes under `assets/data/search/<scope>/index.json`
- generated Studio/catalogue lookup payloads under `assets/studio/data/catalogue_lookup/`

Size signals from this review:

- `assets/js/docs-viewer.js` is about 3,362 lines and 117 KB
- `assets/studio/js/catalogue-work-editor.js` is about 3,181 lines and 134 KB
- `assets/studio/js/catalogue-work-detail-editor.js`, `catalogue-series-editor.js`, `tag-studio.js`, `tag-aliases.js`, `catalogue-moment-editor.js`, `studio-config.js`, and `tag-registry.js` are the next largest browser modules
- `assets/studio/data/studio_config.json` is about 85 KB
- `assets/data/search/catalogue/index.json` is about 1.7 MB
- Studio canonical catalogue source files and lookup payloads are multi-hundred-KB to multi-MB browser-readable assets, though most route controllers only need selected slices

## Existing Strengths

- Studio pages already share `studio-config.js`, `studio-data.js`, `studio-transport.js`, `studio-route-state.js`, `studio-modal.js`, and `studio-ui.js`.
- Tag registry, tag aliases, and tag assignment workflows already show a useful pattern: route controller plus domain helpers plus save/service helpers.
- Catalogue work, work-detail, and series editors already have field modules that own draft shaping, payload shaping, normalization, validation, and id suggestions.
- Search policy parsing is separate from search page orchestration.
- Import/export domain availability has a first adapter registry in `assets/studio/data/export_import_adapters.json`.
- Docs Viewer already fetches generated JSON rather than embedding docs content directly in the page shell.

## Findings

### 1. Studio module cache-busting is inconsistent

Priority: high.

Studio page entry scripts are loaded without the shared asset version query, for example `studio/catalogue-work/index.md` and other Studio routes use `type="module"` script tags without `?v=...`.
The default layout exposes a `dlf-asset-version` meta tag and cache-busts classic scripts, and some dynamic imports read that meta value, but static ES module imports from unversioned Studio entry modules still resolve to unversioned module URLs.

Risk:

- after a build or deploy, a browser can keep stale Studio entry modules or static imports while `studio_config.json` and generated data have changed
- this is most likely to affect local Studio work because page behavior, config, and service payloads evolve together

Likely direction:

- add a shared Studio module script include or layout helper that appends the same asset version query to every `assets/studio/js/*.js` entry script
- keep the existing meta fallback for dynamic imports
- after the entry scripts are versioned, verify whether static imports inherit enough cache busting through browser module graph rules; if not, consider versioned dynamic import wrappers only for route-local dependency graphs

### 2. Docs Viewer is a large mixed-responsibility runtime

Priority: high.

`assets/js/docs-viewer.js` owns route parsing, index tree state, sidebar rendering, search loading/rendering, bookmarks and IndexedDB persistence, Docs management mode, generated-data reads, metadata editing, drag/drop move behavior, archive/delete/show flows, config text application, fetch retry behavior, and link interception in one IIFE.

Risk:

- small Docs Viewer changes require broad local knowledge
- management-mode changes and read-only viewer changes share the same state object and rendering paths
- behavior is hard to test below browser-smoke level
- future Analysis/Library/Studio scope differences are likely to add more conditionals to the same file

Likely direction:

- extract behavior-preserving modules around stable ownership boundaries:
  - `docs-viewer-config`
  - `docs-viewer-data-client`
  - `docs-viewer-tree`
  - `docs-viewer-search`
  - `docs-viewer-bookmarks`
  - `docs-viewer-management-client`
  - `docs-viewer-management-actions`
  - `docs-viewer-render`
- keep the public shell and DOM ids stable during extraction
- pin the current generated-data read and management-mode contracts before moving code

### 3. Catalogue editor route controllers remain too broad

Priority: high.

The catalogue work, detail, series, and moment editors are route-local controllers that still carry many responsibilities despite useful field helper modules.
The work editor is the clearest candidate: it combines media preview readiness, build-preview formatting, field diffing, modal composition, bulk mode, create mode, detail/file/link embedded entries, publication/delete flows, route query updates, service calls, and rendering.

Risk:

- new catalogue editor requirements may continue to duplicate logic across work, work-detail, series, and moment controllers
- field modules help with record shaping, but route controllers still own too much workflow policy
- broad controllers make it harder to reason about what belongs to Catalogue domain logic versus Studio UI shell behavior

Likely direction:

- extract shared catalogue editor modules in slices:
  - record identity and hash helpers
  - dirty-field and field-plan helpers
  - publication/delete/build preview modal formatters
  - embedded entry list helpers for work files and links
  - shared create/edit mode state helpers
  - catalogue editor service client built on `studio-transport.js`
- do not merge all catalogue editors into one mega-controller; keep route-specific composition, but move common domain/workflow behavior out of individual pages

### 4. `studio_config.json` is becoming a broad cross-domain payload

Priority: medium-high.

`studio_config.json` is the shared browser-facing route, data path, UI text, Docs Viewer, search, analysis, and catalogue option payload.
That single payload is fetched by most Studio routes, the public search page, and Docs Viewer even when a page needs only a small subset.
The loader module also owns Studio tag metrics and RAG computation, which is analysis-domain behavior rather than config-loading behavior.

The practical editing pain is already visible.
Simple UI-copy changes can require searching a roughly 1,400-line config file when the exact key name is not known.
That makes background ownership problems show up as slow, uncertain editing work: the maintainer has to scan unrelated route text, domain policy, data paths, and shared viewer/search settings just to find one UI label or status message.
Splitting UI text by domain or page would therefore be a useful side effect of the wider refactor, even before considering runtime payload size.

Risk:

- config ownership becomes unclear as new domains add copy, policy, paths, and options
- every route pays to fetch and parse all route copy and policy
- unrelated domain edits can create unexpected config merge or fallback behavior

Likely direction:

- keep `studio_config.json` as the root browser-facing manifest for paths and bootstrap defaults
- move domain-specific runtime policy into scoped config files only when there is a real second owner or performance benefit
- candidates:
  - `docs_viewer` policy and copy
  - search runtime policy and messages, already partly separate in `assets/data/search/policy.json`
  - analysis RAG policy and helper functions
  - catalogue editor UI copy and option lists if editor-specific config continues to grow
- move `computeStudioTagMetrics`, `computeStudioRag`, and `buildStudioRagTooltip` to an analysis/tag scoring owner, with `studio-config.js` only supplying raw config values

### 5. Public work/series layouts still contain substantial inline JavaScript

Priority: medium. First slice implemented.

Public work pages include route-local inline scripts for work payload caching, metadata rendering, details pagination, details thumbnail URLs, hash scrolling, and swipe bindings, plus `assets/js/work.js`.
Series and work-detail layouts have similar inline behavior.

Risk:

- inline scripts are harder to test, cache, and reuse than assets under `assets/js/`
- data formatting and navigation behavior are split between Liquid, inline JavaScript, and asset modules
- future public route behavior may drift away from Studio/public shared data helpers

Likely direction:

- extract public route helpers only where reuse or testability is clear:
  - public work payload client/cache
  - details section renderer and pager
  - shared public catalogue URL/media path helper
- leave tiny bootstrapping snippets in Liquid when they only pass page data into an asset module

Implemented first slice:

- added `assets/js/public-catalogue-runtime.js` for shared public catalogue fetch, generated-data URL, normalization, and thumbnail helpers
- updated `_layouts/work.html`, `_layouts/work_details.html`, `_layouts/series.html`, and `assets/js/work.js` to use the helper
- kept work metadata rendering, work-details grid rendering, work-detail context hydration, series grid rendering, pagination, and route-specific query preservation in the route templates

### 6. Search has a clear policy split but still does all matching on the main thread

Priority: medium.

The public search page has a reasonable split between `search-page.js` and `search-policy.js`, but aggregate search loads every enabled scope and scans all normalized entries on each render.
The catalogue search index is currently the largest search payload.

Risk:

- aggregate search cost grows with every new scope and generated field
- low-end mobile devices may feel input lag as index size grows
- route-owned search logic may need another performance boundary before adding richer ranking or filters

Likely direction:

- keep current simple client search until measurable lag appears
- add lightweight instrumentation first: loaded scope sizes, normalization time, first-result time, and render time
- if needed, add an optional Web Worker for aggregate search and large catalogue scope searches
- avoid introducing a search framework before the current payload size creates a real usability problem

### 7. Transport endpoints are centralized, but service ownership is still implicit

Priority: medium.

`studio-transport.js` centralizes local service endpoint URLs and generic JSON helpers, which is good.
The endpoint tables are grouped by service port, but route controllers still choose endpoint semantics directly.

Risk:

- route controllers know too much about local service endpoint names and payload contracts
- future endpoint moves or service splits require route-controller changes across the tree

Likely direction:

- keep endpoint constants centralized
- add small domain service clients when several routes share the same service semantics:
  - catalogue editor client
  - docs management client for non-viewer Studio pages
  - tag service client patterns already exist and can guide this

## Recommended Priority Order

1. Fix Studio module asset-versioning for all route entry scripts.
2. Create a Docs Viewer extraction spec with state/data/management/search/bookmark boundaries.
3. Create a Catalogue editor extraction spec focused first on `catalogue-work-editor.js`, then reusable editor helpers.
4. Split analysis tag scoring out of `studio-config.js` and clarify config ownership.
5. Extract public work route inline JavaScript where it creates reuse or testability value.
6. Add search performance instrumentation before considering workers or index reshaping.

## Draft Implementation Slices

### Slice 1: Studio Module Asset Versioning

Status: implemented.

- add a shared include for Studio module scripts or update existing route script tags consistently
- append the same asset version query used by `assets/js/*`
- verify a representative Studio route loads versioned entry scripts
- run a small browser smoke test on one static Studio route and one async Studio route

Detailed implementation tasks are tracked in [Studio Module Asset Versioning Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-module-versioning).

### Slice 2: Docs Viewer Boundary Spec

Status: implemented.

- inventory Docs Viewer functions by owner
- decide the target module list and public internal contracts
- identify tests or smoke checks for read-only docs, search, bookmarks, manage mode, metadata save, move undo, and generated-data reads
- write a follow-up task list before extraction

Detailed planning tasks are tracked in [Docs Viewer Boundary Spec Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-boundary).

### Slice 3: Catalogue Editor Boundary Spec

Status: implemented.

- inventory work, work-detail, series, and moment editor overlap
- define which helpers are Catalogue domain, Studio shell, transport, modal formatting, and route composition
- start with work editor because it has the largest mixed surface
- keep create/edit/bulk modes stable during extraction

Detailed planning tasks are tracked in [Catalogue Editor Boundary Spec Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-catalogue-editor-boundary).

### Slice 4: Config Ownership Cleanup

Status: implemented.

- document `studio_config.json` as root manifest plus UI-copy store, not a catch-all domain policy file
- move analysis tag scoring helpers out of `studio-config.js`
- decide whether Docs Viewer and catalogue editor copy remain in the shared file or become scoped files

Detailed planning tasks are tracked in [Config Ownership Cleanup Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-config-ownership).

### Slice 5: Public Runtime Extraction

- extract only the work-page helper code that is reused or difficult to test inline
- preserve current Liquid-rendered media URLs and page shell
- keep generated payload schemas stable

Detailed planning tasks are tracked in [Public Runtime Extraction Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-public-runtime-extraction).

### Slice 6: Search Performance Instrumentation

- add lightweight timing and payload-size reporting behind a local/debug flag
- use measurements to decide whether workers, per-scope lazy loading, or index slimming are justified

## Acceptance Criteria

- priority areas are accepted, rejected, or reprioritized explicitly
- each accepted area has a narrower implementation request before source changes begin
- ownership boundaries are clear enough that new JS work has an obvious home
- config ownership is clear enough that route paths, UI copy, domain policy, and generated-data schemas do not drift into one file by convenience
- performance changes are measurement-led unless the issue is already deterministic, such as unversioned Studio module scripts

## Related Docs

- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Import/Export System Review Request](/docs/?scope=studio&doc=site-request-import-export-system-review)
- [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review)
