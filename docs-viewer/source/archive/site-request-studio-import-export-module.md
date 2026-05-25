---
doc_id: site-request-studio-import-export-module
title: Studio Data Sharing Module Implementation Request
added_date: 2026-05-13
last_updated: "2026-05-13 18:15"
ui_status: done
sort_order: 28000
viewable: true
---
# Studio Data Sharing Module Implementation Request

Status:

- Done
- Slice 7 cleanup and technical spec consolidation implemented
- Durable implementation details moved to [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing), [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec), and [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)

## Summary

Implement Studio Data Sharing as its own portable module with domain adapters.

This request follows the closed [Import/Export System Review Request](/docs/?scope=studio&doc=site-request-import-export-system-review) and the completed [Docs Management Service Slices](/docs/?scope=studio&doc=site-request-script-structural-review-docs-management-server).
The Docs management service cleanup is complete, and structured data sharing orchestration should now move into an explicitly owned module instead of continuing to grow inside the docs-management service.

The target direction is:

- Studio Data Sharing is a separate installable package or module in future portable environments
- Docs Viewer can ship with a documents data sharing adapter as an optional companion
- domain adapters own document, tag, catalogue, and future data-model package behavior
- the shared shell owns only lifecycle, transport, registry resolution, status, selection, confirmation, and result presentation contracts

## Terminology

Use **Data Sharing** as the canonical feature name.

The previous import/export language is overloaded in this repo.
It clashes with [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import), Catalogue bulk import workflows, and programming-language `import` terminology.
It also describes file movement rather than the real workflow: selected project data is packaged for an external service, often an LLM, and returned structured data is reviewed before any local changes are applied.

Use these terms in new UI, docs, and code:

- feature and UI area: `Data Sharing`
- code namespace: `data_sharing`
- adapter type: `data sharing adapter`
- outbound operation: `prepare package`
- outbound artifact: `share package` or `outbound package`
- configuration: `sharing profile`
- returned artifact: `returned package`
- staged returned artifact list: `returned packages`
- review operation: `review returned package`
- apply operation: `apply returned changes`
- generic operation verbs: `prepare`, `list_returned`, `review`, and `apply`

Avoid these terms in new contracts except when documenting legacy files, routes, or historical requests:

- `import/export`
- `export`
- `import`
- `import_preview`
- `import_apply`

Existing public docs and source names may still use historical terms until the implementation slice replaces them.
Do not add new user-facing UI labels or new module names using import/export terminology.
`import` remains acceptable for programming-language import statements and historical references in archived docs.

## Rationale

The current implementation has a useful first adapter registry, but the executable behavior is still mostly document-shaped.
The registry can declare Library, Catalogue, and Analytics domains, but the Docs management service currently resolves only the documents adapter for real package preparation and returned-package review work.
The `/studio/export/` and `/studio/import/` shells also still assume generated docs indexes, `doc_id` rows, document preview files, and summary/hierarchy apply actions.

That is workable for the Library document workflow, but it is the wrong place to add tags.
Tags are Analytics-owned data that relate to Catalogue series and works through `assets/studio/data/tag_assignments.json`, `assets/studio/data/tag_registry.json`, and `assets/studio/data/tag_aliases.json`.
They need registry, alias, assignment, validation, review, apply, backup, and activity behavior that is not document-shaped.

The local Studio analytics API already has extracted domain owners for those behaviors.
The missing layer is a shared Data Sharing contract that can call those owners without making the Docs management service or the document package adapter responsible for Analytics data.

## Portability Direction

Treat Data Sharing as a module that can be installed separately from Docs Viewer.

In this repo, the module can live under Studio because it serves the current data-sharing workflow routes.
In a portable setup, it should be possible to install:

- Docs Viewer core only: read-only viewer, generated docs data, search, and optional local docs management
- Docs Viewer plus documents data sharing adapter: package preparation and returned-package review support for Docs Viewer corpora
- Studio Data Sharing module: shared shell, adapter registry, local service dispatch, and any installed adapters
- Analytics tags adapter: tag registry, alias, and assignment package/review/apply behavior

Docs Viewer should not own the whole Data Sharing module.
It should provide or ship with a documents data sharing adapter because document package preparation and returned-package review are natural companions to Docs Viewer management.
The shared Data Sharing registry, gateway, and non-doc adapters should remain portable outside Docs Viewer.

