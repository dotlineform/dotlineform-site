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

Prerequisite batch decisions and targeted enabling refactors are tracked in [Docs Import Reviewed Package Preparation And Refactor](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-preparation-refactor). Applicable preparation gates must be resolved before the collection plan/apply workflow is finalized.

## 0. Complete Collection Import Preparation

- [x] Resolve the preparation request's open batch decisions and copy approved product outcomes into the parent request.
- [x] Adopt the approved frontend, adapter, service, plan/apply, rebuild, and result owner contracts.
- [x] Confirm the ordinary single-source importer uses the shared per-document boundary without behavior change.
- [x] Confirm collection dry-run planning is complete and write-free before implementing confirmed apply.

## 1. Move Docs Import To The W0 Drop-Zone Adapter

- [x] Replace `STAGING_REL_DIR` and `repo_root / var/docs/import-staging` assumptions with `configured_workspace_paths(repo_root).import_staging`.
- [x] Reuse `marker_path()` and the W0 availability/status contract.
- [x] Update file listing and primary-source resolution.
- [x] Update Markdown-package discovery and containment.
- [x] Update interactive HTML companion discovery.
- [x] Update `staging_manual` inline-media output.
- [x] Update converted Markdown-package images and copied attachments.
- [x] Keep existing suffix, direct-child, traversal, symlink, and containment protections.
- [x] Remove all production fallback reads and duplicate writes to `var/docs/import-staging/`.
- [x] Update tests to provide an isolated temporary `DOTLINEFORM_PROJECTS_BASE_DIR`.

## 2. Extract The Data Sharing Collection Adapter And Shared Content Contract

- [x] Define supported Data Sharing document-collection schema detection.
- [x] Parse trusted header/export metadata and document records.
- [x] Normalize compact content through explicit Data Sharing mappings.
- [x] Normalize full `canonical_markdown` through explicit Data Sharing mappings.
- [x] Accept omitted returned content for trusted existing records and valid new structural records.
- [x] Preserve replace, preserve-existing, and empty-new content intent through preview and import planning.
- [x] Define a generic `ImportContent` record without mandatory Data Sharing provenance.
- [x] Add content-based Markdown import entrypoints beneath the file wrapper.
- [x] Add content-based HTML-to-Markdown entrypoints beneath the file wrapper.
- [x] Add content-based plain-text import entrypoints beneath the file wrapper.
- [x] Return stable record identities, optional content, content intent, front matter, hierarchy, asset data, and diagnostics.
- [x] Leave standalone collection schema detection as a future adapter rather than implementing it in this slice.

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

- [x] Detect supported Data Sharing headers before generic JSON/JSONL file import.
- [x] List the staged package as a collection import source.
- [x] Parse records through the Data Sharing adapter into shared `ImportContent` records.
- [x] Keep unsupported JSON/JSONL downloadable-file behavior unchanged.

## UI Consistency Guardrail

Any UI addition or change in the remaining implementation must remain consistent with the existing Docs Viewer management UI:

- reuse existing Docs Viewer CSS, layout primitives, tokens, control styles, and shared classes wherever possible; add focused styles only when no current primitive expresses the required state
- follow the existing modal design and lifecycle conventions, with one focused owner responsible for open, render, decision, confirmation, cancellation, close, cleanup, and state reset; keep modal lifecycle and collection state out of the management coordinator
- reuse existing status fields and ready/busy/error state conventions rather than introducing a parallel message surface
- scope status text to the active control or workflow and clear it as soon as focus or interaction moves elsewhere, so stale status messages do not remain attached to an inactive task
- keep UI copy in the existing import text/config owner and use manual or temporary browser checks for modal feel, focus behavior, status clearing, and visual consistency rather than permanent choreography tests

## 6. Add Collection Import Planning And Apply

