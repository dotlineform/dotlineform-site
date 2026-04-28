---
doc_id: site-request-field-aware-build-scoping
title: "Field-Aware Catalogue Build Scoping Request"
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: change-requests
sort_order: 153
---
# Field-Aware Catalogue Build Scoping Request

Status:

- planned

## Summary

This change request tracks a follow-up refinement to catalogue scoped rebuild planning.

The current scoped build planner is intentionally conservative. A work-scoped rebuild pulls in the work, the work's related series, aggregate indexes, and catalogue search by default. That is safe, but it can be broader than the true dependency graph for small metadata changes.

The immediate example is work-owned files and links. Changing `Works.downloads` or `Works.links` affects the focused work payload and any lookup/search surfaces that expose those fields. It does not affect series membership, series ordering, series prose, primary work selection, or most series JSON/page output.

The desired end state is field-aware build scoping:

- the write/build planner maps changed source fields to the smallest correct artifact set
- series artifacts are rebuilt only when a changed field can affect series output
- ambiguous changes keep the current conservative fallback
- dry-runs explain which artifacts were selected and why

## Current Behavior

Current work-scoped build planning:

- `scripts/catalogue_json_build.py` builds a scope for a work id
- the scope includes the work's current `series_ids`
- the default artifact set includes:
  - `work-pages`
  - `work-json`
  - `series-pages`
  - `series-index-json`
  - `works-index-json`
  - `recent-index-json`
- the generated command passes both `--work-ids` and `--series-ids` to `scripts/generate_work_pages.py`

This means a narrow work metadata change can still consider related series outputs.

The implementation is safe because unchanged generated payloads are usually skipped by checksum/version comparison, but the selected scope is still broader than the dependency requires.

## Problem

Coarse scoped builds create avoidable noise:

- dry-runs describe broader work than the user intended
- generated-output diffs can include unrelated artifacts when aggregate or timestamp behavior changes
- the planner does not communicate why a field change needs a given artifact family
- safe broad fallback and true dependency requirements are not clearly separated

The result is conceptually confusing. A change to a work download can appear to require series refresh even though series output does not depend on downloads.

## Goals

- define an explicit field-to-artifact dependency table for catalogue source edits
- narrow rebuild scopes for obvious local metadata changes
- keep conservative fallback for unknown, mixed, or structural changes
- make planner output explain selected artifacts and dependency reasons
- align write-server invalidation, build preview, and generated commands around the same rules
- reduce no-op or near-no-op generated-output churn

## Non-Goals

- do not remove conservative fallback behavior
- do not redesign the generator in this request
- do not change public runtime payload contracts
- do not require perfect incremental generation for every artifact family in the first pass
- do not optimize for large-scale performance ahead of correctness and clarity

## Dependency Model

The planner should classify changed fields by the artifact families they can affect.

### Work-Local Metadata

These fields should usually avoid series artifacts:

- `downloads`
- `links`
- `notes`
- `provenance`
- `storage_location`
- `duration`
- `medium_caption`
- `width_cm`
- `height_cm`
- `depth_cm`

Expected artifacts:

- focused work lookup payload
- focused public work JSON if public output includes the field
- focused work page if the generated page checksum includes the field
- search only when the field is indexed
- aggregate work indexes only when they include the field

### Work Fields With Series Dependencies

These fields may require related series artifacts:

- `series_ids`
- `status`
- `published_date`, where publish transitions affect series membership visibility
- fields used for series ordering
- fields used by series member summaries
- primary image fields if series payloads or cards expose them
- `title`
- `year`
- `year_display`

Expected artifacts:

- focused work artifacts
- old and new related series artifacts when membership or ordering can change
- affected aggregate indexes
- affected search indexes

### Series-Owned Metadata

Series record edits should continue to target series artifacts directly.

Examples:

- `title`
- `status`
- `published_date`
- `series_type`
- `year`
- `year_display`
- `primary_work_id`
- `sort_fields`
- prose source fields

Expected artifacts:

- focused series lookup payload
- focused public series JSON/page
- aggregate series index
- search when indexed fields change

## Delivery Strategy

Do this in small steps.

### Stage 1. Define The Dependency Registry

Create a single source of truth for field-to-artifact dependencies.

This can live in code or config, but it should be explicit enough for:

- write-server save handling
- build preview command generation
- dry-run explanations
- tests or fixture checks

### Stage 2. Use The Registry In Build Planning

Update work-scoped build planning so callers can pass changed-field context.

For example:

- files/links-only change selects work-local artifacts
- `series_ids` change selects old and new related series artifacts
- unknown change keeps the current default artifact set

### Stage 3. Improve Dry-Run Output

Dry-run and preview output should show:

- selected artifacts
- selected work ids
- selected series ids
- dependency reasons, such as `downloads -> work-json` or `series_ids -> series-pages`
- whether the planner used conservative fallback

### Stage 4. Verify With Targeted Cases

Add targeted verification around representative changes:

- `downloads` or `links` change does not select series pages/indexes
- work title/year/status changes select the required search/index surfaces
- `series_ids` change selects old and new series
- unknown or mixed changes keep the safe fallback

## Task List

### Task 1. Inventory Artifact Dependencies

Status:

- planned

Map which source fields appear in:

- work page front matter
- public work JSON
- public works index
- recent index
- series page front matter
- public series JSON
- public series index
- Studio lookup payloads
- catalogue search payloads

### Task 2. Define Field-To-Artifact Rules

Status:

- planned

Create a dependency registry that maps changed fields to artifact families.

The registry should include:

- work fields
- work detail fields where they affect parent work outputs
- series fields
- moment fields if the same planner model is extended there
- fallback rules for unknown fields and structural operations

### Task 3. Wire Rules Into Write-Server Planning

Status:

- planned

Update the local write server so saved changed-field sets can produce narrower build scopes.

The write server should keep full-scope fallback for:

- bulk save
- create/delete operations until explicitly scoped
- unknown field changes
- mixed changes that span multiple dependency classes

### Task 4. Wire Rules Into Build Preview

Status:

- planned

Update `scripts/catalogue_json_build.py` preview generation so field-aware scopes can be previewed consistently outside the write server.

### Task 5. Add Dry-Run Explanations

Status:

- planned

Show why each artifact family was selected.

The explanation should be concise and operational, not a full dependency dump.

### Task 6. Verify And Document

Status:

- planned

Add targeted checks for:

- work-local files/links metadata
- series membership changes
- status/publish transitions
- unknown-field fallback

Update the relevant script and Studio docs after implementation.

## Benefits

- scoped dry-runs become easier to trust
- small metadata edits create less generated-output noise
- build planning rules become inspectable instead of implicit
- future source-model changes can reuse the same dependency model

## Risks

- under-scoping can leave stale generated artifacts
- dependency rules can drift if new fields are added without registry updates
- field-aware planning can become harder to reason about if fallback rules are not explicit

Mitigation:

- keep conservative fallback as the default for unknown cases
- make dependency reasons visible in dry-runs
- verify representative changes before replacing broad scopes
