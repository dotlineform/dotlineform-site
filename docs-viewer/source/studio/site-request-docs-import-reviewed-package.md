---
doc_id: site-request-docs-import-reviewed-package
title: Docs Import Reviewed Package
added_date: 2026-07-11
last_updated: 2026-07-11
ui_status: proposed
summary: Create-only import of validated reviewed-package Markdown through a reusable Docs Import source-provider and normalized-candidate boundary.
parent_id: change-requests
viewable: true
---
# Docs Import Reviewed Package

## Status

Proposed follow-on to [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) and [Docs Review](/docs/?scope=studio&doc=docs-viewer-review).

This request owns the remaining transition from a validated reviewed package into configured Docs Viewer source. The transition is a create-only Docs Viewer import, not Data Sharing promotion and not replacement of an existing canonical document.

## Decision

Treat selected reviewed-package documents as new Docs Viewer import candidates.

- Data Sharing produces and validates the returned package.
- Docs Review renders and temporarily edits the package in isolation.
- Docs Viewer Import previews and creates new configured-scope documents.
- The reviewed package remains unchanged and available as the import source.
- Existing canonical documents are never overwritten, merged, promoted, or deleted by this workflow.

When a proposed `doc_id` already exists in the target scope, the user must choose a new `doc_id`. The collision is not an overwrite opportunity.

## Why A New Import Source Is Needed

The current Docs Viewer import flow reads one primary candidate from `var/docs/import-staging/`:

- a body-only Markdown file
- one Markdown package directory containing exactly one Markdown file and local attachments
- or another registered single-file format

A validated Docs Review package has a different shape:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/<package_id>/
  manifest.json
  source/
    <doc-id>.md
  assets/
  inventories/
  generated/
```

Its source files:

- live outside the repository staging root
- already contain validated Docs Viewer front matter
- may form a multi-document hierarchy
- may link to other documents in the same package
- may contain inline raster data URLs
- may refer to package-inventoried assets

Copying these files into `var/docs/import-staging/` would discard trusted package identity and encourage a second, divergent import path. Passing them unchanged to the current Markdown preview would also treat their front matter as body content.

## Reuse Boundary

Refactor the import flow around a normalized candidate contract rather than duplicating the importer.

Illustrative shape:

```text
ImportSourceProvider
  -> resolve candidate identity inside an allowed root
  -> read and normalize source
  -> DocsImportCandidate
  -> existing preview, validation, media planning, write, and rebuild services
