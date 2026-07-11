---
doc_id: site-request-docs-review-workflow
title: Docs Review Workflow
added_date: 2026-07-10
last_updated: 2026-07-11
ui_status: complete
parent_id: change-requests
viewable: true
---
# Docs Review Workflow

## Status

Complete. The validated-package consumer and `/docs-review/` application are implemented, and the live Data Sharing `document-content` Content action now publishes its rendered-derived text projection through the trusted handoff contract.

The preview builder consumes `docs_review_validated_package_v1` and does not depend on how the package was produced. The exact-Markdown, asset-complete `document-full-source` producer continues as the separate [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) request.

Implemented in this slice:

- independent `DOCS_VIEWER_REVIEW_ENABLED` service authority and `/docs-review/` route
- validated external package listing, manifest and inventory reads, source revision checks, builds, generated reads, and inventoried asset reads
- a synthetic `DocsDataBuilder` configuration that writes only package-local `generated/`
- package-aware media URLs and sandboxed package-local interactive HTML
- the returned-package collection provider, package selector, Build and asset-inventory controls, rendered/source modes, temporary parent editing, and canonical comparison link
- Data Sharing validation and timestamped-folder publication for the compact `document-content` projection
- rejected-package diagnostics in the `/docs-review/` empty state
- focused Python, module-boundary, manage-regression, and browser-route verification

The compact producer and fixture-backed complete-package consumer both use `docs_review_validated_package_v1`. The compact projection records `source_projection: rendered_derived_text_only`; it does not claim exact canonical Markdown or an asset-complete round trip.

This request replaces the retired `Docs Review Local App` proposal. Docs Review is a local review route of the existing Docs Viewer application, not a copied viewer application and not a canonical import tool.

## Outcome

Provide an isolated preview and editing workspace for a complete document package returned from an external service:

1. Data Sharing exports every selected document's exact canonical Markdown in one JSONL file, plus referenced media, interactive assets, manifests, and task context.
2. The complete package is sent to an external service such as ChatGPT.
3. The external service may edit Markdown, reorganize hierarchy, and replace or add packaged media and other allowed assets.
4. The returned package is staged and validated by Data Sharing.
5. The validated package is opened in `/docs-review/`.
6. Docs Review builds and previews the returned documents and assets.
7. The user may edit returned Markdown manually and rebuild the preview.
8. Canonical documents may remain open in `/docs/` in another tab for comparison.
9. Importing the reviewed package into canonical source remains manual until a separate Data Sharing import/promotion phase is specified and implemented.

There is no `Promote to canonical` action in this request.

## Decision

Use the existing Docs Viewer application with a distinct local review route and app context:

- route: `/docs-review/`
- app context: `review`
- same local Docs Viewer service process
- shared Docs Viewer boot, shell primitives, tree, router, panel layout, document renderer, source-editor primitives, and CSS
- a thin review entrypoint/composition layer for review-only capabilities
- a returned-package data provider rather than a configured Docs Viewer scope
- focused package-listing, source-read/write, build, generated-read, and asset-inventory services

Do not create a top-level `docs-viewer-review/` application or copy existing Docs Viewer runtime modules into a second frontend.

The distinct route makes temporary package state visible, keeps review URL state separate from configured scope navigation, and prevents the normal `/docs/` management UI from acquiring returned-package conditionals.

## Relationship To Data Sharing

[Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) owns the complete package contract.

Data Sharing owns:

- exporting exact canonical Markdown for all selected documents in one JSONL stream without rendered-HTML round trips
- discovering and copying referenced local media, interactive HTML, scripts, styles, and other supported assets
- producing package, document, asset, link, and embedded-content manifests
- providing external task instructions and field/context descriptions
- JSONL-plus-assets package creation under the external workspace root
- safe returned-package staging, JSONL validation, optional archive extraction, and structural validation
- materializing validated returned JSONL rows into temporary Markdown files for Docs Review
- regenerating trustworthy returned-package inventories from actual returned files
- handing a validated package folder to Docs Review

Docs Review does not reconstruct missing canonical source constructs from JSON and does not own export dependency discovery.

If automated canonical import or promotion is added later, Data Sharing owns it. Data Sharing has the trusted export provenance, returned-package validation, source/asset mapping, and domain-adapter boundary required to plan canonical changes. Docs Review may link to or display the result of such a workflow, but it must not implement the canonical mutation itself.

## Benefits And Risks

Benefits:

- external editing receives the real source and supporting files rather than a lossy rendered projection
- ChatGPT may preserve, replace, or add images and other packaged assets
- tree navigation, rendering, source editing, routing, and later viewer improvements remain shared
- returned files can be inspected safely before any manual canonical import
- removing automatic promotion avoids conflict resolution, lossless source merging, and canonical write authority in v1
- the public viewer remains isolated from local review assets and services

