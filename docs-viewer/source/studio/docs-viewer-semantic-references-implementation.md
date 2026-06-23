---
doc_id: docs-viewer-semantic-references-implementation
title: Semantic References Implementation
added_date: 2026-06-02
last_updated: 2026-06-23
parent_id: docs-viewer
viewable: true
---
# Semantic References Implementation

This document records the current implementation of Docs Viewer semantic references.

## Current Ownership

Current implementation ownership:

- Docs Viewer owns parsing `[[ref:...]]` tokens from Docs Viewer source Markdown.
- Docs Viewer owns rendered document output for those tokens.
- Docs Viewer owns generated semantic-reference relationship artifacts.
- Docs Viewer owns the read-only [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) management report.

Current registry ownership:

- Docs Viewer should own the lightweight semantic-reference registry while these tokens are authored in Docs Viewer source documents and surfaced through Docs Viewer documents, generated reference artifacts, reports, and source-editor tooling.
- The registry should describe what token kinds exist, how ids are normalized, where browser-safe target data can be read, and how rendered links are built.
- Other repo-local apps, including Analytics, may read the same registry and generated relationship artifacts directly when they add visualization or analysis tools.
- Those apps are separate surfaces in the same repository, not hard service boundaries. Do not introduce server calls or ownership indirection just to let one local app read browser-safe registry or generated data owned by another local app.

Semantic references are repo-specific Docs Viewer behavior, not portable Docs Viewer core.
They are implemented here because the tokens are authored in Docs Viewer source documents.
If another app later becomes the primary authoring or maintenance surface, that change should state which registry fields and build contracts move, rather than adding compatibility layers around an unclear split.

## Source Syntax

Semantic references are authored as inline custom tokens:

```md
[[ref:<kind>:<id>|<label>]]
[[ref:<kind>:<id>]]
[[ref:<kind>:<id>|<label>]]{action=link}
```

Current supported kinds:

- `work`
- `series`
- `moment`

Current supported action:

- `link`

The label is optional.
When the label is omitted, the builder uses the `target_key`.

Tokens inside fenced code blocks and inline code are left literal and do not produce reference records.

## Builder Path

The command entrypoint is `docs-viewer/build/build_docs.py`.
Semantic-reference builder internals live in `docs-viewer/build/docs_builder/semantic_references.py`, with generated relationship payload assembly in `docs-viewer/build/docs_builder/reference_artifacts.py`.
Registry reads and normalization live in `docs-viewer/build/docs_builder/semantic_registry.py`.
The generated target lookup builder lives in `docs-viewer/build/docs_builder/semantic_target_lookup.py`, with command entrypoint `docs-viewer/build/build_semantic_target_lookup.py`.

Relevant responsibilities:

- detect `[[ref:...]]` tokens before Markdown rendering
- parse the kind, target id, optional label, and optional modifier
- skip fenced-code and inline-code occurrences
- load the checked-in semantic-reference registry
- derive supported kinds, id normalization, and route construction from the registry
- render recognized supported token shapes as links
- leave malformed, unsupported, unsupported-action, or invalid-id token-like text literal
- collect semantic-reference records for generated artifacts
- include reference-artifact writes in full and targeted docs payload builds

Current registry:

- `docs-viewer/config/semantic-references/registry.json`
- schema: `docs_semantic_reference_registry_v1`
- browser URL in local manage mode: `/docs-viewer/config/semantic-references/registry.json`
- generated target lookup URL: `/docs-viewer/generated/semantic-references/target-lookup.json`

The registry currently supports only `work`, `series`, and `moment`.
It is browser-readable and small enough for the source editor, report code, and other local browser modules to consume directly.
Insertion-point detection, direct id references, exact-target records, and additional token kinds belong in a later slice.

## Target Resolution

The current renderer is registry-aware, not catalogue-validation-aware.
It does not read canonical catalogue records to decide whether a token should render.

Current registry-backed id normalization:

- `work`: strips non-digits and left-pads to 5 digits
- `series`: accepts a numeric id left-padded to 3 digits, or a lowercase slug id
- `moment`: accepts a lowercase slug id

Current registry-backed route output:

- `work`: `/works/?work=<work_id>`
- `series`: `/series/?series=<series_id_or_slug>`
- `moment`: `/moments/?moment=<moment_id>`

The builder's job is to parse supported token shapes, render links for recognized semantic-reference tokens, and write generated reference artifacts.
It does not validate whether link targets currently exist.
Targets can be deleted or changed after a document build, so target existence is outside the builder's control.

The source-editor semantic-token helper can offer likely targets from browser-safe lookup data.
That assistance should stay lightweight: it helps the author choose a likely target, but it is not authoritative validation and should not become target-existence checking.
Do not add a server endpoint for picker data that can be supplied through static registry data or generated browser-safe lookup data.

## Rendered Output

The builder renders a navigable link only when all of these are true:

- the token parsed successfully
- the token kind exists in the registry
- the action is `link`
- the id can be normalized by the registry-declared normalizer
- the route can be constructed from the registry route metadata

