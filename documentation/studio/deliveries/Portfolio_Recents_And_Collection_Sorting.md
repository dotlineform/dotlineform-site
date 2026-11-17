---
draft: false
doc_id: d-20261117-181805-fff247
title: Portfolio Recents And Collection Sorting
added_date: "2026-11-17 18:18:05"
last_updated: "2026-11-17"
summary: Show recently added portfolio entries in the main Index and use consistent A–Z and Last added orders in Manage and Public collection lists.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Portfolio Recents And Collection Sorting

**Complete.** Accepted in Manage and Public on 2026-11-17. The tracked site contains the projected runtime and the eight published data files. Retain this delivery pending manual archive. Follow-on to [Public Index Search Scopes](../Public_Index_Search_Scopes.md#recent-coverage) under [Planned Features](../Planned_Features.md).

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

- [x] **0. Readiness.** Confirmed date coverage, Gallery seed, collection controls and the cutover through the existing generation and publication owners. See the readiness record below.
- [x] **1. Prepare data.** Rebuilt all six collections with media builds skipped. The complete manifests contain addition dates for every current row and the builds wrote zero by-ID documents. Seeded 191 Gallery definitions and projected their dates through Studio. Refresh wrote the 20-entry Recent feed and skipped all six unchanged Search indexes. Standalone ordinary Build dry-run also produced 20 Recent entries with no warnings.
- [x] **2. Connect readers.** Added one shared sort control, the Catalogue search default and Gallery activation from Recent. Changed-file lint, whitespace checks, site projection and site validation passed. The browser limit cleanup left a dangling `getConfigValue` import that blocked startup. Removed the unused helper, import and Manage context property together. Chromium confirmed Manage reached its ready state after the cleanup.
- [x] **3. Review.** Applied the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Collection sorting reuses loaded rows. The browser trusts the saved Recent order and immediately removes known deletions. The legacy `include_in_site_search` selector, ordinary date reads and browser limit were removed. Gallery date validation lives with Studio's canonical audit, and Publish uses its existing selected-file confinement and byte verification. The first complete Catalogue build selected 5,196 unchanged Work documents. Their bytes already matched both destinations. Cleared those selections and verified that complete Catalogue Build with the corrected handoff queues only changed or restored Work documents.
- [x] **4. Acceptance and closeout.** The user confirmed that Manage and Public work and approved closeout. Verified the six manifests, Gallery search file and new Recent feed in the tracked site. Both publication queues are empty. The [collection browsing guide](../Sub_Scope_Index_Architecture.md#public-and-manage-projections) and [Recent contract](../Generated_Data_Contracts.md#recent-contract) own the current behavior. Keep this delivery pending manual archive. Git commit and Deploy Public are separate release actions.

### Readiness Record

**Date coverage and seed.** Every current Working collection row has a recorded source `added_date`, including all 5,196 Catalogue Works. The prepared Gallery titles and direct memberships match Studio's saved definitions and memberships. The join supplies dates for 191 of 193 Galleries. The two empty Galleries stay undated. On the current eligible Working snapshot, the first 20 would contain 17 Galleries, two Moments and one Context document. This is the result of a single portfolio order with no per-collection quota.

**Cutover.** Use the existing day-level list format (`YYYY-MM-DD`) with title and identity for same-day ties. Keep `last_updated` in collection manifests for Search display metadata. The Working manifest builder and public eligibility projection both need to carry `added_date`. Use a complete docs-only Build for each named collection with `--skip-media-builds` to populate every row. Include Catalogue explicitly because the full Working maintenance command skips it, and targeted Regenerate only updates selected Works. Use the prepared Work dates and Studio's direct memberships for the one-time seed, then regenerate the existing Gallery report/search file before refreshing Recent. The completed public manifests, Gallery file and Recent use their existing queue handoffs. [Collection manifest ownership](../Generated_Data_Contracts.md#collection-manifest-ownership) · [Gallery search publication](Catalogue_Index_Gallery_Results.md#studio-refresh-and-publication)

**Reader boundaries.** The Catalogue report already holds the three search result groups and their distinct targets. It can sort loaded rows within each group and page the result. A different default Work order changes the starting input to future Shuffle passes. The Manage Book List is a flat projection of the loaded manifest and the Tree has its own reading-order projection. Scope the Book sort button to List. Recent can reuse Search's exact Gallery activation and consume completed collection and Gallery metadata. Both discovery build paths can pass the same prepared Gallery data to Search and Recent. The standalone ordinary Build can use those saved inputs. Saving a document must stop replacing its cached Recent date with its update date. [Catalogue browsing](../Sub_Scope_Index_Architecture.md#catalogue-collection-browsing) · [Book curation](../Sub_Scope_Index_Architecture.md#book-curation-in-manage)

**Gate.** Read-only inspection and a calculation against the Working data established readiness. The cutover selected six collection manifests, one Gallery report/search file and one Recent artifact, all transferred by Publish.
