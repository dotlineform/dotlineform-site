---
doc_id: search-public-ui-contract
title: Search Public UI Contract
last_updated: 2026-03-30
parent_id: search
sort_order: 55
---

# Search Public UI Contract

## Purpose

This document defines the public-site search entry model and URL contract that should guide continued search work.

It exists to settle the scalable UI direction before the larger modular search refactor expands search across additional content domains.

This is a contract-and-behaviour document. It does not define ranking rules, index schema, or implementation internals.

## Why this document exists now

Search now has a public route at `/search/` and is still built around one flat search surface backed by `assets/data/search_index.json`.

That implementation is sufficient for the current indexed content, but the route/state contract still needs to stay explicit as:

- additional content domains such as Studio or library are added
- each domain starts to own its own search JSON and search policy/config

The public UI contract needs to be clarified before those structural changes happen, so the later refactor grows against one stable interaction model.

## Core decision

Public search should use:

- one dedicated top-level route: `/search/`
- explicit scope passed in the URL
- search call-to-action entry points placed on the page that owns the search scope

Public search should not initially use:

- a generic top-level nav item called `search`
- implicit scope inferred only from the current page
- one permanently global public search scope with unclear boundaries

## Public route contract

### Base route

The public search page route should be:

- `/search/`

This route should become the shared public search shell for all supported public search scopes.

### Query parameter contract

Recommended URL contract:

- `scope=<domain>`
- `q=<query>`

Examples:

- `/search/?scope=catalogue`
- `/search/?scope=catalogue&q=forest`
- `/search/?scope=studio&q=tags`
- `/search/?scope=library&q=glass`

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

This scope is reserved for future library content once that content domain has its own search support.

### `studio`

This scope is reserved for Studio-owned searchable content.

Initial likely coverage:

- Studio docs

Possible later coverage:

- wider Studio reference or tool-adjacent content if the Studio domain expands

Reason:

- `studio` matches the site domain more clearly than the generic label `docs`
- it remains scalable even if the first searchable Studio content is documentation-led

## Search entry-point rule

The search call to action should live on the page that matches the search scope.

Examples:

- the catalogue search CTA should live on `/series/`
- a Studio search CTA should live on a Studio-owned shell page
- a library search CTA should live on `/library/`

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

## Search-page UI responsibilities

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

## First public rollout rule

The first public scope should be:

- `catalogue`

The first CTA should therefore point from the catalogue page to:

- `/search/?scope=catalogue`

This is the minimal public rollout that aligns with the current indexed content and the current search value proposition.

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

The first public rollout is now in place:

1. the public search page exists at `/search/`
2. the current public scope is `catalogue`
3. `/series/` provides the catalogue search CTA
4. the page UI names the active scope

The next phase can now focus on modular domain-specific search artifacts and policy/config behind the same public route contract.

## Out of scope for this document

This document does not define:

- the internal search engine API
- the exact modular JSON/config file structure
- ranking rules for any domain
- search-result row layout details for each future domain
- whether a future whole-site aggregate scope should exist
