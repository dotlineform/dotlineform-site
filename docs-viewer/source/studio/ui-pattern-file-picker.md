---
doc_id: ui-pattern-file-picker
title: File Picker
added_date: 2026-06-14
last_updated: 2026-07-15
parent_id: ui
viewable: true
---
# File Picker

Use File Picker to choose one or more files from a folder and one optional subfolder level. The caller supplies the meaning of the root and the functions that load available folders and files.

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
- select-all/deselect-all for multiple mode
- missing-selection and loader status inside the control
- validation and a structured selection on submit

The caller owns:

- modal or page composition
- the source-root and scope meaning
- `loadFolders` and `loadFiles` callbacks
- server authorization and path validation behind those callbacks
- mapping the returned folder, subfolder, filename, or filenames into route state
- dirty state, persistence, and workflow errors

Typing in folder search is transient. It must not mark a route dirty; only a confirmed selection should update durable draft state.

## Returned Boundary

The selection identifies `scope`, `folder`, `subfolder`, and either a single filename or a filename list. Exact option names, accepted loader record aliases, status text keys, and controller methods live in the two JavaScript modules above.

The component normalizes a few historical folder/file field names for current consumers. New adapters should use the direct `folder`, `subfolder`, and `filename` shape rather than extending the alias set.

## Method And Weak Spots

- The hierarchy is intentionally limited to a folder plus one optional subfolder. It is not a general filesystem browser.
- Custom listboxes provide consistent multi-select, wheel, and submit behaviour, but require focused accessibility and keyboard verification.
- Loader callbacks make the control reusable but can blur responsibility. API errors and security remain route/server concerns even when the component displays their message.
- The picker returns path parts, not proof that a file is safe or still exists. The server must validate again before a write.

## Verification

Protect:

- loader arguments and normalized results
- single- and multiple-selection output
- missing initial selections
- config text and validation messages
- route mapping from returned selection into draft/source fields
- server-side path and source-root validation

Use manual browser checks for listbox keyboard behaviour, wheel interaction, focus flow, and modal fit.
