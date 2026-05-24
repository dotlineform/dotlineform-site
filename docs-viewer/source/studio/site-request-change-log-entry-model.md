---
doc_id: site-request-change-log-entry-model
title: Change Log Entry Model Request
added_date: 2026-05-19
last_updated: 2026-05-19
ui_status: done
parent_id: archive
sort_order: 74000
viewable: true
---
# Change Log Entry Model Request

Status:

- Step 1 completed: `_docs_logs/` source conventions and schema scaffold added
- Step 2 completed: development workflow doc added under Site Docs and AGENTS.md now points to it
- Step 3 completed: ongoing log authoring workflow documented in `_docs_logs/README.md`
- Step 4 completed: Codex-oriented log entry helper added
- Step 5 completed: legacy site and Search change-log migration script added and run
- Step 6 completed: generated date, domain, related-doc, related-file, change-request, and search projections added
- Step 7 completed: compact change-log archive stubs and manage-only change-history report added
- Step 8 completed: canonical entries migrated from monthly JSONL to flat per-entry JSON files

## Summary

Replace the current long-form site change log and monthly archive pages with a more structured change-entry model.

The current change log is useful as a historical ledger, but it is difficult to read, difficult to browse by subject, and weakly searchable because entries are stored as unstructured sections inside a few very long Markdown files.

The desired direction is to keep a short human-facing change-log summary in the Studio docs while moving detailed entries into a dedicated `_docs_logs/` source root with metadata, generated indexes, and search behavior designed for chronological and subject-based lookup.

## Problem

The existing site change log now contains hundreds of dated entries across the current page and monthly archive pages.

Current limitations:

- entries are grouped mainly by file and date, not by domain or subject
- an individual entry has no stable document identity beyond a heading anchor
- search sees one very long page instead of focused atomic records
- related domains such as Docs Viewer, Catalogue, Search, Library, UI, and build tooling are only captured in prose
- monthly archive files reduce file length but do not improve findability
- the current Studio docs scope mixes operational reference docs with historical implementation records
- detailed change records do not need to be browsable as normal docs, but they do need to be easy for Codex and search tooling to retrieve when tracing development decisions

This makes the change log less useful as technical memory over time.

## Goals

- make each meaningful change entry independently addressable
- capture useful metadata for date, domain, subject, status, related files, and related docs
- store detailed entries in a structured format optimized for validation, retrieval, and search
- support browsing by date and domain without duplicating entry prose manually
- keep the main Studio change log compact and readable
- keep detailed change entries out of `_docs/` and out of the normal Studio Docs Viewer index
- allow a change-history scope or search corpus to use weighting and filters that fit changelog lookup
- preserve existing historical entries during migration
- include existing Search change-log entries in the same structured history corpus
- make the migration scriptable and repeatable enough to avoid manual section cutting

## Non-Goals

- do not rewrite the meaning of existing historical entries during the first migration
- do not make every minor activity-log event a permanent change entry
- do not require a runtime database for v1
- do not remove the existing Studio docs scope as the place for stable operational documentation
- do not fill the Docs Viewer navigation with hundreds of change-entry documents that are unlikely to be browsed directly
- do not use Markdown as the canonical storage format for detailed entries

## Proposed Shape

Keep two layers:

- a compact [Site Change Log](/docs/?scope=studio&doc=site-change-log) page for recent notable changes and links into generated date/domain indexes
- a dedicated `_docs_logs/` source root for detailed change entries

Detailed entries should not be stored in `_docs/`.
They should be stored as structured per-entry JSON records under `_docs_logs/`.
The records should be optimized for retrieval, search indexing, validation, and script processing rather than normal human reading in the Docs Viewer.

## File Layout

Use a shallow, operational folder structure.
Grouping by domain, subject, or date should come from metadata and generated indexes, not from nested source folders.

Recommended layout:

```text
_docs_logs/
  README.md
  schema.json
  entries/
    change-2026-05-19-added-manage-only-change-history-report.json
    change-2026-05-19-added-targeted-docs-payload-rebuilds.json
    change-2026-04-30-converted-public-catalogue-stubs-to-route-anchors.json
  generated/
    by-date.json
    by-domain.json
    by-related-doc.json
    by-related-file.json
    search-index.json
  reports/
    migration-review.json
```

