---
draft: false
doc_id: d-20260715-084611-99ee19
title: Search List
added_date: 2026-07-15 08:46:11
last_updated: "2026-10-20"
parent_id: d-20260505-181739-bb5223

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
- Escape/Tab cancellation and reset in its default selection mode
- close, refresh, and destroy lifecycle

The caller owns:

- data source and loader errors
- domain-specific filtering and option markup
- the meaning of the committed value
- durable form state, dirty state, and follow-on workflow

Transient typing is not a committed selection. Update durable route state from the commit callback unless the workflow explicitly needs live query state.

## Free Entry

`freeEntry: true` makes suggestions optional for an ordinary editable text field. Focus retains normal text/caret behavior; Tab and Escape close without resetting the value; blur closes the popup; Enter commits only an option explicitly activated with the Arrow keys. Pointer selection preserves input focus until click commits. Default pickers retain their existing select-on-focus, reset and first-result Enter behavior. The free-entry mode also owns combobox expanded state. A caller-supplied `getOptionValue` returns the exact string for insertion without trimming in this mode, and the caller must safely escape custom option markup.

Catalogue Medium uses this mode with a caller-owned two-character threshold, prepared local substring matching and all matches in the existing scrollable popup. Its ordinary input/change handlers update the draft while typing; `onCommit` carries a selected value through that same handler. The caller closes suggestions when replacing a draft or disabling its field. This extends the existing popup owner without adding requests, persistent storage or a second autocomplete implementation.

## Extension And Weak Spots

- The component is an input popup, not a full search page or general selectable list.
- Consumers can provide rich option HTML, so they remain responsible for safe rendering of domain values.
- Async loads are simple promises; the caller should consider stale response ordering if loaders become slow or remote.
- Default substring filtering is convenience only. Domain semantics such as prefix matching belong in a supplied filter.
- The 2026-10-20 free-entry change passed explicit-path JavaScript lint and source review; keyboard, pointer, blur, focus, default-picker behavior and listener cleanup remain manual acceptance through the Medium delivery. No tests or browser automation were changed or run.

Read the factory for exact hooks and callback shapes. Verify commit/cancel behaviour, keyboard navigation, async failures, and listener cleanup; judge popup fit visually in the live consumer.
