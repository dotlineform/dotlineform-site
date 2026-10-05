---
draft: false
doc_id: d-20261005-141500-4b71e9
title: Broken Links Snapshot Delivery
added_date: "2026-10-05 14:15:00"
last_updated: "2026-10-05 14:26:00"
parent_id: d-20260428-000000-f5ff18
---
# Broken Links Snapshot Delivery

Status: implemented and reviewed; awaiting user manual review and acceptance.

## Requirements

Opening Broken Links must read its last saved scan quickly. Only the existing Refresh action audits ordinary Working documents and configured collections and saves new results. Display the last scan time beside Refresh, vertically centred, without a broken-link count; retain prior results on refresh failure and leave a missing snapshot empty without a first-refresh prompt. Refresh keeps its icon and uses a progress cursor without either running message.

## Deliverables

- [x] Configuration-owned private JSON snapshot with validated read and explicit scan/save operations.
- [x] Saved-read mount, last-scanned status, retained results and quiet busy presentation.
- [x] Preserve existing audit coverage and local-only execution; keep snapshot data independent of document Build, Search and publication.
- [x] Update [Broken Links Script](../Broken_Links_Script.md) as the durable owner and reconcile report/toolbar descriptions.
- [x] Complete selected checks and bounded code review.

## Process

1. Open Broken Links to read the saved result, or an empty report when no scan has been saved.
2. Use Refresh when current results are needed. The server completes the existing audit, validates the result and replaces the configured report file before returning it.
3. Display the saved timestamp and findings, preserving sort selection. A failed refresh reports its error while retaining any loaded saved results.

## Delivery Steps

### BLS 0 Readiness

- [x] Confirm the existing mount runs a scan and that Media supplies an established saved-report pattern.
- [x] Confirm audit coverage, configuration ownership, Build inventory and public projection boundaries.
- [x] Obtain implementation approval, including removal of both running messages and the first-refresh prompt.

Record: approved on 2026-10-05. One existing local route supports GET for saved reads and empty-object POST for scan/save. The unused empty `report_context` request wrapper is removed without an alias. No audit algorithm, source/media write, test work or publication is included.

### BLS 1 Implementation And Verification

- [x] Implement the configured snapshot, schema validation, complete scan/save response and missing/invalid-data behavior.
- [x] Mount from saved data, retain results/time and sorting, and supply a progress cursor with disabled controls and `aria-busy`.
- [x] Exclude the report directory from Working Build receipts; retain the existing local-only runtime and stylesheet owners.
- [x] Finish focused static evidence.

Verification budget: existing explicit-path Python lint and syntax for the six changed service/config/Build modules, JavaScript lint for the report and client, JSON parsing for the two changed configs, a read-only configuration-load diagnostic and `git diff --check`. These address syntax, configuration shape, snapshot path resolution and whitespace at a cost of seconds with no network or workspace data writes. Bounded source/diff review checks mount-versus-refresh wiring, failure retention, exact identity, safe links and lifecycle isolation. No tests, temporary assertion scripts, browser checks, real scan or report write are included as verification work.

Gate: source implementation is complete and selected checks pass. User manual review owns the live saved-report read/Refresh behavior, persistence, error presentation and cursor feel; report those as pending rather than inferred from static checks.

Record: complete. Explicit-path Python lint and syntax passed for all six changed modules; both report/client JavaScript files passed lint. The affected Python lint/syntax passed again after safe-link validation was added. Both JSON configs parsed, the configured workspace loaded and resolved the intended private snapshot path without scanning or writing, and whitespace checks passed. All changed runtime and CSS files are local-only and absent from the canonical-to-site inventory, so this delivery needs no runtime projection or Publish.

### BLS 2 Code Review

- [x] Complete a separate bounded code/config/documentation review after selected checks.
- [x] Resolve findings and rerun only affected checks.

Gate: resolve material findings within this change; retain current source and audit coverage without compatibility layers or unapproved test changes.

Record: complete. Review added exact source-URL agreement and safe issue-URL validation to the saved-data read boundary; affected lint/syntax passed. Final review confirmed missing data stays empty, only Refresh invokes the audit, result assignment follows successful scan/save, errors retain loaded results/time, and the report cursor cannot affect a different mounted report. Ordinary document builds write only their selected outputs and Preview captures explicit document/Search/media inputs, excluding this independent report. No compatibility alias or new audit algorithm was introduced.

Timestamp-only toolbar follow-up: implemented on 2026-10-05 after the user reported successful service activation. Removed display counts, retained unscanned-source rows, centred the one-line timestamp beside Refresh through the existing flex toolbar, and moved errors below it. Focused report JavaScript lint and whitespace checks passed; bounded source review confirmed error/missing states and the local-only stylesheet boundary. Visual confirmation remains manual.

### BLS 3 Closeout

- [x] Reconcile completion claims with the actual evidence and record pending manual review.
- [x] Present activation requirements, saved-data freshness and verification limits.
- [ ] Record user manual review and acceptance.

Record: source implementation and selected static evidence are complete. No service restart, runtime scan/snapshot write, tests, browser inspection, document/Search rebuild, Publish, deployment, commit or push was performed. Restart an already running local Docs service and reload the viewer before manual review. Confirm saved reopen, explicit refresh/persistence, retained failure results, last-scanned display and the quiet busy cursor.

Retain this delivery for current implementation/manual-review state; its durable destination is Broken Links Script. No temporary verification files were created. Existing Broken Links tests still use retired scope/stage requests and remain unreviewed; test modernization is separate work.
