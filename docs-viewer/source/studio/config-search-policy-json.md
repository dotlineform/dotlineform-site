---
doc_id: config-search-policy-json
title: Catalogue Search Policy JSON
added_date: 2026-03-31
last_updated: "2026-05-11 14:10"
parent_id: search-catalogue-infrastructure
viewable: true
---
# Search Policy JSON

Config file:

- `assets/data/search/policy.json`

## Scope

`policy.json` is the dedicated runtime policy file for the Catalogue-owned `/catalogue/search/` page.

It is a likely candidate for a future JSON Schema because it is compact, source-controlled runtime config with constrained option values.
That follow-up is tracked in [JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption).

Current responsibilities include:

- live-search and Enter-to-search behavior
- minimum query length
- debounce timing
- initial and incremental result batch sizes
- the supported Catalogue search scope and label
- the Catalogue static search index path
- the Catalogue back-link href for the search shell
- dedicated search-shell messages, result labels, and performance summary copy

## What calls it

Current runtime path:

1. `assets/js/catalogue-search.js` imports `assets/js/search/search-policy.js`
2. `assets/js/catalogue-search.js` loads `/assets/data/search/policy.json` directly
3. `assets/js/catalogue-search.js` uses the Catalogue policy entry to resolve labels, back links, messages, and the static search index path

The policy helpers in `assets/js/search/search-policy.js` then expose:

- runtime behavior values
- per-scope UI policy
- shared message strings

## When it is read

- once per `/catalogue/search/` page load
- before the dedicated search page fetches the Catalogue search index

The public `/catalogue/search/` page does not fetch `studio/app/frontend/config/studio-config.json` for normal operation.
This keeps the public search shell independent from Studio bootstrap config size.

## Current scope boundary

Current live dedicated-route scope:

- `catalogue`

Current non-users of this file:

- inline Studio docs search on `/docs/`
- inline Library docs search on `/library/`
- inline Analysis docs search on `/analysis/`

Those docs-domain searches use the shared Docs Viewer runtime instead of the dedicated Catalogue search shell.

For the wider search subsystem, see **[Search Overview](/docs/?scope=studio&doc=search-overview)**.
