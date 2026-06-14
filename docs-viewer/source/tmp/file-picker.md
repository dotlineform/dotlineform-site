---
doc_id: file-picker
title: "emoji"
added_date: 2026-06-14
last_updated: 2026-06-14
ui_status: draft
parent_id: ""
---

> in the select file modal, we could replace the 'project folder' label with the project folder search field.
- for an existing work, all the controls would pre-select the current folder, subfolder, file.
- for a new work, the controls would be be blank until the user searches for a folder
- the project folder, subfolder and filename controls on the page would all become non-editable labels.
- the modal would return the full file path to populate all the labels.

The main tradeoff is that the modal becomes the single editing surface for all three fields, which is probably what you want if the real task is “choose a file”.

A few things to watch:

- Existing work: preselecting folder, subfolder, and file is straightforward if the current folder still exists and the file is returned by the project-file API. If not, the modal needs a clear “current file not found” state.
- New work: blank until folder search is fine. The file list should stay empty/disabled until a folder is selected.
- Page fields as labels: good simplification. But there still needs to be a visible way to clear/reset the selection, unless choosing another file is the only reset path.
- Subfolder: if no subfolder is selected, file list should mean “files directly in project folder”. That matches the current behavior.
- Unsaved changes: typing in the folder search inside the modal should not dirty the form. Only confirming a file selection should update the draft.
- Keyboard flow: after folder selection, focus should move predictably to subfolder or file list. For the common case, probably folder search -> file list.

The modal framework should support this. It already hosts dynamic forms, listboxes, buttons, status text, focus handling, and async loading. A folder search inside it is not inherently a problem.

The cascading CSS risk is real but manageable if we avoid reusing page-level layout classes too freely. I’d treat the modal as its own component surface:

- keep modal-specific wrappers like `catalogueProjectMediaPicker__...`
- reuse the shared search-list JS behavior, but allow modal-specific class hooks
- do not rely on `.tagStudioForm__field` grid layout inside the modal unless we actually want that grid
- keep dimensions explicit for the two listboxes so adding/removing labels/search controls doesn’t shift the layout

So: not tricky in principle, but it should be implemented as one cohesive picker component, not by dropping the page’s project-folder field directly into the modal.

> yes, it is entirely possible that a folder/file no longer exists. I hope they do, but it is possible! so the modal would open blank and probably need to display a message 'file not found' and do its best at displaying the folder if that exists. otherwise blank as if a new record.
yes, if this becomes a self contained file picker, it can be used on work detail, moments, and probably analytics-app data sharing, and probably later on docs-viewer. so it would be a useful component.

That makes sense. I’d model it as a reusable “project file picker” component, with the catalogue work modal as the first integration.

Behavior I’d aim for:

- Input value is a structured selection:
  - `project_folder`
  - `project_subfolder`
  - `project_filename`
- Modal owns all editing.
- Page fields become read-only display labels plus one folder/file button.
- Confirming the modal returns the structured selection.
- The caller decides how to store it in its draft fields.

Missing-current-file handling:

- If folder exists and file exists: preselect folder, optional subfolder, and file.
- If folder exists but file does not: select folder/subfolder if possible, show `file not found`, leave file list with available files.
- If folder does not exist: show `file not found`, start with blank folder search and disabled/empty listboxes.
- If subfolder no longer exists: select folder, show `file not found`, leave subfolder blank and show direct folder files.
- If only filename exists in another subfolder, I would not auto-search across subfolders at first. Too much hidden behavior.

Component shape:

- `shared/frontend/js/project-file-picker.js`
- `shared/frontend/css/project-file-picker.css`
- Depends on shared `search-list.js`
- Accepts callbacks:
  - `loadProjectFolders(query)`
  - `loadProjectFiles({ projectFolder, projectSubfolder, query })`
- Accepts initial selection.
- Returns `{ confirmed, selection }`.

I’d keep the “missing current file” message inside the modal as local picker status, not the page-level editor status. It’s picker-local feedback and should disappear when the modal closes.

This is a good shared component candidate. It has real behavior, keyboard/focus state, async loading, and structured output. That is exactly the kind of thing worth centralizing rather than cloning route by route.

> for later reuse, we might need to be flexible about 'project' folder. the assumption we have in studio is that project folder is under `DOTLINEFORM_PROJECTS_BASE_DIR/projects`, but for other uses, it might be under `DOTLINEFORM_PROJECTS_BASE_DIR/<anything>`. However, for the picker we keep the scope to just one level of subfolders to enforce simple file organisation.

Agreed. The reusable component should not hard-code “projects” as the root concept.

I’d name the generic concept something like `baseScope` or `rootKey`, and let the host app/API decide what that means:

- Studio work editor passes scope/root: `projects`
- A future docs-viewer use might pass `docs`, `imports`, `archive`, etc.
- Analytics data sharing might pass whatever source bucket it needs

The picker itself only understands:

- folder list at the chosen scope root
- optional one-level subfolder list
- file list in `folder` or `folder/subfolder`
- selected file returns structured path parts

So the reusable request shape could be:

```js
loadFolders({ scope })
loadFiles({ scope, folder, subfolder })
```

And the returned selection:

```js
{
  scope: "projects",
  folder: "nerve",
  subfolder: "",
  filename: "nerve.jpg"
}
```

For the catalogue work editor, we’d map that back to existing fields:

```js
project_folder = selection.folder
project_subfolder = selection.subfolder
project_filename = selection.filename
```

The one-level subfolder rule belongs in the picker/API contract. That keeps the component portable while still enforcing the simple organization model.

> how do we manage component drift? I will forget that it is used in file modal, until oneday...

You manage it by making reuse explicit in the component boundary, not tribal memory.

Practical safeguards:

- Put the component in `shared/frontend/`, not inside a route.
- Give it a neutral name, e.g. `project-file-picker`, not `catalogueProjectMediaPicker`.
- Add a short source doc listing current consumers:
  - catalogue work editor
  - later work detail / moments / analytics / docs-viewer
- Add a smoke test for the shared component itself, not only route-specific tests.
- Route tests should only verify integration: “work editor receives `{folder, subfolder, filename}` and updates labels.”
- Keep component API small and documented in code:
  - inputs
  - loader callbacks
  - initial selection
  - returned selection
  - one-level subfolder rule
- Avoid route-specific CSS names inside the component.
- Add a top comment in each consuming route file:
  - `Uses shared project-file-picker; change picker behavior in shared/frontend/js/project-file-picker.js`

The most useful one is a shared smoke test. If someone changes the picker for one route and breaks another behavior, the component test should fail before you rediscover it visually months later.


---