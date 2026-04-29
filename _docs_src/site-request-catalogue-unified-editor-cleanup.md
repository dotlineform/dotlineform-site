---
doc_id: site-request-catalogue-unified-editor-cleanup
title: Catalogue Unified Editor Cleanup Request
added_date: 2026-04-29
last_updated: 2026-04-29
parent_id: change-requests
sort_order: 140
---
# Catalogue Unified Editor Cleanup Request

Status:

- in progress

## Summary

This change request collects the cleanup work that should happen after the work, work-detail, and series editor unification work is stable.

The unified editor requests intentionally prioritized safe route migration and behavior fixes over deleting every old artifact immediately. That left a known cleanup backlog:

- retired new-record pages and controllers still exist as compatibility or leftover implementation artifacts
- docs and config references should be audited after all three editor families settle
- shared editor helpers may need final naming and ownership cleanup
- generated catalogue JSON still carries some fields that are duplicated or no longer consumed by the current public site

This request keeps those jobs together so they can be handled deliberately after the current series editor work finishes.

## Goal

Reduce catalogue editor and generated-artifact ambiguity after the unified workflows are in place.

The target outcome is:

- one active Studio editor implementation per catalogue family
- explicit compatibility policy for old `/studio/catalogue-new-*` URLs
- no active Studio config or docs path that points to retired create implementations
- generated public JSON contracts that match actual runtime usage
- audit, build, delete, and docs behavior aligned with the simplified contracts

## Cleanup Areas

### Legacy Create Routes

Inventory and retire legacy create-route artifacts from the older split editor model:

- `studio/catalogue-new-work/index.md`
- `studio/catalogue-new-work-detail/index.md`
- `studio/catalogue-new-series/index.md`
- `assets/studio/js/catalogue-new-work-editor.js`
- `assets/studio/js/catalogue-new-work-detail-editor.js`
- `assets/studio/js/catalogue-new-series-editor.js`
- `_docs_src/catalogue-new-work-editor.md`
- `_docs_src/catalogue-new-work-detail-editor.md`
- `_docs_src/catalogue-new-series-editor.md`
- any remaining `catalogue_new_*` route, UI text, or dashboard references in Studio config

Before deleting route pages, decide whether old URLs should:

- remain as tiny compatibility redirects, with no dedicated controller
- be removed entirely once no internal docs or dashboard links target them

The important boundary is that old routes must not remain second functional implementations.

### Shared Editor Code

Review the shared helper files introduced during the unified editor work.

Cleanup should check:

- whether field metadata helpers have clear ownership names
- whether work, detail, and series create/save payload shaping follows the same pattern where the workflows are actually equivalent
- whether new-mode and edit-mode validation share the right logic without forcing unlike records into one abstraction
- whether stale compatibility functions remain in active controllers after route migration

This should stay pragmatic. The goal is clearer ownership and less duplicate behavior, not a broad UI rewrite.

### Generated Series JSON Contract

Review `assets/series/index/<series_id>.json`.

Current facts:

- the public series page needs this file for page-local series metadata and `content_html`
- the visible series work grid currently uses `assets/data/series_index.json` and `assets/data/works_index.json`
- the `series.works` array inside the per-series payload is not currently consumed by the public frontend
- the per-series `primary_work_id` value is also redundant there because public thumbnail and membership context come from the aggregate index

Cleanup decision:

- formally deprecate and remove `series.works` and `series.primary_work_id` from per-series JSON, leaving membership canonical in `assets/data/series_index.json`

Update the full contract:

- `scripts/generate_work_pages.py`
- `scripts/catalogue_json_build.py`
- `scripts/studio/catalogue_write_server.py`
- `scripts/audit_site_consistency.py`
- delete/update helpers that touch affected per-series payloads
- data-model docs for generated catalogue artifacts
- search/docs references that describe membership ownership

### Publication Workflow Boundary

Do not solve the publish/unpublish interaction inside this cleanup request.

That product workflow is tracked separately in [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow). This cleanup request should only remove redundant code/docs after that workflow has a stable contract.

## Proposed Tasks

### Task 1. Inventory Remaining Legacy References

Status:

- implemented

Search the repo for:

- `/studio/catalogue-new-work/`
- `/studio/catalogue-new-work-detail/`
- `/studio/catalogue-new-series/`
- `catalogue_new_work_editor`
- `catalogue_new_work_detail_editor`
- `catalogue_new_series_editor`
- `catalogue-new-work-editor`
- `catalogue-new-work-detail-editor`
- `catalogue-new-series-editor`

Classify each reference as:

- active compatibility behavior
- docs/history only
- stale implementation code
- stale config or UI copy

Inventory outcome:

- active compatibility behavior:
  - `studio/catalogue-new-work/index.md`
  - `studio/catalogue-new-work-detail/index.md`
  - `studio/catalogue-new-series/index.md`
- compatibility docs:
  - `_docs_src/catalogue-new-work-editor.md`
  - `_docs_src/catalogue-new-work-detail-editor.md`
  - `_docs_src/catalogue-new-series-editor.md`
- stale implementation code:
  - `assets/studio/js/catalogue-new-work-editor.js`
  - `assets/studio/js/catalogue-new-work-detail-editor.js`
  - `assets/studio/js/catalogue-new-series-editor.js`
- docs/history only:
  - prior unified-editor request docs, Studio UI rule entries, and Site Change Log entries that describe the migration history
- stale config or UI copy:
  - no active `catalogue_new_work_editor`, `catalogue_new_work_detail_editor`, or `catalogue_new_series_editor` route/UI text blocks remain in `studio_config.json`

### Task 2. Decide Old URL Compatibility

Status:

- implemented

Choose one policy for the old create URLs.

Option A keeps tiny redirect pages so old bookmarks continue to land on the unified editors. Option B removes the old pages once all internal references are gone. The repo should not keep full legacy controllers either way.

Decision:

- use Option B
- remove the old `/studio/catalogue-new-*` route pages once active navigation points at the unified editors
- do not keep standalone legacy create controllers, active config/UI text, or page-level compatibility docs for those routes

### Task 3. Remove Retired Implementations

Status:

- implemented

Delete or retire the old implementation code after Task 2.

Expected checks:

- Studio dashboard uses only unified editor links
- Studio config has no active route or UI text block for retired create editors
- compatibility docs either explain redirects or are removed from the active docs tree
- no active controller imports a retired create-editor module

Implementation:

- removed `assets/studio/js/catalogue-new-work-editor.js`
- removed `assets/studio/js/catalogue-new-work-detail-editor.js`
- removed `assets/studio/js/catalogue-new-series-editor.js`
- removed redirect pages for `/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, and `/studio/catalogue-new-series/`
- removed compatibility docs for the old route pages

### Task 4. Normalize Generated Series Payload Contract

Status:

- implemented

Remove redundant per-series runtime membership fields.

Remove `series.works` and `series.primary_work_id` deliberately from generation, write-server update helpers, audit expectations, and docs. Confirm the public series page still renders grids from `series_index.json` and `works_index.json`.

Initial finding:

- the public series page renders its work grid from `assets/data/series_index.json` and `assets/data/works_index.json`
- the per-series `assets/series/index/<series_id>.json` payload is still fetched for page-local metadata and `content_html`
- previous generator logic kept `series.works` and `primary_work_id` in per-series JSON even though those fields were not consumed there
- current aggregate `assets/data/series_index.json` generation also filters membership to published works
- generated data currently has one stale per-series payload: `assets/series/index/002.json` lists draft work `00640`
- source series `002` is already `draft`, so `scripts/catalogue_json_build.py --series-id 002` correctly refuses to run a public runtime build for it

Decision:

- remove `series.works` and `series.primary_work_id` from per-series JSON generation
- treat `assets/data/series_index.json` as the canonical public grid membership source
- make write-server delete cleanup strip those obsolete fields from any older per-series payload it touches

### Task 5. Verify Catalogue Build And Runtime Paths

Status:

- proposed

Run targeted verification after cleanup:

- JS syntax checks for changed Studio controllers
- Python syntax checks for changed scripts
- `scripts/catalogue_json_build.py` preview for representative work, detail, and series ids
- deprecated catalogue commands still exit cleanly with guidance
- docs payload rebuild for Studio scope
- catalogue search rebuild if generated catalogue contracts change
- Jekyll build to a temporary destination
- browser smoke for unified work, detail, and series routes
- old URL behavior according to the selected compatibility policy
- sanitization scan for changed scripts/docs

## Benefits

- reduces duplicate Studio editor surfaces after unification
- makes old-route behavior explicit instead of accidental
- lowers maintenance cost for catalogue save/create flows
- avoids repeated confusion around generated JSON that no runtime path consumes
- keeps generated artifact contracts aligned with public-site behavior

## Risks

- removing old pages too aggressively can break bookmarks or undocumented local workflow habits
- changing generated JSON contracts can affect scripts, audit checks, or future tooling even when public pages still render correctly
- broad helper refactors can obscure the real differences between work, detail, and series workflows

## Related References

- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)
- [Catalogue Work Detail Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-detail-unified-editor)
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)
- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Catalogue Delete Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-delete-cleanup)
- [Data Models: Catalogue](/docs/?scope=studio&doc=data-models-catalogue)
