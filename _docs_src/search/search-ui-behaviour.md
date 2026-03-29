---
doc-id: search-ui-behaviour
title: Search UI Behaviour
last-updated: 2026-03-29
parent-id: search
sort-order: 60
---

# Search UI Behaviour

## Purpose

This document defines how the site search interface behaves from the user’s point of view.

Its purpose is to make the runtime behaviour of the search UI explicit and reviewable. It should describe when search is invoked, how results are presented, how the interface responds to user input, and what interaction rules apply.

This document is about user-facing search behaviour. It is not a ranking document, not a schema document, and not a code walkthrough.

## Scope

This document applies to the browser-side search interface and its interaction model.

It should cover:

- where and how the search UI is invoked
- when the search index is loaded
- minimum query length and search trigger behaviour
- result limits and grouping
- empty, loading, and no-query states
- keyboard behaviour
- pointer and click behaviour
- scoped search, if supported
- how search results are displayed and cleared

This document should define interaction and presentation behaviour, not search engine internals.

## Relationship to other documents

This document should be read alongside:

- `search-overview.md`, which describes the search subsystem at a high level
- `search-index-schema.md`, which defines the data available to the UI
- `search-field-registry.md`, which defines which fields contribute to search and display
- `search-ranking-model.md`, which defines how results are prioritised
- `search-validation-checklist.md`, which defines how UI behaviour should be tested

## UI behaviour principles

The search UI should follow these principles:

### Immediate
The interface should respond quickly and clearly to user input.

### Predictable
Users should be able to understand when search is active, what results mean, and how to navigate them.

### Lightweight
The UI should remain simple and dependency-free.

### Accessible
Search interactions should work by keyboard as well as pointer input.

### Consistent
The same search patterns should behave similarly across different parts of the site unless a scoped mode intentionally changes them.

## Search entry points

This section should define where the user can access search.

Examples:
- global site header search input
- dedicated search page
- section-specific search input
- scoped search within a series or content group

Codex should replace this section with the actual current implementation and any planned but not yet implemented entry points should be clearly marked.

Questions to answer:
- Is search global, local, or both?
- Is there one search input or multiple?
- Is the search UI persistent, expandable, or page-specific?

## Search activation behaviour

This section should define when a search query is actually executed.

Questions to answer:
- Does search begin immediately on input?
- Is there a minimum query length?
- Is there a debounce delay?
- Is Enter required or optional?
- Are results updated on every keystroke after the threshold is reached?

Suggested subsections:

### Minimum query length
State whether search requires a minimum number of characters before results appear.

### Debounce behaviour
State whether the interface waits briefly before running the search after input changes.

### Immediate versus submitted search
State whether results update live or only after an explicit submit action.

Codex should describe the actual current behaviour.

## Search index loading behaviour

This section should define how and when the browser loads the search index.

Questions to answer:
- Is the index loaded at page load?
- Is it loaded only when the user focuses the search input?
- Is it cached in memory after first load?
- Is there a visible loading state while the index is being fetched?

This section should describe the UI-facing behaviour rather than fetch implementation details.

## Result display behaviour

This section should define how results are presented once matches are available.

Questions to answer:
- Are results shown in a dropdown, panel, overlay, or inline section?
- Are all content types mixed together or grouped?
- Is there a cap on the number of results shown?
- Are results displayed as simple links, cards, or richer previews?
- Are secondary fields such as year, kind, or series shown?

Suggested subsections:

### Result container
Describe where results appear in relation to the search input.

### Result count
Describe how many results are displayed and whether there is a hard cap.

### Result grouping
Describe whether results are grouped by content type such as works, series, or notes.

### Result metadata
Describe which secondary information appears in each result.

### Result ordering
State that results are presented in ranked order as defined by the ranking model.

Codex should document the actual current UI shape.

## No-query, loading, and empty states

This section should define what the user sees when there is no active search or no results.

Suggested subsections:

