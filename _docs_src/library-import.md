---
doc_id: library-import
title: Library Import v1
added_date: 2026-05-03
last_updated: "2026-05-03 22:40"
ui_status: in-progress
parent_id: library
sort_order: 30
---
# Library Import v1

Status:

- in-progress

## Summary

This change request specifies a Studio Library import workflow for staged data files that contain Library document content or metadata returned from an external review process.

The first goal is not to write canonical Library source.
The first goal is to turn staged JSON or JSONL files into human-readable Markdown preview documents so the user can compare:

- the staged data file
- the current canonical source under `_docs_library_src/`
- the current rendered Library Docs Viewer output
- any external edits, summaries, or relationship recommendations contained in the staged file

This is the import-side counterpart to [Library Export v1](/docs/?scope=studio&doc=library-export).
Export creates local working files from canonical Docs Viewer data; import reads local working files copied into a staging area and prepares them for inspection.

## Spec

### Product Boundary

Library import v1 should be a review and preview workflow.

It should:

- read files manually copied into a repo-local `var/` staging folder
- parse supported Library export-shaped JSON or JSONL files
- parse minimal hand-authored JSON or JSONL files when they contain document-like records
- generate Markdown preview files under a repo-local `var/` preview folder
- show the staged files, detected import type, key metadata, report issues, and generated preview paths in Studio
- keep canonical `_docs_library_src/` files unchanged

It should not:

- call an LLM API directly
- treat external edits as trusted source
- overwrite Library source Markdown
- apply parent-child relationship changes
- infer a perfect Markdown round trip from exported plain text

Source writes should be a later apply step after preview quality, apply-time validation rules, and file shapes have been proven with real staged files.
Import v1 is not a flight check for those later apply workflows.
It should be permissive enough to preview imperfect files and make defects visible rather than refusing to inspect them.

### Relationship To Existing HTML Import

This workflow is separate from `/studio/docs-import/?scope=library`.

The existing HTML import flow creates or overwrites Library source Markdown from staged `.html` files.
Library import v1 reads staged export-derived data files, usually `.json` or `.jsonl`, and writes preview Markdown only.

Both workflows can use the docs-management local service, but they should keep separate staging conventions and endpoint names so staged HTML imports are not confused with staged data imports.

### Staging And Preview Artifacts

The v1 staging root is:

```text
var/docs/import-staging/library/
```

The v1 preview root is:

```text
var/docs/import-preview/library/
```

These artifacts are local working files.
They should be ignored by git, safe to delete, and reproducible from the staged data file plus the current import renderer.

Preview output is document-centric for summary and full-content imports.
Each imported summary or full-content document should produce one Markdown preview file.
A staged summary or full-content JSON/JSONL file containing four documents should therefore generate four Markdown preview files.
Summary and full-content preview filenames should include the preview-generation timestamp so repeated runs do not overwrite each other.
Relationship imports are the v1 exception: a staged parent-child relationships file should produce one Markdown preview file showing the whole candidate tree contained in that input file.
No generated Markdown index file is required in v1.

Each generated preview should include document-specific front matter only:

```yaml
---
doc_id: defining-information-for-cross-boundary-comparisons
title: Defining Information For Cross Boundary Comparisons
parent_id: library
import_type: document_summary
preview_generated_at: 2026-05-03T20:01:00Z
---
```

Preview files do not need to contain the staged filename or import-file provenance.
That provenance, plus parsing diagnostics and unknown metadata, belongs in the Studio report.

### Supported Input Types

The first importer should recognize the three initial Library export families when their metadata or shape is present:

- `library-parent-child-relationships`
- `library-document-summaries`
- `library-full-document-content`

It should detect the input type from export metadata where available, falling back to structural detection when metadata is missing or when the file has been hand-authored.

JSONL imports should be parsed as one document record per line.
JSON envelope imports should be parsed from the configured document array path when present, initially expected as `documents`.

V1 should also accept minimal document-like records that do not come directly from an export.
The minimum expected document metadata is `doc_id` and `title`.
Missing `doc_id` or `title` indicates a malformed record, but should not cause the whole staged file to be rejected.

