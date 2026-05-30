---
doc_id: search-validation-checklist
title: Search Validation Checklist
added_date: 2026-04-01
last_updated: "2026-05-11 21:30"
parent_id: search
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

- [ ] If the change touched catalogue source generation, refresh the canonical source artifacts with `$HOME/miniconda3/bin/python3 studio/services/catalogue/generate_work_pages.py`
- [ ] Run `./studio/services/catalogue/search/build_search.rb --scope catalogue`
- [ ] Confirm the dry run completes without error, including Catalogue build-config validation
- [ ] Run `./studio/services/catalogue/search/build_search.rb --scope catalogue --write`
- [ ] Confirm `assets/data/search/catalogue/index.json` is updated or correctly skipped by version check
- [ ] Confirm the output is valid JSON
- [ ] Confirm the header contains `schema`, `version`, `generated_at_utc`, and `count`
- [ ] Confirm the entry count is plausible for current works, series, and moments coverage

## B. Docs-Domain Build And Artifact Checks

- [ ] Run `./docs-viewer/build/build_docs.rb`
- [ ] Confirm the docs dry run completes without error for configured docs scopes
- [ ] Run `./docs-viewer/build/build_search.rb --scope studio`
- [ ] Confirm the dry run reports `docs-viewer/generated/search/studio/index.json` or correctly skips by version check
- [ ] Run `./docs-viewer/build/build_search.rb --scope library`
- [ ] Confirm the dry run reports `assets/data/search/library/index.json` or correctly skips by version check
- [ ] Run `./docs-viewer/build/build_search.rb --scope analysis`
- [ ] Confirm the dry run reports `assets/data/search/analysis/index.json` or correctly skips by version check
- [ ] If the change touched targeted docs-search updates, run `./docs-viewer/build/build_search.rb --scope studio --only-doc-ids search-build-pipeline --remove-missing`
- [ ] Confirm targeted dry run reports diagnostic counts for changed, removed, unchanged, skipped, and full-fallback behavior
- [ ] If the change touched docs-management search orchestration, confirm docs-management rebuild responses report `search.mode: targeted` for explicit affected ids
- [ ] Confirm `./studio/services/catalogue/search/build_search.rb --scope catalogue --only-doc-ids anything --remove-missing` fails closed because catalogue uses `--only-records`
- [ ] If the change touched catalogue targeted search, run `./studio/services/catalogue/search/build_search.rb --scope catalogue --only-records moment:4-stories`
- [ ] Confirm catalogue targeted dry run reports changed, removed, unchanged, skipped, and full-fallback behavior
- [ ] Confirm catalogue targeted mode refuses changed existing records and `--remove-missing`
- [ ] On write runs, confirm the Studio and Library search artifacts update or correctly skip by version check
- [ ] Confirm each docs-domain artifact has `header.scope`, `header.schema`, `header.version`, `generated_at_utc`, and `count`

## C. Search Adapter And Config Checks

- [ ] Confirm `scripts/search/adapter_registry.json` is valid JSON
- [ ] Confirm `scripts/search/build_config.json` is valid JSON
- [ ] Confirm every emitted Catalogue field has a source-family declaration
- [ ] Confirm Catalogue source-family scope declarations match the intended `targeted_policy`
- [ ] Confirm Catalogue `targeted_operations` values are valid for the configured `targeted_policy`
- [ ] Confirm Docs Viewer scopes derive from `docs-viewer/config/scopes/docs_scopes.json`
- [ ] Confirm future Catalogue heavy-index field additions update `scripts/search/build_config.json` before changing builder output
- [ ] Confirm future Docs Viewer heavy-index field additions update Docs Viewer-owned search config/runtime surfaces before changing builder output

## D. Catalogue Index Integrity Checks

- [ ] Confirm records exist for all three current kinds: `work`, `series`, `moment`
- [ ] Confirm every serialized record has `kind`, `id`, `title`, `href`, `search_terms`, and `search_text`
- [ ] Confirm array fields such as `series_ids` and `series_titles` use the expected empty-array convention
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

- [ ] Open `/catalogue/search/`
- [ ] Confirm the page loads and the input is visible
- [ ] Confirm the loading state clears and the page becomes usable
- [ ] Confirm live search updates after typing
- [ ] Confirm Enter triggers immediate search
- [ ] Confirm the result count text matches the visible result set
- [ ] Confirm results render inline below the controls
- [ ] Confirm result rows show kind, title link, id, and metadata where expected
- [ ] Confirm work, series, and moment title links open in a new tab on `/catalogue/search/`
- [ ] Confirm linked series titles in work result metadata open the related series page in a new tab
- [ ] Confirm a work opened from search without URL return context uses its primary series for the work-page back link when metadata loads
- [ ] Confirm empty query returns the prompt state
- [ ] Confirm a no-results query returns the empty state
- [ ] Confirm a large result set shows the `more` control
- [ ] Confirm `more` reveals the next batch without resetting the query
- [ ] Confirm the performance debug panel is hidden by default
- [ ] Open `/catalogue/search/?searchPerf=1`
- [ ] Confirm the performance debug panel appears and reports scope payload/load/normalization and query/render timing after a representative query
- [ ] Confirm enabling instrumentation does not change result count or first-result ordering for the representative query
- [ ] Confirm `/search/` is not generated as an active public route

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
- [ ] Confirm the input, result links, and `more` are reachable by Tab on `/catalogue/search/`
- [ ] Confirm linked work-result series titles are reachable by Tab when present
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

- [ ] No automated benchmark query set is implemented yet; the current performance instrumentation is manual and opt-in
- [ ] No dedicated build-time schema assertion pass exists yet
- [ ] No payload-budget enforcement exists yet
- [ ] No automated browser interaction test exists yet
- [ ] No tag-aware validation pass exists yet because tags are not active in v1 ranking

## Notes

When search behaviour changes materially, update the relevant search docs in the same change set rather than treating documentation as a follow-up task.
