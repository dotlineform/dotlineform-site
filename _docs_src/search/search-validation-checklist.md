---
doc_id: search-validation-checklist
title: Search Validation Checklist
last_updated: 2026-03-29
parent_id: search
sort_order: 80
---

# Search Validation Checklist

## Purpose

This document defines the checks used to validate the site search subsystem after changes to search data, search policy, search UI, or search build logic.

Its purpose is to provide a practical, repeatable review checklist so that search changes can be checked systematically rather than informally.

This document is operational. It should be concise, test-oriented, and easy to use during iteration.

## Scope

This checklist applies after any change to one or more of the following:

- search index schema
- search field registry
- normalisation rules
- ranking logic or ranking policy
- search UI behaviour
- search build pipeline
- source content structures that feed the index

It should be used for both implementation review and regression checking.

## Relationship to other documents

This checklist should be used alongside:

- `search_overview.md`
- `search_index_schema.md`
- `search_field_registry.md`
- `search_normalisation_rules.md`
- `search_ranking_model.md`
- `search_ui_behaviour.md`
- `search_build_pipeline.md`

## How to use this checklist

Use this checklist after generating or updating the search index and after making any search-related code or config change.

The checklist should be run in proportion to the change:

- small UI-only change: focus on UI and interaction sections
- ranking or field-policy change: focus on retrieval and result-order sections
- build or schema change: focus on index integrity and record-shape sections
- broad refactor: run the full checklist

Where possible, checks should be based on real site examples rather than only synthetic test cases.

## A. Index generation and file integrity

- [ ] The search index file is generated successfully.
- [ ] The output file is written to the expected location.
- [ ] The generated file is valid JSON.
- [ ] The top-level structure matches the documented schema.
- [ ] Record count is plausible for the currently indexed content.
- [ ] No obviously malformed records appear in the output.
- [ ] No required fields are missing from indexed records.
- [ ] IDs appear unique across records.
- [ ] Links (`href` or equivalent) appear valid and non-empty.
- [ ] Empty optional fields use the expected convention consistently (for example empty arrays rather than omitted keys, if that is the chosen rule).

## B. Record schema checks

- [ ] Work records match the documented schema.
- [ ] Non-work records match the documented schema.
- [ ] Structured fields and derived fields are both present where expected.
- [ ] Field names and types match `search_index_schema.md`.
- [ ] Canonical IDs and display labels are both present where expected.
- [ ] Field-specific conventions are being followed consistently.
- [ ] Example records in the docs still reflect reality closely enough to remain useful.

## C. Field-registry checks

- [ ] Fields marked searchable are actually used in search.
- [ ] Fields marked non-searchable are not accidentally affecting retrieval.
- [ ] Fields intended for result display are available to the UI.
- [ ] Fields intended for filtering are present in a usable form.
- [ ] High-importance fields are not being treated like low-value fallback fields.
- [ ] Derived fields are not unintentionally dominating structured fields.
- [ ] The current implementation still matches `search_field_registry.md`.

## D. Normalisation checks

- [ ] Search is case-insensitive where intended.
- [ ] Leading and trailing whitespace in queries does not affect matching unexpectedly.
- [ ] Repeated internal whitespace is handled consistently.
- [ ] Hyphenated and spaced variants match where intended.
- [ ] Slug-like values and human-readable equivalents behave consistently.
- [ ] Numeric values such as years and IDs are handled as documented.
- [ ] Leading zeros are preserved where meaningful.
- [ ] Phrase fields and token fields are both behaving as expected.
- [ ] Duplicate derived terms are either removed or intentionally preserved, as documented.
- [ ] Query-time and index-time normalisation appear aligned.

## E. Known-item retrieval checks

Use real examples from the site.

- [ ] A full exact work title returns the intended work near the top.
- [ ] A partial title prefix returns the intended work near the top.
- [ ] A canonical ID returns the intended item near the top.
- [ ] A series title returns the intended series or related works appropriately.
- [ ] A numbered title component (for example `11`) behaves as expected.
- [ ] Queries using human-readable forms and slug-like forms both work where intended.

