---
doc_id: site-change-log-2026-05
title: "Site Change Log Archive: May 2026"
added_date: 2026-05-06
last_updated: "2026-05-06 20:58"
parent_id: site-change-log
sort_order: 2000
---
# Site Change Log Archive: May 2026

This archive currently contains May 2026 entries older than the current window on the main site change log.

Return to [Site Change Log](/docs/?scope=studio&doc=site-change-log).

## [2026-05-06] Filename-derived docs HTML import ids

**Status:** implemented

**Area:** Studio / Docs HTML Import

**Summary:**
Changed staged HTML imports so new Markdown source filenames and `doc_id` values are derived from the staged HTML filename stem rather than the imported document title.

**Reason:**
Imported HTML titles can be descriptive and long, while the staged filename is usually the compact source handle the user chose for the import.

**Changes:**
`./scripts/docs/docs_html_import.py` now reports `proposed_doc_id` from the staged source filename stem while preserving the extracted HTML title as the document title.
Create writes now target `<staged-filename-stem>.md`; overwrite behavior still preserves the existing target `doc_id` and filename.

**Files changed:**

- `./scripts/docs/docs_html_import.py`
- `tests/python/test_docs_import_service.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs HTML Import User Guide](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Studio UI Rules](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
New imports produce more compact and predictable source filenames while keeping page titles intact.
If two staged files share the same meaningful stem, the existing overwrite-confirmation path will still be triggered for that generated target.

## [2026-05-03] Timestamped Library import document previews

**Status:** implemented

**Area:** Library / Studio data import

**Summary:**
Added preview-generation timestamps to Library import summary and full-document preview filenames.

**Reason:**
Repeated summary or full-content preview runs for the same `doc_id` were overwriting earlier preview files, which made it harder to compare iterations.

**Changes:**
`./scripts/docs/docs_import.py` now writes summary and full-content preview files as `<doc_id>-<timestamp>.md`, `<doc_id>-record-<n>-<timestamp>.md`, or `record-<n>-<timestamp>.md`.
Relationship tree previews keep the staged-filename-based path because they are one-file review artifacts for the whole relationship import.

**Files changed:**

- `./scripts/docs/docs_import.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)

**Impact:**
Preview runs can now be kept side by side for manual comparison.
The preview folder can accumulate more local artifacts, so stale preview cleanup remains a later workflow consideration.

## [2026-05-03] Added Library import verification to check profiles

**Status:** implemented

**Area:** Library / Studio data import / verification

**Summary:**
Completed Library import Task 8 by adding the retained Library import route smoke test to the `studio-smoke` check profile.

**Reason:**
Parser, renderer, and service verification existed, but the Studio route smoke test still needed to be part of the standard retained check runner.

**Changes:**
`tests/smoke/data_import.py` can now serve a built site root through a temporary loopback HTTP server for repeatable route checks.
`./scripts/run_checks.py --profile studio-smoke` now builds the temporary Jekyll site and runs the Library import smoke with the docs-management service blocked.

**Files changed:**

- `tests/smoke/data_import.py`
- `scripts/run_checks.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Testing](/docs/?scope=studio&doc=testing)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)

**Impact:**
Library import v1 now has retained verification for parser behavior, service handlers, and the Studio route unavailable-service state.
The smoke profile now requires Playwright browser availability, so sandboxed runs may need the same browser permission handling as other Studio smoke tests.

## [2026-05-03] Added the Studio Library import page

**Status:** implemented

**Area:** Library / Studio data import

**Summary:**
Completed Library import Task 6 by adding `/studio/import/`.

**Reason:**
The Library import parser, preview renderer, and local service endpoints existed, but there was not yet a Studio route for selecting staged Library data files and generating preview Markdown from the browser.

**Changes:**
The new Studio page lists staged Library `.json` and `.jsonl` import files from `var/docs/import-staging/library/`, shows selected file metadata, calls the docs-management preview endpoint, and renders detected import type, source export metadata, counts, issues, and preview paths.
The Library dashboard now links to the import page under Data.
Visible runtime copy is stored in `assets/studio/data/studio_config.json`.

**Files changed:**

- `studio/import/index.md`
- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `studio/library/index.md`
- `tests/smoke/data_import.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio](/docs/?scope=studio&doc=studio)

**Impact:**
Library import v1 now has a browser workflow for generating review previews.
It remains preview-only and does not apply summaries, full content, or relationship changes to canonical Library source.

## [2026-05-03] Excluded test artifacts from Jekyll

**Status:** implemented

**Area:** local development workflow / Jekyll watch

**Summary:**
Added `tests/` to the Jekyll exclusion set.

**Reason:**
Python test runs can create `tests/python/__pycache__/*.pyc`.
Those files are not site input, but Jekyll serve was watching them and could run an unnecessary regeneration pass after local checks.

**Changes:**
`_config.yml` now excludes `tests/`.
[Local Docs Data Server Reads Request](/docs/?scope=studio&doc=site-request-local-docs-data-server-reads) Task 1 is marked implemented while the larger generated docs/search server-read work remains proposed.

**Files changed:**

- `_config.yml`
- [Local Docs Data Server Reads Request](/docs/?scope=studio&doc=site-request-local-docs-data-server-reads)
- [Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)

**Impact:**
Local Python checks should no longer wake Jekyll just by creating or updating test cache files.
Generated docs/search JSON remains in the Jekyll watch surface until the local server-read path is implemented.

## [2026-05-03] Added Library import service endpoints

**Status:** implemented

**Area:** Library / Studio data import

**Summary:**
Completed Library import Task 5 by adding docs-management endpoints for staged Library import files and Markdown preview generation.

**Reason:**
The import engine can parse staged files and write review previews, but Studio needs a localhost service boundary before a UI can list files or trigger preview creation.

**Changes:**
`GET /docs/data-import/files?scope=library` now lists staged `.json` and `.jsonl` files under `var/docs/import-staging/library/`.
`POST /docs/data-import/preview` now parses the selected staged file, runs current-Library lookup, renders previews through the shared import engine, and writes them under `var/docs/import-preview/library/` unless the server is running with `--dry-run`.
Service logs include scope, staged filename, dry-run state, import type, counts, issue counts, and preview paths, but not staged payload content or document body text.
Focused service tests cover file listing, preview writing, dry-run preview reporting, and non-Library scope rejection.

**Files changed:**

- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_import_service.py`
- `scripts/run_checks.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)

**Impact:**
Library import now has a safe browser-to-filesystem boundary for local preview files.
It still does not apply summaries, relationships, or content changes to canonical Library source.

## [2026-05-03] Added Library import Markdown preview rendering

**Status:** implemented

**Area:** Library / Studio data import

**Summary:**
Completed Library import Task 4 by adding Markdown preview rendering for staged Library import files.

**Reason:**
The import workflow needs human-readable files before the Studio service and UI can provide useful review of staged summaries, full content, or relationship-tree recommendations.

**Changes:**
`./scripts/docs/docs_import.py --write-previews` now writes previews under `var/docs/import-preview/library/`.
Summary and full-content imports write one Markdown file per parsed document with document-specific front matter, import metadata, relevant warnings, and proposed summary or source-text sections.
Relationship imports write one whole-tree Markdown file with tree-level front matter and a simple candidate tree.
Focused import tests now cover per-document preview output, duplicate/missing `doc_id` filename fallback, full-content text preservation, relationship whole-tree output, dry-run preview reporting, and preview path allowlisting.

**Files changed:**

- `scripts/docs/docs_import.py`
- `tests/python/test_docs_import.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)

**Impact:**
Library import can now produce reviewable Markdown previews without touching canonical Library source.
The next task can expose staged-file parsing and preview generation through the local docs-management service.

## [2026-05-03] Added current-Library lookup to the import parser

**Status:** implemented

**Area:** Library / Studio data import

**Summary:**
Completed Library import Task 3 by adding current Library generated-doc lookup to the staged import parser.

**Reason:**
Preview generation needs to distinguish staged data that maps cleanly to current Library docs from staged records that are unknown, unpublished, missing payloads, or attached to questionable parents.

**Changes:**
`./scripts/docs/docs_import.py` now loads `assets/data/docs/scopes/library/index.json` and generated payload filenames under `assets/data/docs/scopes/library/by-id/` after staged-file parsing succeeds.
The parser adds a `current_library` summary to the report, annotates each normalized record with current existence, publication, viewability, payload, and parent state, and reports lookup problems as warnings rather than blockers.
Focused import tests now cover unknown current ids, unpublished current records, missing current payloads, missing parents, and unpublished parents.

**Files changed:**

- `scripts/docs/docs_import.py`
- `tests/python/test_docs_import.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)

