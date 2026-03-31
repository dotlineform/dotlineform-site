---
doc_id: search-public-ui-contract
title: Search Public UI Contract
last_updated: 2026-03-31
parent_id: search
sort_order: 55
---

# Search Public UI Contract

## Purpose

This document defines the current public-site search entry model and URL contract for search.

It records the route and scope contract that the current implementation already uses across the dedicated search page and the inline docs-viewer search surfaces.

This is a contract-and-behaviour document. It does not define ranking rules, index schema, or implementation internals.

## Why this document exists now

Search now has:

- a dedicated public route at `/search/`, with `catalogue` backed by `assets/data/search/catalogue/index.json`
- an inline Studio docs search surface on `/docs/`
- an inline Library docs search surface on `/library/`

The route/state contract still needs to stay explicit because:

- additional content domains such as Studio or library are added
- each domain starts to own its own search JSON and search policy/config

The public UI contract needs to be clarified before those structural changes happen, so the later refactor grows against one stable interaction model.

## Core decision

Public search should use:

- explicit scope passed in the URL
- search call-to-action entry points placed on the page that owns the search scope
- the page anatomy that best fits the content domain, whether that is a dedicated route or inline viewer search

Public search should not initially use:

- a generic top-level nav item called `search`
- implicit scope inferred only from the current page
- one permanently global public search scope with unclear boundaries

## Public route contract

### Base route

The public search page route should be:

- `/search/`

This route is the dedicated public search shell for catalogue search and remains available for any future scope that genuinely benefits from a standalone search page.

### Query parameter contract

Recommended URL contract:

- `scope=<domain>`
- `q=<query>`

Examples for dedicated route search:

- `/search/?scope=catalogue`
- `/search/?scope=catalogue&q=forest`

### Why `scope` and `q`

Use:

- `scope`
  to define which content domain is being searched
- `q`
  to define the actual user query

Do not use:

- `search=works`
- `search=studio`

Reason:

- `search` is the natural name for the query itself, not the domain
- the current “works” search scope already includes works, series, and moments, so `works` is not a precise domain label
- a stable route vocabulary is more important once multiple search domains exist

## Scope vocabulary

The current agreed public scope vocabulary is:

- `catalogue`
- `library`
- `studio`

### `catalogue`

This scope covers the current public browse domain:

- works
- series
- moments

Reason:

- this name matches the actual user-facing content domain better than `works`
- it remains accurate even though the scope includes more than one record kind

### `library`

This scope currently exists as an inline docs-viewer search scope on `/library/`.

The dedicated `/search/` page does not currently enable `library`.

### `studio`

This scope currently exists as an inline docs-viewer search scope on `/docs/`.

Current coverage:

- Studio docs

Reason:

- `studio` matches the site domain more clearly than the generic label `docs`
- it remains scalable even if the first searchable Studio content is documentation-led

## Search entry-point rule

The search call to action should live on the page that matches the search scope.

Examples:

- the catalogue search CTA should live on `/series/` and open `/search/?scope=catalogue`
- Studio docs search should live inline on `/docs/`
- Library docs search should live inline on `/library/`

Reason:

- the user already understands the content domain from the page they are on
- the CTA can make the scope explicit without adding a second ambiguous navigation concept
- this avoids a top-level “search” nav item whose scope is unclear

## Public navigation rule

Do not introduce a top-level public nav item called `search` as the primary public entry point for scoped search.

Reason:

- it is unclear whether that nav item searches the current page, the current section, or the whole site
- the public site is moving toward multiple content domains, not one undifferentiated body of content
- scope-specific entry points are clearer and scale better

This rule does not forbid a future site-wide search affordance forever. It means the default public search model should be scope-led rather than globally ambiguous.

## Dedicated search-page UI responsibilities

The `/search/` page should:

- display the current search scope clearly in the page UI
- accept and persist the `scope` parameter in the URL
- accept and persist the `q` parameter in the URL
- load the correct search data/config for the active scope
- render one shared search-shell UI with scope-specific data and presentation policy

The `/search/` page should not:

- rely on hidden scope inference from the referrer page
- present an unlabelled generic search box with no visible scope context

## Scope clarity in the UI

The active scope should be visible in the search page itself.

Examples of acceptable signals:

- page title or heading
- supporting scope label near the input
- empty-state copy that names the active domain
- result metadata and filter options that clearly match the active domain

The user should not need to infer scope only from the URL.

## Current Dedicated-Route Scope

The dedicated `/search/` page currently enables:

- `catalogue`

That scope is configured in `assets/data/search/policy.json`.

Current docs-domain scopes:

- `studio`
- `library`

Those scopes currently use inline docs-viewer search rather than the dedicated `/search/` page.

## Relationship to future modular search architecture

This contract is intentionally compatible with the planned modular search refactor.

Expected future direction:

- each content domain can own its own search JSON artifact
- each content domain can own its own search config/policy
- the shared search engine can remain common across domains
- the public route and scope contract do not need to change when that refactor happens

This is the main reason to define the contract now.

## Benefits

- makes public search scope explicit to the user
- scales cleanly from one current domain to multiple future domains
- keeps one reusable public search shell instead of one-off search pages
- avoids ambiguous top-level navigation language
- aligns entry points with the page/domain the user is already browsing

## Main risks

- if scope is carried only in the URL and not reflected clearly in the UI, user understanding will still be weak
- if the initial scope names are chosen badly, later public URLs become harder to keep consistent
- if future requirements demand a genuinely global whole-site search, the scope-led model will need an additional documented rule rather than assuming all search is domain-local

## Current implementation status

The current public rollout is now split by page anatomy:

1. the dedicated public search page exists at `/search/`
2. the live dedicated-route scope is `catalogue`
3. `/series/` provides the catalogue search CTA
4. Studio docs search lives inline on `/docs/`
5. Library docs search lives inline on `/library/`
6. future scopes can still use `/search/` if a standalone page is the better fit

Further refinement areas are collated in [Search Next Steps](/docs/?scope=studio&doc=search-next-steps).

## Out of scope for this document

This document does not define:

- the internal search engine API
- the exact modular JSON/config file structure
- ranking rules for any domain
- search-result row layout details for each future domain
- whether a future whole-site aggregate scope should exist
