---
doc_id: new-pipeline-current-pipeline-map
title: Current Pipeline Map
added_date: 2026-04-17
last_updated: "2026-05-09 21:28"
sort_order: 1000
---
# Current Pipeline Map

Archived: the current catalogue model and build boundaries now live in [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue) and [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json).

This document maps the current JSON-source catalogue pipeline.

## Source Boundary

Canonical catalogue metadata lives under:

```text
assets/studio/data/catalogue/
```

Current source families:

- `works.json`
- `work_details.json`
- `series.json`
- `moments.json`
- `meta.json`

Work-owned downloads and links are stored directly on work records as `downloads` and `links`. Retired standalone file/link source families are not part of the current source boundary.

Other canonical inputs:

- source media under `DOTLINEFORM_PROJECTS_BASE_DIR`
- repo-local catalogue prose under `_docs_catalogue/`
- Studio-owned local state such as tag assignments and activity feeds where documented by their owning pages

## Studio Maintenance

Studio is the normal editing surface for catalogue source records. Local write services validate requests, write only allowlisted files, and create backups for write operations.

Main Studio flows:

- edit works, work details, and series
- add new works and details through the configured bulk-import workflow
- preview delete operations before applying them
- preview and run scoped builds
- review catalogue build/source activity

## Build Boundary

The live rebuild entrypoint is:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py
```

The build path reads canonical JSON source records and invokes the internal generator boundary. `generate_work_pages.py` remains the internal generation engine, not the user-facing command.

Generated runtime artifacts include:

- route stubs under `_works/`, `_series/`, `_work_details/`, and `_moments/`
- aggregate indexes under `assets/data/`
- per-record runtime payloads under `assets/works/index/`, `assets/series/index/`, and `assets/moments/index/`
- Studio lookup and storage helper artifacts where selected by the build rules

Search remains downstream of generated/runtime artifacts:

```bash
./studio/services/catalogue/search/build_search.rb --scope catalogue --write
```

## Deprecated Boundary

Workbook-led scripts and historical workflow docs are retained only where they provide clean-exit guidance or archived implementation context. They should not be treated as current source ownership or as hidden compatibility paths.

## Related References

- [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline)
- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
