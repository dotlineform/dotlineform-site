---
draft: false
doc_id: d-20261003-111241-1a513e
title: Document View And Return Navigation - Delivery
added_date: "2026-10-03 11:12:41"
last_updated: "2026-10-03 11:44:42"
summary: Replace ordinary and collection detail readers with one document view, browser-history return, an independent Index and committed-change notifications to retained caller lists.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Document View And Return Navigation - Delivery

## Current And Next State

Proposed delivery under [Planned Features](Planned_Features.md). The agreed direction is one document view that can open from any document link. Its Back button uses browser history to return to the calling view, and the Index does not follow the opened document to its owning collection. Collection identity stays in collection-document URLs to select the exact storage owner. Completed Save/Delete operations notify affected retained caller lists, which reconcile their own records without scanning on Back.

This document explains the current implementation and the changes needed to move to that model. The user accepted the approaches below on 2026-10-03 and requested that the proposal and delivery steps incorporate them. That authorizes this specification update, not runtime implementation. The next step is read-only readiness to confirm the complete implementation slice, affected route references, report projection inputs and proportionate verification boundary. No runtime, Working source documents, generated payloads or publication state have been changed for this proposal.

Current behavior was established by focused source inspection on 2026-10-03, including the Projects source and its report/link owners. It has not been verified through browser interaction in this delivery. [Runtime](Docs_Viewer_Runtime.md) and [Collection Report Architecture](Sub_Scope_Index_Architecture.md) remain the maintained descriptions of the shipped implementation until a replacement ships.

## Concept

A collection defines storage and membership; a report presents a set of documents; the shared doc view opens an exact document.

A manifest list is the simplest report. Projects, Context, Search and Recent differ in their selection, joins, metadata, grouping and controls. They all use the same document-opening behavior and retain their own state for return.

The report supplies the **calling view**, rather than becoming the document’s parent. Document actions come from the document’s identity and supported collection capabilities, independently of which report led to it.

## Requirements

Deliver one observable outcome: a document link opens the same document view regardless of where the document is stored or where the link appears; Back restores the calling view and its position without redirecting the Index to a collection host.

### How Document Viewing Works Now

The reader has a shared application shell, an Index panel and a main pane. Main-pane views and document display modes are separate: the normal `rendered-document` view displays a document, Content Detail presents media, tables, diagrams or an expanded report, and Manage's `markdown-source` mode edits the active document. The current problem is the separate ownership of ordinary document display and collection detail display, rather than the existence of those supported presentations.

| concern | ordinary document | named-collection document |
| --- | --- | --- |
| Identity in the URL | `doc=<document-id>` selects the document. | `doc=<report-host-id>&subdoc=<document-id>` selects the ordinary host first and a child inside its report. Collection ownership is resolved from the configured host. |
| Loading and rendering | The route workflow loads an Index record through the collection provider, caches its payload by ordinary document ID, and passes it to the document controller. | The route workflow loads the host document. Its `docs_collection` report creates its own detail shell and reads the collection's by-ID payload. |
| List dependency | Ordinary navigation uses the loaded ordinary document model. | Direct detail loading for collections other than Catalogue first loads the collection manifest and checks membership. Catalogue has a direct five-digit Work-ID path that reads its by-ID document without first loading its manifest. |
| Displayed state | Selected and displayed document IDs identify the ordinary document. | The application keeps the ordinary host selected/displayed while the report separately publishes the exact validated child target and metadata. |
| Document actions | Actions resolve from the ordinary loaded document. | Edit, source opening and detail actions consume the report's validated child context. Collection selection and list actions have their own context. |
| Toolbar Back | Ordinary document links have no general caller-return control. Browser Back uses route history. | The shared toolbar delegates Back to the report's `returnToList` callback. It returns to that collection's list, regardless of where the document link was followed. |
| Index tracking | Navigation updates the tree marker, expands the selected document's ancestors and scrolls the visible row when needed. | Navigation tracks the ordinary collection host, so a link followed from another document can select Context or another collection in the Index. |

