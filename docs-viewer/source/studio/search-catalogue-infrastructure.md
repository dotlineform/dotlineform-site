---
doc_id: search-catalogue-infrastructure
title: Catalogue Infrastructure
added_date: 2026-06-02
last_updated: 2026-06-02
ui_status: review
parent_id: search
viewable: true
---
# Catalogue Search Infrastructure

## Domain

Catalogue search owns structured artwork/catalogue lookup.

Current live surface:

- `/catalogue/search/`

Current output:

- `site/assets/data/search/catalogue/index.json`

Catalogue search is separate from Docs Viewer search.
It does not index Studio docs, Library docs, Analysis docs, or Docs Viewer source Markdown.

## Config Surface

Current config:

- `studio/services/catalogue/search/build_config.json`

Current responsibilities:

- declare Catalogue source families
- declare source-family eligibility for the `catalogue` scope
- declare targeted policy values such as `additive_only`
- map emitted fields to source families
- keep field/source dependency review separate from record-generation code

The config is not a ranking policy and is not a record-construction DSL.
The Python builder owns how records are derived, sorted, normalized, hashed, and merged.

Runtime UI policy lives separately in:

- `site/assets/data/search/policy.json`

That policy controls the public `/catalogue/search/` browser surface, including enabled scope, index path, input labels, batching, debounce, and messages.

## Build Pipeline

Current build entrypoint:

```bash
./studio/services/catalogue/search/build_search.py --scope catalogue
```

Write command:

```bash
./studio/services/catalogue/search/build_search.py --scope catalogue --write
```

Catalogue build orchestration constructs the same command through:

- `studio/services/catalogue/catalogue_build_commands.py`

Current source inputs:

- `site/assets/data/series_index.json`
- `site/assets/data/works_index.json`
- `site/assets/data/moments_index.json`
- `site/assets/works/index/<work_id>.json` for work-level enrichment

The search builder treats the generated catalogue JSON artifacts as canonical from the site point of view.
Drift between those artifacts and upstream non-repo source systems is outside search ownership.

Current pipeline shape:

1. validate `studio/services/catalogue/search/build_config.json`
2. load generated series, works, and moments indexes
3. derive one search entry per series, work, and moment
4. enrich work entries from per-work JSON where available
5. derive `search_terms` and `search_text`
6. sort by kind, title, and id
7. compute a content hash in the artifact header
8. write only when changed, forced, or targeted changes require it

## Index Schema

Current top-level shape:

- `header`
- `entries`

Current entry identity and display fields include:

- `kind`
- `id`
- `title`
- `year`
- `date`
- `display_meta`
- `series_ids`
- `series_titles`
- `medium_type`
- `series_type`
- `search_terms`
- `search_text`

Current included record kinds:

- `series`
- `work`
- `moment`

Current exclusions:

- docs content
- body prose
- Studio/admin pages
- public route strings that can be derived from `kind` and `id`
- operation logs or targeted-update provenance

## Ranking Runtime

Current runtime modules:

- `site/assets/js/catalogue-search.js`
- `site/assets/js/search/catalogue-search-runtime.js`
- `site/assets/js/search/search-policy.js`
- `site/assets/js/search/search-performance.js`

The runtime loads `site/assets/data/search/policy.json`, fetches the configured Catalogue index, normalizes entries, evaluates matches, sorts results, and renders result HTML.

Current ranking is Catalogue-specific.
It weights exact id/title matches first, then phrase and prefix matches, then domain relationship matches such as series title, medium type, and series type, then broader `search_text` matches.

Result URLs are derived in the browser from catalogue route rules for works, series, and moments rather than serialized into the search artifact.

## Targeted Updates

Catalogue targeted mode uses:

```bash
./studio/services/catalogue/search/build_search.py --scope catalogue --only-records work:<id>
```

Accepted target forms:

- `work:<id>`
- `series:<id>`
- `moment:<id>`

Current targeted policy is additive-only.
Missing entries can be inserted from current generated catalogue JSON.
Identical existing entries are treated as unchanged.
Changed existing entries are refused and require a full Catalogue search rebuild.

Unsupported Docs Viewer flags fail closed:

- `--only-doc-ids`
- `--source-index`
- `--remove-missing`

## Domain Review Questions

Catalogue-specific review should ask:

- Are work, series, and moment fields enough for real catalogue lookup?
- Should more structured catalogue fields, status fields, or tag-derived labels participate in search?
- Are relationship fields such as series membership weighted correctly?
- Is additive-only targeted search sufficient for current catalogue write flows?
- Are generated artifacts compact enough for public browser loading?
- Are public result routes still derivable from `kind` and `id`?
- Does the build remain downstream of canonical generated catalogue JSON?

Related docs:

- [Domain Review Patterns](/docs/?scope=studio&doc=search-domain-review-patterns)
- [Catalogue Scope](/docs/?scope=studio&doc=search-build-pipeline-catalogue)
- [Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract)
- [Build Config JSON](/docs/?scope=studio&doc=config-search-build-json)