Suggested examples to test should be added here once Codex documents current records.

## F. Discovery and metadata checks

- [ ] Medium-based queries return sensible results.
- [ ] Tag-based queries return sensible results, if tags are indexed.
- [ ] Year-only queries behave as expected and do not produce obviously misleading top results.
- [ ] Broad metadata matches do not outrank strong title or ID matches unexpectedly.
- [ ] Cross-field matches improve recall without making results feel noisy.
- [ ] Generic tokens do not swamp the result set unnecessarily.

## G. Ranking checks

- [ ] Exact title matches outrank weak metadata-only matches.
- [ ] Strong known-item matches outrank broad fallback matches.
- [ ] Structured field matches outrank derived fallback field matches where intended.
- [ ] Duplicate terms in derived fields are not causing obvious ranking distortion.
- [ ] Ties are resolved consistently and predictably.
- [ ] Multi-field matches behave in line with the documented ranking model.
- [ ] The current implementation still matches `search_ranking_model.md`.

## H. UI behaviour checks

- [ ] The search input appears where expected.
- [ ] Search begins when expected according to the documented trigger rules.
- [ ] Minimum query length is respected.
- [ ] Debounce behaviour feels correct, if implemented.
- [ ] Results appear in the correct container or layout.
- [ ] Result count cap is respected.
- [ ] Result grouping by type behaves as documented, if implemented.
- [ ] Result metadata appears correctly.
- [ ] No-query state behaves as documented.
- [ ] Loading state behaves as documented.
- [ ] Empty-results state behaves as documented.
- [ ] Clearing the query hides or resets results as expected.
- [ ] Clicking a result navigates correctly.
- [ ] Clicking away or blurring behaves as documented.

## I. Keyboard and accessibility checks

- [ ] Search can be used without a pointer.
- [ ] Focus order is sensible.
- [ ] Arrow-key navigation works, if supported.
- [ ] Enter activates the expected result or action.
- [ ] Escape clears or closes as documented.
- [ ] Active result highlighting is clear enough.
- [ ] Focus remains visible throughout interaction.
- [ ] Search remains usable on smaller screens and touch devices.

## J. Regression checks after schema or pipeline change

Run this section after any build, schema, or source-data change.

- [ ] Previously known working title queries still work.
- [ ] Previously known working ID queries still work.
- [ ] Previously known working series queries still work.
- [ ] Content counts have not dropped unexpectedly.
- [ ] No content type has silently disappeared from the index.
- [ ] No major field has been renamed or removed without documentation updates.
- [ ] The UI still renders results without missing-field failures.
- [ ] Search-related docs have been updated to reflect the change.

## K. Documentation alignment checks

- [ ] `search_index_schema.md` matches the current generated index.
- [ ] `search_field_registry.md` matches current field usage.
- [ ] `search_normalisation_rules.md` matches current behaviour.
- [ ] `search_ranking_model.md` matches current relevance behaviour.
- [ ] `search_ui_behaviour.md` matches current runtime behaviour.
- [ ] `search_build_pipeline.md` matches current generation flow.
- [ ] Open questions and known limitations have been updated where needed.

## Suggested real-example test set

This section should be filled in with a small stable set of real examples from the site.

It should include at least:

- one work title query
- one work ID query
- one series title query
- one medium query
- one year query
- one slug-versus-spaced query
- one empty-results query

Codex should populate this section with concrete examples from the current content set.

## Current validation gaps

This section should be used to note checks that are not yet automated or not yet fully supported.

Examples:
- keyboard navigation not yet complete
- ranking still partly implicit
- duplicate-term handling still under review
- no stable set of regression queries yet
- multi-content-type behaviour not yet fully documented

## Notes

This checklist is intended to remain practical. It should be updated whenever the search system gains new capabilities such as scoped search, filtering, autocomplete, or partitioned indexes.