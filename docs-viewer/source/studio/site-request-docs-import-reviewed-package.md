---
doc_id: site-request-docs-import-reviewed-package
title: Docs Import Reviewed Package
added_date: 2026-07-11
last_updated: 2026-07-12
ui_status: proposed
summary: Move Docs Import to the W0-resolved shared drop-zone, import immutable staged Data Sharing JSONL as a collection, and retain a persistent read-only review projection.
parent_id: change-requests
viewable: true
---
# Docs Import Reviewed Package

## Status

Proposed follow-on to [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) and the current [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) implementation.

The current workflow already proves the persistent Docs Review package and renderer. This request simplifies the remaining import path and removes source editing from Docs Review.

## Decision

Treat the staged Data Sharing JSON/JSONL file as another Docs Import source format.

As a prerequisite, move every Docs Viewer import format to the existing shared drop-zone:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

This folder is not exclusive to the Data Sharing application. It is the consistent user-facing import drop-zone. Which application or workflow uses a file depends on the file format, schema, trusted metadata, and the action the user invokes.

Keep the persistent preview package because JSONL is not convenient for a person to review and the review and import decisions may happen at different times. The preview package is a durable, read-only view projection; it is not the import source.

```text
immutable staged JSONL
  -> persistent read-only Docs Review projection
     -> import-preview/<package_id>/source/*.md
     -> import-preview/<package_id>/generated/...

immutable staged JSONL
  -> Docs Viewer collection import
     -> create, overwrite, or skip
     -> configured-scope Markdown
```

The staged file remains the authoritative returned package. Docs Import reads that file directly when the user later chooses to import it.

## Artifact Roles

| Artifact | Role | Write authority |
| --- | --- | --- |
| `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` | shared user drop-zone for all supported imports | user placement and Data Sharing staging producers |
| `<timestamped-file>.jsonl` inside that drop-zone | immutable returned package and collection import input | Data Sharing staging contract |
| `import-preview/<package_id>/manifest.json` | trusted association between the staged package and its view projection | preview producer only |
| `import-preview/<package_id>/source/*.md` | durable, human-readable, read-only build input | preview producer only |
| `import-preview/<package_id>/generated/` | durable Docs Review tree and document payloads | package-local builder only |
| configured Docs Viewer scope source | accepted import output | managed Docs Import only |

The preview `source/*.md` files must never become an alternative import authority. They exist to reuse the Docs Viewer builder and make the projection inspectable.

## Shared Import Drop-Zone

Retire Docs Viewer’s repo-local `var/docs/import-staging/` contract. HTML, Markdown, Markdown packages, text, SVG, images, downloadable files, interactive HTML companions, and supported Data Sharing JSON/JSONL collections should all be listed and resolved from:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

The folder name reflects the existing workspace layout, not exclusive application ownership.

- A user can place an ordinary HTML, Markdown, media, or package source there for Docs Import.
- A user can place a returned JSON/JSONL file there for the appropriate Data Sharing validation/review workflow.
- Docs Import may list any file or direct-child package supported by its format registry.
- Data Sharing should list only files that satisfy its metadata and adapter contracts.
- Supported Data Sharing document JSON/JSONL can later be consumed by both the review workflow and Docs Import, each through its named action.
- Files without an applicable handler remain ordinary drop-zone files; their presence does not assign them to an application.

Do not copy files between a Data Sharing staging root and a Docs Viewer staging root. There is one configured root.

### Reuse The W0 Workspace Adapter

Use the external workspace adapter delivered by W0 of [Docs Viewer Architecture Assessment And Refactor Roadmap](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap):

```python
from services.paths import configured_workspace_paths, marker_path

staging_root = configured_workspace_paths(repo_root).import_staging
```

This is the same `data-sharing/services/paths.py` contract already used by Docs Review to resolve `import_preview`.

Docs Import must:

