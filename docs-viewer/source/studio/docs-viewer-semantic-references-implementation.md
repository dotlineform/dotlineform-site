---
doc_id: docs-viewer-semantic-references-implementation
title: Semantic References Implementation
added_date: 2026-06-02
last_updated: 2026-06-22
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
When the label is omitted, the builder uses the resolved catalogue title when available, then falls back to the `target_key`.

Tokens inside fenced code blocks and inline code are left literal and do not produce reference records.

## Builder Path

The command entrypoint is `docs-viewer/build/build_docs.py`.
Semantic-reference builder internals live in `docs-viewer/build/docs_builder/semantic_references.py`, with generated relationship payload assembly in `docs-viewer/build/docs_builder/reference_artifacts.py`.

Relevant responsibilities:

- detect `[[ref:...]]` tokens before Markdown rendering
- parse the kind, target id, optional label, and optional modifier
- skip fenced-code and inline-code occurrences
- validate the kind against the hard-coded supported-kind set
- validate the action against the hard-coded action set
- normalize target ids for current catalogue kinds
- read catalogue records for title, status, and href resolution
- render either a link or inert span
- collect semantic-reference records for generated artifacts
- include reference-artifact writes in full and targeted docs payload builds

Current constants:

- `SEMANTIC_REF_SUPPORTED_KINDS = {"work", "series", "moment"}`
- `SEMANTIC_REF_ALLOWED_ACTIONS = {"link"}`

There is no semantic-reference registry in the current implementation.
Allowed kinds, allowed actions, route construction, target-data reads, and ownership assumptions are hard-coded in the builder.
That is the main structural limitation the semantic-reference editor request needs to address before adding picker UI.

Target registry shape for the next slice:

- checked-in, browser-readable data owned by Docs Viewer
- small enough to be loaded directly by the source editor and other local browser modules
- explicit fields for current kind ids, id normalization, target-data source, route construction, and source-editor availability
- no backend read orchestration for data that is already safe to expose as static JSON or generated browser data

The first registry-backed editor slice should support only the current token kinds, `work`, `series`, and `moment`, using simple browser-side search from selected source-editor text.
Insertion-point detection, direct id references, exact-target records, and additional token kinds belong in a later slice.

## Target Resolution

The current resolver is catalogue-aware.
It reads canonical catalogue records from:

```text
studio/data/canonical/catalogue/works.json
studio/data/canonical/catalogue/series.json
studio/data/canonical/catalogue/moments.json
```

Current id normalization:

- `work`: strips non-digits and left-pads to 5 digits
- `series`: accepts a numeric id left-padded to 3 digits, or a lowercase slug id
- `moment`: accepts a lowercase slug id

Current route output:

- `work`: `/works/?work=<work_id>`
- `series`: `/series/?series=<series_id_or_slug>`
- `moment`: `/moments/?moment=<moment_id>`

Current target-status behavior:

- unsupported kind: `target_status` is `unsupported_kind`
- invalid id shape: `target_status` is `invalid_id`
- missing catalogue record: `target_status` is `missing`
- existing catalogue record: `target_status` is the record status, such as `published` or `draft`

This current behavior validates more than type/action support.
It treats catalogue existence and publication status as build-time semantic-reference warning states.

That should not be the long-term boundary.
The builder's job should be to parse supported token shapes, render links for recognized semantic-reference tokens, and write generated reference artifacts.
It should not validate semantic-reference support as a build concern, and it should not validate whether link targets currently exist.
Targets can be deleted or changed after a document build, so target existence is outside the builder's control.

The source-editor semantic-token helper can offer likely targets from browser-safe lookup data.
That assistance should stay lightweight: it helps the author choose a likely target, but it is not authoritative validation and should not become target-existence checking.
Do not add a server endpoint for picker data that can be supplied through static registry data or generated browser-safe lookup data.

## Rendered Output

The builder renders a navigable link only when all of these are true:

- the token parsed successfully
- the action is allowed
- the resolver produced no warning
- the target is linkable
- the target has an href

For a published work reference:

```html
<a href="/works/?work=00638" target="_blank" rel="noopener noreferrer" data-ref-kind="work" data-ref-id="00638" data-ref-action="link">3 symbols</a>
```

For a warning state, the builder renders an inert span with `data-ref-status`.
Missing targets and non-published targets currently render this way:

```html
<span data-ref-kind="work" data-ref-id="12345" data-ref-action="link" data-ref-status="missing">missing target</span>
```

Malformed tokens render as inert spans with `data-ref-status="malformed"` and do not produce a generated reference record.

Parsed tokens with warnings still produce generated reference records.
That includes unsupported kinds, unsupported actions, invalid ids, missing targets, and non-published targets.

Target registry-backed behavior should be simpler:

- recognized supported token shapes render as links using registry route construction
- unsupported token-like text remains plain rendered text
- missing, unpublished, deleted, or otherwise changed link targets do not block rendering and do not create build warnings
- generated reference artifacts describe what the builder rendered, not whether the target is still semantically valid

If we want to identify possible unsupported token-like text or stale targets, that should be a report concern.
The semantic references report can scan generated reference artifacts, and a future report pass could optionally scan source text for suspicious token-like strings.
That audit should not change builder success, generated payload success, or test-script success.

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

Resolver-data changes outside docs source, such as catalogue title, status, or route changes, need a full same-scope docs payload rebuild unless a future affected-id rule is added.

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
