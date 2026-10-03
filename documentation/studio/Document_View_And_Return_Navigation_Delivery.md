---
draft: false
doc_id: d-20261003-111241-1a513e
title: Document View And Return Navigation - Delivery
added_date: "2026-10-03 11:12:41"
last_updated: "2026-10-03 19:19:18"
summary: Completed exact document reader, independent Index, committed list updates and two retained views with one immediate caller return.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Document View And Return Navigation - Delivery

## Current And Next State

DVR-0–6 are complete, accepted and closed on 2026-10-03 under [Planned Features](Planned_Features.md). The user reopened the original delivery for DVR-6, then accepted the follow-on and authorized closeout with “great, ok to close”. Retain only the current document/report and one immediate caller, consume that caller on Back, and keep Media View inside its document without a history slot. This replaces the unrestricted retained call chain delivered by DVR-2. The exact reader, independent Index, committed list updates and completed Working cutover remain delivered.

The user previously confirmed general navigation, opening Source editor, changing a title and the list updating. DVR-6 implementation, bounded lifecycle review and static checks are complete; user acceptance closes the follow-on without claiming individually confirmed results for every manual scenario. Further testing continues during normal work. [Temporary handoff](Document_View_And_Return_Navigation_Handoff.md) preserves changed boundaries, commands and limits; both records are ready for manual archive. Tests, Search rebuild, Publish, deployment, commit and push were not performed for this follow-on.

The baseline below records the readiness finding, rather than the replacement's current ownership. [Runtime](Docs_Viewer_Runtime.md) and [Collection Report Architecture](Sub_Scope_Index_Architecture.md) describe the implemented model. User manual evidence is limited to the confirmed checks above; detailed failure, cancellation, Delete/Import and public/Review cases were not individually confirmed. The existing Preview/public data still uses its previous prepared contract; the new runtime, browser configuration and regenerated links must be published together through a separately authorized Publish before public release. Implementation closeout does not authorize or claim that release.

## Concept

A collection defines storage and membership; a report presents a set of documents; the shared doc view opens an exact document.

A manifest list is the simplest report. Projects, Context, Search and Recent differ in their selection, joins, metadata, grouping and controls. They all use the same document-opening behavior and retain their own state for return.

The report supplies the **calling view**, rather than becoming the document’s parent. Document actions come from the document’s identity and supported collection capabilities, independently of which report led to it.

## Requirements

Deliver one observable outcome: a document link opens the same document view regardless of where the document is stored or where the link appears; Back restores the calling view and its position without redirecting the Index to a collection host.

### Viewing Baseline At Readiness

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

### Baseline Owners At Readiness

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

Under the DVR-6 follow-on, Back restores only the immediate caller and consumes that return context. Projects → Doc A returns to Projects; Context list → Doc A returns to that retained list; list → Doc A → Doc B releases the list and Back restores Doc A without an earlier toolbar Back. Caller-specific filters, sorting, pagination, selection and reading position remain available within that retained pair. Restore invocation focus when the corresponding control still exists. Hide toolbar Back when there is no retained caller; an unrelated page in browser history is not sufficient.

Document links with a heading fragment open the requested heading. A link to another heading in the already displayed document remains in-document navigation without creating a second document instance merely to scroll. The proposed fragment/history policy is recorded in the readiness decisions below. Preserve normal modified-click, new-tab, download and external-link behavior.

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

### Original Return And History Policy — Superseded By DVR-6

This section records the unrestricted call-chain policy accepted for DVR-0–5. DVR-6 replaces its retention and Content Detail participation with two document/report views and one consumable caller return; Runtime describes the current behavior.

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

Initial direct loading must not select a collection host to represent a displayed collection document. The proposed initial and deleted-selection policy is recorded in the readiness decisions below. Actual hierarchy and metadata updates remain supported; independence does not freeze an obsolete tree.

### Committed Changes Update Retained Callers

A caller need not scan for changes on return. The operation that commits a change already knows the exact target and its resulting metadata. Its successful completion supplies that information, and the shared viewer forwards it to affected retained report/list owners. Each owner updates its own model and presentation rather than allowing Source Save to manipulate another report's DOM.

