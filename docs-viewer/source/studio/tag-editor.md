---
doc_id: tag-editor
title: Tag Editor
added_date: 2026-03-31
last_updated: 2026-06-22
parent_id: analytics
---
# Tag Editor

Route:

- `/analytics/series-tag-editor/`
- required query param: `?series=<series_id>`
- example: `/analytics/series-tag-editor/?series=curve-poems`

Purpose:

- review and edit series-level tag assignments plus per-work override tags for one series
- preserve optional historical alias metadata when a tag is added from an alias suggestion, without surfacing that metadata in the UI

## Route Ready State

The page root `#seriesTagEditorRoot` participates in [Route Ready State](/docs/?scope=studio&doc=route-ready-state) with Analytics attributes.
Route-specific details:

- the editor save command sets route busy
- `data-analytics-mode` is `single` when a work is selected, `edit` for the series-level editor state, and `empty` for missing or failed series loads
- `data-analytics-service` reports whether the Local Analytics API is available for direct saves
- `data-analytics-record-loaded` is `true` after a valid series id is loaded

Successful local-server saves send Analytics activity context and append unified activity rows with script purpose `save tag data`.
Multiple row writes from one Save click share the same initiating action context.

## Page / Template Structure

Static route template:

- `analytics-app/app/frontend/routes/series-tag-editor.html`

App shell:

- `analytics-app/app/frontend/analytics-shell.html`

Page boot module:

- `analytics-app/app/frontend/js/series-tag-editor-page.js`

Editor controller:

- `analytics-app/app/frontend/js/analytics-tag-editor.js`

Supporting modules:

- `analytics-app/app/frontend/js/analytics-ui.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-domain.js`
- `analytics-app/app/frontend/js/tag-assignments-offline.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-render.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-suggestions.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-state.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-save.js`

Top-level structure in the page template:

- `#seriesTagEditorRoot.analyticsPage`
  - page shell and runtime data attributes
- `.analyticsPage__header`
  - two-column series header area
- `.analyticsPage__media`
  - primary image column
- `.analyticsPage__context`
  - series metadata column
- `.analyticsPage__editor`
  - container for the interactive tag editor shell
- `#analytics-tag-editor.analyticsTagEditor[data-role="series-tag-editor"]`
  - template-owned editor shell root
- `[data-role="editor-shell"]`
  - template-owned editor panel shell
- `[data-role="modal-host"]`
  - modal mount point used by `analytics-tag-editor.js`

## Named UI Sections

### Series header

User-facing name:

- series header

DOM / CSS:

- `.analyticsPage__header`

JS owner:

- `analytics-app/app/frontend/js/series-tag-editor-page.js`

This section contains:

- primary image column
- series metadata column

### Primary image

User-facing name:

- primary image

DOM / CSS:

- `#seriesTagEditorMedia.analyticsPage__media`
- `#seriesTagEditorMediaLink`
- `#seriesTagEditorMediaImg.analyticsPage__mediaImg`
- `#seriesTagEditorMediaCaption.analyticsPage__mediaCaption`

JS owner:

- `renderPrimaryMedia(...)`
- `syncHeaderMediaForWork(...)`
  in `analytics-app/app/frontend/js/series-tag-editor-page.js`

Meaning:

- the image area in column 1 of the series header
- shows the series primary work by default
- can switch to the currently selected work while editing
- shows a caption under the image as `work_id - title` and updates when the displayed work changes

### Series metadata

User-facing name:

- series metadata

DOM / CSS:

- `.analyticsPage__context`
- `.analyticsPage__context--meta`
- `.page__caption.page__metaList`
- `#seriesTagEditorTitle`
- `#seriesTagEditorCat`
- `#seriesTagEditorYear`
- `#seriesTagEditorYearDisplay`
- `#seriesTagEditorSortFields`
- `#seriesTagEditorPrimaryWork`
- `#seriesTagEditorFolders`
- `#seriesTagEditorNotes`

JS owner:

- `initSeriesTagEditorPage()`
  in `analytics-app/app/frontend/js/series-tag-editor-page.js`

Meaning:

- the field list in column 2 of the series header
- this now uses the shared unboxed metadata pattern from the main site rather than a Studio-specific boxed panel treatment

### Editor panel

User-facing name:

- tag editor

DOM / CSS:

