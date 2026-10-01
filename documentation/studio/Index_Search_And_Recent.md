---
draft: false
doc_id: d-20261001-203710-09959e
title: Index Search And Recent
added_date: "2026-10-01 20:37:10"
last_updated: "2026-10-01 21:03:10"
summary: Share incremental sidebar tracking across document navigation, then move Search and Recent into retained Index panel views without index or document reloads on return.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Index Search And Recent

Status: agreed feature proposal with proposed delivery steps. The current loading/validation baseline has been inspected; the remaining readiness work and implementation are pending. This feature is parented to [Planned Features](Planned_Features.md).

Move the shared Docs Viewer Search and Recent controls into the Index panel and make their results alternative views of that panel. Users can open several results while the list remains visible and the document appears in the main pane. The retained tree continues tracking the displayed document while hidden; returning to it reveals the current selection without fetching its data or redrawing it merely because it became visible.

First improve the shared sidebar's selection and branch updates for ordinary navigation. The retained results views then use that same behavior. This is one bounded delivery, with the shared sidebar improvement implemented before the Search and Recent integration.

## Controls And Availability

Recent and Search occupy the first row of the Index panel. In Manage, Index Actions and Position move to a second row. These tree-specific management controls are disabled while Search or Recent results replace the tree; document controls continue to operate on the displayed document under their normal capability rules.

Search and Recent are available in the normal document layout. They may be unavailable in any expanded or media view mode. No additional entry point is required in those modes. Hiding the Index panel can retain its active view and list state for the return to normal layout.

The shared behavior applies to the public reader and local Manage. Public narrow-screen layout must keep the displayed document reachable when results sit above it; local Manage retains its desktop layout boundary.

## Search And Recent Interaction

- Entering a non-empty search switches the Index panel from its tree to Search results. The currently displayed document stays visible.
- Clicking a result opens its exact document in the main pane and highlights the active result. The query, results, paging state and list scroll position remain in place.
- Clearing Search reveals the normal Index tree and keeps the currently displayed document. The hidden tree has already followed document selection and required ancestor expansion; revealing it scrolls the selected row into view as needed. Clearing Search does not reload the current document or reopen the document displayed when Search began.
- Recent switches the Index panel to its recent-document list and clears an active search. Clicking a recent result opens its document while retaining the list.
- Clicking Recent again restores the tree with the same current-document tracking behavior. Typing a query while Recent is active switches to Search results.
- Loading, error, empty-result and existing More states belong inside the active results view.

Search state and document selection are independent. Opening a document must no longer clear the active query or dismiss the results. Back and Forward navigation must keep the document target and active Index view consistent, including collection detail targets.

For example, start Search while document A is displayed, then open result B. Clearing Search leaves B displayed and brings its Index row into view. The document that was visible when Search started has no restoration role. Removing the query retains the current exact document route, including any collection `subdoc` target.

## Independent Related Links Panel

Search results in the Index panel and pinned Related links in the [Info Panel](Info_Panel.md) can remain open together in the normal reader layout. Each owns its own list state and both use the shared document-navigation path to change the main pane. Recent can coexist with the pinned Info panel on the same basis.

- Following a result, a pinned Related link or an in-app document-content link preserves the active Search query/results or Recent list, including its paging and scroll position.
- The Info panel remains pinned to its captured document when navigation changes the main pane. Another pin replaces that capture; Close releases it. Clearing Search or leaving Recent affects only the Index view, and closing or replacing the Info capture does not reset the Index results.
- If the newly opened exact target is represented in the displayed results, highlight its row. If it is outside those results, preserve the list with no active result highlighted. Match ordinary or collection/document identity, rather than title.
- The hidden tree follows the current document regardless of which list or document-content link opened it. Revealing the tree uses its already current selection.

Retain the Info panel's existing capture and document-mode lifecycle, including release on Source entry. Coexistence requires no shared list state, new relationship fetch or coordination between the two lists. Their common responsibility is opening an exact document target through the reader's navigation owner.

## Compact Result Rows

Both Search and Recent use the same row format:

```text
<collection icon> <document title>
```

Remove the date and collection-name subtitle from the displayed row. Keep existing Search relevance and Recent date-based ordering; hiding metadata does not remove it from generated data or change selection policy.

Collection documents use their owner's configured icon. Ordinary collection report hosts use the icon of the collection they host; other ordinary documents use `dlf-doc`. Reuse the loaded collection configuration and existing artwork boundary described in [Source Organisation](Source_Organisation.md#collection-icons), without a second icon mapping or collection-manifest fetch.