- [ ] Treat every package record as in scope; do not add per-record selection UI.
- [ ] Compute create, overwrite, skip, collision, parent, and media plans before writing.
- [ ] Pass body-content links through unchanged without resolution, rewriting, blockers, or warnings.
- [ ] Block malformed package/schema data, unsafe identities, missing parents, and hierarchy cycles.
- [ ] Require explicit per-record `Skip` or `Cancel` for invalid front matter and unsupported supplied content formats.
- [ ] Retain an optional user note with each explicitly skipped invalid-record result/activity entry.
- [ ] Pass other non-structural body findings through and show available warnings in the final result.
- [ ] Resolve parents against existing target documents or explicit package document records.
- [ ] Support supplied new parents and multi-level parent chains without reordering package records.
- [ ] Block undeclared missing parents and hierarchy cycles; do not infer placeholder parent docs.
- [ ] Apply hierarchy-only changes surgically to current canonical front matter; preserve existing bodies and unrelated front matter and use empty bodies for content-less new structural records.
- [ ] Add `Overwrite` for the current document collision.
- [ ] Add `Skip` for the current colliding record.
- [ ] Add an unchecked `Apply to all` checkbox for `Overwrite` and `Skip`.
- [ ] Add a `Cancel` button that aborts the complete import with no writes.
- [ ] Resolve collisions sequentially, then show one read-only final plan summary before apply.
- [ ] Keep `Cancel` available before apply only and disable/remove it once confirmed writes begin.
- [ ] Do not expose replacement IDs or `Create as new` for collection collisions.
- [ ] Keep media, attachment, and interactive-asset overwrite authority separate from document `Overwrite` applied to all collisions.
- [ ] Skip unsupported, missing, unauthorized-collision, or failed asset operations without blocking the document or batch.
- [ ] Preserve returned source references when asset materialization cannot complete and report safe asset warnings/manual-copy instructions.
- [ ] Keep trusted intake, containment, symlink, size, and execution-safety failures blocking; never attempt an unsafe copy.
- [ ] Reuse per-document atomic writes without adding batch rollback or a staged collection transaction.
- [ ] Write records strictly in package JSONL order and reuse existing per-record source/media apply behavior.
- [ ] Stop on the first source-write failure and report remaining package records as not attempted.
- [ ] Invoke the existing managed write/rebuild owner once after the write phase with all affected paths and ids.
- [ ] Allow normal targeted-to-full rebuild fallback; add no import-specific generation retry or watcher dependency.
- [ ] Keep apply synchronous; add no progress API, background job, polling, or result-retrieval endpoint.
- [ ] Reuse existing safety limits without adding speculative collection-specific thresholds.
- [ ] Reuse `GET /docs/import-source-files` and `POST /docs/import-source`; add no collection-specific route family.
- [ ] Use `preview_only: true` for server-calculated planning and `preview_only: false` plus explicit per-record decisions for synchronous apply.
- [ ] Resolve a review `package_id` only to a server-listed safe `staged_filename`; never accept package or preview-source paths.
- [ ] Expand `Apply to all` in the frontend and submit explicit record decisions rather than a browser-calculated plan.
- [ ] Recompute/revalidate the plan at apply; add no stored plan, plan token, job id, polling, or result endpoint.
- [ ] Reconfirm only when collision target, target identity, parent resolution, hierarchy validity, or blocker state changes.
- [ ] Do not add source revision/body hashes or reconfirm preserve-existing rows for unrelated canonical body/metadata changes.
- [ ] Report applied, failed, and not-attempted records when a batch is partially written.
- [ ] Keep successful source mutations when Docs/search generation fails and report generation outcome separately.
- [ ] Leave generation diagnosis and repair to the existing ordinary generation workflow.
- [ ] Reuse lower-level source formatting, media materialization, writes, and rebuilds.
- [ ] Return precise per-record and batch results.
- [ ] Add `studio/shared/python/json_markdown_report.py` with pure `render_json_markdown_report()` and atomic `write_json_markdown_report()` entrypoints.
- [ ] Keep the shared helper JSON-compatible, deterministic, Markdown-escaped, order-preserving, caller-path-owned, and free of app-specific dependencies.
- [ ] Keep templates, plugins, HTML rendering, table configuration, output-root resolution, marker projection, and a generic report registry out of the first helper.
- [ ] Add focused shared-helper tests at `studio/tests/python/test_json_markdown_report.py`.
- [ ] Shape the Docs Import result JSON by created, overwritten, skipped, failed, and not-attempted status in package order.
- [ ] Use the shared writer for confirmed-apply reports under `configured_workspace_paths(repo_root).import_staging / "results"`.
- [ ] Reuse `marker_path()` for the response/activity report path and keep result reports out of direct-child source discovery.
- [ ] Include optional invalid-record notes, separate generation outcome, warnings, and manual-copy instructions without source bodies or absolute paths.
- [ ] Treat report-write failure as a non-blocking warning that does not change import outcomes.