Risks:

- complete packages include a large JSONL corpus plus assets and require explicit dependency, size, and optional archive rules
- returned media and scripts are untrusted input
- package-local asset paths must render without pretending they are canonical/public paths
- the current runtime assumes a binary public/manage context and configured-scope data
- search, recently added, bookmarks, and scope selection currently participate in shared startup
- manual canonical import can still make mistakes, but that risk is outside Docs Review automation

The implementation should address these as explicit provider, capability, workspace, asset-resolution, and sandbox seams. It should not add scattered `review` conditionals to the private app runtime.

## Route And URL Contract

Review URLs use package identity, not scope identity:

```text
/docs-review/?package=<package_id>&doc=<doc_id>
/docs-review/?package=<package_id>&doc=<doc_id>&view=source
```

Rules:

- `package` selects one validated returned package folder.
- `doc` selects one document within the package.
- `view=source` selects returned Markdown source editing.
- absence of `view` selects the rendered document.
- review URLs must not use a synthetic configured scope such as `scope=library-review`.
- browser history and internal review links must preserve `package`.
- the current package id must not be held only in ephemeral JavaScript state.
- links to canonical counterparts use `/docs/?scope=<source_scope>&doc=<doc_id>` and may open in another tab.

The implementation may use a thin review shell or a shared local shell. Shell markup remains limited to route identity, mounts, boot, and asset loading.

## App Context And Capability Model

Docs Viewer should support three explicit app contexts:

| context | route family | data authority | writes |
| --- | --- | --- | --- |
| `public` | `/library/`, `/analysis/`, and other public routes | public generated assets | none |
| `manage` | `/docs/` | configured scopes and management service | canonical management actions |
| `review` | `/docs-review/` | selected returned package | temporary Markdown edits and generated review output only |

Route identity and visible controls do not grant backend authority. The backend capability response remains the source of truth.

Initial review capabilities:

- `review_packages_list`
- `review_manifest_read`
- `review_asset_inventory_read`
- `review_generated_read`
- `review_source_read`
- `review_source_write`
- `review_build`

Review must not receive capabilities for:

- canonical source reads through arbitrary paths
- canonical source writes, import, replacement, or promotion
- canonical delete
- configured scope creation or deletion
- hierarchy drag/drop against canonical source
- publish
- canonical source settings
- public-site writes

## Shared Runtime And Data Provider

Add a data-provider seam to existing Docs Viewer app composition. The provider supplies the selected collection's generated and source behavior without requiring the collection to be a configured scope.

The provider contract should support named methods equivalent to:

```text
readIndex()
readDocument(docId)
readSource(docId)                 optional
writeSource(docId, revision, body) optional
build()                           optional
listCollections()                 optional
selectCollection(id)              optional
readManifest()                    optional
readAssetInventory()              optional
```

The configured-scope provider retains current `/docs/` behavior. The returned-package provider adapts review endpoints and wrapper payloads to the same viewer-facing contracts.

Feature-facing generated reads must continue through `docs-viewer-generated-data-runtime.js` or a provider boundary owned by app composition. Review controllers must not bypass the generated-data owner by importing low-level fetch primitives directly.

Review route features are explicit:

- enabled: package selection, tree, rendered document, source editing, parent editing, Build, asset inventory, canonical counterpart link
- disabled initially: scope selector, search, recently added, bookmarks, reports, public links, canonical management toolbar, package deletion

Startup should skip disabled feature controllers and payload requirements. A missing search or recently-added URL must not force the package to include unused placeholder files.

The review entrypoint may import local source-editor and parent-picker primitives because `/docs-review/` is a local temporary-write route. Public entrypoints must never import review or management assets.

## External Workspace Root Contract

Full packages and generated review output are user-workspace artifacts outside the application repository:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/
  exports/
  import-staging/
  import-preview/
  meta/
```

The repo-local `var/analytics/data-sharing/...` contract has been retired. Docs Review uses the external Data Sharing workspace for returned packages and preview sessions.

Rules:

- one shared workspace-root resolver owns `DOTLINEFORM_PROJECTS_BASE_DIR` validation and marker-path projection
- Data Sharing and Docs Review receive resolved workflow roots explicitly; they do not derive artifact roots from `repo_root`
- config and metadata store artifact-relative or marker-rooted paths, never user-specific absolute paths
- a missing, invalid, unreadable, or unwritable workspace root disables affected capabilities with actionable setup guidance
- there is no fallback read or duplicate write to the retired repo-local path
- path traversal, symlink, filename, suffix, archive, and containment checks use the resolved external workflow root
- canonical Docs Viewer source and tracked config remain repository-owned

## Returned Package Folder Contract

Docs Review consumes a Data Sharing-validated folder such as:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/<package_id>/
  manifest.json
  context/
    instructions.md
    package-context.json
  source/
    <doc-id>.md
  assets/
    media/
    interactive/
  inventories/
    assets.json
    links.json
    embedded-content.json
  generated/
    index-tree.json
    by-id/
      <doc-id>.json
```

