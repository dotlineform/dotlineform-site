---
doc_id: scripts-docs-management-scripts-source-editor
title: Source Editor Scripts
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: scripts-docs-management-scripts
---
# Docs Viewer Source Editor Scripts

## `docs-viewer/services/docs_management_source_service.py`

Purpose: source body read/rebuild and local editor open helpers.

Ownership: owns the source-editor API contract and local source-open behavior.

Responsibilities:

- resolves selected docs through the configured source model
- verifies source paths stay inside scope roots
- parses exact existing front matter blocks
- returns source body text without front matter
- returns `sha256:<digest>` revision tokens for stale-write protection
- preserves front matter exactly during body-only writes
- normalizes submitted body line endings
- runs targeted docs payload and docs-search rebuild follow-through after body writes
- opens source docs with the configured or preferred local Markdown editor
- logs source-editor rebuild and open-source events

Not responsible for:

- metadata/front matter mutation workflows outside body-only editing
- staged import conversion
- route path constants

## Editor Selection

`DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP` in `var/local/site.env` wins when set. Without that setting, default editor selection checks:

```text
MarkEdit
Typora
Marked 2
Marked
```

If none are installed, macOS Launch Services chooses the default application for the Markdown file.