The document title is the link label and the icon is decorative. Preserve exact document identity when titles match. Use compact spacing and bounded scrolling suited to the Index panel, without adding summaries or snippets.

## Shared Incremental Sidebar Tracking

Use one current-document selection owner and one sidebar tracking path for ordinary navigation and result navigation. Keep tracking the current target whether the tree is visible or hidden; there is no separate return-from-search catch-up operation or saved original-document selection.

Update the previous and current selection markers and expand the current target's ancestors incrementally. Manual branch expansion or collapse updates only the affected branch. Keep unrelated tree nodes mounted to preserve their focus, expansion and scroll state. Collection details retain the existing collection-host tracking behavior.

Scroll the selected row into view only when the tree is visible and the row needs it. Hidden tracking must not scroll the results list or move focus away from the user's current control. When the tree becomes visible, position its already current selection as needed. Current-document tracking takes precedence over restoring the old tree scroll position when the displayed document changed.

Keep full rendering for initial loading and broader authoritative index replacement or reconciliation where appropriate. Actual source and hierarchy changes continue through their existing update owners, including existing targeted structural updates. This improvement does not require a general DOM-diff framework or a redesign of every index mutation.

## Retained Index Views

Treat Index, Search results and Recent results as views of the existing Index panel. The main pane independently owns the displayed document and its modes.

Keep the tree mounted while a results view is active. Retain the existing loaded document model and tree nodes, applying the shared incremental tracking updates as documents change. Results use their own mounted area beside the hidden tree. Switching views changes visibility; it does not call the index loader, clear and rebuild the tree, or manufacture a separate index snapshot.

Returning to the tree reveals its already synchronized selection and adjusts scroll only as needed to show the current row. It does not fetch the index, reload a document or run a separate selection-reconciliation pass. Search and Recent retain their own list state while users open results.

Actual source, document or hierarchy changes still follow the owning index-update workflow. Retention must not suppress those updates. Visibility alone has no refresh responsibility.

## Loading And Validation Budget

Moving or retaining these lists must not introduce additional runtime validation. Read the inputs required by the action, handle malformed input at its owning boundary, and reuse the resulting loaded state. Do not add destination-existence checks, publication/readiness filtering, freshness scans, hashes, duplicate schema checks or cross-checks against documents and collection manifests. Selection highlighting compares exact targets already in memory; it requires no target read.

Opening, hiding or revealing a panel, following a document link, and clearing Search must not refetch or revalidate the lists. Fetch the chosen document through the existing navigation path when needed; that ordinary document read is separate from list acquisition. Icon selection uses already loaded collection configuration. Keep actual input/cache invalidation under its existing owner, without adding a refresh-on-show policy.

### Current Source Inspection

The following baseline was traced in source on 2026-10-01. It is not a measured browser request trace or a timing/size benchmark.

- Search lazily acquires the complete configured Search index through the generated-data runtime, coalesces an in-flight request, and keeps the payload in browser memory. Queries and More operate on that loaded index; they do not fetch result documents. The same v4 header/schema condition is currently checked in the workspace provider, the Search controller and `collectSearchMatches`, with the query-function check repeated on each query or More render.
- Recent independently acquires the stored recent-document JSON through the same runtime, coalesces an in-flight request, and caches normalized entries. It does not load Search. `normalizeRecentPayload` checks the JSON object, exact top-level keys, `docs_recent_v2`, the docs array, required row values, date format and collection report-host/title fields. Missing required row values are filtered out. The controller then checks the docs array again and calls `normalizeRecentEntries` for another trim/copy/filter pass; rendering sorts and limits the cached rows in memory.
- Local reads use `/docs/search` and `/docs/recent`, selected through the shared cached generated-read capability response. Public reads use their configured static Search and Recent URLs without a local capability probe. Both paths check HTTP success and parse JSON. Local service readers resolve configured Working paths and require an existing file containing valid JSON with an object root; these list endpoints do not rebuild, scan result destinations or read the Index tree to validate membership.
- The explicit management index-reload path currently clears Search and Recent caches. Existing transport retry behavior is tied to the explicit management reload nonce; ordinary list loading does not add that retry mode. These established reload/invalidation paths are distinct from merely switching the Index view.
- Populating either result list does not fetch collection manifests, relationship records or individual result payloads. Following a selected result uses the existing document/report navigation path and any reads already owned by that destination.

