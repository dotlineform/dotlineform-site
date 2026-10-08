---
draft: false
doc_id: d-20261008-110540-64f8f0
title: Work Deletion Delivery
added_date: "2026-10-08 11:05:40"
last_updated: "2026-10-08 11:05:40"
parent_id: d-20260428-000000-f5ff18
---
# Work Deletion Delivery

Implemented and reviewed; awaiting user manual acceptance. Tests are pending separate review and remain untouched.

## Requirements

Delete removes all selected saved Works through one confirmation and one awaited request. Single and multiple selection share the same identity-based operation: current metadata or image changes do not invalidate the selected IDs, and no loaded Work or Gallery revision is required. Canonical Works and their current Gallery memberships are removed together. Retain the displayed Series and layout after updating the editor. Preserve shared media and Gallery/Series definitions; generated readers update through explicit Refresh Catalogue. Series deletion retains its existing rules.

## Deliverables

The Works editor enables Delete for multiple selection. Its confirmation identifies the exact selection without a server preview. The deletion service reads current canonical data once and carries the validated result through the existing transaction and completion owners. Remove unused Catalogue delete-preview plumbing, generic request-ID aliases and the unused browser preview/old Save-Build helpers. Durable behavior belongs to [Catalogue Work Editor](../Catalogue_Work_Editor.md), request shapes to [Local Studio APIs](../Local_Studio_APIs.md), and mutation/completion ownership to [Catalogue Services](../Catalogue_Services.md).

## Process

Select one or multiple saved Works, click Delete, review the ID or count/ID list and confirm. Cancel retains the selection and draft. Apply removes the selected identities and current memberships; invalid requests, unknown IDs or invalid resulting data stop before writes. On a confirmed deletion, remove those Works from the live editor even if later local completion fails, and display the incomplete step. Refresh Catalogue remains separate.

## Delivery Steps

- [x] WD-0 — Readiness: the existing single-delete owner and multiple-selection state are available; the slice is local Catalogue deletion. The user agreed that single and multiple Work deletion use identity, without revision matching. Tests remain unapproved. No change to Series revision policy, media cleanup or publication is required.
- [x] WD-1 — Implementation and selected evidence: shared Work-ID array request, combined current-record/membership removal, multiple-selection button and editor-state updates, and retired preview/aliases are implemented. Explicit Python lint and syntax checks passed for the six changed service/server modules and the completion owner's docstring update; JavaScript lint passed for the five changed browser modules; whitespace checks passed. An import-only diagnostic of `studio_catalogue_api` and `studio_app_config` passed after the service dependency change; it checks module wiring, not mutation behavior. Commands took less than one second each, with no network or canonical mutations and only ordinary ignored compiler cache writes. No tests or behavior checks were created or run.
- [x] WD-2 — Code review: traced exact selected identities through current-source loading, membership removal, allowlisted combined writes, shared completion, returned IDs and editor clearing. Reviewed cancellation, missing/duplicate identities, last-member deletion, saved-but-incomplete handling, and retained Series revision/member rules. Added response-ID string validation and removed unused plan identity fields; affected lint/syntax checks passed again. Active code/config has no references to retired Catalogue preview helpers or request aliases. No blocking findings remain; mutation and browser paths have source-review evidence only.
- [x] WD-3 — Closeout: durable authoring, source-model, service and API contracts are reconciled. Restart Local Studio and force-reload the editor, then manually review single/multiple confirmation, cancellation and intended deletions. Static checks do not establish runtime mutation behavior. Retain this delivery for manual acceptance; its lasting destinations are listed above, and later archive/removal requires user action.

## Follow-on

Tests still require their own reviewed specification under [Test Contract Discipline](../Test_Contract_Discipline.md). Existing deletion tests encode retired preview, Detail and Series-assignment contracts and are unreviewed for current behavior; this delivery does not update them. No real deletion, browser automation, Catalogue Refresh, Publish, commit or push is authorized or performed as verification.
