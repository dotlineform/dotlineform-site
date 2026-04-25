---
doc_id: search-validation-checklist
title: "Search Validation Checklist"
added_date: 2026-04-01
last_updated: 2026-04-25
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

- small UI-only change: run sections F, G, and H
- ranking or normalization change: run sections B, D, E, F, and G
- generator or schema change: run all sections

Prefer real site examples over synthetic test strings.

## A. Catalogue Build And Artifact Checks

- [ ] If the change touched catalogue source generation, refresh the canonical source artifacts with `./scripts/generate_work_pages.py`
- [ ] Run `./scripts/build_search.rb --scope catalogue`
- [ ] Confirm the dry run completes without error, including build-config validation
- [ ] Run `./scripts/build_search.rb --scope catalogue --write`
- [ ] Confirm `assets/data/search/catalogue/index.json` is updated or correctly skipped by version check
- [ ] Confirm the output is valid JSON
- [ ] Confirm the header contains `schema`, `version`, `generated_at_utc`, and `count`
- [ ] Confirm the entry count is plausible for current works, series, and moments coverage

## B. Docs-Domain Build And Artifact Checks

- [ ] Run `./scripts/build_docs.rb`
- [ ] Confirm the docs dry run completes without error for both `studio` and `library`
- [ ] Run `./scripts/build_search.rb --scope studio`
- [ ] Confirm the dry run reports `assets/data/search/studio/index.json` or correctly skips by version check, including build-config validation
- [ ] Run `./scripts/build_search.rb --scope library`
- [ ] Confirm the dry run reports `assets/data/search/library/index.json` or correctly skips by version check, including build-config validation
- [ ] If the change touched targeted docs-search updates, run `./scripts/build_search.rb --scope studio --only-doc-ids search-build-pipeline --remove-missing`
- [ ] Confirm targeted dry run reports diagnostic counts for changed, removed, unchanged, skipped, and full-fallback behavior
- [ ] If the change touched docs-management search orchestration, confirm docs-management rebuild responses report `search.mode: targeted` for explicit affected ids
- [ ] Confirm `./scripts/build_search.rb --scope catalogue --only-doc-ids anything --remove-missing` fails closed because targeted mode is docs-only
- [ ] On write runs, confirm the Studio and Library search artifacts update or correctly skip by version check
- [ ] Confirm each docs-domain artifact has `header.scope`, `header.schema`, `header.version`, `generated_at_utc`, and `count`

## C. Search Build Config Checks

- [ ] Confirm `scripts/search/build_config.json` is valid JSON
- [ ] Confirm every emitted field for the changed scope has a source-family declaration
- [ ] Confirm source-family scope declarations match the intended `targeted_policy`
- [ ] Confirm future heavy-index field additions update `scripts/search/build_config.json` before changing builder output

## D. Catalogue Index Integrity Checks

- [ ] Confirm records exist for all three current kinds: `work`, `series`, `moment`
- [ ] Confirm every serialized record has `kind`, `id`, `title`, `href`, `search_terms`, and `search_text`
- [ ] Confirm array fields such as `series_ids`, `series_titles`, `tag_ids`, and `tag_labels` use the expected empty-array convention
- [ ] Confirm optional scalar fields such as `medium_type` and `series_type` are omitted when empty rather than serialized inconsistently
- [ ] Confirm ids are unique across the full entry list
- [ ] Confirm representative example records in the docs still reflect reality closely enough to stay useful

## E. Catalogue Search Behaviour Checks

- [ ] Query by exact work id and confirm the intended item appears at or near the top
- [ ] Query by exact work title and confirm the intended item appears at or near the top
- [ ] Query by title prefix and confirm the intended item appears at or near the top
- [ ] Query by series title and confirm the intended series or related works appear sensibly
- [ ] Query by `medium_type` and confirm results are sensible
- [ ] Query by `medium_caption` wording and confirm relevant works are still discoverable
- [ ] Query by a year or date fragment and confirm results are plausible rather than obviously broken
- [ ] Confirm a broad fallback query still returns relevant results without outranking strong exact matches

Suggested current examples:

- exact work id: `00533`
- exact work title: `2 bodies monoprint`
- medium caption: `pen on paper`
- series title: `2 bodies`
- slug/spaced equivalence: `2-bodies` and `2 bodies`
- date-like moment query: `2020`
- empty-results example: `zzzz-not-a-real-query`

## F. Dedicated Search Page UI Checks

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

## G. Docs-Viewer Search Checks

- [ ] Open `/docs/?scope=studio&doc=search&q=search`
- [ ] Confirm the Docs Viewer switches the right pane into inline search mode
- [ ] Confirm the left docs tree remains visible
- [ ] Confirm Studio docs results link back into `/docs/?scope=studio&doc=...`
- [ ] Open `/library/?doc=library&q=library`
- [ ] Confirm the Library viewer shows inline search results
- [ ] Confirm Library docs results link back into `/library/?doc=...`
- [ ] Confirm both docs scopes show `more` when result counts exceed the current batch size

## H. Keyboard And Accessibility Checks

- [ ] Confirm the input receives focus on page load
- [ ] Confirm the page can be used without a pointer
- [ ] Confirm the input, result links, and `more` are reachable by Tab when `scope=catalogue`
- [ ] Confirm inline docs-viewer search results are keyboard reachable on `/docs/` and `/library/`
- [ ] Confirm focus-visible styling is present on interactive controls
- [ ] Confirm there is no broken keyboard behaviour from unsupported features such as arrow-key navigation or Escape handling

## I. Documentation Alignment Checks

- [ ] [Search Index Schema](/docs/?scope=studio&doc=search-index-schema) still matches the generated index
- [ ] [Search Field Registry](/docs/?scope=studio&doc=search-field-registry) still matches active field usage
- [ ] [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules) still matches current builder and runtime behaviour
- [ ] [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model) still matches the score-band logic
- [ ] [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour) still matches current runtime behaviour
- [ ] [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) still matches how the artifact is generated
- [ ] [Docs Scope Index Shape](/docs/?scope=studio&doc=search-studio-v1-index-shape) still matches the current Studio and Library docs search artifacts

## Current known validation gaps

- [ ] No automated benchmark query set is implemented yet
- [ ] No dedicated build-time schema assertion pass exists yet
- [ ] No payload-budget enforcement exists yet
- [ ] No automated browser interaction test exists yet
- [ ] No tag-aware validation pass exists yet because tags are not active in v1 ranking

## Notes

When search behaviour changes materially, update the relevant search docs in the same change set rather than treating documentation as a follow-up task.