The inspected owners are the [generated-data runtime](../../docs-viewer/runtime/js/shared/docs-viewer-generated-data-runtime.js), [workspace provider](../../docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js), [Search controller](../../docs-viewer/runtime/js/shared/docs-viewer-search-controller.js), [Search/Recent functions](../../docs-viewer/runtime/js/shared/docs-viewer-search.js), [payload adapter](../../docs-viewer/runtime/js/shared/docs-viewer-tree-payload-adapter.js), and [local stored-JSON reader](../../docs-viewer/services/docs_generated_reads.py). This list identifies the current read/processing path, rather than freezing the implementation file inventory.

Review the repeated Search schema checks and Recent normalization within the integration step and consolidate work where the same input requirement is already covered by its owning boundary. Retain necessary malformed-input handling without extending the validation contract. The delivery's existing source lint and site-code projection/validation are development checks; this runtime budget does not add test runs, browser probes or benchmarks.

## Implementation Boundary

The shared sidebar owns incremental selection, ancestor expansion and branch toggles across navigation paths. The existing shared view registry and panel layout own the Index view selection and visibility. The Index shell owns its controls and mounted tree/results areas. The Search controller retains query, loading, ranking integration and paging responsibility; route navigation opens documents without resetting the active results view. Existing collection configuration owns icon selection.

The current implementation registers Search and Recent as main-panel views, and both the shared link handler and document opening clear Search. Implementation must move those responsibilities coherently and remove the obsolete main-pane result presentation and automatic Search reset behavior. Preserve the active Index view through document navigation from results, pinned Related links and document content; resetting it belongs to explicit Search clearing or Index-view switching. Do not retain compatibility aliases or duplicate results surfaces.

This is a reader presentation and navigation change. Search corpus, tokenizer, ranking, Recent eligibility, generated payload schemas, document builders, services and publication semantics retain their current owners. [Docs Viewer Search](Docs_Viewer_Search.md) describes the maintained data and query contracts.

## Proposed Delivery Steps

The steps below follow [Development Checklist](Development_Checklist.md) and remain proposed until readiness and implementation are authorized. Update each step's compact record with changed owners, selected evidence, findings and its gate outcome as work proceeds.

### 0 Readiness

- [x] Trace and record current Search/Recent acquisition, cache, normalization and validation behavior from the existing source.
- [ ] Confirm the shared sidebar, selection, route, Index view and management-control owners against this specification.
- [ ] Confirm the two implementation steps form one complete outcome and identify any conflicting navigation or hierarchy behavior before editing.
- [ ] Use the recorded baseline to confirm the delivery adds no list reads or validation passes and identify the bounded consolidation needed in the existing read/processing path.

Gate: a concise read-only review establishes the boundary and implementation order. Stop for an unresolved product decision or a required expansion into data, service or hierarchy redesign; exact file inventories and test architecture are not readiness prerequisites. No executable verification is needed at this step.

Record: source inspection recorded on 2026-10-01. Repeated Search schema checks and Recent normalization were found; production code is unchanged. No endpoint calls, executable tests or benchmarks were run. Remaining readiness items are pending.

### 1 Incremental Sidebar Tracking

- [ ] Replace full tree redraws for ordinary selection, required ancestor expansion and manual branch toggles with targeted updates through the shared sidebar owner.
- [ ] Keep selection and ancestor tracking active when the tree is hidden, preserve unrelated mounted nodes, and defer scrolling until the tree is visible.
- [ ] Retain initial/full-index rendering and the existing structural-update workflows where appropriate.

Gate: ordinary navigation benefits independently of Search, and visible and hidden tracking use the same selection path. Source review confirms that these small operations no longer clear and rebuild the whole tree. Focus, branch behavior and scrolling receive user manual review.

Proposed evidence budget: bounded source/diff review, lint of changed JavaScript and whitespace checks, plus focused manual ordinary-document and collection-host navigation and branch toggling. Static commands should take seconds; manual review takes a few minutes. This addresses selection/branch wiring and preservation of mounted nodes, without authorizing automated test work.

Record: not started.

### 2 Search And Recent Index Views

