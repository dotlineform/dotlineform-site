---
doc_id: site-request-docs-import-reviewed-package-implementation
title: Docs Import Reviewed Package Implementation
added_date: 2026-07-12
last_updated: 2026-07-12
ui_status: proposed
summary: Track implementation and verification of the shared import drop-zone, collection adapter, persistent read-only review projection, and managed collection apply workflow.
parent_id: site-request-docs-import-reviewed-package
viewable: true
---
# Docs Import Reviewed Package Implementation

## Purpose

This child document tracks implementation of [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package).

The parent document owns all decisions and acceptance criteria. This checklist records execution progress and evidence only. Do not widen the refactoring boundary or add future standalone collection-schema implementation here.

## 1. Move Docs Import To The W0 Drop-Zone Adapter

- [ ] Replace `STAGING_REL_DIR` and `repo_root / var/docs/import-staging` assumptions with `configured_workspace_paths(repo_root).import_staging`.
- [ ] Reuse `marker_path()` and the W0 availability/status contract.
- [ ] Update file listing and primary-source resolution.
- [ ] Update Markdown-package discovery and containment.
- [ ] Update interactive HTML companion discovery.
- [ ] Update `staging_manual` inline-media output.
- [ ] Update converted Markdown-package images and copied attachments.
- [ ] Keep existing suffix, direct-child, traversal, symlink, and containment protections.
- [ ] Remove all production fallback reads and duplicate writes to `var/docs/import-staging/`.
- [ ] Update tests to provide an isolated temporary `DOTLINEFORM_PROJECTS_BASE_DIR`.

## 2. Extract The Data Sharing Collection Adapter And Shared Content Contract

- [ ] Define supported Data Sharing document-collection schema detection.
- [ ] Parse trusted header/export metadata and document records.
- [ ] Normalize compact content through explicit Data Sharing mappings.
- [ ] Normalize full `canonical_markdown` through explicit Data Sharing mappings.
- [ ] Define a generic `ImportContent` record without mandatory Data Sharing provenance.
- [ ] Add content-based Markdown import entrypoints beneath the file wrapper.
- [ ] Add content-based HTML-to-Markdown entrypoints beneath the file wrapper.
- [ ] Add content-based plain-text import entrypoints beneath the file wrapper.
- [ ] Return stable record identities, content, front matter, hierarchy, asset data, and diagnostics.
- [ ] Leave standalone collection schema detection as a future adapter rather than implementing it in this slice.

## 3. Use The Adapter For Persistent Preview Materialization

- [ ] Keep the timestamped `import-preview/<package_id>/` identity.
- [ ] Write the trusted manifest association.
- [ ] Materialize read-only `source/*.md`.
- [ ] Build and retain package-local `generated/`.
- [ ] Make ordinary Docs Review reads use the persistent generated output.
- [ ] Preserve repair/regeneration only for missing or damaged derived output.

## 4. Remove Docs Review Source Editing

- [ ] Remove source mode and its control.
- [ ] Remove source-read and source-write capabilities.
- [ ] Remove source-read and source-write endpoints.
- [ ] Remove revision and save/rebuild services.
- [ ] Remove review source-editor modules and bindings.
- [ ] Update route contracts and runtime ownership documentation.
- [ ] Update focused review tests.

## 5. Register The JSONL Collection Import Format

- [ ] Detect supported Data Sharing headers before generic JSON/JSONL file import.
- [ ] List the staged package as a collection import source.
- [ ] Parse records through the Data Sharing adapter into shared `ImportContent` records.
- [ ] Keep unsupported JSON/JSONL downloadable-file behavior unchanged.

## 6. Add Collection Import Planning And Apply

- [ ] Allow record selection.
- [ ] Compute create, overwrite, skip, collision, parent, link, and media plans before writing.
- [ ] Add `Overwrite` for the current document collision.
- [ ] Add `Overwrite all` for remaining document collisions in the current import.
- [ ] Add `Skip` for the current colliding record.
- [ ] Add `Skip all` for remaining document collisions in the current import.
- [ ] Add `Cancel import` with no writes.
- [ ] Do not expose replacement IDs or `Create as new` for collection collisions.
- [ ] Keep media, attachment, and interactive-asset overwrite authority separate from `Overwrite all`.
- [ ] Reuse lower-level source formatting, media materialization, writes, and rebuilds.
- [ ] Return precise per-record and batch results.

## 7. Add The Review-To-Import Handoff

- [ ] Identify the staged file through the immutable package association.
- [ ] Open managed Docs Import with that package selected.
- [ ] Keep review and configured-source authority separate.
- [ ] Report import unavailable when the associated staged file has been deleted.

## 8. Verification

- [ ] Keep ordinary single-file import behavior green.
- [ ] Verify every existing Docs Import format is discovered from the W0 external drop-zone.
- [ ] Verify missing workspace configuration disables import cleanly without affecting ordinary Docs viewing.
- [ ] Verify responses expose marker-rooted paths and never user-specific absolute paths.
- [ ] Verify repo-local `var/docs/import-staging/` is not read or written.
- [ ] Test schema detection before generic JSON/JSONL fallback.
- [ ] Test shared parsing produces equivalent preview and import records.
- [ ] Test Markdown, HTML, and plain-text body dispatch through content-based entrypoints.
- [ ] Test persistent preview viewing without repeated JSONL conversion.
- [ ] Test absence of review source-edit capabilities and UI.
- [ ] Test non-colliding create.
- [ ] Test `Overwrite` and `Overwrite all`.
- [ ] Test `Skip` and `Skip all`.
- [ ] Test `Cancel import` produces no writes.
- [ ] Test parent/link mapping across selected records.
- [ ] Test embedded data-URL media planning and materialization.
- [ ] Test deleted staged-file import unavailability while persistent preview remains readable.
- [ ] Verify Docs Review and Data Sharing expose no configured-source mutation capability.

## Completion Rule

Mark this child request complete only when:

- every applicable checklist item is complete
- verification evidence is recorded in the owning durable documentation or tests
- the parent request's acceptance criteria are satisfied
- the parent and child documents are updated to current status

## Related References

- [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