- `.analyticsPage__editor`
- `#analytics-tag-editor[data-role="series-tag-editor"]`
- `[data-role="editor-shell"]`

JS owner:

- page template for shell markup
- `renderShell(state)` in `analytics-app/app/frontend/js/analytics-tag-editor.js` for dynamic labels, refs, and modal DOM

Meaning:

- the interactive editing area with template-owned outer structure and JS-owned dynamic content

### Works

User-facing name:

- works

DOM / CSS:

- `[data-role="work-section"]`
- `[data-role="work-input"]`
- `[data-role="selected-work"]`
- `[data-role="work-popup"]`
- `[data-role="work-popup-list"]`

JS owner:

- `renderShell(state)`
- work-related handlers in `wireEvents(state)`
  in `analytics-app/app/frontend/js/analytics-tag-editor.js`
- selected-work rendering in `analytics-app/app/frontend/js/analytics-tag-editor-render.js`
- work suggestion popup rendering in `analytics-app/app/frontend/js/analytics-tag-editor-suggestions.js`

Meaning:

- the work search box and currently selected works area

### Context hint

User-facing name:

- context hint

DOM / CSS:

- `[data-role="message-section"]`
- `[data-role="context-hint"]`
- `.analytics__contextHint`
- `[data-role="status"]`
- `[data-role="save-warning"]`
- `[data-role="save-result"]`

JS owner:

- `renderContextHint(state)` in `analytics-app/app/frontend/js/analytics-tag-editor-render.js`

Meaning:

- the line explaining whether edits apply to the series or to selected works
- with no active work, this section should make it clear that the editor is in series-tag mode
- the editor now presents context, status, warning, and save-result lines inside one shared message container rather than as separate boxes

### Group rows

User-facing name:

- group rows

DOM / CSS:

- `[data-role="groups-section"]`
- `[data-role="groups"]`
- `.analyticsGroups`
- `.analyticsGroupRow`

JS owner:

- group rendering functions in `analytics-app/app/frontend/js/analytics-tag-editor-render.js`

Meaning:

- the visible rows of tag chips grouped by `subject`, `domain`, `form`, and `theme`
- the group-name anchor for each row now uses the same coloured pill treatment as other Studio group-name displays
- with no active work, these rows are editable series tags
- with an active work, inherited series tags become monochrome context chips and work override tags remain editable
- in offline mode, locally changed assignments show a caption below the chip and bold tag text
- pending deletions remain visible as bold struck chips with a `delete` caption and a `⤺` restore control

### Tag input row

User-facing name:

- tag input row

DOM / CSS:

- `[data-role="search-section"]`
- `[data-role="tag-input"]`
- `[data-role="add-tag"]`
- `[data-role="save"]`
- `[data-role="save-mode"]`

JS owner:

- `renderShell(state)`
- input/save handlers in `wireEvents(state)`

Meaning:

- the main row used to add tags and save changes
- with no active work, this row adds series tags
- with an active work, this row adds work-only overrides

### Suggestions popup

User-facing name:

- tag suggestions popup

DOM / CSS:

- `[data-role="popup"]`
- `[data-role="popup-list"]`
- `.analytics__popup`
- `.analyticsSuggest__*`

JS owner:

- popup rendering functions in `analytics-app/app/frontend/js/analytics-tag-editor-suggestions.js`

Meaning:

- the autocomplete area for canonical tags, aliases, and work suggestions

## UI Contract

- classes define presentation
- `data-role` defines JS selectors
- `data-state` and ARIA define runtime state

`analytics-app/app/frontend/js/analytics-ui.js` holds the role selectors plus the generated style class tokens used by `analytics-tag-editor.js`, `analytics-tag-editor-render.js`, and `analytics-tag-editor-suggestions.js`.

### Status and save feedback

User-facing name:

- editor status
- save warning
- save result

DOM / CSS:

- `[data-role="status"]` / `.analytics__status`
- `[data-role="save-warning"]` / `.analytics__saveWarning`
- `[data-role="save-result"]` / `.analytics__saveResult`

JS owner:

- status rendering helpers in `analytics-app/app/frontend/js/analytics-tag-editor.js`

### Manual patch modal

User-facing name:

- patch preview modal

DOM / CSS:

- `[data-role="analytics-modal"]`
- `[data-role="modal-tags"]`
- `[data-role="modal-snippet"]`
- `[data-role="copy-snippet"]`
- shared shell from `analyticsModal` / `analyticsModal__*`

