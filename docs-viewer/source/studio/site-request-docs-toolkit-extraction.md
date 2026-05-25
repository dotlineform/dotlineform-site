---
doc_id: site-request-docs-toolkit-extraction
title: Docs Toolkit Extraction Request
added_date: 2026-05-05
last_updated: "2026-05-13 21:07"
ui_status: deferred
parent_id: change-requests
sort_order: 8000
viewable: true
---
# Docs Toolkit Extraction Request

Status:

- closed
- see section 'still relevant details' for potential future packaging work

## Summary

This request is closed as a broad extraction proposal.
Its original question was whether the Docs Viewer, generated docs/search pipeline, local Docs management service, and export/import workflow should become one reusable docs toolkit.

That combined boundary is no longer the current direction.
The work has split into clearer, narrower surfaces:

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) tracks the active Docs Viewer portability work.
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) is the current install and copy guide.
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing) describes the shared prepare/review/apply workflow that replaced the old import/export framing.
- [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec) records the Data Sharing adapter, endpoint, registry, row, and portability boundaries.
- [Import/Export Historical Notes](/docs/?scope=studio&doc=import-export) keeps the old terminology only as archive context.

No separate implementation request should be opened from this document unless a later decision intentionally packages these surfaces together again.

## Current Decision

Do not extract a single combined docs toolkit at this stage.

Use these boundaries instead:

- Docs Viewer core: read-only viewer, generated docs data, inline docs search, local management shell, Docs Import, route adapters, config, UI text, CSS, and local Docs management service.
- Documents Data Sharing adapter: optional document package preparation, returned-package review, and document apply behavior for Docs Viewer corpora.
- Studio Data Sharing module: Studio-owned shell, adapter registry, local service dispatch, lifecycle states, confirmations, status presentation, and activity context.
- Non-document adapters: domain-owned implementations such as Analytics tags, with their own source parsing, validation, backups, review rows, writes, and apply actions.

This split keeps Docs Viewer portable without forcing every downstream docs install to accept Studio Data Sharing or non-document data workflows.
It also keeps Data Sharing extensible without making the shared shell learn document-specific or tag-specific semantics.

## What Moved Elsewhere

The original extraction request included several areas that now have more precise homes.

Docs Viewer portability moved to:

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer)

Data Sharing moved to:

- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec)
- [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)

Historical import/export language moved to:

- [Import/Export Historical Notes](/docs/?scope=studio&doc=import-export)
- [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters)
- [Studio Data Sharing Module Implementation Request](/docs/?scope=studio&doc=site-request-studio-import-export-module)

## Still-Relevant Details

The following points from the original request remain useful, but they now belong to narrower follow-up work rather than this broad proposal.

### Upstream And Version Tracking

If Docs Viewer becomes a reusable upstream project, prefer traceable source control before package-manager distribution.

Candidate model:

- create or designate an upstream shared Docs Viewer repo as the master source
- track releases with version tags, a change log, and migration notes
- install into downstream repos with Git subtree or Git submodule while the boundary is still settling
- keep downstream repos responsible for project-local content, routes, theme adapters, and local config
- consider package-manager distribution only after the file boundary, command shape, and config contract have stabilized in at least one fixture install

This belongs to the remaining fixture/upstream work in [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer), not to a combined toolkit request.

### Fixture Validation

The next useful portability test is a minimal downstream Jekyll fixture:

- install the Docs Viewer file set outside dotlineform
- add one read-only docs corpus
- add `/docs/` management for that corpus
- verify search, import initialization, create/edit/move, generated-data reads, and public-route read-only behavior
- record hidden dotlineform assumptions back into the portable Docs Viewer request

### Data Sharing Portability

Data Sharing can become portable later, but it should not be bundled into Docs Viewer core by default.

Open decisions for a future Data Sharing portability request:

- whether the Studio Data Sharing shell is reusable outside this Studio UI
- whether the documents adapter should ship as an optional companion to Docs Viewer
- how a downstream project declares adapter registries, write allowlists, backup roots, package roots, and activity context
- whether non-document adapters belong in a shared package or remain project-local examples
- how package migration notes should handle registry schema changes and adapter response contracts

### License And Visibility

If an upstream Docs Viewer or Data Sharing package is created from dotlineform source, decide first:

- whether the upstream should be public or private
- what license applies to reusable code, docs, and example config
- which dotlineform-specific content, paths, and branding must stay out of the upstream
- how local-only write services and example configs should document loopback binding, path allowlists, and credential handling

## Closed Acceptance

This request is closed because its original acceptance criteria have been superseded or satisfied elsewhere:

- extraction boundary: split into Portable Docs Viewer, optional documents Data Sharing adapter, Studio Data Sharing shell, and domain adapters
- install guidance: tracked in [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- config contract: tracked in Docs Viewer config and Data Sharing adapter config docs
- import/export lifecycle: renamed and clarified as Data Sharing prepare, list returned, review, and apply
- migration/update questions: retained above for future upstream or fixture work
- implementation plan: active work belongs to [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer) and future Data Sharing-specific requests

## Related Docs

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Studio Data Sharing](/docs/?scope=studio&doc=studio-data-sharing)
- [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec)
- [Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)
- [Import/Export Historical Notes](/docs/?scope=studio&doc=import-export)
