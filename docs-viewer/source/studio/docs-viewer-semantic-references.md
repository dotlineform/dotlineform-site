---
doc_id: docs-viewer-semantic-references
title: Semantic References
added_date: 2026-05-18
last_updated: 2026-06-23
ui_status: report
parent_id: docs-viewer
viewable: true
viewer_report: semantic_references
viewer_report_access: local
---
# Semantic References

This management report lists generated semantic references authored in Docs Viewer Markdown.

Use it to inspect which docs reference catalogue works, series, moments, or future registry targets through `[[ref:...]]` tokens.
The report defaults to all configured docs scopes; use the scope selector to focus on Studio, Analysis, or Library references.

## Report Inputs

The report reads generated semantic-reference artifacts from each selected docs scope:

- `references/index.json`
- `references/by-target/<target_kind>/<target_id_slug>.json`

The report can show all configured docs scopes or one selected scope via `report_scope`.
It is read-only and does not edit source Markdown, validate catalogue data, run broken-link checks, or rebuild generated payloads.

Current semantic-reference docs:

- [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation) documents registry, lookup, builder, generated artifacts, browser helpers, and report inputs.
- [Semantic References Editor](/docs/?scope=studio&doc=docs-viewer-semantic-references-editor) documents the manage-mode source-editor picker and token insertion workflow.
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor) tracks v2 editor enhancements.
