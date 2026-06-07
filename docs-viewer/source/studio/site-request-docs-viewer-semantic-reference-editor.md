---
doc_id: site-request-docs-viewer-semantic-reference-editor
title: Docs Viewer Semantic Reference Editor Request
added_date: 2026-05-27
last_updated: 2026-06-07
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Semantic Reference Editor Request

Status:

- proposed
- depends on [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2), especially the semantic-reference registry

## Summary

Add semantic-reference token creation tools to the manage-mode Markdown editor.

The goal is to let an author select text in the Markdown source buffer, choose a supported semantic target, and insert a valid semantic-reference token into the local editor buffer.
The edited source is still written and rebuilt only through the Markdown editor's `Rebuild doc` action.

## Reason

Docs semantic references are currently authored by typing tokens such as:

```md
[[ref:work:00638|3 symbols]]
```

That syntax is compact and useful, but it is error-prone when authors have to type target kinds, ids, labels, and punctuation manually.

Docs Viewer can provide a constrained local helper:

- use the current text selection as the visible label
- choose a supported semantic-reference type
- choose or enter a target id through registry-driven controls
- insert the valid token around the selected text
- leave the change in the local editor buffer until the user clicks `Rebuild doc`

The helper should reduce token authoring errors without hiding the underlying Markdown source model.
It is specific to this repo's dotlineform semantic links and should be omitted from portable installs unless a future host-extension contract provides equivalent registry metadata.

## Goals

- add semantic-reference insertion controls to the Markdown source editor
- use the semantic-reference registry as the source of truth for supported types, actions, ownership, target data, and surfacing
- allow selected text to be wrapped in a supported semantic-reference token
- keep token insertion local in the editor buffer until `Rebuild doc`
- provide target picker/search controls where registry support data exists
- allow a controlled manual target-id entry path where appropriate
- rely on the existing builder for token parsing, rendered output, generated relationship artifacts, and warning behavior
- keep semantic insertion logic in focused browser modules
- avoid adding repo-specific semantic editing to portable Docs Viewer core

## Product Model

The semantic-reference editor is an optional tool inside the manage-mode Markdown source editor.

It should expose:

- semantic-reference type selection driven by the registry
- target picker/search or manual target-id entry based on registry support data
- selected-text label handling
- token preview or clear insertion summary
- validation messages for unsupported type/action, missing selected text, missing target id, or unavailable support data

The commit point remains the Markdown editor's `Rebuild doc` action.

## Token Insertion Behavior

For selected text:

```text
3 symbols
```

and target:

```text
kind: work
id: 00638
```

the editor inserts:

```md
[[ref:work:00638|3 symbols]]
```

The inserted syntax should match the current builder grammar documented in [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation).

Supported target kinds should come from the semantic-reference registry defined by [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2), not from a route-local hard-coded list.

The insertion UI should leave room for future target kinds, such as `tag`, without changing the source-view model.
Future kinds remain repo-specific integrations unless a separate portable host-extension contract is defined later.

The helper should avoid inserting tokens when:

- no text is selected
- the selected semantic-reference type is unsupported
- no target id is selected or entered
- required registry metadata is missing
- the selected text spans an unsupported region if the source editor can detect that reliably

Validation behaviour:

- The backend does not need to validate every body token before writing.
- Docs Viewer should validate allowed semantic types and actions through builder/registry behavior, not whether the submitted target id resolves to a real object.
- Target picker assistance is not the same as target-existence validation.
- The targeted rebuild should surface builder warnings or errors after the write/rebuild step.

## Registry And Support Data

This request depends on a semantic-reference registry.

The registry should define, for each semantic-reference type:

- type id and label
- object owner
- reference owner
- allowed actions
- id normalization policy
- route helper or route pattern
- target existence policy
- target data source for picker/search support
- eligible surfaces, including source editor controls
- diagnostics policy

The semantic-reference editor should read registry metadata through a focused browser helper.

- It should not duplicate supported type lists, route patterns, target-data paths, or ownership assumptions inline in route/controller code.
- Read-oriented support behavior should stay in browser modules wherever it can safely consume generated JSON or browser config.

UI should include:

- target lookup,
- target picker option shaping,
- modal/view copy,
- view registration,
- supported token-kind metadata.

The backend should not become a general read orchestrator for UI state when the same data can be supplied through generated artifacts or Docs Viewer config.

## Relationship To Markdown Editor

