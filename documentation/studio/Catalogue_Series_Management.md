---
draft: false
doc_id: d-20260422-000000-ec1a69
title: Catalogue Series Management
added_date: "2026-04-22 00:00:00"
last_updated: "2026-10-24"
parent_id: d-20260423-000000-d015e6

---
# Catalogue Series Management

Series management lives in the Work editor at `/studio/catalogue-work/`, Studio's sole page and direct entry point. The standalone Series editor route and its dedicated browser modules are retired, with no redirect or compatibility route.

The left-hand Series search selects the saved membership list. Choosing one member Work opens it for editing; Shift-click or Command-click selects multiple Works from that same Series for bulk editing. Work ID search opens one Work at a time. Series membership remains the exact `series_id` on each Work; assignment changes use the Work editor's ordinary Save. Choosing another Series in a bulk draft applies it to every selected Work on Save, removes moved Works from the displayed list and retains the browsed Series. Empty Series remain available. [Catalogue Work Editor](Catalogue_Work_Editor.md#bulk-editing) owns the exact selection and Save behavior. Series and Gallery membership remain independent.

Edit and New live only beside the left-panel Series search; the main Work editor's Series search chooses membership. Edit opens the title modal for the browsed Series, and New opens an empty title modal. OK saves the Series immediately; Cancel discards the modal changes. Creation uses the next numeric ID suggested from the loaded Series map. The newly created Series becomes the browsed selection and is assigned to the current single/New Work draft; bulk assignment uses the Work editor's Series field. Work Save persists the assignment. Delete is inside Edit and available only for an empty saved Series, checked in the UI's complete saved Work map before confirmation.

Canonical Series records contain `series_id` and `title`. See the [Catalogue Source Model](Catalogue_Source_Model.md) for the exact save, membership and output boundaries. Retired Series dates and ordering fields are not restored by the modal.

## Runtime Ownership

`catalogue-work-series-browser.js` owns browsing and action availability. `catalogue-work-series-modal.js` supplies Series title, creation and empty-Series deletion operations to the shared definition modal, and `catalogue-work-definitions.js` applies saved results to the live registry and Work draft. `catalogue-series-records.js` supplies search and next-ID suggestions. These modules use shared search, record-list and modal controls; they do not depend on the retired editor.

The existing Series read/create/save and Catalogue delete APIs remain active for these Work editor controls. `catalogue-editor-service-client.js` owns browser write transport; services under `studio/services/catalogue/` own request/target boundaries, canonical persistence and known-effect completion. Authoring and membership validation stay in the browser. [Catalogue output completion](Catalogue_Save_And_Refresh.md) carries saved Work effects into the separate Refresh lifecycle. A later completion failure preserves the canonical save or deletion and remains visible.
