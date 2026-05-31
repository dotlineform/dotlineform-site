---
doc_id: site-request-catalogue-save-build-diagnostics
title: Catalogue Save Build Diagnostics Request
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
parent_id: change-requests
viewable: true
---
# Catalogue Save Build Diagnostics Request

Status:

- draft

## Summary

Add focused diagnostics for the Local Studio catalogue save/build path before trying to reduce rebuild scope.

The immediate problem is visibility.
A catalogue save can touch source JSON, backups, lookup refreshes, generated public data, catalogue search, media derivatives, publication state, and Studio Activity rows.
The current risk evidence says the workflow is broad enough that optimisation work should start by measuring what each save actually did and why.

## Goals

- add save/build diagnostics that expose generated artifact groups, lookup refreshes, search updates, media work, elapsed time, and fallback reasons
- keep diagnostics compact enough to return in local service responses and activity details
- preserve dry-run/write behavior, backups, write allowlists, and compact logging
- use diagnostics to decide which rebuild reductions are worth implementing
- keep catalogue generation behavior in existing `studio/services/catalogue/` owners

## Non-Goals

- changing generated catalogue data contracts in the first slice
- parallelising media work before timing evidence identifies the slow path
- moving catalogue write behavior into frontend route modules
- broad restructuring of `catalogue_write_server.py`

## Evidence

[Studio App Risk Inventory](/docs/?scope=studio&doc=studio-app-risk-inventory) identifies the catalogue save/build path as the current Studio workflow priority.
[Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory) classifies `studio/services/catalogue/` as high maintenance, medium structure, and high performance risk across 38 files and 17,150 lines.

Relevant owners include:

- `studio/services/catalogue/catalogue_write_server.py`
- `studio/services/catalogue/catalogue_json_build.py`
- `studio/services/catalogue/catalogue_lookup_refresh.py`
- `studio/services/catalogue/catalogue_build_media.py`
- `studio/services/catalogue/catalogue_generation_*`
- `studio/services/catalogue/generate_work_pages.py`

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Map the current save/build response shape, generated artifact groups, lookup refreshes, search rebuilds, media build calls, and fallback paths. |
| 2 | planned | Add compact diagnostics to save/build planning and execution responses, including elapsed time, counts, artifact groups, and fallback reasons. |
| 3 | planned | Add Activity detail projection for written save/build operations without logging full payloads or source content. |
| 4 | planned | Add focused tests for diagnostics shape, dry-run/write parity, fallback reason reporting, and compact logging. |
| 5 | planned | Use the diagnostics to choose the first rebuild-scope reduction slice. |
| 6 | planned | Update catalogue write/build docs and the Studio risk inventory after diagnostics are available. |

## Acceptance Criteria

- catalogue save/build responses report what work ran and why
- dry-run and write responses expose comparable diagnostics
- diagnostics are safe for local logs and Activity rows
- no write allowlists or backup behavior are weakened
- the next optimisation task is based on measured repeated cost rather than static assumptions
