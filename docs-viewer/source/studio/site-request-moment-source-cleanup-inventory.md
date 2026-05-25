---
doc_id: site-request-moment-source-cleanup-inventory
title: Inventory
added_date: 2026-05-01
last_updated: "2026-05-11 13:03"
ui_status: done
parent_id: site-request-moment-source-cleanup
sort_order: 1000
viewable: true
---
# Inventory

Status:

- Task 1 inventory complete for implementation planning

## Purpose

This is the Task 1 inventory for [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup).

Use this document to record retained moment source compatibility paths before deciding whether each path should be kept, narrowed, retired to clean-exit guidance, or removed.

## Classification

Use these classifications consistently:

- `active-live`
  Part of the current canonical moment source workflow.
- `active-import-staging`
  Part of the current staged import workflow that writes canonical JSON metadata and body-only prose.
- `derived`
  Generated from canonical source and not independently editable.
- `migration-only`
  Retained only for older migration, comparison, or recovery paths.
- `deprecated-clean-exit`
  Retained only to exit with guidance instead of running an old workflow.
- `removable`
  No current active, migration, or clean-exit role identified.
- `docs-stale`
  Documentation appears to describe a retired workflow as current, or needs wording clarified.
- `historical-context`
  Historical request or change-log material that can remain if it is clearly not current workflow guidance.

## Findings

| ID | Surface | Location | Live workflow? | Classification | Finding | Proposed action | Verification |
|---|---|---|---|---|---|---|---|
| MSC-001 | Canonical moment metadata | `assets/studio/data/catalogue/moments.json`; `scripts/moment_sources.py` | yes | `active-live` | Moment metadata is canonical JSON source. Metadata is not owned by moment prose front matter. | Keep JSON metadata loading, normalization, validation, and writing helpers. | Existing Moment editor save/import previews still read and write `moments.json`; generator reads metadata from JSON source. |
| MSC-002 | Canonical body-only moment prose | `_docs_catalogue/moments/<moment_id>.md`; `scripts/generate_work_pages.py`; `scripts/catalogue_json_build.py` | yes | `active-live` | Canonical prose is repo-local Markdown body content. The generator renders this body with metadata from `moments.json`. | Keep body-only prose source. Do not reintroduce metadata extraction or front-matter validation for this file. | Moment build preview succeeds for a representative moment and generated moment JSON renders the canonical prose body. |
| MSC-003 | Staged moment prose import | `var/docs/catalogue/import-staging/moments/<moment_id>.md`; `studio/app/server/studio/catalogue_write_server.py`; `scripts/catalogue_json_build.py`; Studio moment import UI | yes | `active-import-staging` | Staged prose is manually copied into staging and imported as body-only Markdown. Metadata is submitted separately and saved to `moments.json`. | Keep staged import support, but do not keep front-matter detection or rejection as an active requirement. | Import preview/apply accepts staged body Markdown, writes `_docs_catalogue/moments/<moment_id>.md`, and writes `moments.json`. |
| MSC-004 | Front-matter detection for body-only validation | previously `has_front_matter_text` and `split_front_matter_text` in `scripts/moment_sources.py`; previous uses in `studio/app/server/studio/catalogue_write_server.py` and `scripts/catalogue_json_build.py` | no | removed | Implemented: active moment import and preview paths no longer detect or reject front matter, and the detection helpers were removed. | Keep staged Markdown as body source. Do not reintroduce front-matter rejection as active validation. | Moment import preview/apply and scoped moment builds pass without calling front-matter detection helpers. |
| MSC-005 | Front-matter metadata extraction from moment prose | previously `parse_front_matter` in `scripts/moment_sources.py`; retired source-entry/update helpers | no | removed | Implemented: source-entry, front-matter update, scalar update, workbook-ish row helpers, standalone delete imports, and the final `parse_front_matter` helper were removed. | Keep moment prose metadata-free. Do not keep front-matter extraction as migration-only support by default. | Source validation, Moment editor import, scoped moment builds, and publish/unpublish flows pass without reading metadata from prose front matter. |
| MSC-006 | External moment source file scanning | `scan_moment_source_files` in `scripts/moment_sources.py`; fallback in `scripts/generate_work_pages.py` | no | removed | Implemented: the generator no longer falls back to scanning external moment Markdown when `moments.json` is empty. Prose is resolved from `_docs_catalogue/moments/` through JSON metadata source records. | Keep generation JSON-source-only. A missing or empty `moments.json` should report no moment metadata rather than silently deriving moments from external Markdown. | Representative moment build previews still select the expected moment artifacts and do not import scanner helpers. |
| MSC-007 | Moment sources manifest support | `build_moment_sources_manifest_payload`, `load_moment_sources_manifest`, `write_moment_sources_manifest`; `--moment-sources-manifest` in `scripts/generate_work_pages.py` | no | removed | Implemented: manifest generation/loading helpers and the generator `--moment-sources-manifest` flag were removed. | Keep manifest-driven generation out of the active path unless a separate request restores a migration tool. | Generator help no longer lists `--moment-sources-manifest`; representative moment builds do not require a manifest. |
| MSC-008 | Workbook preflight moment front-matter scan | `scripts/catalogue_preflight.py` | no | removed | Implemented: the deprecated workbook preflight script was removed after its moment front-matter checks were no longer needed. | Do not keep a parallel workbook preflight path for current moment validation. | Active JSON-source checks do not depend on external moment source scans. |
| MSC-009 | Standalone moment delete script | `scripts/delete_moment.py`; `docs-viewer/source/studio/scripts-delete-moment.md` | no | removed | Implemented: the standalone moment delete script and active script doc were removed. Studio Delete is the only current moment deletion entry point. | Keep moment deletion in `/studio/catalogue-moment/` and the catalogue write service. Do not keep a parallel deletion workflow for habit compatibility. | Studio moment delete preview/apply remains the verified deletion path; scripts docs no longer list standalone moment delete. |
| MSC-010 | Source image lookup | `source_image_file` in `moments.json`; configured projects media root; `scripts/catalogue_json_build.py`; `scripts/generate_work_pages.py` | yes | `active-live` | Moment source images still live under the configured projects media root, normally `moments/images/<source_image_file>`. The filename is metadata in `moments.json`, not prose front matter. | Keep JSON-driven source image lookup. Remove front-matter-derived image lookup from retired paths. | Moment preview reports image readiness from `moments.json`; media refresh does not parse moment prose front matter. |
| MSC-011 | Generated moment artifacts | `_moments/`; `assets/moments/index/`; `assets/data/moments_index.json`; catalogue search | yes | `derived` | Generated artifacts are derived from `moments.json`, body-only prose, source media, and generator settings. | Keep deterministic generation. Do not treat generated route stubs or JSON as source. | Representative scoped moment dry-runs show stable selected artifacts and generated output. |
| MSC-012 | Current Moment editor and import docs | `docs-viewer/source/studio/catalogue-moment-editor.md`; `docs-viewer/source/studio/scripts-catalogue-write-server.md`; `docs-viewer/source/studio/scripts-generate-work-pages.md` | yes | `active-live` | These docs describe the current JSON metadata and body-only prose model. Moment import now lives only in the Moment editor. | Keep as current docs. | Docs search routes current moment editing/import/build users to JSON metadata and body-only prose guidance. |
| MSC-013 | Stale implementation/testing docs | `docs-viewer/source/studio/studio-implementation-plan.md`; `docs-viewer/source/studio/studio-e2e-checklist.md` | no or mixed | resolved | Implemented: current-workflow wording was updated so Phase 2 and the E2E checklist no longer describe front-matter-owned metadata or front-matter preview as current behavior. Historical change-log and migration material remains as historical context. | Keep current workflow guidance aligned with `moments.json`, staged body-only prose, and the Moment editor import flow. | Docs search for moment front-matter workflow terms should not route users through current checklist or implementation-plan guidance as active workflow. |
| MSC-014 | Historical migration/request docs | `docs-viewer/source/studio/site-request-moments-prose-source-model.md`; `docs-viewer/source/studio/moments-json-migration-plan.md`; relevant entries in `docs-viewer/source/studio/site-change-log.md` | no for current workflow | `historical-context` | These docs explain previous migrations from workbook to front matter, then from front matter to JSON plus body-only prose. They are useful history only when clearly framed as completed or superseded. | Keep historical context where useful. Add or preserve wording that prevents it being mistaken for current workflow guidance. | Docs search results and page headings make clear which docs are historical requests or change-log entries. |

