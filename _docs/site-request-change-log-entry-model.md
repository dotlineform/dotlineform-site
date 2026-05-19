---
doc_id: site-request-change-log-entry-model
title: Change Log Entry Model Request
added_date: 2026-05-19
last_updated: 2026-05-19
ui_status: draft
parent_id: change-requests
sort_order: 72000
hidden: false
---
# Change Log Entry Model Request

Status:

- proposed

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
They should be stored as structured JSONL records under `_docs_logs/`.
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
    2026-05.jsonl
    2026-04.jsonl
    2026-03-and-earlier.jsonl
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

- `entries/*.jsonl` are canonical source records
- `schema.json` validates the record contract
- `README.md` documents authoring and migration rules

Generated files:

- `generated/*.json` are derived projections for search, reports, and compact indexes
- `reports/*.json` are migration and validation diagnostics
- generated files are not the source of truth
- staging and commits remain manual during development, as with current generated-output practice

## Record Format

Use JSONL as the primary format: one JSON object per line, one change entry per object.

Reasons:

- easy for Python scripts and Codex to scan
- easy to validate against `schema.json`
- stable diffs when entries are appended
- no front matter/body parsing after migration
- compact enough for machine retrieval without requiring hundreds of Markdown files

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
  "related_files": ["scripts/docs/build_docs.rb", "scripts/docs/docs_write_rebuild.py"],
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
- `scripts/docs/build_docs.rb`
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

Create the `_docs_logs/` source conventions, JSONL record schema, generated index structure, and search policy.

V1 should treat `_docs_logs/` as the canonical source root for detailed change entries.
The normal `_docs/` tree should keep only the compact Studio-facing summary and the request/planning docs.

Expected outputs:

- `schema.json`
- `_docs_logs/README.md`
- JSONL filename rules, initially one file per month
- required and optional record fields
- generated year, month, domain, related-doc, related-file, and change-request index strategy
- automatic generated-output rebuild behavior after log entries change
- report-driven human-readable view under [Site Docs](/docs/?scope=studio&doc=site-docs), with iterative filters starting by scope/domain
- search weighting rules for change-history records

### Step 2. Document The Development Workflow

Create `_docs/development-workflow.md` under [Site Docs](/docs/?scope=studio&doc=site-docs) so AGENTS.md can reference it before and during implementation work.
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

Document how new change-log records are created after the migration.

The workflow should cover two paths:

- completed change request to change-log entry
- direct implementation change to change-log entry without a prior request

Expected workflow:

- keep the change request doc manually managed as the planning and close-out artifact
- when a request is completed, create one or more `_docs_logs/entries/*.jsonl` records for the actual implemented changes
- include `change_request_doc_id` in each related log entry
- add a compact reference list back to the completed change request when its closure/cleanup task calls for it, linking to created log entry ids or the generated report/search view
- move or mark the change request according to the existing request archive practice
- for changes without a request, create a log entry directly with source metadata, related files, related docs, domains, and subjects

This keeps change requests readable and manually curated while making the durable implementation history structured and searchable.

### Step 4. Add Codex-Oriented Helpers For New Log Entries

Add repo-local helper support that Codex can use to create or preview new `_docs_logs/` entries.
This may be a script if useful, but the primary contract is a clear documented workflow and validation path rather than a manually-run operator command.

The helper support should support:

- seeding a log entry from a change request doc id
- creating a log entry from current implementation context when no change request exists
- deriving date, title, status, candidate domains, related docs, and related files
- appending to the correct monthly JSONL file
- validating the resulting record against `_docs_logs/schema.json`
- updating the completed change request with references to created log entry ids when the request's closure/cleanup task requires it
- triggering the generated index/search rebuild after entries are added or changed
- dry-run output before writing

The helper should not decide whether a change request is complete on its own.
Completion remains a manual docs-management decision driven by the request's task list and closure workflow.

### Step 5. Script The Migration From Existing Logs

Use one-off Python scripts to parse the current site and Search change-log files, split each dated `## [YYYY-MM-DD] ...` section into an atomic entry, infer initial metadata, and write JSONL records under `_docs_logs/entries/`.
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

### Step 6. Generate Search And Index Projections

Build generated projections from the JSONL source records.

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

### Step 7. Replace Long Archives With Compact Human Views

After the generated entries are reviewed, replace the current long-form archive pages with compact summaries or generated index links.

The current [Site Change Log](/docs/?scope=studio&doc=site-change-log) should become a concise recent-changes page with links to:

- current month detailed entries
- month archive indexes
- domain indexes
- migration notes

The human-facing change-history report should live under [Site Docs](/docs/?scope=studio&doc=site-docs).
Its v1 display should provide:

- scope/domain filter
- title
- date
- summary paragraph for each log entry

Additional filter granularity can be designed iteratively after the basic report is useful.

## Migration Script Notes

A practical migration can be handled by small repo-local Python scripts:

- parse existing changelog Markdown sections by dated H2 heading
- extract `Status`, `Area`, `Summary`, `Effect`, and `Affected files/docs` blocks where present
- infer domain tags from `Area`, related docs, related files, and title keywords
- generate stable slugs from date and title
- write atomic JSONL records under `_docs_logs/entries/`
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
- search result snippets, generated indexes, and a Docs Viewer report under [Site Docs](/docs/?scope=studio&doc=site-docs) are enough for v1
- the v1 report should start with scope/domain filtering plus title, date, and summary for each entry
- additional report filters should be designed iteratively
- no substantial manual metadata curation is expected after the first scripted migration
- future change-log records should be authored as atomic `_docs_logs/` records, with summary/index views produced from generated JSON
- seeding and populating entries is expected to be Codex-driven from current context or a change request doc
- helper scripts are useful only insofar as they support Codex-driven workflow, validation, and generated-output refresh
- completed request docs should be updated with log-entry references when a defined closure/cleanup task calls for it
- AGENTS.md should point to `_docs/development-workflow.md`, a [Site Docs](/docs/?scope=studio&doc=site-docs) child doc that includes this close-out behavior
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
