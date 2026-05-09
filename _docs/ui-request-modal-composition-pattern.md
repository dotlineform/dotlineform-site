---
doc_id: ui-request-modal-composition-pattern
title: Modal Composition Pattern Request
added_date: 2026-05-10
last_updated: 2026-05-10
ui_status: draft
parent_id: change-requests
sort_order: 190
---
# Modal Composition Pattern Request

Status:

- requested

## Summary

Define a shared modal composition pattern for Studio and Docs Viewer interfaces.

The pattern should make modals consistent as UI containers while keeping domain actions owned by the page or command that opens the modal.

## Reason

Recent Docs Viewer management work exposed a useful boundary: the Edit button should own the write action, while the modal should only collect and return selections. That boundary keeps mutation behavior near the page command that requested it and prevents modal components from becoming hidden application controllers.

The same principle should be made explicit across Studio UI guidance so future modals do not drift into inconsistent shells, duplicated controls, or action ownership that is hard to audit.

## Goals

- define one consistent modal shell for Studio and Docs Viewer management surfaces
- keep modal controls visually and behaviorally consistent with equivalent controls on the page
- define modals as selection/input collectors that return values to the opener
- keep create/update/delete/archive/show actions owned by the page control or command that opened the modal
- document when a modal may validate local input versus when validation belongs to the owning page/service flow
- update UI audit guidance so page audits check modal composition patterns, not only page-level controls

## Non-Goals

- converting every existing modal in the first implementation slice
- creating a new modal framework before inventorying current modal usage
- changing service endpoints only to fit the modal pattern
- using modal guidance as a substitute for route-specific workflow design

## Proposed Pattern

Modal shell:

- use the same structural shell for title, optional metadata, body, action row, close behavior, focus return, and Escape handling
- keep backdrop, close button, action alignment, and responsive sizing consistent
- avoid page-specific modal chrome unless a real workflow difference requires it

Controls:

- use the same primitive style and state behavior as equivalent page controls
- keep labels, selected states, disabled states, listbox sizing, checkboxes, and validation messages consistent with page-level controls
- use configured UI text for visible labels and action copy

Ownership:

- the opener owns the action
- the modal returns selections, input values, or a cancel result
- the modal may perform local completeness checks such as required text or valid option selection
- the modal should not directly perform domain writes, rebuilds, archive/delete operations, or other service mutations
- service payload assembly belongs to the opener or page-level command handler

Audit coverage:

- UI audits should include a modal composition section when the audited route opens modals
- audits should check shell consistency, control consistency, focus/escape behavior, responsive fit, and action ownership
- audit findings should distinguish route-specific workflow issues from shared modal-pattern issues

## First Implementation Slice

1. Inventory existing Studio and Docs Viewer modals.
2. Identify the shared shell already closest to the desired pattern.
3. Write the stable pattern under the UI composition-pattern docs.
4. Update UI audit guidance to include modal composition checks.
5. Convert only one representative modal if needed to prove the guidance.

## Benefits

- keeps modal UX predictable across Studio and Docs Viewer surfaces
- prevents modal components from hiding mutation behavior
- makes UI audits more useful for composed workflows, not just standalone page controls
- reduces duplicated modal styling and one-off interaction fixes

## Risks

- too much abstraction could slow route-specific workflow fixes
- converting existing modals in bulk could introduce regressions in local write flows
- action ownership needs clear naming so code does not become harder to follow

## Open Questions

- Which current modal shell should become the canonical base?
- Should the Docs Viewer metadata modal and Studio command-result modal share the exact same shell, or only the same composition rules?
- Should modal-return contracts be documented as JavaScript helper APIs, prose rules, or both?
- Should UI audits require a modal screenshot/check whenever a route has modal behavior?
