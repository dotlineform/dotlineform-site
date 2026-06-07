---
doc_id: scripts-docs-broken-links
title: Broken Links Script
added_date: 2026-04-23
last_updated: 2026-06-06
parent_id: docs-viewer
viewable: true
---
# Docs Broken Links Script

This script lists Docs Viewer links for one selected docs scope and reports links whose targets no longer resolve.

```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_broken_links.py --scope studio
```

JSON output:
```bash
$HOME/miniconda3/bin/python3 docs-viewer/services/docs_broken_links.py --scope library --json
```

Flags:

- `--scope NAME` required
- `--repo-root PATH` override repo-root auto-detection
- `--json` print the structured payload used by the Docs Viewer report and docs-management endpoint

JSON entries include:

- `from_page_text`
- `from_page_url`
- `from_page_scope`
- `from_page_doc_id`
- `from_page_source_path`
- `link_text`
- `link_url`

Rules:

- link text is not compared with the current target title
- changed, shortened, or historically preserved labels are allowed

Ignored links:

- links inside rendered code blocks
- fragment-only links within the same doc, such as `#section`
- same-doc viewer links with a fragment, such as `/docs/?scope=studio&doc=this-doc#section`
- same-doc source-markdown links with a fragment

## Data Source

The script reads generated docs payloads rather than raw source Markdown.

Inputs:

- `docs-viewer/generated/docs/studio/index-tree.json`
- `docs-viewer/generated/docs/studio/by-id/<doc_id>.json`
- `assets/data/docs/scopes/library/index-tree.json`
- `assets/data/docs/scopes/library/by-id/<doc_id>.json`

Model:

- the selected scope provides the source docs that are scanned for links
- both scopes are loaded into the target registry so cross-scope docs links can still resolve when valid
- unresolved `.md` links left in rendered docs output are treated as `not found`

## Docs Viewer Report

The Docs Viewer report [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links) uses this same logic through the Docs management endpoint `POST /docs/broken-links`. This is a Docs Viewer management report for a read-only docs audit, not a public hosted feature. That keeps the browser report thin while leaving the script reusable from the terminal.

The report depends on the local Docs management API through the configured Docs Viewer service.

1. Docs Viewer loads this report-backed document in manage mode
2. the report module selects the current or requested docs scope
3. the report sends `POST <DOCS_VIEWER_BASE_URL>/docs/broken-links`
4. the Docs Viewer service runs the shared docs broken-links logic for that scope
5. the report renders the returned issue list