**Impact:**
Library import reports are now useful enough to drive preview rendering decisions without implying that staged data is safe to apply.
The next task can consume normalized records plus current-state warnings when writing Markdown previews.

## [2026-05-03] Added the read-only Library import parser

**Status:** implemented

**Area:** Library / Studio data import

**Summary:**
Completed Library import Task 2 by adding a read-only parser for staged Library import JSON and JSONL files.

**Reason:**
The import workflow needs a stable parsing/reporting layer before preview rendering, Studio service endpoints, or any future source apply path can be implemented safely.

**Changes:**
`./scripts/docs/docs_import.py` now reads files under `var/docs/import-staging/library/`, parses JSON envelopes, JSON arrays, and JSONL document rows, detects the three v1 Library export families or minimal document records, normalizes known fields, preserves unknown file and record metadata, and returns a structured report.
Focused parser tests cover JSONL rows, JSON envelopes, full-content structural detection, minimal rows, malformed record warnings, invalid JSONL blocking, and staged path allowlisting.
The `docs` check profile now runs both export and import parser checks.

**Files changed:**

- `scripts/docs/docs_import.py`
- `tests/python/test_docs_import.py`
- `scripts/run_checks.py`
- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)

**Impact:**
Library import now has a source-read-only parser boundary that can feed current-Library lookup and Task 4 Markdown preview rendering.
It still does not write preview files, call the docs-management service, or mutate canonical Library source.

## [2026-05-03] Confirmed Library import v1 preview spec

**Status:** planned

**Area:** Library / Studio data import

**Summary:**
Expanded and confirmed [Library Import v1](/docs/?scope=studio&doc=library-import) as a permissive preview-first spec for staged JSON and JSONL data files returned from Library export or external review workflows.

**Reason:**
The export workflow now produces local data artifacts, but the next step needs a safe review path before external edits, summaries, or structure recommendations can affect canonical Library source.

**Changes:**
The spec now defines the product boundary, confirmed staging and preview roots, supported input types, document-centric Markdown preview behavior, report issue categories, Studio workflow, v1 decisions, remaining open questions, and initial implementation tasks.
The confirmed v1 imports from `var/docs/import-staging/library/`, writes one preview Markdown file per imported document under `var/docs/import-preview/library/`, keeps diagnostics in the Studio report, and does not perform apply-style flight checks.
Relationship imports are the v1 exception to document-centric previews: one staged relationships file produces one Markdown preview of the whole candidate tree.
[Library](/docs/?scope=studio&doc=library) now links to the import-preview spec from its candidate phases.

**Files changed:**

- [Library Import v1](/docs/?scope=studio&doc=library-import)
- [Library](/docs/?scope=studio&doc=library)

**Impact:**
Library import work now has a conservative v1 direction: parse and preview staged data first, accept imperfect files for inspection, and defer canonical source writes until apply behavior is explicitly scoped and validated.

## [2026-05-03] Simplified the Library dashboard route links

**Status:** implemented

**Area:** Studio / Library dashboard

**Summary:**
Aligned `/studio/library/` with the compact `/studio/catalogue/` dashboard pattern.

**Reason:**
The Library dashboard had become a routine navigation surface. Descriptive panel cards added extra reading where the page now needs direct route access.

**Changes:**
Removed the Library dashboard intro, card descriptions, and panel links.
The dashboard now keeps the Library doc count and shows two route columns: `Manage` for Library manage mode and HTML Import, and `Data` for export.

**Files changed:**

- `studio/library/index.md`
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

**Impact:**
Library admin routes are now faster to scan and visually consistent with the Catalogue dashboard.
The Library link now lands directly on `/library/?mode=manage&doc=library`.

## [2026-05-03] Added Library export v1 verification checks

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Completed Library export Task 9 by adding retained checks for the export engine, real Library export configs, and the Studio Library export route.

**Reason:**
The v1 export path now spans config, CLI, generated docs data, local service integration, and Studio UI. It needs repeatable checks before the first iteration is considered stable.

**Changes:**
`tests/python/test_docs_export.py` now verifies config loading, selected-document descendant resolution, deterministic JSONL output for a fixed run time, and representative dry-runs for all three v1 Library export configs.
`tests/smoke/data_export.py` smoke-checks `/studio/export/` route readiness, config loading, document-list rendering, archive exclusion, and disabled run behavior when the docs-management service is unavailable.
The `docs` profile in `./scripts/run_checks.py` now runs the export checks before regenerating Studio docs and search payloads.

**Files changed:**

- `tests/python/test_docs_export.py`
- `tests/smoke/data_export.py`
- `scripts/run_checks.py`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)

**Impact:**
Library export v1 now has a repeatable verification path for engine behavior and basic UI load behavior.
The smoke test is intentionally light and does not replace a manual Studio export run through the local write service.

## [2026-05-03] Switched Library export filename timestamps to local time

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Changed Library export filename timestamps to use the local runtime timezone while keeping export metadata timestamps in UTC.

**Reason:**
Studio-facing output filenames should match the operator's local clock. The previous UTC filename timestamp appeared one hour behind local time during British Summer Time.

**Changes:**
`./scripts/docs/docs_export.py` now separates UTC `generated_at` metadata from the local timestamp used in `{timestamp}` filename substitution.
Docs now call out that `output.timestamp_format` formats the local filename timestamp, not the UTC metadata timestamp.

**Files changed:**

- `scripts/docs/docs_export.py`
- `tests/python/test_docs_export.py`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)

**Impact:**
Export paths shown in Studio now align with the local machine clock, while export payload metadata remains timezone-stable.

## [2026-05-03] Documented Library export v1 runtime usage

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Completed Library export Task 8 by consolidating runtime and config usage documentation for the v1 export path.

**Reason:**
The export workflow now has config, CLI, service, and Studio UI pieces. The docs needed one coherent explanation of how those pieces fit together before the final verification task.

**Changes:**
Library export docs now describe the three v1 entry points: Studio page, docs-management endpoint, and CLI.
Config docs clarify that export patterns live in `library_export_configs.json`, while `studio_config.json` only owns route/data/copy lookup.
Library data-model docs now distinguish source-controlled export configs from ignored local export artifacts.

**Files changed:**

- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Studio](/docs/?scope=studio&doc=studio)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Impact:**
The v1 operational contract is now documented without changing export behavior.
The remaining Library export task is verification of the completed workflow.

## [2026-05-03] Added Library export validation and reporting

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Completed Library export Task 7 by adding explicit v1 validation decisions and clearer export issue reporting.

**Reason:**
The export infrastructure was working, but needed a concrete blocker-versus-warning contract before treating v1 as stable enough to verify and document end to end.

**Changes:**
The export engine now validates config shape, target format and record-shape combinations, field mappings, output paths, source-text transforms, truncation limits, selected document ids, required fields, and empty selections before writing.
Reports now include `failed` counts, `skipped_summary`, and `issue_counts`.
The Studio Library export result UI now distinguishes warnings from blocking issues and shows failed counts.

**Files changed:**

- `scripts/docs/docs_export.py`
- `scripts/docs/docs_management_server.py`
- `assets/studio/js/data-export.js`
- `assets/studio/data/studio_config.json`
- `tests/python/test_docs_export.py`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

**Impact:**
Bad configs, bad selections, and unsafe output paths now fail before export writes, while expected skipped documents and truncation remain visible as warnings.
Batching and total character limits remain deferred until real usage requires them.

## [2026-05-03] Flattened Library export file paths

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Changed Library export output paths to put the timestamp in the filename rather than in a per-run directory.

**Reason:**
A flat scope directory is easier to scan and copy for manual external use.

