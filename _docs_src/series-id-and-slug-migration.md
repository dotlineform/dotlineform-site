---
doc_id: series-id-and-slug-migration
title: "Series ID Migration"
added_date: 2026-04-01
last_updated: 2026-04-01
parent_id: ""
sort_order: 260
published: false
---
# Series ID Migration

## Purpose

This draft documents a migration away from the current series model where `series_id` acts as both:

- the internal record key
- the public URL path segment
- a user-authored slug-safe value in `works.xlsx`

The goal is to remove the authoring burden of maintaining slug-safe series identifiers while ending with a simpler catalogue model.

## Current problem

`work_id` and `series_id` do not have the same meaning.

- `work_id` is a catalogue number with real-world meaning
- `series_id` is mainly an internal join key, but is currently also a public URL token

That creates an awkward authoring workflow:

- the user mainly cares about the series title
- the project folder name is often the natural human reference
- the current workbook requires the user to hand-author a slug-safe `series_id`
- forgetting to keep `series_id` slug-safe creates validation and generation failures

The current model is technically coherent, but one field is carrying too many responsibilities.

## Agreed target model

The preferred end-state is:

- `Series.series_id`
  - numeric
  - immutable once assigned
  - internal join key
  - public route token
- `Series.title`
  - human display title
- `Works.series_ids`
  - stores numeric `series_id` values
  - acts as the join field from works to series

This is intentionally simpler than introducing a separate persisted `series_slug`.

## Why a separate `series_slug` is not required

Earlier options considered splitting routing from identity by introducing a persisted `series_slug`.

That is no longer the preferred direction.

Reasons:

- the site is a catalogue, so numeric series URLs are acceptable
- there is no strong need for public series URLs to remain human-readable
- the user does not want to keep managing a second identifier
- using numeric `series_id` for both joins and routes matches the existing `work_id` pattern more closely

Under this model:

- public series routes become `/series/<series_id>/`
- per-series artifacts can also use numeric `series_id`
- title changes do not affect URLs

## Dependency: preserve workbook formulas first

Before changing the series model, the pipeline should stop destroying workbook formulas when it writes status, date, or dimension updates.

That matters because a safer workbook write path would allow helpful formula-driven columns in `Works`, such as:

- a series title lookup column derived from numeric `series_id`
- other internal helper columns used only for editing and filtering

The intended implementation direction is:

- load one workbook with `data_only=True` for reading computed values
- load one workbook with `data_only=False` for writing cell updates while preserving formulas

This should be treated as a prerequisite for the series migration, not a follow-up cleanup.

## Proposed workbook shape

### Series sheet

Current relevant fields:

- `series_id`
- `title`
- `primary_work_id`

Proposed relevant fields:

- `series_id`
  - numeric internal id
  - also used in public series URLs
- `title`
  - display title
- `primary_work_id`
  - required for series prose resolution and primary work membership checks

### Works sheet

Current relevant field:

- `series_ids`
  - currently stores slug-like series identifiers

Proposed relevant field:

- `series_ids`
  - stores numeric `series_id` values

Optional helper fields:

- `series_titles` or equivalent formula-driven lookup column
  - authoring aid only
  - not canonical

## Runtime and generated artifact implications

The migration affects more than the workbook.

Current generated/runtime usage relies heavily on the current slug-like `series_id`, including:

- `_series/<series_id>.md`
- `assets/series/index/<series_id>.json`
- `/series/<series_id>/`
- per-work `series_ids`
- search result `href` and metadata
- Studio query parameters and tag-assignment keys

The target state should instead be:

- routes keyed by numeric `series_id`
- per-series artifact paths keyed by numeric `series_id`
- titles used for display only
- joins keyed by numeric `series_id`

Likely shape:

- route path:
  - `/series/<series_id>/`
- per-series artifact path:
  - `_series/<series_id>.md`
  - `assets/series/index/<series_id>.json`
- aggregate series index payload:
  - includes numeric `series_id` and title
- per-work payloads:
  - keep numeric `series_ids`
  - do not need a separate slug field

## Migration phases

### Phase 1. Formula-safe workbook writes

Implement workbook write behavior that preserves formulas.

Benefits:

- removes a known workbook integrity risk
- enables formula-based authoring helpers in `Works`
- makes later workbook refactors safer

Risks:

- touches core generator write flow
- needs careful verification so computed reads still match saved writes

### Phase 2. Migrate `series_id` to numeric ids

Change `Series.series_id` to numeric ids and bulk-convert `Works.series_ids` to match.

Benefits:

- gives series joins a stable internal key
- removes the need for user-authored slug-safe ids in `Works`
- makes route paths independent of title changes

Risks:

- high workbook churn
- broad generated artifact churn
- requires all joins, filters, and validation rules to be updated together

### Phase 3. Full republish

Run a full regeneration of:

- works
- series
- related aggregate JSON
- catalogue search

This phase should assume all work and series outputs will be rewritten.

## Compatibility strategy

This migration can be treated as a direct cutover rather than a long compatibility phase.

Reasons:

- current series URLs are not used externally
- the workbook will be bulk-edited in one pass
- a full republish is already expected

Temporary migration support may still be useful inside the generator while the workbook is being converted, but the target implementation does not need long-term support for both old and new series identifiers.

## Republish expectations

The migration should assume a full republish of works and series.

That is acceptable because:

- `Works.series_ids` will change broadly
- per-work payloads will change
- per-series paths and hrefs will likely change
- search indexes will need a clean rebuild

## Resolved decisions

1. Use numeric `series_id` as the join key in `Works`.
2. Use numeric `series_id` as the public series URL token.
3. Do not introduce a persistent `series_slug`.
4. Do not add redirect support for old slug-like series paths.
5. Treat helper lookup columns in `Works` as supported authoring aids once formula-preserving writes are in place.

## Later scope

`moments` appears to have the same general identity-versus-slug problem.

That should be treated as a separate later migration so series can be completed first and used to validate the pattern.

## Recommended order

Recommended implementation order:

1. make workbook writes formula-safe
2. migrate `Series.series_id` and `Works.series_ids` to numeric ids
3. move public routing and per-series artifact paths to numeric `series_id`
4. perform a full republish and search rebuild

This keeps the end-state simple while reducing the chance of building a large migration on top of a workbook-write path that still damages formulas.
