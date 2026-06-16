---
doc_id: site-request-catalogue-canonical-work-detail-structure-review
title: Catalogue Canonical Work Detail Structure Review Request
added_date: 2026-06-16
last_updated: 2026-06-16
ui_status: draft
parent_id: change-requests
viewable: true
---
# Catalogue Canonical Work Detail Structure Review Request

Status:

- proposed

## Summary

Review whether canonical work-detail source data should remain a normalized keyed record model or move to a nested work-owned model.

This request is intentionally separate from [Work Detail Section Data Model Request](/docs/?scope=studio&doc=site-request-work-detail-section-data-model). The section model request fixes the immediate ambiguity around section metadata, `section_order`, `detail_sort`, and detail-owned fields. This request asks the larger design question: what should the canonical source shape be once the historical spreadsheet and standalone-detail workflows no longer drive the model?

The likely blast radius is broad, but it may be controllable if catalogue code consistently goes through helper functions for source reads, source writes, lookup projection, and publication generation.

## Context

The current canonical work-detail model is flat:

```json
{
  "work_details": {
    "00782-001": {
      "detail_uid": "00782-001",
      "work_id": "00782",
      "detail_id": "001",
      "section_id": "00782-1",
      "title": "birth of forms - detail 1",
      "project_filename": "birth of forms - detail 1.jpg"
    }
  }
}
```

This is efficient for row-based imports and direct record lookup, but it can obscure the real ownership model:

- work details belong to a work
- sections belong to a work
- details belong to a section
- the future editing surface is expected to be work-scoped modals, not a standalone work-detail page

Generated lookup and public payloads are build-time products. They do not need the canonical source to optimize for browser lookup shape or historical spreadsheet row shape.

## Review Question

Should canonical detail source data be nested under its owning work?

Example nested source shape:

```json
{
  "works": {
    "00782": {
      "work_id": "00782",
      "detail_sections": [
        {
          "section_id": "00782-1",
          "details_subfolder": "details",
          "section_title": "details",
          "section_order": null,
          "detail_sort": null,
          "details": [
            {
              "detail_uid": "00782-001",
              "detail_id": "001",
              "title": "birth of forms - detail 1",
              "project_filename": "birth of forms - detail 1.jpg"
            }
          ]
        }
      ]
    }
  }
}
```

This example is illustrative. The review should decide whether details live inside `works.json`, inside a separate work-owned source file, or in another nested structure.

## Candidate Models

### Normalized Keyed Model

Shape:

```json
{
  "work_detail_sections": {
    "00782-1": {
      "work_id": "00782"
    }
  },
  "work_details": {
    "00782-001": {
      "work_id": "00782",
      "section_id": "00782-1"
    }
  }
}
```

Strengths:

- direct lookup by `detail_uid`
- small record-level write patches
- familiar table-like import/export shape
- clear foreign-key validation
- easier stale-write hashes per detail or section

Weaknesses:

- still requires joins to understand the full work-owned structure
- source shape is less aligned with the future work-editor modal UI
- separate maps can hide aggregate invariants unless helpers enforce them carefully

### Nested Work-Owned Model

Shape:

```json
{
  "works": {
    "00782": {
      "detail_sections": [
        {
          "section_id": "00782-1",
          "details": [
            {
              "detail_uid": "00782-001"
            }
          ]
        }
      ]
    }
  }
}
```

Strengths:

- canonical source mirrors the real ownership model
- section/detail modals can edit the work aggregate directly
- section-level and detail-level fields are structurally distinct
- generated lookup/search payloads can flatten or index at build time
- fewer repeated parent/section values in source

Weaknesses:

- direct detail lookup requires helper indexes or scanning
- moving details changes a larger nested structure
- conflicts may become work-level rather than detail-level unless helper hashes are careful
- row-based import/export requires transformation at the boundary
- generated diffs may be larger if source serialization is not deterministic and stable

## Key Questions

- What is the canonical editing boundary: work, section, or detail?
- Should a work be the aggregate root for all detail edits?
- Are standalone work-detail edits still a real workflow, or only a transitional route?
- Should canonical source prioritize semantic ownership over row-based import convenience?
- Should generated lookup/search payloads become the only flat detail-index surfaces?
- Can helper functions provide efficient `detail_uid` lookup regardless of source shape?
- How should stale-write protection work: work hash, section hash, detail hash, or helper-derived sub-hash?
- How should imports report row-level errors if the destination source is nested?
- Should prose and primary work metadata remain separate from nested detail data?
- Should detail sections be allowed to exist before they contain details?

## Helper Boundary Hypothesis

The migration should be tractable if all code that reads or writes detail source data goes through a small set of helper APIs.

Target helper responsibilities:

- load canonical catalogue source into a normalized in-memory model
- provide lookup by `work_id`, `section_id`, and `detail_uid`
- expose ordered sections and ordered details for a work
- apply section create/update/delete operations
- apply detail create/update/move/delete operations
- serialize back to the chosen canonical source shape deterministically
- compute stale-write hashes at the intended edit boundary
- provide compatibility adapters for workbook import and generated lookup export

