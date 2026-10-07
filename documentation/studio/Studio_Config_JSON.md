---
draft: false
doc_id: d-20260424-000000-315c1c
title: Studio Config JSON
added_date: "2026-04-24 00:00:00"
last_updated: "2026-10-07 16:46:38"
summary: Checked-in Local Studio route registry, live Catalogue read addresses, and the validated runtime projection.
parent_id: d-20260424-000000-15b6f2

---
# Studio Config JSON

## Authority

`studio/app/frontend/config/studio-config.json` is the checked-in browser bootstrap source for Local Studio.

It owns `app.routes`, the Studio route registry. The current source declares no Catalogue fallback data paths. Catalogue read keys and transport belong to the Studio API and browser data helpers.

It does not own Docs Viewer routes, public catalogue route policy, catalogue or
tag write endpoints, canonical schemas, generated payload schemas, or
route-local UI copy.

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
- a catalogue service endpoint map
- a tag service endpoint map
- tag group and coverage/RAG policy loaded from
  `studio/data/config/tags/tag-management.json`
- public-preview and production site bases
- the data-path projection, empty for the current checked source
- media and thumbnail settings
- pipeline variants and encoding settings
- route records copied as runtime views
- navigation and modal metadata

Those values come from Python constants, environment, `_data/pipeline.json`, filesystem mtimes, and the checked-in source config. Do not copy runtime-injected values back into `studio-config.json`.

## Browser Loader

`studio/app/frontend/js/studio-config.js`:

- requires the runtime-config URL from the outer shell meta tag
- fetches and caches the runtime payload
- resolves repo-rooted asset paths
- exposes focused route and data-path accessors
- supplies code-owned Studio UI text through `studio-ui-text.js`

It is an accessor layer, not a second config registry or route controller. Local write transport remains in `studio-transport.js`.

## Changing Config

For route changes, update the record, template, script and server validation together. Test maintenance and execution require their own approved scope.

For a data-path change:

1. verify active browser and service consumers
2. classify the value as browser-safe static read, focused server URL, server-only path, or generated output
3. keep only browser-safe or intentionally projected read values here
4. update the positive allowed-key tests

## Weak Spots

- Runtime route records are duplicated into `app.runtime.views`.
- Runtime catalogue services and hardcoded browser endpoint constants are overlapping discovery surfaces.
- Catalogue editor/search reads and refreshed Catalogue reader JSON have separate owners and freshness boundaries; configuration must not introduce a persisted-file fallback between them.

Focused runtime-config tests in
`studio/tests/python/test_studio_app_runtime_config.py` protect the route
registry, allowed data keys, tag-policy projection, and current service maps.

## Bounded Route Assertion Maintenance

Home and field-registry route retirement leaves the existing tests and route-ready audit unchanged by explicit user choice. Their obsolete route expectations are deferred to a later full test review; they are not evidence for the current single-page registry. No test suite was run for this retirement.

The approved Series editor retirement removes only three obsolete route assertions: two in `studio/tests/python/test_studio_app_runtime_config.py::test_runtime_config_exposes_adapter_contract` (the route's shell type and runtime view) and one in `docs-viewer/tests/python/test_catalogue_works_report_contract.py::test_catalogue_drafts_removed_and_exact_editors_remain_registered` (its path). Existing positive assertions for the Work editor remain. No new assertions, fixtures, harnesses or profile changes are included, and this maintenance does not certify the other assertions in either test.

The first selector reads the real checked Studio registry through `runtime_config` with temporary environment overrides for local service addresses. The second reads the real registry JSON directly. The maintained route evidence concerns the surviving Work editor registration, not browser interaction, HTTP serving, Series mutations or generated outputs. Test support and temporary-workspace fixtures are unchanged; no service startup or canonical-data write is part of these route assertions.

This bounded edit uses source review and Python lint only; no suite run was approved or performed. A later justified focused run can select either exact node ID above with `python3 -m pytest <node-id> -q` after exporting `.env.local`. Import/fixture costs and unrelated legacy assertions remain unreviewed; expanding execution or cleanup needs its own selection. Maintenance is limited to the three-line deletion and review, with no added runtime or network cost.

The separately approved thumbnail-quality comparison cleanup removes exactly three obsolete absence assertions from `studio/tests/python/test_studio_app_runtime_config.py::test_runtime_config_exposes_adapter_contract`: the retired runtime view, Catalogue service key and Studio data-path key. This selector reads the real registry through `runtime_config` with temporary environment overrides; the remaining Work editor, service and pipeline assertions and all fixtures are unchanged and unreviewed. No replacement cases, fixtures, harnesses, profile changes or test runs are included. Maintenance uses Python lint, syntax and bounded diff review at low local cost, without service startup, browser/network work or canonical/workspace writes; it establishes no new runtime coverage.

The separately approved generated-directory reference cleanup removes exactly one obsolete private generated-file path assertion from `studio/tests/python/test_studio_app_runtime_config.py::test_static_path_policy_serves_current_studio_allowlists`. That assertion calls the real static-path policy directly with an inert handler object and a synthetic URL; it does not exercise filesystem serving or HTTP. All remaining assertions and fixtures are unchanged and unreviewed. No replacement cases, harnesses, profile changes or test runs are included. Maintenance uses Python lint, syntax and bounded diff review at low local cost, without service startup, browser/network work or canonical/workspace writes; it establishes no new runtime coverage.
