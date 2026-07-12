---
doc_id: docs-viewer-documentation-register
title: Docs Viewer Documentation Cleanup
added_date: 2026-07-11
last_updated: 2026-07-12
ui_status: in-progress
summary: Focused work to improve Docs Viewer entry points, current owner documents, workflow guidance, request hygiene, and navigation.
parent_id: change-requests
viewable: true
---
# Docs Viewer Documentation Cleanup

## Status

Active documentation work for the `studio` corpus.

The initial authority audit is complete. This request keeps only the current owner map and the remaining cleanup batches; it is not a historical inventory of every reviewed document.

## Outcome

Make the Docs Viewer documentation easier to enter, trust, and maintain:

- short task-oriented entry points for users and maintainers
- one clear current owner for each architecture and workflow contract
- user guidance separated from implementation reference
- active requests limited to genuinely proposed or in-progress work
- completed outcomes transferred to durable owners without retaining execution chronology
- concise summaries and navigation where they materially improve discovery

The `studio` corpus remains the single reference scope for development and maintenance documentation. This request does not create another docs scope or navigation system.

## Current Owner Map

| subject | current owner | supporting reference |
| --- | --- | --- |
| Docs Viewer entry and routing | [Docs Viewer](/docs/?scope=studio&doc=docs-viewer) | [Overview](/docs/?scope=studio&doc=docs-viewer-overview) |
| public/manage/review runtime boundary | [Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) | [Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces) |
| browser module responsibilities | [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) | [JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) |
| generated payloads and provider reads | [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts) | [Builder](/docs/?scope=studio&doc=scripts-docs-builder) |
| source roots and hierarchy | [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) | [Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer) |
| hosted views and toolbar placement | [Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts) | [Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model) |
| Docs Review | [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) | [Returned Package Review](/docs/?scope=studio&doc=data-sharing-documents-returned-package-review) |
| Docs Import | [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import) | [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec) |
| Data Sharing document export | [Data Sharing](/docs/?scope=studio&doc=data-sharing) | [Documents Prepare Profiles](/docs/?scope=studio&doc=data-sharing-documents-prepare-profiles) |
| management HTTP and Python owners | [Management Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints) | [Management Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts) |
| development and verification rules | [Development Checklist](/docs/?scope=studio&doc=development-checklist) | [Testing](/docs/?scope=studio&doc=testing) |

If a cleanup batch changes one of these boundaries, update the owner map in the same change.

## Batch 1: Entry Points

Focus the primary entry documents around reader tasks:

- make [Docs Viewer](/docs/?scope=studio&doc=docs-viewer) a short router for reading, managing, importing, exporting, reviewing, setup, architecture, and reference
- keep [Overview](/docs/?scope=studio&doc=docs-viewer-overview) concise and architectural rather than a file inventory
- create or focus a maintainer path through current owners instead of linking through completed requests
- remove implementation chronology once current owners are linked

The entrypoint should help a reader choose the next document without requiring knowledge of internal module names.

## Batch 2: User And Operator Workflows

Separate task steps from service and parser detail for:

- browsing, search, recent documents, bookmarks, display modes, and information panels
- source editing, rebuilds, reports, and troubleshooting
- Docs Import and reviewed-package collection import
- Data Sharing preparation and export
- scope creation, deletion, and portable setup
- image, attachment, and interactive asset handling

User guides should describe shipped UI and decisions. Endpoint, script, schema, parser, and security detail should live in the linked reference owner.

## Batch 3: Architecture And Setup Overlap

Reconcile the remaining groups that describe the same boundary from different angles:

### Runtime, Panels, And Controls

- keep current app-context and session-domain behavior in runtime owners
- remove extraction chronology from Panel Hosts
- keep placement in Toolbar Model and availability in the code-owned view/mode/control projection
- retire overlapping capability prose only after the retained owner states the current rule

### Config, Routes, And Portable Setup

- distinguish canonical app config, route records, browser-safe projection, local service config, and code-owned definitions
- keep setup procedures in portable setup documents
- keep route-shell contracts in the static/public template owners
- keep public-scope architecture separate from step-by-step scope creation
- remove repeated file lists when a focused manifest or inventory already owns them

### Import, Export, And Media

- keep operator steps in workflow guides
- keep package shapes in Data Sharing/export references
- keep import normalization, planning, and apply contracts in the import architecture owner
- keep media path, containment, transformation, and manual-copy rules in one focused media reference

## Batch 4: Request Hygiene

For every request-shaped document:

- keep it active only while proposed or implementation work remains
- transfer shipped behavior and durable decisions to current owner documents
- remove completed checklists, verification logs, phase history, and superseded alternatives
- retain a short link to the durable outcome only when it aids navigation
- delete or supersede the request when it no longer owns work

Priority candidates:

- [Docs Viewer Remaining Architecture Work](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap) — keep only trigger-based architecture candidates
- [Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor) — separate implemented behavior from any remaining editor proposal
- [Embedded Detail Documents Request](/docs/?scope=studio&doc=site-request-docs-viewer-embedded-detail-documents) — transfer shipped behavior and retain only unresolved work
- [Data Sharing Full Document Export Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package) — keep export-only implementation work focused

Do not preserve completed requests merely as historical reading material. Git history remains the implementation record.

## Batch 5: Summaries And Discovery

Add summaries first to documents that appear as entry points, high-level architecture owners, user workflows, or active requests. A summary should say what the document helps the reader do or decide; it should not repeat the title.

Do not treat summary coverage across every endpoint or file inventory as a goal by itself. Mechanical reference summaries can follow only when they improve search or navigation.

If current search behavior still makes the corpus difficult to use after entrypoint and summary work, create a separate Documentation Search Discovery And Relevance request with an explicit ranking and result-presentation outcome.

## Working Method

Use small batches:

1. name the current owner and the overlapping documents
2. transfer current behavior and durable constraints to that owner
3. focus user/operator guidance on the task
4. update inbound links and navigation
5. remove redundant or historical prose in the same batch
6. run the docs and search dry-run checks

When a document mixes unrelated responsibilities, split only if both resulting owners are clear. Otherwise focus it around the strongest existing owner.

## Non-Goals

- creating another documentation scope
- preserving completed requests as a history archive
- rewriting the whole corpus in one batch
- changing runtime behavior while reorganizing prose
- duplicating endpoint or module inventories in overview documents
- adding classification metadata without a consumer
- using document length as an automatic failure condition

## Completion Criteria

This request is complete when:

- the Docs Viewer entry documents route users and maintainers by task
- each retained current contract has one clear owner
- user workflows no longer carry unnecessary service or parser inventories
- overlapping runtime, setup, import/export/media, and request prose has been focused or removed
- active requests contain only remaining work
- key entry points and active requests have useful summaries
- internal links and generated docs/search payloads validate cleanly

Completed batch chronology should not accumulate in this request. Update the remaining batch list, transfer durable outcomes, and keep moving toward closure.
