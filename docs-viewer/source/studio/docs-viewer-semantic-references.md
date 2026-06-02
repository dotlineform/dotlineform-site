---
doc_id: docs-viewer-semantic-references
title: Semantic References
added_date: 2026-05-18
last_updated: 2026-06-02
ui_status: report
parent_id: docs-viewer
viewable: true
viewer_report: semantic_references
viewer_report_access: manage
---
# Semantic References

This management report lists generated semantic references authored in Docs Viewer Markdown.

Use it to inspect which docs reference catalogue works, series, moments, or future registry targets through `[[ref:...]]` tokens.
The report defaults to all configured docs scopes; use the scope selector to focus on Studio, Analysis, or Library references.

## Current Implementation

Semantic references are authored in Docs Viewer source Markdown with inline tokens:

```md
[[ref:<kind>:<id>|<label>]]
[[ref:<kind>:<id>]]{action=link}
```

Current supported kinds:

- `work`
- `series`
- `moment`

Current supported action:

- `link`

The implemented parser and renderer live in `docs-viewer/build/build_docs.py`.
During a docs payload build, the builder expands valid tokens before Markdown rendering, emits rendered HTML with `data-ref-*` attributes, and writes generated relationship artifacts under:

```text
assets/data/docs/scopes/<scope>/references/
```

Important generated files:

- `references/index.json`
- `references/by-doc/<doc_id>.json`
- `references/by-target/<target_kind>/<target_id_slug>.json`

The `semantic_references` report reads `references/index.json`, then reads the per-target buckets from `references/by-target/`.
It is a read-only management report; it does not edit source Markdown, validate catalogue data, or rebuild generated docs payloads.

## Current Ownership

There are two ownership layers:

- Docs Viewer currently owns token parsing, rendered document output, generated docs relationship artifacts, and the management report that displays those artifacts.
- Analytics owns the product direction for semantic-reference maintenance, tag expansion, target-support data, document analysis, and future reference/visualisation modules.

This means semantic references are not portable Docs Viewer core in the product sense, even though the current build implementation is in the Docs Viewer builder because the tokens are authored in Docs Viewer source documents.
Future Analytics-hosted modules can consume or extend the generated relationship data, but that migration should keep the boundary explicit.

## Current Validation Behavior

The intended v2 model is that Docs Viewer validates supported semantic types and actions, while target-object existence is handled by host data, editor support, or link-health audits.

The current v1 implementation is more host-aware:

- it reads catalogue records for work, series, and moment references
- it uses catalogue data for resolved titles and hrefs when available
- it records `target_status` in generated reference artifacts
- missing targets warn and render as inert spans
- non-published catalogue targets warn and render as inert spans

That behavior is useful for surfacing catalogue problems, but it is different from treating missing objects like ordinary broken links.
The follow-on [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2) owns the decision about whether to preserve this host-aware validation or refactor it into separate editor/link-health diagnostics.

## Artifact Shape

Each by-doc payload records the references authored by one source doc.
Each by-target payload records the source docs that point at one semantic target.
The index payload lists target summaries and links to per-target buckets.

Reference records include:

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

The generated artifact schema is currently `docs_semantic_references_*_v1`.
Do not change it casually; editor, report, and future panel modules should first identify the concrete field they need.

## Related Requests

- [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references)
- [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
