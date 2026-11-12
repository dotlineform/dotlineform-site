---
draft: false
doc_id: d-20261112-100806-18ec7a
title: Add Works To A Gallery
added_date: "2026-11-12 10:08:06"
last_updated: "2026-11-12"
summary: Find saved Works by title, Work ID or Medium and add a selected batch to the displayed Gallery in Studio.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Add Works To A Gallery

Proposed delivery. Use the Catalogue Editor's existing search panel and Gallery member list. The next step is readiness review before implementation. [Planned Features](../Planned_Features.md#proposed-features) · [Studio Gallery Browser](Studio_Gallery_Browser.md)

## Requirements

- Select a Gallery in the Catalogue Editor and open **Add Works…** beside its member count. The action also works for an empty Gallery. The modal names the displayed Gallery as the destination and uses the familiar Catalogue token picker's search and thumbnail presentation with multiple selection.
- Search saved Works by title, Work ID or a case-insensitive substring of the saved Medium. For example, `acrylic` finds Works with `acrylic on canvas` or `acrylic on board`. Show the thumbnail, title, Work ID, saved Medium and Series so the curator can choose across Series. Exclude Works already in the destination Gallery.
- Check the Works to add and confirm with **Add selected**. Save only the checked Work IDs. Add direct membership to the chosen Gallery while preserving each Work's Series and other Galleries. On completion, update the displayed member list and count from the saved results. Cancel closes the modal without a write.

## Ownership And Deliverables

- **Studio browser.** Own the modal, search, exclusions and selection. Reuse the loaded Work rows and saved Gallery memberships. The Work search response already supplies a distinct Medium vocabulary. Supply per-Work Medium in the existing response from its already loaded records and carry it through the saved-record updates that the editor already receives. The Docs Viewer token picker is the interaction reference. Studio supplies the current authoring data. [Work search projection](../../../studio/services/catalogue/catalogue_lookup.py) · [Token picker](../../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js)
- **Studio persistence.** Reuse the existing bulk Save request for per-Work Gallery membership sets. The browser prepares the exact selected IDs and each Work's existing set plus the destination Gallery. Python persists those sets and completes the existing queue handoff. Reuse the completed records to update the member list. Generated Gallery readers continue through the established Refresh, Regenerate and Publish workflow. [Bulk Save](../../../studio/services/catalogue/catalogue_bulk_service.py) · [Save and Refresh](../Catalogue_Save_And_Refresh.md)

## Delivery Steps

- [ ] **Readiness.** Confirm the button placement in the existing member panel, the path that keeps saved Medium and membership rows current, and how the modal interacts with an open Work draft. Confirm the existing bulk Save and completion paths support a membership-only batch across Series. Keep the implementation scoped to the Catalogue Editor and the Studio lookup and save owners.
- [ ] **Implementation.** Wire the modal, candidate search and selected additions into Studio. Show saved results immediately in the same Gallery and reuse the existing save-error handling.
- [ ] **Code review.** Trace empty Galleries, already assigned Works, cross-Series selections, draft interaction and successful and failed Save completion. Apply the [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review), with particular attention to avoiding a per-Work lookup or a manifest reload for the picker or its Save.
- [ ] **Acceptance and closeout.** In normal Studio use, open a Gallery, search a Medium fragment, check a subset across Series and add it. Confirm the list and count update, the other memberships are intact, the added Works are absent when reopening the picker, and Cancel leaves membership intact. Record the results in the [Catalogue Work Editor](../Catalogue_Work_Editor.md) and update the parent status.

Proposed verification is focused lint for the changed Studio JavaScript and Python, plus whitespace and bounded source review. The static checks take seconds and perform no application writes. Manual acceptance uses one deliberately selected membership batch in Local Studio, with roughly 10 minutes for the checks once suitable Works are chosen.

## Follow-on

- Try repeated Medium searches in normal use before deciding whether to save candidate criteria. A saved search would bring up current candidates for editorial selection.
- Use the existing Media View links when featuring selected Galleries on the dotlineform landing document. Revisit Gallery-only browsing and the **No Series association** filter if finding the destination Gallery in the editor becomes a separate problem.
