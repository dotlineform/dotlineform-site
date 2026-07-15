---
doc_id: studio-config-and-save-flow
title: Studio Read And Save Flow
added_date: 2026-04-22
last_updated: 2026-07-15
summary: How Studio runtime config, safe reads, validated catalogue writes, optional builds, publication, media, and activity fit together.
parent_id: studio
viewable: true
---
# Studio Read And Save Flow

## Configuration Flow

```text
studio-config.json
  -> studio_app_config.py validates routes and data paths
  + environment, pipeline.json, Python runtime constants
  -> /studio/runtime-config.json
  -> studio-config.js caches the browser payload
  -> shell, navigation, data helpers, and route scripts consume focused values
```

[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) owns the source and runtime-projection boundary. Route copy and option lists remain code-owned unless they are genuine shared configuration.

## Read Flow

Studio routes probe catalogue health before server-owned work:

```text
route boots
  -> health probe
  -> server available: use allowlisted /studio/api/catalogue/read
  -> supported fallback workflow: use configured safe JSON path
  -> unavailable workflow: show unavailable state and disable mutation controls
```

`studio-data.js` owns the shared choice between server reads and configured static paths. Active editors and Catalogue Drafts require the local service for their current workflow; there is no offline editing or offline save mode.

Static paths are browser-safe reads, not canonical write targets. Focused record reads and current source truth come from the server when the workflow requires them.

## Save Flow

```text
route action
  -> focused editor/workflow shapes request
  -> catalogue service client / studio-transport.js
  -> /studio/api/catalogue/... adapter
  -> domain service validates identity, hashes, source set, and requested action
  -> preview returns a write-free plan where the workflow requires confirmation
  -> apply revalidates and writes canonical source atomically
  -> optional scoped build, search, publication, or media follow-through
  -> activity and result returned
  -> browser refreshes affected record or lookup state
```

The browser may compute record hashes and patches, but the service validates current source and owns mutation authority. Canonical catalogue writes use `studio/services/catalogue/catalogue_transactions.py` and focused service contexts rather than direct route-script file access.

## Workflow Families

### Works And Series

- create and save use focused work or series services
- existing-record updates include expected record hashes
- published records may request scoped build follow-through
- series membership updates validate both series and affected works
- work-detail sections are aggregate children of the Work editor, not separate route records

### Bulk Changes And Import

- bulk editor changes use one request with the selected ids, expected hashes, and touched fields
- workbook import has separate write-free preview and confirmed apply
- import reads the configured workbook path from server-owned pipeline configuration
- existing records are skipped or blocked according to the focused import plan; Excel is never the write target

### Delete, Publication, Media, And Build

- destructive and remote operations use named preview/apply pairs
- delete plans identify dependent canonical/public/media consequences before apply
- publication changes public status and required output through its focused service
- media publication is separate from canonical record save
- scoped build endpoints own catalogue generation and search follow-through

### Project State

Project State uses its own report and open-report operations. It reads an environment-backed external project root on the server and returns a report result without exposing arbitrary paths to the browser.

## Authority And Failure Rules

- `studio/data/canonical/` is catalogue source authority.
- `studio/data/generated/` and public files are rebuildable projections.
- runtime config and browser paths do not authorize writes.
- source validation occurs before mutation; confirmed apply rechecks current state.
- server unavailability is visible and disables writes.
- remote media cleanup failures may require explicit manual follow-through; they do not make the browser the rollback owner.

Exact endpoint spelling belongs in [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis). Exact domain behavior belongs in focused catalogue services and workflow docs.
