No code changes yet. This is the execution breakdown I’d use.

**Execution Order**

1. Add the offline-session client module.
- Create a shared module for `localStorage` read/write, normalization, export JSON, import JSON parsing, and conflict-base metadata.
- Keep this module UI-free so both the editor and Series Tags page can use it.

2. Integrate offline staged-row overlay into editor boot.
- In [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js), load repo assignments first, then overlay any staged row for the current series before `buildState(...)`.
- Extend state to carry repo-vs-local assignment markers needed for rendering chip captions and delete strikethrough state.

3. Add offline save behavior to editor.
- Implement debounced autosave to the offline-session store when save mode is not `post`.
- Keep `Save Tags` and make it perform an immediate stage plus status update in offline mode.
- After offline stage, advance `baselineSeriesRows` and `baselineWorkStateById` the same way successful server save already does.

4. Add local-assignment visual states in the editor.
- Update chip rendering in [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js) and styling in [studio.css](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/css/studio.css).
- Add caption below chip using `--font-caption`.
- For pending deletions, use struck chip text plus `delete` caption only.

5. Add the session strip to the Series Tags page.
- Extend [studio/series-tags/index.md](/Users/dlf/Developer/dotlineform/dotlineform-site/studio/series-tags/index.md) with a template-owned section above the list.
- In [series-tags.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/series-tags.js), render session summary, `Copy JSON`, `Download JSON`, `Clear session`, and later `Import assignments` when server is available.
- Mark series rows/chips with the same local/delete caption rules used in the editor.

6. Add export flows.
- `Copy JSON` should serialize the whole staged session.
- `Download JSON` should create a file from the same payload.
- Make copy the primary action in both wording and placement because mobile is a target environment.

7. Add assignment import preview/apply on the local server.
- In [tag_write_server.py](/Users/dlf/Developer/dotlineform/dotlineform-site/scripts/studio/tag_write_server.py), add:
  - preview endpoint for assignment import/conflict detection
  - apply endpoint for final import with per-series `overwrite`/`skip`
- Conflict detection should compare current repo row to stored base snapshot.

8. Add Series Tags import UI.
- Only expose import actions when the local server is available.
- Add file chooser/import JSON input, preview summary, and conflict resolution UI on the Series Tags page.
- Conflict UI should be series-row based, with `overwrite` and `skip` per series.

9. Move all copy into config.
- Add new `ui_text` entries in [studio_config.json](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/data/studio_config.json) for:
  - offline session strip
  - save/status messages
  - chip captions
  - import preview/conflict text
  - clear/export text

10. Update docs and verify.
- Update the Studio docs and scripts overview in the same change.
- Verify desktop/mobile behavior, offline persistence, export, conflict preview, and import apply.

**Key Implementation Dependencies**

- Steps 1-3 come first because the staged-row model affects everything else.
- Step 4 depends on carrying local assignment state through rendering.
- Steps 5-6 depend on the shared offline-session module.
- Steps 7-8 depend on the export/import JSON contract being fixed.
- Step 9 should happen alongside UI work, not at the end.
- Step 10 is the closeout step.

**Main Risk Areas To Watch During Implementation**

- keeping the editor’s diff/baseline logic correct after offline saves
- representing deletions clearly without breaking current inherited/ghost semantics
- avoiding divergence between editor chip-state rendering and Series Tags chip-state rendering
- making import conflict detection deterministic enough that users trust it
- handling `localStorage` corruption or old schema versions gracefully

If you want, the next step is to break this into concrete code-change batches with proposed file-level responsibilities before editing.