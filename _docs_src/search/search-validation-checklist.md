---
doc_id: search-validation-checklist
title: Search Validation Checklist
last_updated: 2026-03-30
parent_id: search
sort_order: 80
---

# Search Validation Checklist

## Purpose

This checklist is the operational validation pass for search changes.

Use it after any change to:

- search index generation
- search schema
- search field usage
- normalization rules
- ranking logic
- search UI behaviour

Keep this checklist practical. It is for confirming that the implemented v1 search still works as intended.

## How to use this checklist

- small UI-only change: run sections C, D, and E
- ranking or normalization change: run sections B, C, D, and E
- generator or schema change: run all sections

Prefer real site examples over synthetic test strings.

## A. Build and artifact checks

- [ ] Run `python scripts/generate_work_pages.py --only search-index-json`
- [ ] Confirm the dry run completes without error
- [ ] Run `python scripts/generate_work_pages.py --only search-index-json --write`
- [ ] Confirm `assets/data/search_index.json` is updated or correctly skipped by version check
- [ ] Confirm the output is valid JSON
- [ ] Confirm the header contains `schema`, `version`, `generated_at_utc`, and `count`
- [ ] Confirm the entry count is plausible for current works, series, and moments coverage

## B. Index integrity checks

- [ ] Confirm records exist for all three current kinds: `work`, `series`, `moment`
- [ ] Confirm every serialized record has `kind`, `id`, `title`, `href`, `search_terms`, and `search_text`
- [ ] Confirm array fields such as `series_ids`, `series_titles`, `tag_ids`, and `tag_labels` use the expected empty-array convention
- [ ] Confirm optional scalar fields such as `medium_type`, `storage`, and `series_type` are omitted when empty rather than serialized inconsistently
- [ ] Confirm ids are unique across the full entry list
- [ ] Confirm representative example records in the docs still reflect reality closely enough to stay useful

## C. Search behaviour checks

- [ ] Query by exact work id and confirm the intended item appears at or near the top
- [ ] Query by exact work title and confirm the intended item appears at or near the top
- [ ] Query by title prefix and confirm the intended item appears at or near the top
- [ ] Query by series title and confirm the intended series or related works appear sensibly
- [ ] Query by `medium_type` and confirm results are sensible
- [ ] Query by a year or date fragment and confirm results are plausible rather than obviously broken
- [ ] Confirm a broad fallback query still returns relevant results without outranking strong exact matches

Suggested current examples:

- exact work id: `00533`
- exact work title: `2 bodies monoprint`
- series title: `2 bodies`
- slug/spaced equivalence: `2-bodies` and `2 bodies`
- date-like moment query: `2020`
- empty-results example: `zzzz-not-a-real-query`

## D. UI checks

- [ ] Open `/search/?scope=catalogue`
- [ ] Confirm the page loads and the input is visible
- [ ] Confirm the loading state clears and the page becomes usable
- [ ] Confirm live search updates after typing
- [ ] Confirm Enter triggers immediate search
- [ ] Confirm the result count text matches the visible result set
- [ ] Confirm results render inline below the controls
- [ ] Confirm result rows show kind, title link, id, and metadata where expected
- [ ] Confirm empty query returns the prompt state
- [ ] Confirm a no-results query returns the empty state
- [ ] Confirm a large result set shows the `more` control
- [ ] Confirm `more` reveals the next batch without resetting the query
- [ ] Open `/search/` without `scope`
- [ ] Confirm the input is disabled and the page shows the missing-scope message

## E. Keyboard and accessibility checks

- [ ] Confirm the input receives focus on page load
- [ ] Confirm the page can be used without a pointer
- [ ] Confirm the input, result links, and `more` are reachable by Tab when `scope=catalogue`
- [ ] Confirm focus-visible styling is present on interactive controls
- [ ] Confirm there is no broken keyboard behaviour from unsupported features such as arrow-key navigation or Escape handling

## F. Documentation alignment checks

- [ ] [Search Index Schema](/docs/?doc=search-index-schema) still matches the generated index
- [ ] [Search Field Registry](/docs/?doc=search-field-registry) still matches active field usage
- [ ] [Search Normalisation Rules](/docs/?doc=search-normalisation-rules) still matches current generator and runtime behaviour
- [ ] [Search Ranking Model](/docs/?doc=search-ranking-model) still matches the score-band logic
- [ ] [Search UI Behaviour](/docs/?doc=search-ui-behaviour) still matches current runtime behaviour
- [ ] [Search Build Pipeline](/docs/?doc=search-build-pipeline) still matches how the artifact is generated

## Current known validation gaps

- [ ] No automated benchmark query set is implemented yet
- [ ] No dedicated build-time schema assertion pass exists yet
- [ ] No payload-budget enforcement exists yet
- [ ] No automated browser interaction test exists yet
- [ ] No tag-aware validation pass exists yet because tags are not active in v1 ranking

## Notes

When search behaviour changes materially, update the relevant search docs in the same change set rather than treating documentation as a follow-up task.
