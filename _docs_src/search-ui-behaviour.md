---
doc_id: search-ui-behaviour
title: "Search UI Behaviour"
last_updated: 2026-03-31
parent_id: search
sort_order: 60
---

# Search UI Behaviour

## Purpose

This document defines how the current search interface behaves from the user’s point of view.

It describes when search becomes active, how results are shown, what controls exist, and what the user can currently do by keyboard and pointer.

This is a UI-behaviour document. It is not the ranking, schema, or build-pipeline document.

## Scope

This document applies to the current dedicated public search page at `/search/`.

It covers:

- the current entry point
- search activation and loading behaviour
- visible UI states
- result presentation
- keyboard and pointer interaction
- current scope handling
- responsive and accessibility observations relevant to v1

## Relationship to other documents

- [Search Overview](/docs/?scope=studio&doc=search-overview) describes the subsystem at a high level
- [Search Public UI Contract](/docs/?scope=studio&doc=search-public-ui-contract) defines the public `/search/` route and scope-led entry model
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema) defines the data available to the UI
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry) defines which fields contribute to search and display
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model) defines result ordering
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist) defines what UI behaviour should be checked

## UI behaviour principles

The current UI follows these principles.

### Immediate

Search runs in memory and updates quickly after typing.

### Predictable

The page always presents one visible query field and one inline results area when a valid scope is present.

### Lightweight

The current UI is plain browser UI with no external widget library or autocomplete framework.

### Keyboard-usable

The input, result links, and `more` control are all reachable by keyboard, even though richer list-navigation patterns are not yet implemented.

### Simple first

The v1 public surface favors explicit behaviour over more advanced overlay or autosuggest patterns.

## Search entry points

Current entry point:

- dedicated public page: `/search/?scope=catalogue`

Current status:

- search is global across the indexed content types in the current index
- there is one search input on this page
- the header includes a scope-owned back link to the calling browse page when the scope is valid
- the UI is page-specific rather than persistent in the main site shell

Not yet implemented:

- main site header search
- overlay or dropdown search
- public library search entry points

## Search activation behaviour

The current page supports live in-memory search plus explicit Enter submission.

### Minimum query length

Current behaviour:

- the current minimum normalized query length is policy-driven and currently set to `1`
- an empty normalized query shows the no-query prompt state instead of results

### Debounce behaviour

Current behaviour:

- typing triggers a policy-driven debounce which is currently `140ms`
- when the debounce completes, the current query is searched and results are re-rendered

### Immediate versus submitted search

Current behaviour:

- results update live as the user types
- pressing Enter is optional
- Enter forces an immediate search by cancelling any pending debounce and rendering results at once

This means v1 supports both live search and explicit confirmation, but does not require submit-only search.

## Search index loading behaviour

Current behaviour:

- the page loads the search index during page initialization
- the page appends a lightweight build-version query to the search module, shared config/data modules, and search JSON fetches to reduce stale-cache breakage after local JS or data changes
- the page expects a valid `scope` URL parameter before it becomes usable
- the root remains hidden until the initial search config and search index load attempt completes
- while the page is loading, the status message is set to `loading search index…`
- after the index is loaded, it stays in memory for the page session

Current scope policy:

- `catalogue` is enabled
- no docs-domain scopes are configured on the dedicated search page

If the page loads without a valid scope:

- the page still becomes visible
- the scope-owned back link is hidden
- the input is disabled
- the status area shows a missing-scope message
- results and `more` are cleared

If loading fails:

- the page still becomes visible
- the status area shows the configured load-failure message
- no separate retry UI is currently shown

The current implementation is eager-load on page entry, not lazy-load on focus.

## Result display behaviour

### Result container

Results appear inline on the page, below the search input.

There is no dropdown, overlay, or floating panel in v1.

### Result count

The status line above the results serves as the result-count area.

Current behaviours:

- `Enter a search query.` when there is no active query
- `No results.` when the query returns nothing
- `1 result` for one match
- `{count} results` when all current matches are visible
- `Showing {visible} of {count} results` when the visible list is capped and more remain

### Result grouping

Results are not visually grouped into separate sections by kind.

Instead:

- all matching records are shown in one mixed ranked list
- each result includes a small kind label
- there is no visible UI control to restrict the list to one kind

### Result limits

Current behaviour:

- the page renders the first policy-defined batch of results, currently `50`
- if more matches exist, a `more` control appears beneath the list
- activating `more` reveals the next policy-defined batch, currently `50`