## Resolved Questions

- Moment prose import is body-only Markdown. Metadata is stored in catalogue source JSON, not prose front matter.
- Front-matter parsing helpers are not required for active moment prose import or build paths. Front matter no longer exists, and staged Markdown should be treated as body source.
- Generator fallback scanning of external moment source files is not needed now that `moments.json` is canonical. Prose source files are copied manually into staging.
- The Delete button on `/studio/catalogue-moment/` is the only current entry point for deleting a moment. Standalone delete behavior should not remain a parallel active workflow or habit-compatible fallback.
- Current docs should describe `moments.json`, `_docs_catalogue/moments/`, and `var/docs/catalogue/import-staging/moments/`. Migration plans and change-log entries can remain historical context; stale implementation or script guidance should be rewritten or archived.

## Suggested Cleanup Slices

Use this order for Task 3 after Task 2 confirms retention policy:

1. Done: remove front-matter detection and rejection from active moment preview/import paths. Retired source-entry and front-matter update helpers were also removed.
2. Done: remove generator fallback scanning of external moment source files and moment source manifest support.
3. Done: remove `scripts/delete_moment.py` and `docs-viewer/source/studio/scripts-delete-moment.md` so Studio delete remains the single moment deletion workflow.
4. Done: remove workbook/front-matter moment checks from deprecated preflight paths.
5. Done: rewrite stale docs while preserving clearly marked historical request and change-log context.

## Verification Matrix

| Area | Codex-run checks | Manual checks |
|---|---|---|
| Front-matter helper cleanup | Python syntax check for touched scripts; moment import preview with staged Markdown if local server is in scope | Open `/studio/catalogue-moment/?file=<moment_id>.md`, preview a staged Markdown file, and confirm import still writes prose plus JSON metadata |
| Generator scan removal | Representative `./scripts/catalogue_json_build.py --moment-id <id>` dry-run; generated output comparison for a known moment if code changes touch generation | Open a representative public moment page and confirm prose/image metadata still render |
| Delete path cleanup | Studio delete preview/apply endpoint smoke test if local server is in scope; deprecated script clean-exit check if the script is retained | Use `/studio/catalogue-moment/` delete preview for a draft test moment before any apply check |
| Docs cleanup | `./scripts/build_docs.rb --scope studio --write`; `./scripts/build_search.rb --scope studio --write`; docs profile checks | Search docs for moment front-matter workflow terms and confirm current results do not route users to retired guidance |