For full Source Save, extend the successful response with a normalized committed document summary produced from the metadata already parsed and validated during that write. Include the exact target and the fields needed by supported list projections, such as title, dates, readiness and relevant metadata/Subject. Settle exact response fields through the existing metadata projection owners during implementation; do not reread or scan sources to manufacture the response. Cancelled or failed writes send no committed-change notification.

For a successful Delete, supply the confirmed deleted targets, including any descendants removed by that operation. Retained list owners remove those entries and reconcile selection/page bounds. Create and Import keep their existing explicit completion owners and forward their known affected records or targets where they change a retained caller. Do not require a fresh complete scan merely to return after those operations.

The collection reader already projects confirmed readiness changes and deletions into its retained model without fetching the manifest. Generalize that responsibility through the unified reader/list boundary rather than retaining collection-detail-only callbacks. Reapply filtering, sorting, grouping and pagination over retained in-memory data only where the committed change affects them. Preserve caller controls and reading position; a changed filter match, sort key or group can legitimately move or remove the affected row.

For Projects, a title change updates its document label. A Subject change may move the document between folder or Series groups and must be projected against retained folder/Catalogue inputs. Body changes do not require report recomputation unless that report explicitly derives displayed data from the body. The current response contains the required placement inputs, but its browser normalizer discards Work membership and some Series membership data. Retain that supplied data in the report owner during implementation; do not silently rerun the complete Project State folder scan or report on Save or Back.

Save still succeeds at canonical source persistence. Its committed metadata notification does not imply that generated HTML is ready and does not await the watcher or rebuild Search. A caller projection failure is reported separately and cannot reverse the source write or make an already successful Save fail. Rendered-content freshness remains with the existing watcher and active-document refresh path. Edits made in VS Code continue through that path because there is no viewer Save completion to notify callers directly. Explicit report Run/Refresh remains available for its own inputs and recovery.

### Accepted Readiness Decisions

The current provider, generated-read and configured by-ID boundaries can support the common reader without a storage move, global document registry or manifest prerequisite. The document/navigation owners take responsibility for exact loading, rendering, history and action context; the collection report retains browsing and collection operations. Page-session retention must cover report/list models and supported presentations as well as document payloads, because the current document mount releases adapters and replaces its content. History records carry identity, a session view reference and small restoration values; retained data and presentation handles stay with their owners.

- **Fragments and refresh:** a different document, including a heading destination, adds one entry. Another heading in the displayed document updates that entry's hash and reading position without adding a caller Back step. Refresh creates a new page session, loads the URL's exact target and clears unavailable caller/presentation references; toolbar Back stays hidden until a new in-app caller exists. Browser-native navigation and modified/new-tab links keep their normal behavior.
- **Source cancellation:** use the existing dirty/discard gate before a viewer navigation commits. On browser Back/Forward, retain the editor until the gate resolves; cancellation traverses back to the previously active entry without pushing a replacement entry or discarding the buffer. Acceptance restores the destination through the shared owner. The browser entry position is navigation bookkeeping, not a second return stack.
- **Index and deletion:** following user review on 2026-10-03, initial default or direct ordinary-document loading selects its matching visible Index row once. Direct named-document loading selects no collection host. Tree clicks select the clicked row; Search/Recent clicks mark their exact result while retaining tree state. Source shortcuts use the explicit clicked/invoked row. Remove a deleted tree selection independently of the displayed target. When a committed deletion removes the displayed document, return to its known caller; without one, use the existing first-surviving-loadable-ordinary-root destination, or the existing empty state if none remains. A missing direct target or a caller deleted by an operation shows its exact failure with any available earlier Back, without substituting a host or scanning for a replacement caller.
- **Committed summaries:** return the exact target and a complete projection of supported list metadata from the already validated write: title, summary, dates, supported readiness/status and configured collection row metadata/authoring Subject. An absent supported field clears its previous value; a Folder Subject must survive this private projection even though the public reader Subject projection omits it. Use the owning date/collection projectors, including date-only list values and Catalogue's fixed eligibility. Exclude source text, paths and unrelated front matter. Notify after persistence and keep projection errors separate from the committed operation; cancelled, dry-run and uncommitted results produce no update.
- **Projects and other callers:** retain the response's scanned folder identities, Work-to-folder/Series membership and Series identities, then reconcile title/Subject changes against that captured input in memory. Removing or changing a Subject can remove or reposition a row; it does not trigger Run/Refresh. Reapply the caller's own filters/order/group/page and retain controls, selection and position. These workflows are synchronous: assume callers and captured inputs still exist and have not been edited while a linked document is open, including in another tab. Add no freshness validation or return-time workspace reads.
- **Create and Import:** their completion owners already know exact targets and written records. Extend those record projections from their validated inputs where needed and forward the same committed summaries. For partial Import or a source commit followed by generation failure, forward only the explicitly confirmed committed records and preserve the existing failure report; do not invent successful records for failed/unattempted writes. Delete forwards its confirmed exact targets, including ordinary descendants. Back itself performs no mutation discovery or manifest refresh.

