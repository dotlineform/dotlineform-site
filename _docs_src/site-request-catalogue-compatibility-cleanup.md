---
doc_id: site-request-catalogue-compatibility-cleanup
title: Compatibility Cleanup
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: change-requests
sort_order: 101
---
# Compatibility Cleanup

Status:

- in progress

## Summary

This request tracks cleanup of retained catalogue compatibility paths that are larger than the retired-field cleanup in [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping).

The field-aware registry work should not preserve obsolete source fields, but it also should not absorb a broader generator or source-model refactor. Task 1A in the field-aware request can remove clearly retired fields and record obvious cleanup opportunities. This request owns the deeper compatibility cleanup after those immediate removals are understood.

## Problem

The catalogue pipeline still has compatibility surfaces from earlier workbook-led and transitional JSON-source flows.

Known examples to review:

- workbook-shaped source headers and schema helpers in `scripts/catalogue_source.py`
- internal sheet-like projection used by `scripts/generate_work_pages.py`
- retained source fields that may only exist for old workbook compatibility
- Studio lookup payloads that expose full source records, including retired or compatibility-only fields
- deprecated workbook-led scripts and docs that should remain clearly separated from live workflow behavior
- work file/link compatibility rows retained after `Works.downloads` and `Works.links` became canonical
- the active bulk-import workbook adapter for `data/works_bulk_import.xlsx`, which should remain one-way into canonical JSON even if its implementation still shares workbook-era helpers

Task 1A in the field-aware build scoping request removed confirmed-retired source fields from canonical source, source schema helpers, write allowlists, and generated lookup payloads:

- `works.<work_id>.work_prose_file`
- `works.<work_id>.series_title`
- `series.<series_id>.series_prose_file`

Remaining compatibility cleanup should focus on the broader surfaces above, not on preserving those retired fields.

These surfaces may be harmless individually, but together they make it harder to tell which fields are active source model, editor-only context, derived data, migration-only compatibility, or retired debt.

## Goals

- identify every retained catalogue compatibility path that still affects source loading, generated artifacts, lookup payloads, or docs
- classify each compatibility path as active, migration-only, deprecated clean-exit, or removable
- remove compatibility paths that are no longer needed
- keep any retained migration-only paths narrow, documented, and outside the field-to-artifact registry
- preserve deterministic generated output while cleanup happens
- make live JSON-source workflow boundaries easier to understand
- apply cleanup as if the current scripts were being created without the old `data/works.xlsx` pipeline, so compatibility artifacts are removed rather than relocated under new names

## Non-Goals

- do not block the initial field-aware registry on this broader cleanup
- do not change public runtime payload contracts without an explicit compatibility decision
- do not remove deprecated user-facing commands unless their clean-exit contract is replaced or intentionally retired
- do not redesign catalogue editing workflows as part of this cleanup

## Task List

### Task 1. Inventory Retained Compatibility Paths

Status:

- completed

List compatibility surfaces in code, canonical source JSON, generated Studio lookup payloads, generated public JSON, deprecated scripts, and docs.

Inventory doc:

- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)

The inventory should distinguish:

- active live-source fields
- editor-only fields
- derived fields
- migration-only compatibility fields
- deprecated clean-exit commands
- retired fields ready for removal

Initial Task 1 finding:

- `data/works_bulk_import.xlsx` is an active import adapter, not the retired canonical `data/works.xlsx` workflow. Any workbook-era implementation reused by bulk import should be narrowed into the new JSON-source pipeline boundary rather than removed as legacy by default.

### Task 2. Decide Retention Policy

Status:

- completed

For each retained path, decide whether to remove it, narrow it, or keep it as documented migration/deprecated behavior.

Particular decisions:

- move workbook row helpers such as `header_map` and `cell` closer to the active bulk-import adapter
- remove `data/works.xlsx` provenance from catalogue source metadata
- remove stale `data/works.xlsx` references from current docs
- remove `work_files` and `work_links` compatibility maps after confirming current flows no longer depend on them
- keep deprecated clean-exit paths only where they still provide useful guidance during transition

Task 3 implementation order and verification matrix:

- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)

### Task 3. Remove Or Narrow Compatibility Surfaces

Status:

- in progress

Implemented slices:

- moved workbook row helpers such as `header_map` and `cell` into the active bulk-import adapter boundary in `scripts/catalogue_workbook_import.py`
- removed obsolete `data/works.xlsx` provenance from catalogue source metadata and source metadata generation
- removed `work_files` and `work_links` compatibility maps from live source records, validation, delete previews, lookup invalidation, and activity summaries

Apply approved removals in small slices.

Expected cleanup areas:

- source schema and normalization helpers
- lookup payload builders
- generator adapter/projection code
- deprecated script guidance
- docs that still describe workbook-led paths as live behavior

### Task 4. Verify Generated Output Stability

Status:

- planned

Run targeted previews and generated-output checks after each cleanup slice.

Acceptance checks:

- live JSON-source rebuild previews still work
- deprecated user-facing commands still exit cleanly with guidance, unless intentionally retired
- generated public artifacts remain deterministic
- Studio lookup payloads still provide fields required by current editors
- field-aware registry rules do not include migration-only or retired compatibility fields

## Benefits

- the active catalogue source model becomes easier to reason about
- field-aware build rules avoid inheriting old compatibility debt
- Studio payloads expose less obsolete surface area
- future generator changes can target live JSON-source behavior instead of workbook-era assumptions

## Risks

- removing a compatibility path too early could break a deprecated but still useful workflow
- narrowing lookup payloads could expose hidden editor dependencies
- refactoring generator projection code could create broad generated-output churn

Mitigation:

- classify before removing
- keep Task 1A retired-field cleanup separate from this broader request
- make compatibility removals incremental
- verify deprecated command behavior and JSON-source previews after each slice
