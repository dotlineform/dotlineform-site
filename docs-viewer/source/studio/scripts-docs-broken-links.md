---
doc_id: scripts-docs-broken-links
title: Docs Broken Links Audit
added_date: 2026-04-23
last_updated: "2026-05-13 20:20"
parent_id: docs-viewer
sort_order: 19000
---
# Docs Broken Links Audit

Script:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_broken_links.py --scope studio
```

## Purpose

This script audits Docs Viewer links for one selected docs scope and reports links whose targets no longer resolve.

It reports one problem type:

- `not found`
  the link target does not resolve to a published docs page

Current link-text rule:

- link text is not compared with the current target title
- changed, shortened, or historically preserved labels are allowed
- target resolution is still strict

Ignored links:

- links inside rendered code blocks
- fragment-only links within the same doc, such as `#section`
- same-doc viewer links with a fragment, such as `/docs/?scope=studio&doc=this-doc#section`
- same-doc source-markdown links with a fragment

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
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_broken_links.py --scope studio
```

JSON output:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_broken_links.py --scope library --json
```

Flags:

- `--scope NAME`
  required
  current values: `studio`, `library`
- `--repo-root PATH`
  override repo-root auto-detection
- `--json`
  print the structured payload used by the Docs Viewer report and docs-management endpoint

## Docs Viewer Integration

The Docs Viewer report [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links) uses this same audit logic through the Docs management endpoint:

- `POST /docs/broken-links`

That keeps the browser report thin while leaving the audit reusable from the terminal.

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