The approved authored-source cutover covered nine active Markdown links in five Working documents: ordinary **Beauty** and **Insert Doc link**, and Works **10,000**, **_a links test B** and **3 symbols (book)**. The two literal route examples in ordinary **Data Model** and affected reader/route descriptions in ordinary **Reports** were also updated. The old hosts were resolved against explicit collection configuration while editing; document IDs and unrelated content were preserved. The reader gains no inference or compatibility alias. Historical proposals and test fixtures were not migrated.

The route cutover covers the shared URL/parser and exact-target reader, authored-link insertion, generated semantic/related links, report rows, Search/Recent/Selected navigation, Copy Link, link analysis, Import destinations and export/package rewriting. Collection report hosts remain browse and publication-eligibility owners. Search, Recent, Selected and relationship records already carry structured identities; changing the route does not require a Search rebuild or identity migration. Review preserves its selected package and resolves only that package's documents; it must not fall through to Working or another collection. Existing exported/Review packages and external bookmarks using retired routes require replacement through their owning operation, not in-place migration of package contents.

After the global link/renderer contract changes, reconcile complete Working document output through its owning Build with media builds skipped. Do not hand-edit generated JSON or Preview/public payloads. Shared/public code still requires its tracked projection and site validation. Public generated links remain on the prepared snapshot until a separately authorized Publish; complete that publication before releasing the new runtime and generated route contract together. Search rebuild, Publish, deployment, commit and push are outside this implementation approval.

This delivery owns caller history/restoration on the currently registered document collections, including Catalogue. The older View Caching and History and Subject Associations Retirement deliveries were retired as superseded on 2026-10-03 at the user's request. Catalogue remains a document collection; future Subject work is separate. This delivery does not claim wider resource/media caching changes. Use [Runtime](Docs_Viewer_Runtime.md) as the durable owner for shipped navigation/action/history behavior, with [Collection Report Architecture](Sub_Scope_Index_Architecture.md) updated for list ownership; previous/next traversal remains outside this delivery.

## Deliverables

- [x] One document-view/navigation owner for exact ordinary and named-collection targets across supported link entry points.
- [x] Browser-history caller return with small per-view restoration state, coherent Back/Forward and hidden toolbar Back when no in-app caller exists; no `from` query or separate return stack.
- [x] Independent Index selection and browsing state, with explicit user navigation retained.
- [x] Collection lists that open the common reader, with duplicate detail-rendering/navigation responsibilities retired.
- [x] Unified document actions, Source capture and active-document refresh with existing public, Manage and package authority preserved.
- [x] Committed Save/Delete notifications to retained caller lists, including metadata/Subject regrouping and confirmed deletions, with list-owned reconciliation and no discovery scan on Back.
- [x] Direct ordinary `doc` and named `collection`/`doc` URLs, with explicit producer/reference/generated-output cutover and retirement of host-plus-`subdoc` document routes without aliases.
- [x] Selected static evidence, manual interaction review, distinct code review and transfer of shipped behavior to durable documentation.

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

