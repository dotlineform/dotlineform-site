---
doc_id: data-sharing-tags-adapter-structure
title: Tags Data Sharing Adapter Structure
added_date: "2026-06-21 00:00"
last_updated: 2026-06-21
parent_id: data-sharing
viewable: true
---
# Tags Data Sharing Adapter Structure

The Analytics tags adapter implements Data Sharing for canonical Analytics tag data.
It follows the shared [Data Sharing Adapter Architecture](/docs/?scope=studio&doc=data-sharing-adapter-architecture) and keeps tag-family behavior out of `adapter.py`.

## Layout

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

`adapter.py` only wires `DataSharingAdapterHandlers` for module `analytics.tags`.

`context.py` owns tags adapter support:

- adapter validation for module `analytics.tags`
- shared runtime path resolution
- JSON and JSONL reads/writes
- current tag registry, aliases, and assignments loading
- supporting series and works index loading
- prepare profile lookup
- package metadata helpers
- selected record-id validation for prepare exports
- selected record-index validation
- activity append helpers

`prepare.py` resolves a prepare `config_id` to a tag family and writes outbound JSON packages.
Tags prepare is profile-driven.
Profiles can be profile-only, or they can expose selectable source records through the active family.
The current `tag-registry` profile exposes tag records and uses selected `record_ids` to limit the exported registry package.

`returned.py` lists staged JSON/JSONL files, parses returned packages, detects tag family, builds review payloads, and dispatches apply actions.
It owns the `ReturnedPackage` contract shared by returned-package family code.

## Families

| Family | Module | Prepare | Review | Apply |
| --- | --- | --- | --- | --- |
| `registry` | `families/registry.py` | selectable tag records and tag registry package | registry row preview | `registry_apply` |
| `aliases` | `families/aliases.py` | tag aliases package | alias row preview | `aliases_apply` |
| `assignments` | `families/assignments.py` | tag assignment package | series assignment preview | `assignments_apply` |
| `bundle` | `families/bundle.py` | combined package | none | none |

`bundle` is prepare-only.
It composes registry, aliases, and assignments package payloads for export.
A returned bundle workflow would need an explicit design before review/apply support is added.

## Profiles

Current prepare profiles map to families like this:

| Profile | Family | Selection |
| --- | --- | --- |
| `tag-registry` | `registry` | `explicit_record_ids` |
| `tag-aliases` | `aliases` | `none` |
| `tag-assignments` | `assignments` | `none` |
| `tags-bundle` | `bundle` | `none` |

The profile mapping comes from the tags `prepare` capability in `data-sharing/config/adapters.json`.
If no valid profile list is configured, `context.py` falls back to the built-in default profile map.

Adding a new tags profile can be config-only when it uses an existing family and only changes family-supported options.
Adding a new tags family requires code in `families/`, returned-package detection when imports are supported, and focused tests.

## Prepare Selection

The `tag-registry` profile uses the shared generic prepare list.
`families/registry.py` loads `tag_registry.tags[]` and returns records with the shared `id` and `name` fields:

```json
{ "id": "subject:trees", "name": "trees" }
```

The family can include tag-specific fields such as `tag_id`, `group`, and `status`, but the browser selection UI must use `id` and `name`.
When the prepare request includes `selection.record_ids`, `prepare.py` validates the ids and passes them to `families/registry.py`.
The registry package builder exports only matching source tags, preserving source order.
Unknown selected tag ids fail validation instead of being silently ignored.

The alias, assignment, and bundle profiles currently remain profile-only exports.
They do not expose selectable prepare records until their families define what selected records mean for those package shapes.

## Source Files

The tags adapter reads and writes configured paths from `data-sharing/config/adapters.json`.
Current source/write target keys are:

- `tag_registry`
- `tag_aliases`
- `tag_assignments`
- `series`
- `works`

Registry, aliases, and assignments writes use Analytics tag mutation helpers.
Assignments review also uses the series and works indexes to validate returned assignment payloads and attach activity record groups.

## Returned Packages

`returned.py` detects returned package family from JSON or JSONL payload shape.
Supported package indicators include:

- `import_registry` or `tags`
- `import_aliases` or `aliases`
- `import_assignments` or `series`

Registry and alias imports support `add`, `merge`, and `replace` modes.
Assignment imports use assignment-session payloads and validate applicability against current assignments and catalogue context.

## Verification

Run these focused checks after tags adapter changes:

```bash
$HOME/miniconda3/bin/python3 -m py_compile data-sharing/adapters/tags/*.py data-sharing/adapters/tags/families/*.py
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_tags_data_sharing_adapter.py -q
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_data_sharing_adapters.py analytics-app/tests/python/test_data_sharing_service.py analytics-app/tests/python/test_analytics_data_sharing_api.py -q
```

Run the local route smoke when handler wiring or browser-visible behavior changes:

```bash
$HOME/miniconda3/bin/python3 analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py
```
