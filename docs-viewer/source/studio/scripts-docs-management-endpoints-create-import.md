---
doc_id: scripts-docs-management-endpoints-create-import
title: Create And Import Endpoints
added_date: 2026-06-07
last_updated: 2026-07-12
parent_id: scripts-docs-management-endpoints
---
# Docs Viewer Create And Import Endpoints

## `POST /docs/create`

Expected data:

```json
{
  "scope": "studio",
  "title": "New Doc",
  "parent_id": "docs-viewer"
}
```

Actions:

- validates `scope` against configured docs scopes
- defaults blank titles to `New Doc`
- generates a unique `doc_id` and filename stem from the title
- validates `parent_id` inside the same scope when supplied
- writes a new Markdown source file under the configured scope root
- writes `added_date` and `last_updated` to the current minute
- omits `viewable` for Studio docs, which makes them viewable by default
- writes `viewable: false` for Analysis and Library docs
- rebuilds targeted generated docs payloads and targeted docs search for the new doc
- writes watcher-suppression markers for the new source file

Returned data includes the created doc identity, source path, viewer URL, mutation flags, rebuild diagnostics, summary text, and `dry_run`.

## `GET /docs/import-source-files`

Query parameters: none.

Returned data:

```json
{
  "ok": true,
  "files": [
    {
      "filename": "example.md",
      "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/example.md",
      "format": "markdown",
      "size_bytes": 0,
      "modified": "..."
    }
  ]
}
```

Used for:

- rendering staged-file choices in the Docs Viewer import modal
- showing file metadata before an import writes source docs

Supported staged source formats:

- `html`: `.html`, `.htm`
- `markdown`: `.md`, `.markdown`
- `markdown_package`: direct child package folders containing exactly one Markdown file
- `text`: `.txt`
- `svg`: `.svg`
- `image`: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
- `file`: `.pdf`, `.zip`, `.csv`, `.tsv`, `.json`, `.jsonl`, `.docx`, `.xlsx`, `.pptx`

## `POST /docs/import-source`

Expected data:

```json
{
  "scope": "studio",
  "staged_filename": "example.md",
  "include_prompt_meta": false,
  "overwrite_doc_id": "",
  "confirm_overwrite": false,
  "replacement_doc_id": "",
  "replacement_title": "",
  "preview_only": false
}
```

Actions:

- validates `scope` and resolves `staged_filename` as a direct child of the W0-configured shared import drop-zone
- parses staged HTML, Markdown, Markdown packages, text, SVG, image, and downloadable-file formats
- converts import output to Markdown source
- validates generated Markdown with the shared Docs Viewer Markdown renderer
- derives new `doc_id` and filename stem from the staged filename unless replacement fields are supplied
- returns collision details instead of writing when the proposed target already exists
- creates a new source doc when there is no collision
- overwrites an existing doc only when `overwrite_doc_id` and `confirm_overwrite: true` are both supplied
- preserves overwritten doc `doc_id`, filename, `added_date`, `parent_id`, and current viewability state
- refreshes `last_updated` on create or overwrite
- materializes inline raster media, package media, standalone image wrappers, downloadable-file wrappers, and interactive HTML assets only during write operations
- supports `preview_only: true` for non-writing preview responses
- rebuilds targeted generated docs payloads and targeted docs search after successful writes
- logs import-source activity when a create or overwrite actually writes

Returned data can include preview Markdown, proposed doc identity, operation type, collision information, media plans, interactive HTML plans, written media records, created or overwritten source path, rebuild diagnostics, summary text, and `dry_run`.

## Reviewed-Package Follow-On

[Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) will extend the managed import family with schema-aware Data Sharing JSON/JSONL collection import.

The endpoints now use the shared `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` drop-zone. Endpoint services resolve it through `configured_workspace_paths(repo_root).import_staging`, return marker-rooted paths, and report import unavailable through the W0 workspace capability contract when the root cannot be used. They do not fall back to repo-local staging.

It will resolve a safe immutable staged-file identity through Data Sharing metadata, detect supported package headers before the generic JSON/JSONL file fallback, and normalize document records before shared validation, media planning, source writes, and rebuild work. It will not import from the derived Docs Review `source/*.md` projection.

For each selected record, the user can create, explicitly overwrite, or skip. Collisions must require an explicit choice rather than silently selecting overwrite or a replacement ID.
