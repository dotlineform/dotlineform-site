---
doc_id: ui-pattern-file-picker
title: File Picker Pattern
added_date: 2026-06-14
last_updated: 2026-06-14
parent_id: ui-catalogue
viewable: true
---
# File Picker Pattern

File Picker is the shared production control for choosing a file from a folder plus one optional subfolder level.

The shared assets are:

- behavior: `shared/frontend/js/file-picker.js`
- baseline styling: `shared/frontend/css/file-picker.css`
- component config: `shared/frontend/js/file-picker-config.js`
- browser import path: `/shared/frontend/js/file-picker.js`
- stylesheet path: `/shared/frontend/css/file-picker.css`

## Scope

Use File Picker when:

- the user is choosing one file, not editing path text directly
- folder search should be transient until a folder is selected
- the caller needs structured path parts: `folder`, `subfolder`, and `filename`
- the same picker behavior may be reused across Studio, Analytics, Docs Viewer, or other local app surfaces

The component is intentionally not named for projects.
Studio currently maps `folder` to `project_folder`, but another caller may map the same component to a different source root.

## Behavior Contract

The shared component owns:

- picker-specific defaults for labels, status text, search behavior, and subfolder display
- folder search with prefix matching
- Escape reset for the folder search popup
- one-level subfolder listbox
- parent-folder row at the top of the subfolder listbox, so selecting a subfolder is reversible without reselecting the folder
- file listbox
- mouse wheel selection inside listboxes without scrolling the page
- custom ARIA listbox focus and keyboard behavior
- Enter and double-click submit from the file list
- missing-current-file status inside the picker
- returning a structured selection only after submit

The consuming route owns:

- modal shell or page placement
- optional picker config overrides
- source-root meaning
- folder and file loader callbacks
- mapping returned `folder`, `subfolder`, and `filename` into route state
- page-level dirty state and save behavior

Do not mark a route dirty while the user types in the folder search.
Typing is reversible picker state; only confirming a file selection should update durable route draft fields.

The subfolder and file lists are custom listboxes, not native `<select size>` controls.
This keeps focus trapping, Tab order, arrow keys, wheel selection, and Enter behavior under the shared component's control across browsers.

The folder search input, subfolder listbox, and file listbox rely on accessible names rather than visible field labels by default.
The modal title and the selected folder row provide the local context.

## API

`createFilePicker(rootNode, options)` renders the picker into `rootNode`.

Supported options:

- `id`: stable id prefix
- `scope`: optional caller-owned root identifier
- `config`: optional picker-specific config created with `createFilePickerConfig(overrides)`
- `primaryNode`: optional submit button to enable or disable
- `initialSelection`: optional `{ scope, folder, subfolder, filename }`
- `loadFolders({ scope, query })`: returns folder records or strings
- `loadFiles({ scope, folder, subfolder, query })`: returns `{ subfolders, files }`
- `onSubmit()`: called when file-list Enter or double-click requests submit

The picker module also exports:

- `FILE_PICKER_DEFAULT_CONFIG`
- `createFilePickerConfig(overrides)`
- `filePickerText(config, key, tokens)`

Config sections:

- `text`: picker-specific strings such as `modalTitle`, `cancelButton`, `confirmButton`, `folderLabel`, status messages, and validation messages
- `search`: folder-search settings such as `maxFolderResults` and `openFolderSearchOnFocus`
- `subfolders`: parent row fallback label and subfolder prefix

Returned controller methods:

- `ready`: promise for initial folder/file loading
- `submit()`: validates and returns `{ selection }` or `{ ok: false, status }`
- `focus()`: focuses the folder search input
- `destroy()`: removes shared search-list listeners
- `getSelection()`: returns the current transient selection

Folder records may expose `folder`, `project_folder`, or `value`.
Subfolder records may expose `subfolder`, `project_subfolder`, or `value`.
File records may expose `filename`, `file`, or `value`.

## Current Consumers

- `studio/app/frontend/js/catalogue-project-media-picker.js`: adapts the generic picker to Catalogue Work source-image fields

The Studio adapter uses shared picker config for the file-picker modal title and action labels.
It should not map picker text through Studio's broad `ui-text` keys such as `entry_modal_cancel_button`.

The Work editor stores the confirmed selection as:

- `project_folder = selection.folder`
- `project_subfolder = selection.subfolder`
- `project_filename = selection.filename`

The page fields are read-only labels backed by hidden form values.
The modal is the only editing surface for those three fields.

## Verification

Shared component smoke:

```bash
$HOME/miniconda3/bin/python3 admin-app/tests/smoke/ui_catalogue_file_picker_modules.py --site-root .
```

Studio Work editor integration smoke:

```bash
$HOME/miniconda3/bin/python3 studio/tests/smoke/catalogue_project_media_picker_modules.py --site-root .
```

The shared smoke covers:

- existing folder, subfolder, and file preselection
- parent-folder row selection after selecting a subfolder
- prefix folder search
- one-level subfolder and file loading
- file listbox wheel selection
- Enter submit from the file list
- missing-current-file status
- component-owned config text independent of Studio `ui-text`

The Studio integration smoke covers:

- picker modal title and action labels coming from shared picker config, not Studio `ui-text`
- read-only page labels backed by hidden values
- modal-owned folder search
- no draft mutation while typing in the modal
- Escape reset inside the modal without closing the modal
- confirmed selection updating all three work draft fields
