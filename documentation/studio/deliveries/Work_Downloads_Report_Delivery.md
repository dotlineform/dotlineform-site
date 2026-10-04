---
draft: false
doc_id: d-20261004-202223-422872
title: Work Downloads Report Delivery
added_date: "2026-10-04 20:22:23"
last_updated: "2026-10-04 20:31:49"
summary: A two-column local report reconciling canonical Work download references with saved files.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Work Downloads Report Delivery

## Current And Next State

Status: implemented and reviewed, awaiting user manual review and acceptance. The user approved implementation on 2026-10-04. [Work Downloads](/docs/?doc=d-20261004-202223-1e2205) is registered in the ordinary document tree and its watcher-generated payload is present. The actual producer found five matched download references, with no missing or unassigned files. [Reports](../Reports.md) is current. Restart the Docs Viewer service and reload its browser page to load the new endpoints and report module. No tests, browser automation, Finder launches, media writes, manual builds, Search, Publish, commit or push ran.

Complete result: Work Downloads displays canonical Work attachments alongside their exact saved files, leaving the appropriate cell blank for a missing file or an unassigned file.

## Requirements

- Read download references directly from canonical Catalogue `works.json` and direct saved files from the configured Docs workspace `assets.work_files` family. Match exact filenames without deriving ownership from a Work ID prefix.
- Display only Work and File columns. Work shows `<title> [filename]` and links to that exact Work document in the Catalogue collection. File shows the existing saved filename and reveals it in Finder.
- Use one row per canonical download reference, repeating a shared file for each referencing Work, plus one row per unassigned saved file. Missing files leave File blank; unassigned files leave Work blank.
- Sort A–Z by displayed Work text, with blank Work rows last and deterministic filename/Work-ID tie breaking. Include no search, filters, status column or paging.
- Scan on opening and explicit Run/Refresh. Keep no saved report snapshot and require no Catalogue Refresh. Use existing local report styles, navigation and OS-opening helpers.
- Keep paths server-side, confine Finder targets to exact direct filenames in the configured family, and fail visibly for unavailable input/storage. Ignore storage placeholders and do not recurse into directories.

## Deliverables

- [x] Local report producer, browser presentation, registry/service wiring and confined Finder action.
- [x] Working report-host document and current durable Reports documentation.
- [x] Focused evidence and independent code review, with manual presentation review left to the user.

## Process

Open Work Downloads to inspect the current canonical references and files. Follow a Work to its Catalogue document or activate a saved filename to reveal it in Finder. Run/Refresh reads current inputs again. The report performs no canonical/media mutation, cleanup, conversion, publication or remote check.

## Delivery Steps

### WD-0 — Readiness

- [x] Confirm authority, supported exact Catalogue navigation and configured shared download storage.
- [x] Confirm the two-column scope and implementation approval.

Record: ready. Existing local report/service loaders, shared two-column styles, Catalogue route helper and Finder helper cover the required seams. This is a local report; public runtime projection and R2 coverage are outside the result. Stop for an unavailable configured workspace or a requirement that would introduce media mutation.

### WD-1 — Implementation And Evidence

- [x] Implement the full reconciliation, exact links and Finder validation.
- [x] Create the report host and inspect its watcher-generated payload, or use one targeted docs-only build if the watcher is unavailable.
- [x] Update Reports with the current behavior.

Verification budget: explicit changed-path Python/JavaScript lint, Python syntax and whitespace checks; bounded source/config review; one read-only invocation of the actual producer against current canonical data and configured files. These checks have small local cost and no media/network effects. The report-host projection may write only ordinary generated documents through the watcher or its targeted fallback. No tests, fixtures, harnesses or browser automation are authorized; visual interaction and real Finder launching remain user review.

Record: complete. Changed-path `bin/lint-js` passed for the report module, local report service and loader; `bin/lint-python` and `py_compile` passed for the producer/Finder owner, routes and dispatcher; `git diff --check` passed. A direct read-only producer invocation inspected real canonical references and configured storage, returning five matched rows. The first invocation exposed valid `downloads: null` records, now handled as no downloads consistently with Catalogue. The report host was placed immediately after Media in `index-order.json`; the running watcher generated its exact by-ID report descriptor without a manual Build. Existing two-column styles were reused and no public runtime inventory member changed. Missing, unassigned, shared-file and invalid-target branches received source review, not executable regression coverage.

### WD-2 — Code Review

- [x] Review the final contract/diff independently after focused evidence, resolving issues within the approved scope.

Gate: exact filename matching and blank cells remain consistent; Catalogue links and Finder actions retain their separate owners; local code/config do not enter public loaders or projections. Record the evidence limits without claiming unperformed manual scenarios.

Record: complete. Review confirmed exact filename joins, one row per reference plus unassigned files, null blank-cell meanings, browser-owned Work ordering, exact Catalogue targets and direct configured Finder confinement. Review changes translated filesystem/OS read/open failures to local API errors and blocked report navigation/actions until Finder completion; affected lint/syntax checks passed again. The report host's ordinary tree registration and watcher payload were inspected. No compatibility aliases or public loader/projection additions were introduced. UI ordering, Catalogue navigation and real Finder reveal remain manual review; the current data did not exercise missing/unassigned/shared-file branches.

### WD-3 — Closeout

- [x] Record implementation evidence and remaining manual review.
- [x] Update the Planned Features entry and retain this delivery for lookup.
- [ ] Record user manual review and closeout acceptance.

Record: implementation bookkeeping complete; manual review and acceptance pending. Retain the delivery for lookup. Commit, push and Publish remain separately authorized actions.