The Markdown editor request owns:

- source read endpoint
- source write/rebuild endpoint
- source revision protection
- front matter/source-contract validation
- local source buffer
- dirty state
- `Rebuild doc`
- rendered-view reload

This request owns:

- semantic-reference controls inside the source editor
- registry-driven type/action metadata
- target picker/search behavior
- token construction and insertion into the local buffer
- insertion-specific validation messages

Semantic-reference insertion should not block basic Markdown source editing.

## Infrastructure

Candidate module folder:

- `docs-viewer/runtime/js/modules/source-editor/`

Candidate semantic files inside that folder:

- `semantic-token-editor.js` for token insertion helpers
- `semantic-target-picker.js` for target selection UI
- `semantic-targets.js` for client-side support reads and option normalization
- `semantic-reference-registry.js` for registry reads/normalization if not shared elsewhere

The source editor module can register semantic tools when the registry and helper modules are available.

If the semantic module is absent, disabled, or unsupported for the current install, the Markdown editor should continue to work without semantic-token controls.

## Proposed Implementation Steps

### 1. Registry Read Helper

Tasks:

- add a browser helper that reads and normalizes the semantic-reference registry
- expose supported types, actions, target-data source, and source-editor surface availability
- handle missing or malformed registry data with clear unavailable states

Acceptance:

- semantic editor controls do not hardcode supported type lists
- missing registry data disables semantic controls without breaking the Markdown editor
- diagnostics can explain why semantic insertion is unavailable

### 2. Target Picker Support

Tasks:

- load target options from registry-defined browser-safe data sources where available
- normalize ids, labels, and optional search fields for picker use
- support manual id entry when the registry allows it
- handle stale or missing target data without changing builder validity semantics

Acceptance:

- work, series, and moment target support follows the registry
- picker behavior can be traced to registry metadata
- target ids remain opaque host ids
- target picker assistance does not become target-existence validation

### 3. Token Construction And Insertion

Tasks:

- read selected text from the Markdown editor
- build a semantic-reference token from selected type, target id, selected text, and action
- insert the token at the current selection offsets
- keep the inserted token in the local editor buffer until `Rebuild doc`
- preserve browser-native undo behavior where practical

Acceptance:

- selected text can be wrapped as a supported semantic-reference token
- no insertion happens without selected text and target id
- inserted syntax matches the current builder grammar
- token insertion does not write source or trigger rebuild directly

### 4. Focused Verification And Docs Follow-Through

Tasks:

- add focused tests for registry normalization, target option shaping, and token construction
- add browser smoke coverage for semantic insertion inside the Markdown editor
- update semantic-reference implementation and editor docs after implementation

Acceptance:

- tests cover success and unavailable-registry states
- docs explain that semantic insertion is a repo-specific manage-mode helper layered on the Markdown editor

## Open Questions

- What is the exact semantic-reference registry file path and schema?
- Should the initial editor expose only `work`, `series`, and `moment`, or include disabled/future `tag` metadata?
- Should manual target-id entry always be available, or only when enabled by a registry field?
- Should unsupported selected ranges be blocked in v1, or should token insertion operate only on textarea selection offsets?
- How should unsupported semantic type warnings be displayed when rebuild succeeds?
- Should token insertion expose actions beyond `link` once the registry exists, or keep only `link` for the first slice?

## Risks

- token insertion can produce invalid syntax if escaping rules are incomplete
- target lookup, modal copy, and config reads could drift into backend orchestration or inline route-controller logic
- repo-specific semantic editing could be mistaken for portable Docs Viewer functionality
- semantic insertion could become coupled to a single UI shape before the Analytics surfacing model is clear
- registry and builder behavior could diverge if both define supported types independently

Mitigations:

- derive type/action support from the registry
- keep token construction helpers small and tested
- keep support reads, option shaping, modal/view config, and picker behavior in focused browser modules
- document semantic editing as this repo's manage-mode integration, not portable Docs Viewer core
- rely on builder diagnostics for semantic-reference warnings after rebuild
- keep semantic insertion optional so the Markdown editor remains useful without it

## Verification

Suggested implementation checks:

```bash
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_routes.py
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_mutations.py
```

Add focused tests or smoke checks for:

- semantic-reference registry read/normalization
- missing registry unavailable state
- target option normalization
- manual id entry if enabled
- token construction
- token insertion into selected source text
- no source write before `Rebuild doc`