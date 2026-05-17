---
doc_id: site-request-export-import-adapters
title: Export Import Adapter Boundary Request
added_date: 2026-05-05
last_updated: "2026-05-13 18:15"
ui_status: done
parent_id: archive
sort_order: 9000
---
# Export Import Adapter Boundary Request

Status:

- implemented
- archived after Data Sharing technical spec consolidation

Current implementation details now live in [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing), [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec), and [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters).

## Summary

Adopt an adapter-based export/import architecture before the current Library workflow becomes heavily used or accumulates more requirements in the shared shell.

The current Library export/import workflow should become the first adapter implementation.
The shared layer should remain a generic shell for data-domain selection, command execution, staging, status, and result display.
Domain behavior should live behind adapters that are selected by data model and workflow needs, not by route scope alone.

## Decision Direction

Use one shared export/import shell with data-domain adapters.

Do not make the existing Library document workflow the universal model for every scope.
The Library workflow is document-oriented: it exports documents, stages document-shaped JSON, generates document preview files, and can apply document metadata changes.

Analytics and Catalogue need different domain behavior.
For example, Analytics may export `assets/studio/data/tag_registry.json` for LLM review, receive proposals to merge or redefine tags, validate relationships against works and series, and produce a domain-specific apply plan.
That should not be squeezed into a document preview model.

Adapters should not intrinsically map one-to-one with route scopes.
The existing `scope` language is partly a routing concept that separates public, Studio, Library, and Analysis pages.
Export/import should instead think in terms of data domains and source data models.

Examples:

- a `documents` adapter can support any docs-viewer corpus when supplied with the relevant docs source/config
- a tag adapter is specific to tag data, even though tags touch Studio tooling, Catalogue records, works, and series
- a Catalogue adapter may need to work across several source files and generated relationships rather than one public route

## Problem

The current shared import/export routes are scope-aware, but much of the implementation language and behavior is still Library-document-specific.

That creates a near-term risk:

- new Library requirements will naturally be added to the shell because there is no adapter boundary yet
- future Analytics and Catalogue workflows will inherit document assumptions that do not fit their data
- the eventual split will be harder after the Library system is in full use
- the broader [Docs Toolkit Extraction Request](/docs/?scope=studio&doc=site-request-docs-toolkit-extraction) will be harder to reason about if export/import remains mixed with Library semantics

The design issue is not whether scopes should share infrastructure.
They should.
The issue is where domain behavior belongs.

## Goals

- Define the export/import adapter boundary now.
- Refactor the current Library workflow into the first `documents` adapter configuration.
- Keep the current Library UI and workflow behavior stable where possible.
- Move document-specific assumptions out of the shared shell.
- Leave clear extension points for Analytics and Catalogue without implementing their full workflows yet.
- Keep staging, preview, result, and backup conventions explicit enough for local write safety.
- Use neutral export/import routes for the shared shell instead of Library-named routes.

## Non-Goals

- Do not implement Analytics tag-registry import/apply behavior in this request.
- Do not implement Catalogue export/import behavior beyond keeping a clear future adapter target.
- Do not redesign the Library import/export UI unless the adapter boundary requires small copy or routing changes.
- Do not preserve existing `var/` test content as durable data.
- Do not turn the adapter system into a broad plugin framework before there is more than one real implementation.
- Do not expose adapter terminology as the primary user-facing navigation language.

## Shared Shell Responsibilities

The shared shell should own the common lifecycle only:

- route and data-domain selection
- adapter discovery and capability display
- config discovery and operation selection
- local server transport
- export command launch
- staged file discovery
- preview/apply command launch
- status messages
- result modal and reopenable result behavior
- backup/status conventions that every write adapter must satisfy
- common audit and error presentation

The shared shell should not know that a preview item is a document, a tag, a work, or a relationship proposal.
The page provides a place for selection and reporting, but the adapter supplies the data and presentation model for that space.

Minimum shared result shape:

- success or failure state
- warning messages
- error messages
- optional counts and adapter-owned details

## Adapter Responsibilities

Each adapter should own its domain contract:

- supported export configs and formats
- staging folder shape
- preview folder shape, if any
- staged payload schema
- preview generation semantics
- preview result record shape
- selectable item labels and hierarchy, if the UI needs a list
- validation rules
- apply actions
- backup targets
- relationship checks against other project data
- result summary wording
- domain-specific issue types

## First Adapter Configuration: Library Documents

The current Library document workflow should become the first configuration of a general documents adapter.

Initial adapter name:

- `documents`

Initial data domain:

- `library`

Initial source/write domain:

- `_docs_library/*.md`

Current behavior to preserve:

- export selected Library docs using configured document export patterns
- stage JSON or JSONL under the Library workflow
- generate readable Markdown-style preview files
- show preview results as selectable document rows
- support document hierarchy display where staged parent-child data exists
- apply summary and hierarchy updates when those write contracts are enabled
- create backups before source writes

The existing [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2) spec remains the behavior baseline for this first adapter.

The implementation may still use internal identifiers such as `library-documents` where a concrete operation id is useful, but the durable adapter concept should be `documents` with Library-specific configuration.

## Future Adapter: Analytics Data

Analytics should be treated as a structured-data adapter, not a document adapter.

Likely first candidate:

- tag registry review and reorganisation

Possible export target:

- `assets/studio/data/tag_registry.json`

Likely workflow shape:

- export registry data and enough related context for LLM analysis
- stage proposed tag definition changes, merges, splits, or deprecations
- validate proposals against works, series, and any other tag references
- preview a domain-specific apply plan rather than document files
- require explicit checks before writing core JSON files

This adapter needs its own validation and apply model because it edits core data with relationships across the site.
Its domain is tag data, not a route scope.

## Future Adapter: Catalogue Data

Catalogue should also be treated as domain-specific.

Likely candidates:

- works
- work prose
- work relationships
- selected structured metadata for LLM review

Catalogue may use the same shared lifecycle, but it should not inherit document-import behavior by default.
Its adapter will need relationship validation, source ownership rules, and apply boundaries that match Catalogue data.

## Folder And Data Layout

The current `var/` import/export folders should be replaced by config-declared adapter paths as part of the adapter implementation.
They currently contain only testing content, so there is no durable migration requirement for existing staged or preview files.

Candidate direction:

- keep workflow files grouped under a common export/import root
- make folder layout data-domain-first from the user's perspective
- keep adapter identity in metadata or a lower-level path only where it is operationally useful
- avoid path names that imply every scope is document-based

The implementation should move to the config-declared paths in the first refactor.
If paths change, old test artifacts do not need to be preserved.

User-facing folder discovery should favor paths that are easy to understand, such as a Library staging area for Library document work.
Users should not need to know which adapter is handling that folder.

## Draft Implementation Tasks

### Task 1. Inventory Current Document Assumptions

Status:

- completed

Review the current Library export/import route scripts, server endpoints, import service code, config, and docs.
Classify each behavior as either shared-shell lifecycle or Library-document adapter behavior.

#### Task 1 Inventory

Inventory date:

- 2026-05-06

Current implementation files reviewed:

- `studio/export/index.md`
- `studio/import/index.md`
- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/data/library_export_configs.json`
- `assets/studio/data/library_export_configs.schema.json`
- `scripts/docs/docs_export.py`
- `scripts/docs/docs_import.py`
- `scripts/docs/docs_management_server.py`
- `tests/python/test_docs_export.py`
- `tests/python/test_docs_import.py`
- `tests/python/test_docs_import_service.py`
- `_docs/library-export.md`
- `_docs/library-import.md`
- `_docs/config-library-export-configs.md`
- `_docs/data-models-library.md`

Shared-shell lifecycle behavior:

- route boot, ready, busy, and local-service availability state
- scope or data-domain selector rendering and URL synchronization
- command button enablement around service health, staged files, selected rows, and running state
- config or staged-file selection controls
- command launch over the docs-management loopback service
- dry-run-aware service responses and result reporting
- status messages, selection summaries, result modals, issue lists, and reopenable result behavior
- output-file reporting without exposing full generated payloads in Studio
- staged-file discovery under a workflow root
- preview/apply request shape basics: scope, staged filename, selected record indices, confirmation state
- minimal local logging of ids, counts, status, and paths instead of full document bodies
- write safety conventions for dry-run mode, backups, source writes, rebuilds, and generated-search refreshes

Library-document adapter behavior:

- generated Docs Viewer index loading from `assets/data/docs/scopes/<scope>/index.json`
- per-doc generated payload loading from `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`
- document identity based on `doc_id`, title, `parent_id`, publication state, viewability, `summary`, headings, and rendered content
- hierarchical document selection, descendant expansion, depth calculation, indeterminate parent checkboxes, and relationship-tree ordering
- document list filters such as no content, not viewable, published exclusion, archive handling, and missing summaries only
- export config schema concepts named around documents: `document_fields`, document rows, document arrays, `explicit_doc_ids`, `include_descendants`, and document text transforms
- supported export field sources such as `parent_title`, `ancestor_ids`, `child_ids`, `current_summary`, `source_text`, `viewable`, and `published`
- rendered-HTML to plain-text conversion for document body export
- import shape detection for Library export families: parent-child relationships, document summaries, and full document content
- minimal hand-authored JSON/JSONL rows treated as document-like records
- parser normalization around `doc_id`, title, `parent_id`, summary/current-summary, headings, source text, and relationship metadata
- current-Library lookup annotations and warnings for unknown docs, unpublished docs, missing generated payloads, and missing or unpublished parents
- Markdown preview rendering with one preview file per document plus an optional relationship-tree preview
- preview row rendering as document rows and relationship-tree rows
- selected document `record_index` apply targeting
- summary apply and hierarchy apply against `_docs_library/*.md`
- source-write rebuild/search refresh for Library docs after summary or hierarchy writes

Mixed or transitional seams:

- the shared routes are now `/studio/export/` and `/studio/import/`, while Library remains the only active implemented data domain
- client modules, DOM ids, ready-state route names, and Studio text keys now use `data-export`/`data-import` naming
- transport endpoints now use neutral `/docs/export` and `/docs/import/...` paths
- staged import files and preview files support `library`, `catalogue`, and `analytics` folders, but the parser and preview renderer still assume document-like records
- source apply is explicitly gated to Library by the client and by `normalize_library_import_scope()` in `scripts/docs/docs_management_server.py`
- `assets/studio/data/library_export_configs.json` has a `scopes` array, but all enabled configs are Library-only and the schema is still Library-named
- tests encode useful Library behavior, but they currently test the document workflow and service seams together rather than a separate shared-shell contract and documents-adapter contract

Initial boundary conclusion:

- The shared shell should own route state, service probing, scope/data-domain selection, command lifecycle, staged-file discovery, result modals, generic counts/issues, dry-run reporting, backup/logging conventions, and dispatch to adapter services.
- The first `documents` adapter should own Docs Viewer generated-data reads, document export configs, document field mapping and transforms, tree selection, document-shaped staged payload parsing, Markdown document preview rendering, and Library summary/hierarchy apply behavior.
- Catalogue and Analytics should not reuse the document parser or Markdown document preview renderer by default. They can reuse the shell lifecycle and then provide structured-data adapters with their own export shape, validation model, preview/result presentation, and apply contract.
- Existing Library-named routes and endpoints are prototype names to replace, not compatibility targets. The first adapter implementation should design cleanly around the shared shell and adapter contract as the sole target.

### Task 2. Define A Minimal Adapter Contract

Status:

- completed

Define the smallest contract needed to keep the current Library workflow running while making future Analytics and Catalogue adapters possible.

Expected contract areas:

- adapter id and labels
- supported data domains
- export configs
- staging and preview paths
- preview generation command
- list/result renderer data
- apply actions
- write targets and backup requirements
- capability flags

#### Task 2 Minimal Contract

Contract goal:

- keep the shared shell reusable for export/import lifecycle work
- move document-specific parsing, preview, list, and apply behavior behind the first `documents` adapter
- leave clear seams for future structured-data adapters without requiring a general plugin framework

Core concepts:

- `data_domain`
  User-facing workflow domain, such as `library`, `catalogue`, or `analytics`.
  This replaces route scope as the primary export/import selection concept for new export/import requests.
- `adapter`
  A stable implementation family selected by data model and workflow needs.
  The first adapter is `documents`; future examples include tag-registry or catalogue-record adapters.
- `operation`
  A command the adapter supports, such as `export`, `import_preview`, `summary_apply`, or `hierarchy_apply`.
- `capability`
  A declared boolean or mode that tells the shell which controls to enable and which unsupported actions to hide or disable.
- `presentation`
  Adapter-owned list/result data that the shell can render without knowing whether an item is a document, tag, work, or relationship proposal.

Minimal adapter registry shape:

The first implementation must add an explicit source-controlled adapter config and schema:

- `assets/studio/data/export_import_adapters.json`
- `assets/studio/data/export_import_adapters.schema.json`

The shell must load this config to resolve requests, capabilities, adapter ids, and folder roots.
Folder structures and dispatch decisions must not be hardcoded in route scripts, client modules, or service handlers.

```json
{
  "schema_version": "export_import_adapters_v1",
  "dispatch": [
    {
      "data_domain": "library",
      "operation": "export",
      "adapter_id": "documents"
    },
    {
      "data_domain": "library",
      "operation": "import_preview",
      "adapter_id": "documents"
    },
    {
      "data_domain": "library",
      "operation": "summary_apply",
      "adapter_id": "documents"
    },
    {
      "data_domain": "library",
      "operation": "hierarchy_apply",
      "adapter_id": "documents"
    }
  ],
  "adapters": [
    {
      "id": "documents",
      "label": "Documents",
      "data_domains": {
        "library": {
          "label": "Library",
          "paths": {
            "export_root": "var/studio/export-import/library/exports",
            "staging_root": "var/studio/export-import/library/import-staging",
            "preview_root": "var/studio/export-import/library/import-preview",
            "backup_root": "var/docs/backups"
          },
          "sources": {
            "docs_index": "assets/data/docs/scopes/library/index.json",
            "docs_payload_root": "assets/data/docs/scopes/library/by-id",
            "source_root": "_docs_library"
          },
          "config": {
            "export_configs_path": "assets/studio/data/library_export_configs.json"
          }
        }
      },
      "capabilities": {
        "export": true,
        "staged_file_listing": true,
        "preview": true,
        "source_apply": true,
        "summary_apply": true,
        "hierarchy_apply": true
      }
    }
  ]
}
```

Dispatch rules:

- a shell request must include `data_domain` and `operation`
- the config may contain multiple adapters that could support a data domain, but dispatch must resolve to exactly one adapter for a specific request
- if dispatch finds no match or more than one match, the shell must fail closed with a clear configuration error
- route scripts and service handlers must not contain fallback logic such as "Library means documents" or hardcoded folder roots

Shared shell contract:

- load available adapters and data domains
- render the data-domain selector and operation/config selectors
- probe the local service and reflect service availability
- dispatch export, staged-file listing, preview, and apply commands
- manage busy/ready state, status messages, command enablement, confirmation flow, and result modals
- render generic selectable lists from adapter-provided presentation rows
- render generic counts, warnings, errors, output files, backup paths, and dry-run state
- avoid document-specific assumptions such as `doc_id`, `parent_id`, summaries, generated payloads, or Markdown preview files
- avoid hardcoded adapter selection, operation dispatch, and workflow folder paths

Adapter service contract:

All adapter service responses should include these common fields where relevant:

```json
{
  "ok": true,
  "adapter_id": "documents",
  "data_domain": "library",
  "operation": "import_preview",
  "dry_run": false,
  "summary_text": "Generated 4 Library import preview files.",
  "counts": {},
  "warnings": [],
  "errors": [],
  "issues": [],
  "output_files": [],
  "backup_dir": "",
  "requires_confirmation": false,
  "presentation": {}
}
```

Operation request boundaries:

- `export`
  The shell supplies adapter id, data domain, config id, target format, and adapter-neutral selection data.
  The adapter resolves that selection against its own model and writes export artifacts only under its declared export root.
- `staged_file_listing`
  The shell asks for staged files for one data domain.
  The adapter returns filename, path, format, size, and modified timestamp without parsing the full payload.
- `import_preview`
  The shell supplies adapter id, data domain, and staged filename.
  The adapter parses the staged payload, validates it enough for preview, writes or plans preview artifacts according to dry-run mode, and returns adapter-owned presentation rows.
- `apply`
  The shell supplies adapter id, data domain, staged filename, selected presentation item ids or record indices, operation id, and confirmation state.
  The adapter owns preflight validation, write allowlists, backups, source writes, rebuild/search refresh, and apply-specific result details.

Presentation row contract:

```json
{
  "id": "alpha-record-1",
  "type": "document",
  "label": "Alpha",
  "meta": "alpha; duplicate doc_id",
  "depth": 1,
  "selectable": true,
  "apply_target": {
    "kind": "record_index",
    "value": 0
  },
  "details": {}
}
```

The shell may render `id`, `type`, `label`, `meta`, `depth`, and `selectable`.
Everything in `apply_target` and `details` belongs to the adapter.
For the current Library workflow, `type: "document"` and `type: "relationship_tree"` are documents-adapter rows, not shared shell concepts.

Write safety contract:

- every write-capable adapter must declare source roots, backup root, and supported apply operations
- apply operations must support preflight and confirmed modes
- confirmed writes must create a backup before source mutation
- dry-run mode must report planned writes without writing source, preview, export, backup, or generated docs/search artifacts
- unsupported data domains must fail closed or expose disabled capabilities rather than falling through to document behavior

First adapter mapping:

- adapter id: `documents`
- initial data domain: `library`
- source data: generated Docs Viewer index and per-doc payloads for Library
- source write root: `_docs_library/*.md`
- export config source: `assets/studio/data/library_export_configs.json`
- import staging input: JSON/JSONL document-like staged files
- preview output: Markdown document previews plus optional relationship tree preview
- apply operations: summary front-matter update and hierarchy `parent_id` update

Route and endpoint requirements:

- the implementation target is neutral shared routes, not Library-named routes
- the implementation target is neutral dispatch endpoints such as `/docs/export`, `/docs/import/files`, `/docs/import/preview`, and `/docs/import/apply`
- new export/import requests should use `data_domain`, not `scope`
- existing Library-named routes and import endpoints should be renamed or replaced as part of the adapter implementation, not retained as compatibility layers

Guardrails:

- do not dynamically load arbitrary adapter code from config
- do not expose adapter ids as primary navigation labels
- do not make document preview files mandatory for non-document adapters
- do not let Catalogue or Analytics staged data reuse the document parser unless that domain explicitly chooses the `documents` adapter
- do not add new Library requirements to the shared shell after this contract is accepted
- do not hardcode adapter decisions or workflow folder structures outside `export_import_adapters.json`

Task 2 benefits and risks:

- Benefit: the first implementation can refactor toward adapters without breaking the current Library workflow.
- Benefit: future Analytics and Catalogue work can reuse lifecycle UI and service safety without inheriting document semantics.
- Benefit: explicit adapter config keeps dispatch and folder ownership visible instead of spreading them across route scripts, client modules, and service handlers.
- Risk: a config file introduced before multiple adapters exist can become abstract too early; keep v0 limited to dispatch, capabilities, paths, and the first `documents` adapter.

### Task 3. Move Library Behavior Behind The Documents Adapter

Status:

- completed

Refactor the current Library workflow so document-specific behavior is owned by the `documents` adapter with Library configuration.

Expected outcome:

- shared shell no longer assumes preview results are documents
- Library document behavior remains available through the neutral shared routes
- status/result UI remains familiar
- source writes still target `_docs_library/*.md`

Implementation note:

- added `assets/studio/data/export_import_adapters.json` and `assets/studio/data/export_import_adapters.schema.json`
- added config-driven dispatch in `scripts/docs/export_import_adapters.py`
- moved active import file listing, preview, summary apply, and hierarchy apply calls to neutral docs-management endpoints:
  - `GET /docs/import/files?data_domain=library`
  - `POST /docs/import/preview`
  - `POST /docs/import/apply`
- changed export calls to send `data_domain` so `POST /docs/export` resolves the `documents` adapter before running the Library export config
- removed the Library-named import service endpoints rather than keeping aliases
- kept the current Studio page identity and result UI stable for this task; generic page naming belongs with the shared shell route refactor

Task 3 benefits and risks:

- Benefit: import/export dispatch now has an explicit adapter registry instead of route-level Library assumptions.
- Benefit: removed import endpoint compatibility aliases now, while the implementation surface is still small.
- Benefit: the document parser and source-apply logic are reachable only after config resolves Library to the `documents` adapter.
- Risk: the browser page still has Library-specific DOM ids and copy keys until the shared shell route refactor handles presentation naming.

### Task 4. Normalize Or Refactor Workflow Folders

Status:

- completed

Decide the config-declared folder layout that replaces the current hardcoded `var/docs/.../library` paths.

Because current `var/` content is test-only, implementation can cleanly refactor those folders if doing so clarifies the adapter model.

Implementation note:

- normalized Library export/import workflow files under `var/studio/export-import/library/`
- configured the `documents` adapter paths as:
  - `var/studio/export-import/library/exports`
  - `var/studio/export-import/library/import-staging`
  - `var/studio/export-import/library/import-preview`
- updated Library export config `output.path_pattern` values to write under the normalized export folder
- changed export output validation so the docs-management service validates against the adapter-declared `export_root`
- changed the import CLI defaults to the same normalized staging and preview layout

Task 4 benefits and risks:

- Benefit: workflow artifacts are now grouped by data domain and no longer imply that every export/import workflow is a Docs Viewer workflow.
- Benefit: export, staging, and preview folders are now declared in adapter config and used by the service boundary.
- Risk: existing local staged or preview files under the old `var/docs/...` test folders will not be discovered; that is acceptable because those files were test-only.

### Task 5. Add Future Adapter Stubs

Status:

- completed

Add explicit placeholder config or docs entries for Analytics and Catalogue adapters without implementing domain apply behavior.

Expected outcome:

- future scope support has a named extension point
- the shared shell can show unsupported or preview-only capabilities without guessing
- Analytics and Catalogue requirements do not need to be added to the Library adapter

Implementation note:

- added `catalogue` and `analytics` adapter entries to `assets/studio/data/export_import_adapters.json`
- marked both future adapters as `status: "stub"` with `planned` export, staged-file listing, and import-preview capabilities
- declared data-domain-first placeholder roots under:
  - `var/studio/export-import/catalogue/`
  - `var/studio/export-import/analytics/`
- updated the adapter schema so capabilities can carry `active`, `planned`, or `unsupported` status and an optional user-facing message
- changed adapter resolution so only active adapters, data domains, and capabilities can dispatch to service behavior
- changed the current export/import pages to read domain availability from the adapter registry and show configured unavailable states for future domains

Task 5 benefits and risks:

- Benefit: Catalogue and Analytics now have named extension points without adding their requirements to the Library document adapter.
- Benefit: future-domain UI availability is config-driven rather than inferred from hardcoded scope lists.
- Benefit: service dispatch fails before document parsing when a request targets a stub adapter.
- Risk: the current pages still use Library route names and document-oriented list rendering until the shared shell route refactor completes.
- Risk: the future stubs reserve folder roots but do not define record contracts, relationship validation, write allowlists, or apply behavior yet.

### Task 6. Update Docs And Verification

Status:

- completed

Update the Library export/import docs, scripts docs, and related UI/shared-shell docs so the adapter boundary is visible.

Add or update checks that verify:

- Library adapter export still works
- Library adapter preview still works
- source-write apply actions remain gated by service capability and confirmation
- unsupported future adapters fail or disable controls clearly

Implementation note:

- updated Library export, Library import, Library export/import v2, Library export config, docs-management, adapter config, Studio config, and site-change-log docs to describe the adapter boundary
- rebuilt generated Studio docs-viewer and Studio docs-search payloads
- added adapter-dispatch tests for active Library resolution and future stub rejection
- added a Studio import smoke case for the Catalogue stub unavailable state
- wired adapter and unsupported-stub checks into `./scripts/run_checks.py`

Task 6 benefits and risks:

- Benefit: the active Library workflow and future-domain stubs are documented through stable docs rather than only the implementation plan.
- Benefit: the standard check profiles now cover active Library export/import behavior, source-write gates, and disabled future adapters.
- Risk: the docs still describe the current Library-named page shells because the neutral shared route rename is a separate refactor.
- Risk: future Catalogue and Analytics docs will need another pass when their real data contracts are specified.

## Resolved Direction

- Adapters should not map one-to-one with route scopes. They should map to data models and workflows.
- Use `data domain` as the export/import concept. Keep `scope` only for existing non-export/import route/runtime terminology until that code is separately renamed.
- The first implementation should use a general `documents` adapter with Library configuration, not a hard-coded `library-documents` adapter as the durable concept.
- Export/import routes should use neutral shared routes as the sole target. Existing Library-named route and endpoint names should be replaced, not preserved as compatibility layers.
- Folder layout should be data-domain-first from the user's perspective, because a user staging Library data should be able to find a Library folder without knowing adapter internals.
- Minimum shared modal result shape is success/failure plus warnings/errors, with optional adapter-owned details.
- The import page provides a selection/reporting space; the adapter populates that space with a list or another domain-appropriate presentation.
- Apply actions should use shared endpoints that dispatch to adapter services.

## Remaining Questions

- How should adapter configs declare write allowlists and backup roots?
- How should an adapter describe relationship dependencies, such as tag registry references to works and series?
- Can relationship dependencies for structured data start from existing core JSON shapes and add explicit adapter metadata only where the core shape is not enough?

## Acceptance Criteria

This request is ready to close when:

- the shared shell responsibilities are documented separately from adapter responsibilities
- the current Library workflow is represented as the first `documents` adapter configuration
- `var/` folder handling is decided and documented
- future Analytics and Catalogue adapters have named extension points
- neutral shared export/import routes and endpoints are implemented without Library-named compatibility layers
- implementation tasks are clear enough to start without adding new domain behavior to the shell

Current status:

- all acceptance criteria for this request are met
- future Catalogue and Analytics behavior remains out of scope beyond named stub adapters

## Related Docs

- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Toolkit Extraction Request](/docs/?scope=studio&doc=site-request-docs-toolkit-extraction)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
