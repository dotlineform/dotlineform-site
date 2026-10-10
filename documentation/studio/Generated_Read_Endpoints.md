---
draft: false
doc_id: d-20260607-222033-d06f35
title: Generated Read Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Generated Read Endpoints

Generated read endpoints return existing Docs Viewer JSON artifacts without mutating source or generated files. The local `/docs/` shell reads Working through its owning service, including documents excluded from publication. [Generated Data Contracts](Generated_Data_Contracts.md) owns payload shapes and roots; [Docs Viewer Runtime](Docs_Viewer_Runtime.md) owns navigation and reader authority.

The service resolves Working from `docs-viewer/config/workspace/docs-workspace.json`. Requests reject retired `scope`, `stage` and `sub_scope` selectors. Named-collection artifacts use their configured `/docs/generated/external/<collection>/...` route rather than a selector on these ordinary generated reads. Public routes read the prepared repository/public projection directly.

## Tree Reads

Endpoints:

```text
GET /docs/index-tree
```

Returned data: Working's generated `index-tree.json` with current server-owned `publication_ignored` values added to nodes for management controls. Root fields are `generated_at`, `schema` and `docs`. There is no `viewer_options` or browser subtree/loadability policy.

Payload shape:

```json
{
  "generated_at": "2026-10-11T00:00:00Z",
  "schema": "docs_index_tree_v1",
  "docs": [
    {
      "doc_id": "d-20260424-000000-50b63f",
      "title": "Docs Viewer",
      "content_url": "/docs/doc?doc_id=d-20260424-000000-50b63f",
      "draft": false,
      "publication_ignored": false
    }
  ]
}
```

Used for:

- rendering the Docs Viewer navigation tree
- resolving parent/child relationships in manage mode

## Recent Reads

Endpoints:

```text
GET /docs/recent
```

Returned data: Working's saved `recent.json`, used by the route-configured Recent view. Readers own exact document navigation. [Generated Data Contracts](Generated_Data_Contracts.md#recent-contract) owns the payload contract.

Payload shape:

```json
{
  "schema": "docs_recent_v2",
  "limit": 20,
  "generated_at": "2026-10-11T00:00:00Z",
  "docs": [
    {
      "doc_id": "d-20260424-000000-50b63f",
      "title": "Docs Viewer",
      "timestamp": "2026-07-16",
      "parent_id": "d-20260419-000000-d2e47b",
      "parent_title": "Docs Viewer"
    }
  ]
}
```

Used for:

- rendering the route-configured Recent panel
- reading saved Recent metadata without rebuilding it

## Document Payload Reads

Endpoints:

```text
GET /docs/doc?doc_id=d-20260424-000000-50b63f
```

Returned data: the raw generated `by-id/<doc_id>.json` payload for the selected doc.

Payload shape:

```json
{
  "doc_id": "d-20260424-000000-50b63f",
  "title": "Docs Viewer",
  "added_date": "2026-06-07",
  "last_updated": "2026-06-07",
  "viewer_url": "/docs/?doc=d-20260424-000000-50b63f",
  "parent_id": "d-20260419-000000-d2e47b",
  "content_html": "<h1>Docs Viewer</h1>\n"
}
```

Validation and resolution:

- `doc_id` is required and must use the immutable document ID format.
- The service reads the exact configured Working `by-id/<doc_id>.json` path without consulting the Index or substituting another document.

Used for:

- loading selected document content in Docs Viewer
- inspecting Working documents excluded from publication
- refreshing a selected document after source edits

## Search Reads

Endpoints:

```text
GET /docs/search
```

Returned data: the saved Working Search index at its configured generated location. Reads do not rebuild Search or infer freshness from the document tree.

The current schema is `docs_viewer_search_index_v4`, carrying document/collection/report-host identities and postings without stage or result URLs. [Docs Viewer Search](Docs_Viewer_Search.md) owns the maintained payload and reader contract.

Used for:

- Docs Viewer search UI
- manage-mode validation that search artifacts exist after rebuilds

## Error Behavior

Generated read endpoints reject retired selectors, unsafe IDs, missing generated files, invalid JSON and unexpected payload paths. They do not write source, generated data or operation logs.