Source files:

- `entries/*.json` should be canonical source records after the per-entry migration
- legacy `entries/*.jsonl` monthly files were an intermediate migration format and were retired in Step 8
- `schema.json` validates the record contract
- `README.md` documents authoring and migration rules

Generated files:

- `generated/*.json` are derived projections for search, reports, and compact indexes
- `reports/*.json` are migration and validation diagnostics
- generated files are not the source of truth
- staging and commits remain manual during development, as with current generated-output practice

## Record Format

Use one JSON file per change entry as the primary format.
Each file contains one JSON object matching `_docs_logs/schema.json`.

Reasons:

- efficient for Codex to retrieve individual entries without loading a full month of unrelated records
- easy for `rg -l` to find candidate entry files by id, domain, related file, or prose
- easy to validate against `schema.json`
- stable diffs because completed historical entries rarely change
- no front matter/body parsing after migration
- compact enough for machine retrieval without requiring hundreds of Markdown files

Use a flat source directory rather than month folders.
The entry id and filename already carry the date, and nested month directories do not improve Codex retrieval.

Filename pattern:

```text
_docs_logs/entries/change-YYYY-MM-DD-entry-slug.json
```

Suggested entry record:

```json
{
  "id": "change-2026-05-19-targeted-docs-payload-rebuilds",
  "date": "2026-05-19",
  "title": "Added Targeted Docs Payload Rebuilds",
  "status": "implemented",
  "type": "implementation",
  "domains": ["docs-viewer", "build"],
  "subjects": ["docs payloads", "targeted rebuilds"],
  "change_request_doc_id": "site-request-docs-build-incremental",
  "related_docs": ["scripts-docs-builder", "scripts-docs-management-server"],
  "related_files": ["studio/docs-viewer/build/build_docs.rb", "studio/docs-viewer/services/docs_write_rebuild.py"],
  "summary": "Docs writes can rebuild explicit generated docs payload ids instead of always rebuilding full scope payloads.",
  "effect": "Small docs source writes create less generated-output churn while preserving index correctness.",
  "source": {
    "file": "_docs/site-change-log.md",
    "line": 20,
    "archive": "current"
  }
}
```

The migration may preserve existing prose blocks in structured fields:

- status
- area
- summary
- effect
- affected files/docs
- verification where present

`change_request_doc_id` should be included when the entry closes or implements a documented change request.
Entries created from direct implementation work without a prior request can omit it.

## Grouping Model

The same entry should be findable through multiple views:

- by date: generated year and month indexes
- by domain: generated Docs Viewer, Catalogue, Search, Library, Studio UI, build tooling, runtime, and data-model indexes
- by subject: derived from metadata tags and related docs
- by status or type: implemented, request, refactor, cleanup, bugfix, documentation
- by related file, related doc, or originating change request

V1 should avoid exposing every entry as a normal left-nav document.
The primary access paths should be search, generated compact indexes, and direct links from the short Studio change-log summary.

## Search Policy

A dedicated change-history scope or search corpus should not use the same search policy as stable reference docs.

Likely search priorities:

- entry title
- change date
- domain and subject metadata
- related files and related docs
- summary and effect prose
- affected files/docs lists

Likely lower priorities:

- boilerplate headings such as `Status`, `Summary`, `Effect`, and `Affected files/docs`
- repeated archive/index wrapper text

The scope should support searches like:

- `docs payload rebuild 2026-05`
- `catalogue publication`
- `studio/docs-viewer/build/build_docs.rb`
- `Docs Viewer management`
- `recent UI primitive changes`

Search and retrieval should prioritize Codex use cases:

- trace why a behavior changed
- find previous implementation decisions for a file or subsystem
- connect a current bug or refactor to earlier work
- retrieve compact historical context without opening large narrative documents

Human-readable browsing can be provided by a generated report or compact index view, but normal Docs Viewer document browsing is not the main use case.

## Main Implementation Steps

### Step 1. Define The Change-Entry Source Model And Scope

Status:

- completed

Create the `_docs_logs/` source conventions, structured record schema, generated index structure, and search policy.