**Changes:**
Export configs now write files such as `var/docs/exports/library/library-document-summaries-20260503-161507.jsonl`.
The export config schema and docs now require `var/docs/exports/{scope}/{export_id}-{timestamp}.json` or `.jsonl`.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/library_export_configs.schema.json`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)

**Impact:**
Export artifacts remain under the same allowlisted root, but repeated runs now collect directly under the scope folder.

## [2026-05-03] Split summary metadata exports from full-content exports

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Changed the `library-document-summaries` export so it no longer includes full document body text.

**Reason:**
Document summaries should be a summary metadata export. Body text for generation or external analysis belongs to the full-content export.

**Changes:**
The summary export config now writes identity, parent, headings, current summary, `last_updated`, and `viewable` only.
Its body-text field mapping, character limit, and truncation behavior were removed.
Library export and semantic-enrichment docs now point body-text use cases to `library-full-document-content`.

**Files changed:**

- `assets/studio/data/library_export_configs.json`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Library Semantic Enrichment Spec](/docs/?scope=studio&doc=library-semantic-enrichment-spec)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)

**Impact:**
Summary audits can run without duplicating full content in the output, while full text remains available through the dedicated full-content config.

## [2026-05-03] Added Library export service endpoint

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Added the local docs-management endpoint that lets Studio run configured Library exports.

**Reason:**
The Library export page could select configs and documents, but needed a loopback-only service path to create export files without giving the browser arbitrary filesystem write access.

**Changes:**
`POST /docs/export` now calls the shared export engine in-process, validates config id, scope, explicit `doc_ids`, `select_all`, and `missing_summary_only`, and writes only through the export engine's `var/docs/exports/` path allowlist.
The Studio transport layer exposes the endpoint, and `/studio/export/` now probes the docs-management service, enables Run when available, posts selected docs/config options, and displays output path, format, counts, warnings, and errors.

**Files changed:**

- `scripts/docs/docs_management_server.py`
- `assets/studio/js/studio-transport.js`
- `assets/studio/js/data-export.js`
- `studio/export/index.md`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)

**Impact:**
The Library export workflow is now end-to-end from Studio selection to generated file output.
The main remaining risk is validation/reporting depth for unusual configs or missing required fields, which is tracked by the next Library export task.

## [2026-05-03] Added Library export selection page

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Added `/studio/export/` as the first Studio UI slice for Library exports.

**Reason:**
Library export now has configs and a read-only engine, but it also needs a clear document-selection surface before adding the service-backed run endpoint.

**Changes:**
The Library dashboard now links to Export.
The new page loads enabled Library export configs, reads the generated Library docs index, renders a hierarchical checkbox list in Docs Viewer order, excludes `archive` descendants, marks `viewable: true` docs with a small green dot, and supports select-all, clear, missing-summary filtering, descendant selection, and ancestor indeterminate states.
The run button stays disabled until the Task 6 loopback endpoint is added.

**Files changed:**

- `studio/export/index.md`
- `studio/library/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)
- [Studio](/docs/?scope=studio&doc=studio)

**Impact:**
The export workflow now has a concrete Studio selection surface that matches the Library hierarchy and avoids adding row-level clutter before real export runs exist.
Export execution is still intentionally unavailable from the page, so Task 6 must wire the selected config and explicit `doc_id` list into a local service endpoint before this becomes an end-to-end Studio workflow.

## [2026-05-03] Added Docs Viewer export source-text extraction

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Extended the Docs Viewer export engine with deterministic plain-text extraction from rendered docs payload HTML.

**Reason:**
Summary and full-content Library export configs need body text suitable for LLM upload and external review without exposing raw HTML.

**Effect:**
`source_text` field mappings now convert rendered HTML into text with paragraphs, headings, lists, quote text, optional code omission, and character truncation. Image handling is config-driven at the field-mapping level, and full-content exports extract available image/SVG text while emitting `[image]` for otherwise empty visuals.

**Affected files/docs:**

- `scripts/docs/docs_export.py`
- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/library_export_configs.schema.json`
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Benefits:**
The summary and full-content export configs are now runnable, and image/SVG semantics are preserved when the source provides useful text.

**Risks:**
The extractor is intentionally text-oriented; it does not attempt visual interpretation of images or diagrams without author-provided text.

## [2026-05-03] Added read-only Docs Viewer export engine

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Added a read-only Docs Viewer export CLI that runs configured export patterns against generated docs payloads.

**Reason:**
Library export needs a reusable engine before adding the Studio page and local service endpoint.

**Effect:**
`./scripts/docs/docs_export.py` loads `library_export_configs.json`, resolves selected Library docs, applies supported field mappings, writes exports under `var/docs/exports/` when `--write` is passed, and prints a structured report. The parent-child relationships config is runnable now. Configs that require `source_text` return a clear validation error until the source-text extraction task is implemented.

**Affected files/docs:**

- `scripts/docs/docs_export.py`
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Benefits:**
The export flow now has a reusable, config-driven execution path that can be called by later Studio UI and service work.

**Risks:**
The first engine intentionally stops before plain-text extraction, batching, and Studio service integration, so summary/full-content configs are not fully runnable until the next task.

## [2026-05-03] Added JSON Schema adoption change request

**Status:** documented

**Area:** config / validation

**Summary:**
Added a change request for selective JSON Schema adoption.

**Reason:**
The Library export config schema raised the question of whether similar schema contracts would help elsewhere in the repo.

**Effect:**
The new request recommends using schemas selectively for compact hand-edited config contracts, with search policy and the catalogue field registry as the first likely candidates. It explicitly avoids broad schema adoption for generated payloads or unstable canonical records.

**Affected files/docs:**

- [JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Config](/docs/?scope=studio&doc=config)
- [Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)
- [Catalogue Field Registry Review](/docs/?scope=studio&doc=catalogue-field-registry-review)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Benefits:**
The repo now has a clear backlog item for where schemas are likely to add value, without committing to schema everything.

**Risks:**
Schema adoption still needs to stay disciplined so it does not duplicate unstable implementation details or replace semantic validation scripts.

## [2026-05-03] Added initial Library export configs

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Added the first three source-controlled Library export config patterns.

**Reason:**
The export workflow needs concrete configs before the read-only export engine and Studio UI can be built against the schema.

**Effect:**
The config file now defines enabled patterns for parent-child relationships, document summaries, and full document content. Relationship export uses envelope JSON for whole-corpus structure review. Summary and full-content exports use JSONL document rows for multi-document external review and LLM-upload-oriented workflows.

**Affected files/docs:**

- `assets/studio/data/library_export_configs.json`
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Config](/docs/?scope=studio&doc=config)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Benefits:**
The next exporter task has real config fixtures for field mapping, selection behavior, output format, and limits.

**Risks:**
The configs are not runnable until the export engine implements the declared transforms, relationship fields, filtering rules, and output writer.

## [2026-05-03] Defined Library export config schema

**Status:** implemented

**Area:** Library / Studio docs export

**Summary:**
Added the first formal JSON Schema for Library export config files and documented the config contract.

**Reason:**
Library export needs a stable config-driven boundary before adding initial export configs, exporter code, or Studio UI.

**Effect:**
Export patterns now have a defined shape for scope support, target format, output path pattern, selection rules, limits, run metadata, document field mappings, and transform names. The schema is Library-first but keeps scope support extensible for future Docs Viewer scopes.

**Affected files/docs:**

- `assets/studio/data/library_export_configs.schema.json`
- [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Config](/docs/?scope=studio&doc=config)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

**Benefits:**
The next task can add concrete export configs against a reviewed shape, and the later Studio UI/export engine can avoid hardcoded field sets.

**Risks:**
The schema validates static config shape only; runtime validation still has to check selected docs, source-derived required fields, and resolved output paths.

## [2026-05-03] Added minute-precision Docs Viewer source timestamps

**Status:** implemented

**Area:** Docs Viewer / Studio docs management

**Summary:**
Docs Viewer management writes now record new `added_date` values and changed `last_updated` values with hour/minute precision.

**Reason:**
Library export workflows need a more useful source-version marker than a date-only field, and minute precision is generally useful for same-day docs maintenance.

**Effect:**
Newly created or imported docs write `added_date` and `last_updated` as `YYYY-MM-DD HH:MM`. Metadata, viewability, move/restore, and archive writes preserve existing `added_date` and refresh `last_updated` to the current minute. Existing date-only docs remain valid and do not need migration.

**Affected files/docs:**

- `scripts/docs/docs_management_server.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Shared Patterns](/docs/?scope=studio&doc=data-models-shared)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Library Export v1](/docs/?scope=studio&doc=library-export)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Added catalogue source/registry drift verification

