---
doc_id: site-request-js-config-structural-review-docs-viewer-inventory
title: Docs Viewer Function Inventory
added_date: 2026-05-10
last_updated: "2026-05-10 14:45"
ui_status: done
parent_id: site-request-js-config-structural-review-docs-viewer-boundary
sort_order: 10
hidden: false
---
# Docs Viewer Function Inventory

Status:

- completed

## Purpose

This inventory supports [Docs Viewer Boundary Spec Slice](/docs/?scope=studio&doc=site-request-js-config-structural-review-docs-viewer-boundary).

It groups the current functions in `assets/js/docs-viewer.js` by owner so later extraction slices can move one responsibility at a time.
Line references describe the source file at the time of this inventory.

## Current Runtime Surface

Primary runtime file:

- `assets/js/docs-viewer.js`

Shared shell:

- `_includes/docs_viewer_shell.html`

Current route shells:

- `docs/index.md`
- `library/index.md`

The shell provides fixed DOM ids and route data attributes.
The runtime reads those elements once at startup and keeps all state inside one closure-local `state` object.

## Startup And Shared State

The first startup block owns DOM references, data attributes, constants, and the single mutable state object.
This block should stay in the entry controller until enough extracted modules have stable contracts.

Current responsibilities:

- read `#docsViewerRoot` and all shell element ids
- read `data-index-url`, `data-viewer-base-url`, `data-viewer-scope`, `data-search-index-url`, `data-studio-config-url`, and `data-management-base-url`
- define search, bookmark, management, retry, UI-status, and sidebar constants
- initialize the closure-local `state`

Extraction note:

- later modules should receive only the state or values they need, rather than importing DOM globals from the entry controller

## State, URL, And Route Helpers

Owner candidate:

- `docs-viewer-state.js`

Functions:

- `getCurrentDocId` at `assets/js/docs-viewer.js:176`
- `getCurrentHash` at `assets/js/docs-viewer.js:180`
- `getCurrentQuery` at `assets/js/docs-viewer.js:184`
- `getCurrentMode` at `assets/js/docs-viewer.js:188`
- `hasCanonicalScopeInUrl` at `assets/js/docs-viewer.js:192`
- `hasActiveQuery` at `assets/js/docs-viewer.js:197`
- `viewerUrl` at `assets/js/docs-viewer.js:801`
- `setHistory` at `assets/js/docs-viewer.js:2310`
- `routeFromAnchor` at `assets/js/docs-viewer.js:2397`
- `resolveDocId` at `assets/js/docs-viewer.js:2790`
- `applyCurrentRoute` at `assets/js/docs-viewer.js:2835`

Notes:

- `viewerUrl` depends on `viewerBaseUrl`, `viewerScope`, `includeScopeParam`, and management mode.
- `resolveDocId` depends on current docs maps and default-doc resolution.
- `applyCurrentRoute` is orchestration-heavy and should remain in the entry controller longer than the smaller helpers.

## Config And UI Text Helpers

Owner candidate:

- `docs-viewer-config.js`

Functions:

- `positiveInteger` at `assets/js/docs-viewer.js:255`
- `getConfigValue` at `assets/js/docs-viewer.js:260`
- `getConfigText` at `assets/js/docs-viewer.js:272`
- `normalizeUiStatuses` at `assets/js/docs-viewer.js:277`
- `formatText` at `assets/js/docs-viewer.js:301`
- `applyViewerConfig` at `assets/js/docs-viewer.js:309`
- `loadViewerConfig` at `assets/js/docs-viewer.js:381`

Notes:

- pure config helpers are good early extraction candidates.
- `applyViewerConfig` currently mutates state and DOM, so it should either stay in the entry controller or be split into pure normalization plus controller-owned application.

## Sidebar Collapse Helpers

Owner candidate:

- entry controller first; possible later `docs-viewer-sidebar.js`

Functions:

