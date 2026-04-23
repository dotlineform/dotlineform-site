---
doc_id: scripts-docs-broken-links
title: "Docs Broken Links Audit"
last_updated: 2026-04-23
parent_id: scripts
sort_order: 15
---
# Docs Broken Links Audit

Script:

```bash
./scripts/docs/docs_broken_links.py --scope studio
```

## Purpose

This script audits Docs Viewer links for one selected docs scope.

It reports two problem types:

- `not found`
  the link target does not resolve to a published docs page
- `wrong title`
  the link resolves to a published docs page, but the visible link text does not exactly match that page's current title

Current title rule:

- title matching is strict
- intentionally shortened labels are reported

## Data Source

The audit reads generated docs payloads rather than raw source Markdown.

Current inputs:

- `assets/data/docs/scopes/studio/index.json`
- `assets/data/docs/scopes/studio/by-id/<doc_id>.json`
- `assets/data/docs/scopes/library/index.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Current model:

- the selected scope provides the source docs that are scanned for links
- both scopes are loaded into the target registry so cross-scope docs links can still resolve when valid
- unresolved `.md` links left in rendered docs output are treated as `not found`

## Commands

Human-readable summary:

```bash
./scripts/docs/docs_broken_links.py --scope studio
```

JSON output:

```bash
./scripts/docs/docs_broken_links.py --scope library --json
```

Flags:

- `--scope NAME`
  required
  current values: `studio`, `library`
- `--repo-root PATH`
  override repo-root auto-detection
- `--json`
  print the structured payload used by the Studio page and docs-management endpoint

## Studio Integration

The Studio route `/studio/docs-broken-links/` uses this same audit logic through the Docs Management Server endpoint:

- `POST /docs/broken-links`

That keeps the browser page thin while leaving the audit reusable from the terminal.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
