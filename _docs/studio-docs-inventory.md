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

Scanned `_docs/*.md` after the structured change-history refactor and the 2026-05-19 priority/secondary split passes.

Summary:

- Total Markdown docs: `311`
- Over 200 lines: `127`
- Over 300 lines: `77`
- Over 500 lines: `18`
- Over 1000 lines: `1`

Highest-priority split candidates:

1. `_docs/studio-ui-rules.md` - `2474` lines  
   Pending user review before splitting. This is mostly chronological decision-log material. It already has a “Retirement Direction” section, so it should probably become a short current-rules page plus monthly/quarterly UI decision-log child docs.

Completed non-Priority-1 splits on 2026-05-19:

- Priority 2: `_docs/scripts-docs-management-server.md` split into an overview plus generated reads/config, import/rebuild, Data Sharing, write actions, and operations child docs.

- Priority 3: `_docs/scripts-catalogue-write-server.md` split into an overview plus endpoint reference, build/lookup, and operations child docs.

- Priority 4: `_docs/docs-viewer-management.md` split into an archived index plus current state, contract, and write-model child docs.

- Priority 5: `_docs/data-models-catalogue.md` split into an overview plus source model, indexes/payloads, and maintenance child docs.

Completed secondary splits on 2026-05-19:

- `_docs/studio-ui-framework.md` split into an overview plus primitives, modal contract, modal implementation, and review/coverage child docs.
- `_docs/search-field-registry.md` split into an overview plus registry table, field definitions, and field policy child docs.
- `_docs/search-build-pipeline.md` split into an overview plus architecture and per-scope child docs for Catalogue, Studio, Library, and Analysis.
- `_docs/local-setup.md` split into an overview plus toolchain, environment, recovery, and GitHub/Codex child docs.
- `_docs/docs-viewer-portable-setup.md` split into an overview plus file manifest, source shape, and scope setup child docs.

Remaining review candidates:

- `_docs/studio-implementation-plan.md` - `834` lines; likely an implementation-history/archive candidate rather than a current reference split.
- `_docs/implementation-plan.md` - `782` lines; likely similar archive or supersession review.
- `_docs/site-request-catalogue-js-runtime-consistency.md` - `781` lines; request history may need closure/archive review before splitting.
