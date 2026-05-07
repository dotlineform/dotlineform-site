---
doc_id: studio-works
title: Catalogue Works
added_date: 2026-04-01
last_updated: "2026-05-07"
parent_id: catalogue
sort_order: 60
---
# Catalogue Works

Route:

- `/studio/studio-works/`

Purpose:

- review works with Studio-specific sort-state wiring

## Route Ready State

The page root `#worksStudioRoot` exposes the shared Studio route-ready contract:

- `data-studio-ready` is `false` while config, works, series, and Studio storage data load, then `true` after the list or empty state is rendered
- `data-studio-busy` is `true` during the initial data load and `false` after render
- `data-studio-mode` is `list` for the full index, `single` for a series-filtered view, and `empty` when no rows can be rendered
- `data-studio-record-loaded` is `true` when work rows are loaded

## Page / Template Structure

Primary template:

- `studio/studio-works/index.md`

Page controller:

- `assets/studio/js/studio-works.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`
- `assets/studio/js/studio-data.js`

Current data sources:

- `assets/data/works_index.json`
- `assets/data/series_index.json`
- `assets/studio/data/work_storage_index.json`

Top-level structure:

- Studio layout wrapper from `_layouts/studio.html`
  - shared site header with Studio-specific links, plus the page title row
- `#worksStudioRoot[data-role="studio-works"]`
  - page root and runtime data source
- `#worksListCopySeriesButton`
  - copies the plain-text series list to the clipboard
- `[data-role="sort-button"]`
  - shared sort-button hooks on dense-list header controls

## Named UI Sections

### Sort header

User-facing name:

- works sort header

DOM / CSS:

- `.worksList__head`
- `.tagStudioList__head`
- `.tagStudioList__sortBtn[data-role="sort-button"]`
- `.tagStudioList__sortIndicator`

JS owner:

- `initStudioWorksPage()`
- `updateHeaderState(key, dir)`

Meaning:

- dense-list sort controls bound through the shared Studio role/state contract

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

- `.worksList__item`
- `.tagStudioList__rows`
- `.tagStudioList__row`
- `.tagStudioList__cellLink`
- `.tagStudioList__cellTitle`
- `.tagStudioList__cellMeta`

Meaning:

- the existing Studio works rows and links
- curator-only storage values are merged in from the Studio-only work storage index rather than the public works index
- work links carry Studio sort/filter return state so the work-page back link returns to `/studio/studio-works/`

## UI Layout and Styling

Primary CSS:

- `assets/css/main.css`
- `assets/studio/css/studio.css`

Shared primitives used:

- `tagStudioList`
- `tagStudioList--dense`
- `tagStudioList__head`
- `tagStudioList__sortBtn`
- `tagStudioList__sortIndicator`
- `tagStudioList__rows`
- `tagStudioList__row`
- `tagStudioList__cellLink`
- `tagStudioList__cellTitle`
- `tagStudioList__cellMeta`
- `data-role="sort-button"`
- `data-state="active"`

Page-specific classes retained:

- `worksList--studio`, `worksList--singleSeries`, and focused `worksList__*` cell classes for column templates, route-local link behavior, and series-filter variants

## DOM Rendering and Event Wiring

Page boot:

- `initStudioWorksPage()`

Main event wiring:

- click handlers on `[data-role="sort-button"]`
- click handler on `#worksListCopySeriesButton`

Meaning:

- the page renders rows with the shared dense list primitive while keeping works-specific sort/filter state in the controller
- the page now also loads Studio config for the copy-button label

## UI Contract

This page follows the Studio-specific shared UI boundary documented in [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework):

- classes define presentation
- `data-role` defines JS selectors
- `data-state` defines active sort state

`assets/studio/js/studio-ui.js` holds the role selector and state token used by `studio-works.js`.

## Change Guidance

If a request refers to:

- “sort buttons”
  - start with `[data-role="sort-button"]` and `.tagStudioList__sortBtn`
- “active sort state”
  - start with `updateHeaderState(...)` in `assets/studio/js/studio-works.js`
