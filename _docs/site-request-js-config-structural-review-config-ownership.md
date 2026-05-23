---
doc_id: site-request-js-config-structural-review-config-ownership
title: Config Ownership Cleanup Slice
added_date: 2026-05-10
last_updated: "2026-05-10 17:08"
ui_status: done
parent_id: site-request-js-config-structural-review
sort_order: 4000
viewable: true
---
# Config Ownership Cleanup Slice

Status:

- planning slice created
- implemented

## Purpose

This child doc tracks the fourth implementation slice from the [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The goal is to make browser-facing config ownership clearer before more Studio or public-site runtime code starts using `studio_config.json` by convenience.
The slice should preserve the current payload shape until narrower implementation tasks are accepted.

## Problem

`assets/studio/data/studio_config.json` is currently useful because it is the shared browser-facing manifest for Studio routes, data paths, Docs Viewer settings, search lookup paths, and UI copy.
It has also started to hold domain policy, especially Studio analysis tag scoring and RAG settings.

`assets/studio/js/studio-config.js` has the same mixed shape.
It is the correct owner for loading, defaulting, merging, path resolution, and small config accessors, but it also computes Studio tag metrics, RAG status, and analysis tooltip text.
Those scoring helpers are domain behavior, not generic config loading.

Implementation result:

- `assets/studio/js/analysis-tag-scoring.js` now owns Studio tag metric calculation, RAG rule evaluation, and compact RAG tooltip text.
- `assets/studio/js/studio-config.js` remains the config loader/accessor owner and keeps analysis group accessors used by tag-management routes.
- `assets/studio/js/tag-studio-index.js` and `assets/studio/js/series-tags.js` import scoring helpers from the new analytics module.
- `studio_config.json` path keys, route keys, UI text keys, and analysis policy payload shape stayed unchanged.
- Docs Viewer and catalogue editor copy remain in shared `ui_text`; splitting them is deferred until payload size, independent release cadence, or route ownership pressure creates a concrete benefit.

## Current Ownership

`studio_config.json` should be treated as:

- a browser route and data-path manifest
- the shared Studio UI-copy store under `ui_text`
- a small holder for cross-route viewer settings that are genuinely shared by the browser runtime
- a temporary holder for analysis policy until the policy has a clearer analytics owner

`studio-config.js` should own:

- fetching `studio_config.json`
- merging file values with built-in defaults
- resolving site-relative route and asset paths
- exposing stable accessors such as `getStudioRoute`, `getStudioDataPath`, `getSearchScopeDataPath`, and `getStudioText`

It should not be the long-term owner for:

- analysis tag completeness scoring
- analysis RAG classification
- user-facing analysis tooltip composition
- route-specific workflow policy
- local write-service endpoint definitions
- generated payload schema rules

## Target Boundary Questions

This slice should answer:

1. Which analysis policy values stay in `studio_config.json`, and which should move to a scoped analysis config payload?
2. Should analysis tag scoring live in a new analytics helper module such as `assets/studio/js/analysis-tag-scoring.js`?
3. Which current `studio-config.js` exports need compatibility wrappers during extraction?
4. Which UI-copy groups are stable in shared `ui_text`, and which should move to route-scoped config files only if the payload size or ownership pressure justifies it?
5. Do Docs Viewer and catalogue editor copy remain in `studio_config.json` for now, or should either area define a future scoped copy file?
6. What checks prove that tag analytics, series tag RAG indicators, public search, Docs Viewer, and catalogue editor routes still boot after the boundary change?

## Decisions

The implementation used the conservative path:

- keep `studio_config.json` as the root browser manifest and UI-copy store
- keep existing `analysis` policy values in `studio_config.json` for the first extraction so payload paths do not change
- move analysis metric/RAG/tooltip helpers out of `studio-config.js` into an analytics-owned module
- update the two direct scoring consumers to import the new module directly, without keeping scoring re-exports in `studio-config.js`
- do not split Docs Viewer or catalogue editor copy yet; document the criteria for doing so later

This avoids turning a cleanup slice into a config-file migration.
The source change clarified runtime ownership without changing loaded JSON paths or visible UI behavior.

## Candidate Module Boundary

New module:

- `assets/studio/js/analysis-tag-scoring.js`

Target ownership:

- group and coverage-group normalization for analysis scoring
- deprecated-status normalization
- tag completeness metric calculation
- RAG rule evaluation
- compact tooltip text for RAG badges

`studio-config.js` should still provide:

- raw config loading and default merging
- path and text accessors
- optional policy accessor helpers if callers need a stable way to read `config.analysis`

Avoid:

- a generic `config-policy.js` bucket
- moving all analysis config into a separate file before there is a clear consumer benefit
- changing `studio_config.json` path keys, route keys, or `ui_text` key names in this slice

## Implementation Tasks

1. Inventory current analysis helper consumers.
   - Confirm use in `assets/studio/js/tag-studio-index.js`.
   - Confirm use in `assets/studio/js/series-tags.js`.
   - Check whether any other route imports `computeStudioTagMetrics`, `computeStudioRag`, or `buildStudioRagTooltip`.

2. Define the first extraction.
   - Add an analytics-owned scoring module.
   - Move pure scoring helpers there.
   - Keep helper inputs as plain assigned-tag arrays, registry maps, and loaded config objects.
   - Preserve result shape, RAG labels, and tooltip text.

3. Keep config loader compatibility stable.
   - Either update direct consumers to import the new module, or leave temporary re-exports in `studio-config.js`.
   - Do not remove defaults needed by the scoring module in the same pass unless all callers are updated.

4. Document config ownership.
   - Update [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) to describe `studio_config.json` as root manifest plus shared UI-copy store.
   - Update [Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js) so analysis scoring is no longer listed as loader-owned behavior after extraction.
   - Add a note if analysis policy remains in `studio_config.json` only as an intentional transitional boundary.

5. Decide copy-splitting criteria.
   - Keep Docs Viewer and catalogue editor copy in `ui_text` unless payload size, independent release cadence, or route ownership pressure becomes a concrete problem.
   - If a future split is needed, prefer scoped payloads loaded by the owning route rather than more nested keys in `studio_config.json`.

## Acceptance Checks

- `studio-config.js` remains the config loader/accessor owner, not the analysis scoring owner.
- Existing callers still receive the same metric fields, RAG values, and tooltip text.
- `studio_config.json` route, data-path, and `ui_text` key names are unchanged.
- Tag Studio index and series tag RAG indicators still render.
- Public search, Docs Viewer, and catalogue editor route boot are not affected by the extraction.
- Related config docs describe the new boundary.

## Targeted Verification

Focused checks for this slice:

- `node --check` for changed JavaScript files and direct consumers
- targeted search for retired imports or duplicated scoring helpers
- a representative static or local-browser smoke check for:
  - Studio tag index RAG rendering
  - series tags RAG rendering
  - one route that only needs `studio-config.js` path/text access
- Studio docs payload rebuild and Studio search rebuild after docs updates

Jekyll build is useful if route script tags or generated docs payloads change, but this slice should not require a broad run-checks profile unless the implementation grows beyond analysis scoring extraction.

Results:

- `node --check` passed for `assets/studio/js/analysis-tag-scoring.js`, `assets/studio/js/studio-config.js`, `assets/studio/js/tag-studio-index.js`, and `assets/studio/js/series-tags.js`.
- Targeted search confirmed `computeStudioTagMetrics`, `computeStudioRag`, and `buildStudioRagTooltip` are defined only in `analysis-tag-scoring.js` and imported by the two scoring consumers.
- Studio docs payloads and Studio search index were rebuilt.
- Jekyll build passed to `/tmp/dlf-jekyll-build` because a local Jekyll server was already running.
- Static Playwright smoke against the temp build passed for the series tags page, catalogue work editor page, and direct `tag-studio-index.js` module import; `analysis-tag-scoring.js` loaded with HTTP 200, the series tags page rendered 138 RAG indicators, and no page errors or failed local requests were reported.

## Benefits And Risks

Benefits:

- keeps generic config loading small and easier to reason about
- gives analysis scoring an obvious owner before more analytics UI is added
- makes `studio_config.json` expansion decisions explicit instead of accidental

Risks:

- compatibility wrappers can hide the new boundary if left in place too long
- moving config payloads too early would add fetch sequencing and fallback complexity without clear runtime benefit
- analysis RAG behavior is visible in Studio tables, so metric and tooltip output should be pinned by focused checks before refactoring further