For a work reference:

```html
<a href="/works/?work=00638" target="_blank" rel="noopener noreferrer" data-ref-kind="work" data-ref-id="00638" data-ref-action="link">3 symbols</a>
```

Unsupported, malformed, unsupported-action, or invalid-id token-like text remains literal rendered text and does not produce a generated reference record.
The builder does not render catalogue-missing or catalogue-draft warning spans.

Generated reference artifacts describe what the builder rendered, not whether the target is still semantically valid.
For registry-rendered links, `target_status` is `rendered`.

If we want to identify possible unsupported token-like text or stale targets, that should be a report concern.
The semantic references report can scan generated reference artifacts, and a future report pass could optionally scan source text for suspicious token-like strings.
That audit should not change builder success, generated payload success, or test-script success.

## Generated Target Lookup

The source-editor picker uses a generated target lookup:

```text
docs-viewer/generated/semantic-references/target-lookup.json
```

Browser URL in local manage mode:

```text
/docs-viewer/generated/semantic-references/target-lookup.json
```

The command entrypoint is:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/build/build_semantic_target_lookup.py --write
```

The lookup is a compact title-weighted browser artifact for editor assistance.
Rows use only `kind`, `id`, `title`, and optional `meta` fields.
The lookup includes only published targets because draft records do not have link targets.
The picker should derive normalized titles and title tokens in the browser for v1.
The generated file is written as valid JSON with compact one-line target rows so records are easy to scan and cross-check.
It is not the source of truth for builder rendering and it is not a target-existence authority.
Catalogue write/build follow-through refreshes this lookup after catalogue source or canonical data changes.

## Source Editor Picker

The manage-mode Markdown source editor registers a source-only info-panel hosted view:

- hosted view id: `semantic-token-picker`
- view module: `docs-viewer/runtime/js/management/source-editor/semantic-token-picker-view.js`
- registry helper: `docs-viewer/runtime/js/management/source-editor/semantic-reference-registry.js`
- target lookup/search helper: `docs-viewer/runtime/js/management/source-editor/semantic-targets.js`
- selectable result list: `docs-viewer/runtime/js/management/source-editor/semantic-target-picker.js`
- token construction helper: `docs-viewer/runtime/js/management/source-editor/semantic-token-editor.js`
- stylesheet: `docs-viewer/static/css/docs-viewer-manage.css`

`source-editor.js` owns the Markdown textarea and exposes a narrow active source-editor context adapter while source editing is mounted.
The adapter supports reading the current selection, replacing the selected range, focusing the textarea, reporting source-editor status, and selection-change subscriptions.
It does not expose source reads, rebuild submission, dirty-state ownership, or rendered-document reload behavior.

When Markdown source mode is active, the info toggle defaults to `semantic-token-picker`.
When rendered-document mode is active, the info toggle defaults back to `metadata-info`.
If the semantic picker panel is open when the source editor unmounts, the panel switches back to metadata.
The default view mapping is supplied by the management entrypoint.
Shared Docs Viewer runtime code applies the generic mapping and adapter lifecycle, but does not hardcode semantic picker ids, modules, or CSS selectors.
The info panel shell keeps a single `info` title and no internal view-switching toolbar; document/source mode changes select the active hosted view.

The picker reads the registry and generated target lookup through static browser URLs.
It searches target titles in the browser, renders compact target rows from `title`, `kind`, `id`, and `meta`, and inserts a token only when the source editor has selected text and a chosen target.
Choosing a result replaces the current selection with `[[ref:<kind>:<id>|<selected text>]]` in the local editor buffer.
The change is not written until the existing Markdown source editor `Rebuild doc` action runs.

## Generated Artifacts

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
- `source_path`
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

The index payload contains target summaries and `bucket_url` values for the per-target payloads.
The by-doc payload is the source-owned list for one doc.
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
Catalogue target title, status, deletion, or publication changes do not affect builder render output, but may affect the generated target lookup or future report audits.

## Report Runtime

The [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) report is a read-only Docs Viewer management report.

It reads:

- the selected scope's `references/index.json`
- each listed target bucket under `references/by-target/`

The report can show all configured docs scopes or one selected scope via `report_scope`.
It does not edit source Markdown, validate catalogue data, run broken-link checks, or rebuild generated payloads.

## Issues

The current implementation has no registry, so supported kinds, allowed actions, route construction, target reads, and ownership assumptions are hard-coded in the builder.

The next slice should add the lightweight Docs Viewer-owned registry before expanding the source editor.
The semantic-token editor can then use that registry plus browser-safe target data to provide authoring assistance without adding local-service calls.

The builder should still own parse/render behavior and generated reference artifacts.
Editor-side checks are assistance, not authoritative validation.
Build scripts and tests should not fail because a semantic reference points at a missing, unpublished, deleted, or otherwise unsupported target.
Any future audit of possible semantic-reference issues should belong in the semantic references report or a focused report-style check, separate from build success.
