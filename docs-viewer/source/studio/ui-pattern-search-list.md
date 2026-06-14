---
doc_id: ui-pattern-search-list
title: Search List Pattern
added_date: 2026-06-14
last_updated: 2026-06-14
parent_id: ui-catalogue
viewable: true
---
# Search List Pattern

Search List is the shared production control for an input that filters an option list and commits only after the user chooses a result.

The shared assets are:

- behavior: `shared/frontend/js/search-list.js`
- baseline styling: `shared/frontend/css/search-list.css`
- browser import path: `/shared/frontend/js/search-list.js`
- stylesheet path: `/shared/frontend/css/search-list.css`

## Use When

Use Search List when:

- typing should be transient until a result is committed
- Escape should restore the value from before searching
- ArrowUp, ArrowDown, Enter, pointer hover, and outside-click behavior should be consistent
- multiple local apps need the same interaction model with different data and row rendering

Do not copy this keyboard and popup behavior into route modules.
If the interaction contract changes, update `shared/frontend/js/search-list.js`.

## Behavior Contract

The shared module owns:

- transient query state
- committed-value reset on Escape
- popup open and close behavior
- ArrowDown entering and moving through results
- ArrowUp moving upward and returning from the first result to the field
- Enter committing the active result
- active result scrolling into view with bottom padding respected
- pointer-vs-keyboard navigation mode so hover and keyboard selection do not create double-highlight states
- ARIA listbox attributes and active-descendant state

The consuming app owns:

- input and popup DOM placement
- option loading
- option filtering
- option row rendering
- commit behavior
- any route-specific layout classes

## First Implementation

The first live implementation is the Catalogue Work project-folder picker.
It uses Search List for the project folder field, while `catalogue-project-media-picker.js` remains the adapter for:

- loading project folders from Local Studio
- prefix-matching folder names
- rendering folder rows
- clearing project subfolder and filename after folder commit
- opening the project image modal after folder commit

The file-selection modal is intentionally separate.
It has a different interaction shape: filter field, optional subfolder select, file list, and explicit Select/Cancel actions.
