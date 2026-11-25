---
draft: false
doc_id: d-20261125-221928-22f5e0
title: Docs Viewer Saved Search Results
added_date: "2026-11-25 22:19:28"
last_updated: "2026-11-25"
summary: Accepted Manage workflow for saving and reopening ordered document lists, including the 65-document Library review list.
ui_status: done
parent_id: d-20260602-160839-6d3cbb
---
# Docs Viewer Saved Search Results

Closed on 25 November 2026 after the user accepted the Manage workflow and approved closeout following the ten-row picker and matching X button refinements. [Current saved results workflow](../reference/Reader_Discovery_And_Return.md#saved-results-in-manage)

The **Saved results** icon button follows **Recent** at the right end of the Manage Index Search row. Its modal opens a saved document list, saves the current Search results to a new file, or deletes a selected saved list. A loaded list appears in the Index results panel and supplies the order for **Previous** and **Next**. Selecting a row opens the current Working document, so editorial changes are visible when that document is reopened. [Existing Search result navigation](Docs_Viewer_Search_Result_Navigation.md)

## Manage Workflow

Search, the scope control, Recent and Saved results occupy one row. The new button uses `list-plus.svg` at the existing icon-button size and has the accessible name **Saved results**. The loaded list header uses the compact X from pinned Related Links, with **Close list** as its accessible name. [Icon asset](../../docs-viewer/static/icons/list-plus.svg) · [Index header layout](../../docs-viewer/static/css/docs-viewer.css#L208)

The first browser check found that the four controls aligned at 20rem, with about 103px available for the placeholder text. The implemented Manage Index uses 21rem and reclaims the Clear-button padding while the Search field is empty. At a 1024px viewport, **Search Living Memory** had about 143px of text space and the document pane measured 356px. The controls stayed aligned with a query and **Clear search** visible. [Manage stylesheet](../../docs-viewer/static/css/docs-viewer-manage.css#L5)

| Action | Result |
| --- | --- |
| **Load** | Pick a named JSON file from the modal's ten-row scrolling list and show its documents in array order. Show the list name in the results panel. The current document stays open until a row is selected. |
| **Save as new** | Name a new file and save all document matches from the current live Search in ranked order, including matches beyond **More**. Gallery results use their Media View action. A name already in use prompts the user to choose a new name. |
| **Delete** | Confirm the selected name and remove its JSON file. If that list is loaded, close it and remove its navigation while keeping the current document and reading position. |

Starting a live search, closing the loaded list or loading a different list ends the old navigation sequence. Collapsing the Index keeps the active list and its arrows available. Browser Back can restore a document's arrows while the invoking list is still active. [Reader discovery and return](../reference/Reader_Discovery_And_Return.md#search-previous-and-next)

## File Format And Storage

Store one UTF-8 JSON file per list in `working/source/saved-searches/` beneath the configured Docs workspace. The filename gives the list its name and the array gives it its reading order. Each row has a unique exact document target and a display title. A named-collection row carries `collection`. An ordinary row carries `doc_id` and `title`. List discovery reads the filenames when the modal opens, so a hand-written file appears there after it is saved in this directory. The directory falls within the private Docs workspace Git backup scope. [Workspace storage](../reference/Source_Organisation.md#storage-and-roles) · [Private backup scope](../../docs-viewer/services/docs_publish_backup.py#L10)

```json
[
  {
    "collection": "library",
    "doc_id": "d-20261017-112353-93c738",
    "title": "100 Words Related to Reflection & Memory"
  }
]
```

## First Review List

The first saved list is `library-mostly-list-shaped.json`. Its rows come from the workbook's **Library** sheet where **Majority pattern** in column H is exactly `Mostly list-shaped`. The one-off extraction used **Document ID** from column J, **Library document** from column A, and `collection: library`, preserving the workbook's top-to-bottom order. [Library editorial review workbook](../_working/Library_Editing/Library_Editorial_Review.xlsx) · [Editorial scan context](../_working/Library_Editing/Library_Editorial_Review.md#h2-section-scan)

The source check found 65 matching rows among 433 Library documents. All 65 have distinct valid document IDs and populated titles, and all 65 IDs are present in the Working Library manifest. Of the 65, 25 have H3 promotions. The initial list includes the entire `Mostly list-shaped` group. [Working manifest contract](../reference/Generated_Data_Contracts.md#collection-manifest-ownership)

The list opens with *100 Words Related to Reflection & Memory* and ends with *ZFC — The Baseline Foundation of Modern Mathematics*. From entry 50, *Probabilistic Synaptic Release*, **Next** reaches entry 51, *Quantum Computers - Hardware size and complexity*, while the panel still shows the first batch. [Library editorial review workbook](../_working/Library_Editing/Library_Editorial_Review.xlsx)

## Readiness And Implementation Boundaries

| Area | Implementation decision |
| --- | --- |
| Manage browser | Register the button and modal in Manage. Reuse the management modal shell and maintain one active loaded list in the Index. Use the already-ranked live document matches for **Save as new**. [Manage modal shell](../../docs-viewer/runtime/js/management/docs-viewer-management-modal-shell.js#L82) · [Index views](../../docs-viewer/runtime/js/shared/docs-viewer-view-registry.js#L215) |
| Shared reader | Give rendered document rows from either kind of results the existing exact-target links and navigation sequence. Carry the list order through paging and use its lifetime for footer removal and Back. Keep search matching with the live Search controller and open only the selected document through the reader route. [Search controller](../../docs-viewer/runtime/js/shared/docs-viewer-search-controller.js#L145) · [Reader route](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js#L95) |
| Local service | Resolve the one configured directory. List saved filenames, read and parse the selected file, create one new file, or remove the confirmed file. Use the management gate for reads and writes. Validate the selected filename, path confinement, and the JSON row identities at this boundary. A malformed hand-written list reports which file needs correction and leaves the displayed results in place. [Management endpoint boundaries](../reference/Endpoint_Overview.md#service-and-dispatch) · [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json) |
| Deliverable and evidence | Place the extracted 65-document JSON in the configured private directory once the format and load path are in place. Document the shape and workflow in the reader reference and guide. If a represented shared module changes, project that change and verify the Public reader. [Development checklist](../development/Development_Checklist.md) · [Public projection](../development/Verification.md#docs-viewer-site-code-projection) |

## Implementation And Completion Gates

- [x] Verify the workbook selection, exact identities and availability in the Working Library manifest. Review the existing result navigation, private storage and Manage modal owners.
- [x] Implement the Manage modal, selected-file operations and loaded-list sequence through the existing reader. Update the reference and reading guide. [Current workflow](../reference/Reader_Discovery_And_Return.md#saved-results-in-manage)
- [x] Create `working/source/saved-searches/library-mostly-list-shaped.json`. Read it back through the saved-list service and compare all 65 targets, titles and order with the workbook rows. Load it through the Manage modal.
- [x] Run focused lint for six JavaScript and five Python modules. Inspect the three projected shared modules. `bin/site-code-update --check` and `bin/site-validate` passed. [Projection and validation](../development/Verification.md#docs-viewer-site-code-projection)
- [x] Exercise the Manage workflows. Keyboard-open item 50 of the Library list and use **Next** to reach item 51 before expanding **More**. Verify Back with the list active and after closing it. Save a live Concepts Search with 208 matches while only 50 rows are visible, reopen all 208, and verify duplicate-name rejection. Load a separately authored list in file order, including an ordinary and a named-collection document. Cancel and confirm deletion on disposable lists, and verify that deleting the loaded list preserves the displayed document. The temporary lists were removed.
- [x] Check the Manage header at 1024px and check Public through `site-preview`. Public Search and its document navigation worked and the Saved results button was absent.
- [x] Check the ten-row picker with the two existing saved lists, including keyboard selection, Load and Delete targeting. Check that the compact X matches the pinned panel control and that keyboard activation closes the list, restores Search focus, and leaves the document open. JavaScript lint, shared projection and site validation passed after the X change.
- [x] Record user acceptance and closeout on 25 November 2026.

## Implementation Code Review

- The browser captures the already-ranked display records and supplies one list order to the shared row and footer owners. The saved list remains a tab-local view. Closing or replacing it invalidates the order at the existing footer projection point, including for retained Back. Committed document deletion can remove that row from the open view. The JSON remains the user's saved membership and order. [Shared results controller](../../docs-viewer/runtime/js/shared/docs-viewer-search-controller.js)
- The service lists filenames on modal open and parses only the chosen UTF-8 JSON file on Load. It validates exact row identity and uniqueness once at the intake boundary. Configured source path resolution rejects symlinks, and names select one direct child. Save reuses the atomic create-only helper. Delete removes the confirmed selected file. The regular document reader resolves each selected target when opened. [Saved list service](../../docs-viewer/services/docs_saved_searches.py) · [Management endpoint boundaries](../reference/Endpoint_Overview.md#service-and-dispatch)
- The Manage entrypoint contributes the modal, stylesheet and icon. The shared projected runtime receives only the result-list handoff. Saved files sit in the existing private workspace backup scope and never enter discovery generation or published artifacts. The filename option carries its exact value, including internal spaces. [Manage entrypoint](../../docs-viewer/runtime/js/management/docs-viewer-manage.js) · [Private backup scope](../../docs-viewer/services/docs_publish_backup.py#L10) · [Code review checklist](../development/Development_Checklist.md#redundancy-and-defensive-behavior-review)

## Acceptance And Release

The picker check exercised its ten-row height with two saved lists. Scrolling with more than ten saved files was outside the observed browser cases. The shared runtime changes are projected into the tracked site snapshot. Public deployment is a separate action. A running Manage instance picks up the new endpoints after service restart and may need a hard reload for cached app assets. [Local app caching](../reference/Docs_Viewer_Runtime.md#local-http-caching) · [Publish and deploy](../guide/Publish_And_Deploy.md)
