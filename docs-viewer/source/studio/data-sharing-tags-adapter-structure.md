---
doc_id: data-sharing-tags-adapter-structure
title: Tags Data Sharing Adapter Structure
added_date: "2026-06-21 00:00"
last_updated: 2026-06-21
parent_id: data-sharing
viewable: true
---
# Tags Data Sharing Adapter Structure

The Analytics tags Data Sharing adapter is split by shared workflow plumbing and tag family behavior.
The adapter should stay a thin orchestrator instead of becoming the single place where every tag profile, package shape, review rule, and apply flow accumulates.

## Current Layout

```text
data-sharing/adapters/tags/
  adapter.py
  context.py
  prepare.py
  returned.py

  families/
    registry.py
    aliases.py
    assignments.py
    bundle.py
```

`adapter.py` owns the public `DataSharingAdapterHandlers` wiring for the shared Data Sharing dispatcher.
It validates the adapter resolution, delegates prepare/review/apply/list operations, and keeps compatibility exports for direct tests and legacy local imports.
It should not grow new family-specific package or apply logic.

`context.py` owns generic tags-adapter support:

- adapter validation
- path resolution and path safety
- JSON and JSONL reads/writes
- source loading helpers
- sharing profile lookup
- package metadata construction
- selected-record validation
- activity append helpers

`prepare.py` owns generic prepare dispatch.
It resolves `config_id` to a configured profile, reads that profile's `family`, calls the family package builder, writes the outbound package, and returns the shared prepare result shape.

`returned.py` owns returned-package parsing.
It turns staged JSON or JSONL into a `ReturnedPackage` with a detected family, import mode, normalized import payload, source payload, filename, and input format.

## Family Modules

Family modules own behavior that is specific to one tag data shape.

`families/registry.py` owns registry packages, returned registry review rows, registry subset selection, and registry apply.

`families/aliases.py` owns alias packages, returned alias review rows, alias subset selection, and alias apply.

`families/assignments.py` owns assignment packages, catalogue context attachment, returned assignment preview rows, selected assignment sessions, selected record groups, and assignment apply.

`families/bundle.py` owns bundle package composition.
It combines registry, alias, and assignment package payloads; it should stay prepare-only unless a returned bundle workflow is deliberately designed.

## Profile And Family Boundary

A sharing profile is a configured package option exposed to the prepare UI.
A family is the implementation unit for records that share source shape, package shape, review semantics, and apply behavior.

The current prepare profiles map to families like this:

| Profile | Family | Implementation owner |
| --- | --- | --- |
| `tag-registry` | `registry` | `families/registry.py` |
| `tag-aliases` | `aliases` | `families/aliases.py` |
| `tag-assignments` | `assignments` | `families/assignments.py` |
| `tags-bundle` | `bundle` | `families/bundle.py` |

Adding a new profile should be config-only when it uses an existing family behavior and only changes label, enabled state, supported format, selection defaults, limits, or other options that the family already supports.

Adding a new family module is appropriate when the profile needs a new source shape, package shape, returned-package detection rule, review row model, apply behavior, or validation model.

Do not add unrelated family logic to `adapter.py` or to another family's module.
If a profile starts to require special-case behavior inside a family, prefer adding an explicit family option and keeping that branch local to the family module.

## Selectable Records

Prepare selectable records are adapter-owned.
The shared prepare UI expects generic records in the adapter response:

```json
{ "id": "record-id", "name": "Display name" }
```

The UI must not infer tag record meaning from fields such as `tag_id`, `series_id`, `title`, or `label`.
If the tags adapter exposes selectable records for a profile or family, the relevant family module should normalize source data into the generic `id` and `name` contract before returning it through adapter dispatch.

Future selector controls, such as filtering the prepare list by tag group, should be implemented as a shared selector contract plus family-owned filtering behavior.
Configuration may declare that a selector exists, but code must still implement the selector type, request parameter, and family-side filtering.

## Design Rules

- Keep `adapter.py` thin: handler registration, operation validation, and delegation only.
- Put generic path, source, metadata, and activity helpers in `context.py`.
- Put staged returned-package parsing in `returned.py`.
- Put generic prepare orchestration in `prepare.py`.
- Put family-specific package, review, selection, and apply behavior in `families/<family>.py`.
- Keep config-only profiles config-only when existing family behavior already supports them.
- Avoid compatibility aliases unless there is an explicit migration reason and a removal plan.
- Keep `data-sharing/` headless; browser route code remains in `analytics-app/`.

## Verification

After changing tags adapter structure or behavior, run focused checks that cover both direct adapter imports and Analytics API dispatch:

```bash
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_tags_data_sharing_adapter.py -q
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_data_sharing_service.py analytics-app/tests/python/test_analytics_data_sharing_api.py -q
```

For route-level confidence, run the local Data Sharing smoke:

```bash
$HOME/miniconda3/bin/python3 analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py
```
