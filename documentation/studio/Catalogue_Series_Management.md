---
draft: false
doc_id: d-20260422-000000-ec1a69
title: Catalogue Series Management
added_date: "2026-04-22 00:00:00"
last_updated: "2026-10-05 17:41:06"
parent_id: d-20260423-000000-d015e6

---
# Catalogue Series Management

Series management lives in the Work editor at `/studio/catalogue-work/`, Studio's sole page and direct entry point. The standalone Series editor route and its dedicated browser modules are retired, with no redirect or compatibility route.

The left-hand Series search selects the saved membership list. Choosing a member Work opens it for editing. Series membership remains the exact `series_id` on each Work; assignment changes use the Work editor's ordinary Save. Series and Gallery membership remain independent.

Edit and New live only beside the left-panel Series search; the main Work editor's Series search chooses membership. Edit opens the title modal for the browsed Series, and New opens an empty title modal. OK saves the Series immediately; Cancel discards the modal changes. Creation uses the next numeric ID suggested from a fresh canonical lookup. The newly created Series becomes the browsed selection and is assigned to the current new or existing Work draft. Work Save persists that assignment; bulk Series assignment remains read-only. Delete is inside Edit, available only for an empty saved Series, and uses confirmation and server-side revision/membership validation.

Canonical Series records contain `series_id` and `title`. See the [Catalogue Source Model](Catalogue_Source_Model.md) for the exact save, membership and output boundaries. Retired Series dates and ordering fields are not restored by the modal.

## Runtime Ownership

`catalogue-work-series-browser.js` owns browsing and action availability. `catalogue-work-series-modal.js` supplies Series title, creation and empty-Series deletion operations to the shared definition modal, and `catalogue-work-definitions.js` applies saved results to the live registry and Work draft. `catalogue-series-records.js` supplies search and next-ID suggestions. These modules use shared search, record-list and modal controls; they do not depend on the retired editor.

The existing Series read/create/save and Catalogue delete APIs remain active for these Work editor controls. `catalogue-editor-service-client.js` owns browser write transport; services under `studio/services/catalogue/` own revision checks, canonical validation and writes. [Catalogue output completion](Catalogue_Save_And_Refresh.md) refreshes affected local records and lookups. A later output failure preserves the canonical save or deletion and remains visible.
