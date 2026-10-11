---
draft: false
doc_id: d-20260424-000000-315c1c
title: Studio Config JSON
added_date: "2026-04-24 00:00:00"
last_updated: "2026-10-11 00:00:00"
summary: Checked-in Local Studio route registry, live Catalogue read addresses, and the validated runtime projection.
parent_id: d-20260424-000000-15b6f2

---
# Studio Config JSON

## Authority

`studio/app/frontend/config/studio-config.json` is the checked-in browser bootstrap source for Local Studio.

It owns `app.routes`, the Studio route registry. The current source declares no Catalogue fallback data paths. Catalogue read keys and transport belong to the Studio API and browser data helpers.

It does not own Docs Viewer routes, public catalogue route policy, catalogue write endpoints, canonical schemas, generated payload schemas, or route-local UI copy.

## Route Registry

Each `app.routes` record declares:

- route id from the object key
- label and title
- `/studio/` path
- stable HTML template
- route script
- navigation flag
- shell type
- route-ready id

`studio_app_config.py` validates the registry before it is served. The Work editor at `/studio/catalogue-work/` is the sole current route. [Local Studio Routes](Local_Studio_Routes.md) is the readable exact inventory; the JSON owns the mounted route set.

## Catalogue Read Addresses

`studio-data.js` uses the allowlisted Catalogue server-read keys below. `studio_catalogue_api.py` builds their live canonical projections; no persisted lookup directory is a fallback.

| key | role |
| --- | --- |
| `catalogue_works` | current canonical Works |
| `catalogue_series` | current canonical Series |
| `catalogue_galleries` | current canonical Gallery definitions |
| `catalogue_gallery_record` | exact Gallery definition and relevance pairs |
| `catalogue_lookup_work_search` | live Work search projection |
| `catalogue_lookup_series_search` | live Series search projection |
| `catalogue_lookup_series_base` | exact live Series and member-Work projection |
| `catalogue_work_record` | exact live Work record |

These are read addresses, not source-write contracts or generated-file URLs. Do not add source paths, write targets, adapter configuration, operation logs, or inactive generated outputs to browser configuration.

## Runtime Projection

The source JSON is not the final browser payload. `studio_app_config.py` injects `app.runtime` with:

- host and asset version
- health and runtime-config paths
- public-preview and production site bases
- media and thumbnail settings
- pipeline variants and encoding settings
- route records copied as runtime views

Those values come from Python constants, environment, `_data/pipeline.json`, filesystem mtimes, and the checked-in source config. Do not copy runtime-injected values back into `studio-config.json`.

## Browser Loader

`studio/app/frontend/js/studio-config.js`:

- requires the runtime-config URL from the outer shell meta tag
- fetches and caches the runtime payload
- resolves repo-rooted asset paths
- exposes the route registry used by shell route resolution
- supplies code-owned Studio UI text through `studio-ui-text.js`

It is an accessor layer, not a second config registry or route controller. Local write transport remains in `studio-transport.js`.

## Changing Config

For route changes, update the record, template, script and server validation together. Test maintenance and execution require their own approved scope.

For Catalogue reads, keep the allowed key and response shape in the Catalogue adapter and browser data helper. Named browser endpoint addresses belong to `studio-transport.js`. Runtime config carries the values required by its site/media/pipeline/route consumers.

## Weak Spots

- Runtime route records are duplicated into `app.runtime.views`.
- Catalogue editor/search reads and refreshed Catalogue reader JSON have separate owners and freshness boundaries; configuration must not introduce a persisted-file fallback between them.

The maintained runtime-config and route-validation selection is recorded under [Studio Server Config Cleanup](Testing.md#studio-server-config-cleanup). Other cases in `studio/tests/python/test_studio_app_runtime_config.py` remain separately scoped and unreviewed.

## Bounded Route Assertion Maintenance

The 2026-10-11 server cleanup supersedes earlier deferred Home/field-registry expectations and narrow Series/thumbnail-comparison assertion removals in `test_runtime_config_exposes_adapter_contract`. Its current positive config coverage and the repaired route-validation fixtures are maintained in the linked Testing record. The Docs Viewer route-ready audit and `docs-viewer/tests/python/test_catalogue_works_report_contract.py::test_catalogue_drafts_removed_and_exact_editors_remain_registered` are unchanged by this cleanup and are not claimed as current route evidence.

The separately approved generated-directory reference cleanup removes exactly one obsolete private generated-file path assertion from `studio/tests/python/test_studio_app_runtime_config.py::test_static_path_policy_serves_current_studio_allowlists`. That assertion calls the real static-path policy directly with an inert handler object and a synthetic URL; it does not exercise filesystem serving or HTTP. All remaining assertions and fixtures are unchanged and unreviewed. No replacement cases, harnesses, profile changes or test runs are included. Maintenance uses Python lint, syntax and bounded diff review at low local cost, without service startup, browser/network work or canonical/workspace writes; it establishes no new runtime coverage.
