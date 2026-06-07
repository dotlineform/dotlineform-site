---
doc_id: scripts-docs-management-scripts-read-config
title: Docs Viewer Read And Config Scripts
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: scripts-docs-management-scripts
---
# Docs Viewer Read And Config Scripts

## `docs-viewer/services/docs_management_read_service.py`

Purpose: GET route dispatcher for generated reads, source-config reads, source body reads, and staged import listings.

Ownership: owns query parameter normalization and mapping GET endpoint paths to read helpers.

Responsibilities:

- validates `scope` against configured docs scopes
- dispatches generated tree, recently-added, doc payload, search, references, and reference-target reads
- dispatches source-config report and source-config settings contract reads
- dispatches selected Markdown body reads
- dispatches staged import file listings

Not responsible for:

- serving HTTP responses directly
- writing source or generated files
- rebuilding after writes

## `docs-viewer/services/docs_generated_reads.py`

Purpose: safe readers for generated Docs Viewer JSON artifacts.

Ownership: owns generated artifact path resolution and raw generated JSON loading.

Responsibilities:

- resolves generated docs output roots from docs scope config
- reads `index-tree.json`, `recently-added.json`, `by-id/<doc_id>.json`, docs-search JSON, reference index JSON, and reference-target JSON
- validates safe doc ids and semantic-reference target ids
- verifies document payload reads against the generated index tree before reading payload files
- reports missing or invalid generated JSON as errors

Not responsible for:

- producing generated artifacts
- mutating source config
- filtering generated payload fields for callers

## `docs-viewer/services/docs_management_capabilities_service.py`

Purpose: capability and scope availability payload builder.

Ownership: owns the `GET /capabilities` response contract.

Responsibilities:

- reports enabled management features
- reports per-scope source root availability
- reports generated docs/search artifact availability
- counts scope source docs
- reports scope lifecycle manifest ownership and delete eligibility

Not responsible for:

- enforcing endpoint access
- applying lifecycle changes

## `docs-viewer/services/docs_source_config_report.py`

Purpose: source-config report builder for manage-mode diagnostics.

Ownership: owns the read-only source-config report payload used by configuration report surfaces.

Responsibilities:

- reads known Docs Viewer config files
- compares source config with generated scope data
- reports browser config projections, generated output paths, viewer options, and warnings
- returns repo-relative paths

Not responsible for:

- editing config
- rebuilding stale generated output

## `docs-viewer/services/docs_source_config_settings.py`

Purpose: settings contract, validation, and allowlisted source-config writes.

Ownership: owns which source-config fields are editable through manage mode.

Responsibilities:

- exposes editable scope fields, blocked scope fields, and deferred global fields
- currently allows scoped `show_updated_date`
- validates proposed setting changes and value types
- writes allowlisted changes to `docs-viewer/config/scopes/docs_scopes.json`
- reports whether a rebuild is required

Not responsible for:

- running rebuild commands directly
- editing install-time fields such as roots, output paths, route bases, or import media storage

## `docs-viewer/services/docs_source_model.py`

Purpose: source Markdown model helpers shared by reads, mutations, imports, and capabilities.

Ownership: owns parsing and formatting source docs inside configured docs scopes.

Responsibilities:

- loads configured scope docs
- parses and renders front matter
- resolves scope roots
- normalizes scope ids and UI status values
- determines default viewability by scope
- writes source text atomically when called by workflow modules

Not responsible for:

- HTTP routing
- generated artifact formats
- deciding rebuild scope after a mutation