- resolve the root through `configured_workspace_paths(repo_root).import_staging`
- honor the editable marker-rooted path in `data-sharing/config/adapters.json`
- expose `$DOTLINEFORM_PROJECTS_BASE_DIR/...` marker paths through `marker_path()` rather than absolute user paths
- use the W0 workspace status/error contract when the root is missing, invalid, unreadable, or unwritable
- disable only import-related capabilities when the external workspace is unavailable
- preserve filename, direct-child package, traversal, symlink, suffix, and containment checks against the resolved external root
- use isolated temporary project-base roots in tests

Do not add a second environment-variable reader, another staging-root setting, a Docs-specific path adapter, or a fallback to `var/docs/import-staging/`.

### Import Service Changes

The current import implementation derives paths from `STAGING_REL_DIR` and `repo_root`. Replace that assumption with an explicit resolved staging root shared across:

- staged source listing
- primary-source resolution
- Markdown package discovery and containment
- interactive HTML companion discovery
- inline raster output for `staging_manual`
- converted Markdown-package images and copied attachments
- preview/result path projection

External source paths cannot be displayed with repo-relative helpers. API results and activity diagnostics should use marker-rooted paths or artifact-relative filenames.

## Targeted Import Refactoring Boundary

The current importer is already modular enough at the service level. This request does not authorize a general import architecture rewrite.

Retain the existing layers:

- `docs_management_import_service.py` as the thin dependency adapter
- `docs_import_source_service.py` as the single-document workflow orchestrator
- `docs_import_preview.py` as the current format dispatcher and internal conversion/validation contract
- `docs_import_common.py` as the suffix-to-`source_format` metadata registry
- focused Markdown-package, media, interactive-asset, source-formatting, and write/rebuild helpers

Only four targeted changes are required.

### 1. Externalize The Existing Staging Root

Replace `STAGING_REL_DIR` and `repo_root` joins with an explicit W0-resolved staging root. This changes path authority, not format orchestration.

### 2. Add Schema-Aware JSON/JSONL Detection

Keep suffix detection for existing formats. Before generic `.json` or `.jsonl` file-media fallback, inspect supported Data Sharing header and trusted metadata contracts and select a new collection `source_format` when they match.

### 3. Add A Collection Orchestrator

Keep `handle_import_source()` for the existing one-source-to-one-document flow. Add a focused collection workflow for the one-JSONL-to-many-document case. A suitable focused module is `docs_import_data_sharing_documents.py`; exact names can follow current service conventions.

The collection workflow owns:

- record selection
- create, overwrite, or skip decisions
- cross-record identity, parent, link, and media mapping
- batch result and failure reporting

It should call shared lower-level import services rather than invoke the single-document HTTP/service entrypoint once per record.

### 4. Extract Reusable Per-Document Plan And Apply Helpers

Extract only the common document operation currently embedded in `handle_import_source()`:

- collision lookup and action validation
- create/overwrite source formatting
- inline and package media materialization
- target-path writes
- rebuild follow-through
- logging and result shaping

The existing single-document orchestrator should use the extracted helpers too. This proves that ordinary import behavior remains on the same path while allowing the collection orchestrator to plan and apply several records.

### Explicitly Not Required

- no plugin framework or open-ended handler loader
- no conversion of `SourceImporter` into a callable-handler registry
- no wholesale replacement of the `generate_import_preview()` dispatcher
- no requirement to move every format function into a separate module
- no rewrite of existing HTML, Markdown, text, SVG, image, file, or Markdown-package behavior
- no change to existing single-document create/overwrite semantics beyond the staging-root migration

The implementation should prefer the smallest extraction that supports collection plans. Broader cleanup belongs in a separate request with independent evidence.

## Immutable Package Identity

A staged return and its preview folder form one immutable pair identified by export metadata and the timestamped package identity.

