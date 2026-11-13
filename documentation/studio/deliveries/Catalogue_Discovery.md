---
draft: false
doc_id: d-20261112-235622-7f2733
title: Catalogue Discovery
added_date: "2026-11-12 23:56:22"
last_updated: "2026-11-13"
summary: Browse Catalogue in selections of up to 48 Works, with dice navigation and a matching Media View grid.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Discovery

## Experience

Open unfiltered Catalogue on one selection of up to 48 Works, with the dice as the way to see more. Hide the page count and list pager in this view. The initial selection comes from the default Catalogue order. The first dice click starts a shuffled pass through the full inventory from a uniformly random position in the shuffled list. Each later click advances by 48 in that order, wrapping to the front when it reaches the end of the list. End the pass after showing each Work once, with a shorter final selection when needed. The following click starts a pass from a new random position in the order produced by the next file.

Use each of the 64 existing quantum random files once per cycle. Randomize their order at the start of each cycle and advance through that order. Each file produces a Fisher–Yates permutation. The browser picks the starting position independently of the file. After all 64 passes, start a new cycle. Remember the file order, active file, starting position and progress through the pass in the existing tab state so a reload or return to Catalogue resumes the same selection. [Catalogue Shuffle](Catalogue_Shuffle.md) · [Catalogue Shuffle Randomness](../Catalogue_Shuffle_Randomness.md)

Offer a control to open the current selection as one Media View grid. Use the same Works in the same order, including a shorter final selection. Work navigation inside Media View follows that selection. Returning to Catalogue restores it.

A nonempty query searches the full Catalogue. Keep the existing paginated Work and Gallery results with 20 rows per page. Clearing the query restores the current discovery selection.

In every Working collection, **Select** keeps the displayed list stable while the checkboxes are enabled. Disable browsing controls that change the rows or their order, including search and clear, sort, paging and the pagination toggle, Book section navigation, and the Catalogue dice where present. **Select all** and range selection use the displayed document rows in order. **Done** restores the browsing controls for the current view.

After a successful Working Regenerate, show the first selection in default Catalogue order. Clear the search, custom sort, page, scroll position and shuffle cycle from the live report and the saved browsing state. The next dice click starts a fresh cycle.

## Viewing effort

The tracked public Catalogue snapshot contains 5,196 Works. At 20 rows per page, the current unfiltered list has 260 pages. At 48 Works per selection, a shuffled pass covers the same inventory in 109 selections. There are 108 full selections and a final selection of 12. Starting with the first dice click, it takes 109 clicks to reveal them all, or 108 advances once the first selection is on screen. [Public Catalogue manifest](../../../site/assets/data/docs/catalogue/manifest.json)

One pass is enough to see every Work once. Running all 64 files takes 6,976 selections and shows each Work 64 times in different orders. The initial default selection is outside these counts.

| Time spent per selection | One complete pass | All 64 files |
| ---: | ---: | ---: |
| 5 seconds | 9 min 5 sec | 9 hr 41 min 20 sec |
| 10 seconds | 18 min 10 sec | 19 hr 22 min 40 sec |
| 30 seconds | 54 min 30 sec | 58 hr 8 min |

These are idealized viewing times at the stated pace, with each selection viewed once per pass. They exclude load time, navigation overhead and time spent opening individual Works. The technical minimum is a count of selections. Elapsed time depends on the viewing pace.

## Chances of a repeat

At 5,196 Works, the first dice click in a fresh tab can pick from 64 × 5,196 = 332,544 file-and-start combinations. For two independent fresh tabs with the same inventory, starting order and files, the chance of choosing the same combination is 1 in 332,544 (about 0.00030%). This is also the approximate chance of seeing the same first 10 Works in the same order, or the same full opening selection.

The approximate chance of seeing the same 10 consecutive Works somewhere in both opening selections is 1 in 4,319 (about 0.023%). For the same file, each of the 77 starts within 38 positions of the first start, including that start, gives at least 10 Works of overlap in the two 48-Work selections. Distance is measured around the wrapped order. These estimates use only the first dice click in each tab, assume uniform independent file and position choices across tabs, and treat matches between different files as negligible.

## Readiness

