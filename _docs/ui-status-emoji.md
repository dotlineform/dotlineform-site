---
doc_id: ui-status-emoji
title: UI Status Emoji
added_date: 2026-05-02
last_updated: "2026-05-11 17:50"
ui_status: done
parent_id: archive
sort_order: 320
---
# UI Status Emoji

## Purpose

The purpose is to enable a single emoji to be inserted at the beginning of a document title as displayed in the Docs Viewer index panel.

A simple set could be:

✅ Done<br>
🔄 In progress<br>
❗ Urgent<br>
⏸️ Paused / blocked<br>
📝 Needs review<br>
🧪 Testing<br>
🚫 Cancelled / rejected

The emoji would be determined by a ui_status field in the document’s front matter, with the options for this field enumerated in a section of the appropriate JSON config file:

For example:

```json
{
  "docs_viewer": {
    "ui_statuses_by_scope": {
      "studio": [
        {
          "ui_status": "done",
          "label": "Done",
          "emoji": "✅"
        },
        {
          "ui_status": "urgent",
          "label": "Urgent",
          "emoji": "❗"
        }
      ],
      "library": [],
      "analysis": []
    }
  }
}
```

- This would be a shared feature available to all scopes (Studio docs, Library, Analysis), with each scope able to define a different allowed status set.
- If the status is not present in front-matter, or the value does not correspond to a value in config, it is ignored by the viewer.
- The status can be edited in the Doc Viewer ‘Edit’ modal (in manage mode) by selecting from a dropdown control which lists the fixed `draft` option plus the available config values. The default is `draft` when `viewable: false`; otherwise it is the configured front-matter `ui_status` value when valid, or blank.
- The available status values are also displayed as small circular pills next to the ‘favourites’ pill displayed above the document. The pills contain the associated emoji. When not selected, the pills show the emoji in grey. When selected, the pills show the coloured emoji. The pills can be toggle on/off in the same way as the favourites pill.

## Review Notes

- The feature should stay inside the shared Docs Viewer boundary rather than becoming separate `/docs/`, `/library/`, or future Analysis implementations.
- The docs data builder currently emits explicit fields such as `doc_id`, `title`, `parent_id`, `sort_order`, `summary`, `published`, and `viewable`; `ui_status` needs to become an explicit generated field rather than relying on arbitrary front matter passthrough.
- The manage-mode metadata editor currently owns title, summary, parent, and sort order edits; adding status there requires a matching write-server change so the dropdown is not a UI-only control.
- The requested pill behavior is closer to a document metadata toggle than to the existing favourites feature. It should reuse the compact pill visual language, but it should write source front matter rather than browser-local IndexedDB.

## Decisions

- Status configuration is scope-specific under `docs_viewer.ui_statuses_by_scope`.
- `studio_config.json` remains the shared Docs Viewer config source for now. A route-level config hook is not needed unless a future scope cannot use that shared payload.
- `ui_status` values on hidden, manage-only, or non-loadable docs are ignored by the viewer.
- The emoji prefix appears only in the left index panel. It is a UI visual prompt, not part of search output, breadcrumb/path text, bookmark labels, or document titles.
- The Edit modal only writes a status change when the user clicks `Save`.
- The Edit modal treats `draft` as viewability state: selecting `draft` writes `viewable: false` and clears `ui_status`; selecting any non-draft status writes `viewable: true`.
- The status pills write immediately in manage mode by setting or removing the document's `ui_status` front matter, which causes the index emoji to appear or disappear after the docs payload reloads.
- When manage mode is unavailable, status pills remain visible as read-only indicators.
- The dropdown includes fixed `<none>` and `draft` options outside the configured status values.
- Docs search output is not affected by this feature.
- Malformed config entries are ignored by the viewer rather than treated as build failures.

## Invalid Config Handling

The viewer should ignore a configured status entry when:

- `ui_status` is missing, blank, duplicated within the same scope, or not a string
- `emoji` is missing, blank, or not a string
- `label` is missing, blank, or not a string
- the configured scope entry is not an array

The viewer can also treat overlong emoji strings as invalid to keep the index and pill controls compact. The docs builder should not fail on these config issues in v1; the runtime should normalize defensively and ignore bad entries.

## Proposed Implementation Tasks

