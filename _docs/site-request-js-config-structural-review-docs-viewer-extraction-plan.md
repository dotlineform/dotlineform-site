---
doc_id: site-request-js-config-structural-review-docs-viewer-extraction-plan
title: Docs Viewer Extraction Plan
added_date: 2026-05-10
last_updated: "2026-05-10 14:36"
ui_status: in-progress
parent_id: site-request-js-config-structural-review-docs-viewer-boundary
sort_order: 20
hidden: false
---
# Docs Viewer Extraction Plan

Status:

- completed plan
- Slice A implemented
- Slice B implemented
- Slice C implemented
- slices D-F to be implemented

## Purpose

This plan turns the [Docs Viewer Function Inventory](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-inventory) into implementation-ready extraction slices.

The plan intentionally avoids splitting runtime code in the boundary-spec slice.
Its role is to define the module target, import direction, contracts, and verification map that later implementation slices should use.

## Target Module Shape

Target modules:

- `assets/js/docs-viewer.js`
  entry controller, DOM references, event binding, lifecycle sequencing, current shared state object, and cross-module coordination
- `assets/js/docs-viewer-tree.js`
  document sorting, visibility checks, children map construction, trail/default-doc helpers, and non-loadable target resolution
- `assets/js/docs-viewer-search.js`
  search-entry normalization, scoring, matching, recent-doc collection, and pure result ordering
- `assets/js/docs-viewer-favourites.js`
  bookmark record normalization, ordering, key generation, and IndexedDB persistence helpers
- `assets/js/docs-viewer-data.js`
  asset-versioned JSON request helpers, retry handling, static/generated read preference, and index/payload/search request primitives
- `assets/js/docs-viewer-management-client.js`
  docs-management capability reads and POST helpers for create, metadata update, viewability, move, restore move, archive, delete, rebuild, and open-source actions
- `assets/js/docs-viewer-render.js`
  only after earlier slices: focused rendering helpers for nav rows, metadata, search/recent result rows, status, and pane visibility

Deferred or optional modules:

- `assets/js/docs-viewer-management-ui.js`
  modal, status pills, management toolbar, context menu, and button-state rendering
- `assets/js/docs-viewer-drag-drop.js`
  drag/drop geometry, drop validation, move undo normalization, and drag affordance rendering

## Import Direction

Allowed direction:

- `docs-viewer.js` imports all extracted modules.
- extracted modules do not import `docs-viewer.js`.
- pure modules do not read DOM or mutate the shared state object directly.
- data and management client modules can accept `fetch`, URLs, scope, and capability callbacks as arguments.
- render modules can accept DOM element references and shaped state, but should not fetch data or call write endpoints.

Avoid:

- circular imports
- modules that import and mutate a singleton viewer state object
- service endpoint strings leaking back into render/event code after a management client exists
- a generic utility module before there is demonstrated shared utility pressure

## Public Internal Contracts

Tree helpers:

- input: arrays of doc records, viewer options, selected doc ids, and small option objects
- output: sorted arrays, `Map` instances, `Set` instances, doc ids, or booleans
- no DOM access
- no fetches
- no history writes

Search helpers:

- input: generated search entries, docs arrays, normalized query text, recent limit
- output: normalized entries, match records, sorted doc arrays, or result summaries
- no DOM access
- no history writes
- no fetches except through later data-client glue

Favourites helpers:

- record helpers should be pure
- storage helpers can use an injected `indexedDB` object or default to `window.indexedDB`
- storage helpers return promises and normalized records
- rendering and event handling stay in the entry controller until a render module exists

Data helpers:

- input: static URLs, generated-read URLs, asset version, reload nonce, retry settings, and capability callbacks
- output: parsed JSON payloads or errors with HTTP status where available
- no DOM rendering
- no history writes
- no mutation endpoint POSTs

Management client helpers:

- input: base URL, scope, path/action args, and optional fetch implementation
- output: parsed management response payloads or errors
- no modal prompts
- no button-state rendering
- no docs index reload orchestration

Render helpers:

- input: DOM references, shaped records, route URL callbacks, and display options
- output: DOM updates or HTML strings
- no fetches
- no write calls
- no persistent storage writes

## Implementation Slices

### Slice A: Tree And Visibility Helpers

Status: implemented.

Move the lowest-risk pure document-tree helpers into `docs-viewer-tree.js`.

Candidate functions:

- `sortKey`
- `compareDocs`
- `buildChildrenMap`
- `isDocHidden`
- `isDocViewable`
- `normalizeDocIdSet`

Implementation result:

- `assets/js/docs-viewer-tree.js` now owns the pure sort, children-map, viewability, hidden-state, and doc-id set helpers
- `assets/js/docs-viewer.js` imports the tree helpers and keeps route state, management flags, visibility filtering, rendering, and lifecycle orchestration local
- `_includes/docs_viewer_shell.html` now loads the Docs Viewer entry script as an ES module so the extracted helper can be statically imported
- `buildChildrenMap` receives management visibility options from the entry controller instead of reading viewer state directly

Verification:

- Jekyll build
- read-only `/docs/?scope=studio&doc=studio-runtime` smoke
- `/library/?doc=library` smoke
- manage-mode hidden toggle smoke if practical

### Slice B: Search And Recent Pure Helpers

Status: implemented.

Move pure search and recent-doc helpers into `docs-viewer-search.js`.

Candidate functions:

- `normalizeSearchEntries`
- `scoreSearchEntry`
- `matchesAllTokens`
- `collectSearchMatches`
- `compareRecentDocs`
- `collectRecentDocs`

Implementation result:

- `assets/js/docs-viewer-search.js` now owns search text normalization, search-entry normalization, scoring, token matching, pure result ordering, recent-doc ordering, and recent-doc collection
- `assets/js/docs-viewer.js` imports the search helpers and keeps search index loading, debounce behavior, URL state, pane switching, result rendering, and recently-added button state local
- `collectSearchMatches` receives normalized entries and query text from the entry controller instead of reading viewer state directly
- `collectRecentDocs` receives the already viewable docs array and recent limit from the entry controller instead of reading viewer state directly

Verification:

- search query smoke for Studio docs
- search query smoke for Library docs
- recently added button smoke
- search result click smoke

### Slice C: Favourites Record And Storage Helpers

Status: implemented.

Move bookmark record helpers and IndexedDB storage helpers into `docs-viewer-favourites.js`.

Candidate functions:

- `bookmarkKey`
- `isoNow`
- `compareBookmarks`
- `normalizeBookmarkRecord`
- `openBookmarksDb`
- `loadBookmarks`
- `persistBookmark`
- `deleteBookmarkRecord`

Implementation result:

- `assets/js/docs-viewer-favourites.js` now owns bookmark key generation, timestamp generation, bookmark ordering, record normalization, and IndexedDB open/load/save/delete helpers
- `assets/js/docs-viewer.js` imports the favourites helpers and keeps bookmark state list updates, row rendering, toggle rendering, click/contextmenu handling, rename handling, and status messages local
- storage helpers receive the controller-provided `indexedDB` object and DB settings instead of reading viewer state or DOM directly
- storage-open failures mark the controller bookmark UI as unsupported without exposing storage details to render code

Keep in entry controller for this slice:

- bookmark row rendering
- bookmark toggle rendering
- bookmark click/contextmenu event handling

Verification:

- add/remove bookmark smoke
- rename bookmark smoke if practical
- reload persistence smoke

### Slice D: Data Fetch Helpers

Move asset-version, retry, and generated-read request helpers into `docs-viewer-data.js`.

Candidate functions:

- `appendAssetVersion`
- `requestUrl`
- `requestOptions`
- `generatedRequestOptions`
- `waitForReloadRetry`
- `shouldRetryReload`
- `fetchJsonOnce`
- `fetchGeneratedJsonOnce`
- `fetchJsonWithRetry`
- `fetchGeneratedJsonWithRetry`
- `fetchPreferredGeneratedJson`
- `indexIncludesExpectedDoc`
- `fetchIndexWithRetry`
- `managementReloadPath`
- `readAssetVersion`

