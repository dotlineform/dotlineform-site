---
doc_id: docs-viewer-semantic-references-implementation
title: Semantic References Implementation
added_date: 2026-06-02
last_updated: 2026-06-02
parent_id: docs-viewer
viewable: true
---
# Semantic References Implementation

This document records the current implementation of Docs Viewer semantic references.
It describes what is implemented now, not the original v1 request or the planned v2 alignment work.

## Current Ownership

Current implementation ownership:

- Docs Viewer owns parsing `[[ref:...]]` tokens from Docs Viewer source Markdown.
- Docs Viewer owns rendered document output for those tokens.
- Docs Viewer owns generated semantic-reference relationship artifacts.
- Docs Viewer owns the read-only [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) management report.

Product direction:

- Analytics owns the direction for future semantic-reference maintenance, target support, tag integration, editor support data, document analysis, and visualisation/reference modules.
- Analytics-owned modules may consume or extend the generated relationship artifacts.
- A future migration should explicitly state which pieces move to Analytics and which Docs Viewer build contracts remain.

Semantic references are therefore not portable Docs Viewer core in the product sense, even though the current implementation is in the Docs Viewer builder.
They are currently implemented there because the tokens are authored in Docs Viewer source documents.

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

The implementation lives in `docs-viewer/build/build_docs.py`.

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
That is the main structural limitation v2 needs to address.

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
- `moment`: `/moments/<moment_id>/`

Current target-status behavior:

- unsupported kind: `target_status` is `unsupported_kind`
- invalid id shape: `target_status` is `invalid_id`
- missing catalogue record: `target_status` is `missing`
- existing catalogue record: `target_status` is the record status, such as `published` or `draft`

This current behavior validates more than type/action support.
It treats catalogue existence and publication status as build-time semantic-reference warning states.

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

## Known Alignment Issue

The planned v2 model says Docs Viewer should validate supported semantic types and actions, while target-object existence should be handled by host data, editor support, or link-health audits.

The current implementation does not fully match that model.
It reads catalogue records, records target status, warns for missing/non-published targets, and renders those target states as inert spans.

[Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2) owns the decision about whether to:

- preserve this host-aware validation as intentional current behavior
- or refactor semantic references so allowed type/action references render route-derived links and missing targets become separate link-health/editor-support findings.
