---
draft: false
doc_id: d-20261117-181805-fff247
title: Portfolio Recents And Collection Sorting
added_date: "2026-11-17 18:18:05"
last_updated: "2026-11-17"
summary: Show recently added portfolio entries in the main Index and use consistent A–Z and Last added orders in Manage and Public collection lists.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Portfolio Recents And Collection Sorting

**Proposed delivery.** Follow-on to [Public Index Search Scopes](../Public_Index_Search_Scopes.md#recent-coverage) under [Planned Features](../Planned_Features.md).

## Requirements

**Main Index Recent** shows up to 20 recently added portfolio entries in Manage and Public, newest first. Context documents, Concepts, Moments and Catalogue Galleries qualify under the existing publication eligibility rules. Apply exact document exclusions before taking the first 20. Ordinary site pages, collection landing pages, individual Catalogue Works, Library entries and Books are outside the feed. A Gallery result opens its exact Gallery in the same Media View used by Portfolio search.

**Last added** means newest by recorded addition date everywhere this delivery provides a date order. Edits, renames, membership changes, rebuilds and Publish preserve that date. Use title and exact identity to break ties. Undated entries remain browsable and follow dated entries in a date-sorted list. Recent admits dated entries only.

| Surface | Default | Available orders in Manage and Public |
| --- | --- | --- |
| Context, Concepts, Moments and Library collection reports | A–Z | A–Z and Last added via the shared sort button |
| Catalogue List without a query | Last added | Default order and Shuffle. **Reset to default order** returns to the first 64 Works in Last added order. |
| Catalogue search results | A–Z on starting a search | A–Z and Last added via a sort button shown during search |

Keep Catalogue's rolling Gallery and its dice behavior. Clearing a Catalogue query restores the discovery view and its saved selection. In an active search, keep the chosen sort while refining the query or returning from a result. Retain the existing result groups of Gallery title matches, Galleries matched through member Works, and Works. Apply the selected order within each group before pagination. Main Index search keeps its current relevance ranking and uses title to break score ties. [Catalogue browsing](../Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) · [Search ranking](../Docs_Search_Index.md#query-and-ranking)

Use the same A–Z default and Last added option in the flat Book List in Manage. The Book Tree, public table of contents and edition navigation follow the authored reading order. Public Books open at their TOC. [Book curation and editions](../Sub_Scope_Index_Architecture.md#book-curation-in-manage)

## Deliverables

- Shared collection controls and sort behavior. The browser sorts loaded rows before paginating and keeps the current selection locks, Context pins and retained view state. The existing Book List uses the same sort semantics for its private inventory.
- Compact addition dates in the collection metadata used by each reader. Docs generation projects the saved document `added_date`, including the Catalogue Work document's `added_date`. Studio owns the Gallery addition date and carries it into its prepared Gallery metadata. Both the collection report and Recent use that prepared Gallery metadata.
- A single completed Working Recent artifact with independent portfolio membership and exact document and Gallery targets. Working generation owns candidate selection, filtering, order and the limit. The shared reader renders the saved order and reuses existing result navigation. [Recent contract](../Generated_Data_Contracts.md#recent-contract) · [Gallery search publication](Catalogue_Index_Gallery_Results.md#studio-refresh-and-publication)

Use the Docs Viewer Catalogue document's `added_date` to sort Works by **Last added**. For each existing Gallery, seed its date once from the latest of those document dates among its current direct member Works. This date can reflect a batch import. Join existing memberships to the prepared document dates and save the result on the Gallery definition. A Gallery with no dated direct member stays undated. For a newly created Gallery, Studio records its actual creation date. Later membership edits preserve either date.

## Process

Choose **Last added** in a collection report to see additions at the top, or switch back to A–Z. In Catalogue, use the dice from the unfiltered report or enter a query to browse results starting in A–Z. For a newly added Gallery, run Studio Refresh to prepare its metadata, then use Manage **Refresh Search and Recent** or a Full Working Build. Publish transfers the queued outputs through the existing workflow. Public uses the deployed snapshot. [Search and Recent refresh](../Public_Index_Search_Scopes.md#building-and-publishing-search-indexes)

## Delivery Steps

- [ ] **0. Readiness.** Identify the manifest refresh needed to supply `added_date` to both readers and prepare the Gallery seed from those dates and direct memberships. Confirm the Catalogue result groups and the Book List scope above. Current collection manifests supply update dates. Gallery definitions have no addition dates.
- [ ] **1. Prepare data.** Project addition dates through the existing collection and Gallery producers. Seed the existing Gallery definitions once from the Docs Viewer document dates. Have discovery refresh and Full Working Build reuse completed metadata to build the portfolio feed. Verify the prepared manifests and Recent artifact against the coverage and date rules before reviewing the controls.
- [ ] **2. Connect readers.** Add the shared sort controls, Catalogue search default and Gallery activation from Recent. Project the shared runtime and run scoped lint, projection and site validation. Use a focused manual Manage and public preview walkthrough for List and Shuffle reset, a new Catalogue query and return from a result, Library sorting, Book List versus TOC, and the portfolio feed. Allow roughly 20 minutes for one walkthrough, plus the time needed to prepare the updated manifests and Recent.
- [ ] **3. Review.** Apply the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Confirm that opening and sorting the reports uses loaded metadata, editing a title cannot advance its addition date, and Publish transfers completed selections. Record the evidence and remaining manual checks.
- [ ] **4. Closeout.** After acceptance, update the maintained collection browsing and Recent contract sections, record the release state and recommend whether to retain the delivery.