Unknown metadata should not be discarded.
It should appear in the Studio report and may be summarized in the corresponding preview when useful.

### Markdown Preview Rules

Preview Markdown is for inspection, not canonical round-trip reconstruction.

General rules:

- preserve imported values without silently rewriting meaning
- include `doc_id`, title, parent id, and detected document warnings near each document section
- keep generated preview structure stable and deterministic
- prefer readable Markdown headings, lists, block quotes, and fenced code when the input clearly supports them
- make `source_text` as readable as possible while exposing obvious gaps in the export/import round trip
- avoid raw JSON dumps as the default body

For document summaries:

- render one section per document
- show the proposed replacement summary clearly
- preserve empty or missing summary fields as explicit report warnings
- do not include full document content unless the imported file actually contains it

For full document content:

- render one section per document
- convert `source_text` to basic Markdown using conservative heuristics
- preserve paragraph breaks, obvious bullet lists, numbered lists, and blockquote markers
- treat ambiguous line breaks as plain paragraphs rather than inventing structure
- include headings from explicit `headings` fields before deriving headings from body text
- treat full-content preview output as inspection material only, not as a potential source-content replacement

For parent-child relationships:

- render one Markdown file containing a simple tree for the whole candidate tree in the imported relationships file
- include orphaned records, missing parents, duplicate ids, or cycles as report issues
- preserve any summary or heading context below each tree item when present
- keep relationship import preview-only; later workflows may turn candidate trees into actionable edits

### Parsing And Report Issues

Import v1 should not validate staged files as if they were about to be applied.
Its job is to parse what it can, generate readable previews where possible, and report issues clearly.

File-level blockers are limited to cases where there is nothing useful to preview:

- unreadable file
- unsupported extension
- invalid JSON or JSONL
- output preview path outside the preview root

Warnings:

- missing `doc_id`
- missing title
- duplicate `doc_id`
- unknown `doc_id` compared with the current Library docs index
- record exists in the staged file but is unpublished in the current Library index
- record exists in the staged file but has no matching generated Docs Viewer payload
- missing summary in a summaries import
- missing `source_text` in a full-content import
- parent id points to a missing or excluded record
- parent-child relationship cycles
- unsupported or unknown import shape
- export metadata is missing, partial, or from a different scope

The importer should not compare staged records against `source_last_updated` from export metadata in v1.
That comparison belongs to a later apply workflow.

The Studio page should show counts for files, parsed records, previewed records, warnings, and file-level blockers.
Diagnostics should stay in the Studio report; v1 should not write a separate machine-readable report JSON beside the Markdown previews.

### Studio Workflow

The intended v1 Studio page is likely:

```text
/studio/library-import/
```

The page should:

- list staged Library data files
- show detected import type, source export id when available, generated-at timestamp when available, document count, and report status
- let the user select one staged file
- generate or refresh a Markdown preview
- show generated preview paths
- provide a clear report of warnings and errors

The page should not offer an Apply button in the first implementation unless the apply behavior is explicitly narrowed to summary-only front-matter updates and has its own validation contract.

The Library dashboard should link to the Library import page under the existing `Data` column, beneath the export link.
The page can be created early as a staged-file listing before preview generation exists.
Once previews are available, the list can include preview paths.

### Future Apply Direction

The most likely first apply path is summary import.
It is lower risk because it can update one front-matter field per existing Library doc after validation and preview.
Imported summaries should be treated as proposed replacement summaries until explicitly applied.

Potential later apply flows:

- summary import apply: write `summary` into `_docs_library_src/*.md`
- relationship recommendation review: present proposed parent changes, but apply only after a dedicated tree editor or diff workflow exists
- full content import apply: likely requires a much stronger Markdown round-trip and diff review story before source writes are safe

## V1 Decisions

