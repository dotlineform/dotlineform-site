---
doc_id: studio-data-sharing
title: Analytics Data Sharing Runtime
added_date: 2026-05-06
last_updated: 2026-07-15
parent_id: data-sharing
viewable: true
---
# Analytics Data Sharing Runtime

## Host Boundary

Analytics owns the two Data Sharing routes, same-origin APIs, runtime endpoint projection, browser state, and UI. `data-sharing/` remains a headless subsystem. Docs Viewer and Analytics tag services supply domain helpers but do not host Data Sharing HTTP routes.

Local Studio has no Data Sharing routes, APIs, aliases, proxies, config serving, or static shims.

## Browser Execution Path

```text
/analytics/data-sharing/prepare/ or /review/
  -> Analytics route template/controller
  -> UI-safe Data Sharing config
  -> same-origin Analytics Data Sharing endpoint
  -> data_sharing_service.py
  -> headless workflow/dispatch
  -> configured adapter family
  -> domain helper + external workspace
```

Prepare asks the adapter for selectable records. The browser does not read generated Docs Viewer indexes as a generic source and does not fetch adapter config directly.

## API Groups

The exact paths are projected by `analytics_data_sharing_api.service_endpoints()` and dispatched by `analytics_data_sharing_api.py`:

- health and safe configuration;
- selectable records;
- returned packages and returned records;
- prepare and editable prepare-context updates;
- review;
- apply.

Read the endpoint constants/dispatch when exact methods or payload fields matter. This page deliberately does not mirror the full API table.

## Route Responsibilities

### Prepare

- choose domain/profile/format and required selectors;
- load adapter-owned selectable records;
- send normalized selected IDs/context;
- display package path, counts, warnings, and errors.

### Review

- list staged files with trusted metadata;
- load normalized review rows/issues;
- create review evidence or a validated Docs Review projection;
- preview/confirm configured apply actions;
- display domain-owned result counts.

## Ready/Busy And Activity

Both templates use the Analytics route-ready contract. Network operations set busy; missing workspace/service state remains visible and disables capabilities.

Successful prepare/apply actions may append normalized Admin activity entries. Selection, filters, preview-only reads, and unavailable-service state are not canonical activity.

## Weak Spots

- Prepare/review controllers coordinate generic UI plus domain-specific exceptions, especially document scope/content and Docs Review projection.
- Public config includes operation-owned UI copy; frontend defaults can still create a second copy source.
- Review row selection and apply payload selection are not currently aligned for document apply: the browser omits `record_indices`.
- The host adapter module imports Docs Viewer and Analytics dependencies directly, so new domains increase Analytics server composition even though the subsystem is headless.

Run the Analytics Data Sharing API/service tests for server changes and the focused route smoke only when route/module wiring changes.
