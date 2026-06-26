---
doc_id: docs-viewer-semantic-references-implementation
title: Semantic References Implementation
added_date: 2026-06-02
last_updated: 2026-06-23
parent_id: docs-viewer
viewable: true
---
# Semantic References Implementation

This document records the current technical implementation of Docs Viewer semantic references: token parsing, registry ownership, generated lookup data, browser helper modules, generated reference artifacts, and report inputs.

Author-facing source-editor behavior is documented separately in [Semantic References Editor](/docs/?scope=studio&doc=docs-viewer-semantic-references-editor).
Future editor enhancements are tracked in [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor).

## Ownership

Docs Viewer owns semantic references while the tokens are authored in Docs Viewer Markdown and rendered by Docs Viewer builds.

Current responsibilities:

- parse `[[ref:...]]` tokens from source Markdown
- render recognized supported tokens as links
- leave unsupported or malformed token-like text literal
- emit generated semantic-reference relationship artifacts
- provide a lightweight registry for supported kinds, id normalization, and route construction
- provide generated browser-safe target lookup data for editor assistance
- provide browser helper modules that read and normalize registry and lookup data
- provide the read-only [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) management report

Semantic references are repo-specific Docs Viewer behavior, not portable Docs Viewer core.
Other repo-local apps may read the same browser-safe registry or generated relationship artifacts, but they should not introduce a service boundary just to consume this data.

## Source Syntax

Semantic references are authored as inline custom tokens:

```md
[[ref:<kind>:<id>|<label>]]
[[ref:<kind>:<id>]]
[[ref:<kind>:<id>|<label>]]{action=link}
```

Current supported token kinds:

- `work`
- `series`
- `moment`

Current supported action:

- `link`

The label is optional.
When the label is omitted, the builder uses the normalized target key.
Tokens inside fenced code blocks and inline code are left literal and do not produce generated reference records.

## Registry

The semantic-reference registry is checked in at:

```text
docs-viewer/config/semantic-references/registry.json
```

Browser URL in local manage mode:

```text
/docs-viewer/config/semantic-references/registry.json
```

Current schema id:

```text
docs_semantic_reference_registry_v1
```

The registry is the source of truth for:

- ordered supported token kinds
- id normalization policy
- canonical id pattern hints
- route construction metadata
- source-editor picker availability
- generated target lookup URL

Registry records are deliberately declarative.
Named normalizer implementations live in Python and JavaScript; the registry selects them by name.

Current normalizer vocabulary:

- `digits_left_pad`
- `series_id_or_slug`
- `slug`

Current registry-backed route output:

- `work`: `/works/?work=<work_id>`
- `series`: `/series/?series=<series_id_or_slug>`
- `moment`: `/moments/?doc=<moment_doc_id>`

The builder and browser helpers consume the same registry so supported-kind and route definitions do not drift.
Adding a new kind should normally start with a new registry kind record and only add code when the new kind needs a new id normalizer or target lookup source.

## Builder Path

The command entrypoint is:

```text
docs-viewer/build/build_docs.py
```

Semantic-reference build internals:

- `docs-viewer/build/docs_builder/semantic_references.py`
- `docs-viewer/build/docs_builder/semantic_registry.py`
- `docs-viewer/build/docs_builder/reference_artifacts.py`

Relevant builder responsibilities:

- detect semantic-reference tokens before Markdown rendering
- parse kind, id, optional label, and optional modifier
- skip fenced-code and inline-code occurrences
- load and normalize the checked-in registry
- normalize ids through the registry-selected normalizer
- construct rendered hrefs through registry route metadata
- render supported `link` tokens as links
- leave malformed, unsupported-kind, unsupported-action, or invalid-id token-like text literal
- collect reference records for generated artifacts
- write generated reference artifacts during full and targeted docs payload builds

The builder is registry-aware, not catalogue-validation-aware.
It does not read canonical catalogue records to decide whether a token should render.
Missing, stale, deleted, draft, or unpublished targets are report concerns, not build failures.

## Rendered Output

For a work reference:

```md
[[ref:work:00638|3 symbols]]
```

the builder renders:

```html
<a href="/works/?work=00638" target="_blank" rel="noopener noreferrer" data-ref-kind="work" data-ref-id="00638" data-ref-action="link">3 symbols</a>
```

Generated reference artifacts describe what the builder rendered.
For registry-rendered links, `target_status` is currently `rendered`.
That field does not assert catalogue existence.

## Generated Target Lookup

The source-editor picker uses one generated target lookup artifact:

```text
docs-viewer/generated/semantic-references/target-lookup.json
```

Browser URL in local manage mode:

```text
/docs-viewer/generated/semantic-references/target-lookup.json
```

Current schema id:

```text
docs_semantic_reference_target_lookup_v1
```

Command entrypoint:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/build/build_semantic_target_lookup.py --write
```

Implementation:

```text
docs-viewer/build/docs_builder/semantic_target_lookup.py
```

The lookup is a compact title-weighted browser artifact for editor assistance.
It is not a generic search index, not builder input, and not target-existence authority.

Rows use this simple shape:

```json
{
  "kind": "work",
  "id": "00638",
  "title": "3 symbols",
  "meta": ["2007", "3 symbols"]
}
```

Field intent:

- `kind`: token kind to insert
- `id`: canonical target id to insert
- `title`: primary title for matching, display, and inserted token label
- `meta`: optional compact secondary display fields, such as year/date display or a work's first resolved series title

The lookup includes only published targets because draft records do not have public link targets.
Catalogue write/build follow-through refreshes the lookup after relevant catalogue source or canonical data changes.
Moment targets are sourced from the generated public Docs Viewer `moments` scope, not from catalogue `works.json` or `series.json`.
The generator reads `docs-viewer/generated/docs/moments/index-tree.json` and per-moment payloads under `docs-viewer/generated/docs/moments/by-id/`.

The generated JSON is formatted with compact one-line target rows so records are easy to scan and cross-check.

## Browser Helper Modules

Registry and lookup browser helpers live under:

```text
docs-viewer/runtime/js/management/source-editor/
```

Current helper modules:

- `semantic-reference-registry.js`: fetches and normalizes the registry
- `semantic-targets.js`: normalizes lookup rows and ranks browser-side target matches
- `semantic-target-picker.js`: renders selectable target rows and owns list keyboard/mouse interaction
- `semantic-token-editor.js`: constructs semantic-reference token strings
- `semantic-token-picker-view.js`: hosted view that composes registry, lookup, list, and source-editor adapter behavior

These modules are management/source-editor-owned.
They are not public Docs Viewer runtime modules and their CSS belongs in the manage stylesheet.

The browser search model is intentionally simple:

- derive normalized target titles and title tokens in the browser
- rank exact normalized title matches first
- rank title prefix and title-token matches ahead of metadata matches
- use registry kind order, normalized title, and id as tie-breaks

Ids and `meta` fields can help display and tie-break results, but they should not dominate title search.

## Generated Reference Artifacts

Generated relationship artifacts are written under each docs scope output:

```text
assets/data/docs/scopes/<scope>/references/
```

Current files:

- `references/index.json`
- `references/by-doc/<doc_id>.json`
- `references/by-target/<target_kind>/<target_id_slug>.json`

Current schemas:

- `docs_semantic_references_index_v1`
- `docs_semantic_references_by_doc_v1`
- `docs_semantic_references_by_target_v1`

Each reference record includes:

- `source_scope`
- `source_doc_id`
- `source_title`
- `source_viewer_url`
- `target_kind`
- `target_id`
- `target_key`
- `target_href`
- `target_title`
- `target_status`
- `label`
- `action`
- `ordinal`

The index payload contains target summaries and `bucket_url` values for per-target payloads.
The by-doc payload is the source-owned list for one document.
The by-target payload is the reverse-reference bucket for one target.

## Targeted Build Behavior

Full builds parse all docs in the selected scope and derive all reference artifacts from that parse.

Targeted builds use `--only-doc-ids` to render selected docs only.
For semantic references, the builder:

- refreshes by-doc records for selected docs
- reads existing by-doc records for unselected docs
- derives by-target buckets from selected refreshed records plus existing unselected records
- removes stale selected by-doc records when selected docs no longer have references
- removes stale by-target buckets when the derived target set no longer contains them

Registry route or normalization changes need a full same-scope docs payload rebuild unless a future affected-id rule is added.
Catalogue target title, status, deletion, or publication changes do not affect builder render output, but may affect generated target lookup data or report audits.

## Report Runtime

The [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) report is a read-only Docs Viewer management report.

It reads:

- the selected scope's `references/index.json`
- each listed target bucket under `references/by-target/`

The report can show all configured docs scopes or one selected scope via `report_scope`.
It does not edit source Markdown, validate catalogue data, run broken-link checks, or rebuild generated payloads.

Future stale-target or suspicious-token checks should live in this report or a focused report-style audit, separate from builder success.