- [ ] Move controls and results into the Index shell with the agreed two-row Manage layout, compact icon/title rows and results states.
- [ ] Make Search and Recent independent of the displayed document, preserving exact targets, query/history, active-result highlighting, paging and list scroll through result navigation.
- [ ] Preserve independent Index results and pinned Info capture through navigation from either list or document content, including destinations outside the current results and independent clearing/closing.
- [ ] Reuse existing loaded inputs and consolidate overlapping Search schema checks and Recent normalization at their owning boundary, without adding runtime validation, target preflights or refresh-on-show reads.
- [ ] Retain the synchronized tree, gate tree-specific actions in results views, and implement clearing/toggling and the agreed expanded/media availability.
- [ ] Project changed shared/public runtime through the maintained site-code inventory and update durable runtime/search documentation to describe the implemented behavior.

Gate: all completion criteria below are implemented, with no duplicate main-pane result surface, obsolete Search-reset path or compatibility alias. Manual acceptance remains explicit until the user has reviewed the interactions and layout.

Proposed evidence budget: changed-source lint and whitespace checks, bounded route/view/selection review, then the required `bin/site-code-update`, exact tracked runtime projection review, `bin/site-code-update --check` and `bin/site-validate`. Projection and validation cover public asset distribution, not interaction correctness; inspect their current cost before running. User manual review covers pinned ordinary/collection navigation, simultaneous Index results and Related links, an Info-link destination outside the results, independent clearing/closing, document-content navigation, Back/Forward, disabled actions and public narrow-screen access. No Docs/Search rebuild or Publish is required for this runtime change. Any existing automated test selection or test changes need a separately agreed scope under [Testing](Testing.md).

Record: not started.

### 3 Code Review

- [ ] Review the final production, documentation and projected-runtime diff for ownership drift, full-redraw call sites in ordinary tracking, hidden-state resets, coupled Index/Info lifecycles, duplicate selection state, route-target loss, additional reads/validation against the recorded baseline and compatibility residue.
- [ ] Resolve findings within the delivery boundary and rerun only evidence affected by a relevant change.

Gate: no blocking findings remain, and completion claims match the inspected behavior and selected evidence. The bounded review adds no broad test run; record any remaining manual acceptance gaps.

Record: not started.

### 4 Closeout

- [ ] Record user manual acceptance and reconcile the completion criteria with the final implementation and review evidence.
- [ ] Confirm the durable documentation transfer, summarize remaining limits, and present this proposal for retention or retirement.

Gate: the complete outcome and manual acceptance are recorded. Reuse accepted evidence; closeout bookkeeping does not trigger another rebuild or test run. Publish, deployment, commit and push remain separately requested actions, and proposal deletion requires approval.

Record: not started.

## Completion Criteria

- [ ] Search and Recent controls appear in the first Index row, with Manage Index Actions and Position in the second row.
- [ ] Search and Recent results use the shared icon/title row, with no displayed date or collection subtitle.
- [ ] Opening ordinary or collection results changes the main document while retaining the active list, query where applicable, paging and scroll position.
- [ ] Search or Recent results coexist with pinned Related links; navigation from either list or document content preserves both list states under the existing Info/document-mode lifecycle.
- [ ] Opening a target outside the displayed results leaves the results intact with no active row highlighted; matching uses exact document identity.
- [ ] Clearing Search or leaving Recent preserves the pinned Info capture, and closing or replacing the Info capture preserves the Index results.
- [ ] Clearing Search or toggling Recent off reveals the retained tree without an index request, full tree redraw or document reload caused by the view switch.
- [ ] List/view navigation introduces no extra acquisition, revalidation, destination preflight, membership filtering or freshness scan; duplicate input processing is consolidated with necessary malformed-input handling retained at its owner.
- [ ] Ordinary navigation and manual branch toggles update the affected sidebar nodes without rebuilding unrelated rows.
- [ ] After opening B from results initiated while A was displayed, the hidden Index already tracks B; leaving results keeps B displayed and reveals its selection without reopening A or running a separate catch-up pass.
- [ ] Existing expanded branches are preserved, the current target's ancestors follow navigation, and scrolling occurs only when needed while the tree is visible under existing ordinary-document and collection-host tracking rules.
- [ ] Back and Forward preserve the intended document and Index view behavior.
- [ ] Tree-specific management controls remain disabled in results views, and normal document capabilities remain available.
- [ ] Expanded and media views require no Search or Recent entry point.
- [ ] Manual review accepts compact rows, panel scrolling and public narrow-screen access to the document.

Test authoring, changes or non-trivial test runs require their separately agreed scope under [Testing](Testing.md). This documentation update does not authorize implementation or test work.