- `setRecentModeActive` at `assets/js/docs-viewer.js:201`
- `renderRecentButtonState` at `assets/js/docs-viewer.js:206`
- `sidebarCollapseAvailable` at `assets/js/docs-viewer.js:211`
- `readSidebarCollapsedState` at `assets/js/docs-viewer.js:216`
- `persistSidebarCollapsedState` at `assets/js/docs-viewer.js:224`
- `renderSidebarCollapsedState` at `assets/js/docs-viewer.js:232`
- `toggleSidebarCollapsed` at `assets/js/docs-viewer.js:247`

Notes:

- storage and rendering are currently mixed.
- this group is small enough to defer until larger ownership seams are clearer.

## Document Tree And Visibility Helpers

Owner candidate:

- `docs-viewer-tree.js`

Functions:

- `sortKey` at `assets/js/docs-viewer.js:157`
- `compareDocs` at `assets/js/docs-viewer.js:166`
- `buildChildrenMap` at `assets/js/docs-viewer.js:817`
- `isDocViewable` at `assets/js/docs-viewer.js:838`
- `isDocHidden` at `assets/js/docs-viewer.js:842`
- `isManageOnlyTreeDoc` at `assets/js/docs-viewer.js:850`
- `shouldIncludeDoc` at `assets/js/docs-viewer.js:862`
- `applyDocVisibility` at `assets/js/docs-viewer.js:868`
- `findAllDocById` at `assets/js/docs-viewer.js:883`
- `syncHiddenVisibilityForRequestedDoc` at `assets/js/docs-viewer.js:890`
- `isNonLoadableDoc` at `assets/js/docs-viewer.js:900`
- `statusForIndexDoc` at `assets/js/docs-viewer.js:904`
- `firstLoadableDescendantDocId` at `assets/js/docs-viewer.js:911`
- `resolveLoadableDocId` at `assets/js/docs-viewer.js:926`
- `viewerTargetDocId` at `assets/js/docs-viewer.js:933`
- `flattenRoots` at `assets/js/docs-viewer.js:945`
- `defaultDocId` at `assets/js/docs-viewer.js:951`
- `buildTrail` at `assets/js/docs-viewer.js:962`
- `displayRecentMetaForDoc` at `assets/js/docs-viewer.js:972`
- `expandTrail` at `assets/js/docs-viewer.js:985`
- `docChildren` at `assets/js/docs-viewer.js:1171`
- `docHasChildren` at `assets/js/docs-viewer.js:1175`

Notes:

- `sortKey`, `compareDocs`, `buildChildrenMap`, `isDocHidden`, and `isDocViewable` are strong first extraction candidates.
- `applyDocVisibility`, `isManageOnlyTreeDoc`, and `statusForIndexDoc` depend on state and management mode; move after pure tree helpers.

## Rendering Helpers

Owner candidate:

- `docs-viewer-render.js`, after state and tree helpers are extracted

Functions:

- `renderSidebar` at `assets/js/docs-viewer.js:993`
- `renderNavList` at `assets/js/docs-viewer.js:1003`
- `renderMeta` at `assets/js/docs-viewer.js:1083`
- `setStatus` at `assets/js/docs-viewer.js:1124`
- `hideDocPane` at `assets/js/docs-viewer.js:2261`
- `showDocPane` at `assets/js/docs-viewer.js:2268`
- `showSearchPane` at `assets/js/docs-viewer.js:2276`
- `showRecentPane` at `assets/js/docs-viewer.js:2281`
- `renderPayload` at `assets/js/docs-viewer.js:2287`
- `renderResultEntry` at `assets/js/docs-viewer.js:3025`
- `renderSearchEntry` at `assets/js/docs-viewer.js:3034`
- `renderRecentEntry` at `assets/js/docs-viewer.js:3039`
- `renderRecentMode` at `assets/js/docs-viewer.js:3043`
- `renderSearchPendingState` at `assets/js/docs-viewer.js:3062`
- `renderSearchMode` at `assets/js/docs-viewer.js:3073`

