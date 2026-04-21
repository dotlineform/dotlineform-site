---
doc_id: studio-ui-framework
title: "Studio UI Framework"
last_updated: 2026-04-21
parent_id: design
sort_order: 20
---

# Studio UI Framework

This document defines the shared Studio UI layer.

Start with [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start) before using this document. That short doc is the implementation preflight. This document is the deeper reference.

It covers:

- shared Studio naming boundaries
- shared Studio primitives
- shared Studio toolbar, filter, list, and modal patterns
- the current Studio modal contract and implementation boundary

Site-wide interaction defaults, docs-viewer UI standards, and public-search UI standards live in [UI Framework](/docs/?scope=studio&doc=ui-framework).

Related references:

- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [CSS Primitives](/docs/?scope=studio&doc=css-primitives)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

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
- clickable pill-like controls are not buttons in this system and should be defined through the pill primitive layer instead
- buttons do not need to live inside a toolbar; toolbar is an optional composition primitive rather than part of the button contract
- modal action buttons should remain subsets of the shared button primitive
- button-related status, warning, and success copy should stay adjacent to the related command area, either on the same row or in a dedicated row immediately below it

Use these as the default contract for:

- page and modal action buttons such as `Add`, `Save`, `Import`, `Create`, `OK`, and `Cancel`
- text inputs and search inputs
- modal action rows

Input rule:

- `tagStudio__input` is the shared field shell for text entry, native select controls, and readonly field display
- use placeholder text for muted default text on text-like fields, and `tagStudio__input--defaultValue` when a control such as a select or readonly display needs the same muted default-value treatment
- `tagStudioField` owns width, label placement, and add-on button composition rather than pushing that layout into the base input class
- the default field width is `18rem`; use a local `--field-width` override for deliberate exceptions and `tagStudioField--fill` when the field should take the remaining row width
- text inputs, selects, and stepped numeric controls should keep the same control height as the small Studio button
- numeric data should still default to plain input boxes; do not infer step buttons or native number-widget UI from storage type alone
- disabled means temporarily unavailable because another page state is incomplete; values that are always display-only should use `tagStudio__input--readonlyDisplay` instead of the disabled state
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

### List shell pattern

Use `tagStudioList__*` for shared outer list structure on list-style Studio pages:

- `tagStudioList__head`
- `tagStudioList__headLabel`
- `tagStudioList__rows`
- `tagStudioList__row`

This pattern covers:

- outer header row treatment
- list container reset
- shared row spacing and divider treatment

Page-specific row internals, columns, chips, and actions should stay in the page namespace.

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

## Studio Modal Types

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

## Studio Modal Selection Rule

Choose the simplest modal type that fits the interaction:

1. Use `confirm` for a simple decision.
2. Use `confirm-detail` when the user needs impact context before deciding.
3. Use `form` when the user must enter or edit data.
4. Use `patch-preview` when the user must inspect or copy generated output.

Do not introduce a new modal type unless one of the above cannot express the interaction without awkward conditional behavior or mixed responsibilities.

## Studio Modal Implementation

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

### Shared Shell Renderer

The same module also provides shared modal shell renderers for page-controlled modals:

- `renderStudioModalFrame(...)`
- `renderStudioModalActions(...)`

Use these when a page needs to keep its own refs, visibility toggling, or multi-step workflow, but should still render the same modal chrome:

- backdrop
- dialog surface
- title placement
- body slot
- action row layout

This keeps modal shell markup consistent without forcing all Studio modals into the same promise-based interaction flow.

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
  used for aliases delete confirmation
- `confirm-detail`
  used for aliases promote/demote preview confirmation and registry demote confirmation
- `form`
  used for aliases promote group selection and demote target entry
- `patch-preview`
  shared shell renderer used for registry, aliases, and editor patch/save preview modals

Studio should continue to use these modal types rather than adding new one-off dialogs or reintroducing native `confirm(...)` and `prompt(...)` flows.

### Current Status

- shared modal controller and shell renderer are in use across the editor, registry, and aliases pages
- shared modal state now uses `data-state` rather than page-specific `.is-*` presentation classes
- shared non-modal primitives cover toolbar, filters, list shell, and modal form internals
- lighter Studio pages such as `series-tags`, `tag-groups`, and `studio-works` follow the same role/state contract where applicable
- remaining work is manual browser verification of the current Studio pages, not more framework design

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

### Shared Shell Integration Notes

Registry, aliases, and the editor now use the shared shell renderer for their persistent custom modals.

Current interaction boundary:

1. Page controllers decide when the modal is shown or hidden.
2. `studio-modal.js` provides the common frame and action-row markup.
3. Page controllers keep their own refs, field wiring, preview text, and status rendering.
4. Domain/service modules continue to own validation, preview data, and mutations.

This preserves the clean separation:

- shared modal shell in the UI framework
- application-specific contents and behavior in page/domain/service code

## What Stays Studio Page-Specific

These should remain page-specific unless another page genuinely needs the same structure:

- registry row/header layout
- alias row/header layout
- series tag editor suggestion content
- editor work selection layout
- page-specific action chip groupings

Do not move page-specific list structure into the shared layer just because two pages are both "lists". Share only the repeated UI primitives.

## Studio Review Rules

When adding or changing Studio UI:

1. Start by checking whether an existing shared primitive already matches the intent.
2. If not, add a new shared primitive only when the pattern is expected to be reused.
3. Do not reuse `tagRegistry__*` classes in aliases, or `tagAliases__*` classes in registry, for shared styling.
4. Keep layout-only exceptions local to the page namespace.
5. Keep UI copy in `assets/studio/data/studio_config.json`, not in CSS or hard-coded duplicated markup.

## Current Studio Shared Coverage

Current Studio cleanup standardizes:

- list-page toolbar/import blocks on `tagStudioToolbar__*`
- list-page search/filter controls on `tagStudioFilters__*`
- shared list shells on `tagStudioList__*`
- modal form internals on `tagStudioForm__*`
- lighter pages bind through `data-role` and `data-state` instead of style-class behavior hooks where they expose interactive controls

### Implementation Boundary

The same rule used for modal refactoring applies here:

- shared Studio UI modules and CSS own the shell and styling contract
- page controllers own rendering decisions and event wiring
- domain/service modules own validation, filtering rules, and mutation behavior

Shared styling should not be implemented by borrowing another page's class names. If two pages use the same UI intent, the primitive belongs in the shared `tagStudio*` layer.
