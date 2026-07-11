---
doc_id: scripts-docs-management-scripts-import
title: Import Scripts
added_date: 2026-06-07
last_updated: 2026-07-11
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

- lists staged import files under `var/docs/import-staging/`
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

Planned extension: [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) will first move all Docs Import formats to `configured_workspace_paths(repo_root).import_staging`, the W0-resolved `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/` drop-zone. It will then add schema-aware Data Sharing JSON/JSONL collection parsing before the generic file fallback. A shared record normalizer will feed both persistent read-only review materialization and import, while Markdown validation, inline-media planning/materialization, create/overwrite formatting, source writes, and rebuild follow-through remain shared lower-level services.

## `docs-viewer/services/docs_html_import.py`

Purpose: lower-level staged-file discovery and HTML/Markdown import conversion helpers.

Ownership: owns import staging resolution, supported file detection, preview generation, HTML conversion, inline media extraction, and Markdown package media retargeting.

Responsibilities:

- constrains staged file reads to `var/docs/import-staging/`
- detects supported source formats
- converts HTML and text sources to Markdown
- rewrites package-local images and attachments to docs media links
- materializes inline raster media plans
- applies SVG safety rules used by imports

Not responsible for:

- endpoint dispatch
- writing final docs source files
- running docs/search rebuilds