For the reported example, [Projects](/docs/?doc=d-20260805-155400-4c341f) contains the `project_state` report. Its document rows carry exact Works collection/document targets, but their hrefs are constructed through the configured [Context](/docs/?doc=d-20260801-073826-8865a8) host. A row therefore opens a route of this shape:

```text
/docs/?doc=d-20260801-073826-8865a8&subdoc=<linked-document-id>
```

The opened child is rendered by Context's collection report. Its toolbar Back means “Back to all …” and reveals that report's list. Projects is no longer the mounted caller. Loading Projects again through browser Back remounts its report; that path does not retain its previous filter, sort and report rows.

The current collection reader already retains its own mounted list while opening a detail from a list row. Its toolbar Back can restore the list's query, sort, page, selection, scroll and invocation focus. That useful retention is confined to the collection report; it is not a shared return mechanism for Projects, another document, Search, Recent or Content Detail.

Browser route history currently records the ordinary document ID, heading hash, Search query, report parameters and active Index view. It does not record a general calling main view or a restorable hosted presentation. Content Detail has a separate Back lifecycle that returns to the retained document and restores its position. Following a document link from that presentation goes through the document router rather than recording the presentation as a general return destination.

### Current Owners

| owner | current responsibility and relevant coupling |
| --- | --- |
| [Route workflow](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js) and [router](../../docs-viewer/runtime/js/shared/docs-viewer-router.js) | Intercept eligible same-route anchors, write document/report history, load ordinary documents and apply browser Back/Forward. Document loading also invokes Index selection tracking. |
| [Document controller](../../docs-viewer/runtime/js/shared/docs-viewer-document-controller.js) | Mount ordinary payloads and their extras; forward collection report context only for the current mount. Navigation releases the previous content adapters and replaces the content. |
| [Collection reader](../../docs-viewer/runtime/js/shared/docs-collection-report.js) | Own collection manifests, list/filter/page state, `subdoc` URL changes, detail reads/rendering, validated child action context, refresh and return to list. |
| [Document-view coordinator](../../docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js) and [Content Detail](../../docs-viewer/runtime/js/shared/docs-viewer-content-detail-view.js) | Coordinate document modes, hosted presentations, their Back lifecycle and Info capture. These are distinct from collection detail navigation. |
| [Application session](../../docs-viewer/runtime/js/shared/docs-viewer-app-session.js) and [sidebar](../../docs-viewer/runtime/js/shared/docs-viewer-sidebar.js) | Store selected/displayed document state and derive tree tracking from that selection. The displayed target and Index browsing position do not have independent selection owners. |
| [Document locations](../../docs-viewer/services/docs_document_location.py), builders and link consumers | Encode collection documents through report hosts and `subdoc`; authoring targets, generated related links, report rows and Search/Recent navigation consume that route model. |

These are ownership references for the proposal, not a frozen implementation file inventory. The shared application runtime currently assembles the two kinds of action context and renders the collection Back control. The refactor should move responsibility into focused navigation/document owners, leaving that runtime responsible for composition.

### Target Viewing Model

One document view accepts an exact document target and a calling-view reference. All supported entry points use it: ordinary Index links, collection rows, Projects and other report rows, Search, Recent, related links, authored document links and document links inside supported Content Detail presentations. Direct URLs and links opened in another tab use the same reader, with no invented in-app caller.

The same document renderer handles ordinary and named-collection documents. Collections retain their browsing lists, filters, sorting, paging, row selection and collection-wide operations. A list opens the document view instead of owning a second reader inside its report. An ordinary document hosting a report remains an ordinary document; this change does not require replacing every report with a new top-level view.

Keep three responsibilities explicit:

- **Document target:** the exact ordinary `{doc_id}` or named `{collection, doc_id}` identity, loaded payload and supported action context. Collection IDs and document IDs remain immutable; titles and report hosts are not substitutes for the displayed target.
- **Calling view:** the presentation to restore on Back, including the state needed to resume it. It can be a document, collection list, report presentation or Index results context. It is navigation state, not document metadata or collection membership.
- **Index browsing state:** the current Index view, explicit selection, tree expansion, query, result position and scroll. Opening a document does not automatically select or reveal its owning collection. An explicit Index interaction may update the Index's own selection.

Back follows the actual call chain through browser history. Projects → Doc A returns to Projects; Context list → Doc A returns to that list; Doc A → Doc B returns to Doc A, whose own Back can then return to its caller. Caller-specific filters, sorting, pagination, selection and reading position remain available. Restore invocation focus when the corresponding control still exists. Hide toolbar Back when there is no known restorable in-app caller; an unrelated page in browser history is not sufficient.

Document links with a heading fragment open the requested heading. A link to another heading in the already displayed document remains in-document navigation without creating a second document instance merely to scroll. Readiness confirms how those fragment entries interact with caller Back. Preserve normal modified-click, new-tab, download and external-link behavior.

### Changes Needed

| boundary | required change for the new model |
| --- | --- |
| Document navigation | Introduce one open-document operation and one Back owner. Route all document entry points through it, carrying exact identity and caller state. Remove the collection-specific detail-opening and return policy once replaced. |
| Document reads | Let the provider resolve the exact ordinary or collection by-ID payload directly. A direct document read must not fetch the full collection manifest merely to discover its location or permit display. Validate the requested payload and configured owner through the existing local/public boundaries. |
| Document rendering | Use the document controller for both ordinary and collection documents, with the same related links, media, diagrams, reports, title and loading/error presentation. Remove duplicate collection detail shells and payload caches when their responsibilities have moved. |
| Collection browsing | Retain each list's state under its list owner. Supply exact document targets and the caller reference to navigation. Keep list refresh and selection actions independent of the document view. |
| Return and browser history | Use browser history as the navigation chain and small per-entry view state for restoration. Opening a document or hosted presentation adds a navigation entry; filter/sort/control adjustments update the current entry. Hide toolbar Back without a known in-app caller. Do not duplicate the chain through `from` query parameters or an independent return stack. |
| Index | Separate Index selection from the active document target. Remove automatic host selection, ancestor expansion and scroll caused by document navigation; retain deliberate Index navigation and actual hierarchy/source updates. Search and Recent keep their query/order/paging rather than becoming collection navigation. |
| Document actions | Resolve Edit, Open in VS Code, Copy Link, Draft/Ready and supported collection-specific document actions from the unified validated document target. Preserve collection-specific metadata projection and action availability without requiring a mounted collection detail. |
| Source and refresh | Capture the exact document target for Source. Preserve dirty/discard behavior and Save's existing source-persistence boundary. Refresh the active generated document through the common reader. Source Save returns committed list metadata and the viewer forwards it to affected retained list owners. An Index refresh must not redirect an independently displayed document to its host. |
| Retained list updates | Let each report/list reconcile committed updates and deletions in its own model, reapplying its filter/sort/grouping in memory. Preserve query, selection and position. Save does not manipulate another report's DOM; Back does not discover changes by scanning sources, rereading every manifest or rerunning Projects. |
| Missing or deleted targets | Show the requested document's failure without loading a host as a substitute. Retain a usable caller return where available. After a committed deletion, follow the agreed return policy and reconcile list/Index state without using their selected record as a document-action fallback. |
| Link production and parsing | Replace host-plus-`subdoc` document routes with `collection` plus exact `doc`, omitting `collection` for ordinary documents. Make URL construction, generated links, source insertion, report rows, Search/Recent links, Copy Link, link analysis and export/package rewriting agree. Complete an explicit cutover of affected references and generated outputs without aliases. |
| Public and Review boundaries | Public uses published by-ID data and gains no local services or write handles. Review continues to read only its selected package through its provider; shared navigation changes must preserve that authority and its package context. |

### Agreed Route And Cutover

