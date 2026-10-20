---
draft: false
doc_id: d-20261020-150536-a8f3c2
title: Projects Metadata Snapshot
added_date: "2026-10-20 15:05:36"
last_updated: "2026-10-20"
parent_id: d-20260428-000000-f5ff18
---
# Projects Metadata Snapshot

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Reports](../Reports.md). Status: implemented and reviewed; awaiting user manual acceptance. The user approved this first delivery on 2026-10-20.

## Requirements

Give Projects one private, persisted metadata snapshot and an explicit Refresh lifecycle while retaining the existing Context-only, Subject-based associations. Opening reads the saved snapshot; Run/Refresh gathers, saves and displays new inputs. Missing metadata asks for Refresh. The saved timestamp owns freshness; document edits and Catalogue changes do not alter mounted or persisted results until Refresh.

Python owns configured snapshot reads/writes, one immediate physical-folder scan and one read of each existing Context/Work/Series input during Refresh. The browser owns Subject placement, counts, grouping, search, sorting, exact document links and TSV presentation. Existing shared manifests/indexes, document sources and publication remain unchanged. Outbound Work/Gallery associations and Subject retirement are a later delivery.

## Deliverables And Process

- Configure `working/generated/reports/projects/metadata.json` as Projects' local report artifact.
- Add a parameter-free saved-data GET and retain the empty-object POST as the explicit Refresh operation; neither operation builds Docs or refreshes Catalogue.
- Preserve Folder/Work/None placement, unmatched physical folders, known-Series grouping, first-level folder interpretation, Finder/document destinations and retained browsing controls.
- Remove committed-document update subscriptions and unused placement-update machinery so displayed results consistently represent the saved snapshot.
- Use the existing local-only route/module boundary; opening never creates metadata or scans Projects.

## Delivery Steps

- [x] Readiness: traced the current report service, workspace location/configuration, saved Catalogue inputs, folder scan, browser placement and committed-update paths. This is one finishable persistence/freshness change; link extraction, Subject migration, scope expansion and shared-manifest changes are stop conditions.
- [x] Implement the configured saved reader, explicit refresh writer, GET/POST wiring and browser lifecycle.
- [x] Update Reports and the existing Subject/Catalogue-input descriptions; keep durable guardrails in Development Checklist.
- [x] Run the bounded static/diagnostic evidence below and inspect only the resulting owner diff.
- [x] Complete a distinct code review, including the mandatory Redundancy And Defensive Behavior Review; record findings and retained safeguards here.
- [x] Close implementation with exact evidence and remaining manual acceptance. Retain this delivery for the following association change and acceptance; Reports owns lasting behavior.
- [ ] User manual acceptance after restarting Docs Viewer services and force-reloading Manage: saved opening, explicit Refresh/time, unchanged Subject placement, grouping/search/sort/copy, exact Finder/document destinations, retained navigation and Refresh-only adoption of later changes. First-use/error states remain unexercised in the browser.

Verification budget: focused lint for changed Python/JavaScript owners, Python compilation, workspace JSON/configuration parsing and service import/read diagnostics address wiring, syntax and the saved-read boundary. Expected cost is seconds to under a minute, with only ordinary lint/bytecode outputs and read-only access to configured inputs; no network, browser automation or test work. Any initial snapshot creation is a normal explicit Refresh operation, recorded separately from static evidence. Existing Project State tests contain superseded producer/scope/response contracts; they remain unchanged and unrun under [Test Contract Discipline](../Test_Contract_Discipline.md). User manual acceptance owns opening, missing/saved/failed Refresh states, refresh time, unchanged Subject placement, grouping/search/sort/copy, destinations and retained navigation.

## Code Review And Closeout Record

Focused evidence passed: `bin/lint-python` for `docs_project_state.py`, `docs_workspace_config.py`, `docs_management_routes.py`, `docs_management_read_service.py` and `docs_management_service.py`; `bin/lint-js` for `docs-viewer-report-service.js`, `project-state-data.js` and `project-state-report.js`; Python compilation for the five changed services; environment-loaded management imports and a normal saved-data GET returning `{ok: true, metadata: null}` before first Refresh; workspace configuration parsing and whitespace review. Removed a trailing blank line found by the initial whitespace check. These diagnostics exercise service import/configuration and the absent-snapshot read, not HTTP/browser transport or synthetic failure scenarios.

Initial snapshot creation was a normal explicit Refresh through the production management dispatcher, separate from static verification. It returned HTTP status 200 and saved `2026-10-20T15:10:03Z` metadata with 208 folders, 159 Context documents, 4,618 Works and 139 Series. The operation scanned current project folders and wrote only the configured private Projects artifact, without Docs/Search generation, Catalogue Refresh, media writes or publication effects. Counts describe captured inputs, not placed/visible documents. There was no repeated Refresh or output-verification pass.

Distinct code review traced saved/missing reads, normal/empty/unchanged Refresh, input/write failures, request dispatch, Subject composition, grouping/filtering/TSV, retained browsing and disposal. The mandatory Redundancy And Defensive Behavior Review removed committed-document callbacks and the unused retained placement/Work/folder maps, retaining build-local joins and a carried document count. GET performs one snapshot read after configuration resolution; Refresh reads each existing input once, assembles complete facts, writes once and returns the same metadata. It performs no output reread, membership/count/date audit, content hash, canonical fallback, automatic regeneration, compatibility alias, rollback or backup. New asynchronous load completion uses the existing retained-view disposal boundary and leaves already displayed results visible on failure; it adds no concurrent-operation model.

Retained safeguards have explicit owners and bounded costs: workspace configuration confines the private metadata path beneath Working reports without symlink traversal; the saved reader parses one JSON object and handles ordinary absent/read/parse outcomes; existing Catalogue/document readers retain their representation checks once per Refresh; the shared Projects scanner and Finder action retain configured-root/path checks; browser Subject classification, text-node rendering and exact URL owners retain interpretation/presentation/navigation boundaries. Empty-body/no-dry-run POST and parameter-free GET enforce the new persistence/read interface. These are storage, representation and action boundaries, not repeated validation of saved report rows. Shared manifests/indexes and the local/public inventory remain unchanged.

Tests, fixtures, harnesses and profiles remain unchanged and unrun. No HTTP/browser automation, service restart, public projection, Docs/Search build, Publish, deployment, commit or push ran. Retain this delivery and its Planned Features link through manual acceptance and the later association delivery; durable behavior belongs to Reports, with the existing Subject/Catalogue-input descriptions updated directly.

## Follow-on

Replace Projects' Subject placement with outbound Work/Gallery associations only in a separately agreed delivery, including the existing documents without references and any broader Subject-consumer changes.
