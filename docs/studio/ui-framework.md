# Studio UI Framework

This document defines the shared UI layer for Studio pages.

The goal is consistency without introducing a heavy component system. Studio pages still render their own markup in JS, but they should compose a small set of shared CSS primitives rather than reusing another page's class names.

## Naming Boundary

- `tagStudio__*`
  Shared Studio primitives such as buttons, inputs, chips, panels, popups, and modal shells.
- `tagStudioToolbar__*`
  Shared import/action toolbar pattern used by registry- and alias-style pages.
- `tagStudioFilters__*`
  Shared filter/search row pattern used by list pages.
- `tagStudioForm__*`
  Shared modal form layout primitives such as fields, labels, warnings, statuses, and selected-chip areas.
- `tagRegistry__*`, `tagAliases__*`, `tagStudioSuggest__*`, `seriesTags__*`
  Page- or feature-specific layout and presentation only.

Rule of thumb: if two Studio pages need the same visual treatment, the class should move into the shared `tagStudio*` layer instead of borrowing another page's namespace.

## Shared Primitives

### Base controls

Defined in `assets/studio/css/studio.css`:

- `tagStudio__panel`
- `tagStudio__input`
- `tagStudio__button`
- `tagStudio__button--primary`
- `tagStudio__chip`
- `tagStudio__key`
- `tagStudio__popup`
- `tagStudio__popupInner`
- `tagStudioModal`, `tagStudioModal__*`

These are the baseline building blocks for all Studio pages.

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

## What Stays Page-Specific

These should remain page-specific unless another page genuinely needs the same structure:

- registry row/header layout
- alias row/header layout
- series tag editor suggestion content
- editor work selection layout
- page-specific action chip groupings

Do not move page-specific list structure into the shared layer just because two pages are both "lists". Share only the repeated UI primitives.

## Review Rules

When adding or changing Studio UI:

1. Start by checking whether an existing shared primitive already matches the intent.
2. If not, add a new shared primitive only when the pattern is expected to be reused.
3. Do not reuse `tagRegistry__*` classes in aliases, or `tagAliases__*` classes in registry, for shared styling.
4. Keep layout-only exceptions local to the page namespace.
5. Keep UI copy in `assets/studio/data/studio_config.json`, not in CSS or hard-coded duplicated markup.

## Current Refactor Direction

Current Studio cleanup standardizes:

- list-page toolbar/import blocks on `tagStudioToolbar__*`
- list-page search/filter controls on `tagStudioFilters__*`
- modal form internals on `tagStudioForm__*`

Further cleanup should continue in that direction rather than adding more page-to-page class borrowing.
