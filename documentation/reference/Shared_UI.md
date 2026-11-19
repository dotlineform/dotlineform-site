---
draft: false
doc_id: d-20260505-181739-bb5223
title: Shared UI
added_date: "2026-05-05 18:17:39"
last_updated: "2026-11-19"
summary: Caller-owned state and reusable search, list and picker boundaries across Docs Viewer and Studio.
parent_id: ""
---
# Shared UI

Use `shared/frontend/js/` and `shared/frontend/css/` for reviewed browser primitives. The caller supplies domain records, loaders and callbacks, keeps durable form/query/selection state, and decides what a completed interaction means. Python owns the required filesystem reads, confinement, persistence and transfers behind those loaders and workflows.

## Choose A Component

| Need | Component | Current adoption |
| --- | --- | --- |
| Present an existing search input consistently | [Search field](#search-field) | Docs Viewer reader, collections and pickers; Studio Catalogue |
| Offer suggestions and commit an option | [Search list](#search-list) | Studio Catalogue selectors and File Picker |
| Show fixed columns and single-row actions | [Record list and actions](#record-list-and-actions) | Studio Series/member and resource adapters |
| Choose files or confirm a bounded loaded folder | [File Picker](#file-picker) | Studio project-media adapter |
| Choose a Projects directory at arbitrary depth | [Folder Picker](#folder-picker) | Docs Import |
| Generic checkbox/tree selection | [Selectable List](#selectable-list) | Retained source with no active route adapter |

These independent modules have no shared application store or server API. Adapt records at the caller, receive a component result, update the caller's draft and render from that draft. Transient focus, typing, highlighted options and navigation inside a picker are separate from a confirmed form value.

## Search Field

[`mountSearchField`](../../shared/frontend/js/search-field.js) wraps the same caller-owned input after it has been placed in its host. It preserves the input's identity, labels, attributes and existing listeners. The search icon focuses the field. Clear empties an editable field, restores focus and emits one ordinary bubbling `input` event; the caller's existing input handler owns filtering, debounce, route history and persistence.

[Field CSS](../../shared/frontend/css/search-field.css) owns the permanent underline, 20px focus icon, 16px clear artwork and clear visibility derived from the input's value/disabled/read-only state. A hidden clear button is absent from Tab navigation. Pointer activation preserves focus so a picker cannot restore its selected value on blur before Clear runs.

Docs Viewer and Studio supply text/muted colours and root-relative icon URLs through `--shared-search-*` properties. A relative URL inside a supplied CSS variable resolves against the consuming stylesheet, so the app supplies an explicit canonical route. Popup positioning remains with the caller or Search List. Ordinary form inputs and the Review package select retain their own styles.

## Search List

[`bindSearchList(input, popup, options)`](../../shared/frontend/js/search-list.js) owns listbox/combobox wiring, option acquisition through the injected loader, rendering, active-option navigation, commit/cancel and close/refresh/destroy. The caller owns matching policy, safe custom option HTML, loader/commit error feedback and the meaning of a selected value. The default filter is substring convenience; Catalogue and folder adapters supply their own policy.

Default selection mode can select on focus, commit the first result with Enter and restore the committed text on cancellation. `freeEntry: true` keeps ordinary editable text: focus preserves the caret, blur/Tab/Escape close without resetting, and Enter chooses only an option explicitly activated with Arrow keys. A supplied value accessor preserves the exact insertion string in this mode. Catalogue Medium updates the browser draft through its normal input/change handler while typing; choosing a suggestion carries the value through the same handler.

Close cancels pending option display. Keep that lifecycle with the mounted input and close it when replacing a draft or disabling the field. Hover/active appearance consumes the app's shared result colour; it does not choose selection semantics.

## Record List And Actions

[`createRecordList` and `createRecordListActions`](../../shared/frontend/js/record-list.js) render normalized rows/columns, optional single-row selection and an independent selection-aware action toolbar. The list owns pointer/keyboard selection, focus boundaries, update/destroy and its component event payloads. The toolbar registers as a focus boundary so moving from a row to an action retains that selection. The route owns row order, domain formatting, available actions, modals, confirmation, dirty state, mutation and Save.

Text formatters return a string; optional absence and literal whitespace belong to the column owner. `tooltipKey` supplies caller-prepared native title text independently of visible text, including line breaks. Link/image columns retain their URL-safety boundary. Icon columns supply an exact caller-owned class and accessible type label; icon actions supply an accessible button name. Text-only cell updates do not update icon columns. [Record CSS](../../shared/frontend/css/record-list.css) consumes supplied grid widths and colour roles.

For example, the [Work sections adapter](../../studio/app/frontend/js/catalogue-work-sections.js) maps resources into rows and supplies File/Link artwork. Editing an entry updates the browser Work draft; the shared list does not save that record or select its publication target.

## File Picker

[`createFilePicker`](../../shared/frontend/js/file-picker.js), its [configuration](../../shared/frontend/js/file-picker-config.js) and [CSS](../../shared/frontend/css/file-picker.css) own loaded-folder prefix search, one optional subfolder level, file listboxes, transient selection and submit feedback. The [project-media adapter](../../studio/app/frontend/js/catalogue-project-media-picker.js) supplies loaders and maps the returned `scope`, `folder`, `subfolder`, `filename`/`filenames` into the Work draft. Here `scope` is the picker's source-domain marker; it does not restore the retired Docs scope lifecycle.

Single and multiple modes choose files. Folder mode displays informational filenames and returns every loaded filename with the selected folder; it has no file checkboxes, thumbnails or selection events. Confirmation requires a successful non-empty load and, when requested, a direct subfolder. Superseded loads cannot enable submission for another folder. Exact filename case survives. The adapter carries this loaded membership forward to Save rather than listing again.

Typing a folder query does not dirty the Work. Confirming selection changes the draft; Work Save owns persistence and media processing. A seeded selected folder keeps suggestions closed during initial focus, while typing opens them normally. File identities are selection output; server-side source-root/path confinement remains at the actual file-read boundary.

## Folder Picker

[`createFolderPicker`](../../shared/frontend/js/folder-picker.js) and its [CSS](../../shared/frontend/css/folder-picker.css) navigate the configured Projects tree lazily by current directory, parent and direct children. It returns one current directory marker through `onSubmit({directory})` only after the injected response declares `current_selectable: true`. An empty selectable directory can be chosen. It never lists or selects files.

The [Import source owner](../../docs-viewer/runtime/js/import/docs-import-source-selection.js) retains the chosen source directory; the [management Import controller](../../docs-viewer/runtime/js/management/docs-viewer-management-import-controller.js) supplies the module and service handoff. The component expects the Projects root marker and `source_directory` child fields. The caller owns authorization/confinement, errors, remembered state, modal buttons/focus and the eventual import. Its controller exposes readiness, preferred focus, directory access, submit and destroy.

File Picker and Folder Picker serve different navigation and output needs. Compose or extend them only for a concrete workflow that needs both arbitrary depth and file selection.

## Selectable List

[`createSelectableList`](../../shared/frontend/js/selectable-list.js) and its [CSS](../../shared/frontend/css/selectable-list.css) retain id-based single/multiple selection, optional parent/child order, collapse, cascading and indeterminate state. No active production adapter currently imports the module. Current Collection Actions selection has its own [mounted report owner](Collections_And_Books.md); the ordinary Index has no checkbox selection.

Selectable List is retained for possible future reuse. Review its fit against the adopting workflow and its requirements before integrating it.

## Extension And Serving

Keep one-route decisions in that adapter. Share an interaction when real consumers have the same responsibility. An explicitly reviewed one-consumer exception can represent a cross-app domain, as with Projects navigation; it does not require manufacturing a second adopter. [Source Tree Ownership](../development/Development_Checklist.md#browser-javascript-and-source-documentation) owns the repository rule.

Docs Viewer explicitly serves Search Field and the local Folder Picker through its confined route map. Studio serves its shared frontend dependencies through its repository static boundary. The [public inventory](../../site-tools/config/site-code-update.json) currently projects only Search Field JS/CSS from this shared directory. Other components stay local unless explicitly adopted into that inventory. [CSS ownership](CSS_Ownership.md) and [public shell maintenance](Public_Docs_Route_Shell.md#maintenance) explain the remaining style and projection steps.

Exact options, event payloads and cleanup methods are code-owned. Test changes need a separately agreed specification under [Testing](../development/Verification.md); source inspection here does not establish interactive accessibility, focus feel or visual fit.
