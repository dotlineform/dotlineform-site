---
doc_id: site-request-docs-viewer-external-asset-collections
title: Docs Viewer External Asset Collections
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: draft
parent_id: change-requests
---
# Docs Viewer External Asset Collections

Status: proposed

## Summary

Add an optional external asset collection to local Docs Viewer scopes.

The collection gives a scope a deterministic files-and-media root outside the repository while its Markdown remains in the scope's existing canonical source root. Docs Viewer should index that collection, serve its files through a confined local route, and expose the inventory through one report-backed document. Files do not become Docs Viewer documents merely because they are present in the collection.

This should be a formal New Scope capability and a lifecycle action that can be added to an existing local scope. Processing is the first retrofit proving case. The larger I Ching project is the scale test once the basic contract is working.

## Why This Is Needed

Docs Import currently gives each standalone image or downloadable file a wrapper Markdown document. That is useful when an individual attachment is intentionally part of the document tree, but it is the wrong model for a substantial project asset collection.

Processing already has source sketches, libraries, saved slider configurations, ZIP archives, spreadsheets, images, and recovered notes with different ownership needs:

- Markdown belongs in `docs-viewer/source/processing/` and remains commit-worthy.
- Small document attachments can continue to live in `docs-viewer/source/processing/media/`.
- Project files that are large, numerous, recovered, or independently useful should not be committed merely so Docs Viewer can list them.
- An inventory is useful, but one generated wrapper document per file would make the index tree worse.

The I Ching project adds roughly 150 MB of files and images. Its byte size is not itself the main risk; file count, directory depth, formats, and refresh time will show whether the initial index remains suitably simple.

## Goals

- make external asset storage an explicit optional capability of local scopes
- keep canonical Markdown in the scope's existing source root
- derive one predictable external root instead of storing arbitrary absolute paths
- let existing local scopes add the capability through preview/apply lifecycle behavior
- show assets in a read-only Docs Viewer report without creating a document per asset
- preserve nested project folder structure
- provide safe local links for opening or downloading indexed files
- distinguish external assets from repo-managed Docs Import attachments
- keep external user files outside scope deletion ownership
- reuse the existing report system and lifecycle service boundaries
- identify and resolve pressure on current media, manifest, rename, and delete behavior before exposing the feature

## Non-Goals

- treating the external collection as a second Markdown source root
- importing every asset into the Docs Viewer document tree
- automatically moving existing repo-managed attachments
- making external asset collections available on public read-only routes
- R2 publication or remote synchronization
- content indexing, OCR, EXIF extraction, archive expansion, or spreadsheet parsing
- thumbnails or a general digital asset manager in the first implementation
- asset editing, renaming, moving, or deletion from Docs Viewer
- arbitrary user-selected absolute paths per scope
- a new plugin, action, or asset registry framework
- background-job machinery before a real scan demonstrates the need

## Core Contract

### Location

An enabled scope uses the derived root:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media/<scope>/
```

For Processing this is:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media/processing/
```

The checked-in scope config stores only capability state. It must not store the resolved user-specific absolute path.

Suggested scope config:

```json
{
  "external_asset_collection": {
    "enabled": true,
    "report_doc_id": "processing-assets"
  }
}
```

The root resolver should use the same workspace marker and confinement rules as other external Docs Viewer paths. Enabling the capability is blocked when `DOTLINEFORM_PROJECTS_BASE_DIR` is unset or the configured Docs Viewer workspace is unavailable.

### Document And Asset Ownership

The scope's Markdown source location does not change:

