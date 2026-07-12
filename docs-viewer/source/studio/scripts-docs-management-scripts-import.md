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

Ownership: owns import preview, collision handling, source creation/overwrite, media materialization, and import response contracts.

Responsibilities:

- lists staged import files under the W0-configured shared import drop-zone
- imports HTML, Markdown, Markdown packages, text, SVG, image files, and downloadable files
- converts imported content to Markdown source
- derives proposed titles, doc ids, and filename stems
- plans media tokens and materializes import media on writes
- handles replacement ids and confirmed overwrites
- preserves existing doc identity, parent, added date, and viewability during overwrites
- validates generated Markdown before returning success
- calls supplied source-write and rebuild follow-through helpers after successful writes

Not responsible for:

- HTTP routing
- source-config settings
- builder implementation

The service resolves `configured_workspace_paths(repo_root).import_staging`, passes that explicit root through the workflow, and reports the marker-rooted drop-zone path without exposing user-specific absolute paths. The planned reviewed-package extension will next add schema-aware Data Sharing JSON/JSONL collection parsing before the generic file fallback. A shared record normalizer will feed both persistent read-only review materialization and import, while Markdown validation, inline-media planning/materialization, create/overwrite formatting, source writes, and rebuild follow-through remain shared lower-level services.

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

Not responsible for:

- endpoint dispatch
- writing final docs source files
- running docs/search rebuilds
