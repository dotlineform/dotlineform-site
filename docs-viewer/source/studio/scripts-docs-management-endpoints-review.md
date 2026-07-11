---
doc_id: scripts-docs-management-endpoints-review
title: Docs Review Endpoints
added_date: 2026-07-11
last_updated: 2026-07-11
summary: Local package-rooted API contract for Docs Review capabilities, package reads, builds, assets, generated payloads, and temporary Markdown writes.
parent_id: scripts-docs-management-endpoints
viewable: true
---
# Docs Review Endpoints

Docs Review endpoints are local-only JSON APIs served by the standalone Docs Viewer service. They are independently gated by `DOCS_VIEWER_REVIEW_ENABLED`; enabling `/docs/` management does not grant review-package access.

Endpoint constants live in `docs-viewer/services/docs_review_routes.py`. Business behavior lives in `docs_review_service.py`, `docs_review_packages.py`, and `docs_review_build.py`.

Browser requests require an allowed loopback origin; same-origin and non-browser requests without an `Origin` header are accepted. Disabled review endpoints return `403`, missing packages or files return `404`, invalid contracts return `400`, and unexpected failures return `500`. JSON responses use `Cache-Control: no-store`.

## `GET /docs-review/capabilities`

Query parameters: none.

Returns external workspace status plus independently projected review capabilities:

```json
{
  "ok": true,
  "available": true,
  "workspace": {},
  "capabilities": {
    "review_packages_list": true,
    "review_manifest_read": true,
    "review_asset_inventory_read": true,
    "review_generated_read": true,
    "review_source_read": true,
    "review_source_write": true,
    "review_build": true,
    "canonical_write": false,
    "management": false,
    "publish": false
  }
}
```

The positive review capabilities are false when the configured external workspace is unavailable. The three authority exclusions remain false in all states.

## `GET /docs-review/packages`

Query parameters: none.

Lists validated folders under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/`.

Each package record includes package identity, title, source scope, default document, document count, generated-document count, and whether generated output is current for the complete source set.

Folders with safe identities but invalid manifests or source contracts are returned in `rejected` with concise diagnostics. They are not exposed as selectable packages.

## `GET /docs-review/packages/manifest`

Query parameters:

```text
package_id=<package_id>
```

Returns the trusted validated manifest and package document count. The manifest must use `docs_review_validated_package_v1`, match the folder identity, use `status: validated`, and identify `source_scope`.

## `GET /docs-review/packages/assets`

Query parameters:

```text
package_id=<package_id>
```

Returns any present allowlisted inventory files:

- `assets.json`
- `links.json`
- `embedded-content.json`

Missing optional inventories are omitted rather than treated as errors.

## `GET /docs-review/packages/assets-content/<package_id>/<asset-path>`

Serves an inventoried package asset.

The requested path must:

- match a `package_path` in `inventories/assets.json`
- stay under the selected package's `assets/` folder
- contain no absolute path, traversal, or symlink segment
- resolve to an existing file

Only `media` and `interactive` inventory kinds are supported by the current review builder.

## `GET /docs-review/packages/index-tree`

Query parameters:

```text
package_id=<package_id>
```

Returns the package-local `generated/index-tree.json` wrapper used by the shared Docs Viewer tree adapter. The frontend runs Build and retries when the selected validated package has not yet been built.

## `GET /docs-review/packages/payload`

Query parameters:

```text
package_id=<package_id>
doc_id=<doc_id>
```

Returns one package-local generated document payload from `generated/by-id/<doc_id>.json`. The requested `doc_id` must identify a source document in the selected package.

## `GET /docs-review/packages/source`

Query parameters:

```text
package_id=<package_id>
doc_id=<doc_id>
```

Returns:

```json
{
  "ok": true,
  "package_id": "example-package",
  "doc_id": "example-doc",
  "source_body": "# Example\n",
  "source_revision": "sha256:...",
  "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/example-package/source/example-doc.md"
}
```

The endpoint returns only the body after front matter. It does not write files.

## `POST /docs-review/packages/build`

Expected JSON:

```json
{
  "package_id": "example-package"
}
```

Build validates the selected package, uses a synthetic local-external Docs Viewer configuration, and writes only the selected package's `generated/` folder.

The response includes document and asset counts, warnings, diagnostics, generated path, and summary text.

## `POST /docs-review/packages/source`

Expected JSON:

```json
{
  "package_id": "example-package",
  "doc_id": "example-doc",
  "source_revision": "sha256:...",
  "source_body": "# Example\n\nEdited review text.\n"
}
```

The write service:

- rejects a missing or stale revision
- preserves existing front matter exactly
- rejects `parent_id` updates
- writes the normalized body atomically inside the package
- rebuilds package-local generated output
- restores the previous source text if rebuilding fails

The response includes the next revision token, rebuild diagnostics, and summary text.

## Authority Boundary

These routes do not accept:

- arbitrary filesystem paths
- configured Docs Viewer scope ids as write targets
- canonical source targets
- parent or hierarchy mutations
- publish, promotion, import, delete, or general management actions

See [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) for the durable workflow and ownership contract.

The planned [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) flow remains a managed `/docs/` import capability. Docs Review may hand off safe package/document identities, but this endpoint family must not gain configured-source apply authority.
