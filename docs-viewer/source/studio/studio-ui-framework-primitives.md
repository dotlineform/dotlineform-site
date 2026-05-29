---
doc_id: studio-ui-framework-primitives
title: UI Framework Primitives
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: ui-catalogue
viewable: true
---
# UI Framework Primitives

## Studio Naming Boundary

- `tagStudio__*`
  Shared Studio primitives such as buttons, inputs, chips, panels, popups, and modal shells.
- `tagStudioField__*`
  Shared input-field compositions such as label placement, width handling, and stepped value controls.
- `tagStudioToolbar__*`
  Shared import/action toolbar pattern used by registry- and alias-style pages.
- `tagStudioFilters__*`
  Shared filter/search row pattern used by list pages.
- `tagStudioForm__*`
  Shared modal form layout primitives such as fields, labels, warnings, statuses, and selected-chip areas.
- `tagRegistry__*`, `tagAliases__*`, `tagStudioSuggest__*`, `seriesTags__*`
  Page- or feature-specific layout and presentation only.

Rule of thumb: if two Studio pages need the same visual treatment, the class should move into the shared `tagStudio*` layer instead of borrowing another page's namespace.

## Studio Shared Primitives

### Base controls

Defined in `assets/studio/css/studio.css`:

- `tagStudio__panel`
- `tagStudio__panelLink`
- `tagStudio__input`
- `tagStudio__input--defaultValue`
- `tagStudio__input--readonlyDisplay`
- `tagStudio__button`
- `tagStudio__chip`
- `tagStudio__keyPill`
- `tagStudio__popupPill`
- `tagStudio__chipText`
- `tagStudio__chipCaption`
- `tagStudio__chipTag--local`
- `tagStudio__chipTag--delete`
- `tagStudio__key`
- `tagStudio__popup`
- `tagStudio__popupMore`
- `tagStudio__popupInner`
- `tagStudioField`, `tagStudioField--*`, `tagStudioField__*`
- `tagStudioList__*`
- `tagStudioList--dense`
- `tagStudioForm__field--topAligned`
- `tagStudioModal`, `tagStudioModal__*`

These are the baseline building blocks for all Studio pages.

Primitive catalogue rule:

- UI catalogue primitive pages should render the primitive on a neutral page surface rather than inside the same primitive again.
- Primitive variants should stack vertically by default so each shell edge can be inspected without cross-column alignment noise.
- Primitive notes should record implementation constraints, known failure modes, and composition warnings rather than purpose-only prose.
- Primitive definitions should also record design guidance when a layout or sizing choice materially affects correct reuse.
- Primitive code samples should include common design-led overrides when those overrides are part of normal deliberate reuse.
- When a Jekyll-rendered Studio page chooses design-time panel-link background images, keep the asset-width choice in shared page data rather than hardcoding width-specific filenames inline.
- Use a page-level default width plus optional per-panel width overrides for those image choices, and keep the asset naming convention explicit in the docs.
- If a primitive can validly compose with itself, add that self-composition case to the catalogue and fix the shared primitive or shared composition contract when the result is weak.
- When a panel is used as a full-area navigation target, define that as an explicit shared variation with fixed design-time height rather than allowing route-local card patterns to drift independently.

Chip rule:

- `tagStudio__chip`, `tagStudio__keyPill`, and `tagStudio__popupPill` should share the same base pill geometry and height
- only text-level state styling such as offline `local` / `delete` treatment should override that base

Button rule:

- `tagStudio__button` is the shared command-button primitive for actions such as `Save`, `Import`, `New`, `OK`, and `Cancel`
- shared command buttons use one compact height; use the default-width modifier when a command row needs stable button widths
- clickable pill-like controls are not buttons in this system and should be defined through the pill primitive layer instead
- buttons do not need to live inside a toolbar; toolbar is an optional composition primitive rather than part of the button contract
- modal action buttons should remain subsets of the shared button primitive and use the default-width contract
- button-related status, warning, and success copy should stay adjacent to the related command area, either on the same row or in a dedicated row immediately below it

Use these as the default contract for:

- page and modal action buttons such as `Add`, `Save`, `Import`, `Create`, `OK`, and `Cancel`
- text inputs and search inputs
- modal action rows

Input rule:

- `tagStudio__input` is the shared field shell for text entry, native select controls, and readonly field display
- use `tagStudio__input--readonlyDisplay` on a non-input element for values that are display-only by design; use readonly native inputs only when the value still needs input-like text selection or focus behavior
- use placeholder text for muted default text on text-like fields, and `tagStudio__input--defaultValue` when a control such as a select needs the same muted default-value treatment
- default text should use a lighter tone than normal muted labels/meta text so placeholders and default values are clearly distinguishable from entered content
- `tagStudioField` owns width, label placement, and add-on button composition rather than pushing that layout into the base input class
- the default field width is `18rem`; use a local `--field-width` override for deliberate exceptions and `tagStudioField--fill` when the field should take the remaining row width
- text inputs, selects, and stepped numeric controls should keep the same control height as the small Studio button
- numeric data should still default to plain input boxes; do not infer step buttons or native number-widget UI from storage type alone
- disabled means temporarily unavailable because another page state is incomplete; disabled text should use the same lighter default-text tone, and values that are always display-only should use the non-input Readonly Display treatment instead of the disabled state
- stepped value controls should use full-height small buttons rather than half-height split-arrow cells
- in two-column Studio form rows, labels should be vertically centered with single-line controls and top-aligned only for multiline controls; prefer explicit alignment classes such as `tagStudioForm__field--topAligned` over padding offsets
- info-only current-record panels in the catalogue editor family should use the Readonly Display treatment rather than the older muted `tagStudioForm__readonly` surface
- the same Readonly Display treatment should be used for other display-only Studio summary/value surfaces such as import-workbook paths and preview summaries when they are not editable controls

### Toolbar pattern

Use `tagStudioToolbar__*` for the shared top action/import block:

- `tagStudioToolbar`
- `tagStudioToolbar__row`
- `tagStudioToolbar__field`
- `tagStudioToolbar__label`
- `tagStudioToolbar__select`
- `tagStudioToolbar__mode`
- `tagStudioToolbar__selected`
- `tagStudioToolbar__result`

Use this for:

- import file chooser
- mode selector
- import action button
- create/new action button
- save/import mode text
- selected file text
- success/warn/error result text

### Filter row pattern

Use `tagStudioFilters__*` for shared list filtering controls:

- `tagStudioFilters`
- `tagStudioFilters__key`
- `tagStudioFilters__searchWrap`
- `tagStudioFilters__searchInput`
- `tagStudioFilters__allBtn`
- `tagStudioFilters__groupBtn`

This pattern is intended for registry-, aliases-, and similar list pages.

### List primitive pattern

Use `tagStudioList` and `tagStudioList__*` for shared outer list structure on list-style Studio pages:

- `tagStudioList`
- `tagStudioList__head`
- `tagStudioList__headLabel`
- `tagStudioList__sortBtn`
- `tagStudioList__sortIndicator`
- `tagStudioList__rows`
- `tagStudioList__row`
- `tagStudioList__row--center`
- `tagStudioList__row--start`
- `tagStudioList__cell`
- `tagStudioList__cellTitle`
- `tagStudioList__cellMeta`
- `tagStudioList__cellLink`
- `tagStudioList__thumb`
- `tagStudioList__thumbImage`

This pattern covers:

- optional list width constraint through `--studio-list-width`
- outer header row treatment
- list container reset
- shared row spacing and divider treatment
- one-line row centering and multiline row top alignment
- common title/meta cell stacking
- common cell link treatment
- sortable header-button treatment
- fixed thumbnail frame geometry

Page-specific row internals, column templates, chips, and actions should stay in the page namespace.

Baseline versions:

- simple list: no header row, used for short obvious collections
- sortable list: sortable columns use `tagStudioList__sortBtn` and show direction with `tagStudioList__sortIndicator`
- dense list: works-index style scan table using `tagStudioList--dense`, `--text-xs` type, no row dividers, sortable columns, and `tagStudioList__cellTitle` for the bold title column
- thumbnail list: first column uses `tagStudioList__thumb`; sorting may be controlled outside the list with separate buttons or segmented controls

Alignment and width rules:

- use `tagStudioList__row--center` for one-line rows
- use `tagStudioList__row--start` for rows that may contain multiline cells
- lists fill the available width by default
- set `--studio-list-width` on `tagStudioList` when a list should be narrower than its parent
- UI primitives use `--font-small`, mapped from `--text-sm`; normal page prose outside primitives should continue to use `--font-body`, mapped from `--text-md`

### Modal form pattern

Use `tagStudioForm__*` for form-like modal content:

- `tagStudioForm__meta`
- `tagStudioForm__fields`
- `tagStudioForm__field`
- `tagStudioForm__label`
- `tagStudioForm__readonly`
- `tagStudioForm__descriptionInput`
- `tagStudioForm__warning`
- `tagStudioForm__status`
- `tagStudioForm__impact`
- `tagStudioForm__searchWrap`
- `tagStudioForm__key`
- `tagStudioForm__selected`

This covers shared modal form structure, not page-specific content.

### Message and result pattern

Use the shared message/status classes for status, warning, hint, and result copy:

- `tagStudio__contextHint`
- `tagStudio__status`
- `tagStudio__saveWarning`
- `tagStudio__saveResult`
- `tagStudioToolbar__result`
- `tagStudioForm__warning`
- `tagStudioForm__status`
- `tagStudioForm__impact`

This pattern now covers:

- shared message typography and spacing
- message containers should remain transparent and borderless on pages and in modals
- empty-state collapse for unused message blocks
- the editor’s combined message-container presentation, where multiple lines can live inside one shared message section
- command-specific feedback should stay local to the relevant command area rather than being routed into a distant generic message block
