---
doc_id: config-search-policy-json
title: Search Policy JSON
added_date: 2026-03-31
last_updated: "2026-05-10 18:45"
parent_id: search
sort_order: 1020
---
# Search Policy JSON

Config file:

- `assets/data/search/policy.json`

## Scope

`policy.json` is the dedicated runtime policy file for the public `/search/` page.

It is a likely candidate for a future JSON Schema because it is compact, source-controlled runtime config with constrained option values.
That follow-up is tracked in [JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption).

Current responsibilities include:

- live-search and Enter-to-search behavior
- minimum query length
- debounce timing
- initial and incremental result batch sizes
- supported dedicated-route scopes and their labels
- per-scope static search index paths
- per-scope back-link hrefs for the public search shell
- the virtual `all` scope used by direct `/search/`
- dedicated search-shell messages, result labels, and performance summary copy

## What calls it

Current runtime path:

1. `assets/js/search/search-page.js` imports `assets/js/search/search-policy.js`
2. `assets/js/search/search-page.js` loads `/assets/data/search/policy.json` directly
3. `assets/js/search/search-page.js` uses policy scope entries to resolve labels, back links, messages, and static search index paths

The policy helpers in `assets/js/search/search-policy.js` then expose:

- runtime behavior values
- per-scope UI policy
- shared message strings

## When it is read

- once per `/search/` page load
- before the dedicated search page decides whether the requested scope is enabled and before it fetches the scope-owned search index

The public `/search/` page does not fetch `assets/studio/data/studio_config.json` for normal operation.
This keeps the public search shell independent from Studio bootstrap config size.

## Current scope boundary

Current live dedicated-route scope:

- `all`
- `catalogue`
- `library`
- `studio`
- `analysis`

Current non-users of this file:

- inline Studio docs search on `/docs/`
- inline Library docs search on `/library/`

Those docs-domain searches use the shared Docs Viewer runtime instead of the dedicated `/search/` shell.

For the wider search subsystem, see **[Search Overview](/docs/?scope=studio&doc=search-overview)**.