- Normal workflow never edits or replaces a staged JSONL file.
- A later return produces a new timestamped staged file and a new preview folder.
- The older pair does not become stale when a newer pair exists.
- Preview source is read-only and therefore cannot diverge through Docs Review edits.
- If the staged file is deleted, its persistent preview may remain viewable but import from that package is unavailable.
- A staged-file hash may be retained for provenance or corruption detection; it is not a lifecycle revision or staleness mechanism.

Do not add refresh polling, source revisions, stale-preview states, or preview/apply drift logic for the staged file.

## Why The Preview Package Remains

Ordinary staged Markdown and HTML are already human-readable outside Docs Viewer, so the current import flow can convert and save them without a separate user-facing content preview.

JSONL is different. It is an efficient multi-document transport but a poor reading surface. Docs Review provides the readable hierarchy, document renderer, media projection, and canonical comparison needed before the user decides whether to import.

That decision may happen much later. Materialize and build the preview once, then serve the persistent package-local generated tree on every later view. Do not parse and rebuild the complete JSONL each time a document is opened.

## Docs Review Changes

Docs Review becomes a read-only package viewer.

Remove:

- source mode and its toolbar control
- source reads and writes
- revision tokens and stale-revision handling
- Markdown save/rebuild behavior
- `review_source_read` and `review_source_write` capabilities
- source-editing endpoints, service methods, browser modules, and tests

Retain:

- validated package listing and selection
- the persistent package-local hierarchy and generated document reads
- rendered document navigation
- inventoried asset rendering
- canonical counterpart links
- package information and validation diagnostics
- initial package build or explicit repair when generated output is absent

Ordinary viewing must read the existing package-local generated output. Building is not part of every view request.

The preview `source/*.md` files should be treated like other generated workspace artifacts: inspectable and reproducible, but not editable through the product.

## Data Sharing JSONL Import Format

Register a schema-aware document-collection format before the current generic `.json`/`.jsonl` downloadable-file fallback. It uses the same resolved drop-zone as every other Docs Import format.

Extension alone is insufficient because Docs Import already accepts JSON and JSONL as ordinary downloadable files. Detection must inspect the package header and trusted metadata, for example:

- `record_type: data_sharing_header`
- supported package `schema_version`
- supported documents profile/import type
- matching trusted `export_id` metadata

If the staged file does not match a supported document-collection schema, retain the existing generic file-import behavior.

The collection importer should support both the compact returned-document format and the full-source format only where their field contracts are explicitly mapped. It must not infer a document package merely from arbitrary row fields.

## Future Standalone JSON/JSONL Collections

Data Sharing is the first collection wrapper, not a permanent prerequisite for collection import.

A future ChatGPT or other external workflow may create a new document collection directly as JSON or JSONL without receiving an exported Data Sharing seed. Docs Viewer should be able to support such a file through a separately declared standalone collection schema, for example `docs_import_collection_v1`.

That future format is not implemented by this request. The current design must nevertheless avoid assumptions that would prevent it:

- the shared normalized record must not require `export_id`, original canonical hashes, a Data Sharing profile, or trusted export metadata
- Data Sharing provenance belongs to the Data Sharing collection adapter, not the core Docs Import record
- a future standalone adapter can validate its own explicit schema and emit the same normalized records
- arbitrary JSON/JSONL must continue to use the generic downloadable-file fallback unless it declares a supported collection schema
- standalone collections use the same external import drop-zone and the same create/overwrite/skip workflow
- the wrapper may contain Markdown, HTML, or plain-text document bodies through an explicit `content_format`

Because JSONL is not convenient to read, a future standalone collection may also use the persistent read-only Docs Review projection. Its preview identity and validation contract would be defined by that collection schema rather than fabricated Data Sharing provenance.

## Collection Adapters And Normalized Import Content

Use wrapper-specific adapters that emit one shared Docs Import content contract.

```text
ordinary .md/.html/.txt reader ───────────────┐
Data Sharing JSON/JSONL adapter ──────────────┼─> ImportContent record(s)
future standalone collection adapter ─────────┘
                                                  -> body-format conversion
                                                  -> persistent review materializer when applicable
                                                  -> configured-scope import planning/apply
```

