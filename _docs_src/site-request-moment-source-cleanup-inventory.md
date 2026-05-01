---
doc_id: site-request-moment-source-cleanup-inventory
title: Inventory
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: site-request-moment-source-cleanup
sort_order: 10
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
| MSC-002 | Canonical body-only moment prose | `_docs_src_catalogue/moments/<moment_id>.md`; `scripts/generate_work_pages.py`; `scripts/catalogue_json_build.py` | yes | `active-live` | Canonical prose is repo-local Markdown body content. The generator renders this body with metadata from `moments.json`. | Keep body-only prose source. Do not reintroduce metadata extraction or front-matter validation for this file. | Moment build preview succeeds for a representative moment and generated moment JSON renders the canonical prose body. |
| MSC-003 | Staged moment prose import | `var/docs/catalogue/import-staging/moments/<moment_id>.md`; `scripts/studio/catalogue_write_server.py`; `scripts/catalogue_json_build.py`; Studio moment import UI | yes | `active-import-staging` | Staged prose is manually copied into staging and imported as body-only Markdown. Metadata is submitted separately and saved to `moments.json`. | Keep staged import support, but do not keep front-matter detection or rejection as an active requirement. | Import preview/apply accepts staged body Markdown, writes `_docs_src_catalogue/moments/<moment_id>.md`, and writes `moments.json`. |
| MSC-004 | Front-matter detection for body-only validation | `has_front_matter_text` and `split_front_matter_text` in `scripts/moment_sources.py`; uses in `scripts/studio/catalogue_write_server.py` and `scripts/catalogue_json_build.py` | no | `removable` | Moment prose front matter no longer exists. Detecting or rejecting it is retained compatibility behavior, not active validation. | Remove front-matter detection/rejection from active moment import and preview paths. Treat staged Markdown as body source. | Moment import preview/apply and scoped moment builds pass without calling front-matter detection helpers. |
| MSC-005 | Front-matter metadata extraction from moment prose | `parse_front_matter`, `build_moment_source_entry`, `update_moment_source_front_matter`, and related scalar helpers in `scripts/moment_sources.py` | no | `removable` | These helpers support the retired model where moment Markdown front matter owned metadata. Current metadata lives in `moments.json`, and front matter no longer exists. | Remove after confirming no active Studio path imports them. Do not keep them as migration-only by default. | Source validation, Moment editor import, scoped moment builds, and publish/unpublish flows pass without reading metadata from prose front matter. |
| MSC-006 | External moment source file scanning | `scan_moment_source_files` in `scripts/moment_sources.py`; fallback in `scripts/generate_work_pages.py` | no | `removable` | The generator still falls back to scanning external moment Markdown when `moments.json` is empty. That is not needed now that `moments.json` is canonical and prose is manually copied into staging. | Remove the fallback scan from generator behavior, then remove the scanner if no other active path remains. | A missing or empty `moments.json` should report a source-data issue rather than silently deriving moments from external Markdown. |
| MSC-007 | Moment sources manifest support | `build_moment_sources_manifest_payload`, `load_moment_sources_manifest`, `write_moment_sources_manifest`; `--moment-sources-manifest` in `scripts/generate_work_pages.py` | no | `removable` | Manifest support mirrors the older external source model and can override canonical JSON source during generation. No current Studio or build preview workflow requires it. | Remove manifest generation/loading support from the active generator path unless a separate request restores a migration tool. | Representative moment builds should not require a manifest; docs search should not route current users to manifest-driven generation. |
| MSC-008 | Workbook preflight moment front-matter scan | `scripts/catalogue_preflight.py` | no | `removable` | The deprecated workbook preflight still scans external moment Markdown and parses front matter for status validation. This belongs to retired workbook/front-matter behavior. | Remove the moment source scan from preflight behavior if the deprecated preflight script remains. | Deprecated workbook commands still exit cleanly with guidance if retained; active JSON-source checks do not depend on this scan. |
| MSC-009 | Standalone moment delete script | `scripts/delete_moment.py`; `_docs_src/scripts-delete-moment.md` | no | `removable` | Current Studio Delete button is the only moment deletion entry point. The standalone script still describes external canonical prose and front-matter-derived source images. Manual delete-script habits are not being preserved. | Remove or retire the standalone script and active script docs surface. Do not keep a parallel deletion workflow for habit compatibility. | Studio moment delete preview/apply remains the verified deletion path; docs no longer instruct users to run the standalone script for normal moment deletion. |
| MSC-010 | Source image lookup | `source_image_file` in `moments.json`; configured projects media root; `scripts/catalogue_json_build.py`; `scripts/generate_work_pages.py` | yes | `active-live` | Moment source images still live under the configured projects media root, normally `moments/images/<source_image_file>`. The filename is metadata in `moments.json`, not prose front matter. | Keep JSON-driven source image lookup. Remove front-matter-derived image lookup from retired paths. | Moment preview reports image readiness from `moments.json`; media refresh does not parse moment prose front matter. |
| MSC-011 | Generated moment artifacts | `_moments/`; `assets/moments/index/`; `assets/data/moments_index.json`; catalogue search | yes | `derived` | Generated artifacts are derived from `moments.json`, body-only prose, source media, and generator settings. | Keep deterministic generation. Do not treat generated route stubs or JSON as source. | Representative scoped moment dry-runs show stable selected artifacts and generated output. |
| MSC-012 | Current Moment editor and import docs | `_docs_src/catalogue-moment-editor.md`; `_docs_src/catalogue-moment-import.md`; `_docs_src/scripts-catalogue-write-server.md`; `_docs_src/scripts-generate-work-pages.md` | mostly yes | `active-live` | These docs mostly describe the current JSON metadata and body-only prose model. Some wording around delete behavior and generated stub normalization may need review during cleanup. | Keep as current docs, but update any remaining stale references found in later slices. | Docs search should route current moment editing/import/build users to JSON metadata and body-only prose guidance. |
| MSC-013 | Stale implementation/testing docs | `_docs_src/studio-implementation-plan.md`; `_docs_src/studio-e2e-checklist.md`; `_docs_src/scripts-delete-moment.md` | no or mixed | `docs-stale` | These docs still include front-matter-owned metadata, source preview, or standalone delete assumptions that no longer match the current moment workflow. | Rewrite or archive stale current-workflow guidance during documentation cleanup. | Docs search for moment front-matter workflow terms should not return stale pages as current guidance. |
| MSC-014 | Historical migration/request docs | `_docs_src/site-request-moments-prose-source-model.md`; `_docs_src/moments-json-migration-plan.md`; relevant entries in `_docs_src/site-change-log.md` | no for current workflow | `historical-context` | These docs explain previous migrations from workbook to front matter, then from front matter to JSON plus body-only prose. They are useful history only when clearly framed as completed or superseded. | Keep historical context where useful. Add or preserve wording that prevents it being mistaken for current workflow guidance. | Docs search results and page headings make clear which docs are historical requests or change-log entries. |

