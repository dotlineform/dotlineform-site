---
doc_id: scripts-docs-management-scripts-import
title: Import Scripts
added_date: 2026-06-07
last_updated: 2026-07-12
parent_id: scripts-docs-management-scripts
---
# Docs Viewer Import Scripts

## `docs-viewer/services/docs_management_import_service.py`

Purpose: thin management-service adapter for staged source imports.

Ownership: owns dependency wiring between route dispatch and the import source workflow.

Responsibilities:

- builds the import dependency object
- supplies management logging to the import workflow
- supplies source-write and rebuild follow-through helpers to the import workflow
- delegates actual import behavior to `docs_import_source_service.py`

Not responsible for:

- format conversion
- collision handling
- media materialization
- docs/search rebuild command details

## `docs-viewer/services/docs_import_source_service.py`

Purpose: staged source import workflow for the Docs Viewer import modal.

Ownership: owns ordinary single-source request interpretation, preview orchestration, collision discovery, confirmation gates, rebuild invocation, and response assembly.

Responsibilities:

- lists staged import files under the W0-configured shared import drop-zone
- imports HTML, Markdown, Markdown packages, text, SVG, image files, and downloadable files
- converts imported content to Markdown source
- derives proposed titles, doc ids, and filename stems
- plans media tokens through focused preview/media services
- handles replacement ids and confirmed overwrites
- validates generated Markdown before returning success
- maps the ordinary staged source to one normalized `ImportContent` record
- delegates per-document source/media planning and apply to `docs_import_document.py`
- calls supplied source-write and rebuild follow-through helpers after successful writes

Not responsible for:

- HTTP routing
- source-config settings
- builder implementation

The service resolves `configured_workspace_paths(repo_root).import_staging`, passes that explicit root through the workflow, and reports the marker-rooted drop-zone path without exposing user-specific absolute paths. `docs_import_content.py` defines the wrapper-neutral normalized record, and the documents Data Sharing adapter emits that record for compact and full-source packages. Persistent read-only review materialization consumes the same adapter. Collection route registration and confirmed apply remain later phases.

## `docs-viewer/services/docs_import_data_sharing_documents.py`

Purpose: trusted Data Sharing documents collection dry-run orchestration.

Ownership: thin public composition of Data Sharing package intake and wrapper-neutral collection planning.

Responsibilities:

- validates the target scope
- calls `docs_import_data_sharing_package.py` for trusted wrapper intake
- calls `docs_import_collection_plan.py` for complete write-free planning
- shapes the safe package identity projection supplied to the planner

Not responsible for:

- package parsing or per-row normalization details
- collision, hierarchy, media, or response-planning details
- collection UI or decision state
- configured-source or media writes
- apply revalidation and partial-failure handling
- Docs/search rebuild invocation
- result-report writing

## `docs-viewer/services/docs_import_data_sharing_package.py`

Purpose: Data Sharing documents wrapper intake and normalization.

Ownership: owns safe staged-package resolution, trusted export association, raw-row identity validation, and conversion to normalized collection record state.

Responsibilities:

- resolves a safe direct-child JSON/JSONL staged identity and matching trusted export metadata
- normalizes compact and full-source rows through the Data Sharing documents adapter
- preserves package order and represents every raw package record in typed planning state
- distinguishes wrapper/schema blockers from explicit per-record contract errors

Not responsible for:

- configured-scope collisions or hierarchy planning
- body conversion or media planning
- API response projection

## `docs-viewer/services/docs_import_collection_plan.py`

Purpose: wrapper-neutral write-free collection planning over normalized `ImportContent` records.

Ownership: owns typed collection record state and complete collision, hierarchy, parent-dependency, media-summary, blocker, warning, record-error, and body-free response planning.

Responsibilities:

- generates replacement previews through the shared content conversion boundary
- obtains candidate source targets and Docs/search ids from `docs_import_document.py`
- distinguishes collision decisions from invalid-record decisions
- resolves existing parents and supplied multi-level new-parent chains
- blocks malformed identity and hierarchy states
- reports inline media and declared-asset handling without materializing either
- exposes a body-free API projection plus internal per-document plans for later confirmed apply

Not responsible for:

- wrapper schema or provenance rules
- collection UI or decision state
- configured-source or media writes
- apply revalidation and partial-failure handling
- Docs/search rebuild invocation
- result-report writing

## `docs-viewer/services/docs_import_document.py`

Purpose: shared per-document Docs Import plan and apply boundary.

Ownership: owns one normalized record's create/overwrite validation, allowed front-matter application, canonical source formatting, target/search ids, media/source apply, and document result/activity shaping.

Responsibilities:

- consumes `ImportContent` records without requiring Data Sharing provenance
- plans create, overwrite, `replace`, `preserve-existing`, and `empty-new` behavior without writing
- preserves the current canonical body and unrelated front matter for metadata/hierarchy-only updates
- keeps the ordinary single-source replacement formatting contract unchanged
- rejects unsafe target ids and content intents that do not match the target action
- delegates media bytes and interactive asset materialization to their focused services
- atomically writes the planned document source
- returns changed paths and Docs/search ids to a caller-owned rebuild boundary

Not responsible for:

- package provenance or schema validation
- content-format conversion
- collection collision state or package ordering
- Docs/search rebuild invocation

## `docs-viewer/services/docs_import_preview.py`

Purpose: lower-level staged-file discovery and HTML/Markdown import conversion helpers.

Ownership: owns explicit-root staging resolution, supported file detection, preview generation, and format dispatch.

Responsibilities:

- constrains staged file reads to `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/`
- detects supported source formats
- converts HTML and text sources to Markdown
- rewrites package-local images and attachments to docs media links
- materializes inline raster media plans
- applies SVG safety rules used by imports
- exposes content-based Markdown, HTML-to-Markdown, and plain-text entrypoints beneath the existing file wrappers

Not responsible for:

- endpoint dispatch
- writing final docs source files
- running docs/search rebuilds