```

The exact Python names can be chosen during implementation. The boundary must preserve these responsibilities.

### Source Providers

The existing staging provider owns:

- listing safe direct children of `var/docs/import-staging/`
- resolving the current staged filename contract
- choosing a registered source format
- supplying one candidate at a time

The reviewed-package provider owns:

- resolving a safe `package_id` through the existing validated-package service
- requiring the trusted validated manifest
- listing selectable package document identities
- resolving only direct `source/<doc-id>.md` children
- parsing validated front matter and separating it from body Markdown
- supplying package and inventory context without accepting browser-supplied filesystem paths

Neither provider writes configured-scope source.

### Normalized Candidate

A normalized candidate should carry at least:

- source kind, such as `staged_file` or `review_package_document`
- stable source identity and display label
- source format
- proposed title and `doc_id`
- body Markdown
- allowed imported metadata
- source/package context needed for safe media materialization
- warnings and provenance for the preview

Path values remain server-derived diagnostics. The browser sends package and document identities, never arbitrary source paths.

### Existing Import Functions To Reuse

Keep one implementation of:

- Markdown preview construction and renderer validation
- inline raster data-URL detection and media planning
- media-plan retargeting when the final `doc_id` changes
- inline raster materialization
- configured-scope validation
- collision detection
- standard source formatting and atomic writes
- targeted Docs payload and search rebuilds
- activity logging and result summaries

The current `generate_import_preview()` and `handle_import_source()` APIs may need to be split so source resolution is no longer fused to conversion and apply. The reviewed-package adapter must call shared lower-level services rather than simulate a staged filename or invoke the staging-only endpoint internally.

The practical extraction should include content-based cores with path-based wrappers:

- a Markdown preview function that accepts normalized Markdown text, a source label, a proposed identity, and target scope
- an inline-media materializer that verifies against the normalized candidate content instead of rereading only a staging path
- a create-source formatter that accepts the preflighted target identity, mapped parent, and allowed metadata instead of always forcing `parent_id: ""`
- an apply function that accepts preflighted candidate/create plans, while the existing `handle_import_source()` continues to adapt the current request body into one such plan

This is needed because the current media materializer rereads `source_path` and the current create formatter always produces root documents. Those staging-era assumptions cannot represent a front-matter-bearing, hierarchical reviewed package, but the underlying parsing, planning, media decoding, write, and rebuild logic remains reusable.

## Create-Only Policy

This workflow always returns `operation: create` when it writes.

- Do not accept `overwrite_doc_id` or `confirm_overwrite` as document-overwrite controls.
- A target `doc_id` or filename-stem collision blocks apply until a replacement `doc_id` is supplied.
- Re-run validation and collision checks immediately before writing.
- Do not compare package source hashes in order to classify update or replacement operations.
- Do not mutate or delete the reviewed package after a successful import.
- Preserve import provenance in diagnostics or activity records without making temporary workspace paths canonical metadata.

The ordinary staged-file importer may retain its existing overwrite behavior. Create-only is a policy of the reviewed-package source flow, not necessarily a global import change.

## Batch Preflight And Mapping

Reviewed packages may contain several related documents, so preview the complete selected set before writing any document.

The preview must show:

- target scope
- selected source documents
- proposed and final target `doc_id` values
- title and allowed front matter
- collision status
- parent mapping
- internal link rewrites
- media plans and manual-copy requirements
- warnings and blockers

Build a package-document-to-target-document mapping before apply. Use it to:

- retain a package `parent_id` when its target is known and valid
- rewrite it when a selected parent receives a replacement target `doc_id`
- rewrite supported internal Docs Viewer links between selected package documents
- identify parents or links that point outside the selected set

The implementation must explicitly decide and document:

- whether selection must be hierarchy-complete or may import a partial set
- whether an unresolved package parent becomes root, can be mapped to an existing target parent, or blocks apply
- which internal link syntaxes are rewritten
- whether one invalid candidate blocks the whole batch
- how a write or rebuild failure avoids leaving a misleading partial result

Prefer complete preflight and one mutation/rebuild boundary for the batch. If the current source-write service cannot provide a safe atomic batch, the UI and result must report partial completion precisely rather than implying transactionality.

## Front Matter Policy

Reviewed-package files are already Docs Viewer-shaped source, but importing them as new documents must not blindly preserve every field.

The normalizer should:

- use the validated source `doc_id` and title as proposals
- map package-local `parent_id` through the batch mapping
- preserve allowed descriptive fields such as `summary` when valid
- set target-scope date and visibility defaults through the normal import/create policy unless the target scope explicitly allows an imported value
- reject or omit package-only operational metadata
- write standard target source front matter once, without nesting the original front matter in the Markdown body

The allowlist belongs to Docs Viewer Import. Data Sharing validation proves package shape; it does not authorize every returned field for configured source.

## Images And Other Assets

Inline raster data URLs in Markdown should use the current Docs Import path:

1. preview detects supported PNG, JPEG, WebP, or GIF data URLs
2. media plans replace the data URLs with target-scope media references
3. replacement target IDs retarget the planned filenames
4. apply decodes and materializes the images through `materialize_inline_raster_media()`

Current scopes use `staging_manual`, so the preview and result must still explain the final manual media-store copy step. This request does not create a new Data Sharing asset-promotion system.

Package-inventoried binary files that are not embedded data URLs require an explicit supported import mapping. Unsupported or unresolved package assets remain blockers or warnings; they must not be copied into canonical paths merely because Data Sharing validated their package containment.

## UI And Service Ownership

The apply surface belongs to managed `/docs/`, where configured-scope import and canonical write capabilities already exist.

Docs Review may provide an `Import as new docs` handoff that opens the managed Docs Import flow with a safe `package_id` and optional selected document identities. It must not receive canonical mutation capabilities or call a general canonical-write endpoint from the review app context.

The Docs management service should expose focused reviewed-package preview/apply operations or a source-provider-aware import operation. The endpoint contract must keep normal import authorization, configured-scope checks, dry-run/preview behavior, and write/rebuild ownership.

## Security

- Resolve package and document identities through the validated-package provider.
- Never accept absolute paths, workspace-relative paths, or source text supplied as a substitute for the selected package file.
- Repeat containment and symlink checks at preview and apply.
- Enforce per-document and total batch size limits, including decoded data-URL media.
- Revalidate front matter, hierarchy, links, media plans, target scope, and collisions at apply time.
- Do not execute returned scripts or grant package HTML same-origin authority.
- Do not let a validated Data Sharing manifest bypass Docs Viewer import validation.

## Implementation Tasks

### 1. Extract The Reusable Candidate Boundary

- separate staging resolution from format preview and apply orchestration
- define a normalized candidate/context contract
- wrap current staged-file behavior in the first provider without changing its UI contract
- keep format conversion and media helpers independent of provider type

### 2. Add The Reviewed-Package Provider

- reuse validated package discovery and manifest/source containment helpers
- list safe package document candidates by identity
- split front matter from Markdown body
- project only allowed metadata into normalized candidates
- preserve provenance and inventory context for diagnostics

### 3. Add Batch Preview

- accept package identity, target scope, and selected document identities
- compute final ID, parent, internal-link, and media mappings
- report collisions as replacement-ID requirements only
- expose blockers and warnings before apply

### 4. Add Create-Only Apply

- reject overwrite controls
- repeat preflight against current target source
- materialize supported inline media through existing helpers
- create standard Docs Viewer source files
- rebuild affected Docs and search payloads through the existing write/rebuild boundary
- return precise per-document and batch results

### 5. Add The Managed Handoff

- add a safe Docs Review link/handoff without adding review write authority
- open the reviewed-package import state in `/docs/`
- show selection, target scope, mapping, media handoff, warnings, and apply result

### 6. Verify

- keep the existing staged-file import checks green after extracting the provider boundary
- test reviewed front-matter normalization without front-matter leakage into body Markdown
- test package containment and browser path rejection
- test create-only collision and replacement-ID behavior
- test batch parent and internal-link mapping
- test embedded data-URL image planning, ID retargeting, and materialization
- test preflight/apply drift and failure reporting
- verify Docs Review still exposes no canonical mutation capability

## Acceptance Criteria

- a validated package document can be previewed and created in a configured Docs Viewer scope without copying it into repo staging
- reviewed front matter is normalized into standard new-document source rather than imported as body text
- several selected package documents can be mapped before any write
- collisions require new target IDs and cannot overwrite existing docs
- supported internal parents and links follow replacement target IDs
- supported embedded raster images reuse the existing import media pipeline
- apply uses the existing Docs source-write/rebuild authority
- Data Sharing and Docs Review gain no canonical source-write responsibility
- the original reviewed package remains unchanged

## Non-Goals

- promoting a reviewed version over an existing canonical document
- merging, diffing, replacing, deleting, or revising existing docs
- using Data Sharing apply adapters for configured-source creation
- moving the reviewed package into `var/docs/import-staging/`
- automatically publishing or uploading media in `staging_manual` mode
- importing unsupported package binaries or executing returned content
- changing the full-package transport contract in this request

## Related References

- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Docs Review Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-review)
- [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)
