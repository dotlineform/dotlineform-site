---
doc_id: studio-ui-framework-modal-implementation
title: Modal Implementation
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: ui-catalogue
---
# Modal Implementation

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
- shared non-modal primitives cover toolbar, filters, list, and modal form internals
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
