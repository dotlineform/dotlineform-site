---
doc_id: search-public-ui-contract
title: Search Public UI Contract
added_date: 2026-03-31
last_updated: "2026-05-11 14:10"
parent_id: search
---
# Search Public UI Contract

## Purpose

This document defines the current public-site search entry model and URL contract for search.

The current public dedicated-route search surface is Catalogue-owned.
Docs-domain search lives inside Docs Viewer routes.

This is a contract-and-behaviour document.
It does not define ranking rules, index schema, or implementation internals.

## Current Public Search Surfaces

Current live surfaces:

- Catalogue search on `/catalogue/search/`
- Studio docs search inline on `/docs/`
- Library docs search inline on `/library/`
- Analysis docs search inline on `/analysis/`

There is no active top-level `/search/` route.
The former scope-routed `/search/?scope=...` model has been retired because it implied a generic cross-domain search product.

## Core Decision

Search entry points should belong to the data domain being searched.

Catalogue search:

- owns the dedicated `/catalogue/search/` page
- searches works, series, and moments
- reads `site/assets/data/search/catalogue/index.json`
- is entered from the Catalogue browse surface, currently `/series/`

Docs search:

- belongs to Docs Viewer
- runs inline on `/docs/`, `/library/`, and `/analysis/`
- opens results inside the active viewer route

## Catalogue Route Contract

Base route:

- `/catalogue/search/`

Supported query parameter:

- `q=<query>`

Examples:

- `/catalogue/search/`
- `/catalogue/search/?q=forest`

The route does not accept `scope`.
The domain is fixed by the route.

## Catalogue Entry-Point Rule

The Catalogue search call to action should live on the page that matches the Catalogue browsing context.

Current entry point:

- `/series/` search button opens `/catalogue/search/`

The wider `/series/` to `/catalogue/` route naming cleanup is intentionally separate.
Until that route migration is designed, `/series/` remains the Catalogue browse entry point and `/catalogue/search/` is the Catalogue search entry point.

## Public Navigation Rule

Do not introduce a top-level public nav item called `search` as the primary public entry point.

Reason:

- it is unclear whether that nav item searches the current page, Catalogue, Docs, or the whole site
- the public site has distinct Catalogue and Docs data domains
- scope-specific entry points are clearer than a global search route

## Dedicated Catalogue Search Responsibilities

The `/catalogue/search/` page should:

- display Catalogue search context clearly
- accept and persist the `q` parameter
- load only the Catalogue search index and Catalogue search policy
- render work, series, and moment results
- keep result links and related series links usable by keyboard

The `/catalogue/search/` page should not:

- infer hidden scope from referrer context
- expose docs-domain scopes
- search Studio, Library, or Analysis documents
- preserve the retired `/search/?scope=...` URL contract

## Related Documents

- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
