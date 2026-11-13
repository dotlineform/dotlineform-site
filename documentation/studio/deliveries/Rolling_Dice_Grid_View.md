---
draft: false
doc_id: d-20261113-205853-3b0a73
title: Rolling Dice Grid View
added_date: "2026-11-13 20:58:53"
last_updated: "2026-11-13"
summary: Switch between a Catalogue list and a rolling 8 × 8 thumbnail gallery built one column at a time by the dice.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Rolling Dice Grid View

## Requirements

Add a **List / Gallery** toggle to unfiltered Catalogue in Working and Public. Gallery evolves the archived site's thumbnail-only browsing view. Each dice roll adds a column of eight Works on the left and shifts earlier columns right. Keep up to eight columns. Once the grid is full, drop the oldest column from the right on each roll. Thumbnails have accessible names and the grid shows no visible titles.

List shows up to 64 Works with titles. It opens on the first 64 in the default recently updated order, and its dice advances its own shuffled selection. **Reset to default order** restores the first 64 and scrolls to the top. Using the toggle to enter Gallery starts an empty grid and a fresh shuffle. Toggling back restores List's Works, order and scroll position. Keep the full-Catalogue Work and Gallery search with 20 results per page. Clearing search returns to the current discovery view.

In Working, disable **Select** and the sort controls while Gallery is active. Selection is available from List or search and applies to the displayed document rows.

Thumbnails open the Work's Catalogue document from both List and Gallery. The List thumbnail and title link to the same document. When a Work opens from Gallery, Previous and Next follow the Works displayed at the time of the click, down each column from left to right. From List they follow the displayed Works. Browser Back to the retained caller restores the invoking view, scroll position and thumbnail focus. Hide **Open selection in Media View** in Gallery. In List it opens the displayed Works, and Media View Back returns to the invoking List control.

Shuffle uses `dices.svg` and has a filled button in Gallery. **Switch to Gallery view** uses `layout-grid.svg`. **Switch to List view** uses `list.svg` with the normal unfilled button treatment.

Keep the List thumbnail elements mounted when the user enters Gallery. Keep surviving Gallery thumbnails mounted as new columns shift them right. Keep the invoking report for Back from a Work document or Media View through the existing retained-view lifecycle. A Gallery roll creates at most eight new thumbnail elements.

If the user leaves Catalogue and later reopens it in the same tab, restore the active mode, its displayed Works and scroll position, and the independent dice positions. Save shuffled List IDs and ordered Gallery column IDs alongside the shuffle controls. The saved List position is available when returning from Gallery. If the report was released or the tab was reloaded, recreate thumbnails from the saved IDs and let the browser cache handle the image requests. Gallery starts empty when explicitly entered through the toggle. A tab with no saved state starts in default List.

Use an eight-column, eight-row desktop grid for Media View Gallery pages too, with up to 64 Works per page. Keep the existing thumbnail rendition, supplied Work order and return to the page containing the selected Work. At 64 px per thumbnail and 8 px between thumbnails, the full grid is 568 px square before surrounding padding. Fit it comfortably on the user's laptop, allowing the Catalogue grid to extend beyond the document text width where the pane has room.

## Deliverables

- Shared Catalogue frontend for List and Gallery, retained columns, dice progression and the Work navigation sequence. Reuse the existing loaded inventory, prepared thumbnail URLs, tab state and same-origin QRNG stock. The browser owns presentation and progression. The server continues serving the existing manifest, images and shuffle files.
- Shared Media View pagination at 64 Works per page, with a page size independent of the eight-Work Catalogue roll. Project changed shared runtime and styles into the tracked public site. [Catalogue Discovery](Catalogue_Discovery.md) · [Catalogue Media View](../Catalogue_Media_View.md)

## Process

Each mode starts its own randomly ordered cycle of the existing QRNG files, with an independent starting position for each pass. Later rolls reuse that mode's in-memory permutation. List advances by up to 64 Works and can show a shorter final selection before moving on to the next file. Gallery advances by eight and skips a remainder of fewer than eight to keep columns full. A failed file read preserves the current view and leaves the file available for retry. [Catalogue Shuffle Randomness](../Catalogue_Shuffle_Randomness.md)

Successful Working Regenerate clears the discovery history and returns to the default selection.

## Readiness