Notes:

- rendering helpers currently read state and DOM directly.
- `renderResultEntry`, `renderSearchEntry`, and `renderRecentEntry` are smaller and can move earlier than full sidebar rendering.
- full `renderSidebar` extraction should wait until tree and drag-state contracts are explicit.

## Bookmarks And Favourites

Owner candidate:

- `docs-viewer-favourites.js`

Functions:

- `bookmarkKey` at `assets/js/docs-viewer.js:404`
- `isoNow` at `assets/js/docs-viewer.js:408`
- `compareBookmarks` at `assets/js/docs-viewer.js:412`
- `normalizeBookmarkRecord` at `assets/js/docs-viewer.js:419`
- `getScopeBookmarks` at `assets/js/docs-viewer.js:437`
- `getBookmarkForDoc` at `assets/js/docs-viewer.js:443`
- `findBookmarkByKey` at `assets/js/docs-viewer.js:447`
- `nextBookmarkOrder` at `assets/js/docs-viewer.js:454`
- `defaultBookmarkLabel` at `assets/js/docs-viewer.js:460`
- `upsertBookmarkState` at `assets/js/docs-viewer.js:465`
- `removeBookmarkState` at `assets/js/docs-viewer.js:484`
- `renderBookmarkUi` at `assets/js/docs-viewer.js:494`
- `renderBookmarkToggle` at `assets/js/docs-viewer.js:500`
- `renderBookmarkRow` at `assets/js/docs-viewer.js:558`
- `openBookmarksDb` at `assets/js/docs-viewer.js:608`
- `loadBookmarks` at `assets/js/docs-viewer.js:647`
- `persistBookmark` at `assets/js/docs-viewer.js:664`
- `deleteBookmarkRecord` at `assets/js/docs-viewer.js:675`
- `initializeBookmarks` at `assets/js/docs-viewer.js:686`
- `addBookmarkForDoc` at `assets/js/docs-viewer.js:706`
- `removeBookmarkByKey` at `assets/js/docs-viewer.js:727`
- `toggleCurrentBookmark` at `assets/js/docs-viewer.js:739`
- `startBookmarkRename` at `assets/js/docs-viewer.js:750`
- `finishBookmarkRename` at `assets/js/docs-viewer.js:757`

Notes:

- bookmark storage, state mutation, and rendering are mixed.
- extract pure record helpers first, then IndexedDB storage, then controller adapters for rendering/event handling.
- `renderBookmarkUi`, `renderBookmarkToggle`, and `renderBookmarkRow` should either stay controller-owned or move to a renderer after storage/state is isolated.

## Status Pills And Metadata UI

Owner candidate:

- `docs-viewer-management-ui.js`, after management client extraction

Functions:

- `currentStatusValue` at `assets/js/docs-viewer.js:516`
- `statusPillsCanWrite` at `assets/js/docs-viewer.js:520`
- `renderStatusPills` at `assets/js/docs-viewer.js:530`
- `metadataModalOpen` at `assets/js/docs-viewer.js:1279`
- `metadataParentOptions` at `assets/js/docs-viewer.js:1385`
- `metadataParentOptionDisplay` at `assets/js/docs-viewer.js:1404`
- `renderMetadataParentOptions` at `assets/js/docs-viewer.js:1409`
- `resolveMetadataParentId` at `assets/js/docs-viewer.js:1423`
- `metadataStatusOptions` at `assets/js/docs-viewer.js:1444`
- `renderMetadataStatusOptions` at `assets/js/docs-viewer.js:1458`
- `renderMetadataStatusSelection` at `assets/js/docs-viewer.js:1464`
- `dismissMetadataParentSuggestions` at `assets/js/docs-viewer.js:1474`
- `closeMetadataModal` at `assets/js/docs-viewer.js:1484`
- `openMetadataModal` at `assets/js/docs-viewer.js:1499`

