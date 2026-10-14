---
draft: false
doc_id: d-20261014-180649-92c49d
title: Project State Optimisation
added_date: "2026-10-14 18:06:49"
last_updated: "2026-10-14 18:11:12"
parent_id: d-20260428-000000-f5ff18
---
# Project State Optimisation

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Reports](../Reports.md). The user approved the reviewed optimisation scope on 2026-10-14 and explicitly required tests to remain unchanged.

## Agreed Result

Python owns one configured workspace load, the live immediate Projects folder scan and one read of each saved document/Work/Series input. The browser owns joins, placement, counts, exact viewer links and prepared Folder/Series groups. Initial loading and committed document changes use one placement function. Search filters prepared ordered rows, sorting runs only after dataset/group/sort changes, and Copy table serializes the displayed projection.

Preserve unmatched physical folders, Folder/Work/None semantics, first-level folder interpretation across media sources, known-Series grouping, exact document/Finder destinations and TSV columns. Trust completed authoring/build/Refresh handoffs without output audits, provenance recounts, duplicate row validation, title normalization, unused reconciliation diagnostics or compatibility aliases. Retained storage, representation and OS-action safeguards and their costs are recorded in Reports.

## Completion Gates

- [x] Readiness: traced the report, loaders, saved-input and directory helpers, browser placement/sort/filter/copy/update paths and public inventory; user approved the complete slice.
- [x] Replace the producer/validator with a narrow read-only input service and update the owning route.
- [x] Implement shared browser placement and prepared grouped/search/comparison data; carry mounted state through search, copying and retained navigation.
- [x] Update Reports, Subject Associations, Catalogue Report Inputs and the durable implementation guardrail; parent this delivery here.
- [x] Focused Python lint/compilation passed for the input reader and management route; JavaScript lint passed for the data and report modules, and whitespace/source checks passed. One read-only production input call returned 205 folders, 235 documents, 4,620 saved Works and 140 Series. This confirms current input resolution/parsing, without proving HTTP/browser transport, rendering or committed-update execution.
- [x] Complete the distinct code review and mandatory Redundancy And Defensive Behavior Review. Traced normal/empty/unchanged/failure, grouping/search/copy/restore and committed move/delete paths; reviewed shared configuration, Catalogue reader, Subject classifier, Projects scan and local-target/link boundaries. Removed the remaining generic TSV fallback, narrowed composition's dependency from the report context to its exact URL callback, and corrected a second stale response-envelope description in Reports. Confirmed no compatibility alias, output audit, freshness pass, repair, canonical fallback, public projection or test delta remains within this slice. Retained safeguards and their owning costs are recorded in Reports; lint affected by review changes passed.
- [ ] User manual acceptance after restarting Docs Viewer services and force-reloading the viewer: Run/Refresh, Folder/Series grouping, search, sorting, copied TSV, status counts, exact document/Finder destinations, retained navigation and committed document moves/deletions.

Tests, fixtures, harnesses and profiles remain unchanged and unrun. Existing Project State tests retain retired APIs and response/scope contracts; migration requires separate approval under [Test Contract Discipline](../Test_Contract_Discipline.md). No browser automation, service restart, source/media/generated-data write, Docs/Search build, Publish, deployment, commit or push is part of this delivery. Changed browser modules are local-only and outside the public projection inventory. The private service/browser cutover requires adopting both together; manual acceptance remains separate from static and current-data evidence.