## Ownership Boundary

### Shared Studio Data Sharing module

Owns:

- adapter registry loading and validation
- domain and capability discovery
- local service dispatch for package preparation, returned-package listing, review, and apply
- common request and response envelopes
- common outbound-package, returned-package, and review-output path safety checks
- shared dry-run, confirmation, status, and result-display contracts
- common activity append timing and adapter-provided activity metadata

Does not own:

- document parsing or Markdown preview generation
- tag registry, alias, assignment, or catalogue relationship validation
- domain-specific source writes
- domain-specific backup payload content
- domain-specific review row semantics beyond the presentation contract

### Documents adapter

Owns:

- Library and future Docs Viewer corpus sharing profiles
- generated docs index and payload reads for package selection
- staged document JSON/JSONL parsing
- document review files
- summary and hierarchy apply planners
- Docs source writes and same-scope docs/search rebuild follow-through

This adapter is the one that should be packaged alongside Docs Viewer when a portable install wants document data sharing.

### Analytics tags adapter

Owns:

- `tag_registry.json` package/review/apply behavior
- `tag_aliases.json` package/review/apply behavior
- `tag_assignments.json` package/review/apply behavior
- validation against tag policy, aliases, series, and work membership
- registry, alias, and assignment review/apply planning
- writes/backups using existing Analytics tag transaction helpers
- activity record groups for tags, series, works, aliases, and files

Initial adapter identity:

- `data_domain`: `tags`
- `adapter_id`: `analytics-tags`
- `module`: `analytics.tags`

Use `tags` rather than broad `analytics` for the first real non-document adapter so future Analytics scoring or registry workflows do not inherit tag-specific assumptions.

## Adapter Contract Direction

Keep one registry, but extend it into a v2 capability contract before adding tags.

The minimum contract should cover:

- adapter id, module, label, status, and portability package
- data domains supported by the adapter
- operation capabilities such as `prepare`, `list_returned`, `review`, and adapter-specific apply operations
- selection model: `documents`, `records`, `file_only`, or `none`
- configured source records endpoint or source data paths
- outbound package root, returned package staging root, review output root, source-write targets, and backup root
- supported input and output formats
- review row presentation fields
- apply operation definitions and confirmation copy
- activity context metadata, including script purpose and record groups
- dry-run and confirmation requirements

The shared review response should be record-oriented rather than document-oriented.
For example, a tags review row should be able to describe a tag, alias, series assignment, warning, conflict, or whole-file operation without fabricating a `doc_id`.

Minimum shared review row shape:

```json
{
  "id": "registry:subject:trees",
  "type": "tag",
  "title": "subject:trees",
  "meta": "replace existing tag",
  "record_index": 0,
  "selectable": true,
  "record_groups": {
    "tags": ["subject:trees"]
  },
  "issues": []
}
```

The current Library document response can be adapted into this shape without changing the document adapter's internal parsing and apply behavior.

## Implementation Approach

Normal Studio data sharing operations can be suspended during this implementation except when they are explicitly needed for testing.
The goal is a clean cutover, not a compatibility-preserving migration.

Do not create compatibility layers by default.
If a temporary compatibility layer is absolutely critical to complete a mid-step safely, that layer must be named as temporary in the slice notes and removed before that slice is accepted.
Acceptance criteria for any slice that introduces such a bridge must include its removal.

Do not keep temporary implementation artifacts.
Any generated fixtures, transitional route aliases, one-off config files, duplicate registries, or scratch data created to support implementation must be deleted in an explicit cleanup step before closeout.

Consolidate planning and review documentation into a permanent technical spec during closeout.
The final implementation should leave one durable Data Sharing technical spec plus the normal user-facing docs.
Earlier planning and review documents should be archived after their decisions have been carried forward.

## Suggested Implementation Slices

### Slice 0: terminology cutover without behavior change

Status: in progress.

Apply Data Sharing terminology to the existing implementation before changing architecture.
This is a significant rename-only slice and should not change user-visible behavior beyond labels, route names, and terminology.
The purpose is to remove overloaded import/export names before adding the new adapter contract.

Implementation targets:

- `/studio/export/` and `/studio/import/` route pages become Data Sharing routes
- create a Data Sharing home page, expected at `/studio/data-sharing/`, with links to the outbound package preparation and returned-package review pages
- move the existing outbound package page to `/studio/data-sharing/prepare/`
- move the existing returned-package review page to `/studio/data-sharing/review/`
- delete the old active `/studio/export/` and `/studio/import/` routes as part of the same slice
- add Data Sharing as a top-level Studio nav item
- settle the top-level Studio nav order as Studio, Catalogue, Analytics, Data Sharing, Docs
- remove data sharing operation links from Catalogue and Analytics dashboards so those workflows start from the Data Sharing dashboard
- `assets/studio/js/data-export.js` and `assets/studio/js/data-import.js` move to Data Sharing module names
- `assets/studio/js/export-import-adapters.js` moves to `assets/studio/js/data-sharing-adapters.js`
- `assets/studio/data/export_import_adapters.json` moves to `assets/studio/data/data_sharing_adapters.json`
- `docs-viewer/services/export_import_adapters.py` moves to a Data Sharing owner name, preferably under `scripts/studio/`
- existing UI text keys and labels move from data import/export language to Data Sharing language
- existing tests move from export/import names to Data Sharing names
- Studio route state, activity context, route ids, script purpose ids, and config data-path keys use Data Sharing terminology
- `studio_config.json`, UI text files, data path keys, route registries, activity config, and any generated/static config references are renamed together
- docs that describe the live UI are updated to Data Sharing terminology

Acceptance checks:

- no functional behavior changes beyond terminology, route names, and file/module names
- no compatibility routes, wrappers, duplicate modules, or duplicate config files remain at slice acceptance
- all references to renamed files, routes, config keys, route ids, activity ids, and UI text keys are updated in the same slice
- `/studio/data-sharing/` exists as the home page for the workflow and links to package preparation and returned-package review
- existing `/studio/export/` and `/studio/import/` pages have moved to `/studio/data-sharing/prepare/` and `/studio/data-sharing/review/`
- old active `/studio/export/` and `/studio/import/` routes are deleted rather than retained as redirects or aliases
- the top-level Studio nav exposes Data Sharing in the settled order: Studio, Catalogue, Analytics, Data Sharing, Docs
- Catalogue and Analytics dashboards do not expose separate data sharing operation links
- historical Studio Activity rows may keep old `data-export` and `data-import` ids, but all newly written activity context ids use Data Sharing terminology
- existing Library package preparation, returned-package listing, returned-package review, summary apply, and hierarchy apply flows still work in targeted smoke tests
- old import/export route names and module names are absent from active code except where archived docs or historical notes intentionally mention them
- no new adapter contract behavior is added in this slice

### Slice 1: adapter contract

Status: implemented.

Define the v2 adapter contract in docs and tests after the terminology cutover.

Implementation targets:

- `assets/studio/data/data_sharing_adapters.json`
- shared owner such as `studio/app/server/studio/data_sharing_adapters.py`
- `studio/tests/python/test_data_sharing_adapters.py`

Acceptance checks:

- registry rejects duplicate domain/operation dispatch
- registry rejects unsafe paths
- registry distinguishes planned, stub, active, and disabled capabilities
- registry can resolve document and tags adapter definitions
- capability metadata includes selection, apply, activity, and path contracts
- adapter contract operation names use `prepare`, `list_returned`, `review`, and `apply`

### Slice 2: shared service gateway cutover

Status: implemented.

Extract shared data sharing dispatch out of `docs-viewer/services/docs_management_server.py` into a Studio-owned data sharing service module.

Implementation targets:

- new shared service owner: `studio/app/server/studio/data_sharing_service.py`
- neutral data sharing route constants: `studio/app/server/studio/data_sharing_routes.py`
- removal of old route ownership from docs-management once the service cutover is complete

Acceptance checks:

- normal data sharing operations may be unavailable during the cutover except for targeted tests
- there are no retained compatibility wrappers or legacy route aliases at slice acceptance
- unsupported adapters fail with explicit planned/stub messages
- Docs management service no longer decides non-document adapter architecture
- data sharing routes remain local-only and loopback-safe

### Slice 3: documents adapter wrapper

Status: implemented.

Move Library document package behavior behind the documents adapter wrapper.

Implementation targets:

- `docs-viewer/services/docs_export.py`
- `docs-viewer/services/docs_import.py`
- possible adapter wrapper such as `docs-viewer/services/documents_data_sharing_adapter.py`
- Data Sharing UI routes

