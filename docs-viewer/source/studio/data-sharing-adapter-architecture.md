---
doc_id: data-sharing-adapter-architecture
title: Data Sharing Adapter Architecture
added_date: "2026-06-21 00:00"
last_updated: 2026-06-21
parent_id: data-sharing
viewable: true
---
# Data Sharing Adapter Architecture

Data Sharing adapters are headless service modules under `data-sharing/adapters/`.
They translate shared Data Sharing operations into domain-specific package, review, and apply behavior while keeping Analytics browser routes generic.

The shared UI and dispatcher should not know whether a record is a document, tag, alias, series, or future domain object.
Adapters normalize domain data into shared request and response contracts.

## Layout Pattern

Adapters should follow this structure:

```text
data-sharing/adapters/<domain>/
  adapter.py
  context.py
  prepare.py
  returned.py

  families/
    <family>.py
```

`adapter.py` is the public dispatch wiring.
It should only build `DataSharingAdapterHandlers` and delegate to operation modules.
It should not re-export implementation helpers, keep compatibility aliases, parse package contents, or contain family-specific package/apply logic.

`context.py` owns shared adapter support:

- adapter validation
- dependency dataclasses
- path/source/config helpers
- common normalization
- logging/activity helpers
- source loading helpers that apply across families

`prepare.py` owns generic prepare orchestration for the adapter.
It resolves the selected profile, maps that profile to a family, calls the family package builder, writes the outbound package when not dry-running, and returns the shared prepare payload.

`returned.py` owns returned-package orchestration.
It lists staged files, parses returned packages, detects package family, dispatches review behavior, and dispatches apply behavior.
Returned-package parsing can live here when it is shared across families.

`families/<family>.py` owns behavior for records that share a source shape, package shape, review model, validation model, and apply semantics.
Family modules may call domain helper services, but they should not own HTTP routing or browser UI behavior.

## Profiles And Families

A profile is a configured option exposed to package preparation.
A family is the implementation unit that knows how to build, review, and apply records.

Adding or changing a profile can be config-only when it uses an existing family and only changes options the family already supports.
Examples include label, enabled state, supported format, selection defaults, limits, or family-owned options.

Adding a new family is a code change.
Use a new family when the work needs a new source shape, package shape, returned-package detection rule, review row model, apply action, validation model, or selector behavior.

Adapters may support multiple profiles through one family.
Adapters may also support multiple families when profiles need materially different record behavior.
Avoid one large domain script that accumulates all profile behavior.

## Selectable Records

Prepare selectable records use a generic contract:

```json
{ "id": "record-id", "name": "Display name" }
```

Adapters may include domain-specific fields for their own use, but browser selection UI must use `id` and `name`.
The UI should not infer record type from fields such as `doc_id`, `tag_id`, `series_id`, `title`, or `label`.

Selectors, such as `docs_scope` or a future tag-group filter, need both config and code:

- config declares that the selector exists and how the UI should expose it
- API requests carry the selected value
- adapter/family code implements filtering and validation

## No Compatibility Layers

Do not keep adapter-level compatibility aliases for moved functions.
When implementation moves from `adapter.py` into `prepare.py`, `returned.py`, `context.py`, or a family module, update imports and tests to use the owning module.

Compatibility aliases are allowed only with an explicit migration reason and removal criteria.
Ordinary local test imports are not a reason to preserve an old surface.

## Browser Boundary

`data-sharing/` remains headless.
Browser route modules live in `analytics-app/` and call same-origin Analytics Data Sharing APIs.
Browser code reads the Analytics API's UI-safe config projection; it must not read `data-sharing/config/...` files directly.

Adapters can call domain helpers:

- documents adapter calls Docs Viewer data-sharing helpers
- tags adapter calls Analytics tag helper services

Those helpers are domain implementation details, not Data Sharing API hosts.

## Verification

After adapter structure changes, run focused checks for the adapter and dispatch boundary.
Typical checks:

```bash
$HOME/miniconda3/bin/python3 -m py_compile data-sharing/adapters/<domain>/*.py data-sharing/adapters/<domain>/families/*.py
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_data_sharing_service.py analytics-app/tests/python/test_analytics_data_sharing_api.py -q
```

Run the adapter-specific tests listed in that adapter's implementation document.
Use the local Data Sharing route smoke when server wiring or browser-facing route behavior changes:

```bash
$HOME/miniconda3/bin/python3 analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py
```
