---
draft: false
doc_id: d-20261112-235622-7f2733
title: Catalogue Discovery
added_date: "2026-11-12 23:56:22"
last_updated: "2026-11-13"
summary: Propose browsing Catalogue in selections of up to 48 Works, with dice navigation and a matching Media View grid.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Discovery

## Proposed experience

Open unfiltered Catalogue on one selection of up to 48 Works, with the dice as the way to see more. Hide the page count and list pager in this view. The initial selection comes from the default Catalogue order. The first dice click starts a shuffled pass through the full inventory from a uniformly random position in the shuffled list. Each later click advances by 48 in that order, wrapping to the front when it reaches the end of the list. End the pass after showing each Work once, with a shorter final selection when needed. The following click starts a pass from a new random position in the order produced by the next file.

Use each of the 64 existing quantum random files once per cycle. Randomize their order at the start of each cycle and advance through that order. Each file produces a Fisher–Yates permutation. The browser picks the starting position independently of the file. After all 64 passes, start a new cycle. Remember the file order, active file, starting position and progress through the pass in the existing tab state so a reload or return to Catalogue resumes the same selection. [Catalogue Shuffle](Catalogue_Shuffle.md) · [Catalogue Shuffle Randomness](../Catalogue_Shuffle_Randomness.md)

Offer a control to open the current selection as one Media View grid. Use the same Works in the same order, including a shorter final selection. Work navigation inside Media View follows that selection. Returning to Catalogue restores it.

A nonempty query searches the full Catalogue. Keep the existing paginated Work and Gallery results with 20 rows per page. Clearing the query restores the current discovery selection.

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

## Delivery steps

- [ ] Confirm readiness. Catalogue already holds the full inventory for search and Shuffle. The browser can derive a bounded selection from that order and supply its Work IDs, titles and thumbnail URLs to Media View. Confirm the shared report and Media View integration in Working and Public.
- [ ] Implement the discovery selection, dice progression and tab restore. Load the next file when a pass begins, choose its random start and reuse the shuffled list for each advance. Reuse the existing thumbnail URLs and single-grid Media View layout. [Media View](../Catalogue_Media_View.md#gallery-presentations)
- [ ] Review the boundary between discovery and search, wraparound and coverage of every Work once per pass, the shorter final selection, advancement between files, rollover after the 64th file, and return from Media View. Assess visible thumbnail loading for 48 Works under throttling before settling the loading policy.
- [ ] Record acceptance and update the maintained Catalogue browsing and Media View documentation.