Working and Public mount the same collection report. It already prepares the full Work inventory with exact IDs, titles and thumbnail URLs, and its default order is latest updated first, then title and Work ID. The browser owns the 48-Work selection, pass and file cycle, and can remember the cycle order, active file, starting position and progress in the existing tab snapshot. Keep the active permutation in memory. On a remount, use the saved controls and loaded inventory to recreate it from one file through the existing static route. The tracked public manifest has 5,196 Works and the stock has 64 files of 32 KiB. At this size each pass needs 5,195 accepted draws from a file of 8,192 draws. The existing shuffle reports exhaustion if a future inventory outgrows the stock. Existing servers already serve the required data and media.

Both report hosts expose the existing Media View opener for browser-supplied presentations. The current grid accepts a canonical Gallery identity, and the saved Gallery reader fetches membership, media policy and Context links. Add support for a temporary ordered Work selection at the supplied-presentation boundary. Pass the current selection's IDs, titles and prepared thumbnail URLs directly to the existing grid and Work navigation. Opening the grid needs only those rows. Opening a Work uses its existing exact by-ID read. Content Detail owns Back and focus restoration to the Catalogue list, and the selected Work can return to the same grid. Keep authored Gallery routes, links and ordering with their current owners. The shared frontend changes require a tracked public runtime projection.

### Proposed decisions before implementation

- Show the Working sort control in search. Discovery starts in the default order and uses it as the input to each shuffle. Catalogue Work links opened from discovery follow the displayed selection, as they do inside Media View. Search keeps its current full-result navigation and 20-row pages.
- The shared Working selection owner controls the lock, and the report supplies the displayed document IDs in render order. Enable entry once any pending search or shuffle has settled. Include Context's displayed pinned rows and Catalogue's displayed Work rows. Collection Actions continue to receive the checked IDs.
- The Working Regenerate completion owns the browsing reset. The current action reloads the manifest in place when it builds, creates or deletes Works. Use those refreshed rows for the initial selection, or the already loaded rows when there were no Work changes. Reset the Catalogue search URL with the query. The default sort uses the latest update day first, with ties by title and Work ID. Ordinary reload and return still resume discovery against stable inputs. On a failed shuffle file read, retain the current selection and leave that file next for retry.

## Delivery steps

- [x] Inspect readiness. Reviewed the shared report, Working selection and Public composition, tab snapshot, Media View and static stock in source. Browser interaction remains for implementation acceptance.
- [x] Confirm the proposed decisions and approve implementation. Approved on 2026-11-13.
- [x] Implement the shared Working selection lock. The report supplies displayed document IDs to the existing selection owner. That owner projects the checked rows and controls when browsing is locked.
- [x] Implement discovery, tab restore and the [Media View](../Catalogue_Media_View.md#discovery-grid) handoff. Regenerate resets the saved and live browsing state on success. The 48-Work list and grid use lazy thumbnail loading pending manual review. Focused lint, whitespace, public runtime projection and static site validation passed.
- [x] Review the implementation using the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review). Source review traced default, search and empty results, pass advancement and restore, failed file reads, mixed Work and Gallery pages, pinned rows, section and pagination controls, Media View and Regenerate with or without Work changes. Advances reuse the loaded permutation, the grid carries prepared thumbnails, and ordinary paging supplies only displayed document IDs to Working selection. Removed the full filtered-ID projection and the pagination callback that used to clear selection. Kept file transport checks, tab-state parsing, Media View target and URL checks, and the guard against a late shuffle replacing the Regenerate reset. The existing Regenerate path rereads the manifest when Work changes complete. The delivery adds no server or generated-data contract.
- [x] Record initial user confirmation. On 2026-11-13 the user reported that it works so far and will continue checking during normal operation. Individual scenarios were not itemised.
- [ ] Record normal-use findings as they arise. Remaining coverage includes selection across all six Working collections, Working and Site Preview discovery and Media View, shuffle boundaries and tab restore, live Regenerate, and thumbnail loading under throttling.
- [ ] Record the retain-or-retire decision at closeout. Updated the maintained [selection lifecycle](../Sub_Scope_Index_Architecture.md#selection-lifecycle), [Catalogue browsing](../Sub_Scope_Index_Architecture.md#catalogue-collection-browsing), [shuffle reference](../Catalogue_Shuffle_Randomness.md) and [Media View](../Catalogue_Media_View.md#discovery-grid).