Verification:

- static generated docs index load
- static selected payload load
- search index load
- generated-data read fallback with management server unavailable
- generated-data read path with management server mocked or running, if practical

### Slice E: Management Client

Move management endpoint transport and action-specific POST wrappers into `docs-viewer-management-client.js`.

Candidate functions:

- `fetchManagementJson`
- `scopeSupportsGeneratedDataReads`
- `scopeSupportsGeneratedSearchReads`
- capability read helpers
- wrappers for `/docs/create`, `/docs/update-metadata`, `/docs/update-viewability-bulk`, `/docs/move`, `/docs/restore-move`, `/docs/archive`, `/docs/delete-preview`, `/docs/delete-apply`, `/docs/rebuild`, and `/docs/open-source`

Keep in entry controller for this slice:

- prompts and confirms
- busy-state updates
- modal interactions
- docs index reload orchestration
- status and management message rendering

Verification:

- manage mode unavailable smoke
- metadata save request interception smoke
- rebuild request interception smoke
- delete preview/apply request interception smoke only if scoped narrowly

### Slice F: Management UI Or Drag/Drop Follow-Up

Only start this after the client and pure helpers are stable.

Candidate directions:

- status pill and metadata modal rendering helpers
- context menu rendering helpers
- drag/drop pure helpers and undo normalization

Verification:

- metadata modal open/close smoke
- status pill write interception smoke
- drag/drop move interception smoke
- undo move interception smoke

## Smoke Check Map

Read-only docs:

- route: `/docs/?scope=studio&doc=studio-runtime`
- expect: docs index loads, selected doc content renders, title/meta render, no manage toolbar outside manage mode

Library route:

- route: `/library/?doc=library`
- expect: library docs index loads, selected doc content renders, URL does not require `scope=library`

Search:

- route: `/docs/?scope=studio&doc=studio-runtime`
- action: type a query into `#docsViewerSearchInput`
- expect: URL gains `q=...`, results render, clicking a result loads a doc and clears search state

Recently added:

- route: `/docs/?scope=studio&doc=studio-runtime`
- action: click `#docsViewerRecentButton`
- expect: results pane renders recent docs and doc links remain routable

Favourites:

- route: `/docs/?scope=studio&doc=studio-runtime`
- action: click `#docsViewerBookmarkToggle`
- expect: bookmark pill appears, reload preserves it, remove clears it

Manage mode unavailable:

- route: `/docs/?scope=studio&mode=manage&doc=studio-runtime`
- setup: no docs-management server
- expect: manage row appears with unavailable message and controls disabled/hidden according to current behavior

Metadata save:

- route: `/docs/?scope=studio&mode=manage&doc=studio-runtime`
- setup: intercept `/docs/update-metadata`
- action: open Edit, change safe field in modal, submit
- expect: POST payload carries `scope`, `doc_id`, `title`, `summary`, `ui_status`, `hidden`, `parent_id`, and `sort_order`

Move and undo:

- route: `/docs/?scope=studio&mode=manage&doc=<leaf-doc>`
- setup: intercept `/docs/move`, then `/docs/restore-move`
- action: drag a leaf doc to a valid target, then click undo
- expect: move payload carries `scope`, `doc_id`, `target_doc_id`, `position`; undo payload carries `scope`, `focus_doc_id`, and `records`

Generated-data reads:

- route: direct selected doc and search route
- setup: compare management unavailable fallback and available generated-read response
- expect: static JSON fallback still works; generated-read path uses no-store request behavior when available

## First Implementation Recommendation

Start with Slice A.

Reason:

- the tree helpers are heavily used but mostly pure
- the write set should be limited to `assets/js/docs-viewer.js` plus one new module
- no management service is required for the basic smoke checks
- failures should be easy to localize because behavior should remain unchanged

Do not start with management, drag/drop, or modal code.
Those paths mix too many concerns and need stronger smoke coverage before extraction.
