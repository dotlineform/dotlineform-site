---
doc_id: docs-viewer-review
title: Docs Review
added_date: 2026-07-11
last_updated: 2026-07-11
summary: Durable product, workflow, package, editing, and authority contract for the local returned-package review route.
parent_id: docs-viewer
viewable: true
---
# Docs Review

## Purpose

Docs Review is the local isolated preview and temporary editing surface for document packages that Data Sharing has already validated.

It is served at `/docs-review/` by the standalone Docs Viewer service. It reuses the shared Docs Viewer tree, document renderer, panel layout, route state, source editor, and CSS through the explicit `review` app context and a returned-package provider.

Docs Review is not:

- a configured Docs Viewer scope
- a copy of the Docs Viewer frontend
- a returned-package validator or transport owner
- a canonical import, promotion, merge, or commit tool

## Ownership Boundary

Data Sharing owns:

- export provenance and portable package contracts
- returned-package staging and validation
- materializing validated source and asset files under the external workspace root

Docs Viewer Import owns the planned import of the immutable staged JSONL associated with a review package. Managed import will let the user create, explicitly overwrite, or skip records; it will not treat the derived preview Markdown as import input.

Docs Review owns only:

- listing validated review packages
- building package-local generated previews
- rendering package documents and inventoried assets
- temporary Markdown body editing with revision checks
- package inventory visibility
- links to canonical counterparts for manual comparison

Canonical source remains outside Docs Review authority. The route exposes no canonical write, management, publish, promotion, or import-apply capability. A future review control may hand safe package/document identities to the managed `/docs/` import flow without granting that authority to the review app context.

## Enablement And Route

`DOCS_VIEWER_REVIEW_ENABLED` independently enables the route and its package-rooted APIs.

- `bin/local-all` enables Docs Review by default.
- `DOCS_VIEWER_REVIEW_ENABLED=0` suppresses the route and API family.
- launching `docs-viewer/bin/docs-viewer` directly keeps review disabled unless it is explicitly enabled.

Review URLs use package identity rather than configured scope identity:

```text
/docs-review/?package=<package_id>&doc=<doc_id>
/docs-review/?package=<package_id>&doc=<doc_id>&view=source
```

- `package` selects one validated package and is preserved in internal route changes.
- `doc` selects one document within that package.
- `view=source` selects temporary Markdown body editing.
- links to canonical counterparts use `/docs/?scope=<source_scope>&doc=<doc_id>`.

## Current Interface

The single Docs Viewer toolbar row contains:

- the validated-package selector
- `Build`
- `Assets`
- `Open canonical` when the selected package and document identify a counterpart
- the Markdown source/rendered-mode control
- the document information control

The index panel renders the hierarchy supplied by the validated package. Docs Review does not provide parent or hierarchy editing. The planned Docs Viewer import preflight will map selected package parents to the new target documents without making the review route a hierarchy editor.

`Build` writes a fresh package-local generated preview. Opening an unbuilt package also triggers the required initial build before its index is read.

`Assets` reports which optional package inventories are present. Docs Review does not provide a binary asset editor.

## Validated Package Contract

Packages live outside the repository under:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/<package_id>/
  manifest.json
  source/
    <doc-id>.md
  assets/
    ...
  inventories/
    assets.json
    links.json
    embedded-content.json
  generated/
    index-tree.json
    by-id/
      <doc-id>.json
```

`generated/` may be absent until the first build. Inventory files are optional.

The trusted `manifest.json` must:

- use `schema_version: docs_review_validated_package_v1`
- contain a `package_id` matching the folder name
- use `status: validated`
- identify `source_scope`
- optionally provide `title` and `default_doc_id`

The source contract requires:

- at least one direct `source/*.md` child
- no nested source Markdown or symlinks
- a safe, unique front-matter `doc_id`
- a filename stem matching `doc_id`
- any `default_doc_id` to identify a package document
- a valid package-local hierarchy for building

Data Sharing is responsible for producing this trusted handoff. Invalid folders remain outside the selectable package list and are returned as rejected-package diagnostics.

## Build And Asset Rendering

The review builder uses a synthetic local-external Docs Viewer configuration. It reads only the selected package and writes only that package's `generated/` folder. It does not register the package in scope config or write repository source, normal generated scope output, public assets, or search output for another scope.

Package media and interactive HTML are served only when they are declared in `inventories/assets.json` and resolve to safe files under `assets/`.

Asset inventory records support:

- `kind: media` or `kind: interactive`
- a required `token_path`
- a safe `package_path` under `assets/`

Package-local interactive HTML is rendered in a sandboxed iframe with scripts allowed but without same-origin authority.

## Temporary Source Editing

Source reads return only the Markdown body after front matter plus a SHA-256 revision token.

Source writes require:

- `package_id`
- `doc_id`
- the expected `source_revision`
- `source_body`

The write service:

- verifies package and document containment
- rejects stale revisions
- preserves the existing front matter exactly
- normalizes the submitted Markdown body
- writes atomically inside the package
- rebuilds the package preview
- restores the previous source text if rebuilding fails

`parent_id` updates are rejected. Docs Review cannot edit front matter, create documents, delete documents, or change canonical source.

## Capability And Security Boundary

Review capabilities are independent from `/docs/` management capabilities:

```text
review_packages_list
review_manifest_read
review_asset_inventory_read
review_generated_read
review_source_read
review_source_write
review_build
```

The review capability response always reports these authority exclusions:

```text
canonical_write: false
management: false
publish: false
```

The service remains loopback-only, validates allowed origins, rejects unsafe package/document/path values, forbids symlink traversal, and serves only inventoried package assets.

## Failure Behavior

- A missing or unavailable external workspace disables review capabilities with workspace setup diagnostics.
- A package with an invalid manifest, source set, or package-local hierarchy is rejected rather than partially loaded.
- A missing generated tree or payload is repaired by Build when possible.
- A stale source revision is rejected before writing.
- A source write whose rebuild fails is rolled back.
- A manually deleted package produces an ordinary not-found response.
- No package failure falls back to canonical source or a configured Docs Viewer scope.

## Verification

The `docs-viewer-smoke` profile includes the fixture-backed Docs Review route check. Focused package tests live in:

```text
docs-viewer/tests/python/test_docs_review_packages.py
docs-viewer/tests/smoke/docs_viewer_service_review.py
```

These checks cover validated package discovery, package-root containment, build and generated reads, inventoried assets, source revision/write behavior, parent-update rejection, route boot, rendered/source switching, and canonical comparison without canonical writes.

## Related References

- [Docs Review Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-review)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership)
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Returned Package Review](/docs/?scope=studio&doc=data-sharing-documents-returned-package-review)
- [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)
- [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package)
- [Local Setup Environment](/docs/?scope=studio&doc=local-setup-environment)
