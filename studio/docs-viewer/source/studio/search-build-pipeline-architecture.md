---
doc_id: search-build-pipeline-architecture
title: Search Build Pipeline Architecture
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-build-pipeline
sort_order: 8100
---
# Search Build Pipeline Architecture

## Current Design And Implementation

The current search build uses one stable entrypoint with domain-owned adapters:

- stable command wrapper and dispatcher: `scripts/build_search.rb`
- adapter registry: `scripts/search/adapter_registry.json`
- Catalogue implementation owner: `scripts/search/build_search.rb`
- Docs Viewer implementation owner: `studio/docs-viewer/build/build_search.rb`

Current live search outputs:

- `assets/data/search/catalogue/index.json`
- `assets/data/search/studio/index.json`
- `assets/data/search/analysis/index.json`
- `assets/data/search/library/index.json`

Current build principles:

- deterministic output from stable repo inputs
- scope-owned search artifacts
- compact records rather than prose-heavy payloads
- search stays downstream of canonical source systems rather than becoming a new source of truth
- docs-domain scopes can use targeted search updates by `doc_id`
- catalogue can use additive-only targeted inserts by explicit `kind:id` record targets

Current source boundary:

- `catalogue` search reads canonical repo JSON artifacts, not retired workbook sources or non-repo source files
- `studio`, `analysis`, and `library` search read canonical generated docs indexes and include only rows where `viewable !== false`

This means the stable command shape is shared, while ownership stays with each data domain.

## Cross-Scope Conventions

All current search artifacts use the same high-level top-level structure:

- `header`
- `entries`

Current shared build conventions:

- outputs are written under `assets/data/search/<scope>/`
- records are generated at build time, not assembled in the browser
- content-version hashing is used for write skipping
- generated payloads stay compact and avoid body-prose indexing
- Catalogue fields declare their source artifact family and dependency policy in `scripts/search/build_config.json`
- Docs search policy is Docs Viewer-owned and emitted through `assets/docs-viewer/data/docs-viewer-config.json`
- builder code validates the relevant domain config while keeping record-generation algorithms in code
- public search artifacts should not become operation logs; targeted-update changed-id diagnostics belong in CLI/server output or local logs, not in the artifact by default
- keep one combined artifact per scope until payload size or browser performance proves sidecar payloads are needed

Current non-goals across all scopes:

- no raw HTML or Markdown parsing at runtime
- no search-specific backend service
- no prose shard loading
- no strict schema-fail validation layer separate from the builders themselves
- no per-record checksums for body or summary indexing in the first heavy-index slice

## Adapter Registry And Build Config

The top-level command loads `scripts/search/adapter_registry.json` to map requested scopes to domain builders.
The registry maps `catalogue` to the Catalogue adapter and configured Docs Viewer scopes from `studio/docs-viewer/config/scopes/docs_scopes.json` to the Docs Viewer adapter.

`scripts/search/build_config.json` is now Catalogue-owned.
Current Catalogue config responsibilities:

- declare source families such as `catalogue_indexes`, `catalogue_work_payloads`, `tag_assignments`, and `tag_registry`
- declare scope eligibility for each source family
- declare explicit `targeted_policy` values for each source family and scope
- map emitted search fields to source families
- keep the Catalogue artifact strategy combined

Current validation responsibilities in `scripts/search/build_search.rb`:

- reject unsupported config versions
- reject source-family references outside the Catalogue scope
- reject unsupported `targeted_policy` values
- reject obsolete boolean `targeted` flags
- reject missing, misplaced, or policy-incompatible `targeted_operations`
- reject fields without source-family declarations
- reject emitted entry fields that are missing from the config for the current scope

The config is intentionally not a record-generation DSL. The Catalogue builder still owns field derivation, sorting, normalization, hashing, and targeted-update algorithms.
Docs Viewer search derives scope input and output paths from `studio/docs-viewer/config/scopes/docs_scopes.json`; its `record_update` policy remains in the Docs Viewer builder and generated browser config.

Current targeted policy values:

- `record_update`: targeted create, update, and delete by explicit record id, currently used by Docs Viewer search
- `additive_only`: targeted insertion only, currently used by the first catalogue targeted-search slice
- `full_rebuild`: targeted updates are not allowed for that source family or scope

For the config-specific reference, see [Search Build Config JSON](/docs/?scope=studio&doc=config-search-build-json).
