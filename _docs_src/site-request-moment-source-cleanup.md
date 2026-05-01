---
doc_id: site-request-moment-source-cleanup
title: "Moment Source Cleanup"
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: change-requests
sort_order: 102
---
# Moment Source Cleanup

Status:

- in progress

## Summary

This request tracks a focused cleanup of retained moment source compatibility paths.

The completed [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup) removed workbook-shaped compatibility from the work, detail, and series catalogue pipeline. Moments do not appear to need the same generator row-projection cleanup, but they still have moment-specific source-model compatibility surfaces from earlier migrations.

Current moment source model:

- canonical metadata: `assets/studio/data/catalogue/moments.json`
- canonical prose: `_docs_src_catalogue/moments/<moment_id>.md`
- staged import prose: `var/docs/catalogue/import-staging/moments/<moment_id>.md`
- source images: configured projects media root, normally `moments/images/<source_image_file>`
- generated runtime artifacts: `_moments/`, `assets/moments/index/`, `assets/data/moments_index.json`, catalogue search, and local/remote moment media derivatives

## Problem

Some retained moment code and docs still describe or support older source assumptions:

- front-matter-owned moment metadata in Markdown source files
- external folder scanning for moment Markdown source files
- manifest generation/loading paths that may now be migration-only
- delete docs and script behavior that still reference external canonical moment prose under the projects base directory
- historical migration docs that may be useful history but should not be mistaken for current workflow guidance

These surfaces make it harder to tell which moment source paths are live workflow, staging/import support, migration-only compatibility, or removable debt.

## Goals

- inventory retained moment source compatibility paths in scripts, Studio flows, source data, generated artifacts, and docs
- classify each path as active, staging/import support, migration-only, deprecated clean-exit, docs-stale, or removable
- keep the current moment source model explicit and consistent with work/series source boundaries
- remove or narrow obsolete front-matter/external-source compatibility only after confirming current import, publish, unpublish, delete, and build paths do not depend on it
- update current docs so they do not route users through retired moment source assumptions
- preserve deterministic generated moment output

## Non-Goals

- do not redesign the Moment editor
- do not add browser-side prose editing
- do not change remote media publishing or R2 behavior
- do not delete external historical moment source files as part of cleanup
- do not remove staged prose import support unless a separate workflow decision replaces it

## Task List

### Task 1. Inventory Moment Source Compatibility Paths

Status:

- completed

Result:

- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)

Inventory likely areas:

- `scripts/moment_sources.py`
- `scripts/generate_work_pages.py`
- `scripts/catalogue_json_build.py`
- `scripts/delete_moment.py`
- `scripts/studio/catalogue_write_server.py`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/data/catalogue/moments.json`
- `_docs_src_catalogue/moments/`
- `var/docs/catalogue/import-staging/moments/`
- moment docs and migration request docs

Questions to answer:

- Which front-matter parsing helpers are still required for staged import validation versus only retained for migration?
- Is generator fallback scanning of external moment source files still needed now that `moments.json` is canonical?
- Should `delete_moment.py` delete canonical prose from `_docs_src_catalogue/moments/`, or remain source-metadata/runtime cleanup only by default?
- Which docs describe historical migration context, and which are stale current workflow guidance?

Resolved direction:

- Moment prose import is body-only Markdown. Metadata is stored in catalogue source JSON, not prose front matter.
- Front-matter parsing should remain only where it is needed to reject front matter in staged or canonical body-only prose. Helpers that extract metadata from moment prose are migration-only unless another active path proves otherwise.
- Generator fallback scanning of external moment source files is not needed now that `moments.json` is canonical. Prose source files are copied manually into staging.
- The Delete button on `/studio/catalogue-moment/` is the only current deletion entry point for moments. Standalone delete behavior should not preserve a separate active moment-deletion workflow.
- Documentation needs classification before cleanup. Current workflow docs should describe `moments.json`, `_docs_src_catalogue/moments/`, and `var/docs/catalogue/import-staging/moments/`; migration/change-log docs may remain as historical context when clearly framed that way.

### Task 2. Decide Retention Policy

Status:

- planned

For each retained path, decide whether to:

- keep as active workflow
- keep as explicit staging/import support
- keep temporarily as migration-only support
- convert to deprecated clean-exit guidance
- remove
- update docs only

### Task 3. Remove Or Narrow Moment Compatibility Surfaces

Status:

- planned

Apply approved changes in small slices.

Likely cleanup areas:

- remove unused workbook-ish helpers from `scripts/moment_sources.py`
- narrow or remove external moment source scanning if no live flow needs it
- align delete script docs and behavior with `_docs_src_catalogue/moments/` as the canonical prose source
- update current docs to distinguish staged import, canonical prose, and source image lookup

### Task 4. Verify Moment Output Stability

Status:

- planned

Acceptance checks:

- moment build previews still work for a representative moment
- generated moment route stub, per-moment JSON, moments index, and catalogue search output remain deterministic
- Moment editor import preview/apply still works for staged body-only prose
- publish, unpublish, delete preview, and media refresh behavior remain aligned with the current source model
- docs no longer present retired front-matter/external-prose assumptions as current guidance

## Benefits

- moment source ownership becomes as clear as work and series ownership
- future moment editor and generator work can target the current JSON/prose split without carrying migration assumptions
- delete/import docs become less ambiguous

## Risks

- removing external scan or front-matter helpers too early could break a staging, recovery, or migration workflow
- delete behavior touches generated artifacts, source prose, source images, local media, and search, so it needs especially careful verification
- historical migration docs may still be useful as context, but current workflow docs should not depend on them

Mitigation:

- inventory before code changes
- keep import/staging support explicit
- use isolated temp generation and preview/delete dry-runs before write checks
