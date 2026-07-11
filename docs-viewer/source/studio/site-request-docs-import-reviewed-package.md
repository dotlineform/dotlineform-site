---
doc_id: site-request-docs-import-reviewed-package
title: Docs Import Reviewed Package
added_date: 2026-07-11
last_updated: 2026-07-11
ui_status: proposed
summary: Import immutable staged Data Sharing JSONL as a document collection while retaining a persistent, read-only Docs Review projection.
parent_id: change-requests
viewable: true
---
# Docs Import Reviewed Package

## Status

Proposed follow-on to [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) and the current [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) implementation.

The current workflow already proves the persistent Docs Review package and renderer. This request simplifies the remaining import path and removes source editing from Docs Review.

## Decision

Treat the staged Data Sharing JSON/JSONL file as another Docs Import source format.

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
| `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/<timestamped-file>.jsonl` | immutable returned package and import input | Data Sharing staging only |
| `import-preview/<package_id>/manifest.json` | trusted association between the staged package and its view projection | preview producer only |
| `import-preview/<package_id>/source/*.md` | durable, human-readable, read-only build input | preview producer only |
| `import-preview/<package_id>/generated/` | durable Docs Review tree and document payloads | package-local builder only |
| configured Docs Viewer scope source | accepted import output | managed Docs Import only |

The preview `source/*.md` files must never become an alternative import authority. They exist to reuse the Docs Viewer builder and make the projection inspectable.

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

Register a schema-aware document-collection format before the current generic `.json`/`.jsonl` downloadable-file fallback.

Extension alone is insufficient because Docs Import already accepts JSON and JSONL as ordinary downloadable files. Detection must inspect the package header and trusted metadata, for example:

- `record_type: data_sharing_header`
- supported package `schema_version`
- supported documents profile/import type
- matching trusted `export_id` metadata

If the staged file does not match a supported document-collection schema, retain the existing generic file-import behavior.

The collection importer should support both the compact returned-document format and the full-source format only where their field contracts are explicitly mapped. It must not infer a document package merely from arbitrary row fields.

## Shared Parser And Normalizer

Use one parser/normalizer for preview materialization and import.

```text
staged JSONL
  -> validate header and trusted metadata
  -> parse document records
  -> normalize identity, front matter, Markdown, hierarchy, and assets
     -> persistent preview materializer
     -> configured-scope collection importer
```

The normalized record should carry at least:

- source export/package identity
- record index or stable record identity
- proposed `doc_id`
- title
- body Markdown or exact `canonical_markdown`
- allowed front matter
- `parent_id`
- link and asset information
- source format/profile diagnostics

For `canonical_markdown`, parse front matter once and keep it out of the body supplied to standard source formatting. For compact `content`, use the declared profile mapping rather than treating arbitrary JSON fields as source.

The persistent preview materializer and Docs Import may apply different output policies, but they must not interpret the JSONL record shape differently.

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

For each selected record, the user can choose:

- `create`: create a new configured-scope document
- `overwrite`: replace an explicitly selected existing document
- `skip`: leave the record unimported

A proposed `doc_id` with no collision defaults naturally to create. A collision must not silently choose an action. The UI should ask whether to overwrite the matching document, create under a replacement `doc_id`, or skip it.

Overwrite is a user decision, not a Data Sharing promotion operation. It does not require the preview file to be compared with canonical source or classified as a new revision.

### Create

- validate the final `doc_id` and filename
- map allowed title, summary, visibility, and parent fields
- use normal target-scope date defaults
- create standard Docs Viewer source

### Overwrite

- require explicit target identity and confirmation
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
- proposed and final target identities
- parent mapping
- supported internal link rewrites
- media plans and manual-copy requirements
- blockers and warnings

Use the record-to-target mapping to update parents and supported internal links when a created document receives a replacement ID or an overwrite targets a different explicit identity.

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
4. retarget filenames when the final target `doc_id` differs
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

## Implementation Tasks

### 1. Extract The Shared JSONL Parser

- define supported Data Sharing document-collection schema detection
- parse trusted header/export metadata and document records
- normalize compact content and full `canonical_markdown` through explicit mappings
- return stable record identities, content, front matter, hierarchy, asset data, and diagnostics

### 2. Use The Parser For Persistent Preview Materialization

- keep the timestamped `import-preview/<package_id>/` identity
- write the trusted manifest association
- materialize read-only `source/*.md`
- build and retain package-local `generated/`
- make normal Docs Review reads use the persistent generated output
- preserve repair/regeneration only for missing or damaged derived output

### 3. Remove Docs Review Source Editing

- remove source mode and its control
- remove source-read/source-write capabilities and endpoints
- remove revision and save/rebuild services
- remove review source-editor modules and bindings
- update route contracts, runtime ownership docs, and focused tests

### 4. Register The JSONL Collection Import Format

- detect supported Data Sharing headers before generic JSON/JSONL file import
- list the staged package as a collection import source
- parse records through the shared normalizer
- keep unsupported JSON/JSONL behavior unchanged

### 5. Add Collection Import Planning And Apply

- allow record selection
- compute create, overwrite, skip, ID, parent, link, and media plans
- require explicit overwrite decisions
- reuse lower-level source formatting, media materialization, writes, and rebuilds
- return precise per-record and batch results

### 6. Add The Review-To-Import Handoff

- identify the staged file through the immutable package association
- open managed Docs Import with that package selected
- keep review and configured-source authority separate
- report import unavailable when the associated staged file has been deleted

### 7. Verify

- keep ordinary single-file import behavior green
- test schema detection before generic JSON/JSONL fallback
- test shared parsing produces equivalent preview and import records
- test persistent preview viewing without repeated JSONL conversion
- test absence of review source-edit capabilities and UI
- test create, confirmed overwrite, replacement-ID create, and skip
- test parent/link mapping across selected records
- test embedded data-URL media planning and materialization
- test deleted staged-file import unavailability while persistent preview remains readable
- verify Docs Review and Data Sharing expose no configured-source mutation capability

## Acceptance Criteria

- a timestamped staged JSONL file produces one persistent, read-only Docs Review package
- repeated review reads use package-local generated output rather than reparsing the JSONL
- Docs Review cannot read or write editable source bodies
- a newer staged return creates a separate preview package and does not stale the older pair
- Docs Import recognizes supported Data Sharing JSONL as a document collection
- the importer reads the staged JSONL, never preview `source/*.md`
- the user can create, explicitly overwrite, or skip selected records
- supported hierarchy, links, and embedded raster images are mapped through shared import services
- configured source writes and rebuilds remain owned by managed Docs Import

## Non-Goals

- editing the persistent preview projection
- importing from preview Markdown
- reparsing the complete JSONL on every Docs Review navigation
- staged-file staleness or revision management
- automatic overwrite based only on matching `doc_id`
- diff, merge, delete, or promotion semantics
- moving staged Data Sharing JSONL into repo-local Docs Import staging
- automatic remote media upload
- executing returned content

## Related References

- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Docs Review Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-review)
- [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)