Working and Public use the same Catalogue report. It already has the Work rows, exact document links, prepared thumbnail URLs and in-memory shuffle. The report owns the roll, visible columns, mode and saved tab state. Keep the discovery columns in a retained browser view so prepending a column or revealing titles can reuse the surviving image elements. Search can keep using the existing list renderer, which currently rebuilds regular rows. The existing tab snapshot can carry the mode and ordered column IDs alongside the active shuffle controls. On a fresh mount, the loaded inventory supplies the displayed rows and only the active file is needed to reconstruct the next roll. At the tracked 5,196 Works, each file provides 649 full rolls with four Works left over. No server or generated-data change is needed. [Catalogue browsing](../Sub_Scope_Index_Architecture.md#catalogue-collection-browsing)

The same-tab document router already accepts an ordered sequence from the invoking link. Supply the clicked cell's position in the captured grid order. A Work can occur twice among retained columns when rolls cross a file boundary, so looking up its Work ID alone could start Previous and Next at the wrong cell. The router treats an adjacent link to the same Work as staying on the current document. The current history lifecycle retains one immediate caller. Going directly Back to that caller can reuse the mounted grid and exact link. Returning after further navigation uses the saved Catalogue view when the caller has been released. Keep this lifecycle for the delivery. [Collection Previous and Next](../Docs_Viewer_Runtime.md#collection-previous-and-next)

Media View already uses one page size for both page membership and the selected Work's return page. Give that owner 64 Works per page and give Catalogue its own eight-Work roll. The existing narrow public Media View wraps its thumbnails into fewer columns. Reuse the current Working selection lock and the normal search result path. Project the changed shared frontend to Public. [Catalogue Media View](../Catalogue_Media_View.md#gallery-presentations)

### Approved defaults

- Start in List with the first 64 Works in default order. A successful Working Regenerate or a snapshot from the former shared discovery view starts a fresh List. Keep Working sort in search, and disable the List / Gallery toggle while checkboxes are active so the displayed selection stays stable.
- Allow a Work to appear again across shuffle files. Preserve both displayed occurrences and use the clicked cell to enter the captured sequence. If consecutive cells open the same Work, treat that run as one stop in document navigation so Previous and Next can move past it.
- Where the Catalogue pane cannot fit the rolling grid, use List and retain the chosen mode and columns for when there is room again. Confirm desktop fit and basic narrow-window access during acceptance. Refine the width threshold and device behavior in the site-wide follow-on if needed.

## Delivery Steps

- [x] **Readiness inspection.** Reviewed the current report, tab snapshot, document navigation and Media View in source. The thumbnail action and traversal order are agreed. Laptop and narrow-window behavior remain for implementation acceptance.
- [x] **Approval.** The user approved implementation on 2026-11-13.
- [x] **Implementation.** Added rolling columns, the shared toggle, Work navigation, the narrow-pane List fallback and independent 64-Work Media View pages. Changed-module JavaScript lint, whitespace, the four-file public projection and static site validation passed.
- [x] **Code review.** Applied the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) to initial display, roll, eviction, mode switch, search, restore, Regenerate and return. Surviving columns retain image nodes. Restore uses loaded rows and defers the QRNG read until the next roll needs a permutation. Normal rolls reuse the in-memory order. The reader keeps its existing immediate-caller lifetime and uses a clicked cell position. Working selection receives the current List or search rows. Retained file transport checks, bounded tab parsing, exact document routing and resize-observer disposal protect the existing input and view boundaries.
- [x] **Separate List and Gallery.** After the initial implementation, the user approved 64-Work List, explicit List reset and starting Gallery empty on each toggle entry. The two views use the same pass logic with independent state. Returning restores the List selection and position, and a retained return from a Work preserves the current Gallery. Focused JavaScript lint, public projection and static site validation passed.
- [x] **Toolbar refinement.** Gallery highlights Shuffle with `dices.svg`, uses an unfilled `list.svg` switch back to List and hides the Media View opener. The switch into Gallery uses `layout-grid.svg`. Focused lint, whitespace, projection check, icon byte comparisons and static site validation passed.
- [x] **Acceptance.** The user requested closeout on 2026-11-13 after reviewing the revised List and Gallery workflow and toolbar. Individual browser scenarios were not itemised. Narrow-pane layout and measured thumbnail reuse remain follow-on evidence.
- [x] **Closeout.** The maintained [Catalogue browsing](../Sub_Scope_Index_Architecture.md#catalogue-collection-browsing), [Media View](../Catalogue_Media_View.md#gallery-presentations) and [shuffle reference](../Catalogue_Shuffle_Randomness.md) describe the delivered behavior. Keep this delivery linked from Planned Features until the site-wide review picks up the small-screen and payload items below, then archive it. The public runtime is projected in the worktree. Commit and deployment remain separate actions.

## Follow-on

### Small-screen layout

Review the site as a whole in a separate delivery, including narrow Catalogue panes, navigation, Media View and touch interaction. Use the available pane width to decide whether the rolling Gallery works. A candidate is to offer List, search and dice when the pane is too narrow for the rolling grid, with Gallery available again when there is room. Compare that with showing fewer Gallery columns before deciding where to switch. Media View can keep its gallery on small screens, wrapping thumbnails into fewer columns with vertical scrolling. This delivery makes best-effort use of existing reflow and checks basic access in a narrow window. Extensive device, viewport and touch testing belongs to the site-wide review.

### Payload and loading

Measure on representative devices and connections with both cold and warm caches. Record transferred bytes, image requests and revalidations, and time until the first visible thumbnails are usable. Check the first Catalogue view, successive dice rolls, List / Gallery toggles, opening and returning from a Work, and changing Media View pages. Compare a full 64-thumbnail Media View page with the former 48-thumbnail page. Separate the cost of the manifest and the 32 KiB QRNG file at a file boundary from thumbnail transfers and the larger selected Work image. An HTTP `304` reuses cached image bytes, while a network `200` with a response body transfers the image again.

Use those observations to decide whether to tune visible-thumbnail loading, request priority, thumbnail renditions or cache policy. Screen width governs layout and control availability. Connection and cache behavior govern loading choices. The rolling grid limits each roll to one new column, and Media View requests the larger rendition when a Work is opened. Detailed throttling, cache-policy comparisons and performance targets can be agreed during the follow-on.