**Status:** implemented

**Area:** catalogue pipeline / checks

**Summary:**
Extended the catalogue field-registry verifier so it also checks source-schema coverage and optional source serialization behavior.

**Reason:**
The canonical source serializers and field-aware build registry are intentionally separate contracts, but that separation made it easy to add a source field without registry coverage or add a registry field that the source schema did not know about.

**Effect:**
`./scripts/verify_catalogue_field_registry.py` now fails for unknown registry fields, uncovered editable source fields, duplicate field ownership, and identity/derived fields misclassified as normal metadata edits. It also checks omit-empty behavior for `project_subfolder`, `details_subfolder`, and `sort_order`. The catalogue check profile inherits the stronger guardrail through the existing verifier wrapper.

**Affected files/docs:**

- `scripts/catalogue_source.py`
- `scripts/moment_sources.py`
- `scripts/verify_catalogue_field_registry.py`
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Catalogue Source And Registry Drift Verification Request](/docs/?scope=studio&doc=site-request-catalogue-source-registry-drift-verification)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Added Studio Audits page and audit service

**Status:** implemented

**Area:** Studio runtime / checks

**Summary:**
Added `/studio/audits/`, a loopback-only audit service, and structured JSON output for the Studio ready-state audit.

**Reason:**
Important maintenance audits were still easy to forget even after the ready-state audit was added to `./scripts/run_checks.py --profile quick`. Studio needed a visible place to run and inspect key audit results from the normal local workflow.

**Effect:**
The Studio home Resources section now links to Audits. The Audits page probes the local service, lists the allowlisted `studio-ready-state` audit, runs it with a command button, renders counts/findings, and maintains the shared `data-studio-ready` / `data-studio-busy` contract. `bin/dev-studio` now starts `scripts/studio/audit_service.py` on port `8790` by default.

**Affected files/docs:**

- `bin/dev-studio`
- `scripts/audit_studio_ready_state.py`
- `scripts/studio/audit_service.py`
- `assets/studio/js/studio-audits.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `studio/index.md`
- `studio/audits/index.md`
- [Studio Audits](/docs/?scope=studio&doc=studio-audits)
- [Studio Audit Service](/docs/?scope=studio&doc=scripts-studio-audit-service)
- [Studio Audits Page Request](/docs/?scope=studio&doc=site-request-studio-audits-page)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Added Studio ready-state audit hardening

**Status:** implemented

**Area:** Studio runtime / checks

**Summary:**
Added a read-only Studio ready-state audit and included it in the lightweight `quick` check profile.

**Reason:**
The static ready-state framework gives low-behavior Studio pages a useful baseline, but future async features should not accidentally keep using static readiness after adding data loads, service checks, route commands, or extra route scripts.

**Effect:**
`./scripts/audit_studio_ready_state.py --strict` now checks Studio route templates for ready/busy baseline attributes, static/dashboard marker mixups, dashboard loader wiring, and static-route drift. `./scripts/run_checks.py --profile quick` runs the audit in strict mode so this contract is enforced during normal lightweight verification.

**Affected files/docs:**

- `scripts/audit_studio_ready_state.py`
- `scripts/run_checks.py`
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Added static ready-state framework to Studio dashboards and references

**Status:** implemented

**Area:** Studio runtime / smoke testing

**Summary:**
Adopted the shared ready-state contract on the remaining lower-priority Studio landing, dashboard, and UI catalogue reference pages.

**Reason:**
These pages do not currently have complex route behavior, but they still need a visible page-root framework so future dashboard metrics, reference demos, or route-level controls extend the shared `data-studio-ready` / `data-studio-busy` contract instead of inventing local readiness markers.

**Effect:**
The Studio home page and UI catalogue pages now use a generic static-route initializer with `landing` or `reference` mode. Catalogue, Library, Analytics, and Search dashboards now mark busy while lightweight metric hydration runs and ready after those reads settle. The ready-state request checklist now has every tracked Studio route adopted.

**Affected files/docs:**

- `assets/studio/js/studio-dashboard.js`
- `assets/studio/js/studio-static-route.js`
- `studio/index.md`
- `studio/catalogue/index.md`
- `studio/library/index.md`
- `studio/analytics/index.md`
- `studio/search/index.md`
- `studio/ui-catalogue/index.md`
- `studio/ui-catalogue/button/index.md`
- `studio/ui-catalogue/input/index.md`
- `studio/ui-catalogue/list/index.md`
- `studio/ui-catalogue/panel/index.md`
- [Studio](/docs/?scope=studio&doc=studio)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Completed primary Studio ready-state route adoption

**Status:** partially implemented

**Area:** Studio runtime / smoke testing

**Summary:**
Adopted the shared `data-studio-ready` / `data-studio-busy` route contract on Series Tag Editor, Series Tags, Studio Works, Tag Aliases, Tag Groups, and Tag Registry.

**Reason:**
These were the remaining primary async or service-backed Studio routes in the ready-state request. They load tag data, assignment data, generated catalogue indexes, group descriptions, or work indexes before route state is stable, and several run local write-server commands.

**Effect:**
`#seriesTagEditorRoot`, `#series-tags`, `#worksStudioRoot`, `#tag-aliases`, `#tag-groups`, and `#tag-registry` now expose route, ready, busy, mode, service availability where applicable, and record-loaded attributes. Primary async and service-backed Studio routes now have the shared smoke-test readiness contract; only lower-priority dashboards, landing pages, and reference pages remain.

**Affected files/docs:**

- `assets/studio/js/series-tag-editor-page.js`
- `assets/studio/js/tag-studio.js`
- `assets/studio/js/series-tags.js`
- `assets/studio/js/studio-works.js`
- `assets/studio/js/tag-aliases.js`
- `assets/studio/js/tag-groups.js`
- `assets/studio/js/tag-registry.js`
- `studio/series-tag-editor/index.md`
- `studio/series-tags/index.md`
- `studio/studio-works/index.md`
- `studio/tag-aliases/index.md`
- `studio/tag-groups/index.md`
- `studio/tag-registry/index.md`
- [Tag Editor](/docs/?scope=studio&doc=tag-editor)
- [Series Tags](/docs/?scope=studio&doc=series-tags)
- [Studio Works](/docs/?scope=studio&doc=studio-works)
- [Tag Aliases](/docs/?scope=studio&doc=tag-aliases)
- [Tag Groups](/docs/?scope=studio&doc=tag-groups)
- [Tag Registry](/docs/?scope=studio&doc=tag-registry)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Extended Studio ready-state contract to bulk and docs tools

**Status:** partially implemented

**Area:** Studio runtime / smoke testing

**Summary:**
Adopted the shared `data-studio-ready` / `data-studio-busy` route contract on Bulk Add Work, Docs Broken Links, Docs Import, and Project State.

**Reason:**
These routes perform async config, service, file-list, workbook, audit, import, or report work before they are stable for interaction. They should expose the same route-root readiness signal as the catalogue editors and operational catalogue reports.

**Effect:**
`#bulkAddWorkRoot`, `#docsBrokenLinksRoot`, `#docsHtmlImportRoot`, and `#projectStateRoot` now expose route, ready, busy, mode, service availability, and record-loaded attributes. Empty and unavailable states are marked ready once stable, and preview, audit, import, and report commands synchronize route busy state.

**Affected files/docs:**