Use `/docs/?collection=<collection>&doc=<document-id>` for named-collection documents and `/docs/?doc=<document-id>` for ordinary documents, with the configured public or package route used by its owning reader. Query-parameter order has no semantic meaning. `collection` selects the configured by-ID storage and supported actions; it does not select a collection view or move the Index. Even a globally unique document ID does not identify its storage directory. Keep that owner explicit rather than introducing a global location registry, collection scan or new shared storage arrangement.

Caller state belongs to browser history and retained page-session view state. Do not add `?from=<doc_id>`: it would duplicate navigation history while omitting the calling presentation, filter/scroll state, collection identity and earlier call chain. Copy Link identifies the destination document independently of the caller.

Retire host-plus-`subdoc` document routes as part of this delivery. Update their active producers and inspect the actual authored/saved references that require conversion. Generated rendered links need regeneration through their owning builders; canonical Markdown links need explicit source edits where affected. Do not add compatibility aliases or automatic collection inference as an end state. Existing external bookmarks require replacement where they use the retired form. Readiness identifies and agrees the bounded source/generated-output cutover before implementation writes or rebuilds.

No source storage move or document-ID migration is needed for the viewing model. Collection report hosts still have a valid role as browse entry points, and publication eligibility still belongs to the existing workspace policy. Distinguish those responsibilities from a document's loading route. Do not weaken inherited draft/unpublishable exclusions or change Search membership simply because host routing changes.

### Agreed Return And History Policy