The review should identify any code that still reaches directly into JSON maps and decide whether to move it behind helpers before changing the source shape.

## Initial Frontend Findings

Studio frontend access is not a simple split between "direct canonical JSON" and "API only". Initial inspection suggests the transport boundary is mostly centralized, but source-shape assumptions are still spread across feature modules.

Current findings:

- `studio/app/frontend/js/studio-data.js` centralizes catalogue reads through `loadStudioLookupJson`, `loadStudioLookupRecordJson`, and `loadStudioServerReadJson`.
- When the catalogue service is available, supported reads go through `/studio/api/catalogue/read?key=...`; otherwise the same helpers can fall back to static JSON paths from `studio/app/frontend/config/studio-config.json`.
- `studio/app/frontend/js/catalogue-editor-service-client.js` centralizes write calls for works, work details, series, moments, imports, publication, build preview/apply, and delete preview/apply.
- The main work, series, and work-detail editors generally read generated lookup payloads rather than reading canonical source files directly.
- `studio/app/frontend/config/studio-config.json` still exposes canonical source-shaped paths including `catalogue_works`, `catalogue_work_details`, and `catalogue_moments`.
- Some frontend routes still request canonical source-shaped payloads through the shared loader. For example, `studio/app/frontend/js/catalogue-status.js` reads `catalogue_works` and `catalogue_moments`, and `studio/app/frontend/js/catalogue-moment-editor.js` reads `catalogue_moments`.

The practical risk is therefore not a large number of raw `fetch("work_details.json")` calls. The larger risk is that feature modules understand source and lookup shapes directly after the shared loader returns JSON. A canonical structure change should first identify these shape assumptions and either move them behind helper functions or deliberately leave them as lookup-only consumers.

Moments are probably not part of this work-detail hierarchy review. They have no section/detail hierarchy, and the likely future direction is to move them toward Docs Viewer-managed documents rather than fold them into the work-detail canonical structure decision. Moment reads are still useful evidence for the broader Studio data-access pattern, but they should not expand the scope of this review unless a shared loader or write-service change affects them incidentally.

## Likely Blast Radius

High-level affected areas:

- `studio/services/catalogue/catalogue_source.py`
- `studio/services/catalogue/catalogue_source_mutation.py`
- `studio/services/catalogue/catalogue_work_detail_service.py`
- `studio/services/catalogue/catalogue_bulk_service.py`
- `studio/services/catalogue/catalogue_workbook_import.py`
- `studio/services/catalogue/catalogue_lookup.py`
- `studio/services/catalogue/generate_work_pages.py`
- `studio/services/catalogue/catalogue_generation_records.py`
- `studio/services/catalogue/catalogue_delete_plans.py`
- `studio/services/catalogue/catalogue_build_media.py`
- `studio/services/catalogue/project_state_report.py`
- Studio work editor detail browser and future modal code
- transitional work detail editor route
- source validation, field registry, focused Python tests, and browser smokes
- stable source-model, lookup, write-service, and build documentation

This list is large, but much of the change should be mechanical if direct JSON access is first consolidated behind helper functions.

## Evaluation Plan

1. Inventory direct accesses to `records.work_details`, `work_details.json`, `section_id`, `details_subfolder`, `section_title`, `section_order`, `detail_sort`, and `detail_uid`.
2. Classify each access as read-only projection, validation, mutation, import/export, media path resolution, delete planning, or UI lookup.
3. Identify the smallest helper API that can satisfy all callers independent of source shape.
4. Prototype helper-backed read projection without changing canonical JSON.
5. Compare normalized keyed source versus nested work-owned source against real operations:
   - open a work editor
   - create a section
   - edit a section
   - create a detail
   - edit a detail
   - move a detail between sections
   - delete a detail
   - delete or merge a section
   - import a workbook
   - regenerate lookup payloads
   - regenerate public work JSON and search
6. Decide whether the semantic clarity of nesting is worth the write/conflict/import changes.

## Non-Goals

- Do not change the current section data-model task scope.
- Do not redesign public route UI as part of this review.
- Do not remove generated lookup/search payloads; they remain build-time projections.
- Do not preserve historical spreadsheet shape as a hard requirement unless it is still needed for active workflows.

## Decision Outputs

The review should produce:

- chosen canonical shape
- source file ownership decision
- helper API boundary
- stale-write hash boundary
- migration sequence
- compatibility policy for old source fields
- affected docs/tests list
- explicit recommendation about retiring or narrowing `/studio/catalogue-work-detail/`

## Open Questions

- If nested source wins, should detail data live inside `works.json`, `work_details.json`, or one file per work?
- Should canonical work source and generated public work payload intentionally look similar, or is that too easy to confuse?
- Should detail `detail_uid` remain stored, or be derived from `work_id` and `detail_id` inside a nested work?
- Should section ids remain generated strings like `00782-1`, or should nested section order allow simpler per-work section keys?
- Should workbook import remain row-first and adapt through helpers, or should it stage a nested preview before apply?
