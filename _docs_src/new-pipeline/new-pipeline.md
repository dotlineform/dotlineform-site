---
doc_id: new-pipeline
title: New Cat Pipeline
last_updated: 2026-04-18
parent_id: ""
sort_order: 40
---

# New Catalogue Pipeline

This section describes the active catalogue workflow: local Studio maintenance backed by canonical JSON source files.

The goal is not to redesign the public catalogue runtime. The public pages continue to read the existing generated route stubs and runtime JSON artifacts. The change is upstream: `data/works.xlsx` is no longer the primary editing surface, runtime data contracts stay stable where possible, and Studio writes canonical source JSON through localhost-only services.

Read this section in this order:

1. **[Current Pipeline Map](/docs/?scope=studio&doc=new-pipeline-current-pipeline-map)** for how `build_catalogue.py`, `generate_work_pages.py`, `data/works.xlsx`, media scripts, and generated runtime artifacts currently fit together
2. **[Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)** for the proposed canonical JSON source files and how they map from the existing workbook sheets
3. **[Web System Specification](/docs/?scope=studio&doc=new-pipeline-web-system-spec)** for the Studio pages, local write service, validation, bulk edit behavior, and build boundaries
4. **[Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)** for the phased implementation record and the final retirement of workbook-led entrypoints
5. **[Refine Catalogue](/docs/?scope=studio&doc=new-pipeline-refine-catalogue)** for the next planning pass covering workflow refinement, media/prose handling, activity reporting, and end-to-end testing

## Scope

In scope:

- replacing `data/works.xlsx` as the primary mode of catalogue maintenance
- making new Studio-owned JSON files the canonical source for works, work details, work files, work links, and series
- keeping current runtime-critical JSON files stable wherever possible
- adding local Studio pages for searching, editing, adding, deleting, and bulk-editing catalogue source records
- keeping media storage conventions and media derivative scripts functionally unchanged
- retaining a workbook import path for bulk additions, but not for editing currently published records

Out of scope for the first implementation pass:

- changing public page layouts or public runtime JSON contracts
- changing how source media files are named and stored
- replacing the current tags system
- turning Studio into a remote multi-user CMS