Acceptance checks:

- existing Library sharing profiles still work after cutover
- staged document files still list from the configured staging root
- returned-package review still generates the expected markdown review files
- summary and hierarchy apply still back up, write, rebuild, and append activity as before
- no transitional duplicate adapter wrapper remains

### Slice 4: generic UI presentation contract

Status: implemented.

Refactor the shared UI just enough to render adapter-provided records rather than hardcoded document rows.

Implementation targets:

- Data Sharing UI JavaScript modules
- `assets/studio/js/data-sharing-adapters.js`
- UI text under `assets/studio/data/ui_text/`

Acceptance checks:

- document data sharing renders the Library workflow after cutover
- review rows can render `type`, `title`, `meta`, `record_index`, `selectable`, and `issues`
- apply actions are driven by adapter capability metadata rather than fixed summary/hierarchy buttons
- result modals use adapter-provided count labels where available

### Slice 5: tags adapter review and apply

Status: implemented.

Add the first real non-document adapter by wiring existing tag planners into the shared Data Sharing module.

Implementation targets:

- `studio/services/analytics/tag_source_model.py`
- `studio/services/analytics/tag_assignment_service.py`
- `studio/services/analytics/tag_registry_mutations.py`
- `studio/services/analytics/tag_alias_mutations.py`
- `studio/services/analytics/tag_write_transactions.py`
- new adapter wrapper such as `studio/services/analytics/tags_data_sharing_adapter.py`
- `assets/studio/data/data_sharing_adapters.json`

Acceptance checks:

- tag registry returned-package review validates without writing
- tag aliases returned-package review validates without writing
- tag assignments returned-package review reports conflicts, missing series, invalid rows, and applicable rows
- apply operations require confirmation
- apply operations use existing Analytics tag backup and write helpers
- activity rows include relevant tag, series, work, alias, and file groups

### Slice 6: tags package preparation

Status: implemented.

Add package preparation support for tag registry, aliases, and assignments once tags review/apply behavior is stable.

Implementation targets:

- tags adapter wrapper
- sharing profile or capability metadata for tags
- Data Sharing UI presentation updates if needed

Acceptance checks:

- packages can target registry, aliases, assignments, or a combined tags bundle
- outbound packages include metadata sufficient for later returned-package review
- output stays under the configured outbound package root
- activity rows record the packaged data family and output file

### Slice 7: cleanup and technical spec consolidation

Status: implemented.

Remove temporary implementation artifacts and consolidate durable documentation.

Implementation targets:

- permanent Data Sharing technical spec
- user-facing Data Sharing docs
- archived planning/review docs
- removed temporary fixtures, aliases, duplicate configs, and scratch data
- updated live docs for the Data Sharing home, package preparation, returned-package review, and documents adapter
- archived historical import/export planning docs after their decisions are carried forward

Acceptance checks:

- no temporary compatibility layer remains
- no scratch implementation artifact remains
- planning and review documents have been consolidated into the permanent technical spec
- superseded planning/review docs are archived
- live user-facing docs use Data Sharing terminology, except where they intentionally reference historical names
- current route, module, and UI terminology uses Data Sharing

## Benefits

- prevents Docs management service from becoming the owner of all Studio data movement
- gives tags a clean path into data sharing without pretending they are documents
- keeps Docs Viewer portable by letting it ship a documents adapter without owning unrelated adapters
- creates a practical second adapter that tests the contract against real non-document behavior
- preserves the existing Library workflow while making its document assumptions explicit

## Risks

- the first extraction could widen route and UI touch points if the cutover is not protected by tests
- a too-generic contract could become abstract before the tags adapter proves what is actually needed
- activity and backup semantics differ enough between documents and tags that the shared layer must avoid over-owning domain details
- future portability will be harder if shared data sharing paths stay under `scripts/docs/` for too long

## Initial Verification Plan

- run focused Python tests for adapter registry and documents data sharing service behavior
- run focused tags planner tests after the tags adapter wrapper is added
- run a local Data Sharing smoke test for Library after each UI contract change
- run a local Data Sharing smoke test for tags once the tags adapter is active
- keep broad docs payload rebuilds out of these slices unless docs source behavior changes require regenerated viewer data