Browser history provides the navigation chain. A unique document URL identifies a destination; navigating to it creates the history entry that makes Back possible. The viewer must still restore the calling presentation and its state. Use small restoration records alongside history entries, reusing retained page-session data where needed; do not store full report payloads or DOM nodes in history state. [Browser Back](https://developer.mozilla.org/en-US/docs/Web/API/History/back) and [history state](https://developer.mozilla.org/en-US/docs/Web/API/History/pushState) describe the browser mechanism.

Opening another document or supported hosted presentation adds a navigation entry. Typing Search, changing sort/filter/group/page and switching Index controls update the current entry's state rather than adding steps through individual control adjustments. Toolbar Back and browser Back/Forward use that same navigation chain, with the existing Source discard gate respected before leaving. Returning reveals the completed calling view directly without an intermediate collection or underlying-document display.

Show toolbar Back only for a known restorable in-app caller. Direct URLs, new tabs, external callers and a refreshed session without such a caller leave it hidden. Do not infer a caller from `history.length`, an owning collection or a document ID alone. Browser-native Back remains under the browser's normal control.

Preserve only the state needed to resume the caller: its exact view/document/presentation identity, relevant list controls, selection, scroll and invocation focus. Keep retention within the page session and existing view/data owners. No persistent/offline cache, expiry framework or independent application history stack is required.

### Current Index Actions And Agreed Change Policy

The following behavior was checked against the current route, sidebar, Search/Recent and management owners during the decision review. Most actions retain their meaning; document navigation stops driving tree selection implicitly.

| current action | current selection/display effect | target policy |
| --- | --- | --- |
| Click a tree document title | Opens it, marks its row, expands ancestors and scrolls the row into view when needed. | Retain explicit row selection/opening and deliberate tree positioning. |
| Expand/collapse a branch | Changes expansion only. | Retain. |
| Open/dismiss a row context menu | Temporarily outlines its target and preserves displayed-document selection. | Retain independent captured row targeting. |
| Copy Link, Open, Open in VS Code, Export, Prepare package | Preserve viewer selection; Open launches the source through its default application. | Retain. |
| Double-click a tree row | Enters Source for the selected ordinary document, normally opened by the first click. | Use the explicit clicked-row target after Index and document state separate. |
| New Sibling/New Child | Creates, selects and opens the new document in Source; resets Search/Recent to the tree. | Retain the deliberate creation result and reconcile the new Index entry. |
| Position | Refreshes the hierarchy while preserving the displayed document. | Retain actual hierarchy reconciliation without making the document target own Index selection. |
| Delete | Preserves a surviving displayed document; otherwise opens a remaining root document. | Preserve an unrelated displayed document. When the displayed document is deleted, return to its known caller; apply the explicit existing no-caller destination policy rather than inventing a collection caller. |
| Type/clear Search or toggle Recent | Changes Index view/query and history while preserving the displayed document. | Preserve independent Index controls; update the current history entry for control adjustments. |
| Click a Search/Recent result | Opens it and updates tree tracking; collection results select their host. | Open the exact document and mark the relevant result, retaining the tree's existing selection/expansion/scroll. |
| Follow a document link outside the Index | Updates tree tracking through the same navigation path. | Open the exact document without moving tree selection, expansion or scroll. |

Initial direct loading must not select a collection host to represent a displayed collection document. Readiness confirms the minimal initial Index state and how a deleted Index-selected row is cleared or replaced independently of the current main-pane document. Actual hierarchy and metadata updates remain supported; independence does not freeze an obsolete tree.

### Committed Changes Update Retained Callers

A caller need not scan for changes on return. The operation that commits a change already knows the exact target and its resulting metadata. Its successful completion supplies that information, and the shared viewer forwards it to affected retained report/list owners. Each owner updates its own model and presentation rather than allowing Source Save to manipulate another report's DOM.

For full Source Save, extend the successful response with a normalized committed document summary produced from the metadata already parsed and validated during that write. Include the exact target and the fields needed by supported list projections, such as title, dates, readiness and relevant metadata/Subject. Settle exact response fields through the existing metadata projection owners during implementation; do not reread or scan sources to manufacture the response. Cancelled or failed writes send no committed-change notification.

For a successful Delete, supply the confirmed deleted targets, including any descendants removed by that operation. Retained list owners remove those entries and reconcile selection/page bounds. Create and Import keep their existing explicit completion owners and forward their known affected records or targets where they change a retained caller. Do not require a fresh complete scan merely to return after those operations.

The collection reader already projects confirmed readiness changes and deletions into its retained model without fetching the manifest. Generalize that responsibility through the unified reader/list boundary rather than retaining collection-detail-only callbacks. Reapply filtering, sorting, grouping and pagination over retained in-memory data only where the committed change affects them. Preserve caller controls and reading position; a changed filter match, sort key or group can legitimately move or remove the affected row.

For Projects, a title change updates its document label. A Subject change may move the document between folder or Series groups and must be projected against retained folder/Catalogue inputs. Body changes do not require report recomputation unless that report explicitly derives displayed data from the body. Readiness confirms that the necessary projection inputs are retained; do not silently rerun the complete Project State folder scan or report on Save or Back.

Save still succeeds at canonical source persistence. Its committed metadata notification does not imply that generated HTML is ready and does not await the watcher or rebuild Search. A caller projection failure is reported separately and cannot reverse the source write or make an already successful Save fail. Rendered-content freshness remains with the existing watcher and active-document refresh path. Edits made in VS Code continue through that path because there is no viewer Save completion to notify callers directly. Explicit report Run/Refresh remains available for its own inputs and recovery.

### Remaining Readiness Checks

- Confirm fragment-navigation history behavior, Source cancellation during browser navigation and restoration after refresh against the agreed caller policy.
- Confirm minimal initial Index state, deletion of its selected row and exact row targeting for Source while the displayed document differs.
- Identify the actual route producers and authored/saved references for the accepted URL cutover; agree any required Working source edits and generated reconciliation before writes.
- Confirm the smallest committed summary shared by Save and retained list owners, and Projects' retained inputs for Subject/group changes. Stop if a new workspace scan or broader report-data redesign is required.
- Confirm Create/Import completion integration and treatment of unavailable/deleted callers using existing failure owners, without a new recovery framework.
- Important: this is a synchronous workflow. It should be assumed without validation that callers still exist and have not been edited whilst a linked doc is open, regardless of whether it has been opened in a new tab.

## Deliverables

- [ ] One document-view/navigation owner for exact ordinary and named-collection targets across supported link entry points.
- [ ] Browser-history caller return with small per-view restoration state, coherent Back/Forward and hidden toolbar Back when no in-app caller exists; no `from` query or separate return stack.
- [ ] Independent Index selection and browsing state, with explicit user navigation retained.
- [ ] Collection lists that open the common reader, with duplicate detail-rendering/navigation responsibilities retired.
- [ ] Unified document actions, Source capture and active-document refresh with existing public, Manage and package authority preserved.
- [ ] Committed Save/Delete notifications to retained caller lists, including metadata/Subject regrouping and confirmed deletions, with list-owned reconciliation and no discovery scan on Back.
- [ ] Direct ordinary `doc` and named `collection`/`doc` URLs, with explicit producer/reference/generated-output cutover and retirement of host-plus-`subdoc` document routes without aliases.
- [ ] Selected static evidence, manual interaction review, distinct code review and transfer of shipped behavior to durable documentation.

## Process

1. Open Projects and choose its grouping, filter, sort and reading position.
2. Follow a document link. The single document view reads the exact target through its `collection`/`doc` URL and adds a browser-history entry. Projects remains the calling view; the Index keeps its own browsing state.
3. Read or use the document's supported actions. Opening another document adds the next history entry. Filter/sort/control adjustments update the current entry rather than creating extra Back steps.
4. Save a title or relevant metadata change. After source persistence, the viewer passes the committed summary to Projects, which updates that record and any affected grouping/filter/order in memory. A confirmed Delete removes its exact affected entries. Source Save does not wait for generated rendering.
5. Use toolbar Back or browser Back. Restore Projects or another caller through history with its controls and reading position preserved. Returning does not scan sources, reread an unchanged collection list or rerun Projects.
6. Open the same document from a collection list, Search, Recent, another document or Content Detail. The reader and document actions are the same; each caller owns its retained presentation and applicable list updates.
7. Open a direct URL or a new tab without a known in-app caller. Use the same document reader with toolbar Back hidden. Copy Link identifies only the document target.

## Delivery Steps

### DVR-0 — Readiness

- [ ] Confirm the requested model against the current navigation, collection, action, Index and provider owners.
- [ ] Confirm the accepted browser-history model, small restoration records, control-entry updates and hidden no-caller Back; settle the remaining fragment/refresh/Source edge cases.
- [ ] Confirm explicit Index action targeting and initial/deleted-selection behavior while its state is independent of the document.
- [ ] Identify the affected references and agree the source/generated-output boundary for direct `collection`/`doc` routes and host-plus-`subdoc` retirement, including external bookmark effects.
- [ ] Confirm committed Save/Delete summaries and the retained data needed for caller list reconciliation, particularly Projects Subject/group changes; stop for a required full scan or unapproved report redesign.
- [ ] Reconcile overlap with the existing proposals below and choose the current durable owner for shipped navigation behavior.
- [ ] Agree a proportionate verification budget. Stop if the result requires an unapproved source migration, a change of package/public authority or a broader Catalogue/caching redesign.

Verification budget: focused read-only owner inspection and bounded proposal review. No tests, prototypes, builds, source migrations or publication in readiness.

Record: proposed. Current ownership, Index action effects and the existing committed readiness/deletion callbacks have been inspected. The user accepted the history, route, caller-notification and Index direction on 2026-10-03. Remaining readiness checks and runtime implementation approval are outstanding.

Gate: accept the resolved specification and authorize implementation before runtime or generated-output edits.

### DVR-1 — Exact-Target Document Reader And Route Cutover

- [ ] Introduce the common exact-target reader and action context through focused owners.
- [ ] Load ordinary and collection by-ID payloads through their configured providers without a full manifest read merely to open a document.
- [ ] Move collection detail rendering into the common document view while retaining list browsing and its supported customisations.
- [ ] Resolve document actions, Source capture and active generated-document refresh from the exact target rather than the selected Index row or a mounted collection detail.
- [ ] Change supported document-link producers and consumers to ordinary `doc` or named `collection`/`doc`, preserving public route and Review package context.
- [ ] Complete the approved authored/saved-reference cutover and remove host-plus-`subdoc` document routing and duplicate detail responsibilities without aliases.
- [ ] Reconcile affected generated output only where the changed builder or link contract requires it. Search rebuild, Publish, deployment, commit and push remain separately authorized actions.
- [ ] Preserve related-links capture, supported Content Detail adapters and local/public/package authority through the reader change.

Verification budget: choose exact changed-file lint/syntax and direct existing diagnostics after the implementation owners are known, addressing exact target reads/actions, route agreement and public/package isolation. For represented shared/public code, run `bin/site-code-update`, inspect the tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`. Apply the same projection requirement to subsequent runtime steps. Select any existing tests only after inspecting their coverage and agreeing execution scope; creating or changing tests, fixtures, harnesses or profile membership requires a separate approved specification under [Test Contract Discipline](Test_Contract_Discipline.md). Record exact evidence, costs, side effects and limits; no automatic suites or browser click scripts.

Manual review gate: the same document opens with correct content/actions from a direct URL and each agreed link entry point; collection membership changes neither the reader nor action target. Missing targets show an error without substituting the host. Route cutover is complete within the approved boundary. These are acceptance cases, not evidence already obtained.

Record: not started.

Gate: one exact-target document reader and route contract replace both old reader paths; the delivery remains active until caller return and mutation reconciliation also work.

### DVR-2 — Browser History, Caller Restoration And Independent Index

- [ ] Record document/hosted-view navigation through browser history with small per-entry restoration state; do not add `from` queries or a second history stack.
- [ ] Update the current history entry for Search/Recent and other filter/sort/group/page control adjustments.
- [ ] Restore document, list, report/results and supported Content Detail callers directly, with controls, selection, scroll and invocation focus retained.
- [ ] Make toolbar Back and browser Back/Forward use the same call chain; hide toolbar Back without a known restorable in-app caller.
- [ ] Separate Index selection from the active document and retain the explicit action behavior above, including clicked-row Source targeting.
- [ ] Remove automatic collection-host selection, ancestor expansion and tree scrolling from document links outside the tree; retain relevant Search/Recent result marking.
- [ ] Complete the agreed direct-load, fragment, refresh, deleted-caller and Source discard behavior without navigation-time scans or speculative freshness checks.

Verification budget: changed-file diagnostics and bounded state/route review for caller identity, history-entry ordering, explicit Index targets and Source cancellation. Manual interaction review owns return state and focus/scroll presentation. Reuse sufficient evidence from DVR-1; add tests only under separately approved scope.

Manual review gate: Projects → Doc → Back restores its filter/sort/position; collection list → Doc → Back restores its list; Doc A → Doc B returns through the call chain; Search/Recent and Content Detail callers return correctly. Control adjustments do not introduce extra Back steps, the Index stays in place, and direct/new-tab openings without a caller hide toolbar Back. Browser Back/Forward and cancelled Source navigation preserve the intended view.

Record: not started.

Gate: caller return is coherent through the one navigation owner and independent Index state; no collection fallback, duplicate chain or intermediate wrong view remains.

### DVR-3 — Committed Changes And Retained List Reconciliation

- [ ] Extend full Source Save's successful result with an exact-target committed list summary from the metadata already validated during persistence, without another source read/scan.
- [ ] Forward completed Save/readiness/Delete changes to affected retained list owners; retain confirmed deleted targets and descendants where applicable.
- [ ] Keep each report/list responsible for its model and rendering; Source Save must not edit another report's DOM directly.
- [ ] Reconcile affected records and filter/order/group/page projections in memory while preserving controls, selection and reading position.
- [ ] Update Projects title labels and Subject-based folder/Series placement from retained report inputs without rerunning its full scan.
- [ ] Integrate known Create/Import results through their existing completion owners where retained callers are affected.
- [ ] Notify only committed changes. Preserve source-persistence Save completion and report projection failures separately from the saved source; retain watcher/active-generated refresh for rendered content and VS Code edits.
- [ ] Remove return-time change-discovery scans or unconditional report/list reloads introduced by the old ownership split. Preserve explicit owning Run/Refresh and recovery actions.

Verification budget: focused service/module diagnostics and bounded response/list-owner review for exact identity, committed metadata, deletion scope and source/generated completion separation. Inspect the relevant existing readiness/deletion patterns before reusing them. Any tests or live mutation checks require separately agreed scope and effects; do not write temporary regression scripts or mutate real sources merely for documentation evidence.

Manual review gate: edit a linked document's title, readiness and relevant Subject, then return to the caller with the changed row/group and retained controls. Delete an entry and verify its removal and page/selection reconciliation. A body-only edit does not recompute unrelated report data. Failed/cancelled writes produce no successful update; a caller projection failure does not undo Save. Returning adds no workspace scan, unchanged manifest fetch or automatic Projects Run/Refresh.

Record: not started.

Gate: retained callers reflect notified committed changes through their own owners, and Back only restores the view. All three implementation steps are required for the complete delivery.

### DVR-4 — Code Review

- [ ] Review the bounded final change for duplicate readers, hidden collection-host routing, Index coupling, wrong action targets, compatibility residue and public/package authority leaks.
- [ ] Review history/control entry ownership and exact caller restoration, including Source cancellation and deleted callers.
- [ ] Review committed summaries and list notifications for identity agreement, report-owned projection, hidden scans and source/generated completion coupling.
- [ ] Confirm failure and return handling against the agreed specification without treating a list projection failure as a failed persisted Save.
- [ ] Resolve findings within scope and repeat only evidence affected by review changes.

Verification budget: bounded production/config/generated diff review and targeted follow-up diagnostics justified by findings.

Record: not started.

Gate: findings resolved and completion claims match the inspected surfaces and actual evidence.

### DVR-5 — Closeout

- [ ] Transfer the shipped viewing, browser-history return, Index, direct-route and committed-list-update model into Runtime and the collection architecture owner, or a focused durable navigation document if that is clearer.
- [ ] Record user manual confirmation, exact selected evidence and remaining material limitations.
- [ ] Reconcile affected older proposals without claiming their wider caching, Catalogue or previous/next work is delivered.
- [ ] Present a retain-or-retire recommendation for this delivery. Document deletion and Git/publication actions remain explicit.

Verification budget: documentation and scoped closeout review; no repeated builds or tests without a new reason.

Record: not started.

Gate: the agreed complete result is delivered and its durable documentation is current.

## Follow-on And Related Proposals

[View Caching and History - Delivery](View_Caching_And_History_Delivery.md) overlaps caller restoration and browser history, but its current specification still references the removed Links view and retired scope/stage identities. It is not a current runtime contract or an automatic prerequisite. Reconcile the overlapping navigation responsibility before implementation; page-session caching for all media/resources and changes to HTTP freshness are separate decisions. Preserve the implemented Working watcher/refresh behavior unless a specific replacement is agreed.

[Subject Associations Retirement - Delivery](Subject_Associations_Retirement_Delivery.md) separately proposes retiring Catalogue documents and opening direct Work detail reports. This document describes Catalogue's currently registered document reader. If that retirement ships first, a Work detail is a report caller/target under its own owner, not a document to recreate through this refactor. Resolve the order and intersecting navigation contracts at readiness without absorbing Catalogue retirement into this delivery.

[Doc Navigation](Doc_Navigation.md) and [Context Navigation](Document_Context_Navigation.md) concern saved hierarchy ordering and proposed previous/next traversal. Caller Back does not define that sequence. Native app navigation, cross-application return protocols, persistent/offline caching and general report redesign remain separate work.
