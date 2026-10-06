---
draft: false
doc_id: d-20260614-155753-e87844
title: File Picker
added_date: "2026-06-14 15:57:53"
last_updated: "2026-10-06 15:11:00"
parent_id: d-20260505-181739-bb5223

---
# File Picker

Use File Picker to choose one or more files, or confirm a loaded folder, from a folder and one optional subfolder level. The caller supplies the meaning of the root and the functions that load available folders and files.

## Authority

- behaviour: `shared/frontend/js/file-picker.js`
- defaults and text: `shared/frontend/js/file-picker-config.js`
- styles: `shared/frontend/css/file-picker.css`
- current adapter: `studio/app/frontend/js/catalogue-project-media-picker.js`

Search imports from `/shared/frontend/js/file-picker.js` for the current consumer set.

## Stable Structure

`createFilePicker(root, options)` owns:

- prefix search across loaded folders
- a parent row and one level of subfolders
- custom keyboard/mouse listboxes
- single- or multiple-file transient selection
- explicit folder confirmation with read-only filename rows and the complete loaded filename list
- select-all/deselect-all for multiple mode
- missing-selection and loader status inside the control
- validation and a structured selection on submit

The caller owns:

- modal or page composition
- the source-root and scope meaning
- `loadFolders` and `loadFiles` callbacks
- server authorization and path validation behind those callbacks
- mapping the returned scope, folder, subfolder, filename, or filenames into route state
- dirty state, persistence, and workflow errors

Typing in folder search is transient. It must not mark a route dirty; only a confirmed selection should update durable draft state.

## Returned Boundary

The selection identifies `scope`, `folder`, `subfolder`, and either a single filename or a filename list. Exact options, status text keys and controller methods live in the two JavaScript modules above. Loaders return strings or direct `folder`, `subfolder` and `filename` records; initial selection uses those same names. Adapters map service-owned field names explicitly. Historical record and initial-selection aliases are removed.

`selectionMode: "folder"` shows filenames as informational text rows with no file-selection events, checkboxes, toolbar, thumbnails or image previews. Confirmation requires a successfully loaded non-empty folder, and `requireSubfolder: true` additionally requires a direct subfolder. Loading, empty results and failures disable confirmation and are also rejected by `submit()`. Each loader result belongs to its requested navigation; a superseded result cannot enable confirmation for a different folder. Exact names and case distinctions are preserved.

Folder confirmation returns a copy of every loaded filename. The caller retains this list for subsequent Save without another listing request. This defines membership, while the server still confines and validates the exact files when reading them. The Catalogue Work Editor uses this mode through the current adapter and retains ordinary single-file selection for Choose image.

## Relationship To Folder Picker

[Folder Picker](Folder_Picker.md) navigates the Projects-root directory tree and returns one current directory marker. File Picker searches a loaded folder set, exposes one optional subfolder level, and selects one or more files. Neither component is a base class or replacement for the other.

Keep the Works Editor adapter on File Picker while it needs bounded project folder/subfolder selection and file or loaded-folder confirmation. Consider composition with Folder Picker only when a concrete workflow needs arbitrary-depth directory navigation; do not migrate Works Editor merely to reduce the number of shared components.

## Method And Weak Spots

- The hierarchy is intentionally limited to a folder plus one optional subfolder. It is not a general filesystem browser.
- Custom listboxes provide consistent multi-select, wheel, and submit behaviour, but require focused accessibility and keyboard verification.
- Loader callbacks make the control reusable but can blur responsibility. API errors and security remain route/server concerns even when the component displays their message.
- The picker returns path parts, not proof that a file is safe or still exists. The server must validate again before a write.
- No direct focused module test currently imports `createFilePicker()`. Establish the documented loader, selection, and controller baseline before changing its hierarchy, aliases, or Works Editor integration.

## Verification

Protect:

- loader arguments and normalized results
- single-, multiple- and folder-selection output
- missing initial selections
- config text and validation messages
- route mapping from returned selection into draft/source fields
- server-side path and source-root validation

Use manual browser checks for listbox keyboard behaviour, wheel interaction, focus flow, and modal fit.