- `assets/studio/js/bulk-add-work.js`
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/project-state.js`
- `studio/bulk-add-work/index.md`
- `studio/docs-broken-links/index.md`
- `studio/docs-import/index.md`
- `studio/project-state/index.md`
- [Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)
- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Extended Studio ready-state contract to operational catalogue routes

**Status:** partially implemented

**Area:** Studio runtime / smoke testing

**Summary:**
Adopted the shared `data-studio-ready` / `data-studio-busy` route contract on Studio Activity, Studio Activity, Catalogue Drafts, and Catalogue Field Registry.

**Reason:**
These read/reporting routes load service-backed feeds, source-family data, or registry JSON before they are stable for smoke-test interaction. They should expose the same route-root readiness signal as the catalogue editors.

**Effect:**
`#buildActivityRoot`, `#catalogueActivityRoot`, `#catalogueStatusRoot`, and `#fieldRegistryReviewRoot` now expose route, ready, busy, mode, service availability, and record-loaded attributes. Empty and unavailable states are marked ready once stable, and list/registry routes can be smoke-tested without waiting on route-specific visible status text.

**Affected files/docs:**

- `assets/studio/js/activity.js`
- `assets/studio/js/activity.js`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-field-registry-review.js`
- `studio/activity/index.md`
- `studio/activity/index.md`
- `studio/catalogue-status/index.md`
- `studio/catalogue-field-registry/index.md`
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status)
- [Catalogue Field Registry Review](/docs/?scope=studio&doc=catalogue-field-registry-review)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-03] Extended Studio ready-state contract to catalogue editors

**Status:** partially implemented

**Area:** Studio runtime / smoke testing

**Summary:**
Adopted the shared `data-studio-ready` / `data-studio-busy` route contract on the catalogue work-detail, series, and moment editors.

**Reason:**
These routes have async initial selections, service-backed lookup reads, build previews, import flows, and command buttons. Smoke tests need the same stable route-root signal already available on the work editor.

**Effect:**
`#catalogueWorkDetailRoot`, `#catalogueSeriesRoot`, and `#catalogueMomentRoot` now expose route, ready, busy, mode, service availability, and record-loaded attributes. Initial query-param selection/import setup is awaited before ready becomes true, and route command flags synchronize busy state during save, create, publish, unpublish, refresh, import, and delete flows.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `studio/catalogue-work-detail/index.md`
- `studio/catalogue-series/index.md`
- `studio/catalogue-moment/index.md`
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Added Studio ready-state contract first slice

**Status:** partially implemented

**Area:** Studio runtime / smoke testing

**Summary:**
Added the shared Studio route-state helper and adopted `data-studio-ready` / `data-studio-busy` on the catalogue work editor route.

**Reason:**
Studio smoke tests previously had to wait on route-specific user-facing status text. The work editor is async-rendered and can load focused records, lookup payloads, media previews, detail sections, and public-update previews after the route shell becomes visible.

**Effect:**
`#catalogueWorkRoot` now exposes stable route attributes for ready, busy, mode, service availability, and record-loaded state. Initial `?work=<work_id>` route selection is awaited before the route is marked ready, and route-level command flags synchronize the busy attribute.

**Affected files/docs:**

- `assets/studio/js/studio-route-state.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- `studio/catalogue-work/index.md`
- `tests/smoke/catalogue_work_ready_state.py`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Added filtering and sorting to Docs Broken Links

**Status:** implemented

**Area:** Studio docs maintenance UI

**Summary:**
Updated `/studio/docs-broken-links/` so audit results use count-bearing `all`, `not found`, and `wrong title` filter pills, default to the `not found` view, and sort by `from page` ascending by default.

**Reason:**
The old aggregate issue summary made it harder to focus the operational list on missing docs links first, and the fixed row order made larger reports slower to scan.

**Effect:**
The summary sentence is replaced by filter pills, all result columns are sortable, and `from page` is now the second column before `linked page`.

**Affected files/docs:**

- `studio/docs-broken-links/index.md`
- `assets/studio/css/studio.css`
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/data/studio_config.json`
- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Removed work-detail route layout from per-work JSON

**Status:** implemented

**Area:** catalogue runtime payload

**Summary:**
Removed the redundant `layout: work_details` field from nested detail records in generated `assets/works/index/<work_id>.json` payloads.

**Reason:**
Work and work-detail route layouts are fixed by Jekyll collection defaults rather than per-record runtime JSON. Keeping `layout` in nested detail records implied a choice that does not exist and added unnecessary generated payload weight.

**Effect:**
Per-work JSON detail entries now carry only the fields used by public work/detail runtime consumers: identity, title, and dimensions. Section metadata remains section-level, and route layout remains configuration-owned.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- `assets/works/index/*.json`
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Verified catalogue media-section migration and runtime output

**Status:** implemented

**Area:** catalogue build / Studio verification

**Summary:**
Completed the final verification pass for the catalogue media-section migration across source data, generated work JSON, focused lookup files, Studio create/edit payloads, and the Jekyll build path.

**Reason:**
The migrated detail schema affects canonical source records, generated public work JSON, Studio editing payloads, and field-aware build scoping, so closeout needed evidence that the runtime contract stayed stable after the write migration.

**Effect:**
The migration dry-run now reports no pending source changes, target source validation passes, representative catalogue build previews select the expected outputs, and generated runtime payloads preserve existing section labels without carrying legacy detail `project_subfolder`.

**Affected files/docs:**

- [Catalogue Media Section Schema Request](/docs/?scope=studio&doc=site-request-catalogue-media-section-schema)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Documented migrated catalogue media-section contract

**Status:** implemented

**Area:** documentation / catalogue data model

**Summary:**
Updated the stable catalogue source, build, lookup, and field-registry docs to describe the migrated work-detail media-section schema.

**Reason:**
After the source migration and generated work JSON rebuild, the active contract no longer uses detail `project_subfolder`. Stable reference docs needed to distinguish source-media fields, public section metadata, Studio lookup payloads, and generated per-work runtime JSON.

**Effect:**
The documentation now states that detail source records use `details_subfolder`, `section_id`, `section_title`, optional `sort_order`, and `project_filename`; generated work JSON keeps section metadata at section level; and lookup payloads expose the target shape without legacy detail `project_subfolder`.

**Affected files/docs:**

- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- [Catalogue Field Registry Review](/docs/?scope=studio&doc=catalogue-field-registry-review)
- [Catalogue Media Section Schema Request](/docs/?scope=studio&doc=site-request-catalogue-media-section-schema)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Fixed catalogue media-section legacy lookup IDs

**Status:** implemented

**Area:** catalogue build / Studio lookup

**Summary:**
Fixed legacy work-detail source rows so derived work JSON and Studio lookup payloads synthesize migration-equivalent `section_id` values such as `00001-1` instead of reusing legacy `project_subfolder` labels such as `details`.

**Reason:**
Before the source migration is written, canonical detail rows still carry legacy `project_subfolder`. The read fallback was preserving that value as the generated section key, which made public work JSON and Studio current-record panels disagree with the locked `section_id` format.

**Effect:**
`scripts/generate_work_pages.py` and `scripts/catalogue_lookup.py` now share the same legacy section-resolution helper from `scripts/catalogue_source.py`. Studio detail lookup records include derived `section_id`, `section_title`, and `details_subfolder`, so the read-only current-record field is populated even before the source migration write.

**Affected files/docs:**

- `scripts/catalogue_source.py`
- `scripts/catalogue_lookup.py`
- `scripts/generate_work_pages.py`
- [Catalogue Lookup Export](/docs/?scope=studio&doc=scripts-catalogue-lookup)
- [Catalogue Media Section Schema Request](/docs/?scope=studio&doc=site-request-catalogue-media-section-schema)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Updated catalogue media-section Studio surfaces

**Status:** implemented

**Area:** Studio catalogue editing

**Summary:**
Updated the work and work-detail editors plus workbook import previews to use the separated source media and detail-section fields.

**Reason:**
The detail `project_subfolder` field was split into `details_subfolder`, `section_id`, `section_title`, and `sort_order` so source image paths and public section labels are no longer overloaded.

