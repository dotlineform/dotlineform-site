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

## Modal Types

Studio should use a small standardized set of modal types. The framework defines the modal shell, required slots, and UI interaction contract. Application code defines the actual content, validation rules, and mutation behavior.

### `confirm`

Use for:

- a single yes/no decision
- low-complexity actions
- actions where one short sentence of context is enough

Required UI slots:

- title
- body text
- primary action
- cancel action

Expected UI contract:

- no free-form user input
- primary action may be destructive
- action labels should be explicit, for example `Delete` rather than `OK`

Application logic stays outside the modal:

- eligibility checks
- the actual delete/promote/dismiss operation
- status handling after confirm

### `confirm-detail`

Use for:

- destructive or high-impact actions
- actions that affect multiple records
- actions that need preview, warning, or impact text before confirmation

Required UI slots:

- title
- summary/body text
- impact or warning area
- primary action
- cancel action

Expected UI contract:

- no free-form user input
- may show multiple paragraphs or structured status/impact blocks
- should be used instead of native `confirm(...)` when the action is a core Studio workflow

Application logic stays outside the modal:

- preview generation
- impact computation
- mutation rules
- server or patch execution

### `form`

Use for:

- create/edit flows
- actions that require user input
- flows with inline validation or selection widgets

Required UI slots:

- title
- fields area
- warning and/or validation area
- status area
- primary save/create action
- cancel action

Expected UI contract:

- input fields live inside the modal
- validation messages are rendered inline
- the primary action can be enabled/disabled based on validation state

Application logic stays outside the modal:

- validation rules themselves
- mapping form state to domain payloads
- persistence and patch fallback logic

### `patch-preview`

Use for:

- read-only generated output
- copy-and-paste workflows
- fallback flows where the user must manually apply a patch or snippet

Required UI slots:

- title
- explanation/body text
- read-only code or snippet area
- copy action
- close action

Expected UI contract:

- no editing inside the modal
- should present output clearly and preserve formatting
- copy action is the main primary action

Application logic stays outside the modal:

- snippet generation
- deciding when patch mode is needed
- post-copy status handling

## Modal Selection Rule

Choose the simplest modal type that fits the interaction:

1. Use `confirm` for a simple decision.
2. Use `confirm-detail` when the user needs impact context before deciding.
3. Use `form` when the user must enter or edit data.
4. Use `patch-preview` when the user must inspect or copy generated output.

Do not introduce a new modal type unless one of the above cannot express the interaction without awkward conditional behavior or mixed responsibilities.

## Modal Implementation

### Shared Controller

Studio modal behavior should be implemented through a shared controller module:

- `assets/studio/js/studio-modal.js`

The shared controller is responsible for:

- mounting and unmounting modal DOM
- rendering the modal shell for supported modal types
- collecting generic user intent or field values
- resolving confirm/cancel/submit results back to the caller

The shared controller is not responsible for:

- validation rules
- preview computation
- mutation logic
- patch generation
- save/delete/promote/demote behavior

### Integration Pattern

Each page/controller should follow this flow:

1. Build the modal view model from current application state.
2. Open the appropriate Studio modal type.
3. Await the modal result.
4. Pass the result into domain/service logic.
5. Render the resulting success, warning, or error state back into the page.

This keeps modal rendering in the UI layer while keeping business rules in the existing domain/service modules.

### Supported Modal Types Implementation Status

- `confirm`
  Phase 2: used for aliases delete confirmation
- `confirm-detail`
  Phase 3: used for aliases promote/demote preview confirmation and registry demote confirmation
- `form`
  Phase 2: used for aliases promote group selection and demote target entry
- `patch-preview`
  Phase 1: controller scaffold only

Later phases should replace native `confirm(...)` and `prompt(...)` calls with these modal types rather than adding new one-off dialogs.

### Migration Status

- Phase 1
  Added shared modal controller scaffold and documented modal contracts.
- Phase 2
  Replaced aliases native dialogs with Studio modal types:
  - alias delete uses `confirm`
  - alias promote uses `form` then `confirm-detail`
  - alias-side tag demote uses `form` then `confirm-detail`
- Phase 3
  Replaced registry demote native confirm with Studio `confirm-detail`, using page-root host placement.
- Phase 4
  Planned: normalize existing custom modal implementations onto the shared controller contract.
- Phase 5
  Planned: complete regression coverage and close out modal-system docs.

### Aliases Integration Notes

Aliases now uses the shared modal controller for native-dialog replacement only.

Current interaction boundary:

1. `tag-aliases.js` prepares modal view-model data.
2. `studio-modal.js` renders the modal shell and collects user decisions or field values.
3. `tag-aliases.js` validates the returned values or preview requirements.
4. `tag-aliases-service.js` performs the actual mutation.

This phase intentionally keeps aliases business rules in the page/service layer rather than moving them into the modal controller.

### Registry Integration Notes

Registry demote now uses the shared modal controller for the final confirmation step only.

Current interaction boundary:

1. `tag-registry.js` keeps the existing target-tag selection workflow and preview generation.
2. `studio-modal.js` renders the final `confirm-detail` shell inside the registry page root.
3. `tag-registry.js` handles the returned confirm/cancel result and then calls the mutation service.

This phase intentionally leaves registry demote validation and mutation logic outside the modal controller.

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