Notes:

- metadata parent option generation has useful pure pieces but depends on current all-doc state.
- modal open/close and status pills are strongly DOM-coupled.

## Management Capability, Transport, And Mutation Actions

Owner candidates:

- `docs-viewer-management-client.js`
- `docs-viewer-management-actions.js`, later if useful

Functions:

- `setManagementMessage` at `assets/js/docs-viewer.js:1130`
- `scopeManagementCapabilities` at `assets/js/docs-viewer.js:1136`
- `scopeSupportsGeneratedDataReads` at `assets/js/docs-viewer.js:1141`
- `scopeSupportsGeneratedSearchReads` at `assets/js/docs-viewer.js:1152`
- `managementArchiveAvailable` at `assets/js/docs-viewer.js:1543`
- `managementNoteText` at `assets/js/docs-viewer.js:1548`
- `renderManagementUi` at `assets/js/docs-viewer.js:1559`
- `fetchManagementJson` at `assets/js/docs-viewer.js:1649`
- `checkGeneratedDataReadCapability` at `assets/js/docs-viewer.js:1677`
- `initializeManagement` at `assets/js/docs-viewer.js:1709`
- `checkManagementCapabilities` at `assets/js/docs-viewer.js:1725`
- `reloadDocsIndex` at `assets/js/docs-viewer.js:1754`
- `handleCreateDoc` at `assets/js/docs-viewer.js:1779`
- `handleCreateRelatedDoc` at `assets/js/docs-viewer.js:1809`
- `handleEditMetadataSubmit` at `assets/js/docs-viewer.js:1847`
- `metadataPayloadForStatus` at `assets/js/docs-viewer.js:1909`
- `handleStatusPillClick` at `assets/js/docs-viewer.js:1922`
- `handleRebuildDocs` at `assets/js/docs-viewer.js:1954`
- `handleArchiveDoc` at `assets/js/docs-viewer.js:1977`
- `buildDeleteConfirmation` at `assets/js/docs-viewer.js:2004`
- `handleDeleteDoc` at `assets/js/docs-viewer.js:2026`
- `handleMakeViewable` at `assets/js/docs-viewer.js:2074`
- `handleDraftToggleChange` at `assets/js/docs-viewer.js:2104`
- `handleOpenSource` at `assets/js/docs-viewer.js:2220`

Notes:

- `fetchManagementJson`, capability checks, and generated-data capability helpers are the strongest management-client candidates.
- mutation action handlers mix prompts, busy-state updates, service calls, reload orchestration, and rendering.
- move only the client first; keep user-prompt and reload orchestration in the entry controller until smoke tests cover them.

## Drag, Drop, Move, And Undo

Owner candidate:

- keep entry-controller-owned until after management client extraction

Functions:

- `currentSelectedDoc` at `assets/js/docs-viewer.js:1163`
- `currentContextMenuDoc` at `assets/js/docs-viewer.js:1167`
- `managementDragEnabled` at `assets/js/docs-viewer.js:1179`
- `canDragDoc` at `assets/js/docs-viewer.js:1183`
- `dropPositionForRow` at `assets/js/docs-viewer.js:1188`
- `canDropOnDoc` at `assets/js/docs-viewer.js:1204`
- `currentDropTargetFromEvent` at `assets/js/docs-viewer.js:1214`
- `clearDragState` at `assets/js/docs-viewer.js:1228`
- `normalizeSortOrderValue` at `assets/js/docs-viewer.js:1235`
- `moveUndoRecordChanged` at `assets/js/docs-viewer.js:1239`
- `normalizeMoveUndoRecords` at `assets/js/docs-viewer.js:1247`
- `moveUndoPayloadRecords` at `assets/js/docs-viewer.js:1265`
- `updateNavDragState` at `assets/js/docs-viewer.js:1524`
- `handleMoveDoc` at `assets/js/docs-viewer.js:2128`
- `handleUndoMove` at `assets/js/docs-viewer.js:2181`