The Data Sharing request owns the exact portable schema and asset layout. Docs Review relies only on a validated package record and explicit resolved paths.

The `source/*.md` files in this folder are a temporary review projection materialized by Data Sharing from validated returned `documents.jsonl` rows. They are not the external transport format and are not canonical source.

Package rules:

- package ids are safe single path segments derived from trusted export metadata
- package folders are never added to `docs-viewer/config/scopes/docs_scopes.json`
- package folders are never published
- manual deletion is valid
- loading a deleted package reports an ordinary not-found state
- opening or editing a package does not change the active configured `/docs/` scope
- timestamped package folders are immutable; publishing the same package id again is rejected
- package source and assets are untrusted until Data Sharing validation succeeds

## Review Build

Build reads the selected package's exact Markdown and asset inventory and writes only its `generated/` folder.

Use `DocsDataBuilder` as a library with a synthetic configuration and a package-aware asset resolver. Do not invoke the CLI, add the package to configured scope data, or use normal scope rebuild orchestration.

Build must:

- validate the selected package and require at least one source Markdown file
- parse and validate every review document
- resolve package-local media and interactive assets through the manifest contract
- keep returned scripts and interactive HTML isolated through the existing sandbox model and any package-specific restrictions
- generate the tree and per-document rendered payloads
- preserve package identity in review navigation
- return document/asset counts, warnings, generated paths, and a concise summary
- refresh the current tree and document after success

The provider owns index and document reads. It must not depend on generated `content_url` values resolving as public static paths under the external workspace root.

## Temporary Source Editing

The review source editor writes only Markdown under the selected returned package.

It may edit the complete returned source, including text around media, links, references, and embedded-content tokens. Because no automated canonical promotion exists, Docs Review does not need a protected-placeholder merge model.

Source writes still require:

- safe package and document ids
- expected review-source revision
- containment inside the package source root
- atomic writes
- ordinary parse/build validation
- no canonical path supplied by the browser

`parent_id` should be editable using existing parent-picker/metadata primitives where practical. The package may contain new chapter documents and new parent relationships because preview does not write canonical source.

Docs Review does not provide an asset editor in v1. Replacing or adding files may be done in the package workspace or by the external service; the asset inventory and build results make those changes visible.

## Canonical Comparison And Manual Handoff

Docs Review does not provide a comprehensive diff or merge interface.

The intended comparison workflow is:

- keep the reviewed document open in `/docs-review/`
- open the canonical counterpart in `/docs/` in another tab
- compare visually as needed

There is no Docs Review endpoint or UI action that writes canonical source. After review, the user manually imports, copies, or commits the desired Markdown and assets until a separately specified Data Sharing import/promotion workflow exists.

The reviewed package should retain source scope, original source path, original file hashes, and canonical counterpart URLs so that a later manual or separately specified import workflow has useful provenance.

## Suggested Backend Surface

Exact route names may be refined during implementation:

```text
GET  /docs-review/packages
GET  /docs-review/packages/manifest?package_id=<package_id>
GET  /docs-review/packages/assets?package_id=<package_id>
GET  /docs-review/packages/index-tree?package_id=<package_id>
GET  /docs-review/packages/payload?package_id=<package_id>&doc_id=<doc_id>
GET  /docs-review/packages/source?package_id=<package_id>&doc_id=<doc_id>
POST /docs-review/packages/build
POST /docs-review/packages/source
```

Source writes require `package_id`, `doc_id`, expected review revision, and the edited body or explicit metadata change. No endpoint accepts an arbitrary filesystem path or caller-supplied canonical target.

## Proposed Repo Ownership

Review-specific code stays inside the existing Docs Viewer area:

```text
docs-viewer/
  shell/
    docs-viewer-review.html
  runtime/js/review/
    docs-viewer-review.js
    docs-viewer-review-controller.js
  services/
    docs_review_packages.py
    docs_review_build.py
    docs_review_source.py
```

Shared changes belong with shared owners:

```text
docs-viewer/runtime/js/shared/
  docs-viewer-app-context.js
  docs-viewer-app-composition.js
  docs-viewer-app-runtime.js
  docs-viewer-generated-data-runtime.js
  docs-viewer-route-config.js
  docs-viewer-view-context.js
```

Data Sharing full-package export/intake code remains under `data-sharing/` and its Documents adapter. Review modules must not be imported by the public entrypoint.