V1 should treat `_docs_logs/` as the canonical source root for detailed change entries.
The normal `_docs/` tree should keep only the compact Studio-facing summary and the request/planning docs.

Expected outputs:

- `schema.json`
- `_docs_logs/README.md`
- source filename rules, initially JSONL by month and later flat per-entry JSON
- required and optional record fields
- generated year, month, domain, related-doc, related-file, and change-request index strategy
- automatic generated-output rebuild behavior after log entries change
- report-driven human-readable view under [Site Docs](/docs/?scope=studio&doc=dev-home), with iterative filters starting by scope/domain
- search weighting rules for change-history records

### Step 2. Document The Development Workflow

Status:

- completed

Create `_docs/development-workflow.md` under [Site Docs](/docs/?scope=studio&doc=dev-home) so AGENTS.md can reference it before and during implementation work.
Part of this work should review the current AGENTS.md content and move detailed procedural guidance into the workflow document where that guidance does not need to be read for every task.
AGENTS.md should become more directional: it should tell Codex which workflow sections to consult for the current class of work rather than carrying every detailed rule inline.

This document should cover the project workflow around:

- when to create or update change requests
- how to close out completed change requests
- how to create structured change-log entries from current implementation context
- how to create structured change-log entries from a completed change request
- how direct changes without a change request should still be logged
- what docs, generated payloads, and search artifacts need to be updated after work
- technical development checks that frequently matter in this repo, including state routing, module dependencies, UI design, docs ownership, search policy, and generated-data follow-through

AGENTS.md should point to this workflow document so Codex sees the close-out and log-entry obligations as part of normal work, while task-specific details can be read only when relevant.

### Step 3. Document The Ongoing Log Authoring Workflow

Status:

- completed

Document how new change-log records are created after the migration.

The workflow should cover two paths:

- completed change request to change-log entry
- direct implementation change to change-log entry without a prior request

Expected workflow:

- keep the change request doc manually managed as the planning and close-out artifact
- when a request is completed, create one or more `_docs_logs/entries/*.json` records for the actual implemented changes
- include `change_request_doc_id` in each related log entry
- add a compact reference list back to the completed change request when its closure/cleanup task calls for it, linking to created log entry ids or the generated report/search view
- move or mark the change request according to the existing request archive practice
- for changes without a request, create a log entry directly with source metadata, related files, related docs, domains, and subjects

This keeps change requests readable and manually curated while making the durable implementation history structured and searchable.

### Step 4. Add Codex-Oriented Helpers For New Log Entries

Status:

- completed

Add repo-local helper support that Codex can use to create or preview new `_docs_logs/` entries.
This may be a script if useful, but the primary contract is a clear documented workflow and validation path rather than a manually-run operator command.

The helper support should support:

- seeding a log entry from a change request doc id
- creating a log entry from current implementation context when no change request exists
- deriving date, title, status, candidate domains, related docs, and related files
- writing a flat per-entry JSON file
- validating the resulting record against `_docs_logs/schema.json`
- updating the completed change request with references to created log entry ids when the request's closure/cleanup task requires it
- triggering the generated index/search rebuild after entries are added or changed
- dry-run output before writing

The helper should not decide whether a change request is complete on its own.
Completion remains a manual docs-management decision driven by the request's task list and closure workflow.

### Step 5. Script The Migration From Existing Logs

Status:

- completed

Use one-off Python scripts to parse the current site and Search change-log files, split each dated `## [YYYY-MM-DD] ...` section into an atomic entry, infer initial metadata, and write structured records under `_docs_logs/entries/`.
Search change logs should be included in the same implementation and represented with `domain: search` rather than maintained as a separate documentation system.

The scripts should be dry-run first and report:

- source file and line range for each parsed entry
- generated entry id
- inferred date, title, status, area, domains, related docs, and related files
- inferred `change_request_doc_id` when existing prose clearly names a request doc
- entries needing manual review
- duplicate or ambiguous titles

The first migration can preserve existing prose exactly and only add conservative metadata.
There should be no assumption of a large manual curation pass after migration.

Implementation notes:

- `studio/workflows/change-requests/services/migrate_legacy_logs.py` parses the current site log, May archive, April archive, March-and-earlier archive, and Search change log.
- The initial migration wrote monthly JSONL buckets, which Step 8 later converted to flat per-entry JSON files.
- `_docs_logs/reports/migration-review.json` records the migration summary and entries that need metadata review.

### Step 6. Generate Search And Index Projections

Status:

- completed

Build generated projections from the JSON source records.

Required generated outputs:

- date index
- domain index
- related-doc index
- related-file index
- change-request index
- search source or search payload tuned for change-history lookup
- migration review report for low-confidence metadata

The search projection should weight title, date, domains, subjects, related docs, related files, change request doc id, summary, and effect ahead of boilerplate section labels.
Generated `_docs_logs/generated/*.json` outputs should rebuild automatically when log entries are added or changed.

Implementation notes:

- `studio/workflows/change-requests/services/build_indexes.py` validates `_docs_logs/entries/*.json` and writes the generated projections.
- `studio/workflows/change-requests/services/log_entry.py` now has an implemented generated rebuild hook through `build_indexes.py`.
- Generated v1 outputs are `_docs_logs/generated/by-date.json`, `_docs_logs/generated/by-domain.json`, `_docs_logs/generated/by-related-doc.json`, `_docs_logs/generated/by-related-file.json`, `_docs_logs/generated/by-change-request.json`, and `_docs_logs/generated/search-index.json`.

### Step 7. Replace Long Archives With Compact Human Views

Status:

- completed

After the generated entries are reviewed, replace the current long-form archive pages with compact summaries or generated index links.

The current [Site Change Log](/docs/?scope=studio&doc=site-change-log) should become a concise recent-changes page with links to:

- current month detailed entries
- month archive indexes
- domain indexes
- migration notes

The human-facing change-history report should live under [Site Docs](/docs/?scope=studio&doc=dev-home).
Its v1 display should provide:

- scope/domain filter
- title
- date
- summary paragraph for each log entry

The generated JSON projections and migration reports are large local build artifacts, not tracked source.
Track canonical `_docs_logs/entries/*.json` records, ignore `_docs_logs/generated/*.json` and `_docs_logs/reports/*.json`, and rebuild generated projections locally from source records.

The v1 report should be manage-only without adding a new front-matter field.
Use an ordinary Studio docs report page with `viewer_report_access: manage`, place it under a dedicated report-tree root such as `change-history-reports`, and add that root to the Studio scope's `manage_only_tree_root_ids`.
That keeps the report doc and its descendants out of public navigation and public docs search while still allowing manage mode to mount a report that reads local generated docs-log projections.

Implementation notes:

- `_docs/site-change-log.md` and the dated site archive docs are compact migration stubs.
- `_docs/change-history-reports.md` is the manage-only report-tree root.
- `_docs/change-history.md` uses `viewer_report: change_history` and `viewer_report_access: manage`.
- The Studio scope lists `change-history-reports` in `manage_only_tree_root_ids`.
- `assets/docs-viewer/js/reports/change-history-report.js` renders the v1 domain-filtered report from `_docs_logs/generated/search-index.json` via `GET /docs/generated/docs-log?projection=search-index`.

Additional filter granularity can be designed iteratively after the basic report is useful.

### Step 8. Migrate Canonical Entries To Flat Per-Entry JSON

Status:

- completed

Replace the monthly JSONL canonical source files with one flat JSON file per change entry.

The previous monthly JSONL files were script-friendly, but they were inefficient for Codex context because reading one entry could require opening a large month file.
The canonical source should optimize for selective retrieval by Codex and scripts.

Target layout:

```text
_docs_logs/
  entries/
    change-2026-05-19-added-manage-only-change-history-report.json
    change-2026-05-19-added-targeted-docs-payload-rebuilds.json
    change-2026-04-30-converted-public-catalogue-stubs-to-route-anchors.json
```

Implementation requirements:

