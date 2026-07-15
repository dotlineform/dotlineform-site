---
doc_id: ui-search-list-component
title: Search List
added_date: 2026-07-15
last_updated: 2026-07-15
parent_id: ui
viewable: true
---
# Search List

Use Search List to add autocomplete/listbox behaviour to a caller-owned text input and popup. It supports asynchronous option loading, filtering, pointer/keyboard navigation, cancellation, and explicit commit.

## Authority

- behaviour: `shared/frontend/js/search-list.js`
- styles: `shared/frontend/css/search-list.css`

Current consumers include Catalogue work/series selection and File Picker folder search. Search imports from `/shared/frontend/js/search-list.js` for the exact set.

## Stable Boundary

`bindSearchList(input, popup, options)` owns:

- input/listbox ARIA wiring
- loading and rendering visible options
- active-option keyboard and pointer state
- Enter/click commit
- Escape/Tab cancellation and reset
- close, refresh, and destroy lifecycle

The caller owns:

- data source and loader errors
- domain-specific filtering and option markup
- the meaning of the committed value
- durable form state, dirty state, and follow-on workflow

Transient typing is not a committed selection. Update durable route state from the commit callback unless the workflow explicitly needs live query state.

## Extension And Weak Spots

- The component is an input popup, not a full search page or general selectable list.
- Consumers can provide rich option HTML, so they remain responsible for safe rendering of domain values.
- Async loads are simple promises; the caller should consider stale response ordering if loaders become slow or remote.
- Default substring filtering is convenience only. Domain semantics such as prefix matching belong in a supplied filter.

Read the factory for exact hooks and callback shapes. Verify commit/cancel behaviour, keyboard navigation, async failures, and listener cleanup; judge popup fit visually in the live consumer.
