---
doc_id: site-request-export-import-adapters
title: Export Import Adapter Boundary Request
added_date: "2026-05-05"
last_updated: "2026-05-05"
parent_id: change-requests
sort_order: 27
---
# Export Import Adapter Boundary Request

Status:

- proposed

## Summary

Adopt an adapter-based export/import architecture before the current Library workflow becomes heavily used or accumulates more requirements in the shared shell.

The current Library export/import workflow should become the first adapter implementation.
The shared layer should remain a workbench shell for scope selection, command execution, staging, status, and result display.
Domain behavior should live behind scope-specific adapters.

## Decision Direction

Use one shared export/import workbench shell with scope-specific adapters.

Do not make the existing Library document workflow the universal model for every scope.
The Library workflow is document-oriented: it exports documents, stages document-shaped JSON, generates document preview files, and can apply document metadata changes.

Analytics and Catalogue need different domain behavior.
For example, Analytics may export `assets/studio/data/tag_registry.json` for LLM review, receive proposals to merge or redefine tags, validate relationships against works and series, and produce a domain-specific apply plan.
That should not be squeezed into a document preview model.

## Problem

The current shared import/export routes are scope-aware, but much of the implementation language and behavior is still Library-document-specific.

That creates a near-term risk:

- new Library requirements will naturally be added to the shell because there is no adapter boundary yet
- future Analytics and Catalogue workflows will inherit document assumptions that do not fit their data
- the eventual split will be harder after the Library system is in full use
- the broader [Docs Workbench Extraction Request](/docs/?scope=studio&doc=site-request-docs-workbench-extraction) will be harder to reason about if export/import remains mixed with Library semantics

The design issue is not whether scopes should share infrastructure.
They should.
The issue is where domain behavior belongs.

## Goals

- Define the export/import adapter boundary now.
- Refactor the current Library workflow into the first adapter.
- Keep the current Library UI and workflow behavior stable where possible.
- Move document-specific assumptions out of the shared shell.
- Leave clear extension points for Analytics and Catalogue without implementing their full workflows yet.
- Keep staging, preview, result, and backup conventions explicit enough for local write safety.

## Non-Goals

- Do not implement Analytics tag-registry import/apply behavior in this request.
- Do not implement Catalogue export/import behavior beyond keeping a clear future adapter target.
- Do not redesign the Library import/export UI unless the adapter boundary requires small copy or routing changes.
- Do not preserve existing `var/` test content as durable data.
- Do not turn the adapter system into a broad plugin framework before there is more than one real implementation.

## Shared Workbench Responsibilities

The shared shell should own the common lifecycle only:

- route and scope selection
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

## First Adapter: Library Documents

The current Library scope should become the first adapter.

Initial adapter name:

- `library-documents`

Initial source/write domain:

- `_docs_library_src/*.md`

Current behavior to preserve:

- export selected Library docs using configured document export patterns
- stage JSON or JSONL under the Library workflow
- generate readable Markdown-style preview files
- show preview results as selectable document rows
- support document hierarchy display where staged parent-child data exists
- apply summary and hierarchy updates when those write contracts are enabled
- create backups before source writes

The existing [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2) spec remains the behavior baseline for this first adapter.

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

## Future Adapter: Catalogue Data

Catalogue should also be treated as domain-specific.

Likely candidates:

- works
- work prose
- work relationships
- selected structured metadata for LLM review

Catalogue may use the same workbench lifecycle, but it should not inherit document-import behavior by default.
Its adapter will need relationship validation, source ownership rules, and apply boundaries that match Catalogue data.

## Folder And Data Layout

The current `var/` import/export folders can be refactored as part of the adapter implementation.
They currently contain only testing content, so there is no durable migration requirement for existing staged or preview files.

Candidate direction:

- keep workflow files grouped under a common export/import workbench root
- include adapter identity in staging and preview paths
- avoid path names that imply every scope is document-based

The implementation can either retain the existing Library paths temporarily or migrate them to adapter-shaped paths in the first refactor.
If paths change, old test artifacts do not need to be preserved.

## Draft Implementation Tasks

### Task 1. Inventory Current Document Assumptions

Status:

- pending

Review the current Library export/import route scripts, server endpoints, import service code, config, and docs.
Classify each behavior as either shared workbench lifecycle or Library-document adapter behavior.

### Task 2. Define A Minimal Adapter Contract

Status:

- pending

Define the smallest contract needed to keep the current Library workflow running while making future Analytics and Catalogue adapters possible.

Expected contract areas:

- adapter id and labels
- supported scope or scopes
- export configs
- staging and preview paths
- preview generation command
- list/result renderer data
- apply actions
- write targets and backup requirements
- capability flags

### Task 3. Move Library Behavior Behind A Library Documents Adapter

Status:

- pending

Refactor the current Library workflow so document-specific behavior is owned by the `library-documents` adapter.

Expected outcome:

- shared shell no longer assumes preview results are documents
- Library document behavior remains available at the current routes
- status/result UI remains familiar
- source writes still target `_docs_library_src/*.md`

### Task 4. Normalize Or Refactor Workflow Folders

Status:

- pending

Decide whether to keep the current `var/docs/.../library` paths temporarily or move to adapter-shaped paths.

Because current `var/` content is test-only, implementation can cleanly refactor those folders if doing so clarifies the adapter model.

### Task 5. Add Future Adapter Stubs

Status:

- pending

Add explicit placeholder config or docs entries for Analytics and Catalogue adapters without implementing domain apply behavior.

Expected outcome:

- future scope support has a named extension point
- the shared shell can show unsupported or preview-only capabilities without guessing
- Analytics and Catalogue requirements do not need to be added to the Library adapter

### Task 6. Update Docs And Verification

Status:

- pending

Update the Library export/import docs, scripts docs, and related UI/workbench docs so the adapter boundary is visible.

Add or update checks that verify:

- Library adapter export still works
- Library adapter preview still works
- source-write apply actions remain gated by service capability and confirmation
- unsupported future adapters fail or disable controls clearly

## Open Questions

- Should adapters map one-to-one with scopes, or can a scope select between multiple adapters?
- Should `library` use adapter id `library-documents`, `docs-library`, or a more general `documents` adapter with Library config?
- Should current routes stay `/studio/library-export/` and `/studio/library-import/`, or should a later request introduce neutral workbench route names?
- Should folder layout be scope-first or adapter-first?
- What is the minimum result record shape the shared result modal needs?
- How much rendering should be adapter-owned versus handled by shared list and modal primitives?
- Should apply actions be adapter-owned endpoints, or shared endpoints that dispatch to adapter services?
- How should adapter configs declare write allowlists and backup roots?
- How should an adapter describe relationship dependencies, such as tag registry references to works and series?

## Acceptance Criteria

This request is ready to close when:

- the shared workbench responsibilities are documented separately from adapter responsibilities
- the current Library workflow is represented as the first adapter implementation plan
- `var/` folder handling is decided and documented
- future Analytics and Catalogue adapters have named extension points
- implementation tasks are clear enough to start without adding new domain behavior to the shell

## Related Docs

- [Library Export/Import v2](/docs/?scope=studio&doc=library-import-export-v2)
- [Docs Workbench Extraction Request](/docs/?scope=studio&doc=site-request-docs-workbench-extraction)
- [Library Import](/docs/?scope=studio&doc=library-import)
- [Library Export](/docs/?scope=studio&doc=library-export)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
