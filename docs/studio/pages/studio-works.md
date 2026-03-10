---
permalink: /docs/studio/pages/studio-works/
---

# Studio Works

Route:

- `/studio/studio-works/`

Purpose:

- review curator works with Studio-specific sort-state wiring

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
- `#worksCuratorRoot[data-role="studio-works"]`
  - page root and runtime data source
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

- the existing works curator sort controls, now bound through the shared Studio role/state contract

### Works list

User-facing name:

- works list

DOM / CSS:

- `.worksList__list`
- `.worksList__item`

Meaning:

- the existing curator works rows and links

## UI Layout and Styling

Primary CSS:

- `assets/css/main.css`

Shared primitives used:

- `data-role="sort-button"`
- `data-state="active"`

Page-specific classes retained:

- `worksList__*` for the existing curator layout and row styling

## DOM Rendering and Event Wiring

Page boot:

- `initStudioWorksPage()`

Main event wiring:

- click handlers on `[data-role="sort-button"]`

Meaning:

- the page keeps its existing list rendering, but the interactive sort state no longer depends on style-class behavior hooks

## UI Contract

This page follows the shared Studio UI boundary documented in `docs/studio/ui-framework.md`:

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