## Implementation Steps

### 1. Complete Prerequisite Contracts

- complete the limited Docs Viewer app-context, provider, route-feature, and view/mode/control refactors — complete
- complete the external Data Sharing/review workspace-root slice — complete
- approve the validated-package consumer contract — complete; full export/intake producer continues independently
- retire or isolate any stub review-session behavior that assumes repo-local, rendered-content source folders

### 2. Complete Returned-Package Services — complete

- list validated package folders
- read manifests and inventories
- read/write package Markdown with revision checks
- report missing, malformed, or manually deleted packages cleanly
- expose only package-rooted paths and data

### 3. Implement Review Builds — complete for the validated consumer contract

- construct a synthetic builder configuration from the validated manifest
- resolve package-local asset mappings
- write generated output inside the selected package
- expose generated index and payload reads
- verify interactive content remains sandboxed

### 4. Add Review App Context And Provider Seam — complete

- add explicit `review` context without granting management
- implement the returned-package provider
- make startup features explicit
- preserve public/manage behavior and module-graph isolation

### 5. Serve `/docs-review/` — complete

- add the local shell/route
- add the review entrypoint and controller
- implement package selection, tree navigation, rendered/source modes, Build, asset inventory, and canonical counterpart links

### 6. Add Temporary Markdown And Parent Editing — complete

- reuse source-editor interaction primitives
- add package-specific source endpoints
- reuse parent-selection primitives where appropriate
- rebuild and refresh after edits
- keep every write inside the selected package

### 7. Focused Verification — complete for fixture-backed Docs Review

- pure app-context and provider tests
- public/manage/review import-boundary tests
- external package-root path and traversal tests
- package manifest and asset-resolution tests
- package source revision/write tests
- package build tests containing media, links, semantic references, interactive HTML, and new chapter nodes
- route/service API tests
- one focused browser smoke for review route boot and package switching

### 8. Documentation And Closeout — complete for the Docs Review consumer

- update runtime boundary, module ownership, source organisation, Data Sharing, and user/operator guidance
- record the manual canonical handoff explicitly
- remove retired prototype docs and paths rather than keeping compatibility aliases

## Acceptance Criteria

The initial Docs Review release is complete when:

- `/docs-review/` is served by the existing Docs Viewer service
- the route uses shared runtime/rendering/source-editing primitives without copied viewer modules
- validated complete returned packages can be selected
- exact returned Markdown, hierarchy, media, and supported embedded assets build successfully
- rendered/source views and manual Markdown editing work entirely inside the external package workspace
- package-local interactive content remains sandboxed
- public entrypoints do not import review or management modules
- canonical counterpart links work for existing documents
- no Docs Review capability, route, or service writes canonical repository source
- the manual canonical handoff is documented

## Additional Handoff Completion — 2026-07-11

The follow-up producer/consumer gap is closed without accepting the obsolete schema in Docs Review.

- Data Sharing materializes the complete `document-content` source set in memory, strictly parses the resulting front matter, validates safe filename/`doc_id` agreement, unique identities, package-local hierarchy, and hierarchy cycles, then writes the timestamped package folder directly. Parents outside a partial compact selection are rooted in the temporary projection and preserved as validation warnings.
- The written manifest uses `docs_review_validated_package_v1`, a matching `package_id`, `status: validated`, `source_scope`, `default_doc_id`, trusted export provenance, and validation diagnostics.
- The manifest records `source_projection: rendered_derived_text_only`. Exact `canonical_markdown`, binary assets, dependency inventories, and full returned-package validation remain owned by `document-full-source`.
- Repeating Content for the same metadata-derived timestamp is rejected; timestamped package folders are not replaced.
- When no valid package is available, `/docs-review/` now includes the package-list rejection diagnostics in its empty-state error.
- The returned-package provider normalizes the nested package index through the shared tree-payload adapter before handing it to the app runtime, so nested review documents and expansion controls appear in the Docs Review index.
- Focused tests cover row/materialization rejection, partial-selection parent projection, trusted publication, immutable timestamp conflicts, package discovery, Build, generated payload reads, and rejection diagnostics.
- The live staged Studio package was republished with the trusted manifest: six documents, one external-parent warning, no errors. `/docs-review/` listed it, Build emitted six package-local payloads, and rendered/source reads succeeded without repository source or public-asset writes.

## Non-Goals

- implementing automatic promotion, import, replacement, or commit inside Docs Review; any future automation belongs to Data Sharing
- line-by-line diff, conflict resolution, or merge UI
- automatic Git commit or push
- making returned packages configured Docs Viewer scopes
- public deployment of `/docs-review/`
- editing binary media inside Docs Review
- silently downloading remote assets during package export
- retaining repo-local `var/` as a fallback workspace