The generic `ImportContent` record should carry at least:

- source kind and stable source/record identity
- optional adapter-specific provenance
- proposed `doc_id`
- title
- body content
- `content_format`: `markdown`, `html`, or `plain_text`
- allowed front matter
- `parent_id`
- link and asset information
- source format/profile diagnostics

Body-format conversion then reuses the normal Docs Import paths:

- `markdown` uses the Markdown normalization/validation path
- `html` uses the HTML-to-Markdown conversion path
- `plain_text` uses the text path

These paths need content-based entrypoints beneath their current file-based wrappers so JSON/JSONL adapters can pass unwrapped strings without writing temporary files.

For Data Sharing `canonical_markdown`, parse front matter once and keep it out of the body supplied to standard source formatting. For compact `content`, use the declared profile mapping rather than treating arbitrary JSON fields as source.

The Data Sharing preview materializer and importer must call the same Data Sharing adapter. Future standalone schemas may use a different wrapper adapter, but all adapters converge on the same `ImportContent` contract and downstream conversion/write behavior.

## Reuse Of Existing Docs Import

Keep one implementation of:

- Markdown validation through the shared renderer
- configured-scope validation
- `doc_id` and filename collision detection
- standard source formatting
- inline raster data-URL detection, planning, retargeting, and materialization
- atomic source writes
- Docs payload and search rebuild follow-through
- activity logging and result summaries

The existing importer handles one primary source at a time. Add a collection orchestration layer that converts normalized JSONL records into the same lower-level document write plans used by ordinary imports.

Useful extractions include:

- a content-based Markdown validation/media-planning function beneath path-based import wrappers
- a standard create-source formatter that accepts mapped parent and allowed metadata
- an overwrite-source formatter with explicit preservation rules
- a batch write/rebuild boundary accepting several planned target paths

Do not invoke the ordinary staged-filename endpoint once per record, copy preview Markdown into repo staging, or make the importer read `import-preview/<package_id>/source/`.

## Import Actions

Each selected record has one of these actions:

- `create`: create a new configured-scope document when no identity or filename collision exists
- `overwrite`: replace the existing document that caused the collision
- `skip`: leave the record unimported

A proposed `doc_id` with no collision creates normally unless the record is unselected. A collision must not silently choose an action and must never offer `Create as new` or replacement-`doc_id` handling in the collection workflow.

Resolve all collision choices before any writes. The collision UI provides:

- `Overwrite`: overwrite this colliding document
- `Overwrite all`: overwrite every remaining document collision in this import
- `Skip`: skip this colliding record
- `Skip all`: skip every remaining document collision in this import
- `Cancel import`: abort the complete apply with no writes

`Overwrite all` and `Skip all` apply only to remaining document collisions in the current import operation. They are not persistent preferences and do not authorize media, attachment, or interactive-asset overwrites.

Overwrite is a user decision, not a Data Sharing promotion operation. It does not require the preview file to be compared with canonical source or classified as a new revision.

### Create

- validate the final `doc_id` and filename
- map allowed title, summary, visibility, and parent fields
- use normal target-scope date defaults
- create standard Docs Viewer source

### Overwrite

- target only the existing document identified by the collision
- require explicit `Overwrite` or `Overwrite all` confirmation
- preserve the target `doc_id`, filename, and `added_date`
- refresh `last_updated`
- apply the imported body and explicitly allowed front matter
- validate the imported parent in the target scope
- retain target-only metadata unless the import contract explicitly allows replacement

Follow the ordinary importer’s explicit overwrite model where possible. Do not introduce staged-package revision or stale-source checks that the existing import workflow does not otherwise require.

## Collection Mapping

Resolve the complete selected set before writing so related records remain coherent.

The import plan should show:

- target scope
- selected records
- create, overwrite, or skip action
- imported identities and matching collision targets
- parent mapping
- supported internal link rewrites
- media plans and manual-copy requirements
- blockers and warnings

Because the collection workflow does not rename colliding records, imported identities remain stable. Use the selected create/overwrite/skip set to validate parents and supported internal links against the documents that will exist after apply. A skipped parent or link target must produce the documented blocker or warning rather than an implicit identity rewrite.

The implementation must decide and document:

- whether partial package selection is allowed
- how parents outside the selected set are resolved
- which internal link syntaxes are rewritten
- whether one invalid record blocks the complete batch
- how partial write failure is reported if the current mutation boundary cannot be fully atomic

This planning is an import-action summary, not a second content-review surface. Docs Review already supplies the readable content review.

## Images And Other Assets

Inline raster data URLs inside returned Markdown should use the existing Docs Import path:

1. parse the selected JSONL record
2. detect supported PNG, JPEG, WebP, or GIF data URLs
3. plan target-scope media references
4. derive filenames from the stable record/target `doc_id`
5. decode and materialize through the shared media service during import

Current scopes use `staging_manual`, so results must continue to report the required media-store copy step.

Package binary files that are not embedded data URLs still require an explicit supported mapping. Validation of a preview asset proves safe package containment; it does not by itself authorize copying that file into a configured media store.

## UI And Authority

Docs Review may expose an `Import` handoff for the selected immutable package. That handoff passes a safe package/staged-file identity to managed `/docs/`.

Managed Docs Import owns:

- target scope selection
- record selection
- create/overwrite/skip choices
- collision and mapping summary
- confirmation
- configured source and media writes
- rebuild and result reporting

Docs Review retains no configured-source mutation authority. Data Sharing retains no general Docs Viewer source-creation or overwrite authority.

## Security

- Resolve staged identities through Data Sharing’s safe staging and trusted metadata contracts.
- Never accept arbitrary filesystem paths from the browser.
- Require the staged file to match the preview package’s recorded export/package identity.
- Revalidate the JSONL schema, record shape, target scope, front matter, hierarchy, media plans, and collisions at import time.
- Enforce record, file, batch, and decoded-data limits.
- Reject symlink and containment escapes.
- Do not execute returned scripts or grant package HTML same-origin authority.
- Do not treat persistent preview Markdown as trusted import input.

## Implementation Tracking

Execution tasks and verification evidence are tracked in [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation).

This parent document remains the authority for product decisions, architecture boundaries, acceptance criteria, and non-goals. The child document may track progress but must not redefine these contracts.

## Acceptance Criteria

- a timestamped staged JSONL file produces one persistent, read-only Docs Review package
- every Docs Import format uses the configured `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` drop-zone
- Docs Import resolves that root through the existing W0 workspace adapter
- no production import path falls back to repo-local `var/docs/import-staging/`
- repeated review reads use package-local generated output rather than reparsing the JSONL
- Docs Review cannot read or write editable source bodies
- a newer staged return creates a separate preview package and does not stale the older pair
- Docs Import recognizes supported Data Sharing JSONL as a document collection
- the importer reads the staged JSONL, never preview `source/*.md`
- non-colliding records can create, while collisions can only be explicitly overwritten or skipped
- supported hierarchy, links, and embedded raster images are mapped through shared import services
- configured source writes and rebuilds remain owned by managed Docs Import

## Non-Goals

- editing the persistent preview projection
- importing from preview Markdown
- reparsing the complete JSONL on every Docs Review navigation
- staged-file staleness or revision management
- implementing the future standalone document-collection schema
- automatic overwrite based only on matching `doc_id`
- replacement-ID or `Create as new` handling for collection collisions
- diff, merge, delete, or promotion semantics
- moving staged Data Sharing JSONL into repo-local Docs Import staging
- introducing a second Docs-specific staging root or external-workspace resolver
- automatic remote media upload
- executing returned content

## Related References

- [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Docs Review Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-review)
- [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)