- [x] Confirm the requested model against the current navigation, collection, action, Index and provider owners.
- [x] Resolve the browser-history, fragment/refresh/Source and explicit Index choices for approval, including initial and deleted selection.
- [x] Identify the bounded authored references, active producer/consumer boundaries and generated reconciliation needed for direct routes without aliases.
- [x] Confirm committed Save/Delete summary inputs, Create/Import completion owners and Projects' available placement data without a new scan or report redesign.
- [x] Reconcile proposal overlap and choose Runtime and the collection architecture as durable owners.
- [x] Accept the resolved choices and bounded Working source/generated-output cutover; authorize DVR-1–3 implementation.
- [x] Accept the proportionate implementation verification budget below. Stop for a broader source migration, package/public authority change or Catalogue/caching redesign.

Verification budget: readiness used focused read-only code/config/reference inspection and bounded proposal review only. For implementation, use explicit changed-file JavaScript/Python lint, required shared/public code projection/check and `bin/site-validate`, ordinary whitespace review and the owning complete Working document Build with `--skip-media-builds` for the global rendering/link change. These address module diagnostics, projection drift, deploy-root integrity and regenerated document-route agreement; allow a few minutes per implementation batch for routine diagnostics, with complete Build cost dependent on the current corpus and reported when selected. No test run, test/fixture edits, temporary regression code, browser automation, live mutation experiments, Search rebuild or publication is included. User manual review owns presentation and return interaction; the distinct final code review remains required.

Record: readiness and the bounded implementation/verification scope were accepted on 2026-10-03. Implementation reuses configured by-ID storage, validated metadata projection and source-persistence completion; Projects retains supplied placement data. No storage move, route compatibility alias, new scan or wider caching/Catalogue redesign was introduced.

Gate: accepted; implementation is authorized within the recorded boundary.

### DVR-1 — Exact-Target Document Reader And Route Cutover

- [x] Introduce the common exact-target reader and action context through focused owners.
- [x] Load ordinary and collection by-ID payloads through their configured providers without a full manifest read merely to open a document.
- [x] Move collection detail rendering into the common document view while retaining list browsing and its supported customisations.
- [x] Resolve document actions, Source capture and active generated-document refresh from the exact target rather than the selected Index row or a mounted collection detail.
- [x] Change supported document-link producers and consumers to ordinary `doc` or named `collection`/`doc`, preserving public route and Review package context.
- [x] Complete the approved authored/saved-reference cutover and remove host-plus-`subdoc` document routing and duplicate detail responsibilities without aliases.
- [x] Reconcile affected generated output only where the changed builder or link contract requires it. Search rebuild, Publish, deployment, commit and push remain separately authorized actions.
- [x] Preserve related-links capture, supported Content Detail adapters and local/public/package authority through the reader change.

