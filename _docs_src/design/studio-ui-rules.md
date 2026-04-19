---
doc_id: studio-ui-rules
title: Studio UI Rules And Decision Log
last_updated: 2026-04-19
parent_id: design
sort_order: 21
---

# Studio UI Rules And Decision Log

This document is the working record for Studio UI issues, decisions, and permanent standards that emerge from real fixes.

Use it to separate:

- one-off page corrections
- repeated issues that should become shared Studio rules
- local Codex changes that would otherwise disappear without PR discussion

Use this as the single capture surface for Studio UI work:

- open UI observations from IAB review
- one-off route corrections
- systemic findings that should become permanent rules
- local Codex change notes for UI work that did not go through PR review

## Purpose

Use this document to:

- capture open UI issues as they are found
- record the triage note for a UI issue
- decide whether the issue is local or systemic
- capture the permanent rule when the issue should affect future work
- record where the rule is enforced
- leave a short local change log when work is done directly with Codex instead of through PR review

## Triage Labels

Every UI issue should start with one triage note:

- `one-off`
  The problem belongs to one route or one piece of markup only.
- `systemic`
  The problem exposes a shared primitive, token, layout pattern, or behavior that should be corrected at the design-system level.
- `pending`
  The issue has not yet been classified.

## Local Workflow

Because the primary workflow is local Codex work rather than PR-based review, each systemic fix should leave evidence in this document.

For local work, record:

- the route where the issue was seen
- the triage note
- the reasoning behind the classification
- the exact shared rule or non-rule decision
- the files changed
- the local verification method
- any follow-up work still needed

If a similar issue appears a second time, promote it to `systemic` unless there is a clear reason not to.

## Workflow

Use this sequence for Studio UI work:

1. Capture the issue here when it is observed in IAB or local browser testing.
2. Add the initial triage note as `pending`, `one-off`, or `systemic`.
3. Fix the issue locally.
4. Update the same entry with the outcome:
   - keep it `local-only` if it was truly route-specific
   - mark it `adopted` if it became a permanent Studio rule
5. Record the files changed and the local verification method.

## Working Rule

Use this decision test:

- if the fix should change only one route, keep it local
- if the fix changes a shared class, shared token, shared layout primitive, or common interaction, record it here as a permanent rule

## Entry Template

```text
## UI Rule Log YYYY-MM-DD / UI-###

- status: open | adopted | local-only | superseded
- route:
- issue:
- triage: pending | one-off | systemic
- reasoning:
- permanent rule:
- enforcement point:
- files changed:
- local verification:
- follow-up:
```

## Current Rules And Log

Add new entries at the top of this section.

## UI Rule Log 2026-04-19 / UI-001

- status: adopted
- route: `/studio/catalogue-work/`
- issue: the `New Detail` action looked visually inconsistent beside the shared Studio search input and adjacent section actions; the reported symptom was non-standard button height
- triage: systemic
- reasoning: the first pass treated the issue as local layout only, but the more important finding was that shared Studio buttons were not explicitly using `border-box` sizing. That meant anchor-backed buttons using `tagStudio__button` could render at a different effective height from standard Studio controls even when they appeared to share the same class.
- permanent rule: shared Studio action controls must derive their geometry from the shared primitive, not from route-specific compensation. If a control uses `tagStudio__button`, its height and box model must match the Studio control token contract whether the element is a native `<button>` or an `<a>` styled as a button.
- enforcement point: `assets/studio/css/studio.css` in the shared `.tagStudio__button` rule
- files changed:
  - `assets/studio/css/studio.css`
  - `studio/catalogue-work/index.md`
- local verification:
  - inspect the route in the in-app browser at `/studio/catalogue-work/`
  - compare `New Detail`, `New File`, `New Link`, and nearby search/input controls
  - confirm the shared control height is visually consistent after refresh
- follow-up:
  - when a future UI issue touches a shared primitive, record the decision here even if the visible defect was first reported on one route
  - prefer fixing shared primitives before adding page-specific overrides

### Example Triage Note For This Issue

Use this structure when the issue first appears:

```text
route: /studio/catalogue-work/
problem: `New Detail` button appears visually inconsistent; reported symptom is non-standard height
initial triage: pending
first hypothesis: local layout mismatch in the work-details header row
after inspection: systemic
reason: shared `tagStudio__button` sizing contract is incomplete for anchor-backed buttons
action: fix shared button primitive, then record permanent rule in studio-ui-rules.md
```

### Subsequent Actions For This Issue

1. Fix the immediate UI defect.
2. Decide whether the root cause lives in page markup or a shared primitive.
3. If shared, update the shared primitive rather than compensating on one route.
4. Add or update the rule entry in this document.
5. Recheck the original route and at least one sibling route that uses the same primitive.