### No-query state
What is shown before the user types enough to trigger search.

Examples:
- nothing
- placeholder text only
- recent suggestions
- instructional hint

### Loading state
What is shown while the search index is loading or while search cannot yet run.

Examples:
- spinner
- loading message
- nothing visible

### Empty results state
What is shown when a valid query returns no results.

Examples:
- “No results found”
- guidance to broaden the query
- suggestion to check spelling

Codex should describe the current behaviour exactly.

## Keyboard interaction

This section should define how keyboard users interact with the search UI.

Questions to answer:
- Can results be navigated with arrow keys?
- Does Enter open the selected result?
- Does Escape close or clear the result list?
- Does Tab move focus naturally through the UI?
- Is there a highlighted active result?

Suggested subsections:

### Arrow navigation
Describe whether users can move through results with Up and Down keys.

### Enter behaviour
Describe whether Enter selects the active result, submits the raw query, or both.

### Escape behaviour
Describe whether Escape clears the query, closes results, or removes focus.

### Focus management
Describe how focus moves into and out of the result list.

If keyboard support is not yet fully implemented, this section should state the current status clearly.

## Pointer and click interaction

This section should define how pointer users interact with the search UI.

Questions to answer:
- Does clicking a result navigate immediately?
- Does clicking outside the search area close the result list?
- Does clicking the input reopen prior results?
- Does the UI support touch interaction in the same way as pointer interaction?

This document should describe intended user behaviour rather than DOM event details.

## Query persistence and clearing

This section should define what happens to the query and results over time.

Questions to answer:
- Does the query remain visible after navigating away and back?
- Does the result list close after selection?
- Is there an explicit clear button?
- Does clearing the query immediately hide results?
- Does blur hide results?

Codex should document the actual current behaviour and any known inconsistencies.

## Scoped search behaviour

If scoped search exists or is planned, this section should define it.

Examples:
- search only within the current series
- search only within works
- search only within a studio or admin tool context

Questions to answer:
- How is the scope indicated to the user?
- Can users switch scope manually?
- Does the same ranking model apply inside a scope?
- Is scope inferred from page context?

If scoped search is not currently implemented, this section should state that explicitly.

## Content-type display policy

This section should define how different result kinds appear in the UI.

Examples:
- whether works and series use different labels or badges
- whether some types show thumbnails and others remain text-only
- whether type grouping affects visual presentation
- whether hidden or excluded types are suppressed at UI level

This section is about result presentation by type, not ranking rules.

## Mobile and responsive behaviour

This section should define how the search UI behaves on smaller screens.

Questions to answer:
- Does the result container resize or reposition?
- Is the interface still keyboard-accessible where applicable?
- Are result counts reduced on mobile?
- Does the search UI become full-width, modal, or otherwise change layout?

Codex should document the current behaviour if responsive treatment already exists.

## Accessibility notes

This section should capture UI-level accessibility expectations.

Examples:
- focus visibility
- keyboard operability
- clear labels or placeholder guidance
- semantic roles, if relevant
- screen-reader-friendly result updates, if implemented

This should remain behavioural rather than implementation-heavy.

## Current implementation summary

This section should briefly summarise how the current search UI behaves in practice.

Examples:
- where the input lives
- whether results update live
- whether the index loads eagerly or lazily
- whether grouping is present
- whether keyboard navigation is complete or partial
- whether scoped search exists yet

This section should be concise and factual.

## Known limitations or open UI questions

This section should capture unresolved UI-behaviour questions only.

Examples:
- whether search should open in a dedicated results page rather than a dropdown
- whether keyboard navigation needs improvement
- whether loading state should be more explicit
- whether scope switching should be added
- whether mobile presentation needs refinement
- whether result metadata is too sparse or too noisy

## Out of scope for this document

This document should not define:

- the search index schema
- how matching works internally
- scoring formulas
- build pipeline steps
- low-level fetch or cache implementation details

Those belong in other search documents.