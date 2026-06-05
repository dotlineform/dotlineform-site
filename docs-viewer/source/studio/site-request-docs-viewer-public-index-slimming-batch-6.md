---
doc_id: site-request-docs-viewer-public-index-slimming-batch-6
title: Docs Viewer Public Index Slimming Batch 6
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: planned
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 6: Verification

This is the delivery specification for [Batch 6 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 6: Verification

Summary: Add or update contract/projection coverage, then run focused public and manage smoke checks against the new payload-loading path.
Keep these checks scoped to payload contract and route/runtime behavior; do not use the Docs Viewer public-index slimming smoke pass to cover broken-links reports or manage dark-theme styling.

| ID | status | action |
| --- | --- | --- |
| 6.1 | planned | Add or update tests, generated-output contract fixtures, and projection checks that assert public `index-tree.json`, public recently-added payloads, public by-id reader metadata, and public route loads omit non-public or selected-document-only metadata, and that public routes do not request public `index.json`. |
| 6.2 | planned | Update the current Docs Viewer smoke checks for the new loading contract, then run public Docs Viewer read-only smoke against a fresh temporary Jekyll build and focused manage-mode checks for shared runtime compatibility. Required smoke updates include replacing old `index.json` route-config/request expectations with route-appropriate public and manage `index-tree.json` expectations, asserting recently-added payload requests, search payload requests, selected by-id hydration for info panels, and absence of public `index.json` requests; broken-links report behavior and manage dark-theme styling are out of scope for this request's smoke pass. |

## Steer for these tasks

- Verification should prove the new route contract, not incidental report or theme behavior.
- Update existing smoke expectations that currently reference old `index.json` route config or generated-read paths.
- Public checks need both positive assertions for new payloads and negative assertions for public `index.json`.
- Manage checks should prove shared runtime compatibility without forcing public payloads to carry manage metadata.

## Deliverables

- Generated-output contract fixture/projection coverage for public tree, recently-added, and public by-id reader metadata.
- Updated public read-only smoke for `/library/` and `/analysis/`.
- Updated focused manage-mode smoke for the new loading contract.
- Request/asset assertions for public and manage `index-tree.json`, recently-added, search payloads, and by-id hydration.
- Negative assertions proving public routes do not request public `index.json`.

## Implementation and policy guidance

- Broken-links report behavior and manage dark-theme styling are out of scope for this request's smoke pass.
- Keep smoke checks focused and route-specific.
- Prefer updating existing focused smokes over adding broad end-to-end coverage unless the new behavior has no suitable existing home.

## Proposed verification set

- `$HOME/miniconda3/bin/python3 -m py_compile` for changed smoke scripts and test helpers.
- Focused pytest for generated-output contract/projection checks.
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke` when the smoke profile is updated and the touched area warrants the full profile.
- Fresh temporary Jekyll build plus public `/library/` and `/analysis/` read-only checks.
- Focused manage-mode checks for `index-tree.json`, recently-added, search, by-id hydration, and no public `index.json` requests.

## completed verification

- Not started.

## follow-on tasks

- Batch 5 handoff: final verification must assert that public route configs for `/library/` and `/analysis/` do not expose `docs_paths.index_url`.
- Batch 5 handoff: final verification must assert that public browser scope config records for `library` and `analysis` do not expose docs `index_url`; search policy `index_url` values under `assets/data/search/<scope>/index.json` remain valid and should not be treated as failures.
- Batch 5 handoff: final verification must assert that public `/library/` and `/analysis/` route requests include `index-tree.json`, `recently-added.json`, selected by-id payloads, and search payloads when those UI paths are exercised, and never request `assets/data/docs/scopes/<scope>/index.json`.
- Batch 5 handoff: final verification must assert that `assets/data/docs/scopes/library/index.json` and `assets/data/docs/scopes/analysis/index.json` are absent from the repo and not recreated by public docs builds.
- Batch 5 handoff: final verification must assert public by-id payload fixtures remain reader-only and do not require `doc_id`, `source_path`, `viewer_url`, `ui_status`, `viewable`, `parent_id`, `added_date`, `content_text_length`, or report metadata.
- Batch 5 handoff: manage/local rich flat indexes under `docs-viewer/generated/docs/<scope>/index.json` remain in scope for manage/report/tooling consumers; do not fail Batch 6 scans on those manage/local paths.
- Batch 5 handoff: Data Sharing export/import, docs import review, broken-link tooling, source-config reports, and report/internal rich-index reads are separate tooling consumers. Do not preserve public flat indexes for them; classify remaining needs under their owning internal-index/tooling requests.

## task close

- Add a handoff note to Batch 7 with commands run, pass/fail results, generated payload status, and remaining risks.
- Set this document and the tracker row status to `done` when the batch is complete.
