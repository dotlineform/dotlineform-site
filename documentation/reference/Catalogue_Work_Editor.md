---
draft: false
doc_id: d-20260422-000000-45a776
title: Catalogue Work Editor
added_date: "2026-04-22 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6

---
# Catalogue Work Editor

Start Local Studio at `/studio/catalogue-work/`. The editor searches saved Works, Series and Galleries and owns the active draft, selection and unsaved state. [Catalogue lifecycle](Catalogue_Save_And_Refresh.md#current-workflow) · [Canonical source model](Catalogue_Source_Model.md)

## Work lookup and selection

Startup sends separate Work and Series search requests. Work search reads canonical Works and Gallery memberships, and supplies Medium suggestions from the same Work map. Series search reads the Series map. Selecting a Work requests its focused record and memberships. Save and Refresh return completed records, which the editor adopts for its search rows, previews and bulk baselines. Dirty comparison uses saved/draft values. The former response hash is retired, separate from the image's `media_version` and the generated Work record's `header.version`. [Lookup producers](../../studio/services/catalogue/catalogue_lookup.py)

Member rows sort by title, with numeric title parts in natural order. Click selects a Work, Shift-click selects a range, and Command-click toggles individual selections. The list uses exact Work IDs even when titles repeat.

## Create And Save

New Work defaults to the displayed Series, when one is open. The suggested Work ID is above the highest saved ID; a valid unused five-digit ID can be entered for an individual creation. Series, Title, Year and Year display are required, with Work ID additionally required in New mode. Confirming an image fills an empty New title from the filename stem. Source and saved data preserve authored text. Series changes in an open list do not silently overwrite the draft.

Save becomes available after a field change, an attachment selection or an explicit image confirmation. The browser validates the form and its loaded choices and sends the exact authored intent. Save returns completed canonical records and any incomplete local effects. The editor can adopt a saved Work even when media preparation fails. Repair that Work using its reported ID. [Write phase and recovery](Catalogue_Save_And_Refresh.md#save-boundary)

## Import A Project Subfolder

In New Work, choose **Open subfolder** and confirm one direct project subfolder. The batch uses its supported direct image files, shared authored fields and filename-stem titles. Save allocates consecutive five-digit Work IDs above the highest current ID, then prepares media. A repeated import can create another batch. Use the reported created IDs if local media work fails after canonical creation. The former Excel import is retired. [Batch save route](../../studio/services/catalogue/catalogue_write_service.py)

## Browse Galleries

Choose a Gallery by title or ID in the left-panel search. It shows direct member Works across Series. Expand the list to see Series. Gallery view keeps Series read-only and can show **Multiple Series** for a mixed selection. Switch to Series view to create a Work, change its Series or edit Series-wide Gallery relevance. Switching views preserves the draft.

## Gallery And Series Definitions

**New Series or Gallery** opens a definition dialog from the left panel. The Work form also offers **New Gallery**. **OK** saves the shared definition immediately. A Gallery created from the Work form adds a draft pill, with membership saved by the subsequent Work Save. A draft discard therefore leaves the saved definition available. A pill's × edits draft membership. Delete in Gallery Edit removes the shared definition.

Gallery New/Edit accepts Title, an optional single-line Description and a brush, video or book marker. The report displays these after Refresh. The same-type duplicate-title warning uses the loaded definitions and allows saving. Series and Gallery titles may coincide. The browser owns title completion and the exact loaded Series choice. In Series view **Relates to all works in this series** changes the explicit relevance pair. The Gallery's direct membership remains a separate choice. Gallery view preserves such pairs during title or presentation edits.

Use Galleries for editorial groups and the Work's Medium for descriptive text. **Add works…** searches saved Work title, ID or Medium and can populate an empty Gallery. Save or discard a dirty Work draft first. Checked selections persist across searches. **Add selected** saves the chosen memberships in one batch, preserving each Work's Series and other memberships.

## Bulk Editing

Bulk Save supports explicit changes to Series in Series view, Title, Year, Year display, Medium, Height and Width, Storage location, Gallery membership and the source-folder location. Untouched mixed values are preserved. Depth, filenames, individual images, downloads and links stay with individual editing.

Both views start with the intersection of selected Works' Gallery memberships. In **Series view**, editing the pills replaces the membership set of each selected Work. For `{A, B}` and `{B, C}`, adding `D` to the shared `{B}` yields `{B, D}` for both. In **Gallery view**, the browser applies only the pill additions and removals to each Work's saved memberships. Adding `D` in the same example yields `{A, B, D}` and `{B, C, D}`. This view sends per-Work replacements for the changed IDs. [Bulk write owner](../../studio/services/catalogue/catalogue_bulk_service.py)

### Relink Source Folder

After moving originals, use **Choose source folder** beside either folder field. The browser checks each selected Work's saved filename against the loaded destination and reports any missing IDs or filenames before accepting the location. Folder-only Save updates the source declaration and selected metadata without preparing another image. Use **Choose image** to confirm a different filename or regenerate the rendition set. [Work media](Catalogue_Save_And_Refresh.md#work-media-authoring)

## Delete

Work Delete confirms the exact saved Work or selected batch. It removes canonical Works and direct memberships, carries exact media descriptors and updates the displayed list. To finish removal, follow Refresh, Regenerate and Publish. Saved Work removal and an **empty Gallery** are distinct decisions. After a successful Work Save, the editor offers Delete or Keep for a newly empty Gallery identified from its saved membership map. An already empty Gallery remains available. A confirmed Gallery Delete removes its memberships and explicit Series relevance. Series Delete is available once no saved Works belong to that Series. [Updates queue](Catalogue_Save_And_Refresh.md#updates-queue)

## Media and runtime ownership

### Image Preview And Dimensions

**Choose image** uses the current draft folder, or the highest-ID cached Work with a folder in the displayed Series as a provisional starting point. Cancel leaves the draft intact. Confirm requests a temporary still WebP at up to 512px on its long edge, without generating persistent renditions. Original pixel dimensions fill initially blank physical fields using `round(pixels × 2.54 ÷ 300, 1)`. Existing or manually edited values, including a deliberate clear, take precedence. The loaded Work can display the 300dpi suggestion without another request.

### Persistent Media

The picker resolves the configured Projects original. Save prepares renditions and native downloads under Projects `catalogue/media-staging/`. The editor follows the supplied staging flags and media version for display. Refresh completes the handoff to `working/assets/works/`. Open resource labels in a new tab. **Edit** changes a managed download's label and **Add file** with the same normalized identity replaces its bytes. [Work media authoring and queue](Catalogue_Save_And_Refresh.md#work-media-authoring)
