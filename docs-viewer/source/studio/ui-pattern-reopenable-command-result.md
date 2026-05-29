---
doc_id: ui-pattern-reopenable-command-result
title: Reopenable Command Result Pattern
added_date: 2026-05-05
last_updated: 2026-05-15
parent_id: ui-catalogue
---
# Reopenable Command Result Pattern

This composition pattern covers command results that open in a modal and can be reopened while the visible status still refers to the same result.

Current live examples:

- `/studio/data-sharing/review/?mode=manage`

Demo reference:

- [Reopenable command result pattern demo](/studio/ui-catalogue/demos/patterns/reopenable-command-result/)

## Scope

Use this pattern when:

- a command generates a reviewable result
- the result is detailed enough to belong in a modal
- the user may reasonably close the modal before finishing review
- rerunning the command would be unnecessary or could mutate filesystem output
- the page can store the exact payload needed to reopen the same result

Do not use this pattern for:

- confirmation dialogs
- destructive actions
- stale write previews
- results whose input context has changed
- status messages that are purely transient and have no useful modal detail

## Anatomy

The pattern has four parts:

- command control
- adjacent status message
- small `results` action beside the current success message
- modal result payload stored by the route

The `results` action should read as a lightweight recovery affordance, not a second primary command.
In current routes it can use the pill visual treatment.

## Lifecycle Contract

The route stores a result payload only after the command succeeds.

The route shows the `results` action only while:

- the stored result exists
- the visible status message still describes that stored result
- the input context that produced the result has not changed

The route hides or clears the action when:

- the user changes the source input
- a new command starts
- an error replaces the success status
- another operation becomes the current context
- the route is reset

The stored payload should contain the data required to reopen the modal, not just the status text.

## Implementation Notes

Current demo implementation lives in:

- `studio/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `studio/ui-catalogue/assets/js/ui-catalogue-demo.js`
- `studio/ui-catalogue/demos/patterns/reopenable-command-result/index.md`

The UI Catalogue demo uses `uiCatalogueDemo*` classes and demo-owned modal JavaScript. Treat the demo as the pattern reference, then map the lifecycle, result storage, modal helper, and class names into the live route.

The Library import implementation stores:

- modal title
- summary text
- count rows
- issue messages

It then renders the same result modal from either:

- the original command completion
- the status-adjacent `results` action

The server owns durable result wording, such as context-aware singular/plural text.
The route owns visibility and invalidation of the `results` action.

## Benefits

- keeps dense command pages free of persistent result panels
- lets the user recover a dismissed modal without rerunning the command
- makes the status line useful without making it a second report surface
- keeps modal result details aligned with the command that generated them

## Risks

- stale results can appear if invalidation rules are loose
- the status row can become noisy if every success message gets an action
- storing partial modal state can drift from the original server result
- this pattern should remain tied to reviewable results, not routine status messages

## Migration Notes

Related historical notes from the retired Studio UI rules log now live in structured docs-log entries.
Move stable guidance here when retiring that log content.
