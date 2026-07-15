---
doc_id: search
title: Search
added_date: 2026-03-31
last_updated: 2026-07-15
parent_id: ""
---
# Search

Search is two domain-owned static-index systems, not one global product.

## Current Surfaces

- [Catalogue Search](/docs/?scope=studio&doc=search-catalogue-infrastructure) serves `/catalogue/search/` for public works and series.
- [Docs Viewer Search](/docs/?scope=studio&doc=search-docs-viewer-infrastructure) is embedded in Docs Viewer routes such as `/docs/`, `/library/`, and `/analysis/`.

Both build compact JSON indexes ahead of runtime and rank them in the browser. They share broad conventions—identity, title, derived search terms, deterministic ranking—but have separate builders, records, UI, and ownership.

## Find The Authority

| Question | Authority |
| --- | --- |
| Catalogue source families and field dependencies | `studio/services/catalogue/search/build_config.json` |
| Catalogue record construction | `studio/services/catalogue/search/build_search.py` |
| Catalogue ranking and rendering | `site/assets/js/search/catalogue-search-runtime.js` |
| Catalogue page timing, messages, and index URL | `site/assets/data/search/policy.json` |
| Docs scope source and generated/published output paths | `docs-viewer/config/scopes/docs_scopes.json` |
| Docs search record construction | `docs-viewer/build/build_search.py` |
| Docs ranking | `site/docs-viewer/runtime/js/shared/docs-viewer-search.js` |
| Docs loading, route state, and result rendering | `site/docs-viewer/runtime/js/shared/docs-viewer-search-controller.js` |

Use [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline-architecture) for commands and the source-to-runtime flow.

## Design Method

- Keep canonical source and search projections separate.
- Let each domain decide which source fields are safe and useful for retrieval.
- Keep public indexes small enough for client-side loading and ranking.
- Prefer explicit deterministic relevance over an opaque general search service.
- Rebuild the owning domain only; a Catalogue source change should not require a Docs search build.

## Extension Rule

Add a field or source at the domain boundary. Update its builder/config, generated record, runtime matching, and focused tests together. Do not add a shared search abstraction merely because both products use similar score bands.

For a new Docs Viewer scope, configure its source/output/published paths and runtime index URL; the generic docs builder and runtime should then work without scope-specific ranking code.

For Catalogue, treat the build config as the dependency registry. A new emitted field must declare its source family before the builder accepts it.

## Current Weak Spots

- Normalization and score bands are duplicated between the two domains. The similarity is useful, but changes can drift.
- Catalogue runtime policy exists both as checked-in JSON and JavaScript defaults.
- Docs runtime config exposes both legacy `search_index_url` and nested `search.index_url` values.
- Exact index schemas are Python/JavaScript contracts rather than validated standalone schemas.
- Client-side indexes impose a practical payload ceiling; body-heavy or semantic search needs a separate design decision.

Those are the useful review points. Exact fields, scores, selectors, messages, and consumer lists belong in code and config.

The mechanics review belongs to [Search Mechanics](/docs/?scope=studio&doc=repository-search-mechanics), not to the current architecture pages.