- staging root: `var/docs/import-staging/library/`
- preview root: `var/docs/import-preview/library/`
- output shape: one Markdown preview file per imported document for summary and full-content imports
- relationship output shape: one Markdown preview file showing the whole imported candidate tree
- index files: none in v1
- preview front matter: document-specific metadata only
- staged-file provenance: shown in the Studio report, not copied into every preview file
- diagnostics: shown in the Studio report, not embedded as compact JSON in preview files
- machine-readable report JSON: not written in v1
- accepted input: export-derived files and minimal hand-authored JSON or JSONL rows
- unknown metadata: preserved in the Studio report and exposed in preview when useful
- minimum expected document metadata: `doc_id` and `title`
- malformed records: reported without rejecting the whole staged file
- summary semantics: proposed replacement summaries
- full content semantics: readable inspection preview only, not a source-content replacement
- relationship semantics: candidate tree preview only
- source freshness comparison against `source_last_updated`: deferred
- dashboard link: add Library Import below export under the Library dashboard `Data` column once the route exists

## Remaining Open Questions

- What exact preview filename should be used for duplicate or missing `doc_id` records?
- Should unknown metadata be rendered in a small human-readable metadata section in each preview, or only in the Studio report?
- How much UI should the early `/studio/library-import/` page expose before preview generation exists?

## Initial Likely Tasks

### Task 1. Define Staging And Preview Conventions

Confirm the staging root, preview root, per-document preview filename convention, ignored artifact policy, and preview front-matter shape.

Expected outputs:

- staging root `var/docs/import-staging/library/`
- preview root under `var/docs/import-preview/`
- one preview file per imported document under `var/docs/import-preview/library/` for summary and full-content imports
- one whole-tree preview file under `var/docs/import-preview/library/` for relationship imports
- preview filename convention based primarily on `doc_id`, with a fallback for malformed records
- document-specific front matter only
- docs-management allowlist rules for read/write paths

### Task 2. Build Read-Only Import Parser

Implement a parser that reads staged `.json` and `.jsonl` files, detects supported Library export shapes or minimal document-like records, normalizes records, preserves unknown metadata, and returns a structured report.

The parser should not write source docs.

Status: implemented in `./scripts/docs/docs_import.py`.
The parser reads only from `var/docs/import-staging/library/`, supports JSON envelopes, JSON arrays, and JSONL document rows, detects the three v1 Library export families or minimal document records, preserves unknown file and record metadata in the report, and treats malformed records as warnings where parsing can continue.
It does not render Markdown previews or write any output files.

### Task 3. Add Report Issues And Current-Library Lookup

Load the generated Library Docs Viewer index and report staged records against current Library `doc_id`, publication, parent, and generated payload state.

This task should keep file-level blockers narrow and treat record-level problems as report warnings unless parsing cannot continue.

Status: implemented in `./scripts/docs/docs_import.py`.
The parser now loads `assets/data/docs/scopes/library/index.json` plus generated payload filenames under `assets/data/docs/scopes/library/by-id/`, adds current-Library summary data to the report, annotates normalized records with current existence, publication, viewability, payload, and parent state, and reports lookup problems as warnings.
Current-Library lookup warnings include unknown `doc_id`, unpublished current records, missing generated payloads, missing parent ids, unpublished parents, and parents without generated payloads.
If the current index is missing or unreadable, parsing still proceeds and the index problem is reported as a warning.

### Task 4. Render Markdown Previews

Create deterministic Markdown preview rendering for:

- document summaries
- full document content
- parent-child relationship trees

The renderer should write only under the preview root.
Summary and full-content imports should generate one Markdown file per imported document and include document-specific front matter.
Relationship imports should generate one Markdown file containing the whole candidate tree and include tree-level front matter.
Source-file provenance and diagnostics should remain in the Studio report.

Status: implemented in `./scripts/docs/docs_import.py`.
The parser can now render Markdown preview files with `--write-previews`.
Summary and full-content imports write one file per parsed document under `var/docs/import-preview/library/`, using `<doc_id>-<timestamp>.md`, `<doc_id>-record-<n>-<timestamp>.md` for duplicate ids, and `record-<n>-<timestamp>.md` for missing ids.
Relationship imports write one whole-tree Markdown file based on the staged filename, such as `relationships-tree.md`.
Preview files include front matter and readable Markdown sections for import metadata, relevant warnings, summaries, headings, source text, or candidate relationship trees.

