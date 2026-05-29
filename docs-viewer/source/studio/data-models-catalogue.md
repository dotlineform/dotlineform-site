---
doc_id: data-models-catalogue
title: Catalogue Scope
added_date: 2026-04-01
last_updated: 2026-05-19
parent_id: catalogue
---
# Catalogue Scope

This section covers the current data model for the public catalogue: works, series, moments, detail pages, and catalogue search.
The original long reference has been split by responsibility so source records, generated runtime artifacts, and maintenance rules can be searched independently.

## Boundary

Current checked-in catalogue model families include:

- canonical source records under `assets/studio/data/catalogue/`
- canonical prose sources under `_docs_catalogue/`
- public route stubs under `_works/`, `_series/`, `_work_details/`, and `_moments/`
- shared indexes under `assets/data/`
- per-record payloads under `assets/series/index/`, `assets/works/index/`, and `assets/moments/index/`
- catalogue search under `assets/data/search/catalogue/index.json`
- Studio planning/support data in `assets/studio/data/catalogue_field_registry.json`

Primary writers:

- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json) refreshes route stubs, shared indexes, and per-record catalogue payloads.
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) writes `assets/data/search/catalogue/index.json`.

Primary validator:

- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)

## Child References

- [Source Model](/docs/?scope=studio&doc=data-models-catalogue-source) covers canonical source records, field registry, work-owned files/links, route stubs, and moment source files.
- [Indexes And Payloads](/docs/?scope=studio&doc=data-models-catalogue-indexes) covers shared indexes, per-record runtime payloads, and catalogue search.
- [Maintenance](/docs/?scope=studio&doc=data-models-catalogue-maintenance) covers dependencies, enforcement, performance notes, and update rules.