Verification budget: choose exact changed-file lint/syntax and direct existing diagnostics after the implementation owners are known, addressing exact target reads/actions, route agreement and public/package isolation. For represented shared/public code, run `bin/site-code-update`, inspect the tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`. Apply the same projection requirement to subsequent runtime steps. Select any existing tests only after inspecting their coverage and agreeing execution scope; creating or changing tests, fixtures, harnesses or profile membership requires a separate approved specification under [Test Contract Discipline](Test_Contract_Discipline.md). Record exact evidence, costs, side effects and limits; no automatic suites or browser click scripts.

Manual review gate: the same document opens with correct content/actions from a direct URL and each agreed link entry point; collection membership changes neither the reader nor action target. Missing targets show an error without substituting the host. Route cutover is complete within the approved boundary. These are acceptance cases, not evidence already obtained.

Record: implemented. Complete Working builds with `--skip-media-builds` processed 41 ordinary, 244 Works, 246 Concepts, 57 Moments and 4,616 Catalogue documents with zero warnings. Generated by-ID output contains no retired `subdoc=` route. Working browser configuration projects its exact ordinary document URL template from the builder. Review keeps its selected-package authority and existing safe package IDs. Changed-file lint covered 53 JavaScript and 20 Python files, including follow-up checks after review fixes. Code projection/check, deploy-root validation and whitespace checks passed. The user accepted the implementation after the recorded manual checks; public snapshot preparation/distribution remains a separate action.

Gate: passed; one exact-target document reader and route contract replace both old reader paths, with caller return and mutation reconciliation completed in DVR-2–3.

### DVR-2 — Browser History, Caller Restoration And Independent Index

- [x] Record document/hosted-view navigation through browser history with small per-entry restoration state; do not add `from` queries or a second history stack.
- [x] Update the current history entry for Search/Recent and other filter/sort/group/page control adjustments.
- [x] Restore document, list, report/results and supported Content Detail callers directly, with controls, selection, scroll and invocation focus retained.
- [x] Make toolbar Back and browser Back/Forward use the same call chain; hide toolbar Back without a known restorable in-app caller.
- [x] Separate Index selection from the active document and retain the explicit action behavior above, including clicked-row Source targeting.
- [x] Remove automatic collection-host selection, ancestor expansion and tree scrolling from document links outside the tree; retain relevant Search/Recent result marking.
- [x] Complete the agreed direct-load, fragment, refresh, deleted-caller and Source discard behavior without navigation-time scans or speculative freshness checks.

Verification budget: changed-file diagnostics and bounded state/route review for caller identity, history-entry ordering, explicit Index targets and Source cancellation. Manual interaction review owns return state and focus/scroll presentation. Reuse sufficient evidence from DVR-1; add tests only under separately approved scope.

Manual review gate: first load or reload selects the opened default/ordinary document's matching Index row; direct named-document loading selects no collection host. Projects → Doc → Back restores its filter/sort/position; collection list → Doc → Back restores its list; Doc A → Doc B returns through the call chain; Search/Recent and Content Detail callers return correctly. Control adjustments do not introduce extra Back steps, the Index stays in place, and direct/new-tab openings without a caller hide toolbar Back. Browser Back/Forward and cancelled Source navigation preserve the intended view.

Record: implemented through one browser-history owner and retained document/list/presentation owners. Control changes replace current-entry restoration values; explicit tree selection is independent of displayed identity. Source discard cancellation traverses back to the active browser position without another push. The initial Index selection correction passed focused route-workflow JavaScript lint, inspected public code projection/check, site validation and whitespace review. The user confirmed general navigation and accepted the page-session Back behavior, including no toolbar Back after refreshing a direct Catalogue URL. Detailed scroll, focus and Source-cancellation cases were not individually confirmed and continue through normal work.

Gate: caller return is coherent through the one navigation owner and independent Index state; no collection fallback, duplicate chain or intermediate wrong view remains.

### DVR-3 — Committed Changes And Retained List Reconciliation

- [x] Extend full Source Save's successful result with an exact-target committed list summary from the metadata already validated during persistence, without another source read/scan.
- [x] Forward completed Save/readiness/Delete changes to affected retained list owners; retain confirmed deleted targets and descendants where applicable.
- [x] Keep each report/list responsible for its model and rendering; Source Save must not edit another report's DOM directly.
- [x] Reconcile affected records and filter/order/group/page projections in memory while preserving controls, selection and reading position.
- [x] Update Projects title labels and Subject-based folder/Series placement from retained report inputs without rerunning its full scan.
- [x] Integrate known Create/Import results through their existing completion owners where retained callers are affected.
- [x] Notify only committed changes. Preserve source-persistence Save completion and report projection failures separately from the saved source; retain watcher/active-generated refresh for rendered content and VS Code edits.
- [x] Remove return-time change-discovery scans or unconditional report/list reloads introduced by the old ownership split. Preserve explicit owning Run/Refresh and recovery actions.

Verification budget: focused service/module diagnostics and bounded response/list-owner review for exact identity, committed metadata, deletion scope and source/generated completion separation. Inspect the relevant existing readiness/deletion patterns before reusing them. Any tests or live mutation checks require separately agreed scope and effects; do not write temporary regression scripts or mutate real sources merely for documentation evidence.

Manual review gate: edit a linked document's title, readiness and relevant Subject, then return to the caller with the changed row/group and retained controls. Delete an entry and verify its removal and page/selection reconciliation. A body-only edit does not recompute unrelated report data. Failed/cancelled writes produce no successful update; a caller projection failure does not undo Save. Returning adds no workspace scan, unchanged manifest fetch or automatic Projects Run/Refresh.

Record: implemented. Full validated committed summaries feed retained collections, Projects, Works, Index, Search/Recent, Selected, Docs Media and workspace Links. Projects/Works preserve supplied membership inputs; body-only changes skip report recomputation when their displayed fields are unchanged. Source exposes projection errors separately from persistence. Create/Import forward confirmed commits, including supported partial results; Draft/Ready forwards complete metadata and Delete forwards descendants. Search's saved file, body postings and coverage are unchanged. The user confirmed changing a title and the list updating. Codex ran no tests or live mutation experiments; other mutation/failure cases were not individually confirmed and continue through normal work.

Gate: retained callers reflect notified committed changes through their own owners, and Back only restores the view. All three implementation steps are required for the complete delivery.

### DVR-4 — Code Review

- [x] Review the bounded final change for duplicate readers, hidden collection-host routing, Index coupling, wrong action targets, compatibility residue and public/package authority leaks.
- [x] Review history/control entry ownership and exact caller restoration, including Source cancellation and deleted callers.
- [x] Review committed summaries and list notifications for identity agreement, report-owned projection, hidden scans and source/generated completion coupling.
- [x] Confirm failure and return handling against the agreed specification without treating a list projection failure as a failed persisted Save.
- [x] Resolve findings within scope and repeat only evidence affected by review changes.

Verification budget: bounded production/config/generated diff review and targeted follow-up diagnostics justified by findings.

Record: bounded production/config/generated review completed. Findings resolved for descendant deletion notifications, deleted Index selection, Content Detail layout/retention, report sort/control history, exact clicked-row Source opening during a pending document read, complete Draft/Ready summaries and saved-source notification failures. User review found a blank Source view for a direct Works URL: Source CSS hid the new document mount containing the editor. The local stylesheet now keeps that mount visible and hides only its rendered children; the user subsequently confirmed opening Source editor. No compatibility route was retained. Relevant existing tests still contain retired route/helper assumptions; they were inspected only for affected references and remain unchanged and unrun under the separate test-work policy. Public configuration/data migration remains with Publish, rather than a hand-edited snapshot.

User review also found Media View displayed below its calling Catalogue document. The Content Detail marker was on the retained document mount while shared CSS still targeted the outer content panel. The selector now follows the marked document mount for all four supported presentation kinds. Scoped selector/lifecycle review, inspected public code projection/check, site validation and whitespace review passed. The user accepted general navigation at closeout; the detailed Media View visual case was not separately confirmed.

Gate: findings resolved and completion claims match the inspected surfaces and actual evidence.

### DVR-5 — Closeout

- [x] Transfer the shipped viewing, browser-history return, Index, direct-route and committed-list-update model into Runtime and the collection architecture owner, or a focused durable navigation document if that is clearer.
- [x] Record user manual confirmation, exact selected evidence and remaining material limitations.
- [x] Reconcile affected older proposals without claiming their wider caching, Catalogue or previous/next work is delivered.
- [x] Present a retain-or-retire recommendation for this delivery. Document deletion and Git/publication actions remain explicit.

Verification budget: documentation and scoped closeout review; no repeated builds or tests without a new reason.

Record: accepted and closed on 2026-10-03. Runtime, Search and collection-list architecture describe the implemented model; user manual checks cover general navigation, Source opening, title changes and list updates. Further testing continues as part of normal work. Existing implementation/review evidence was reused; closeout changed repository documentation only, with scoped reference/diff and whitespace review. Retain this delivery and its completed handoff for manual archive. The two superseded deliveries were removed with the user's approval; Catalogue stays and future Subject work is separate. Public Publish, deployment, commit and push remain separately authorized actions.

Gate: the agreed complete result is delivered and its durable documentation is current.

### DVR-6 — Two Retained Views And One Caller Return

The approved model retains at most two document/report views: the current view and its immediate caller. Back restores that caller, consumes the return context and releases the view being left. There is then no earlier toolbar Back and no retained Forward destination. Browser-native older Back/Forward may reload the exact URL; it does not promise discarded report state.

For the user's example:

1. Open the Catalogue list: it occupies slot 1.
2. Open Work A: the retained list is the caller in slot 1 and Work A is current in slot 2.
3. Follow a document link from Work A to Doc B: release the list, make Work A the caller and Doc B current.
4. Back from Doc B restores Work A and releases Doc B. The return context is consumed, so toolbar Back is hidden.
5. Open Catalogue through the Index to load that discarded report again.

Repeated Catalogue list → Work → Back → another Work cycles retain the same list mount and model, avoiding a repeated manifest/report read. Media View is a temporary presentation of the current document: its Back returns to that document, preserves its immediate caller and uses no document slot. Apply the same Content Detail lifecycle to table, diagram and expanded-report presentations. Following a document link from Content Detail records the underlying document as caller.

Discarding a view releases its DOM, payload, report models, subscriptions and presentation resources through their owning lifecycles. Retained lists continue receiving committed metadata updates while a linked document is current. Source discard confirmation, exact-target loading, direct/reloaded first-document behavior and independent Index state remain supported. This is bounded page-session retention, without an expiry framework or a second navigation stack.

- [x] Implement the two-view retention boundary and consumable caller return; release older and returned-from views.
- [x] Remove Content Detail from document history and retain its local return-to-document lifecycle.
- [x] Release discarded report subscriptions, payloads, mounts and presentation resources; keep list reuse and committed updates within the retained boundary.
- [x] Update Runtime and the temporary handoff to the final policy, review the bounded change and run focused static checks plus required public code projection/validation.
- [x] Record user acceptance and closeout, distinguishing it from individually confirmed manual scenarios.

Verification budget: bounded navigation/document/presentation lifecycle review, changed-file JavaScript lint, `git diff --check`, inspected `bin/site-code-update` projection, `bin/site-code-update --check` and `bin/site-validate`. These are read-only diagnostics or the required tracked code projection, expected to cost seconds to a few minutes. No test creation, test suite, browser automation, live mutation experiment or generated-document rebuild is authorized by this step.

Manual review gate: repeated list → Work → Back cycles preserve list controls and position; list → Work A → Doc B → Back restores Work A with no further toolbar Back; reopening a discarded list through Index loads it again. Media View returns to the same document without consuming its document caller. Source cancellation preserves the editor and caller. Direct/reloaded first documents hide toolbar Back, and browser-native navigation outside the retained pair reloads the exact destination.

Record: implemented on 2026-10-03. The browser-entry owner prunes restoration records to current/caller and consumes caller context on Back. The document controller removes discarded mounts/payloads and releases report subscriptions, collection lifecycles and adapters; retained subscriptions still receive committed updates. Content Detail uses its own local return and no suspended presentation history. Bounded review covered repeated list visits, deeper links, native older/Forward URL reload, Source cancellation and asynchronous report lifetime cleanup. JavaScript lint passed for the nine changed canonical modules; code projection updated exactly those nine public modules, projection check passed for 101 files and site validation passed for 62 required files, 7 directories and 71 runtime modules. No tests, browser automation, live mutation experiment, document/Search rebuild, Publish or Git action was performed. The user accepted the follow-on and authorized closeout; detailed manual scenarios were not individually reported.

Closeout: accepted and closed on 2026-10-03. Runtime, Search, collection-list architecture and Development Checklist already describe the final policy. This status-only closeout updates the delivery, handoff and Runtime acceptance record; code review is not applicable because no code/config changes are made. Reuse the completed implementation review and static evidence, with bounded source/diff review of the closing text. Retain this delivery and handoff for manual archive. Further interaction testing belongs to normal work; public release and Git actions remain separately authorized.

## Follow-on And Related Proposals

The older View Caching and History delivery was retired as superseded. [Runtime](Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns caller restoration and browser history; its local HTTP caching section records the existing transport policy. Wider resource/media reuse changes require their own requirements and authorization. Working watcher/active refresh remains implemented.

The Subject Associations Retirement delivery was retired as superseded. Catalogue remains a registered document collection. [Subject Associations](data/subject-associations.md) records current behavior; future Subject review is separately scoped.

[Doc Navigation](Doc_Navigation.md) and [Context Navigation](Document_Context_Navigation.md) concern saved hierarchy ordering and proposed previous/next traversal. Caller Back does not define that sequence. Native app navigation, cross-application return protocols, persistent/offline caching and general report redesign remain separate work.
