---
title: book-collections
added_date: "2026-05-26 00:00:00"
last_updated: "2026-10-17"
---
# book collections

Parent: [Planned Features](../Planned_Features.md). Status: proposal; implementation has not started.

Make Library a **named collection with type `book-collection`**. The first delivery uses Context's existing collection features as its explicit baseline: optional thumbnails, title search, title/recent sorting with the Manage sort option button, pagination, selection and Prepare Package, and Import support. It additionally provides an explicit Manage-only option to turn pagination on or off. Later deliveries add authored books and their separate local curation tooling.

`book-collection` is an extension of the existing collection system. Context supplies the feature baseline; the implementation reuses the shared collection machinery. Standard browsing, document reading, management, imports, package preparation, media handling, generation and publication retain one maintained implementation. Improvements to shared features remain available to their adopting collections.

The design separates collection membership, book structure and book authoring. Library publishes normally throughout these deliveries. The collection is not treated as draft or withheld from publication while further capabilities are being developed; ordinary document draft and publication rules continue to apply.

Library is currently an ordinary document with children in the main Index. Existing named collections already keep their documents outside the main Index and provide collection browsing, so this can extend the [existing collection architecture](../Sub_Scope_Index_Architecture.md).

**First delivery: convert Library**

The complete outcome is Library operating as a normal named collection in Manage and the public reader, using [Context's collection browsing](../Works_Collection_Browsing.md) and the standard collection management capabilities:

- Retain the existing Library document and its ID as the collection report host.
- Register the `library` collection with type `book-collection`, initially providing standard collection behavior.
- Move the selected current Library children into the collection, preserving their document IDs, and remove their ordinary Index placements.
- Update affected document references, identity-bearing selections and media ownership.
- Make Library available as the import destination and preserve its current site-search inclusion explicitly.
- Display optional authored document thumbnails through the existing collection media support.
- Provide Context's collection-title search, title/recent ordering and the existing Manage sort option button.
- Provide pagination in both readers, plus the explicit Manage-only pagination on/off option.
- Provide Manage document selection and Prepare Package, alongside Import support.
- Keep normal document management, generation and publication available.

Feature parity retains the existing public/Manage boundaries. Thumbnails, collection search and paginated reading are shared; the sort option button, selection, Prepare Package, Import and the additional pagination toggle follow their local management ownership. The collection uses the existing document reader and management workflows.

Pagination is enabled by default in both Manage and the public reader, using the existing collection page size. Manage additionally offers a pagination on/off control; off displays all documents matching the current filter in the current order. Query, ordering and document selection remain independent of pagination. Retain the local pagination choice through the existing tab-scoped collection browsing state.

The toggle is an explicit Manage-only browser customisation supplied by local composition. The public reader retains pagination and receives no toggle, management implementation or local preference. This is browser view state: switching pagination reuses the loaded inventory and requires no server request, manifest reload, source write, generation or publication. It does not require a server authoring `collection_customisation` registration.

Existing pagination is currently selected for Catalogue and Context; registering Library alone will not enable it. This delivery explicitly adopts that existing list capability for Library without changing other collections.

This delivery creates no initial book, empty `books.json`, book selector, outline renderer or curation report. It introduces no collection-wide draft state or development publication gate.

The iCloud `library` directory remains an import source. Imported canonical documents live in Working; collection conversion does not reorganise the original import files.

Current named-document routes include `collection=library`, so preserving document IDs alone does not preserve existing ordinary-document URLs. Whether those old URLs must continue working remains a decision before the migration is approved; compatibility routing is not assumed.

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

The collection configuration selects `book-collection` and explicitly adopts the required shared capabilities. Where pagination or sorting currently depends on specific collection IDs, introduce a narrow adoption point so Library can use that existing behavior while preserving the choices of current collections. Keep the shared report and workflow owners authoritative; do not fork Context's implementation or create parallel book-specific versions of standard collection operations.

The first extension is the pagination toggle, supplied through the existing Manage-only contribution boundary and using the shared list's pagination state. Later extensions add book data and tree presentation through focused owners, with the local organisation editor delivered separately. The collection type and browser composition remain distinct from existing server authoring customisations; using Context as the browsing baseline does not adopt its Work/Subject authoring specialisation.

| Owner | Responsibility |
|---|---|
| Browser | Outline editing, placement choices, ordering, filtering, expansion and retained view state |
| Python service | Persist the submitted outline and complete its generated/publication effects |
| Generation | Produce eligible public outlines using completed collection metadata |
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

Book placement must not determine publication eligibility. Existing document draft/exclusion policy and collection-host eligibility remain authoritative.

Generation would omit ineligible document references from public outlines and prune sections left empty. Outline saves would queue the changed shared artifact. Document deletion would remove its known placements as part of the deletion operation.

Changing a document’s position would consequently require no document rendering or Search rebuild. The public reader would receive the collection inventory and compact outlines, loading document bodies only when opened.

**Delivery sequence**

| Delivery | Complete outcome |
|---|---|
| 1. Convert Library | Context's existing collection features: optional thumbnails, title search, title/recent ordering and Manage sort button, pagination, selection and Prepare Package, Import, document management and publication; add the Manage-only pagination toggle. No books or authoring tool. |
| 2. Add book browsing | Establish canonical book data and its generated public projection, and render named trees consistently in local and public collection readers. Structures can initially be authored directly in the canonical file. |
| 3. Add book curation | Introduce the separate local organisation report/editor for creating books, inspecting memberships and managing placements through an explicit save operation. |

Book browsing is independent of the graphical authoring tool. Detailed book schema, authoring operations and publication follow-through remain proposals for their owning deliveries. Each material implementation delivery needs its own readiness, proportionate verification budget, code review and closeout under [Development Checklist](../Development_Checklist.md). Test work requires its separately agreed specification.
