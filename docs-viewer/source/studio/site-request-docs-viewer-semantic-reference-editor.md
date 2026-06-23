---
doc_id: site-request-docs-viewer-semantic-reference-editor
title: Docs Viewer Semantic Reference Editor Request
added_date: 2026-05-27
last_updated: 2026-06-23
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Semantic Reference Editor Request

Status: proposed

## Summary

Add semantic-reference token creation tools as an optional child feature of the existing manage-mode Markdown editor.

The goal is to let an author select text in the Markdown source buffer, choose a supported semantic target, and insert a valid semantic-reference token into the local editor buffer.
The edited source is still written and rebuilt only through the Markdown editor's `Rebuild doc` action.

Current model:

- [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation)
- [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) report.

## Reason

Docs semantic references are currently authored by typing tokens such as:

```md
[[ref:work:00638|3 symbols]]
```

That syntax is compact and useful, but it is error-prone when authors have to type target kinds, ids, visible text, and punctuation manually.

Docs Viewer can provide a constrained local helper:

- use the current text selection as a search seed and replacement range
- choose a supported semantic-reference type
- choose a target from registry-driven browser-side lookup controls
- insert the valid token with the selected target's canonical title as the link label
- leave the change in the local editor buffer until the user clicks `Rebuild doc`

The helper should reduce token authoring errors without hiding the underlying Markdown source model.
It is specific to this repo's semantic links (e.g. works, tags) and should be omitted from portable installs unless a future host-extension contract provides equivalent registry metadata.

## Goals

- add semantic-reference insertion controls to the Markdown source editor
- create a lightweight semantic-reference registry as the source of truth for supported types and target data
- allow selected text to be replaced by a supported semantic-reference token
- keep token insertion local in the editor buffer until `Rebuild doc`
- provide target picker/search controls where registry support data exists
- support only the current semantic-reference token kinds in v1: `work`, `series`, and `moment`
- use simple browser-side search on selected words for v1 target picking
- rely on the existing builder for token parsing, rendered output, and generated relationship artifacts
- keep semantic insertion logic in focused child modules under the current source-editor owner
- avoid adding repo-specific semantic editing to portable Docs Viewer core

## Anticipated Blast Radius

This section is intended to keep implementation scope explicit before code work starts.

### Initial V1 Implementation

Runtime JavaScript and config should live in these areas:

- `docs-viewer/runtime/js/management/source-editor/` for source-editor-owned semantic modules, including token construction, selected-text adapter usage, registry reads, target lookup reads, and picker support helpers
- `docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js` for registering the manage-only `semantic-token-picker` hosted view
- `docs-viewer/runtime/js/management/docs-viewer-manage.js` for manage-owned mapping from document display mode to default info-panel view
- `docs-viewer/static/css/docs-viewer-manage.css` for semantic picker styling; semantic picker CSS should not be added to the public/shared Docs Viewer stylesheet
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js`, `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js`, `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js`, `site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js`, and `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js` only for generic hosted-view plumbing, such as passing hosted-view context or applying a configured default info-panel view
- `docs-viewer/config/semantic-references/registry.json` for the checked-in semantic-reference registry
- `docs-viewer/generated/semantic-references/target-lookup.json` for the generated browser-side lookup used by v1 selected-text search

Existing Docs Viewer modules expected to need integration code:

- `docs-viewer/runtime/js/management/source-editor/source-editor.js` should expose a narrow source-editor context adapter for reading selected text, replacing the selected range, returning focus, and reporting insertion status
- the hosted-view registry should expose `semantic-token-picker` as a manage-only `info` panel view while the Markdown source editor is active
- the management entrypoint should configure context/info panel default-view selection so rendered documents use `metadata-info` and the source editor uses `semantic-token-picker`; shared runtime code should not hardcode the semantic picker id
- `docs-viewer/build/build_docs.py` may need to read the registry for supported token kinds and route construction so builder support does not drift from editor support, while still avoiding target-existence validation
- the target lookup generator should read existing source/generated catalogue data for current v1 kinds and emit compact title-weighted rows for `work`, `series`, and `moment`

Service changes expected for v1:

- no new management service endpoint
- no new target lookup API
- no write-service changes
- no source read/write/rebuild endpoint changes
- only static browser-readable config/generated-data exposure should be needed, using existing local Docs Viewer/static route patterns where possible

Settled implementation decisions before v1 starts:

- `build_docs.py` must switch to registry-backed semantic rendering before source-editor picker work starts; the builder and editor should not temporarily carry separate supported-kind or route definitions.
- the target lookup generator should live with Docs Viewer build internals, with a thin command entrypoint at `docs-viewer/build/build_semantic_target_lookup.py` and implementation under `docs-viewer/build/docs_builder/semantic_target_lookup.py`
- the target lookup generator should write `docs-viewer/generated/semantic-references/target-lookup.json` and be runnable manually; catalogue write/build follow-through should invoke it after catalogue source or canonical data changes
- `build_docs.py` should not own target lookup generation; docs payload rebuilds and semantic target lookup freshness are related but separate build products
- `docs-viewer/config/semantic-references/registry.json` and `docs-viewer/generated/semantic-references/target-lookup.json` are already browser-addressable in local manage mode through existing `/docs-viewer/config/` and `/docs-viewer/generated/` static route prefixes once the files exist
- the source editor should expose its semantic-token adapter through hosted-view context during `markdown-source` activation, and clear it on teardown; avoid broad globals such as `window`-level editor handles
- if a shared adapter holder is needed, make it an explicit scoped runtime service with `setActiveSourceEditorContextAdapter()` and `clearActiveSourceEditorContextAdapter()` lifecycle rather than route-global mutable state
- shared runtime may carry generic source-editor context adapter lifecycle and generic info-panel default-view mapping, but semantic picker ids, modules, CSS selectors, and row UI stay under management/source-editor ownership
- picker search should read the current selection when the picker opens, then update while the picker is active on textarea selection/input events with a small debounce; it should not run background lookup work while the context/info panel is closed
- v1 lookup rows should stay minimal: `kind`, `id`, `title`, and optional `meta`
- v1 lookup generation should include only published targets because draft records do not have link targets
- v1 ranking should derive normalized titles and title tokens in the browser, then prefer exact normalized title match, title prefix match, all selected tokens present in title, partial title-token match, then tie-break by registry kind order, normalized title, and id
- ids and compact metadata should be available for display and tie-breaks, but should not dominate selected-text search ranking
- entering source edit mode should not auto-open the context/info panel; it should only switch the default info-panel view to `semantic-token-picker`
- if the info panel is already open when the Markdown source editor becomes active, switching the visible hosted view to `semantic-token-picker` is acceptable because the active context changed

### Adding A New Token Kind Later

Supporting a new token kind should have a smaller blast radius than v1.
The expected change set should be:

- add a new `kinds` record to `docs-viewer/config/semantic-references/registry.json`
- add or reuse a named id normalizer in JavaScript and Python only if the new kind needs a new id shape
- teach the target lookup generator how to emit compact browser-safe lookup rows for that kind, if the kind should participate in selected-text search
- ensure `build_docs.py` can construct the rendered href from the registry route metadata
- add focused tests for the new registry kind, normalizer if any, lookup rows if searchable, and rendered link output
- update Semantic References documentation if the kind changes author-facing syntax or report interpretation

Adding a new token kind should not require:

- new source-editor panel code
- new context/info panel host code
- new source read/write/rebuild endpoints
- new target lookup services
- hard-coded supported-kind lists in route controllers or picker UI

Open questions for future token kinds:

- whether every new kind should be searchable in the picker, or whether some kinds should be supported only by later v2 direct-id flows
- whether a new kind's source data is safe and compact enough for browser-side lookup
- whether the semantic references report should audit the new kind differently from existing generated reference artifacts

## Product Model

The semantic-reference editor is an optional tool inside the manage-mode Markdown source editor.
The source editor is useful for viewing and small Markdown edits, but this request treats semantic-token authoring as the main product reason to extend it.

The picker should not introduce another panel.
In current panel language, it is a different hosted view inside the existing context/info panel shell, alongside the selected-document metadata view.
The implementation may still use `infoPanel` names until a focused rename is worth the churn, but the product role is the broader context panel.

It should expose:

- semantic-reference target search driven by the current editor selection or explicit picker search input and the registry
- selected-text handling for replacement range and search seeding when a range is selected
- token preview or clear insertion summary
- validation messages for unsupported type, missing target id, invalid target title, or unavailable support data

The commit point remains the Markdown editor's `Rebuild doc` action.

## Picker Use Case

The v1 UI should be centered on turning selected Markdown text into a semantic-reference token.

Expected flow:

1. The user selects text in the source editor, such as `3 symbols`.
2. The semantic token picker view, hosted in the existing context/info panel, notices the selection and uses it as the search query.
3. The picker searches browser-safe target data for every kind in the registry.
4. Results are shown using the token kind and existing record metadata, similar to catalogue search results.
5. The user chooses one result.
6. The editor replaces the selected text with a token such as `[[ref:work:00638|3 symbols]]`, using the selected target's canonical title as the label.
7. After `Rebuild doc`, the published document renders that token as a link such as `/works/?work=00638`.

For `3 symbols`, the picker may show both a `series` result and a `work` result if both records match.
For a broader selected query or explicit picker search such as `symbols`, v1 should still use simple word search across the current lookup records.

The selected target supplies the token kind, id, and canonical label.
Selected text is not used as the inserted label because it may be abbreviated or misspelled.
If there is only a caret/insertion point, choosing a target inserts a labeled token such as `[[ref:work:00638|3 symbols]]` at the caret.
Cursor expansion, direct id lookup, manual id entry, and additional token kinds are deferred to v2.

## Token Insertion Behavior

For selected text:

```text
3 symblos
```

and target:

```text
kind: work
id: 00638
title: 3 symbols
```

the editor inserts:

```md
[[ref:work:00638|3 symbols]]
```

The inserted syntax should match the current builder grammar documented in [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation).

Supported target kinds should come from a semantic-reference registry JSON file, not from a route-local hard-coded list.

The helper should avoid inserting tokens when:

- the selected semantic-reference type is unsupported
- no target id is selected or entered
- the target title cannot be used as a token label
- required registry metadata is missing

Validation behaviour:

- The backend does not need to validate every body token before writing.
- The editor should offer targets from the browser-side lookup data, but that lookup is authoring assistance, not target-existence authority.
- Target picker assistance should not require new server endpoints.
- The builder should not validate semantic-reference support or link-target existence. If a typed sequence is not a recognized supported token, it should remain plain rendered text.
- Link targets may be deleted or changed after a document build, so target existence is outside the builder's control.
- The semantic references report can audit generated reference artifacts and surface possible issues separately from build success.

## Registry And Support Data

This request depends on a semantic-reference registry.

The registry should define, for each semantic-reference type:

- type id
- id normalization policy
- route helper or route pattern

The picker should use a generated semantic-target lookup JSON, not unrelated generic search indexes.
The registry should point to that lookup once, and each target row in the lookup should carry its own `kind`.

The semantic-reference editor should read registry metadata through a focused browser helper.

- It should not duplicate supported type lists, route patterns, or target lookup paths inline in route/controller code.
- Read-oriented support behavior should stay in browser modules wherever it can safely consume generated JSON or browser config.

UI should include:

- target lookup,
- target picker option shaping,
- context-panel hosted-view copy,
- context/info panel view registration,
- supported token-kind metadata.

The backend should not become a general read orchestrator for UI state when the same data can be supplied through generated artifacts or Docs Viewer config.

## Proposed Registry File And Schema

Proposed checked-in registry file:

- `docs-viewer/config/semantic-references/registry.json`

Browser URL in local/manage Docs Viewer:

- `/docs-viewer/config/semantic-references/registry.json`

Schema id:

- `docs_semantic_reference_registry_v1`

Use one small browser-readable registry that can be fetched directly by the source editor.
Do not add a JSON Schema file in the first slice.
The runtime helper can validate the few required fields it consumes.

Top-level fields:

- `schema_version`: registry schema id
- `target_lookup_url`: generated semantic-target lookup JSON URL
- `kinds`: ordered semantic-reference kind records

Kind fields:

- `kind`: token kind, such as `work`
- `id`: id normalization and editor-matching metadata
- `route`: browser route construction metadata
- `source_editor`: source-editor availability and control hints

Example v1 payload:

```json
{
  "schema_version": "docs_semantic_reference_registry_v1",
  "target_lookup_url": "/docs-viewer/generated/semantic-references/target-lookup.json",
  "kinds": [
    {
      "kind": "work",
      "id": {
        "normalizer": "digits_left_pad",
        "width": 5,
        "input_pattern": "^\\d{1,5}$",
        "canonical_pattern": "^\\d{5}$",
        "example": "00638"
      },
      "route": {
        "type": "query",
        "path": "/works/",
        "param": "work"
      },
      "source_editor": {
        "selection_search": true,
        "picker": true
      }
    },
    {
      "kind": "series",
      "id": {
        "normalizer": "series_id_or_slug",
        "input_pattern": "^[a-z0-9][a-z0-9-]*$",
        "example": "009"
      },
      "route": {
        "type": "query",
        "path": "/series/",
        "param": "series"
      },
      "source_editor": {
        "selection_search": true,
        "picker": true
      }
    },
    {
      "kind": "moment",
      "id": {
        "normalizer": "slug",
        "input_pattern": "^[a-z0-9][a-z0-9-]*$",
        "example": "lotus-pond"
      },
      "route": {
        "type": "query",
        "path": "/moments/",
        "param": "moment"
      },
      "source_editor": {
        "selection_search": true,
        "picker": true
      }
    }
  ]
}
```

Keep the registry declarative.
It should tell the editor what kinds exist, how to normalize ids, where to load the semantic-target lookup, and how to build routes.
Presence in `kinds` means the semantic-reference kind is supported.
The only v1 action is `link`, so the registry should not model actions until a second action has a real use case.
The source editor should represent semantic-reference kinds with their token ids, such as `work`, `series`, and `moment`, rather than separate UI labels.
The actual normalizer implementations should live in JavaScript and Python by name, using a small shared vocabulary:

- `digits_left_pad`
- `series_id_or_slug`
- `slug`

The builder and editor should consume the same registry, but the builder remains the final parse/render authority during rebuild.
The builder should use the registry to decide which token shapes it can render as links.
It should not report unsupported kinds, missing targets, unpublished targets, or deleted targets as build warnings.

## Generated Semantic Target Lookup

The picker should use one generated semantic-target lookup JSON built specifically for token insertion.
This lookup is not a generic search index.
The selected editor text is only a search seed and replacement range, so likely matches should still be close to the target title rather than broad metadata such as year, medium, status, or ids.

Proposed generated lookup file:

- `docs-viewer/generated/semantic-references/target-lookup.json`

Browser URL in local/manage Docs Viewer:

- `/docs-viewer/generated/semantic-references/target-lookup.json`

Schema id:

- `docs_semantic_reference_target_lookup_v1`

The lookup generator can run whenever source data changes, like the existing catalogue lookup modules.
It should read canonical/generated source data for supported target kinds and write a compact browser-safe payload for the editor.
V1 should include only published targets because draft records do not have link targets.

Example lookup payload:

```json
{
  "schema_version": "docs_semantic_reference_target_lookup_v1",
  "targets": [
    {
      "kind": "series",
      "id": "005",
      "title": "3 symbols",
      "meta": ["2007"]
    },
    {
      "kind": "work",
      "id": "00638",
      "title": "3 symbols",
      "meta": ["2007", "3 symbols"]
    }
  ]
}
```

Lookup field intent:

- `kind`: token kind to insert
- `id`: canonical target id to insert
- `title`: primary title for matching and display
- `meta`: optional compact secondary display fields, such as `year_display` or `date_display`; work rows can also include the first resolved series title

Search should be browser-side and title-weighted:

- exact normalized title match first
- title prefix or token match next
- ids and metadata can be available for display, but should not dominate selection-search ranking

This keeps the picker aligned with the real interaction: selected text is likely a rough title query, while the inserted label should come from the selected target.
If the user selects `3 symbols`, matching title records should rank above incidental metadata matches.
If the user selects `symbols`, title-token matches can participate by deriving tokens from each row title in the browser.

## Context Panel Integration

The semantic token picker is a view in the existing context/info panel, not another panel and not a second sidebar.
It should use the same panel shell, close button, status area, and hosted-view lifecycle used by the current metadata/info view.

Initial view identity:

- panel: `info`
- view id: `semantic-token-picker`
- access: manage-only
- availability: only when the Markdown source editor is active and has supplied a semantic-token adapter

The picker view owns target search UI, result selection, and insertion-status copy.
It does not own the textarea, dirty-state truth, source write/rebuild, document-display mode switching, or rendered-view reload.

The source editor should provide the picker view with a narrow adapter for:

- reading current selection text and offsets
- replacing the selected range with a token
- restoring focus to the textarea
- receiving insertion validation/status messages

Panel view selection should be driven by the active outside context, not by controls inside the info panel.
The metadata/info view remains available for selected-document context, and the semantic-token picker becomes the active info-panel view while Markdown source editing is active.

The default context-panel view should follow the active main view:

- when the rendered document is active, opening the context/info panel should show `metadata-info`
- when the Markdown source editor is active, opening the context/info panel should show `semantic-token-picker` if it is available
- when the source editor exits back to the rendered document, the context/info panel should return to `metadata-info` or close according to the existing panel state rules

This default-view choice is a management entrypoint setting.
Shared Docs Viewer runtime code may apply a generic document-mode-to-default-info-view mapping, but it should not hardcode `semantic-token-picker` or other semantic-reference feature details.

This makes the semantic picker feel like source-editor context rather than a separate destination.
The info panel should keep a simple `info` title, no `Document metadata` label, and no internal view-switching toolbar.

This keeps panel ownership aligned with the current Docs Viewer model:

- the context/info panel hosts selected-document and source-editor context views
- document/source mode owns which info-panel view is active
- the source editor owns Markdown source editing
- semantic-reference modules own token-specific lookup, construction, and insertion behavior

## Relationship To Markdown Editor

The current Markdown editor implementation remains the owner of source editing lifecycle.
It lives under `docs-viewer/runtime/js/management/source-editor/` and is registered as the manage-only `markdown-source` document display mode.

The source editor owns:

- source read endpoint
- source write/rebuild endpoint
- source revision protection
- front matter/source-contract validation
- local source buffer
- dirty state
- `Rebuild doc`
- rendered-view reload
- document-display-mode lifecycle
- textarea rendering, focus, selection, and leave prompts

This request owns:

- semantic-reference controls inside the source editor
- registry-driven type metadata
- target picker/search behavior
- token construction and insertion into the local buffer
- insertion-specific validation messages

Semantic-token modules should receive a narrow source-editor adapter for operations such as reading the current selection, replacing selected text, focusing the textarea, and showing validation/status messages.
They should not own source reads, source writes, rebuild submission, dirty-state truth, or rendered-view reload.

Semantic-reference insertion should not block basic Markdown source editing.

## Infrastructure

Use the existing live source-editor owner:

- `docs-viewer/runtime/js/management/source-editor/`

Candidate semantic files inside the current source-editor folder:

- `semantic-token-editor.js` for token insertion helpers
- `semantic-token-toolbar.js` for controls mounted inside the source editor UI
- `semantic-token-picker-view.js` for the context/info panel hosted view
- `semantic-target-picker.js` for reusable target selection rendering inside the hosted view
- `semantic-targets.js` for client-side support reads and option normalization
- `semantic-reference-registry.js` for registry reads/normalization if not shared elsewhere

`semantic-target-picker.js` should be a lightweight Docs Viewer source-editor component, not a direct import of Studio catalogue picker code.
It can reuse the interaction pattern from `docs-viewer/runtime/js/management/docs-viewer-management-parent-picker.js`: delegated mouse selection, active row state, ArrowUp/ArrowDown, Enter, Escape, and an `onSelect(target)` callback.
It should own rendering selectable rows from `{ kind, id, title, meta }`, but it should not know about token construction, source-editor buffer changes, registry loading, or rebuild behavior.
Design the component so the selectable-list behavior is easy to extract later, but do not create a generic shared component in v1.
The first implementation has only one confirmed consumer and a domain-specific row shape, so premature extraction would force generic API decisions before a second use case proves them.
If another Docs Viewer management feature later needs the same interaction, promote the generic core to a shared helper such as `docs-viewer/runtime/js/management/shared/selectable-list.js`, leaving `semantic-target-picker.js` as the source-editor adapter.

The hosted view should be registered through the existing hosted-view registry as an `info` panel view.
It should not create a new panel host, sidebar, app-shell region, or route-level display mode.
Its CSS belongs in `docs-viewer/static/css/docs-viewer-manage.css`, not `site/docs-viewer/static/css/docs-viewer.css`, so the public Docs Viewer route does not load semantic picker selectors.

`source-editor.js` should stay focused on display-mode lifecycle, textarea state, dirty/save/rebuild behavior, and rendered-view return.
It can register semantic-token controls when the registry and helper modules are available, passing only a narrow editor adapter into those modules.

If the semantic module is absent, disabled, or unsupported for the current install, the Markdown editor should continue to work without semantic-token controls.

## Proposed Implementation Steps

### 1. Registry-Backed Builder And Target Lookup Preparation

Tasks:

- [x] add `docs-viewer/config/semantic-references/registry.json` with v1 `work`, `series`, and `moment` kind records
- [x] add Python registry read/normalization helpers for builder use
- [x] update semantic-reference rendering so the builder derives supported kinds, id normalization, and route construction from the registry
- [x] keep builder behavior limited to rendering recognized semantic tokens and emitting generated reference artifacts
- [x] remove builder dependence on catalogue existence/status for semantic-reference render success
- [x] ensure missing, draft, unpublished, deleted, or stale targets do not create builder warnings or test-script failures
- [x] keep stale-target and suspicious-token auditing in focused report logic rather than build success logic
- [x] add `docs-viewer/build/docs_builder/semantic_target_lookup.py` for compact target lookup payload generation
- [x] add `docs-viewer/build/build_semantic_target_lookup.py` as the manual command entrypoint
- [x] generate `docs-viewer/generated/semantic-references/target-lookup.json` from browser-safe catalogue data for current v1 kinds
- [x] wire catalogue write/build follow-through to refresh the target lookup after relevant catalogue source or canonical data changes
- [x] verify the registry and lookup files are readable through existing local Docs Viewer static route prefixes

Acceptance:

- builder, editor, and target lookup support all derive v1 supported kinds from the registry
- `work`, `series`, and `moment` tokens render through registry route metadata
- generated semantic-reference artifacts continue to describe rendered recognized references
- generated reference artifacts do not claim catalogue target existence as builder truth
- missing or stale catalogue targets are report concerns, not build failures
- target lookup generation is independent of docs payload rebuilds
- no new management service endpoint or target lookup API is introduced

### 2. Registry Read Helper

Tasks:

- [x] add a browser helper that reads and normalizes the semantic-reference registry
- [x] expose supported types, target lookup URL, and source-editor surface availability
- [x] handle missing or malformed registry data with clear unavailable states

Acceptance:

- semantic editor controls do not hardcode supported type lists
- missing registry data disables semantic controls without breaking the Markdown editor
- diagnostics can explain why semantic insertion is unavailable

### 3. Context Panel Hosted View

Tasks:

- [x] register `semantic-token-picker` as a manage-only `info` panel hosted view
- [x] make the view available only while the Markdown source editor can provide the semantic-token adapter
- [x] use the existing context/info panel shell, status area, close behavior, and hosted-view lifecycle
- [x] make the context/info panel default to `semantic-token-picker` while the Markdown source editor is active
- [x] make the context/info panel default to `metadata-info` while the rendered document is active
- [x] remove the info-panel label and internal hosted-view toolbar; outside document/source context selects the active panel view
- [x] keep the `semantic-token-picker` default mapping in the management entrypoint rather than hardcoding it in shared runtime
- [x] keep semantic picker styles in the management stylesheet rather than the public/shared stylesheet
- [x] keep metadata/info as a separate hosted view in the same panel
- [x] pass only the narrow source-editor adapter and registry-derived support data into the picker view

Acceptance:

- semantic token picking does not create a new panel, sidebar, or route display mode
- the picker can be opened as a context/info panel view when source editing is active
- the context/info panel surfaces metadata for rendered docs and the semantic picker for source editing
- switching between document/source modes updates the active info-panel view without losing source-editor dirty state or triggering source writes
- the metadata/info hosted view remains available through the same panel model

### 4. Target Picker Support

Tasks:

- [x] load the generated semantic-target lookup from the registry-defined URL
- [x] search title-focused target records browser-side from the current editor selection
- [x] search the current v1 token kinds from the current editor selection: `work`, `series`, and `moment`
- [x] render candidate rows from lookup `title`, `id`, `kind`, and `meta` fields
- [x] use a lightweight `semantic-target-picker.js` list component for row rendering, mouse selection, active row state, and keyboard selection behavior
- [x] keep `semantic-target-picker.js` local to the source-editor feature in v1, while structuring the selectable-list behavior so it can be promoted to a shared management helper after a second consumer appears
- [x] handle stale or missing target data without changing builder behavior

Acceptance:

- work, series, and moment target support follows the registry
- selecting `3 symbols` can surface both matching work and series targets when both records exist
- selected text search ranks title matches ahead of incidental metadata matches
- picker list behavior follows the existing Docs Viewer parent-picker interaction pattern without importing Studio catalogue picker code
- picker list code is designed for future extraction but is not generalized before there is a second Docs Viewer management consumer
- picker behavior can be traced to registry metadata
- target ids remain opaque host ids
- stale, missing, or deleted targets do not become builder or test-script validation failures
- target picker assistance does not introduce server-side target lookup

### 5. Token Construction And Insertion

Tasks:

- [x] read selected text from the Markdown editor
- [x] build a semantic-reference token from selected type, target id, and target title
- [x] insert the token at the current selection or caret offsets
- [x] keep the inserted token in the local editor buffer until `Rebuild doc`
- [x] preserve browser-native undo behavior where practical

Acceptance:

- selected text can be replaced by a supported semantic-reference token using the target title as the label
- an explicit picker search can insert a labeled semantic-reference token at the current caret when no text is selected
- no insertion happens without a target id
- inserted syntax matches the current builder grammar
- token insertion does not write source or trigger rebuild directly
- token insertion is implemented through a narrow source-editor adapter rather than by reaching into source read/write/rebuild services

### 6. Focused Verification And Docs Follow-Through

Tasks:

- [x] add focused tests for registry-backed builder render output and generated reference artifacts
- [x] add focused tests for semantic-target lookup generation
- [x] add focused tests for browser ranking
- [x] add focused tests for registry normalization
- [x] add focused tests for target option shaping
- [x] add focused tests for token construction
- [x] add browser smoke coverage for semantic insertion inside the Markdown editor
- [x] update semantic-reference implementation and editor docs after implementation

Acceptance:

- tests cover success and unavailable-registry states
- tests cover stale/missing target behavior without builder warnings or failures
- docs explain that semantic insertion is a repo-specific manage-mode helper layered into the existing source editor

## Open Questions

- Should the semantic references report flag unsupported typed token-like text, or only audit recognized generated references?

## Deferred To V2

The following ideas are useful but out of scope for v1:

- insertion-point refresh that detects the word or id around a collapsed cursor
- cursor seed expansion and punctuation-boundary rules
- direct id references, including exact matches such as `00001-001`
- generated exact-target records for high-cardinality kinds
- `work_detail` and other additional token kinds beyond current `work`, `series`, and `moment`
- manual target-id entry
- link-text replacement from a resolved id record title
- tag or tag-alias search

## Risks

- token insertion can produce invalid syntax if escaping rules are incomplete
- target lookup, modal copy, and config reads could drift into backend orchestration or inline route-controller logic
- semantic-token behavior could take over source-editor lifecycle responsibilities if module boundaries are too broad
- semantic-token picking could accidentally be implemented as a new panel instead of a hosted context/info panel view
- repo-specific semantic editing could be mistaken for portable Docs Viewer functionality
- semantic insertion could become coupled to a single UI shape before the Analytics surfacing model is clear
- registry and builder behavior could diverge if both define supported types independently
- builder or test scripts could drift into semantic validation that should belong to editor assistance or reporting

Mitigations:

- derive supported types from the registry
- keep source read/write/rebuild, dirty state, and rendered reload owned by the existing source editor
- keep token construction helpers small and tested
- keep support reads, option shaping, context-panel view config, and picker behavior in focused browser modules
- register the picker as an existing context/info panel hosted view, not a new panel host
- document semantic editing as this repo's manage-mode integration, not portable Docs Viewer core
- keep the builder responsible for rendering recognized links, not validating semantic support or target existence
- use the semantic references report, not build/test failure, for any future audit of possible semantic-reference issues
- keep semantic insertion optional so the Markdown editor remains useful without it

## Verification

Suggested implementation checks:

```bash
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_routes.py
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_mutations.py
```

Add focused tests or smoke checks for:

- [x] semantic-reference registry read/normalization
- [x] semantic-target lookup generation
- [x] title-weighted target ranking
- [ ] missing registry unavailable state
- [x] target option normalization
- [x] token construction
- [x] token insertion into selected source text
- [x] no source write before `Rebuild doc`
