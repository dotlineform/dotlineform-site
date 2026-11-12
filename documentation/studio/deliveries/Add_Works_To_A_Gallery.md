---
draft: false
doc_id: d-20261112-100806-18ec7a
title: Add Works To A Gallery
added_date: "2026-11-12 10:08:06"
last_updated: "2026-11-12"
summary: Find saved Works by title, Work ID or Medium and add a selected batch to the displayed Gallery in Studio.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Add Works To A Gallery

Complete. The user accepted the Local Studio workflow, confirmed the result in Docs Viewer after Refresh, and requested closeout on 2026-11-12. The [Catalogue Work Editor](../Catalogue_Work_Editor.md#add-works-to-a-gallery) owns the workflow. Retain this delivery pending manual archive.

## Requirements

- Use the left-panel **New Series or Gallery** action to create and open an empty Gallery. The choice of type defaults to the current view. Creating a Gallery here preserves the Work draft and creates no Series-wide relevance.
- Select a Gallery in the Catalogue Editor and open **Add Works…** beside its member count. The action also works for an empty Gallery. The modal names the displayed Gallery as the destination and uses the familiar Catalogue token picker's search and thumbnail presentation with multiple selection.
- Search saved Works by title, Work ID or a case-insensitive substring of the saved Medium. For example, `acrylic` finds Works with `acrylic on canvas` or `acrylic on board`. Show the thumbnail, title, Work ID, saved Medium and Series so the curator can choose across Series. Show a tick in place of the checkbox for Works already in the destination Gallery.
- Check the Works to add and confirm with **Add selected**. Save only the checked Work IDs. Add direct membership to the chosen Gallery while preserving each Work's Series and other Galleries. On completion, update the displayed member list and count from the saved results. Cancel closes the modal without a write.

## Ownership And Deliverables

- **Studio browser.** Own the modal, search, membership indicators and selection. Reuse the loaded Work rows and saved Gallery memberships. The Work search response already supplies a distinct Medium vocabulary. Supply per-Work Medium in the existing response from its already loaded records and carry it through the saved-record updates that the editor already receives. The Docs Viewer token picker is the interaction reference. Studio supplies the current authoring data. [Work search projection](../../../studio/services/catalogue/catalogue_lookup.py) · [Token picker](../../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js)
- **Studio persistence.** Reuse the existing bulk Save request for per-Work Gallery membership sets. The browser prepares the exact selected IDs and each Work's existing set plus the destination Gallery. Python persists those sets and completes the existing queue handoff. Reuse the completed records to update the member list. Generated Gallery readers continue through the established Refresh, Regenerate and Publish workflow. [Bulk Save](../../../studio/services/catalogue/catalogue_bulk_service.py) · [Save and Refresh](../Catalogue_Save_And_Refresh.md)

## Delivery Steps

- [x] **Readiness.** Show the `image-plus.svg` button beside the member count in Gallery view. The browser searches the live Work lookup, including saved Medium from startup and subsequent saved records. An open clean Work selection stays in place and adopts any added membership. Resolve unsaved Work changes before opening the picker so later Work Save cannot overwrite the new membership. Bulk Save already supports membership-only changes across Series and returns saved records and queue completion. No new endpoint or generated-reader change is needed.
- [x] **Implementation.** The picker retains checks across searches and shows the checked Works when the search is cleared. The Catalogue Editor adopts the saved memberships and updates the displayed Gallery. The [Catalogue Work Editor](../Catalogue_Work_Editor.md#add-works-to-a-gallery) describes the workflow.
- [x] **Code review.** Traced empty Galleries, existing memberships, cross-Series selection, draft interaction, and both Save failure paths. The [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) confirmed that the picker reads the loaded rows and the service reads Works and memberships once for the existing write and queue handoff. No per-Work lookup, follow-up manifest read, media preparation or Gallery audit is added. Shared bulk response adoption checks selected IDs and record shape before updating the browser; the existing server request, exact target and confined write checks remain. The picker uses the shared Work busy indicator rather than rerendering the editor before Save. The modal blocks duplicate submissions while Save is pending. A failed request keeps the checks; a confirmed write with a queue completion error updates the list and reports the unfinished handoff.
- [x] **Standalone Gallery creation.** The browser adopts the returned definition and opens its empty list. Source review traced both New choices, the title warning for the selected type, draft and registry updates, Cancel and save completion. Both choices reuse their existing create requests and returned records. Opening the picker and adopting the created definition require no lookup or draft rebuild. Focused lint passed for the seven changed JavaScript modules.
- [x] **Acceptance and closeout.** The user confirmed standalone Gallery creation, the picker’s appearance and the result in Docs Viewer after Refresh. The delivery was accepted for closeout. Individual picker scenarios, including cross-Series selection, the tick on reopening and Cancel, were not reported separately. The Catalogue Work Editor and [Planned Features](../Planned_Features.md#reviews) record the outcome.

Focused Studio JavaScript and Python lint, whitespace checks and bounded source review passed during implementation. The user supplied the live acceptance evidence. Closeout updates repository documentation.

## Follow-on

- Try repeated Medium searches in normal use before deciding whether to save candidate criteria. A saved search would bring up current candidates for editorial selection.
- Use the existing Media View links when featuring selected Galleries on the dotlineform landing document. Revisit Gallery-only browsing and the **No Series association** filter if finding the destination Gallery in the editor becomes a separate problem.