**Effect:**
Work records can persist optional `project_subfolder` source metadata. Work-detail save/create payloads use `details_subfolder`, `section_title`, and `sort_order`; `section_id` is generated by the server and displayed read-only. Workbook import previews now expose generated section-id grouping before apply.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-fields.js`
- `assets/studio/js/catalogue-work-detail-fields.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/data/studio_config.json`
- `scripts/catalogue_workbook_import.py`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Media Section Schema Request](/docs/?scope=studio&doc=site-request-catalogue-media-section-schema)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-02] Removed public site map page

**Status:** implemented

**Area:** site route cleanup

**Summary:**
Removed the retired `/site_map/` page and its dedicated sitemap data build path.

**Reason:**
The page is no longer required, and its generated `_data/sitemap.yml` source only supported that route plus a now-obsolete audit precheck.

**Effect:**
The public site no longer builds `/site_map/`. Studio Works no longer links to it, `studio_config.json` no longer advertises a site-map route, and the site consistency audit now keeps generated link/query checks without validating the removed sitemap data file.

**Affected files/docs:**

- `site_map.html`
- `_data/sitemap.yml`
- `scripts/build_sitemap_data.py`
- `studio/studio-works/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/audit_site_consistency.py`
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Closed moment source cleanup

**Status:** implemented

**Area:** moment source cleanup

**Summary:**
Closed the moment source cleanup request after verifying the current JSON metadata plus body-only prose workflow.

**Reason:**
The implementation slices had already removed front-matter detection, external moment source scanning, manifest support, standalone moment deletion, deprecated preflight coupling, and stale current-workflow docs. The request needed a final verification record before being marked complete.

**Effect:**
Representative moment build previews, generator dry-runs, catalogue search dry-run, staged body-only import preview, and moment delete preview now document the close-out state. Destructive import-apply and delete-apply checks were intentionally left as manual checks for a prepared test moment.

**Affected files/docs:**

- [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed retired workbook scripts

**Status:** implemented

**Area:** catalogue compatibility cleanup

**Summary:**
Removed the remaining retired workbook-led script files and narrowed workbook code to the Studio bulk-import path.

**Reason:**
The only current Excel requirement is the configured Studio bulk import for new works and new work details. Keeping unrelated workbook-led commands or generic workbook helpers preserved compatibility artifacts that no longer support the current Studio workflow.

**Effect:**
Workbook-specific parsing now lives beside `scripts/catalogue_workbook_import.py`. The retired build, media-copy, export, comparison, preflight, recent-backfill, and standalone work-delete scripts were removed. Build-activity summaries no longer expose workbook change groups, and docs now route current catalogue work through Studio, canonical source JSON, and `catalogue_json_build.py`.

**Affected files/docs:**

- `scripts/catalogue_workbook_import.py`
- `scripts/catalogue_source.py`
- `scripts/generate_work_pages.py`
- `scripts/catalogue_json_build.py`
- `scripts/activity_log.py`
- `assets/studio/js/activity.js`
- `AGENTS.md`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Rewrote stale moment workflow docs

**Status:** implemented

**Area:** documentation / moment source cleanup

**Summary:**
Updated current Studio planning and testing docs so they no longer describe moment front matter as the active metadata model.

**Reason:**
The current moment workflow uses canonical JSON metadata in `assets/studio/data/catalogue/moments.json` and body-only prose in `_docs_catalogue/moments/`. Some older current-workflow docs still described front-matter preview and front-matter-owned metadata from an earlier source model.

**Effect:**
The Studio implementation plan now frames the old Phase 2 source model as superseded by canonical JSON metadata plus body-only prose. The Studio E2E checklist now tests staged prose import, submitted metadata, canonical draft metadata writes, and publish/save follow-through. The Moment import docs now refer to resolved moment metadata rather than source metadata.

**Affected files/docs:**

- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)
- [Studio E2E Checklist](/docs/?scope=studio&doc=new-pipeline-studio-e2e-checklist)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed moment front-matter preflight checks

**Status:** implemented

**Area:** deprecated preflight / moment source cleanup

**Summary:**
Removed the last front-matter parsing dependency from the deprecated workbook preflight path.

**Reason:**
Moment metadata is canonical in `assets/studio/data/catalogue/moments.json`, and moment prose is body-only Markdown. The workbook preflight was still scanning external moment Markdown files and parsing front matter for status validation, which preserved a retired source model.

**Effect:**
`scripts/catalogue_preflight.py` no longer imports moment source helpers, resolves an external moments root, or validates moment front matter. The unused `parse_front_matter` helper was removed from `scripts/moment_sources.py`.

**Affected files/docs:**

- `scripts/catalogue_preflight.py`
- `scripts/moment_sources.py`
- [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed standalone moment delete script

**Status:** implemented

**Area:** Studio / moment source cleanup

**Summary:**
Removed the standalone moment deletion script and its active script reference.

**Reason:**
Moment deletion is now a Studio-only workflow through `/studio/catalogue-moment/`. Keeping a separate delete command preserved an obsolete external-prose and front-matter-derived source-image model.

**Effect:**
`scripts/delete_moment.py` and its script doc were removed. The Scripts overview no longer lists standalone moment deletion. Current deletion behavior is owned by the Studio catalogue write service and the Moment editor delete flow.

**Affected files/docs:**

- `scripts/delete_moment.py`
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed moment external scan and manifest paths

**Status:** implemented

**Area:** generator / moment source cleanup

**Summary:**
Removed generator fallback scanning of external moment Markdown files and removed moment source manifest support.

**Reason:**
`assets/studio/data/catalogue/moments.json` is the canonical moment metadata source, and moment prose is resolved from `_docs_catalogue/moments/`. External Markdown scanning and manifest-driven generation preserved an older source model that is no longer part of the Studio workflow.

**Effect:**
`generate_work_pages.py` now builds moment records only from canonical JSON metadata and repo-local prose paths. The `--moment-sources-manifest` flag was removed, `scripts/moment_sources.py` no longer exposes source-file scanner or manifest helpers, and empty moment metadata now reports no moment metadata rather than deriving records from external files.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- `scripts/moment_sources.py`
- [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed active moment front-matter rejection

**Status:** implemented

**Area:** Studio / moment source cleanup

**Summary:**
Removed front-matter detection and rejection from active moment preview/import paths.

**Reason:**
Moment prose front matter no longer exists. Moment metadata is canonical in `assets/studio/data/catalogue/moments.json`, and staged prose is imported as Markdown body source.

**Effect:**
Moment build previews and Studio staged prose imports no longer call the moment front-matter detection helper or reject Markdown that starts with a front-matter-shaped block. Staged prose still goes through the existing file, UTF-8, null-byte, blank-file, overwrite, metadata, and write-root checks. Retired front-matter parsing helpers were removed in later cleanup slices.

**Affected files/docs:**

- `scripts/catalogue_json_build.py`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Moment Source Cleanup](/docs/?scope=studio&doc=site-request-moment-source-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-moment-source-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Verified compatibility cleanup output stability

**Status:** implemented

**Area:** generator / compatibility cleanup

**Summary:**
Completed the generated-output stability verification pass for the catalogue compatibility cleanup.

**Reason:**
The generator projection cleanup removed workbook-shaped internal access from `generate_work_pages.py`, so the generated artifacts needed a targeted stability check before moving on.

**Effect:**
Representative generated route stubs, per-record JSON, aggregate indexes, recent index output, Studio storage index output, deprecated command guidance, temp Studio lookup export shape, and field registry rules were verified. The recent index comparison explicitly seeded the temp output with the checked-in recent index because that artifact intentionally preserves existing recent-publication state.

**Affected files/docs:**

- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed generator row projection

**Status:** implemented

**Area:** generator / compatibility cleanup

**Summary:**
Removed the retained workbook-shaped row projection from `generate_work_pages.py`.

**Reason:**
After source write-back moved to canonical source records and proxy worksheet/cell wrappers were removed, the remaining header-indexed row lists were only preserving an old workbook implementation shape inside the JSON-source generator.

**Effect:**
The generator now builds work, series, work-detail, and index artifacts from canonical source records directly. Per-series sort rules are read from `series.<series_id>.sort_fields`, and generator-updated work/detail status, published dates, and image dimensions are still written back to canonical source records during write runs.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed generator proxy worksheet wrapper

**Status:** implemented

**Area:** generator / compatibility cleanup

**Summary:**
Removed the internal proxy worksheet/cell wrapper from `generate_work_pages.py`.

**Reason:**
After source write-back moved onto canonical source records, the proxy worksheet objects no longer represented a real persistence boundary. They were only preserving a workbook-shaped abstraction around generator read loops.

**Effect:**
The generator now uses mutable row-list projections for the remaining header-indexed read loops. Series iteration no longer uses any proxy row wrapper, and work/detail same-run status and dimension updates mutate those row lists directly while also updating canonical source records.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Narrowed generator source write-back

**Status:** implemented

**Area:** generator / compatibility cleanup

**Summary:**
Changed `generate_work_pages.py` so mutable source updates are written directly to canonical source records instead of rebuilding source JSON from the internal sheet-like projection.

**Reason:**
The live JSON generator still has retained worksheet-shaped read loops. Source write-back was unnecessarily coupled to that projection, which kept workbook-era helper code in the persistence path.

**Effect:**
Work and work-detail status, published dates, and image dimensions are now applied to the loaded source records before `write_source_record_payloads(...)` runs. The sheet-like projection remains for read-side generation loops and is tracked as follow-up cleanup.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed workbook-led script implementations

**Status:** implemented

**Area:** scripts / compatibility cleanup

**Summary:**
Replaced retained workbook-led catalogue entrypoints with short clean-exit stubs.

**Reason:**
The scripts already returned early in some cases, but still carried retired implementation code behind those returns. That left hidden compatibility artifacts in the repo and made it harder to tell which command paths were genuinely live.

**Effect:**
`build_catalogue.py`, `copy_draft_media_files.py`, `export_catalogue_source.py`, and `compare_catalogue_sources.py` now only print deprecation guidance and exit successfully. Active docs route current checks through source validation, Studio, and scoped JSON build previews.

**Affected files/docs:**

- `scripts/build_catalogue.py`
- `scripts/copy_draft_media_files.py`
- `scripts/export_catalogue_source.py`
- `scripts/compare_catalogue_sources.py`
- `AGENTS.md`
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Rewrote stale workbook workflow docs

**Status:** implemented

**Area:** documentation / compatibility cleanup

**Summary:**
Rewrote current catalogue docs and archived workflow guides so they no longer route users through retired workbook-led or standalone file/link workflows.

**Reason:**
The live catalogue source is canonical JSON maintained through Studio and scoped JSON builds. Keeping old workflow detail in current docs made the source boundary look ambiguous.

**Effect:**
The current pipeline map now describes the JSON-source workflow. Deprecated workbook-led script/use-case pages are concise archive stubs that point to current references. Catalogue source, search, delete cleanup, lookup invalidation, work-owned file/link, and planning docs now describe work-owned downloads/links and scoped JSON builds rather than retired workflow paths.

**Affected files/docs:**

- `AGENTS.md`
- [Current Pipeline Map](/docs/?scope=studio&doc=new-pipeline-current-pipeline-map)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Delete Work](/docs/?scope=studio&doc=scripts-delete-work)
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed file and link compatibility maps

**Status:** implemented

**Area:** catalogue source model / compatibility cleanup

**Summary:**
Removed the retained `work_files` and `work_links` compatibility maps from live catalogue source records and dependent status surfaces.

**Reason:**
Files and links are now work-owned metadata in `works.json` as `downloads` and `links`. Keeping separate in-memory source families made validation, delete previews, lookup invalidation, and activity summaries look as though the old file/link source records still existed.

**Effect:**
`CatalogueSourceRecords` now contains works, work details, and series only. Source validation, delete previews, lookup refresh logic, Studio activity shaping, and Studio transport no longer expose `work_files` or `work_links` as current source families. Retired standalone work-file and work-link endpoints continue to return `410 Gone`; legacy workbook import helpers may still read `WorkFiles` and `WorkLinks` sheets only to fold rows into work-owned `downloads` and `links`.

**Affected files/docs:**

- `scripts/catalogue_source.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/activity_log.py`
- `assets/studio/js/activity.js`
- `assets/studio/js/studio-transport.js`
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Studio Activity](/docs/?scope=studio&doc=studio-activity)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Removed workbook provenance from source metadata

**Status:** implemented

**Area:** catalogue source model / compatibility cleanup

**Summary:**
Removed obsolete `data/works.xlsx` provenance from catalogue source metadata.

**Reason:**
The canonical catalogue source is now JSON under `assets/studio/data/catalogue/`, and `data/works.xlsx` is no longer an intended workflow input. Keeping workbook migration provenance in current metadata made the source model look partially workbook-owned.

**Effect:**
`assets/studio/data/catalogue/meta.json` now records the canonical source mode without a `created_from` workbook path. `scripts/catalogue_source.py` no longer emits workbook provenance from `payloads_from_records`, and [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model) documents the current metadata shape.

**Affected files/docs:**

- `assets/studio/data/catalogue/meta.json`
- `scripts/catalogue_source.py`
- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Moved workbook row helpers into bulk import adapter

**Status:** implemented

**Area:** catalogue source model / compatibility cleanup

**Summary:**
Moved the workbook row helper boundary used by the active bulk-import workflow into `scripts/catalogue_workbook_import.py`.

**Reason:**
The active `data/works_bulk_import.xlsx` workflow remains an import adapter, but workbook-specific helpers should not live in the canonical JSON source helper module just because the old `data/works.xlsx` pipeline once did.

**Effect:**
`scripts/catalogue_workbook_import.py` now owns its own `header_map` and `cell` helpers. Its imports from `scripts/catalogue_source.py` are limited to canonical source records, field lists, normalization, sorting, loading, and validation APIs.

**Affected files/docs:**

- `scripts/catalogue_workbook_import.py`
- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Completed compatibility cleanup planning pass

**Status:** implemented

**Area:** catalogue source model / cleanup planning

**Summary:**
Completed the first inventory and retention-policy pass for compatibility cleanup, leaving Task 3 ready for implementation slices.

**Reason:**
Code cleanup should not begin until the retained compatibility paths, removal decisions, implementation order, and verification expectations are explicit.

**Effect:**
The inventory now records additional findings for the generator's worksheet-shaped projection, deprecated workbook-led scripts, stale workbook workflow docs, and activity keys for retired file/link maps. The parent request marks Tasks 1 and 2 complete and Task 3 ready.

**Affected files/docs:**

- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Recorded compatibility cleanup retention direction

**Status:** implemented

**Area:** catalogue source model / documentation

**Summary:**
Resolved the first compatibility cleanup inventory questions and recorded the cleanup policy for upcoming implementation slices.

**Reason:**
The cleanup should not preserve compatibility artifacts under new names. Decisions needed to be made from the perspective of the current JSON-source pipeline rather than from the old `data/works.xlsx` workflow.

**Effect:**
The inventory now records that workbook row helpers should move beside the active bulk-import adapter, `data/works.xlsx` provenance and stale doc references should be removed, and `work_files` / `work_links` compatibility maps are not needed by current editor, lookup, delete, or validation paths. The parent request now marks retention-policy work as in progress.

**Affected files/docs:**

- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Started compatibility cleanup inventory

**Status:** implemented

**Area:** catalogue source model / documentation

**Summary:**
Added the first inventory document for the catalogue compatibility cleanup request.

**Reason:**
The compatibility cleanup needs a place to classify retained workbook-era and transitional paths before deciding what to keep, narrow, move, or remove. The active `data/works_bulk_import.xlsx` flow also needed to be distinguished from retired canonical editing through `data/works.xlsx`.

**Effect:**
The request now points Task 1 at a short child doc, [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory), with initial findings for the active bulk-import workbook adapter, workbook import helpers, deprecated workbook references, direct generator clean-exit behavior, source provenance metadata, and work file/link compatibility records.

**Affected files/docs:**

- [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)
- [Inventory](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup-inventory)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added lightweight optional test framework

**Status:** implemented

**Area:** testing / Codex workflow

**Summary:**
Added an opt-in repo check runner, test-script directories, and local run-log convention for larger-risk changes.

**Reason:**
The repo needed a pragmatic place for repeatable checks such as catalogue field-registry verification without turning every change request into a broad test-suite run. Codex also needs a standard way to run checks, capture logs, and report what still needs manual Studio review.

**Effect:**
`./scripts/run_checks.py` now runs coarse profiles such as `quick`, `catalogue`, `docs`, and `studio-smoke`, writing summaries and command logs under ignored `var/test-runs/`. `tests/python/`, `tests/smoke/`, and `tests/fixtures/` now define where retained checks and small fixtures belong, and `AGENTS.md` tells Codex to use the runner only when the change blast radius justifies it.

**Affected files/docs:**

- `scripts/run_checks.py`
- `tests/`
- `.gitignore`
- `AGENTS.md`
- [Testing](/docs/?scope=studio&doc=testing)
- [Run Checks](/docs/?scope=studio&doc=scripts-run-checks)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added catalogue field registry review page

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
Added `/studio/catalogue-field-registry/` as a read-only Studio page for inspecting the active catalogue field registry.

**Reason:**
The field-aware build registry is now the source of truth for save-time and preview scoping. It needed a simple Studio review surface so fields and rules can be inspected without opening implementation code.

**Effect:**
The page loads the registry path from `studio_config.json`, displays the formatted raw registry JSON in a read-only text box, and filters by field name to show the complete matching rule object. The Resources section on `/studio/` now links to the page. The Jekyll exclude rules for runtime catalogue data are directory-specific so `assets/studio/data/catalogue_field_registry.json` is still served. This closes the field-aware catalogue build scoping request.

**Affected files/docs:**

- `studio/catalogue-field-registry/index.md`
- `assets/studio/js/catalogue-field-registry-review.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `_config.yml`
- `studio/index.md`
- [Catalogue Field Registry Review](/docs/?scope=studio&doc=catalogue-field-registry-review)
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Documented Studio smoke-test harness guidance

