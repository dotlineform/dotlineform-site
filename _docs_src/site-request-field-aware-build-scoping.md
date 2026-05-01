---
doc_id: site-request-field-aware-build-scoping
title: Field-Aware Catalogue Build Scoping Request
added_date: 2026-04-27
last_updated: 2026-05-01
parent_id: change-requests
sort_order: 100
---
# Field-Aware Catalogue Build Scoping Request

Status:

- in progress

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
- do not analyze source image replacement, srcset generation, staged image media, or thumbnail copy as part of JSON artifact dependency scoping
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

### Stage 0. Pre-Analysis Cleanup

Before the full dependency inventory becomes executable, take obvious broad work out of the path when the dependency is already clear.

Good candidates:

- media behavior: local media generation only depends on source media identity/path fields and explicit force/media refresh requests
- page-shell checksums: minimal Jekyll route pages should not be rewritten just because unrelated runtime JSON metadata changed
- generated hash/version inputs: checksums should describe the artifact's actual serialized payload, not a broader source record

Related pre-analysis spec:

- [Route-Anchor Collection Stubs Spec](/docs/?scope=studio&doc=site-request-route-anchor-collection-stubs)
- [Studio Record Hash Simplification Analysis](/docs/?scope=studio&doc=site-request-studio-record-hash-simplification)

This stage should stay narrow. It can hard-code small, well-understood exclusions, but it should not become a partial hidden dependency registry.

### Stage 1. Define The Dependency Registry

Create a single source of truth for field-to-artifact dependencies.

This can live in code or config, but it should be explicit enough for:

- write-server save handling
- build preview command generation
- dry-run explanations
- tests or fixture checks

Before building the executable registry, run a retired-field cleanup pass so obsolete source fields do not become permanent registry entries.

Broader catalogue compatibility cleanup should stay separate from this request. Task 1A may remove obvious retired fields, but it should not refactor workbook-shaped generator bridges or lookup compatibility surfaces unless that is required to remove a confirmed-retired field.

Related follow-up:

- [Catalogue Compatibility Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)

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

### Stage 5. Add A Registry Review Surface

After the analysis is complete and the executable registry exists, add a Studio page that displays the field registry for future review.

The page can render the registry as a tree list, grouped table, or generated Markdown-style document. The important requirement is that the registry becomes the single source of truth and the Studio page becomes the review surface. At that point, the current inventory document tables should be treated as a frozen evidence snapshot rather than living dependency tables.

## Task List

### Task 0. Pre-Analysis Cleanup

Status:

- planned

Apply immediate low-risk cleanup before the full dependency registry work:

- review page-shell checksum inputs for `_works/`, `_series/`, and `_moments/`
- narrow page-shell checksums to the fields actually serialized into each page shell, or document why broader checksums must remain
- define whether generated collection Markdown files should become route anchors only, with runtime metadata moved entirely to JSON artifacts
- decide whether Studio record hashes should be removed from broad lookup rows and normal local save enforcement
- review generated payload version inputs for cases where broad source hashes cause no-op rewrites or misleading rebuild plans

Acceptance checks:

- page-shell files do not rewrite when only fields outside their serialized front matter changed
- route-anchor collection stubs do not rewrite on metadata-only saves once the route-stub cleanup is implemented
- broad Studio lookup rows do not rewrite solely because full-record hash baselines changed

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

Inventory doc:

- [Field-Aware Build Scoping Inventory](/docs/?scope=studio&doc=site-request-field-aware-build-scoping-inventory)

Open questions:

- none blocking for Task 1

Resolved Task 1 note:

- retained compatibility paths should not be treated as active field dependencies for Task 2
- no non-image metadata should change generated JSON artifacts through retained compatibility paths unless that dependency is explicitly documented as active
- compatibility fields discovered during inventory should be classified as active, editor-only, derived, migration-only, or retired before registry rules are created
- broader compatibility cleanup is tracked separately in [Catalogue Compatibility Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup)

### Task 1A. Retired Field Cleanup

Status:

- completed

Check canonical source records, schemas, editor fields, lookup payloads, generated artifacts, and docs for retired catalogue fields.

Removed source fields:

- `works.<work_id>.work_prose_file`
- `works.<work_id>.series_title`
- `series.<series_id>.series_prose_file`

Also scan for obvious adjacent workbook-era or retained compatibility fields. If a field is clearly obsolete and its removal is narrow, remove it in this task. If the field still has unclear generator, lookup, import/export, or editor implications, document it as follow-up in [Catalogue Compatibility Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup) rather than turning Task 1A into a compatibility-layer refactor.

Remove confirmed-retired fields before creating executable field-to-artifact rules, so the new registry does not preserve obsolete compatibility surface.

Out of scope for Task 1A:

- redesigning the internal workbook-shaped projection used by generator helpers
- removing deprecated workbook-led scripts or their clean-exit behavior
- changing public runtime payload contracts except to remove confirmed-retired fields
- pruning Studio lookup payloads beyond fields that are confirmed retired

Acceptance checks:

- retired fields are absent from canonical source records
- retired fields are absent from Studio editor forms and lookup payloads
- retired fields are absent from source schema/normalization helpers unless a migration-only compatibility path is explicitly documented
- generated public artifacts do not expose retired fields
- docs identify ID-derived prose paths as the supported model
- any suspicious compatibility fields that remain are listed in the separate compatibility cleanup request

### Task 2. Define Field-To-Artifact Rules

Status:

- completed

Create a dependency registry that maps changed fields to artifact families.

Registry source:

- `assets/studio/data/catalogue_field_registry.json`

Registry design:

- use JSON so the future Studio review page can fetch and display the same source of truth
- group rules by record family, operation, and field set where fields share the same behavior
- keep `current` behavior separate from `target` behavior so planned optimizations are not mistaken for live behavior
- record `reason`, `fallback`, and `conditional_artifacts` where dependencies are not unconditional
- list retired fields explicitly so review surfaces can show that they are intentionally absent from active rules

Task 2 sequence:

1. Confirm the registry shape, location, artifact family names, fallback model, and current/target separation.
2. Populate the registry with current field-to-artifact rules as currently selected by the broad planner, lookup invalidation, and media workflow.
3. Review current rules for optimization opportunities, redundant artifact selection, and dependencies that must stay conservative.
4. Populate target rules that later tasks can wire into the write server, build preview, dry-run explanations, and tests.

The registry includes:

- work fields
- work detail fields where they affect parent work outputs
- series fields
- moment fields if the same planner model is extended there
- fallback rules for unknown fields and structural operations

The registry is now the single source of truth for Task 3 implementation planning. The Task 1 inventory remains useful as the evidence basis, but should stop being maintained as the live dependency table.

### Task 3. Wire Rules Into Write-Server Planning

Status:

- completed

Update the local write server so saved changed-field sets can produce narrower build scopes.

The write server should keep full-scope fallback for:

- bulk save
- create/delete operations until explicitly scoped
- unknown field changes
- mixed changes that span multiple dependency classes

Implemented behavior:

- single work, work-detail, series, and moment save endpoints now resolve changed fields through `assets/studio/data/catalogue_field_registry.json`
- fields that share one registry rule use the rule's target artifacts for save-time `apply_build`
- unknown fields, mixed rule classes, and series saves that also change member work records keep conservative fallback
- editor-only work fields such as `notes` and `provenance` can skip public build work entirely
- build scopes can now independently skip catalogue search and local media generation when the selected registry rule does not require them

Current limits:

- bulk save, create, delete, publication, import, and direct build-preview/apply paths keep the existing broad behavior
- some generator artifact flags are still coarser than the registry vocabulary; later tasks should tighten preview output and generator granularity where needed

### Task 4. Wire Rules Into Build Preview

Status:

- completed

Update `scripts/catalogue_json_build.py` preview generation so field-aware scopes can be previewed consistently outside the write server.

Implemented behavior:

- `scripts/catalogue_json_build.py` accepts `--changed-fields` and optional `--record-family`
- field-aware CLI previews resolve the registry path from `studio_config.json`
- preview output uses the same rule planner as save-time write-server builds
- `/catalogue/build-preview` accepts optional `changed_fields` and `record_family` request fields
- preview scopes include `field_plan`, narrowed `generate_only`, `rebuild_search`, `generate_local_media`, and local-media counts that reflect the selected rule

Current limits:

- direct `/catalogue/build-apply` remains explicit/broad unless called through save-time `apply_build`
- detailed human-readable artifact reasons are still part of Task 5

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
- metadata-only saves skip local media generation
- image/media source field changes still select local media generation
- series membership changes
- status/publish transitions
- unknown-field fallback

Update the relevant script and Studio docs after implementation.

### Task 7. Add Studio Field Registry Review Page

Status:

- planned

Create a Studio page that surfaces the active field-to-artifact registry for review.

The page should:

- load the registry source of truth, not scrape the frozen inventory document
- group fields by record family and artifact family
- show fallback rules for unknown, mixed, create/delete, and identity operations
- make retired or unsupported fields visibly absent rather than silently listed
- support quick scanning through a tree list, grouped table, or generated Markdown-style view
- link back to the frozen inventory evidence doc and this change request for context

Acceptance checks:

- the Studio page reflects the executable registry exactly
- current inventory tables are treated as frozen evidence, not an editable live dependency source
- adding a new active source field requires updating the registry before the page can display a complete dependency model
- manual review can confirm work, detail, series, moment, media, and catalogue-search dependency groups without reading implementation code

## Benefits

- scoped dry-runs become easier to trust
- small metadata edits create less generated-output noise
- metadata-only saves avoid unnecessary local media checks and generation work
- build planning rules become inspectable instead of implicit
- the active registry can be reviewed from Studio without treating planning docs as source of truth
- future source-model changes can reuse the same dependency model

## Risks

- under-scoping can leave stale generated artifacts
- dependency rules can drift if new fields are added without registry updates
- field-aware planning can become harder to reason about if fallback rules are not explicit
- the Studio review page can drift if it duplicates registry logic instead of rendering the registry itself

Mitigation:

- keep conservative fallback as the default for unknown cases
- make dependency reasons visible in dry-runs
- make the Studio page read the registry source of truth directly
- verify representative changes before replacing broad scopes
