---
title: book-collections
added_date: "2026-05-26 00:00:00"
last_updated: "2026-10-17"
---
# book collections

Parent: [Planned Features](../Planned_Features.md). Status: Delivery 1 complete and user-accepted for closeout on 2026-10-17, including the Save queue refinement and pagination icons. The user confirmed successful Publish and cross-collection Related Links. Further verification continues through normal use. Book browsing and curation remain proposed later deliveries.

Make Library a **named collection with type `book-collection`**. The first delivery uses Context's existing collection features as its explicit baseline: optional thumbnails, title search, title/recent sorting with the Manage sort option button, pagination, selection and Prepare Package, and Import support. It additionally provides an explicit Manage-only option to turn pagination on or off. Later deliveries add authored books and their separate local curation tooling.

`book-collection` is an extension of the existing collection system. Context supplies the feature baseline; the implementation reuses the shared collection machinery. Standard browsing, document reading, management, imports, package preparation, media handling, generation and publication retain one maintained implementation. Improvements to shared features remain available to their adopting collections.

The design separates collection membership, book structure and book authoring. Library publishes normally throughout these deliveries. The collection is not treated as draft or withheld from publication while further capabilities are being developed; ordinary document draft and publication rules continue to apply.

Library was an ordinary document with children in the main Index before the Delivery 1 cutover. It now extends the [existing collection architecture](../Sub_Scope_Index_Architecture.md#flat-book-collections), with one ordinary Library host and flat collection documents.

**First delivery: convert Library**

The complete outcome is Library operating as a normal named collection in Manage and the public reader, using [Context's collection browsing](../Works_Collection_Browsing.md) and the standard collection management capabilities:

- Retain the existing Library document and its ID as the collection report host.
- Register the `library` collection with type `book-collection`, initially providing standard collection behavior.
- Use the existing [library.svg](../../../docs-viewer/static/icons/library.svg) as Library's collection icon, configured as `icon: "library"` in Manage and the public reader through the existing shared icon projection.
- Move the selected current Library children into the collection, preserving their document IDs, and remove their ordinary Index placements.
- Update affected document references, identity-bearing selections and media ownership.
- Make Library available as the import destination.
- Configure `library` with `include_in_site_search: true` so its eligible documents continue participating in full-text site search after conversion.
- Display optional authored document thumbnails through the existing collection media support.
- Refactor the shared collection report to separate collection-title search and sort capabilities from pagination state, retaining each existing collection's current behavior and defaults.
- Provide Context's collection-title search, title/recent ordering and the existing Manage sort option button.
- Provide pagination in both readers, plus the explicit Manage-only pagination on/off option.
- Provide Manage document selection and Prepare Package, alongside Import support.
- Keep normal document management, generation and publication available.
- Retain the current flat-collection draft rule: draft documents remain available in Manage and are excluded from generated public output.

Feature parity retains the existing public/Manage boundaries. Thumbnails, collection search and paginated reading are shared; the sort option button, selection, Prepare Package, Import and the additional pagination toggle follow their local management ownership. The collection uses the existing document reader and management workflows.

Site-search inclusion is an explicit requirement of the first delivery. Eligible Library documents remain searchable alongside ordinary documents and Context in Manage and the public reader, using the existing site-search fields and eligibility policy. Results retain the exact `library` collection identity and open the common document reader. Inclusion is independent of pagination and any later book memberships; a document need not appear in a book to participate in site search. The collection's existing title search remains a separate browsing capability.

The conversion includes an explicit Working Search and Recent refresh to replace the moved documents' ordinary identities with their collection identities, with publication following the existing queued discovery workflow. Search and Recent already share collection inclusion policy, so preserving Library's coverage also preserves its existing participation in Recent. Ordinary Save and Import retain the existing explicit discovery-refresh lifecycle; this requirement introduces no automatic Search or Recent rebuild on document changes.

Pagination defaults to off in Manage to support the initial content-import and organisation work. Off displays all documents matching the current filter in the current order; the Manage pagination on/off control enables paged browsing when wanted. The public reader keeps pagination enabled, using the existing collection page size. Changing pagination through the Manage toggle clears checked documents and range-selection state, exits selection mode and resets the page position; enabling pagination starts on the first page. Keep the current search query and sort order. Retain the local pagination choice through the existing tab-scoped collection browsing state, applying the off default when no choice has been saved.

The toggle is an explicit Manage-only browser customisation supplied by local composition. The public reader retains pagination and receives no toggle, management implementation or local preference. This is browser view state: switching pagination reuses the loaded inventory and requires no server request, manifest reload, source write, generation or publication. It does not require a server authoring `collection_customisation` registration.

The refactor applies to the shared collection-report implementation used by all collections. Context and Catalogue retain paginated browsing; other existing collections retain their current presentation and controls. Library alone initially adopts the Manage pagination toggle and its selection-reset behavior. Collection-title search and sort remain available according to each collection's capabilities in either pagination mode. This refactor does not change site search.

This delivery creates no initial book, empty `books.json`, book selector, outline renderer or curation report. It introduces no collection-wide draft state or development publication gate.

The iCloud `library` directory remains an import source. Imported canonical documents live in Working; collection conversion does not reorganise the original import files.

The agreed migration uses named-document URLs containing `collection=library`, preserves document IDs and updates managed references. The Library host keeps its current ordinary-document URL. Old external child-document links and bookmarks may stop working; no compatibility routing or aliases are required.

**Delivery 1 readiness — 2026-10-17**

- [x] Confirm the complete result and boundary: convert the current Library branch to a flat named collection with the agreed Context feature baseline, explicit site-search inclusion, the Library icon and the Manage-only pagination toggle. Books, tree eligibility and the curation editor are not prerequisites.
- [x] Confirm the current source boundary: the existing Library host is ready and its 17 current children are flat. Working source and generated owners are configured externally; the iCloud Library directory remains an import input. Migration affects selected existing documents and their referenced media, not the original import files or a bulk import of that directory.
- [x] Confirm ownership: the browser owns loaded inventory, title search, sort, selection, pagination and tab-scoped view state. Python owns configured storage, persistence, exact generation, discovery refresh and publication handoffs. Reuse standard Import and Prepare Package collection targets; Context's Work/Subject specialisation is not required.
- [x] Confirm extension feasibility: the shared collection report, management contribution and common reader provide the required boundaries. Collection type adoption needs explicit configuration/browser support. Current pagination state also selects search/control/rendering behavior, so Delivery 1 includes a bounded shared refactor separating search/sort capabilities from pagination state for all collection reports. Existing collections retain their behavior and defaults. Library's Manage toggle resets selection and page position while keeping the query and sort order; selection capability remains available in both modes.
- [x] Resolve routing: use collection URLs and update managed references; preserve the host URL and document IDs. The user accepts that old external child-document URLs may stop working. No alias or routing compatibility work is included.
- [x] Confirm publication and discovery follow-through: preserve per-document draft exclusion, register document-media ownership, explicitly promote the icon, update exact identity-bearing saved data and refresh Search/Recent once for the cutover. Withdraw old ordinary publication outputs as well as preparing new collection outputs; preserve unrelated pending selections.
- [x] Confirm the sequence, review gate and evidence limits below. Readiness used bounded source/configuration and canonical Library-tree inspection only. No implementation, test code, test run, browser run, real source/media mutation, generation, Search/Recent refresh, Publish, commit or push was performed. Only this proposal was updated.

Readiness result: passed; Delivery 1 is ready to implement as one bounded outcome. No unresolved product decision or dependency blocks starting it. Shared browsing changes and the source/media/publication owner cutover are the credible blast radius. The new local toggle must remain absent from the public module graph; normal public browsing and eligibility remain available throughout further feature development.

Stop and raise scope before adding legacy URL support, a general cross-collection move facility, book/tree/editor behavior, new folder-import authority, automatic repair/recovery, or unrelated collection changes. During implementation, resolve the exact old-owner withdrawal/new-owner publication ordering before moving live documents; the queue must not lose required effects or unrelated pending work. This is an implementation gate, not a request for a frozen migration design during readiness.

**Delivery 1 implementation sequence**

- [x] BCF.0 — Readiness: outcome, owners, dependencies, URL decision, credible risks and scope gates confirmed above.
- [x] BCF.1 — Refactor the shared collection report to separate title-search/sort capabilities from pagination state for all collections, preserving their existing behavior and defaults. Extend the existing collection/configuration and management composition for the flat `book-collection`, with Manage pagination default off and a retained local toggle that clears selection/range state, exits selection mode and resets page position while keeping query and sort. Retain public pagination. Register Library, its document-media owner and public icon projection without copying Context's workflows.
- [x] BCF.2 — Complete the selected Library cutover: keep the host, move canonical document/media ownership, update managed references and saved identities, generate the required ordinary/Library output and prepare both old-owner withdrawals and new-owner publication effects. Refresh Search/Recent for the changed identities. Keep normal Import, Source Save, Prepare Package and publication available.
- [x] BCF.3 — Review the bounded implementation and generated effects, including the shared paginated/unpaginated paths, unchanged existing collection behavior and Library's explicit selection reset. Apply the mandatory [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Challenge repeated source reads, per-row payload loads, corpus scans, duplicated validation, compatibility residue and hidden generation; retain actual authoring, path/confinement and selected transfer boundaries.
- [x] BCF.4 — Close out the complete result, update the durable collection/runtime ownership documentation and record remaining manual observations. User accepted closeout on 2026-10-17. Book browsing and curation remain separate proposed deliveries. Publish, deployment and Git actions retain their explicit action boundaries.

Implementation record: the optional `collection_type` adopts shared list capabilities, with the pagination control supplied only by Manage composition. The toggle is synchronous and adds no pending-search guard; existing search delay remains a browsing performance choice. Changed-owner JavaScript lint passed for five modules and Python lint passed for four modules. Public projection added the Library SVG and changed only the public configuration, shared collection report and configuration normaliser. The icon inventory's initial ordering error was corrected; `bin/site-code-update --check`, `bin/site-validate` and whitespace review passed. No tests or browser automation were authored or run.

Cutover record: moved 17 ready Markdown sources into the Library owner, preserved IDs/dates/draft values, removed their ordinary Index placements and added the host's `docs_collection` block. Copied the three exact referenced ready-media files (PNG, SVG and HTML) to Library ownership, retaining old media for manual orphan cleanup. Rewrote the one internal Library link; completed relationship records showed no incoming authored links from outside Library. Selected and Recent-exclusion source controls contained no moved targets and were unchanged. Targeted ordinary generation wrote the host and removed 17 old payloads; the first complete Library build wrote 17 payloads and its manifests, with zero warnings. The directly affected Concepts neighbour was rendered once and required no payload change. Explicit discovery refresh wrote 28 Search results, including all 17 Library targets, and 20 Recent rows, including 15 Library targets. The existing limit and exclusions remain authoritative.

Publication handoff record: the existing document-ID queue cannot otherwise retain old-owner withdrawal and new-owner addition for the same ID. The one-time cutover therefore supplied `removed_document_collections: [""]` on each of the 17 Library units; queue updates carry that exact effect through later Save/Delete and the selected publisher removes former Preview/repository by-ID files before completing the unit. This is a finished-effect field in the existing queue, with no new ledger, general Move workflow, source scan or publication audit. At handoff, the Docs queue also held the host and the changed ordinary index, Library manifest, Search and Recent; both Catalogue queues were empty. Codex did not run Publish or transfer verification. The user subsequently reported successful Publish.

Review record: bounded production/configuration/projected-source review traced shared paged/unpaged rendering, selection reset/restoration, type propagation, existing Import/package targets, source/media ownership and publication queue replacement/consumption. No aliases or copied collection workflows were introduced. Routine list changes reuse prepared inventory and make no requests. Retained safeguards are type selection at the configuration boundary, exact configured artifact/media confinement, create-only migration destinations and existing authoring/transfer checks. New collection setup explicitly established empty prior manifests once; no runtime fallback or repair was added. No additional asynchronous-state handling was added to the pagination toggle. Durable collection, runtime, source-organisation and Builder docs are updated.

Closeout record: user accepted Delivery 1 and its follow-ups on 2026-10-17. The user confirmed Publish and then saved a link from Context's “100 grasping hands” to Library's “Abstract Thought and Physical Processes”, confirming Related Links across the new collection boundary. Those are the specifically recorded runtime observations; individual list controls, thumbnail assignment, Import, Prepare Package and failure variants were not separately itemised as exercised. They remain normal-use verification opportunities rather than open delivery gates. No Codex-run remote transfer, commit, push or deployment occurred. Durable behavior is maintained in Sub-Scope Index Architecture, Runtime, Source Organisation, Builder and Toolbar Icon Mapping. Retain this document as the feature snapshot and route to the proposed book-browsing/curation deliveries; retain the ignored one-time operation as local implementation evidence, with no runtime role or rerun requirement. No document deletion or archive is part of this closeout.

Closeout review: this is a documentation-only status update, so a new code review is not applicable. Bounded source/diff review reuses the recorded implementation reviews, lint/projection/site checks and user observations. No tests, builds, Search refresh, generation, publication or runtime changes are required or rerun for closeout.

Save follow-up: an already-draft Context Save had queued a redundant document removal despite the document already being absent from completed public membership and Preview. The approved fix applies the existing eligibility-transition/pending-effect guard to normal generation as well as maintenance. It skips only new removals for already-excluded saved documents with no pending entry or media removals, retaining actual withdrawals, explicit Delete and pending effects without Preview probes or additional reads. Changed-file Python lint for `docs_publication_preparation.py` and whitespace checks passed. The subsequent Redundancy And Defensive Behavior Review traced the already-loaded membership transition, normal/maintenance branches and existing queue effect preservation: the fix adds only in-memory decisions, retains explicit Delete behavior and introduces no validation, filesystem probe, fallback or recovery path. No executable regression tests, builds, live Save, queue cleanup or Publish were performed; the existing harmless deletion entry is unchanged.

Implementation verification budget: use changed-owner JavaScript/Python lint, relevant syntax/configuration diagnostics, whitespace review, bounded source/diff review, and the required public runtime projection/check and site validation. These local checks should cost seconds to a few minutes and establish static contracts and public projection, with no browser/service startup or remote transfer. The selected cutover additionally requires real Working document/media writes, required document generation and one explicit discovery refresh; its exact processing cost is determined from the selected inputs during implementation, without a readiness benchmark or media-producer run. Inspect required generated identities, eligibility, media references and queued effects without rerunning solely for idempotence evidence. User manual acceptance covers thumbnails, search/sort, both pagination modes and retained state, selection, Import, Source Save and Prepare Package. No pytest profile, browser automation, new tests, fixtures or temporary regression scripts are selected or authorised by this readiness review; test work remains separately specified under [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md).

Pagination icon follow-up: Library's Manage toggle now uses the supplied `dlf-paginate-on.svg` and `dlf-paginate-off.svg` for its current pagination mode. The local management stylesheet owns the two mask mappings; the source SVGs are used as supplied and require no public promotion. Changed-file JavaScript lint and whitespace checks passed. Bounded review confirmed the existing icon element is reused, with only its mask classes changing alongside the existing accessible label/pressed state; no service calls, source writes, validation or recovery behavior were added. Accepted within the user's Delivery 1 closeout; no separate visual scenarios were recorded and no tests, browser automation, generation or Publish ran for the icon change.

Pagination visibility correction — 2026-10-17: the user reported page controls appearing once Library exceeded a page while its Manage toggle was off, with the controls apparently unaffected by toggling. Source inspection found two visibility writers: the collection hid the pager for unpaged browsing, then the pager's count-only update showed it again for multiple pages. The report now supplies its current pagination mode to the pager update, and the pager alone combines that choice with page count. Off retains every matching row without page controls; on uses the existing 20-row pages. Toggle selection reset, query/sort, saved mode and the public always-paged default retain their existing owners. No service work or search-pending handling was added.

The correction passed changed-path JavaScript lint for the shared report and browsing helper, whitespace checks, public projection consistency and site validation. The exact two-file projection was inspected. Bounded code review traced initial controls, toggle rendering, saved-mode restoration and public/default modes; it removed the competing visibility write without adding validation, compatibility aliases, reads, preflights or recovery behaviour. No tests, browser actions, document generation or Publish ran; live confirmation after reloading Docs Viewer remains manual. [Collection architecture](../Sub_Scope_Index_Architecture.md#flat-book-collections) owns pager visibility.

**The browsing model**

The main Index contains one Library entry. Delivery 1 opens the normal collection list. Later book browsing would extend that same reader with:

| View | Purpose |
|---|---|
| All documents | Current collection list, title filtering, title/recent ordering and pagination |
| A named book | An authored, expandable hierarchy of parts, chapters and document links |
| Another named book | A different arrangement of the same underlying documents |

For example:

```text
Library

All documents
Books:
  Memory and identity
    Part I — Foundations
      Memory systems
      Reconstructive memory
    Part II — Personal identity
      Autobiographical memory

  Mind and computation
    Representations
      Memory systems
      Neural representations
```

“Memory systems” is one document appearing in two books. Editing it updates what both books open.

Here, a **book is a curated table of contents**. Combining its documents into one continuous reading or export view could follow separately.

**Membership and structure**

I suggest these rules:

- Every Library document belongs to the collection independently of any book.
- A book contains ordered section nodes and document references.
- Sections can nest, allowing parts, chapters and deeper subdivisions without imposing fixed levels.
- Documents can appear in several books, and optionally in several places within one book.
- Books can cover only part of Library.
- Removing a placement or section changes the outline; deleting a document remains a separate action.

Unplaced documents is not an automatic book section or a reader view. All documents remains the complete collection inventory. Local curation tooling may provide filters such as documents in no books or absent from a selected book, calculated from loaded membership and placements. Import does not require an editorial placement decision.

Document titles should come from the collection inventory. Outlines store references, rather than copied titles or content. Renaming a document therefore needs no edits to its book placements.

**Authoring and navigation**

Book creation and organisation belong in a separate local Book Organisation report/editor, comparable in placement to local Catalogue reports. It could show document memberships and placements, a searchable document pool and the selected outline. Proposed operations include creating and renaming books, adding sections, placing documents, moving or indenting nodes, removing placements and duplicating an outline.

Editing authored organisation introduces an explicit authoring responsibility beyond the read-only or inspection-oriented boundary in [Reports](../Reports.md). That policy extension and its save/completion contract must be agreed in the later curation delivery. It does not require a general active-report framework. [Report Capability and Composition](../Report_Capability_And_Composition.md) retains ownership of the separate public and local module graphs.

The editor would persist canonical book organisation, such as `books.json`, through its local service. It would not directly edit generated indexes or the main Index's `index-order.json`. Local and public collection readers share their browsing behavior; authoring controls and membership diagnostics remain in the separate local tool.

The reader would remember the selected book, expanded branches and reading position through the existing retained collection state. Opening a chapter would use the common document reader; Back would restore its originating outline.

Filtering an outline should retain the ancestors of matching documents so the results remain understandable. All documents would remain the straightforward way to search the entire collection.

I would keep global Index navigation unchanged. The additional trees belong inside the Library report.

**Implementation ownership**

The collection configuration selects `book-collection` and explicitly adopts the required shared capabilities. Delivery 1 includes a shared refactor of `docs_collection`: collection-title search and sort capabilities are distinct from the current pagination state. Where adoption currently depends on specific collection IDs, introduce a narrow adoption point while preserving the choices of current collections. All collections use the refactored shared implementation; the new pagination control and selection reset are supplied only by Library's Manage composition. Keep the shared report and workflow owners authoritative; do not fork Context's implementation or create parallel book-specific versions of standard collection operations.

The first extension is the pagination toggle, supplied through the existing Manage-only contribution boundary and using the shared list's pagination state. Later extensions add book data and tree presentation through focused owners, with the local organisation editor delivered separately. The collection type and browser composition remain distinct from existing server authoring customisations; using Context as the browsing baseline does not adopt its Work/Subject authoring specialisation.

| Owner | Responsibility |
|---|---|
| Browser | Outline editing, placement choices, ordering, filtering, expansion and retained view state |
| Python service | Persist the submitted outline and complete its generated/publication effects |
| Generation | Produce public outlines from completed collection metadata and the agreed tree eligibility rules |
| Publish | Transfer the queued finished artifacts through its existing workflow |

The browser already has the inventory needed to organise documents. Saving an outline should not reread every Markdown source or render document bodies.

Book browsing extends the existing `docs_collection` report with a focused outline presentation owner, sharing its inventory, document links, retained lifecycle and common reader integration. The extension approach requires neither a separate book document reader nor a general collection plugin framework. Each delivery adds only the extension points needed by its agreed capability.

In the later book-browsing delivery, canonical outline data could live alongside the collection's sources:

```text
working/source/collections/library/
  documents/
  books.json
```

Each book and placement would have a stable identity. This lets the browser preserve selection and expansion when nodes move, and distinguishes two appearances of the same document.

**Publication**

The first delivery retains existing flat-collection eligibility: `draft: true` excludes a document from public output, and an excluded Library host excludes its collection. Manage retains the draft documents. No collection tree or inherited collection-parent rule is introduced in that delivery.

The proposed direction for the later collection tree-index is to follow the current main Index: exclude a draft document and, when that document is a parent, all its descendants. An otherwise eligible parent remains visible even when all its children are excluded. Automatic empty-section pruning is not a requirement.

How inherited exclusions interact with multiple trees, the All documents list and site-search eligibility remains a decision for the later book-browsing delivery. This proposal does not yet decide whether a branch exclusion affects only that tree's presentation or the document's overall publication eligibility.

Outline saves would queue their completed shared artifact. Document deletion would remove its known placements as part of the deletion operation. Routine ordering that does not change eligibility should reuse completed document payloads without rendering documents or rebuilding Search; follow-through for tree changes that affect inherited eligibility belongs in the later delivery specification. The public reader would receive the collection inventory and compact outlines, loading document bodies only when opened.

**Delivery sequence**

| Delivery | Complete outcome |
|---|---|
| 1. Convert Library — complete and accepted | Context's existing collection features: optional thumbnails, title search, title/recent ordering and Manage sort button, pagination, selection and Prepare Package, Import, document management and publication; retain Library's site-search inclusion and add the Manage-only pagination toggle. No books or authoring tool. |
| 2. Add book browsing | Establish canonical book data and its generated public projection, and render named trees consistently in local and public collection readers. Structures can initially be authored directly in the canonical file. |
| 3. Add book curation | Introduce the separate local organisation report/editor for creating books, inspecting memberships and managing placements through an explicit save operation. |

Book browsing is independent of the graphical authoring tool. Detailed book schema, authoring operations and publication follow-through remain proposals for their owning deliveries. Each material implementation delivery needs its own readiness, proportionate verification budget, code review and closeout under [Development Checklist](../Development_Checklist.md). Test work requires its separately agreed specification.
