---
doc_id: offline-tag-assignments-implementation-breakdown
title: Offline Tag Assignments Implementation Breakdown
last_updated: 2026-03-28
parent_id: tagging
---

# Offline Tag Assignments Implementation Breakdown

Status:

- planning document
- derived from the locked v1 product spec

## Execution Order

1. Add the offline-session client module.
2. Integrate offline staged-row overlay into editor boot.
3. Add offline save behavior to the editor.
4. Add local-assignment visual states in the editor.
5. Add the session strip to the Series Tags page.
6. Add export flows.
7. Add assignment import preview and apply on the local server.
8. Add Series Tags import UI.
9. Add new UI copy to `studio_config.json`.
10. Update docs and verify behavior.

## Batch 1: Offline Session Foundation

Create:

- `assets/studio/js/tag-assignments-offline.js`

Responsibilities:

- `localStorage` schema and versioning
- normalized staged-session payload handling
- read, write, and clear session
- read and write one staged series row
- export JSON generation
- imported offline JSON parsing
- comparison between current repo row and stored base snapshot
- preserve full normalized assignment rows, including optional `alias` metadata

Keep out of this module:

- DOM rendering
- page-specific UI text
- fetch and server logic

Likely related files:

- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`

## Batch 2: Editor Offline Overlay and Save Semantics

Primary files:

- `assets/studio/js/tag-studio.js`
- `assets/studio/js/tag-studio-domain.js`
- `assets/studio/js/tag-studio-save.js`

Responsibilities in `tag-studio.js`:

- overlay staged row at boot
- add offline autosave debounce
- make offline `Save Tags` perform immediate stage plus status update
- advance baseline after offline stage
- carry local assignment-state metadata into the render layer
- preserve the current `post` save path
- preserve optional `alias` metadata through overlay, diffing, staging, and rehydration

Responsibilities in `tag-studio-domain.js`:

- helpers for deriving local-vs-repo assignment state
- stable normalized row comparisons for series tags and work rows
- helpers required for pending-delete display state
- treat assignment equality as full row equality, including optional `alias`

Responsibilities in `tag-studio-save.js`:

- retain current patch snippet support if still needed
- support offline save-mode and status helpers if keeping that logic there is cleaner

Main design constraint:

- offline state should be layered over normalized assignment rows, not mixed into canonical row normalization

## Batch 3: Editor Visual State Styling

Primary files:

- `assets/studio/js/tag-studio.js`
- `assets/studio/css/studio.css`
- [UI Framework](/docs/?doc=ui-framework)

Responsibilities:

- render chip caption below the chip using `--font-caption`
- render caption `local` for locally added or modified assignments
- render struck-through chip text plus caption `delete` for staged deletions
- define shared Studio classes or modifiers for these chip states

Important note:

- local-modified state is assignment-state based, so alias-only changes still count as local changes even when the visible chip text is unchanged

Locked styling rule:

- no ghost styling for delete state

## Batch 4: Series Tags Session Strip and Local Markers

Primary files:

- `studio/series-tags/index.md`
- `assets/studio/js/series-tags.js`
- `assets/studio/css/studio.css`
- optionally `assets/studio/js/studio-ui.js`

Responsibilities in template:

- add a template-owned session strip section above the table

Responsibilities in `series-tags.js`:

- load the offline session
- render session summary
- wire `Copy JSON`, `Download JSON`, and `Clear session`
- conditionally expose `Import assignments` when the local server is available
- mark series rows and chips with `local` and `delete` captions
- refresh list state after clear and import actions

This page is the session hub.

## Batch 5: Assignment Import Server Support

Primary file:

- `scripts/studio/tag_write_server.py`

Responsibilities:

- add `OPTIONS` and `POST` routes for assignment import preview and apply
- validate imported offline session JSON
- validate series ids and work ids against current assignment and site structure
- compare imported base snapshot with current repo row
- accept and preserve optional `alias` values on assignment rows
- return preview statuses such as `apply`, `conflict`, `invalid`, and `missing`
- apply approved series rows atomically
- update timestamps and backups consistently with existing writer behavior
- log import summaries minimally

Likely helper additions:

- normalized assignment comparison helpers in Python
- import payload validation helpers
- import summary builders
- alias-aware assignment row normalization helpers where needed

## Batch 6: Series Tags Import UI

Primary files:

- `assets/studio/js/series-tags.js`
- `studio/series-tags/index.md`
- `assets/studio/css/studio.css`
- optionally `assets/studio/js/studio-transport.js`

Responsibilities:

- add file picker for offline JSON import
- call import preview endpoint when local server is available
- render preview summary
- render conflict resolution UI with per-series `overwrite` and `skip`
- send final apply request
- clear imported rows from local session after successful import
- preserve skipped or unresolved rows in local session

This batch depends on the server contract from Batch 5.

## Batch 7: Documentation and Verification

Docs to update:

- [Tag Editor](/docs/?doc=tag-editor)
- [Series Tags](/docs/?doc=series-tags)
- [Studio](/docs/?doc=studio)
- [UI Framework](/docs/?doc=ui-framework)
- [Tag Write Server](/docs/?doc=scripts-tag-write-server)

Verification focus:

- offline stage persists across reload and browser restart
- offline stage works across multiple series
- local and delete chip styling works in editor and Series Tags
- copy and download export flows work
- mobile copy and download behavior is acceptable
- import preview works with and without conflicts
- overwrite and skip apply correctly
- fallback from local server mode to offline mode behaves cleanly

## Main Risk Areas

- keeping editor diff and baseline behavior correct after offline saves
- representing deletion clearly without breaking current inherited-state semantics
- keeping chip-state behavior consistent between editor and Series Tags
- making import conflict detection deterministic and trustworthy
- handling `localStorage` corruption or schema migration cleanly

## Recommended Edit Order

1. Batch 1
2. Batch 2
3. Batch 3
4. Batch 4
5. Batch 5
6. Batch 6
7. Batch 7

This order stabilizes the client-side offline model before import work begins.