## Resolved Questions

- Moment prose import is body-only Markdown. Metadata is stored in catalogue source JSON, not prose front matter.
- Front-matter parsing helpers are not required for active moment prose import or build paths. Front matter no longer exists, and staged Markdown should be treated as body source.
- Generator fallback scanning of external moment source files is not needed now that `moments.json` is canonical. Prose source files are copied manually into staging.
- The Delete button on `/studio/catalogue-moment/` is the only current entry point for deleting a moment. Standalone delete behavior should not remain a parallel active workflow or habit-compatible fallback.
- Current docs should describe `moments.json`, `_docs_src_catalogue/moments/`, and `var/docs/catalogue/import-staging/moments/`. Migration plans and change-log entries can remain historical context; stale implementation or script guidance should be rewritten or archived.

## Suggested Cleanup Slices

Use this order for Task 3 after Task 2 confirms retention policy:

1. Done: remove front-matter detection and rejection from active moment preview/import paths. Parsing and update helpers remain only where later cleanup slices still own retired scanner/delete/preflight paths.
2. Remove generator fallback scanning of external moment source files and moment source manifest support.
3. Remove or retire `scripts/delete_moment.py` and `_docs_src/scripts-delete-moment.md` so Studio delete remains the single moment deletion workflow.
4. Remove workbook/front-matter moment checks from deprecated preflight paths or convert those paths to clean-exit guidance.
5. Rewrite stale docs while preserving clearly marked historical request and change-log context.

## Verification Matrix

| Area | Codex-run checks | Manual checks |
|---|---|---|
| Front-matter helper cleanup | Python syntax check for touched scripts; moment import preview with staged Markdown if local server is in scope | Open `/studio/catalogue-moment-import/`, preview a staged Markdown file, and confirm import still writes prose plus JSON metadata |
| Generator scan removal | Representative `./scripts/catalogue_json_build.py --moment-id <id>` dry-run; generated output comparison for a known moment if code changes touch generation | Open a representative public moment page and confirm prose/image metadata still render |
| Delete path cleanup | Studio delete preview/apply endpoint smoke test if local server is in scope; deprecated script clean-exit check if the script is retained | Use `/studio/catalogue-moment/` delete preview for a draft test moment before any apply check |
| Docs cleanup | `./scripts/build_docs.rb --scope studio --write`; `./scripts/build_search.rb --scope studio --write`; docs profile checks | Search docs for moment front-matter workflow terms and confirm current results do not route users to retired guidance |