This is incremental list expansion, not paged navigation.

### Result metadata

Each result currently displays:

- kind label
- title as the main link
- id on a separate line
- optional metadata line

The metadata line may include:

- `display_meta`
- `medium_type` for works
- `series_titles` for works
- `series_type` for series

### Result ordering

Results are displayed in the ranked order defined by [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model).

## No-query, loading, and empty states

### No-query state

Current behaviour:

- the input remains visible
- the status line shows `Enter a search query.`
- the results list is empty
- the `more` control is hidden

### Loading state

Current behaviour:

- before the initial load completes, the page status indicates loading
- the page root remains hidden until initialization completes

This means the user does not interact with a partially initialized visible search shell.

### Empty results state

Current behaviour:

- the status line shows `No results.`
- the results list is cleared
- the `more` control is hidden

There are currently no spelling hints, suggestions, or alternate-query prompts.

## Keyboard interaction

Current keyboard behaviour is basic but functional.

### Arrow navigation

Current behaviour:

- there is no custom arrow-key navigation through results
- arrow keys are not used to maintain an active highlighted result

### Enter behaviour

Current behaviour:

- Enter in the input triggers an immediate search using the current query
- Enter does not activate a selected result because there is no active-result model

### Escape behaviour

Current behaviour:

- no custom Escape behaviour is currently implemented
- Escape does not clear the query or close a result panel because there is no panel state

### Focus management

Current behaviour:

- focus moves naturally through the page using normal browser tab order
- the input is focused automatically after successful page initialization
- result links and the `more` button are standard focusable elements

The current UI does not yet implement roving focus, active-result selection, or managed focus transfer into the results list.

## Pointer and click interaction

Current pointer behaviour:

- clicking a result link navigates directly to the target page
- clicking `more` reveals the next batch of results

Not currently implemented:

- outside-click dismissal
- reopening a dismissed result panel
- pointer-specific behaviour distinct from the inline page model

Because the current UI is inline rather than overlay-based, there is no open/close panel state to manage.

## Query persistence and clearing

Current behaviour:

- there is no explicit clear button
- clearing the input back to an empty query returns the page to the no-query state
- the current query is held only in the current page session state
- there is no URL persistence of the current search query
- the page does not currently restore the last query after navigation away and back

There is also no blur-driven result dismissal because results are rendered inline on the page.

## Scoped search behaviour

Current implemented scope control:

- URL scope only: `scope=catalogue`

Current non-features:

- no visible per-kind filter buttons
- no “search within current series”
- no hidden fallback scope when the URL context is missing

The current public page is usable only when a valid scope is supplied in the URL.

## Content-type display policy

Current content-type presentation:

- works, series, and moments share one visual result-row pattern
- each row includes a kind label so the user can distinguish record type quickly
- works may show `medium_type` and related series titles in metadata
- series may show `series_type` in metadata
- moments currently use the same basic row structure without a special richer preview

There are no thumbnails, excerpts, or per-kind custom card layouts in v1.

## Mobile and responsive behaviour

Current responsive behaviour is simple rather than mode-switched.

Current properties:

- the page uses a stacked inline layout
- the header keeps the back link on the left and the scope label on the right
- the search input remains full-width within the page layout
- the results list remains inline rather than switching to modal or overlay presentation

There is no separate mobile-only search mode in v1.

## Accessibility notes

Current accessible behaviours:

- the search input has a visually hidden label and configured `aria-label`
- focus-visible states exist for result links and the `more` button
- result links are standard anchors
- keyboard users can reach all current interactive controls through normal tab navigation

Current gaps:

- no arrow-key result navigation
- no active-result announcement model
- no dedicated live-region treatment for result-count updates

Those gaps are acceptable in the current implementation.

## Current implementation summary

Current UI behaviour in practice:

- search lives on one dedicated public page
- the header back link is scope-driven and currently resolves `catalogue` to `← works`
- the page currently expects `scope=catalogue`
- the index loads eagerly when the page initializes
- results update live after a short debounce, and Enter can force immediate search
- results appear inline below the controls
- there is no visible kind filter
- results are shown in batches of `50` with a `more` control
- keyboard support is basic tab-and-activate behaviour rather than full result-list navigation

## Out of scope for this document

This document does not define:

- the search index schema
- internal matching logic
- scoring formulas
- build-pipeline steps
- low-level fetch implementation details