### Task 5. Add Local Service Endpoints

Expose staged-file listing and preview generation through the docs-management local service.

Likely endpoints:

- `GET /docs/library-import/files`
- `POST /docs/library-import/preview`

Endpoint logs should include filenames, counts, status, and preview paths, not full document content.

Status: implemented in `./scripts/docs/docs_management_server.py`.
`GET /docs/library-import/files?scope=library` lists staged `.json` and `.jsonl` files under `var/docs/import-staging/library/`.
`POST /docs/library-import/preview` parses the selected staged file, runs current-Library lookup, renders Markdown previews through the shared import engine, writes previews in normal server mode, and reports planned previews without writing when the server is running with `--dry-run`.
The endpoint returns the same structured report as the CLI and logs only scope, staged filename, dry-run state, import type, counts, issue counts, and preview paths.

### Task 6. Add Studio Library Import Page

Status:

- implemented

Add a Library-scope Studio page that lists staged files, displays detected metadata, runs preview generation when available, and shows the resulting report.

The page should follow the same local-service availability pattern as Library export and docs HTML import.
The page can ship first as a staged-file listing and then grow preview generation.

Status note:

- implemented at `/studio/library-import/`
- listed from the `/studio/library/` dashboard under Data
- loads staged `.json` and `.jsonl` files through `GET /docs/library-import/files?scope=library`
- runs preview generation through `POST /docs/library-import/preview`
- shows selected file metadata, detected import type, source export metadata, counts, issues, and generated preview paths
- keeps the route disabled when the docs-management local service is unavailable
- does not apply summaries, full content, or relationship changes to canonical Library source

### Task 7. Link From Library Dashboard

Add the Library Import route under the Library dashboard `Data` column below `export` once the page route exists.

Status: implemented.

### Task 8. Add Verification

Add focused tests for:

- JSONL parsing
- JSON envelope parsing
- hand-authored minimal row parsing
- unknown metadata preservation
- unsupported shape reporting
- duplicate and missing `doc_id` reporting
- current-Library lookup reporting
- relationship tree rendering
- relationship whole-tree preview output
- deterministic preview output
- staged path allowlist behavior
- local service staged-file listing
- local service preview generation and dry-run behavior
- Studio route ready state and unavailable-service behavior

Parser and renderer coverage for JSONL parsing, JSON envelope parsing, minimal JSON rows, unknown metadata preservation, malformed record reporting, current-Library lookup reporting, per-document preview output, relationship whole-tree preview output, deterministic preview paths, invalid JSONL blocking, and staged/preview path allowlisting is implemented in `tests/python/test_docs_import.py`.
Local service handler coverage for staged-file listing, preview writing, dry-run preview reporting, and non-Library scope rejection is implemented in `tests/python/test_docs_import_service.py`.
A light Studio smoke test for the page shell and unavailable-service behavior is implemented in `tests/smoke/library_import.py`.
The `docs` profile in `./scripts/run_checks.py` runs the parser and local service checks.
The `studio-smoke` profile builds the site to a temporary Jekyll destination and runs the Library import route smoke with the docs-management service blocked.

### Task 9. Decide Summary Apply Scope

After preview v1 is usable, decide whether to add a narrow summary-only apply task.

That task should have its own spec before implementation because it would modify canonical Library source.

## Benefits And Risks

Benefits:

- provides a human-readable bridge between exported JSON files, rendered Library docs, and canonical Markdown source
- creates a safer review step before any external content affects source files
- gives real examples to guide later summary and relationship apply workflows

Risks:

- Markdown preview can look more authoritative than the staged data deserves if conversion heuristics are too aggressive
- full-content import can imply a round-trip quality that does not exist yet
- relationship previews may be useful for review but still unsafe to apply automatically
- staging and preview folders can accumulate stale artifacts unless the Studio page makes file age and provenance clear
