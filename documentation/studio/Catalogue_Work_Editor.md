---
draft: false
doc_id: d-20260422-000000-45a776
title: Catalogue Work Editor
added_date: "2026-04-22 00:00:00"
last_updated: "2026-10-06 15:41:56"
parent_id: d-20260423-000000-d015e6

---
# Catalogue Work Editor

## What It Does

Use `/studio/catalogue-work/` to create, find, edit or delete canonical Works, including a batch from one project subfolder and images converted from former Details. Work downloads, links and project-media selection belong to this editor. The Detail browser and section-entry workflow are retired.

- `?work=<work_id>` opens one Work.
- `?mode=new` starts a new canonical record; optional `?series=<series_id>` preselects a Series.
- Explicit IDs, numeric ranges or a mixture open bulk edit mode.

The [Catalogue Source Model](Catalogue_Source_Model.md) owns the data boundary. Ordinary Save completes the canonical edit and required local media; [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the separate generated-reader boundary.

## Create And Save

The Work search and New, Save and Delete icon buttons share the top toolbar inside the editor panel. Press Enter or choose a search result to open a Work; there is no separate Open button. Save status remains below the toolbar. The Refresh Catalogue icon sits in the Catalogue Work Editor header row, aligned with the Work search, with its freshness/result message to the right. The Series member list, editor and preview panels align at the top, with the preview stacking below the editor when its available width is narrow.

In the member list, click selects one Work, Shift-click selects a continuous range, and Command-click adds or removes individual Works. The selection field compresses consecutive IDs into ranges, for example `01981-01983, 01985`. Selecting one Work uses the normal editor; selecting multiple Works opens bulk Gallery editing.

The right-chevron control in the member list's top-right corner expands the list, moves the editor to the right and hides the preview. It becomes a left chevron to restore the normal layout. At full desktop width the editor keeps its original width and the list takes the released preview space. Expansion remains selected while opening and saving Works, and resets when the page reloads. Toggling changes presentation only: the mounted list, scroll position, selection and unsaved draft remain intact. New and empty editor states continue to omit the preview when the list is restored.

Expanded view adds a Galleries column with comma-separated titles, wrapping and vertical centring. Two lines fit the normal thumbnail row; additional lines increase its height. The column shows saved memberships. After Save, affected Gallery cells update in place while retaining mounted rows/thumbnails, selection and the visible scroll anchor. Series reassignment may refresh the list.

New mode shows the editable form and Save. The suggested Work ID can be replaced with any valid unused ID, including a deleted ID. The suggested ID and any preselected Series form the initial draft baseline and do not count as edits. Selecting a Work from the member list immediately after New opens it without a discard prompt. Actual field changes, pending attachments or confirmed image regeneration trigger the existing selection-change confirmation; Cancel retains the draft. The Work ID field's × is labelled **Cancel new Work**: it immediately discards the unsaved Work draft and pending attachments, removes `mode=new` from the URL and returns to empty Work search with focus in the search field. Typing or manually clearing the Work ID keeps New mode active. The × is disabled while Save, Refresh or Delete is busy. Secondary controls appear after the first successful save.

Field labels use the normal text colour; required fields also have bold labels and expose their requirement to assistive technology. Series, Title, Year and Year display are required when creating or individually editing a Work, so their labels stay bold in both modes. Work ID is additionally required in New mode. Missing values keep Save disabled and block Enter-to-save without missing-field prompts. Invalid values, duplicate Work IDs and save failures retain visible messages. The Series search keeps its existing `find series by title` placeholder. Bulk mode retains saved required fields as read-only and permits Gallery membership editing.

Search uses the live canonical Studio Work search projection. Opening a Work loads its exact canonical record, server-issued revision and related context from the local API. The source record remains the editable baseline.

Save remains disabled for an unchanged draft, including immediately after loading a Work or completing Save. In single/New mode, restoring the draft's initial or saved values disables it again; pending attachments and confirmed image regeneration remain changes independently of field values. Save validates the form and sends the changed record with its revision. The service rejects a stale revision, validates canonical integrity, writes through the source transaction owner and completes required local media. It returns current canonical records and revisions so the editor stays current without generating Catalogue reader JSON or private Docs metadata. If media or a later editor refresh fails, the saved canonical change remains complete and the message identifies the incomplete step.

The pointer shows waiting throughout the Work editor while Save runs, returning to normal on completion or failure. Work search/New, list selection and editing controls follow the operation's busy state. Save success and unsaved-change messages remain visible through the normal status owner.

A Work must belong to exactly one Series. Selecting another Series reassigns it; clearing the required membership cannot be saved. The Work editor's Series field is a search input for choosing membership. Both Series searches display titles only in their selected values and results, with the same popup and result-row styling. The bulk summary also displays Series titles. Series Edit and New live only beside the left-panel Series search. Membership does not assign a document subject, parent or destination.

There is no Work publication state, Publish/Unpublish action or Catalogue Drafts route. Save and Refresh Catalogue are separate awaited actions; there is no media-publish control. Refresh reconciles generated Catalogue readers and private Docs metadata, without publishing documents. The local API must be available; browser edits are not queued for offline saving.

## Import A Project Subfolder

In New Work mode, the **Open subfolder** icon button beside project subfolder opens the shared **Select folder** modal. It uses the same folder-open artwork and icon-button styling as Choose image; its tooltip and accessible label remain **Open subfolder**. Choose a project folder and one direct subfolder. The existing file list shows every supported direct image as read-only filename text. **OK** remains unavailable during loading, after failure, for the project parent or for an empty subfolder. Cancel leaves the draft unchanged. Source originals stay in their configured Projects or Processing locations.

Confirmation retains the loaded filenames internally and updates the existing folder fields. It adds no pending list, count or confirmation. Work ID and Title become read-only placeholders because each Work gets a server-assigned ID and its own filename-stem title. Series, Year and Year display remain required; Galleries and other form metadata apply to every addition. Choosing an individual image returns to ordinary single creation; changing media source releases the pending batch. Cancel new Work and normal draft-discard protection also release it.

**Save** makes one awaited batch request. The server orders exact filenames deterministically, assigns consecutive five-digit Work IDs starting one above the highest current canonical Work ID and validates all shared records and memberships before one combined canonical transaction. Lower unused IDs may be reserved, so batch creation leaves those gaps untouched; fill one deliberately through ordinary single-Work creation when needed. An empty Catalogue starts at `00001`; a batch that would exceed `99999` fails before writing and does not fall back to gaps. Save then completes normal primary renditions and thumbnails for all created Works. The confirmed list defines membership through Save: no second directory listing occurs, new files require reopening the picker, and missing/unreadable images produce visible incomplete media completion after canonical creation. Source names remain exact, including case differences and surrounding spaces; path confinement and symlink rejection still apply when images are accessed.

Successful creation adds every returned Work to the live editor search and member-list data and opens the first Work for individual editing. Canonical success releases the pending creation batch even if media or editor completion fails. The failure names the created IDs and unfinished step; correct the cause and use ordinary individual Work editing or confirmed image regeneration. The editor never automatically recreates the batch. Validation errors before persistence retain it. If the response is unavailable, the editor reports an unconfirmed outcome; inspect canonical Works before another user-initiated batch Save.

Every import includes every supported direct image, including a repeated import of the same folder. There is no duplicate-image detection, source-path comparison, hash or import ledger. Track completed imports with the existing reports. Refresh Catalogue remains a separate action.

## Gallery And Series Definitions

Gallery pills and search results display titles only. The Gallery dropdown shares the Series dropdown's popup and result-row styling.

New beside the Gallery field or the left-panel Series search opens a New modal with OK and Cancel. Clicking a Gallery pill's title or the left-panel Series Edit opens an Edit modal with OK, Cancel and Delete. Series Edit targets the browsed Series. Delete is inside Edit. Edit never changes into New.

OK saves the shared definition immediately and updates the editor's live canonical views. Creating a Gallery adds its pill to the current Work draft. Creating a Series selects it in the left-panel browser and assigns it to the current new or existing Work draft; bulk Series assignment remains read-only. Work Save persists the assignment, including the existing bulk Gallery replacement semantics. Cancel before OK creates nothing. Discarding the Work draft after OK leaves the saved definition available, potentially unassigned. Title editing changes the shared definition without changing draft membership. Generated readers update on Refresh Catalogue.

The Gallery pill's × only removes membership from the current draft. Delete inside Edit confirms the number of saved associated Works and removes the Gallery definition and all canonical memberships together. The list, loaded saved memberships and draft drop the deleted ID while retaining other unsaved edits. Refresh Catalogue later updates affected generated Works and indexes and removes the deleted Gallery JSON; no subsequent Work Save is required. A failure after canonical persistence is reported as incomplete local completion rather than an unsaved deletion.

Series Delete is disabled with an explanation while saved Works belong to the Series. The service checks membership again when applying deletion. Deleting an empty Series clears any unsaved assignment to it in the current Work draft. Other bulk fields, including Series assignment, remain read-only.

## Bulk Editing

Gallery membership is the only editable field in bulk mode, whether selection comes from list rows or the ID/range search. Other Work fields are read-only; download, link, media and delete controls are unavailable.

The Gallery picker initially shows the intersection of the selected Works' memberships. Editing that pill set and saving replaces every selected Work's memberships with the final set. For Works in `{A, B}` and `{B, C}`, the picker shows `{B}`; adding `D` and saving gives both Works `{B, D}`. Works in `{A}` and `{B}` show no initial pills; adding `D` and saving gives both Works only `{D}`.

Removing all displayed pills and saving clears the selected Works' memberships. There is no dedicated clear-all control. Save is disabled until an explicit Gallery membership edit, so an untouched selection retains differing saved memberships. Changing the selected Work set discards unsaved bulk edits; expansion/collapse and focus within the editor preserve them. Normal single-Work unsaved-change protection remains.

Bulk Save uses one request and one combined canonical transaction. Each selected Work supplies its metadata revision and, when replacing Galleries, its independent loaded membership set. A stale Work or membership rejects the whole replacement before writing. The service writes the membership map once and completes required local media through the same owner as single-Work Save. Returned saved memberships and current revisions refresh the editor/list; Gallery-only editing does not regenerate unchanged images. Generated reader memberships update on Refresh Catalogue.

## Delete

Work deletion uses a server preview and confirmation, then repeats validation and checks the Work revision before applying. It deletes the canonical Work and its Gallery membership entry in the same transaction. The editor then removes the deleted Work from its live search and Series member list, updates the member count, and clears the Work selection, form, preview and Work URL parameter without reloading the page. The selected Series and expanded-list layout remain in place, including when the last member is deleted. A confirmed canonical deletion with incomplete local completion still clears the deleted Work and displays the completion error. Cancellation or an unconfirmed deletion leaves the current Work selected. Refresh Catalogue later removes its generated record and updates indexes and former Series/Gallery memberships. Shared or remote media cleanup is separate. Deletion does not write retired Detail storage.

The 2026-10-06 deletion-state correction passed focused JavaScript lint for `catalogue-work-actions.js` and repository whitespace checks. Bounded source/diff review traced confirmed deletion through the live maps, empty Work state, retained Series browser, member count, preview/layout and final busy-state release; no findings remained. Cancellation, last-member deletion and incomplete local completion received source review only. No tests, browser automation or real Work deletion ran; manual interaction confirmation remains with the user.

Subfolder batch creation uses New Work mode; saved bulk editing remains limited to Gallery memberships. Shared file-picker, record-list, modal and media-preview components remain available without restoring Detail-specific browsers, modals or services.

## Media And Runtime Ownership

The media picker resolves the Work's configured source, folder, optional direct subfolder and filename. Empty folder, subfolder and filename values display as plain `—` placeholders with no hover underline. The server validates paths without exposing absolute filesystem locations. Catalogue staging uses `catalogue/media-staging/` beneath the configured Projects base. Save prepares required primary renditions and thumbnails in shared Docs `assets/works/`. The preview uses the saved Work's media version; an unavailable image is reported separately from missing preview configuration.

Browser modules under `studio/app/frontend/js/` divide the route into fields/form, selection, actions, record state, resources and media picking. `catalogue-editor-service-client.js` owns transport; `studio_catalogue_api.py` dispatches to the focused services under `studio/services/catalogue/`. Field definitions and current code own the exact editable inventory.

The editor reuses saved SVG artwork from `docs-viewer/static/icons/`, served by the existing Studio server. `studio.css` owns its theme-aware mask and icon-button presentation; `studio-icon.js` supplies decorative spans for generated fields. Resource actions and type cells use the shared record list's opt-in icon rendering. The [Works Editor Mapping](Works_Editor_Icon_Mapping.md) records the approved artwork and retained text controls. Modal actions, Gallery pill labels and media-source names remain text.

The three panels are siblings in one named CSS grid. `catalogue-work-layout.js` owns the expansion choice, preview visibility and toggle accessibility; the summary renderer supplies whether preview content is available. `studio.css` owns the column tracks, expanded-only Gallery cells and narrower-window stacking. Layout changes do not calculate widths in JavaScript or rebuild panel contents. The shared record list owns opt-in multiple selection and exact-ID text-cell updates; the Work editor owns the membership intersection, draft intent and save response handling. Normal and expanded layouts use the same row dataset. Gallery titles resolve through the already-loaded canonical registry from IDs added to the live Work search response.

The shared [Route Ready State](Route_Ready_State.md) is exposed on `#catalogueWorkRoot`. The retained Catalogue smoke is scoped to route/service boot; UI acceptance remains manual. Mutation test work follows the separately agreed [test specification](Test_Contract_Discipline.md).

[Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns local Save completion, Refresh status and reader timing after the canonical transaction. The editor combines single and bulk state with Work resources and media context, so new responsibilities should use their existing focused owners.