## 7. Add The Review-To-Import Handoff

- [ ] Identify the staged file through the immutable package association.
- [ ] Open managed Docs Import with that package selected.
- [ ] Keep review and configured-source authority separate.
- [ ] Report import unavailable when the associated staged file has been deleted.

## 8. Verification

- [x] Keep ordinary single-file import behavior green.
- [x] Verify every existing Docs Import format is discovered from the W0 external drop-zone.
- [x] Verify missing workspace configuration disables import cleanly without affecting ordinary Docs viewing.
- [x] Verify responses expose marker-rooted paths and never user-specific absolute paths.
- [x] Verify repo-local `var/docs/import-staging/` is not read or written.
- [x] Test schema detection before generic JSON/JSONL fallback.
- [x] Test shared parsing produces equivalent preview and import records.
- [x] Test Markdown, HTML, and plain-text body dispatch through content-based entrypoints.
- [ ] Test persistent preview viewing without repeated JSONL conversion.
- [ ] Test absence of review source-edit capabilities and UI.
- [ ] Test non-colliding create.
- [ ] Test `Overwrite` and `Skip` with the `Apply to all` checkbox off and on.
- [ ] Test `Apply to all` affects only remaining document collisions and is unavailable for invalid-record decisions.
- [ ] Test `Cancel` produces no writes.
- [ ] Test cancellation is unavailable after apply begins and the synchronous operation runs to completion or failure.
- [ ] Verify no collection-specific progress/job infrastructure or speculative size limit is introduced.
- [ ] Test both collection phases use the existing import POST and that apply ignores/rejects browser-authored plan/path fields.
- [ ] Test review handoff preselects the safe listed staged record without granting package-path authority.
- [ ] Test changed target facts return a refreshed plan with no writes, while unrelated preserve-existing source changes do not require reconfirmation.
- [ ] Test parent mapping across all package records.
- [ ] Test body links are preserved exactly without resolution diagnostics.
- [ ] Test package/identity/structural blockers cannot proceed to apply.
- [ ] Test invalid front matter and unsupported content require explicit `Skip` or `Cancel`, with no implicit or bulk skip.
- [ ] Test optional invalid-record notes persist in result/activity data and body diagnostics appear in final warnings.
- [ ] Test later write failure does not roll back completed per-document writes and reports unapplied records precisely.
- [ ] Test source-write failure stops package-order apply without attempting later records.
- [ ] Test generation failure preserves successful source mutations and remains separate from import record outcomes.
- [ ] Test existing-parent reuse, supplied new-parent creation, package-order writes, multi-level hierarchy validation, missing-parent blocking, and cycle rejection.
- [ ] Test one targeted Docs/search rebuild follows the batch and the watcher suppression contract prevents duplicate managed-write rebuilds.
- [ ] Test safe full-scope fallback completes while actual generation failure stops and reports separately without import retry.
- [ ] Test omitted existing content changes only returned allowed front matter on current canonical source, while omitted new-parent content creates an empty body.
- [ ] Test embedded data-URL media planning and materialization.
- [ ] Test asset-level failure preserves the source reference, imports the document, warns, and continues to later package records.
- [ ] Test document `Overwrite` applied to all collisions does not authorize asset overwrite and unsafe asset paths are never copied.
- [ ] Test result Markdown groups documents by status, preserves package order within groups, and omits empty sections.
- [ ] Test the shared helper renders nested JSON-compatible mappings/lists deterministically, escapes Markdown, honors optional section order, and writes atomically.
- [ ] Test completed, partial, and generation-failed applies write reports while preview, rejected plans, and pre-write cancellation do not.
- [ ] Test result reports are ignored by import-source discovery and expose only marker-rooted paths.
- [ ] Test report-write failure preserves the import result and adds a warning.
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
- [Docs Import Reviewed Package Preparation And Refactor](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-preparation-refactor)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
