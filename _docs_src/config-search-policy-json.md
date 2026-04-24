---
doc_id: config-search-policy-json
title: "Search Policy JSON"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: config
sort_order: 50
---

# Search Policy JSON

Config file:

- `assets/data/search/policy.json`

## Scope

`policy.json` is the dedicated runtime policy file for the public `/search/` page.

Current responsibilities include:

- live-search and Enter-to-search behavior
- minimum query length
- debounce timing
- initial and incremental result batch sizes
- supported dedicated-route scopes and their labels
- dedicated search-shell messages for missing or unsupported scopes

## What calls it

Current runtime path:

1. `assets/js/search/search-page.js` loads `assets/studio/js/studio-config.js`
2. that loader resolves the policy URL from `studio_config.json`
3. `assets/js/search/search-page.js` calls `loadSearchPolicy(...)` in `assets/js/search/search-policy.js`

The policy helpers in `assets/js/search/search-policy.js` then expose:

- runtime behavior values
- per-scope UI policy
- shared message strings

## When it is read

- once per `/search/` page load, after `studio_config.json` has loaded
- before the dedicated search page decides whether the requested scope is enabled and before it fetches the scope-owned search index

## Current scope boundary

Current live dedicated-route scope:

- `catalogue`

Current non-users of this file:

- inline Studio docs search on `/docs/`
- inline Library docs search on `/library/`

Those docs-domain searches use the shared Docs Viewer runtime instead of the dedicated `/search/` shell.

For the wider search subsystem, see **[Search Overview](/docs/?scope=studio&doc=search-overview)**.