- convert existing `_docs_logs/entries/*.jsonl` rows to flat `_docs_logs/entries/<id>.json` files
- preserve the existing record schema and ids
- update `studio/workflows/change-requests/services/log_entry.py` so new entries preview/write one JSON file instead of appending to monthly JSONL
- update `studio/workflows/change-requests/services/build_indexes.py` to read `entries/*.json`
- update `studio/workflows/change-requests/services/migrate_legacy_logs.py` so its write mode creates per-entry JSON files rather than monthly JSONL
- update tests to cover per-entry read/write behavior and duplicate-id handling
- update `_docs_logs/README.md`, `_docs_logs/entries/README.md`, and this request doc to remove JSONL as the active canonical format
- remove the monthly JSONL files after the per-entry files are generated and verified
- keep ignored generated projections under `_docs_logs/generated/*.json`
- check and update if needed the manage -only change-history report.

Codex retrieval should use simple file search first:

```bash
rg -l "studio/docs-viewer/build/build_search.rb" _docs_logs/entries
rg -l "change-history-report" _docs_logs/entries
rg -l "\"docs-viewer\"" _docs_logs/entries
```

Expected result:

- Codex can locate and open one or a few small entry files instead of loading a 600KB month file
- generated indexes and the manage-only change-history report keep the same output shape
- script behavior remains deterministic, with flat per-entry JSON files as the sole canonical source

Implementation notes:

- Existing monthly JSONL rows were converted into 470 flat `_docs_logs/entries/<id>.json` files, then this Step 8 implementation added its own structured entry.
- The retired monthly JSONL files were removed from `_docs_logs/entries/`.
- `studio/workflows/change-requests/services/log_entry.py`, `studio/workflows/change-requests/services/build_indexes.py`, and `studio/workflows/change-requests/services/migrate_legacy_logs.py` now use per-entry JSON files.
- Focused tests cover per-entry read/write behavior and duplicate-id handling.

## Migration Script Notes

A practical migration can be handled by small repo-local Python scripts:

- parse existing changelog Markdown sections by dated H2 heading
- extract `Status`, `Area`, `Summary`, `Effect`, and `Affected files/docs` blocks where present
- infer domain tags from `Area`, related docs, related files, and title keywords
- generate stable slugs from date and title
- write atomic JSON records under `_docs_logs/entries/`
- validate generated records against `_docs_logs/schema.json`
- infer `change_request_doc_id` when existing changelog prose clearly names a request doc
- generate month, year, domain, and related-file indexes
- generate the change-history search payload or source data needed by the search builder
- write a review report for ambiguous metadata

The scripts should not delete or rewrite the original log files until the generated entries have been reviewed.

## Decisions

- generated `_docs_logs/generated/*.json` files should rebuild automatically when log entries are added or changed
- staging and commits remain manual during development
- Search change-log entries are included in the same implementation with `domain: search`
- individual rendered entry detail views are not needed for v1
- search result snippets, generated indexes, and a Docs Viewer report under [Site Docs](/docs/?scope=studio&doc=dev-home) are enough for v1
- the v1 report should start with scope/domain filtering plus title, date, and summary for each entry
- additional report filters should be designed iteratively
- no substantial manual metadata curation is expected after the first scripted migration
- future change-log records should be authored as atomic `_docs_logs/` records, with summary/index views produced from generated JSON
- seeding and populating entries is expected to be Codex-driven from current context or a change request doc
- helper scripts are useful only insofar as they support Codex-driven workflow, validation, and generated-output refresh
- completed request docs should be updated with log-entry references when a defined closure/cleanup task calls for it
- AGENTS.md should point to `_docs/development-workflow.md`, a [Site Docs](/docs/?scope=studio&doc=dev-home) child doc that includes this close-out behavior
- detailed procedural guidance that does not need to be loaded for every task should move from AGENTS.md into the development workflow doc, leaving AGENTS.md as a concise directional entrypoint

## Benefits And Risks

Benefits:

- individual changes become identifiable and searchable
- the main change log becomes readable again
- historical implementation memory can be retrieved by domain, file, date, and subject instead of only by month
- future migration and cleanup work can operate on structured records

Risks:

- a naive migration could create too many visible navigation items if entries are exposed as normal docs
- inferred metadata will need review before it is trusted
- search policy work may be needed before the new scope feels useful
- future change-log authoring needs a clear workflow so the corpus does not drift back into long unstructured pages

## Change Log Entries

- `change-2026-05-19-migrated-docs-logs-to-per-entry-json`
- `change-2026-05-19-added-manage-only-change-history-report`
