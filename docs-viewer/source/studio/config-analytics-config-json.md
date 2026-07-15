---
doc_id: config-analytics-config-json
title: Analytics Config JSON
added_date: 2026-06-02
last_updated: 2026-07-15
parent_id: analytics
---
# Analytics Config JSON

## Owner

`analytics-app/app/frontend/config/analytics-config.json` is checked source configuration for the Analytics browser app.

It owns:

- `app.routes` — route ID, path, template, controller, shell type, and navigation flag;
- `paths.data.site` — browser paths for the public series/work indexes Analytics reads;
- `analysis.groups` — display/coverage group order;
- `analysis.rag` — implemented tag-completeness thresholds and rules.

It does not own API paths, filesystem roots, public-site base URLs, media hosts, pipeline variants, Data Sharing adapter config, or UI copy. Those are server-, subsystem-, pipeline-, or code-owned.

## Projection Path

```text
analytics-config.json
  -> analytics_app_config.py validates routes/files
  -> server adds environment + service + media + pipeline settings
  -> /analytics/runtime-config.json
  -> analytics-config.js caches browser config
  -> route registry/data/scoring consumers
```

The source JSON is not the complete runtime payload. Exact service endpoints live in `ANALYTICS_SERVICE_ENDPOINTS` and the Data Sharing API projection.

## Change Method

### Route

Add or remove the template/controller and registry row together. The server rejects missing fields/files, duplicate paths, unsupported shell types, and route metadata placed in the old `paths.routes` location.

### Catalogue Input

Keep a data path only while an active browser loader consumes it. A path exposes a dependency; it does not transfer ownership of that artifact to Analytics.

### Group Or RAG Policy

Change policy here and implementation/tests in `analysis-tag-scoring.js` together. Do not turn config into an inventory of possible future scoring models.

### Data Sharing

Change `data-sharing/config/adapters.json` or the selected adapter config. Analytics routes obtain a safe projection from `/analytics/api/data-sharing/config`; they must not read subsystem config files directly.

## Weak Spots

- runtime config also projects routes as `app.runtime.views`, so source and runtime shapes are intentionally different;
- scoring functions retain code defaults for resilience, which can conceal missing config unless tests assert the projection;
- all current route rows have `nav: false`, so the route registry is broader than the visible navigation model;
- media and service settings are Python constants rather than checked JSON policy.

When an exact key inventory matters, read the JSON and `runtime_config()` directly. This page owns the boundary and edit method, not a duplicate schema.
