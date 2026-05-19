---
doc_id: studio-docs-inventory
title: Studio Docs Inventory
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: studio
sort_order: 7505
published: true
viewable: true
---
# Studio Document Inventory

This document is used to identify any large documents in Studio scope that are good candidates for splitting into logical child-documents. The aim is to improve search and readability of long complex documents, especially where they are frequently used for reference during development.

It should be updated following any subsequent review or document-splitting.

## Current Review

Scanned `_docs/*.md` after the structured change-history refactor.

Summary:

- Total Markdown docs: `277`
- Over 200 lines: `126`
- Over 300 lines: `84`
- Over 500 lines: `25`
- Over 1000 lines: `2`

Highest-priority split candidates:

1. `_docs/studio-ui-rules.md` - `2474` lines  
   This is mostly chronological decision-log material. It already has a “Retirement Direction” section, so it should probably become a short current-rules page plus monthly/quarterly UI decision-log child docs.

2. `_docs/scripts-docs-management-server.md` - `799` lines  
   Covers startup, endpoint reference, generated reads, source-config settings, mutations, rebuilds, Data Sharing, security, and verification. Strong candidate for children like endpoint reference, generated reads, source settings, write/rebuild behavior, and Data Sharing integration.

3. `_docs/scripts-catalogue-write-server.md` - `757` lines  
   Similar issue: endpoint inventory, module ownership, delete/publication/import/build behavior, security, and artifacts are all in one page. Split by endpoint family or operational responsibility.

4. `_docs/docs-viewer-management.md` - `739` lines
   Combines management mode behavior, local service expectations, modal workflows, move/order behavior, import integration, and verification notes. Good candidate for child docs around management runtime, write actions, import integration, and ordering/rebuild behavior.

5. `_docs/data-models-catalogue.md` - `554` lines  
   Mixes source records, field registry, work-owned files, moments, indexes, per-record payloads, and search model. Good split candidates: source model, moment model, generated indexes/payloads, catalogue search model.

Secondary candidates:

- `_docs/studio-ui-framework.md` - `541` lines; modal guidance and shared primitives could become focused children.
- `_docs/search-field-registry.md` - `558` lines; long but partly justified as a registry. Could split field definitions from policy.
- `_docs/search-build-pipeline.md` - `495` lines; spans Catalogue, Studio, Library, and Analysis adapters.
- `_docs/local-setup.md` - `461` lines; setup, recovery, environment, and Codex notes could be separated.
- `_docs/docs-viewer-portable-setup.md` - `462` lines; the file manifest/setup procedure looks like a natural child doc.

