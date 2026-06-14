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

## Extension Points

`bindSearchList(inputNode, popupNode, options)` is the only public entry point.

Supported options:

- `id`: stable popup and option id prefix
- `loadOptions(query)`: returns the candidate option records
- `filterOptions(options, query)`: filters loaded records; use this for route-specific matching such as prefix-only search
- `getOptionValue(option)`: returns the committed string value
- `renderOption(option, context)`: returns the row markup; use this for one-column, two-column, or route-specific rows
- `renderNoResults()`: returns custom empty-state markup
- `renderError(error)`: returns custom load-error markup
- `maxOptions`: caps visible results after filtering
- `classNames.option`: adds a route-specific option class
- `onTransientInput({ value })`: observes uncommitted typing
- `onCommit(option, { value })`: receives the committed option
- `onCancel({ value })`: receives the reset value after Escape
- `onCommitError(error)`: handles commit failures

## Standardisation Rules

Do not change the shared default matching to satisfy one consumer.
If a consumer needs prefix matching, ranked matching, work-id matching, or another domain rule, pass `filterOptions`.

Do not change the shared fallback row to satisfy one consumer.
If a consumer needs a second column, status text, ids, or another route-specific layout, pass `renderOption` and route-specific CSS.

Do not mark a form dirty from `onTransientInput`.
Typing into the field is a reversible search state; durable form changes should normally happen in `onCommit`.

Do not copy the listbox keyboard handling into route modules.
Add missing shared interaction behavior in `shared/frontend/js/search-list.js` and update `admin-app/tests/smoke/ui_catalogue_search_list_modules.py`.

## First Implementation

The first live implementation is the Catalogue Work project-folder picker.
It uses Search List for the project folder field, while `catalogue-project-media-picker.js` remains the adapter for:

- loading project folders from Local Studio
- prefix-matching folder names
- rendering folder rows
- clearing project subfolder and filename after folder commit
- opening the project image modal after folder commit

The file-selection modal is intentionally separate.
It has a different interaction shape: selected project folder context, optional subfolder listbox, file listbox, and explicit Select/Cancel actions.

## Current Consumers

- `studio/app/frontend/js/catalogue-project-media-picker.js`: project-folder search on the Catalogue Work editor

## Verification

Focused smoke test:

```bash
$HOME/miniconda3/bin/python3 admin-app/tests/smoke/ui_catalogue_search_list_modules.py --site-root .
```

The smoke test covers the shared contract rather than one route adapter:

- selected text on focus
- caller-owned prefix filtering
- default contains filtering
- caller-owned two-column row rendering
- Escape reset
- ArrowDown, ArrowUp, Enter commit behavior
- active-option scrolling inside a constrained popup