Notes:

- drag/drop mixes DOM geometry, management mode, tree state, service writes, undo state, and reload orchestration.
- `normalizeSortOrderValue`, `moveUndoRecordChanged`, `normalizeMoveUndoRecords`, and `moveUndoPayloadRecords` are pure enough to move earlier if needed.
- full drag/drop extraction should be a late slice.

## Context Menu And Viewability Helpers

Owner candidate:

- entry controller first; split only after management client and render boundaries are clearer

Functions:

- `contextMenuEnabled` at `assets/js/docs-viewer.js:1275`
- `hideContextMenu` at `assets/js/docs-viewer.js:1283`
- `showContextMenu` at `assets/js/docs-viewer.js:1292`
- `collectDescendantDocIds` at `assets/js/docs-viewer.js:1305`
- `collectAllDescendantDocIds` at `assets/js/docs-viewer.js:1314`
- `nonViewableAncestorDocs` at `assets/js/docs-viewer.js:1323`
- `docTitleList` at `assets/js/docs-viewer.js:1335`
- `viewabilityTargetDocIds` at `assets/js/docs-viewer.js:1341`

Notes:

- descendant collection is reusable tree logic.
- `viewabilityTargetDocIds` is mixed: it combines tree traversal, prompts, status messages, and management policy.

## Document Loading And Generated Data Reads

Owner candidate:

- `docs-viewer-data.js`

Functions:

- `loadDoc` at `assets/js/docs-viewer.js:2329`
- `initializeIndex` at `assets/js/docs-viewer.js:2812`
- `loadIndex` at `assets/js/docs-viewer.js:2876`
- `appendAssetVersion` at `assets/js/docs-viewer.js:3162`
- `requestUrl` at `assets/js/docs-viewer.js:3173`
- `requestOptions` at `assets/js/docs-viewer.js:3182`
- `generatedRequestOptions` at `assets/js/docs-viewer.js:3189`
- `waitForReloadRetry` at `assets/js/docs-viewer.js:3196`
- `shouldRetryReload` at `assets/js/docs-viewer.js:3202`
- `fetchJsonOnce` at `assets/js/docs-viewer.js:3211`
- `fetchGeneratedJsonOnce` at `assets/js/docs-viewer.js:3231`
- `fetchJsonWithRetry` at `assets/js/docs-viewer.js:3243`
- `fetchGeneratedJsonWithRetry` at `assets/js/docs-viewer.js:3255`
- `fetchPreferredGeneratedJson` at `assets/js/docs-viewer.js:3267`
- `indexIncludesExpectedDoc` at `assets/js/docs-viewer.js:3280`
- `fetchIndexWithRetry` at `assets/js/docs-viewer.js:3288`
- `managementReloadPath` at `assets/js/docs-viewer.js:3312`
- `readAssetVersion` at `assets/js/docs-viewer.js:3323`

Notes:

- generic request helpers are strong early extraction candidates.
- `fetchPreferredGeneratedJson` depends on management generated-data capability, so it needs a small capability adapter or a callback.
- `loadDoc` and `initializeIndex` are orchestration-heavy and should remain in the entry controller until data request helpers are stable.

## Search And Recently Added

Owner candidate:

- `docs-viewer-search.js`

Functions:

- `cancelSearchDebounce` at `assets/js/docs-viewer.js:2323`
- `loadSearchEntries` at `assets/js/docs-viewer.js:2890`
- `normalizeSearchEntries` at `assets/js/docs-viewer.js:2923`
- `scoreSearchEntry` at `assets/js/docs-viewer.js:2959`
- `matchesAllTokens` at `assets/js/docs-viewer.js:2975`
- `collectSearchMatches` at `assets/js/docs-viewer.js:2984`
- `compareRecentDocs` at `assets/js/docs-viewer.js:3006`
- `collectRecentDocs` at `assets/js/docs-viewer.js:3015`

