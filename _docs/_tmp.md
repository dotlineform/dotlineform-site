---
doc_id: _tmp
title: tmp
added_date: "2026-05-19"
last_updated: "2026-05-19"
parent_id: ""
sort_order: 100000
published: true
viewable: false
---

Scanned `_docs/*.md` under `/Users/dlf/Developer/dotlineform/dotlineform-site`.

Summary:
- Total Markdown docs: `273`
- Over 200 lines: `129`
- Over 300 lines: `87`
- Over 500 lines: `27`
- Over 1000 lines: `5`

Highest-priority split candidates:

1. [site-change-log.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/site-change-log.md:1) - `4217` lines  
   Despite saying it should stay compact, it is larger than its archive children. I’d keep only recent/current entries here and move older May entries into dated children.

2. [studio-ui-rules.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/studio-ui-rules.md:1) - `2474` lines  
   This is mostly chronological decision-log material. It already has a “Retirement Direction” section, so it should probably become a short current-rules page plus monthly/quarterly UI decision-log child docs.

3. [scripts-docs-management-server.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/scripts-docs-management-server.md:1) - `799` lines  
   Covers startup, endpoint reference, generated reads, source-config settings, mutations, rebuilds, Data Sharing, security, and verification. Strong candidate for children like endpoint reference, generated reads, source settings, write/rebuild behavior, and Data Sharing integration.

4. [scripts-catalogue-write-server.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/scripts-catalogue-write-server.md:1) - `757` lines  
   Similar issue: endpoint inventory, module ownership, delete/publication/import/build behavior, security, and artifacts are all in one page. Split by endpoint family or operational responsibility.

5. [data-models-catalogue.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/data-models-catalogue.md:1) - `554` lines  
   Mixes source records, field registry, work-owned files, moments, indexes, per-record payloads, and search model. Good split candidates: source model, moment model, generated indexes/payloads, catalogue search model.

Secondary candidates:
- [studio-ui-framework.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/studio-ui-framework.md:1) - `541` lines; modal guidance and shared primitives could become focused children.
- [search-field-registry.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/search-field-registry.md:1) - `558` lines; long but partly justified as a registry. Could split field definitions from policy.
- [search-build-pipeline.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/search-build-pipeline.md:1) - `495` lines; spans Catalogue, Studio, Library, and Analysis adapters.
- [local-setup.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/local-setup.md:1) - `461` lines; setup, recovery, environment, and Codex notes could be separated.
- [docs-viewer-portable-setup.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/docs-viewer-portable-setup.md:1) - `462` lines; the file manifest/setup procedure looks like a natural child doc.

I’d treat long `site-request-*`, archived implementation plans, and monthly change-log archives as lower priority unless they are still used as active reference docs. Their length is less harmful if they are historical records rather than current operating guidance.