---
draft: false
doc_id: d-20261005-234748-f80b29
title: Folders Without Works Report Delivery
added_date: "2026-10-05 23:47:48"
last_updated: "2026-10-22"
summary: Recursive local inspection of folders with no directly registered Work primary source.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Folders Without Works Report Delivery

## Current And Next State

Status: retired at the user's request on 2026-10-22. The original implementation and verification below are historical. [Reports](../Reports.md) owns the current inventory. Retain this document and [the optimisation delivery](Folders_Without_Works_Optimisation.md) for historical evidence pending manual archive.

## Retirement

The user authorized retirement of Uncatalogued Folders while retaining shared `private/work-sources.json`. Browser ownership ends with removal of the loader, renderer, request method, report styles and private-action identity. Server ownership ends with removal of the scan producer, route/dispatch and its unused private-reader convenience wrapper. Projects, Uncataloged Images and Missing Source Files continue to use the existing saved input reader and shared filesystem inspector; Catalogue Refresh production and the saved input contract are unchanged. No alias or replacement is introduced.

The existing confirmed document-deletion owner removed only host `d-20261005-234748-d69c84`, its Index entry and generated payload, completing its ordinary publication handoff with zero warnings. Its explicit publication exclusion was removed directly. Search and Recent were not rebuilt; no Publish, commit, push or deployment ran. Restart Docs Viewer services and force-reload Manage to adopt the removed route and browser registration.

Verification budget: changed-path Python/JavaScript lint, Python compilation/import diagnostics, registry JSON parsing, whitespace and scoped reference/diff review. These checks address dangling imports/registrations and accidental shared-reader changes, cost seconds with no network or report scans, and create only normal compiler/lint caches. Tests remain unchanged and unrun under [Testing](../Testing.md). Browser interaction remains manual. The changed browser/CSS/config files are local-only and outside the public projection inventory.

- [x] Remove dedicated report runtime, configuration and host through the owning boundaries.
- [x] Complete focused verification and distinct code review, including the mandatory Redundancy And Defensive Behavior Review.

Evidence: Python lint passed for the route constants, dispatcher and private-input owner; JavaScript lint passed for the loader, request service and action definitions. The three changed Python files compiled, the management service and all three surviving source-report modules imported, and report registry JSON parsed. Whitespace and scoped reference review passed; no runtime or test caller references the retired producer, route, renderer, service method or reader wrapper. The host deletion wrote no documents, removed one generated payload and wrote one index with zero warnings. No tests or browser checks ran.

Distinct code and redundancy review: the remaining reports pass resolved Working locations to `read_catalogue_report_input` and still consume `WORK_SOURCES_PATH`; the removed wrapper had only the retired report as a caller. All shared inspector methods retain callers in Uncataloged Images or Missing Source Files. Removing the report eliminates its recursive scan and response/presentation lifecycle without adding validation, freshness work, fallback, compatibility or recovery behavior. Existing saved-input parsing, configured path/symlink confinement and Finder authority retain their original owners and costs. Host removal reused the ordinary exact-target/confined-path Delete and completed generation/publication handoff, with no new deletion machinery. No actionable findings remain within this boundary.

## Historical Implementation

Complete result: Folders Without Works lists every physical folder below the configured Work source roots with no directly registered canonical Work primary source, including empty and non-image folders. Works below distinguishes unused branches from containers with catalogued descendants.

## Requirements And Decisions

- Recursively scan every configured Work source root, currently `projects/` and `processing/`, on mount and explicit Run/Refresh. Include ordinary hidden directories; skip symbolic links and do not list the source-root containers themselves.
- Derive direct membership from current canonical Work source folder/subfolder and primary filename declarations. Count a registered Work even when its primary file is missing, provided its physical folder exists. Match physical folder identity so filesystem case or Unicode spelling does not produce false unused rows.
- Display Folder and Works below columns, full relative paths in deterministic A–Z order and folder links through the existing confined Finder action. A zero means no registered Works anywhere beneath that folder.
- Keep no saved snapshot, content/image heuristic, filesystem mutation or public report. An unreadable folder or unavailable configured root fails the scan visibly without presenting partial results.
- Use current local report/service owners and styles; no compatibility aliases or changes to existing report contracts.

## Deliverables

- [x] Readiness and scope confirmed: a separate recursive report complements immediate-only Projects and represented-folder Uncataloged Images. Existing local registry, loader, empty-body service dispatch and Finder action cover integration; no public runtime inventory change is needed.
- [x] Implement producer, renderer, registry/service wiring and report-owned local presentation.
- [x] Create the Working host, register its index placement and explicit publication exclusion, and inspect its watcher projection or use the approved targeted fallback if unavailable.
- [x] Update durable Reports documentation and Planned Features routing.
- [x] Complete focused evidence and final code review.
- [x] Record user manual review and acceptance.

## Verification Budget

Use changed-path Python/JavaScript lint, Python syntax, JSON parsing and whitespace/source review, plus one read-only invocation of the actual producer over current canonical Works and configured media roots. The recursive scan cost depends on the existing folder tree; it lists directories without opening file content. The ordinary watcher or one targeted docs-only fallback may write the host's generated projections. No tests, fixtures, regression scripts, browser automation or real Finder launches are authorized. [Testing](../Testing.md) owns separate test-work approval. Manual presentation, Finder interaction and usefulness remain acceptance gates; Search, Publish, commit and push are separate actions.

Evidence: changed-path Python and JavaScript lint, Python syntax and whitespace checks passed. Report registry, source index order and publication exclusions parsed successfully. The watcher-generated by-ID host contains the exact report descriptor. Final source review confirmed physical directory matching, one scan per directory, reverse parent accumulation, fail-visible scans and local-only loader/style ownership. A read-only POST to the running service returned 404, confirming restart is required; no service was stopped. No executable tests, synthetic regression scripts, browser checks, real Finder launches, manual Builds, Search, Publish, commit or push ran. The current folder tree did not exercise positive Works below rows; that accumulation received source review only, alongside missing/unreadable/symlink behavior.