Notes:

- `normalizeSearchEntries`, `scoreSearchEntry`, `matchesAllTokens`, `collectSearchMatches`, `compareRecentDocs`, and `collectRecentDocs` are good pure extraction candidates.
- `loadSearchEntries` depends on generated-data reads and should move with or after data-client helpers.
- search rendering should remain separate from scoring/collection.

## Event Binding And Lifecycle

Owner candidate:

- `docs-viewer.js` entry controller

Functions:

- `bindLinkInterception` at `assets/js/docs-viewer.js:2411`

Top-level listeners:

- `popstate`
- `scroll`
- `resize`
- `keydown`

Top-level startup calls:

- `bindLinkInterception()`
- `renderSidebarCollapsedState()`
- `loadViewerConfig()`
- `initializeBookmarks()`
- `initializeManagement()`
- `loadIndex()`

Notes:

- event binding should stay in the entry controller until extracted modules expose stable command-style functions.
- after extraction, the entry controller should still own lifecycle sequencing and DOM event binding.

## Generic Utilities

Owner candidates:

- colocate with first consumer, or create `docs-viewer-utils.js` only if several modules need them

Functions:

- `normalize` at `assets/js/docs-viewer.js:3329`
- `normalizeDocIdSet` at `assets/js/docs-viewer.js:3337`
- `escapeHtml` at `assets/js/docs-viewer.js:3347`
- `cssEscape` at `assets/js/docs-viewer.js:3356`

Notes:

- `normalize` is needed by search and route query checks.
- `escapeHtml` is currently render-only.
- `cssEscape` is DOM-selector-only.
- avoid a general utility module unless these helpers are genuinely shared after extraction.

## Mixed-Responsibility Hotspots

These areas should not be the first extraction targets:

- `applyViewerConfig`
  mixes config normalization, state writes, DOM labels, metadata controls, sidebar rendering, and recent-mode rerendering
- `renderNavList`
  mixes tree rendering, hidden/viewable display, status pills, route URL generation, and drag affordances
- `renderManagementUi`
  mixes capability state, busy state, selected-doc state, search-mode restrictions, note rendering, and button enablement
- `handleEditMetadataSubmit`
  mixes form validation, parent resolution, payload shaping, service calls, modal close, reload, and status rendering
- `handleMoveDoc` and `handleUndoMove`
  mix drag state, service calls, undo normalization, reload, and management UI
- `loadDoc`
  mixes route state, payload cache, data fetch, render state, status messages, and history behavior
- `bindLinkInterception`
  is a large event-binding hub and should remain entry-controller-owned until command functions are stable

## Recommended Early Extraction Candidates

1. Pure tree helpers:
   `sortKey`, `compareDocs`, `buildChildrenMap`, `isDocHidden`, `isDocViewable`, `normalizeDocIdSet`

2. Pure search helpers:
   `normalizeSearchEntries`, `scoreSearchEntry`, `matchesAllTokens`, `collectSearchMatches`, `compareRecentDocs`, `collectRecentDocs`

3. Bookmark record helpers:
   `bookmarkKey`, `isoNow`, `compareBookmarks`, `normalizeBookmarkRecord`

4. Request helpers:
   `appendAssetVersion`, `requestUrl`, `requestOptions`, `generatedRequestOptions`, `waitForReloadRetry`, `shouldRetryReload`, `fetchJsonOnce`, `fetchJsonWithRetry`, `readAssetVersion`

5. Management client transport:
   `fetchManagementJson`, `scopeSupportsGeneratedDataReads`, `scopeSupportsGeneratedSearchReads`, capability checking helpers

These can be moved with lower risk than rendering, modal, drag/drop, or lifecycle code.
