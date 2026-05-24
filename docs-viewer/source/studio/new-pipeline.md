---
doc_id: new-pipeline
title: New Catalogue Pipeline
added_date: 2026-04-19
last_updated: 2026-05-01
parent_id: archive
sort_order: 23000
---
# New Catalogue Pipeline

Archived: this planning section has been superseded by the current Studio, scripts, data-model, and architecture docs.

This section describes the active catalogue workflow: local Studio maintenance backed by canonical JSON source files.

The goal is not to redesign the public catalogue runtime. The public pages continue to read generated route stubs and runtime JSON artifacts. The source-of-truth change is upstream: Studio writes canonical source JSON through localhost-only services, and runtime data contracts stay stable where possible.

Read this section in this order:

1. **[Current Pipeline Map](/docs/?scope=studio&doc=new-pipeline-current-pipeline-map)** for how canonical catalogue JSON, Studio write services, scoped builds, media scripts, and generated runtime artifacts currently fit together
2. **[Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)** for the proposed canonical JSON source files and how they map from the existing workbook sheets
3. **[Web System Specification](/docs/?scope=studio&doc=new-pipeline-web-system-spec)** for the Studio pages, local write service, validation, bulk edit behavior, and build boundaries
4. **[Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)** for the phased implementation record and the final retirement of workbook-led entrypoints
5. **[Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)** for the next phased Studio roadmap, with Catalogue as the main implementation thread
6. **[Studio E2E Checklist](/docs/?scope=studio&doc=new-pipeline-studio-e2e-checklist)** for the first full execution pass across Studio and public-runtime follow-through
7. **[UI](/docs/?scope=studio&doc=ui)** and **[Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)** for current UI guidance; historical UI decisions now live in structured docs-log entries
8. **[Library](/docs/?scope=studio&doc=library)** for the parallel Library planning track
9. **[Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)** for the parallel Analytics planning track
10. **[Search Plan](/docs/?scope=studio&doc=new-pipeline-refine-search)** for the parallel Search planning track

## Scope

In scope:

- maintaining catalogue metadata through Studio-owned JSON source files
- making Studio-owned JSON files the canonical source for works, work details, and series
- keeping current runtime-critical JSON files stable wherever possible
- adding local Studio pages for searching, editing, adding, deleting, and bulk-editing catalogue source records
- keeping media storage conventions and media derivative scripts functionally unchanged
- retaining a workbook import path for bulk additions, but not for editing currently published records

Out of scope for the first implementation pass:

- changing public page layouts or public runtime JSON contracts
- changing how source media files are named and stored
- replacing the current tags system
- turning Studio into a remote multi-user CMS
