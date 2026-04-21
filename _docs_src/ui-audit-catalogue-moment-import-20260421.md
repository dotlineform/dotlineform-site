---
doc_id: ui-audit-catalogue-moment-import-20260421
title: "UI Audit: Catalogue Moment Import (2026-04-21)"
last_updated: 2026-04-21
parent_id: ui-audits
sort_order: 10
---
# UI Audit: Catalogue Moment Import (2026-04-21)

Page:

- `/studio/catalogue-moment-import/`

Outcome:

- `non-conforming`

## Coverage Summary

- buttons: `authoritative`
  The page uses the shared `tagStudio__button` command-button primitive.
- fields/inputs: `authoritative`
  The filename field uses the shared input shell, but the preview summary display values do not yet use the current readonly-display treatment.
- panels/surfaces: `authoritative`
  The page uses shared `tagStudio__panel` shells.
- summaries/messages: `framework-only`
  Message/status treatment is covered by the shared Studio framework, but preview summary display values still need to match the shared readonly-display rule.
- list or result shells: `partial`
  The preview-details area relies on inherited `catalogueWorkDetails__*` structure rather than a fully published shared primitive.
- route-specific compositions: `coverage-gap`
  The page grid and action-row layout still borrow `catalogueWork*` route classes rather than using a shared `tagStudio*` composition or a page-local namespace.

## Findings

1. `medium` `non-conforming` preview summary display values
   source rule:
   [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework) input rule requiring display-only summary/value surfaces to use Readonly Display
   evidence:
   `assets/studio/js/catalogue-moment-import.js:54` renders summary values as `tagStudio__input tagStudioForm__readonly` at `assets/studio/js/catalogue-moment-import.js:88`, and the older muted surface is still defined in `assets/studio/css/studio.css:1679`
   why it matters:
   The preview summary is display-only, so using the older muted readonly surface conflicts with the current shared distinction between disabled state and always-readonly display.
   fixability:
   `local-now`

2. `medium` `coverage-gap` route composition and namespace reuse
   source rule:
   [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework) naming-boundary rule
   evidence:
   `studio/catalogue-moment-import/index.md:12` uses `catalogueWorkPage`, `catalogueWorkPage__grid`, `catalogueWorkPage__actions`, `catalogueWorkSummary`, and `catalogueWorkDetails`, with matching CSS in `assets/studio/css/studio.css:1863` and `assets/studio/css/studio.css:2070`
   why it matters:
   The page currently depends on another route family’s layout namespace, which makes it harder to tell whether a future issue belongs in shared Studio compositions or in one borrowed local pattern.
   fixability:
   `blocked`
   The page can only fully conform here after the shared import/result-shell composition is defined more clearly.

## Cleanup Opportunities

- redundant local CSS:
  The page should stop depending on `tagStudioForm__readonly` for preview summary values once the summary renderer switches to Readonly Display.
- redundant local markup:
  No immediate redundant wrappers were identified for the current summary fix, but the broader `catalogueWork*` structure looks like inherited route reuse rather than a deliberate long-term contract.
- shared CSS or JS that can now replace local behavior:
  `tagStudio__input--readonlyDisplay` can replace the older summary-value treatment immediately.
- follow-up steps:
  1. Switch the preview summary renderer to `tagStudio__input--readonlyDisplay`.
  2. Decide whether the page grid, action row, and result-shell layout should become a shared Studio composition.
  3. If that shared composition is formalized, remove the borrowed `catalogueWork*` namespace from this route and any similar import-style pages.

## Verification

- routes checked:
  - `http://127.0.0.1:4000/studio/catalogue-moment-import/`
- desktop checks run:
  - Playwright Chromium at `1440x1200`
  - confirmed no horizontal overflow
  - confirmed the page loaded with shared buttons, panels, and input
  - measured control heights: buttons about `32.94px`, input about `32px`
- mobile checks run:
  - Playwright Chromium at `390x844`
  - confirmed no horizontal overflow
  - confirmed the action row remained usable and the summary panel stacked below the form area
- code inspection:
  - `studio/catalogue-moment-import/index.md:12`
  - `assets/studio/js/catalogue-moment-import.js:54`
  - `assets/studio/css/studio.css:1651`
  - [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- blocked checks:
  - the local catalogue write service was unavailable during the audit, so preview/apply could not be exercised end-to-end
  - the live page therefore remained in its disabled state with the status message `Local catalogue server unavailable. Moment import is disabled.`

## Process Notes

- The audit process was usable as a real page review.
- It successfully distinguished:
  - a true covered-area non-conformance
  - a genuine standards coverage gap
  - blocked runtime verification
  - cleanup that could happen now versus later
- One process gap remains:
  - the conformance spec would benefit from one explicit line describing how to choose the overall outcome when a page has both real non-conformance and coverage gaps; this audit used `non-conforming` because a covered-area rule is already violated.