JS owner:

- modal shell in `renderShell(state)`
- shell open/close/focus behavior in `analytics-app/app/frontend/js/analytics-tag-editor-modals.js`
- copy/status handling in `analytics-app/app/frontend/js/analytics-tag-editor.js`

Meaning:

- fallback/manual inspection modal for resolved tag-assignment payloads and patch guidance
- not the primary offline-save workflow

## UI Layout and Styling

Primary CSS file:

- `analytics-app/app/assets/css/analytics.css`

Relevant shared classes:

- `.analyticsPage__*`
- `.analytics__panel`
- `.analytics__inputRow`
- `.analytics__input`
- `.analytics__button`
- `.analytics__chip`
- `.analytics__popup`
- `.analytics__status`
- `.analyticsModal*`

Layout model:

- the page header is a two-column layout on larger screens
- the editor is a panel rendered below the header
- the editor itself uses stacked sections rather than a table/list shell

## DOM Rendering and Event Wiring

Page boot:

- `initSeriesTagEditorPage()` in `analytics-app/app/frontend/js/series-tag-editor-page.js`

Editor boot:

- `initAnalyticsTagEditor()` in `analytics-app/app/frontend/js/analytics-tag-editor.js`

Main render functions:

- `renderShell(state)`
- `renderAll(state)`

Main event wiring:

- `wireEvents(state)`

Important event integration:

- `series-tag-editor:selected-work-change`
  - emitted by the editor state flow
  - consumed by `series-tag-editor-page.js` to update the primary image

## State Handling

Primary page state:

- series metadata and primary-image state live in `series-tag-editor-page.js`

Primary editor state:

- editor state object is created by `buildAnalyticsTagEditorState(...)` in `analytics-tag-editor-state.js`
- `analytics-tag-editor.js` owns route orchestration and mutates that state through event handlers

Key editor state areas:

- selected works
- active work
- resolved series entries
- per-work entries
- save mode
- offline session baseline and staged-series metadata
- modal snippet/status fields

Business/state helpers live in:

- `analytics-app/app/frontend/js/analytics-tag-editor-domain.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-state.js`

## Data Access / Query Params / JSON Parsing

Query params:

- `series`
  - required page input
- `works`
  - selected work ids persisted by the editor
- `active`
  - active work id persisted by the editor

Page data fetches:

- series index JSON in `series-tag-editor-page.js`
- work detail JSON for header media in `series-tag-editor-page.js`

Editor data fetches:

- registry
- aliases
- assignments
- series index
- works index

These are loaded through:

- `analytics-app/app/frontend/js/analytics-data.js`

## Offline Session Mode

Current offline behavior:

- the editor stages normalized series rows in browser `localStorage`
- staged rows preserve assignment objects, including `w_manual` and optional `alias`
- the editor advances its baseline after staging so the page behaves like a save flow
- local-only changes are surfaced back into the UI

Current session management surface:

- the Series Tags page is the session hub
- `Session` opens the offline-session modal
- `Import` opens the import-preview/apply flow when the local server is available

## Business Logic

Primary business logic modules:

- `analytics-app/app/frontend/js/analytics-tag-editor-domain.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-save.js`

Business responsibilities include:

- tag normalization and resolution
- alias resolution
- work-state diffing
- persisted assignment shape conversion
- save/persist mode handling
- offline-session staging and baseline overlay
- local-server availability re-probe on page return/focus for staged-series notice
- patch snippet generation for fallback/manual inspection only

## Change Guidance

If a change request refers to:

- “primary image”
  - start with `#seriesTagEditorMedia` and `series-tag-editor-page.js`
- “series metadata”
  - start with `.analyticsPage__context` and `series-tag-editor-page.js`
- “works”
  - start with `.analytics__inputRow--work` and selected-work rendering in `analytics-tag-editor-render.js`
- “tag suggestions”
  - start with `.analytics__popup` / `.analyticsSuggest__*` and `analytics-tag-editor-suggestions.js`
- “save modal”
  - start with `analytics-tag-editor-modals.js` plus shared modal styles in `analytics.css`

Clarify with the user when a request could mean:

- page header metadata vs editor panel metadata
- selected-work UI vs work-specific tag chips
- context hint vs save/status messages
