---
draft: false
doc_id: d-20261001-192157-493fe8
title: Search Fields
added_date: "2026-10-01 19:21:57"
last_updated: "2026-10-01 19:31:53"
parent_id: d-20260505-181739-bb5223
---
# Search Fields

Use `mountSearchField()` from `shared/frontend/js/search-field.js` for an existing search or autocomplete input. `shared/frontend/css/search-field.css` owns its presentation. This is the shared field primitive beneath site Search, collection/report filters, Docs destination/document/Catalogue pickers, Studio Work/Series/Gallery searches and the shared File Picker's folder search.

## Appearance And Interaction

Every field has a 20px `search.svg` on the left, a transparent 2rem-high text field with one permanent grey underline and grey placeholder text, and normal-colour entered text. The line spans only the text field. Clicking the icon focuses the input; the icon has no hover highlight or extra keyboard stop. Clicking the text region enters the input normally. Input focus uses the caret and existing underline without a second outline, glow or colour variant.

A right-aligned 16px `x.svg` appears when the input contains text and is editable. The button clears the text, focuses the input and emits one ordinary bubbling `input` event. Its keyboard focus has a visible outline. Clearing the field does not call a service, commit a selection or persist a value on its own; each caller's existing input handler owns that meaning. Picker adapters retain their ordinary selected-value restoration on blur or cancel. Pointer activation preserves input focus so those handlers do not restore a value before the clear action runs.

The underline and space for the clear icon remain stable. CSS derives clear-button visibility from the actual input value, including values restored through navigation or picker selection, and its disabled/read-only state. Placeholder text does not show the clear button. Hidden clear buttons use `display: none` so native Tab navigation and the existing modal focus owners exclude them. Callers without a placeholder receive `search`.

## Ownership And Integration

Place the caller-owned input in its host before calling `mountSearchField(input, { clearLabel })` once. The component wraps the same input without replacing its identity, labels, input type, autocomplete attributes or listeners and returns its root and clear button. `clearLabel` is optional and defaults to `Clear search`. Retain the caller's exact search, debounce, route/history, busy and selection logic in that caller. The primitive has no app API, transport, persistent state, document-level listener or observer.

Hosts supply `--shared-search-text`, `--shared-search-muted`, `--shared-search-icon` and `--shared-search-clear-icon`. Docs Viewer and Studio use the same placeholder-grey palette (`#8c8c8c` in light themes and `#9b9ba3` in dark themes); the underline and placeholder consume the same colour token. Explicit placeholder text fill keeps Safari's field text-fill styling from changing that shade. Normal entered text retains the host's text role. Both hosts select the same canonical artwork under `docs-viewer/static/icons/` with root-relative URLs: CSS variables containing relative URLs resolve against the consuming shared stylesheet, so an owner-relative icon path is incorrect here. Docs Viewer and Studio CSS load the shared stylesheet; File Picker CSS also declares its field dependency for standalone consumers. Popup anchors remain with the surrounding search-list or picker host.

The Docs service explicitly serves the two shared field files through its confined static-route map. Studio serves them through its existing shared frontend boundary. `site-tools/config/site-code-update.json` projects only `search-field.js`, `search-field.css` and the required Docs artwork into the public site. Other shared primitives remain local unless explicitly listed. [Source Tree Ownership](Source_Tree_Ownership.md) owns the general shared boundary.

Ordinary form fields and selects keep their own presentation. The Docs Review package select uses its dedicated class rather than borrowing search-input styling. Archived Catalogue pages retain their archived runtime. The native application is a separate project.

## Verification Boundary

Focused JavaScript/Python lint and the public code-projection/static-site validators provide syntax, maintained source and artifact evidence. No behavior tests were added or changed for this presentation delivery. Manual review owns light/dark appearance, click and keyboard feel, populated/empty/busy states, picker clearing and public mobile fit. [Testing](Testing.md) owns subsequent test-work approval and selection.