### 1. Define the config contract

Status: implemented.

- Add a `docs_viewer.ui_statuses_by_scope` object to `assets/studio/data/studio_config.json`.
- Define scope keys for current and planned docs-viewer scopes, starting with `studio`, `library`, and `analysis`.
- Use stable values such as `ui_status`, `label`, and `emoji`.
- Normalize the viewer runtime so duplicate, blank, overlong, or malformed status entries are ignored deterministically per scope.
- Document the config contract in [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) or the current Docs Viewer config reference.

### 2. Carry status through docs generation

Status: implemented.

- Update `scripts/build_docs.rb` so `ui_status` is parsed from document front matter.
- Include the normalized raw status value in generated docs index entries and per-doc payloads.
- Keep missing or blank status values out of rendered UI while preserving deterministic generated output.
- Do not validate `ui_status` against config in the builder for v1; let the viewer ignore unknown values per scope.

### 3. Render status in the index panel

Status: implemented.

- Load configured statuses through the existing Docs Viewer config request.
- Build a scope-specific lookup from `ui_status` to emoji/label.
- Prefix the rendered index title with the configured emoji when the active doc record has a matching status.
- Ignore `ui_status` for non-loadable and manage-only tree nodes.
- Do not add the emoji to search results, recent results, breadcrumb/path text, bookmark labels, or document content/header copy.
- Make the prefix presentational unless a label is needed for assistive technology.

### 4. Add manage-mode editing

Status: implemented.

- Add a `ui_status` select control to the shared metadata modal in `_includes/docs_viewer_shell.html`.
- Populate the dropdown from the normalized config values for the active scope, with a fixed blank `<none>` option for no status.
- Initialize the dropdown from the active doc's generated `ui_status`.
- Include the selected value in the metadata update payload.
- Save modal changes only when the user clicks `Save`.

### 5. Persist status writes

Status: implemented.

- Update `scripts/docs/docs_management_server.py` to accept `ui_status` in `/docs/update-metadata`.
- Rewrite front matter so blank status removes `ui_status` and non-blank status writes the selected value.
- Keep dry-run and write responses clear about whether status changed.
- Rebuild docs payloads after status changes using the existing docs-management rebuild path.
- Do not trigger docs search rebuilds solely for status changes.

### 6. Add status pill controls

Status: implemented.

- Render configured status pills beside the existing favourites/bookmark row area.
- Treat a selected pill as the current document's source-backed `ui_status`.
- Toggle the selected status off when the active pill is clicked again.
- In manage mode, make pill toggles write immediately through the docs-management server and reload the generated docs payload.
- When manage mode is unavailable, leave the pills visible as read-only indicators.
- Avoid mixing source-backed status controls with browser-local favourites persistence.

### 7. Style and accessibility

Status: implemented.

- Reuse the compact Docs Viewer pill styling direction established by favourites.
- Provide selected/unselected states that do not rely on color alone.
- If monochrome emoji are implemented with CSS filters, verify emoji rendering remains legible across Chromium and Safari.
- Add accessible labels such as `Set status: Done` and `Clear status: Done`.

### 8. Verification

Status: implemented.

- Run `./scripts/build_docs.rb --scope studio --write` after docs-source changes.
- Run `node --check assets/docs-viewer/js/docs-viewer.js` after runtime changes.
- Run a targeted docs build or `./scripts/run_checks.py --profile docs` if the implementation changes docs builder, docs-management server, generated payloads, and viewer runtime together.
- Manually verify `/docs/` and `/library/` on desktop and mobile: scope-specific status config, index-only prefix rendering, edit-modal default selection, modal save behavior, immediate pill writes in manage mode, read-only pills outside manage mode, status clearing, reload persistence, invalid-status ignore behavior, and no search/recent/bookmark label emoji leakage.

## Benefits

- Adds lightweight scan cues to the Docs Viewer index without changing document titles.
- Keeps allowed statuses centralized in scope-aware config rather than scattered through docs.
- Lets manage mode update status from the same metadata workflow used for other document front matter.

## Risks

- The title prefix could make the index visually noisy if too many status categories are configured.
- Source-backed status pills may feel similar to favourites while having different persistence behavior.
- Immediate pill writes require clear busy/error handling so they do not feel like browser-local favourites.
