---
draft: false
doc_id: d-20261011-000000-413f7a
title: Index Option Retirement
added_date: "2026-10-11 00:00:00"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260428-000000-f5ff18
---
# Index Option Retirement

Status: complete. The user approved retirement on 2026-10-11.

## Outcome And Readiness

Ordinary Index navigation uses one document inventory with exact document IDs. Retire `viewer_options`, its non-loadable document and Manage-only root lists, their workspace configuration, browser subtree filtering and descendant redirects. Keep the previously requested `generated_at` header ordering, normal tree selection/expansion, configured default document, document routes and server-owned publication eligibility.

The owning boundary is workspace configuration, the ordinary document builder, Review's isolated configuration and shared Index/navigation readers. The configured lists were empty; the public preparation owner already selects eligible sources. This is one finishable slice. Changes to source identity, publication eligibility, Search, document actions or tests would widen it and are excluded. Prepared Preview and public data are replaced only by an explicit Publish.

## Decisions And Verification Budget

- Write `generated_at`, `schema` and `docs` in that order. A payload content change advances the timestamp; reordering alone preserves it.
- Keep one browser document list/map and parent map. Every Index, Search, Recent and document link uses its exact ID; no loadability resolver, hidden-tree inventory or option-reading compatibility path remains.
- Reconcile the global builder/config change with one ordinary Working build using `--skip-media-builds --skip-recent`. This writes configured generated output as needed and leaves Search unchanged.
- Use changed-owner lint, the owning build, read-only production-reader diagnostics over its real saved tree and the required public runtime projection/check/site validation. Expected cost is seconds to a few minutes. Projection writes tracked runtime assets; diagnostics perform no writes. No tests, fixtures or browser automation are created, changed or run; [Testing](../Testing.md) owns separate test approval.

## Completion Gates

- [x] Confirm the approved scope, owners and credible blast radius.
- [x] Remove the retired configuration, producer and runtime machinery; update durable owners.
- [x] Regenerate Working's ordinary tree and inspect it through production normalization and Index state.
- [x] Complete required shared/public projection checks and bounded code review.
- [x] Record final evidence limits, restart/reload requirements and retain-or-retire recommendation.

The ordinary build processed 34 documents, preserved every by-ID/Links file and Recents, wrote one Index and reported no warnings. The production reader returned 34 records/map entries and 21 roots, with only `generated_at`, `schema` and `docs` at the payload root. Changed Python and JavaScript owner lint, Python syntax, whitespace, public projection/check and site validation passed. The projection updated 10 shared modules. Bounded code review confirmed exact route targets, one Index inventory, current configuration constructors and intact management publication metadata; no active retired-option references or compatibility paths remain. Review also corrected trailing blank lines and stale endpoint examples. Remaining legacy test configuration/fixtures are unchanged and unexecuted pending separately approved test work. Manual navigation is unverified. Restart Docs Viewer services and reload the browser to adopt the changed loader and runtime. No Search rebuild, Publish, commit, push or deployment occurred.

Closeout recommendation: retain this delivery and its Planned link temporarily for the recent evidence/restart pointer; the linked durable owners contain the lasting contracts. No documentation deletion is required.

## Durable Owners

[Generated Data Contracts](../Generated_Data_Contracts.md#index-treejson-contract), [Generated Read Endpoints](../Generated_Read_Endpoints.md#tree-reads), [Docs Viewer Runtime](../Docs_Viewer_Runtime.md#retained-index-views) and [Development Checklist](../Development_Checklist.md) own the lasting contracts.
