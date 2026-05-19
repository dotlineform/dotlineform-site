---
doc_id: studio-ui-framework-modal-contract
title: Studio UI Framework Modal Contract
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: ui-catalogue
sort_order: 5500
---
# Studio UI Framework Modal Contract

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