- a local tracked scope keeps Markdown under `docs-viewer/source/<scope>/`
- an external local scope keeps Markdown under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/<scope>/`
- the external asset collection always uses the derived media root above

Markdown found inside the asset collection is an asset for inventory purposes. It is not loaded as a scope document. A file becomes a document only through the normal source or import workflow.

Existing repo-managed attachments remain under `docs-viewer/source/<scope>/media/` and continue to use `/docs/media/<scope>/...`. They do not move when this capability is enabled.

### Relationship To Existing External Media

`local_external` scopes already use `import_media_storage.storage_mode: external_assets`, with Docs Import materializing attachments under the same derived media root. The new capability must not introduce another storage mode or another physical root.

External document storage and an external asset collection are independent choices:

- `local_external` means the scope's Markdown source and generated data live outside the repository.
- `external_asset_collection` means Docs Viewer recursively indexes and reports a project-file collection.

A `local_external` scope may contain only Markdown and ordinary imported attachments and therefore need no asset collection. Conversely, a project such as I Ching may use an external scope and still benefit from indexing a larger collection of images and files.

The collection remains an explicit opt-in for both local scope types. It is not enabled merely because a scope is `local_external`.

Instead, it adds collection behavior over that root:

- recursive nested-path inventory
- a report-backed view
- a nested-path local asset route
- explicit lifecycle association and preservation policy

The current import route remains valid for flat, classed Docs Import media:

```text
/docs/media/<scope>/<img-or-files>/<filename>
```

External collection links use a separate route so current media semantics do not have to become ambiguous:

```text
/docs/assets/<scope>/<relative-path>
```

Both routes may refer to files beneath the same physical root for an external local scope. The asset route is available only when the collection capability is enabled.

## Scope Lifecycle

### New Scope

The New Scope flow should offer an `External asset collection` option for:

- Local tracked
- External local

It should not be offered for Public read-only.

The option should initially be off for both eligible scope types so collection indexing is always intentional. For an external local scope, selecting it enables indexing and reporting over the root already implied by its media storage. It does not create a second media destination.

Create preview should include:

- the derived external asset root
- the scope config capability record
- the manifest association
- the report source document
- the resulting management/report URL
- any filesystem or environment blockers

Create apply should create the asset root if absent, write the config and report document, record the association, and run the normal scope rebuild.

### Existing Scope Retrofit

An eligible existing local scope should expose `Add external asset collection...` through the scope lifecycle actions.

This is not an ordinary Settings field. Enabling it creates a directory and source document, changes scope config and manifest state, and requires a rebuild. It should therefore have its own preview/apply operation rather than expanding the guarded source-config settings allowlist.

A proposed service boundary is:

- `POST /docs/scopes/assets/enable-preview`
- `POST /docs/scopes/assets/enable-apply`

The precise endpoint spelling may change during Slice 0, but preview must remain write-free and apply must require explicit confirmation.

The first retrofit should enable the capability for Processing and create a report document such as `processing-assets.md` under its existing source root.

### Disable And Removal

The first release does not require a disable action. The contract must nevertheless make later removal safe:

- disabling a collection must never delete external files
- deleting its report document is not implied unless that document is still lifecycle-owned and the deletion is separately confirmed
- removing the capability should make the asset route unavailable after config apply
- the now-unassociated external folder should be reported clearly to the user

### Manifest Ownership And Delete Safety

The external asset root is associated with the scope but is user-owned data. It is not a lifecycle-owned source or generated root.

The manifest needs an explicit representation for that distinction. Do not add the asset root as an ordinary deletable `files` record and rely on callers remembering an exception. A focused association record should be able to express at least:

- derived path
- external location
- capability id
- ownership: user data
- delete policy: preserve

Scope delete preview must state that the external asset collection will be preserved. Scope delete apply must remove only config, lifecycle-owned report/source records, and generated state already covered by the lifecycle plan; it must leave the collection untouched.

### Rename Safety

External-local scope rename currently moves an existing media root along with source and generated roots. That behavior predates user-owned asset collections and is the main lifecycle pressure point for this request.

Before the capability is exposed, rename must distinguish import-managed media from an enabled external asset collection:

- an absent or empty lifecycle-created root may move with the scope
- a populated user asset collection must not move silently
- the first implementation may block rename with a clear explanation rather than implement a separate relocation workflow
- any later relocation must have its own preview, explicit confirmation, collision checks, and failure-safe semantics

The design must not claim that a path is both derived from the current scope id and preserved across rename without defining how that mapping remains resolvable.

## Asset Index

### Initial Record

The initial inventory should expose only inexpensive filesystem metadata:

- relative path
- name
- folder or file kind
- extension or broad type
- byte size for files
- modified time
- reference state: referenced, unreferenced, or missing reference

Absolute paths must not be returned to the browser. Folder records may be included when they help preserve the project hierarchy.

Reference state should correlate source Markdown links that use either the external asset route or the existing local media route. Missing references belong in the report even when no corresponding file record exists.

Image dimensions, hashes, previews, metadata extraction, and content indexing are deferred until they answer a demonstrated need.

### Scan Behavior

The first implementation should scan on report load and explicit refresh through the local service. It should not write a committed or authoritative asset index.

The scan should:

- remain confined to the derived scope root
- preserve nested relative paths
- not follow symlinks
- skip hidden/system noise such as `.DS_Store`
- return warnings for unreadable or unsupported entries without failing the complete inventory
- report total files, folders, and bytes with elapsed scan time

Processing should establish the behavior. The I Ching collection should then test realistic file count, depth, and response time. Add caching or asynchronous work only if that evidence shows a synchronous metadata scan is not responsive enough.

## Report

Add one local-only `scope_assets` report through the existing report metadata registry and executable loader allowlist.

An enabled scope gets a normal source document with front matter equivalent to:

```yaml
doc_id: processing-assets
title: Assets
parent_id: processing
viewer_report: scope_assets
viewer_report_scope: processing
viewer_report_access: local
```

The report should initially provide:

- summary counts and scan time
- hierarchical or path-sorted asset rows
- filename/path, type, size, modified time, and reference state
- open/download and copy-link actions where the file is safely servable
- an explicit Refresh action
- clear empty, unavailable, partial-warning, and missing-reference states

This reuses the report system. `scope_assets` is report metadata and an allowlisted report implementation; it is not a new general asset registry.

## Local Asset Route And Safety

`/docs/assets/<scope>/<relative-path>` must remain a loopback-service route. It must not be projected into public browser config or static route shells.

The service must:

- require a configured local scope with the collection enabled
- resolve the derived root on the server
- reject absolute paths, traversal, malformed encoding, and symlink escape
- support nested relative paths
- set `X-Content-Type-Options: nosniff`
- serve safe image/file types with an appropriate MIME type
- force download for executable, interactive, unknown, or otherwise unsafe inline types
- never execute or inline ordinary HTML as an active local page

The report should list a file even when policy requires it to download rather than display inline.

## Configuration And Capability Projection

There are three deliberately separate roles:

- scope config records that a scope has enabled the collection and names its report document
- `GET /capabilities` advertises whether the running local service supports collection lifecycle, indexing, and serving, plus the enabled state for each scope
- the existing report registry describes the `scope_assets` report presentation

This does not require another registry. The filesystem inventory is runtime data, not configuration.

The browser must use service-projected capability state rather than infer support from scope type or the presence of a folder.

## Existing System Pressure Points

These are prerequisite design checks, not invitations to broad refactoring:

1. `docs_media_storage.py` currently ties external media roots to `local_external` import storage. The derived-root helper needs a scope-independent asset-collection boundary without weakening the import rules.
2. `/docs/media/` currently understands classed `img|files` media and flat filenames. Nested external assets need the separate confined route rather than a silent expansion of that contract.
3. `docs_scope_rename.py` currently moves the media root for external-local scopes. Enabled, populated collections require an explicit block or relocation policy before launch.
4. The scope manifest currently models lifecycle-owned files. User-owned associated data must not be squeezed into the same deletable record shape.
5. Scope delete and capability projection must consume the server-owned ownership decision, not reproduce path heuristics in the UI.
6. Reports already provide the desired read-only document surface. Asset-specific filtering and rendering belong in a report module, not the shared document controller.
7. Docs Import should continue to own import plans and wrapper-document decisions. This capability must not be smuggled into the importer as a second bulk-import workflow.

If one of these modules cannot accept its narrow responsibility cleanly, pause that slice and record the ownership problem before refactoring. A prerequisite refactor should leave current behavior intact and should not vertically implement the later report or UI slices as a side effect.

## Implementation Slices

### Slice 0 — Capability And Lifecycle Prerequisite

- define the scope config and service capability shapes
- add a shared derived external asset-root resolver
- define manifest association and preservation semantics
- reconcile external-local rename behavior with populated collections
- define enable preview/apply plans for an existing local scope
- add focused service tests for config validation, containment, delete preservation, and rename blocking

Exit condition: Processing can be previewed for enablement with an exact safe plan, but no asset index/report UI needs to exist yet.

### Slice 1 — New Scope And Retrofit Actions

- add the New Scope option for both local publishing modes
- add `Add external asset collection...` for eligible existing scopes
- implement confirmed enable apply
- create the derived folder, config/manifest records, and report source document
- rebuild and navigate to the resulting report document

Exit condition: a new or existing local scope can acquire the capability through the lifecycle UI without hand-editing config.

### Slice 2 — Index And Local File Route

- implement the confined metadata index endpoint
- implement the nested local asset route
- add reference correlation and missing-reference records
- cover traversal, symlink, unsafe-inline, partial-read, and nested-path behavior

Exit condition: Processing assets can be inventoried and safely opened or downloaded through the local service.

### Slice 3 — Report

- register and allowlist `scope_assets`
- add the local report loader and rendering module
- provide summary, path hierarchy, reference state, file actions, and explicit refresh
- keep report state and warnings contained within the report boundary

Exit condition: the lifecycle-created Processing report gives a useful inventory without wrapper docs.

### Slice 4 — Proving Cases And Closeout

- organize the Processing external asset collection and verify its real links
- test I Ching as the larger file-count/size case
- decide from measurements whether caching, exclusions, dimensions, or preview generation deserve follow-on work
- update durable docs and absorb stable decisions from this request
- create a child execution tracker only if implementation history is too detailed for this parent request

Exit condition: the capability is proven on both shapes of project and stable behavior is documented outside this request.

## Initial Open Questions

1. Should the first report show folders as rows or derive hierarchy only from file paths?
2. Which hidden files and project-generated/cache folders should be excluded beyond platform noise? Start with a very small built-in exclusion set and learn from Processing.
3. Should reference correlation recognize only `/docs/assets/` and `/docs/media/` links, or also a future compact Markdown asset token? No new token is required initially.
4. What scan time is acceptable before the report needs a cache or asynchronous refresh? Measure by file count and elapsed time rather than the collection's total bytes.
5. Should a later collection-disable action preserve the report document as an explanatory stub or offer its deletion as a separate confirmed choice?
6. Does I Ching become its own Docs Viewer scope or remain a collection attached to another scope? That project-organization decision is outside the capability contract.

## Acceptance Criteria

- New Scope offers the capability only for local tracked and external local scopes.
- An existing eligible local scope can enable it through a write-free preview and confirmed apply.
- Processing Markdown remains under `docs-viewer/source/processing/`.
- Processing external assets resolve under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media/processing/` without an absolute config path.
- Repo-managed Processing attachments remain valid and unmoved.
- The report lists nested assets without creating one Markdown document per file.
- Asset records expose relative paths only.
- Nested local links reject traversal and symlink escape and do not execute active content inline.
- Public routes do not expose the asset index or local asset service.
- Scope deletion demonstrably preserves external asset files.
- A populated enabled asset collection is not silently moved by scope rename.
- Processing works as the initial retrofit and I Ching supplies a measured scale result before performance machinery is added.

## Documentation Impact

This request owns the proposed behavior until implementation makes it current.

Closeout should update:

- [New Scopes Builder](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) for the create and retrofit lifecycle behavior
- [Scope Lifecycle Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-scope-lifecycle) for preview/apply, ownership, rename, and delete semantics
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling) for the distinction between imported attachments and external collections
- [Reports](/docs/?scope=studio&doc=docs-viewer-reports) for `scope_assets`
- [Source Config Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-config) only to preserve the boundary that lifecycle-installed capabilities are not generic settings
- [JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) and [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) for the new lifecycle/report owners
- the scope config and manifest contract documentation for capability and association fields
- Processing setup documentation for the final external asset layout and inventory link

Do not update these durable docs ahead of implementation except where Slice 0 exposes an incorrect current statement that must be corrected for safety.