**Status:** implemented

**Area:** Studio / testing

**Summary:**
Added a dedicated Studio smoke-testing reference, recorded future Studio ready-state work as a separate change request, and updated `AGENTS.md` so future Codex sessions use the same Playwright interaction rules.

**Reason:**
Recent Work editor smoke tests showed that async-rendered Studio pages can create false pointer-click failures when tests interact before the route has settled. The immediate need is a stable harness rule; the broader product improvement belongs in its own request.

**Effect:**
Codex-run Studio smoke tests now have documented guidance for route readiness waits, hit-testable pointer clicks, and setup-only DOM activation. The separate ready-state request tracks a future shared `data-studio-ready` / `data-studio-busy` contract.

**Affected files/docs:**

- `AGENTS.md`
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added Work editor unsaved build preview modal

**Status:** implemented

**Area:** Studio / catalogue work editor

**Summary:**
Added a `Preview update` command to the Work editor current-record rail for unsaved single-work changes on published works.

**Reason:**
Field-aware build previews were available from the CLI and local write server, but the Work editor did not expose a visible preview before `Save`. The preview result is useful for occasional review, but too verbose to keep permanently in the already dense current-record rail.

**Effect:**
The command appears immediately after the current-record image and caption, sends the unsaved changed field names to `POST /catalogue/build-preview`, and shows the field-aware summary, rules, artifacts, and reasons in a modal. For a download-only edit, the modal reports the narrowed `work_local_public_metadata` scope instead of a broad series/search/media update.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added field-aware catalogue registry verification

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
Added `./scripts/verify_catalogue_field_registry.py` to check representative field-aware build planner cases against the live registry.

