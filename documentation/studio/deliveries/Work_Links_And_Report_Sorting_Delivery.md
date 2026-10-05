---
draft: false
doc_id: d-20261005-153252-4b47a9
title: Work Links And Report Sorting Delivery
added_date: "2026-10-05 15:32:52"
last_updated: "2026-10-05 15:50:46"
summary: A local Work Links companion and sortable columns for both Work resource reports.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Work Links And Report Sorting Delivery

## Current And Next State

Status: implemented and reviewed, awaiting user manual review and acceptance. The user approved implementation on 2026-10-05, including authored link labels under a Links heading. [Work Links](/docs/?doc=d-20261005-153252-541ac3) follows Downloads in the ordinary tree and has its watcher-generated report descriptor. Restart Local Studio and reload Docs Viewer to load the new endpoint and modules. Manual interaction and presentation remain user review.

Complete result: Work Links lists canonical Work titles and authored link labels, while both Work Links and Work Downloads offer ascending/descending sorting on either column. [Reports](../Reports.md) is the durable owner; this delivery is parented to [Planned Features](../Planned_Features.md).

## Requirements

- Work Links reads canonical Work `links` directly and produces one row per authored link. Work titles open exact Catalogue documents; Links labels open their authored URLs in a new tab. Do not make remote requests, check availability, scan media, save a report snapshot or model missing/orphaned links.
- Both reports use clickable Work and resource headings, default Work A–Z, direction indicators and accessible sort state. Switching columns starts ascending; clicking the active heading toggles direction. Blank cells stay last in either direction. Preserve deterministic identity ties and sort selection through Refresh and retained Back navigation.
- Retain Work Downloads' title-only Work cells, blank missing/unassigned cells, exact reference validation and confined Finder action. Use black theme text and hover-only link underlining in both reports.
- Share only the common two-column presentation and sorting. Keep report-specific data validation, local filesystem actions and remote link navigation explicit. Add no compatibility aliases or public loader/projection entries.
- Register a local report and a Working host immediately after Work Downloads. Keep the new host explicitly excluded from publication. No Search rebuild, Publish, media mutation, commit or push is included.

## Deliverables

- [x] Canonical Work Links producer and empty-request local endpoint.
- [x] Work Links registration, loader, client and shared sortable presentation.
- [x] Working host, tree order and generated report descriptor.
- [x] Current durable documentation, focused evidence and independent source/diff review.

## Delivery Steps

### WLS-0 — Readiness

- [x] Confirm canonical Works authority, local report wiring and configured ordinary source/generated paths.
- [x] Confirm authored labels, new-tab URLs, sorting, missing-cell behavior and implementation approval.

Record: ready. Existing report routes, Catalogue target helper, local styles and sortable heading conventions cover the required owners. New link navigation must retain safe URL handling. Stop for an unavailable configured workspace; do not create another root.

### WLS-1 — Implementation And Focused Evidence

- [x] Implement the full result and update Reports.
- [x] Inspect the watcher-generated host; use only the new host's targeted doc-only build if its watcher output is unavailable.

Verification budget: changed-path JavaScript/Python lint, Python syntax, configuration JSON and whitespace checks; one read-only call to each actual report producer against canonical Works and configured download storage. These diagnose source/shape/wiring failures with small local cost, no remote calls and no data writes. The host's owning watcher or targeted fallback writes ordinary document projections only. Tests, fixtures, temporary regression scripts and browser automation are not authorized; sorting interactions, Back restoration, new tabs and Finder remain manual review.

Record: complete. Changed-path JavaScript lint passed for both report adapters, the shared presentation, service client and loader. Python lint and syntax passed for the shared canonical reader, both producers, routes and dispatcher. Registry, tree-order and publication-exclusion JSON parsed successfully, and whitespace checks passed. The initial JavaScript lint found a control-character regex; equivalent character-code validation replaced it and its lint rerun passed. One read-only invocation of each actual producer returned three link rows across three Works and six download rows, with no missing or unassigned files. The running watcher generated the exact new by-ID host descriptor; no manual Build or Search rebuild ran. Changed owners are local-only and absent from the public code projection inventory. These checks do not exercise browser sorting, retained Back, new tabs, Finder or malformed-input branches.

### WLS-2 — Code Review

- [x] Review final code/config/source changes after focused evidence for ownership drift, unsafe links, request agreement, null/sort semantics, retained state, busy controls and compatibility residue.
- [x] Resolve bounded findings and repeat only affected checks.

Record: complete. The distinct post-evidence source/diff review found no unresolved issues. Canonical identities are validated by one shared reader; report-specific row validation and Finder/navigation actions retain their owners. Review confirmed request/schema/loader agreement, safe authored URL handling, title-only Work cells, selected-column blanks last before direction reversal, deterministic ties, Refresh/retained sort state and busy controls. The host's tree position, generated descriptor and explicit publication exclusion were inspected. No compatibility aliases, remote checks or public loader/projection additions were introduced. Malformed-input and missing/unassigned branches received source review only; current real data does not cover those cases.

### WLS-3 — Closeout

- [x] Reconcile completion claims and record remaining manual review.
- [x] Update Planned Features and retain this delivery for lookup.
- [ ] Record user manual review and closeout acceptance.

Record: implementation bookkeeping complete; manual review and acceptance pending. Confirm both headings' ascending/descending behavior, hover-only underlining, new-tab labels, Refresh/Back sort retention and Downloads Finder reveal manually. No tests, browser automation, Finder launches, media writes, manual builds, Search, Publish, commit or push ran. Retain this delivery for lookup.
