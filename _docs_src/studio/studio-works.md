---
doc_id: studio-works
title: Studio Works
last_updated: 2026-03-28
parent_id: studio
sort_order: 20
---

# Studio Works

Route:

- `/studio/studio-works/`

Purpose:

- review works with Studio-specific sort-state wiring

## Page / Template Structure

Primary template:

- `studio/studio-works/index.md`

Page controller:

- `assets/studio/js/studio-works.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`
- `assets/studio/js/studio-data.js`

Top-level structure:

- Studio layout wrapper from `_layouts/studio.html`
  - shared site header with Studio-specific links, plus the page title row
- `#worksStudioRoot[data-role="studio-works"]`
  - page root and runtime data source
- `#worksListCopySeriesButton`
  - copies the plain-text series list to the clipboard
- `[data-role="sort-button"]`
  - shared sort-button hooks on the existing works header controls

## Named UI Sections

### Sort header

User-facing name:

- works sort header

DOM / CSS:

- `.worksList__head`
- `.worksList__sortBtn[data-role="sort-button"]`
- `.worksList__sortIcon`

JS owner:

- `initStudioWorksPage()`
- `updateHeaderState(key, dir)`

Meaning:

- the existing works sort controls, now bound through the shared Studio role/state contract

### Meta actions

User-facing name:

- works meta actions

DOM / CSS:

- `.worksList__metaRow`
- `.worksList__metaActions`
- `#worksListCopySeriesButton`

JS owner:

- `initStudioWorksPage()`

Meaning:

- provides the `copy series` clipboard action alongside the site-map link
- copies plain-text series titles, one per line, in alphabetical order

### Works list

User-facing name:

- works list

DOM / CSS:

- `.worksList__list`
- `.worksList__item`

Meaning:

- the existing Studio works rows and links
- work links carry Studio sort/filter return state so the work-page back link returns to `/studio/studio-works/`

## UI Layout and Styling

Primary CSS:

- `assets/css/main.css`

Shared primitives used:

- `data-role="sort-button"`
- `data-state="active"`

Page-specific classes retained:

- `worksList__*` plus `worksList--studio` for the Studio works layout and row styling

## DOM Rendering and Event Wiring

Page boot:

- `initStudioWorksPage()`

Main event wiring:

- click handlers on `[data-role="sort-button"]`
- click handler on `#worksListCopySeriesButton`

Meaning:

- the page keeps its existing list rendering, but the interactive sort state no longer depends on style-class behavior hooks
- the page now also loads Studio config for the copy-button label

## UI Contract

This page follows the Studio-specific shared UI boundary documented in [UI Framework](/docs/?doc=ui-framework):

- classes define presentation
- `data-role` defines JS selectors
- `data-state` defines active sort state

`assets/studio/js/studio-ui.js` holds the role selector and state token used by `studio-works.js`.

## Change Guidance

If a request refers to:

- “sort buttons”
  - start with `[data-role="sort-button"]` and `.worksList__sortBtn`
- “active sort state”
  - start with `updateHeaderState(...)` in `assets/studio/js/studio-works.js`