**Reason:**
After moving build scoping into a registry-backed planner, the important dependency classes needed a fast read-only verification path that does not require running generators or mutating source data.

**Effect:**
The helper verifies work-local metadata, editor-only metadata, media source fields, search/display fields, publication and membership fields, work-detail, series, and moment rules, plus unknown-field, mixed-dependency, and cross-family series-save fallback behavior.

**Affected files/docs:**

- `scripts/verify_catalogue_field_registry.py`
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Moved field-aware fallback artifact defaults into the registry

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
Field-aware fallback artifact sets now live in `assets/studio/data/catalogue_field_registry.json` instead of a hardcoded Python table.

**Reason:**
Fallback behavior is part of the dependency model. Keeping unknown-field and mixed-dependency artifact sets in the registry makes the registry the reviewable source of truth for both narrow rules and conservative behavior.

**Effect:**
The planner reads `defaults.*.target.artifacts_by_record_family` for fallback artifacts, derives fallback `generate_only`, catalogue-search, and local-media selections from those registry artifacts, and uses the renamed `mixed_dependency_classes` default for mixed rule classes.

**Affected files/docs:**

- `assets/studio/data/catalogue_field_registry.json`
- `scripts/catalogue_field_registry.py`
- `scripts/studio/catalogue_write_server.py`
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added dry-run explanations for field-aware catalogue builds

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
Field-aware catalogue build plans now include concise explanation rows for the artifact families selected by the registry.

**Reason:**
After preview and save-time builds began using narrowed rules, dry-runs needed to show why a plan selected `work-json`, catalogue search, local media, fallback artifacts, or no public build work.

**Effect:**
CLI previews print grouped `Field-aware reasons` lines, and `POST /catalogue/build-preview` plus dry-run save-time `apply_build` responses expose `field_plan.explanations[]`. Unknown fields and mixed dependency classes now explain conservative fallback selection.

**Affected files/docs:**

- `scripts/catalogue_field_registry.py`
- `scripts/catalogue_json_build.py`
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added field-aware catalogue build previews

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
`scripts/catalogue_json_build.py` and `POST /catalogue/build-preview` can now accept changed-field context and preview the same registry-backed narrowed scope used by save-time builds.

**Reason:**
Task 3 narrowed save-time builds, but previews still showed broad commands unless the save endpoint had already planned the build. The CLI and preview endpoint needed the same field-aware rule path for review and debugging.

**Effect:**
The preview path resolves the field registry through `studio_config.json`, applies matching target rules to `generate_only`, `rebuild_search`, and `generate_local_media`, and returns or prints the selected `field_plan`. Unknown fields and mixed rule classes continue to preview conservative fallback.

**Affected files/docs:**

- `scripts/catalogue_field_registry.py`
- `scripts/catalogue_json_build.py`
- `scripts/studio/catalogue_write_server.py`
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Wired catalogue field registry into save-time build planning

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
Single-record catalogue saves now resolve changed fields through `assets/studio/data/catalogue_field_registry.json` before running save-time public builds.

**Reason:**
Small metadata saves should not automatically select local media generation, catalogue search, or broad page/index refreshes when the registry says the changed fields affect only focused payloads or Studio-only source data.

**Effect:**
Work, work-detail, series, and moment save endpoints can pass narrowed `generate_only`, `rebuild_search`, and `generate_local_media` values into the scoped build runner. Unknown fields, mixed rule classes, bulk saves, create/delete flows, imports, publication actions, and cross-family series saves retain conservative fallback.

**Affected files/docs:**

- `scripts/studio/catalogue_write_server.py`
- `scripts/catalogue_json_build.py`
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Added catalogue field registry for build scoping

**Status:** implemented

**Area:** Studio / catalogue build planning

**Summary:**
Added `assets/studio/data/catalogue_field_registry.json` as the JSON source of truth for Task 2 field-to-artifact build scoping rules.

**Reason:**
The field-aware build planner needs a reviewable registry that separates current broad behavior from target narrowed behavior before the write server and build preview are changed.

**Effect:**
The registry groups catalogue fields by record family and operation, records current and target artifact families, keeps fallback rules explicit, and lists retired fields removed by Task 1A. `studio_config.json` now exposes the registry path for the future Studio review page.

**Affected files/docs:**

- `assets/studio/data/catalogue_field_registry.json`
- `assets/studio/data/studio_config.json`
- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-05-01] Limited recently added entries to currently published targets

**Status:** implemented

**Area:** catalogue generation / public runtime

**Summary:**
`assets/data/recent_index.json` now retains only entries whose current target series or work is still `published`.

**Reason:**
The recent-publications ledger can outlive a target's current status. Draft records that still existed in the generated aggregate indexes could remain visible on `/recent/`.

**Effect:**
Regenerating the recent index prunes draft works and draft series from the public recently added list while keeping the existing historical ordering for published targets.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- `assets/data/recent_index.json`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
