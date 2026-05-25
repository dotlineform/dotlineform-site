---
doc_id: search-build-pipeline-catalogue
title: Search Build Pipeline Catalogue Scope
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-build-pipeline
sort_order: 8200
---
# Search Build Pipeline Catalogue Scope

## Catalogue Scope

### Current Writer

- `./studio/services/catalogue/search/build_search.rb --scope catalogue`

### Current Output

- `assets/data/search/catalogue/index.json`

### Current Source Inputs

Canonical catalogue source artifacts:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/data/moments_index.json`

Current Studio-owned tag metadata inputs:

- `assets/studio/data/tag_registry.json`
- `assets/studio/data/tag_assignments.json`

Important boundary:

- the search builder treats these checked-in JSON artifacts as canonical from the site’s point of view
- drift between those JSON artifacts and workbook or non-repo source systems is outside search’s responsibility

### Current Build Path

The current catalogue build path is:

1. load the canonical catalogue indexes
2. load Studio tag registry and assignment data
3. derive `series` entries
4. derive `work` entries, including effective tag metadata by combining series tags with work overrides
5. derive `moment` entries
6. sort the flat entry list by kind, title, and id
7. compute header metadata and version hash
8. write `assets/data/search/catalogue/index.json` if changed or forced

Current integration facts:

- `scripts/generate_work_pages.py` no longer writes catalogue search directly
- the draft pipeline now rebuilds catalogue search after `generate_work_pages.py` refreshes the canonical catalogue JSON inputs
- catalogue search can be rebuilt independently as long as those source JSON artifacts already exist

### Current Commands

Default write command:

```bash
./studio/services/catalogue/search/build_search.rb --scope catalogue --write
```

Dry run:

```bash
./studio/services/catalogue/search/build_search.rb --scope catalogue
```

Current supported overrides:

- `--series-index PATH`
- `--works-index PATH`
- `--moments-index PATH`
- `--tag-assignments PATH`
- `--tag-registry PATH`
- `--output PATH`
- `--only-records RECORDS`
- `--write`
- `--force`

Current targeted-update boundary:

- `catalogue` does not support `--only-doc-ids`
- `--only-records` accepts comma-separated `work:<id>`, `series:<id>`, and `moment:<id>` targets
- catalogue targeted mode is additive-only
- missing entries are inserted from current generated catalogue source JSON
- identical existing entries are treated as unchanged
- changed existing entries are refused and require a full catalogue search rebuild
- `--remove-missing` is not supported for catalogue

### Current Included Content

- works
- series
- moments

Each included item becomes one search record.

### Current Exclusions

- full prose or body text
- docs content
- Studio/admin pages
- unrelated site sections outside the current catalogue model

### Current Record Construction

Current core identity fields:

- `kind`
- `id`
- `title`
- `href`

Current display and structured support fields may include:

- `year`
- `date`
- `display_meta`
- `series_ids`
- `series_titles`
- `medium_type`
- `series_type`
- `tag_ids`
- `tag_labels`

Current derived search fields:

- `search_terms`
- `search_text`

Current work-only enrichment from per-work JSON may also add values such as:

- `medium_caption`

Current transformation behaviour:

- lowercase normalization
- whitespace collapse
- phrase retention
- additional split-token generation
- duplicate-token removal while preserving first-seen order
- `search_text` assembled from `search_terms`

### Current Validation And Fallbacks

Current behaviour is pragmatic rather than strict.

Current examples:

- missing titles fall back to item id
- optional scalar fields may be omitted when empty
- array-valued relationship and tag fields are still serialized as arrays
- partial tag-label lookup does not block record generation

Current safeguards include:

- normalized and deduplicated token generation
- deterministic sort order before serialization
- content-version hashing for change detection
- domain-specific config validation before output is written or skipped
