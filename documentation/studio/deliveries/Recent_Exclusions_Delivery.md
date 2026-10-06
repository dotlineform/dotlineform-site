---
draft: false
doc_id: d-20261006-215144-c2937e
title: Recent Exclusions Delivery
added_date: "2026-10-06 21:51:44"
last_updated: "2026-10-06 21:51:44"
parent_id: d-20260428-000000-f5ff18
---
# Recent Exclusions Delivery

## Current And Next State

Status: implementation complete; focused static checks and bounded code review passed. The editable Working exclusion list owns every Recent-specific exclusion, with dotlineform and four collection landing pages initially listed. Publish preparation refreshes the one shared Recent list from current eligible metadata, and local Recent offers a VS Code action. Next: restart/reload for user manual review and run full Build or Publish to apply the initial list. No Build, Search rebuild, Publish, browser automation, tests, commit or push was performed. This delivery is parented to [Planned Features](../Planned_Features.md); [Source Organisation](../Source_Organisation.md#recent-exclusions) owns the editable policy and [Generated Data Contracts](../Generated_Data_Contracts.md#recent-contract) owns the payload/lifecycle.

## Requirements And Deliverables

- Let the editable list control every Recent-specific exclusion, without automatic host rules. Exclude exact document targets only, retaining descendant, Search and publication eligibility.
- Seed `working/source/documents/recent-exclusions.json` with dotlineform (`d-20260426-164043-e14f49`) and the Context, Concepts, Moments and Catalogue hosts. The array uses `doc_id` with optional exact collection identity; malformed or missing policy fails visibly and an empty array is valid.
- Expose Open Recent exclusions in VS Code in the local Recent view through the existing index-view control surface and a configured-file-only empty-body service action. Retain ability to open invalid JSON for repair.
- Use one shared sorter, exact exclusion filter and limit for full Working Builds and Publish. Publish derives candidates from the eligible sources already loaded for its full temporary build, replenishing to the configured limit when sufficient dated documents remain.
- Bind prepared Recent bytes into the plan, validate them in the temporary build, then remove the previous Working full-Build receipt and write identical bytes to Working before Preview replacement. Distribution copies the completed snapshot without filtering. Keep Search's existing capture/copy policy.
- Invalidate Manage's cached Recent entries and error through the list controller after Publish attempts, including failures after Working refresh. Preserve ordinary save/watcher/targeted-build behavior and avoid an extra Working Build or source scan.

## Process

Open Recent, choose its VS Code toolbar action, edit and save the exclusion array, then run full Build or Publish. Publish already performs the full eligible document build and refreshes the shared list without requiring a prior Build. Reload Recent after a full Build; Publish refreshes the visible cached list automatically. Restart Local Studio to register the new service endpoint and reload the management modules for the new control.

## Delivery Steps

- [x] **REC-0 — Readiness:** confirmed current eligibility, collection coverage, source metadata loading, configured storage, completed-snapshot distribution, existing index-view control wiring and VS Code service ownership. User selected list-controlled exclusions and the VS Code action; no additional approval gate remains.
- [x] **REC-1 — Implementation:** delivered exact-target policy and initial data, common payload generation, Publish source-metadata refresh, plan binding, Working write, local control/endpoint and Manage cache invalidation. Durable owners describe the schema and partial-failure effects.
- [x] **REC-2 — Verification And Review:** `bin/lint-python` and explicit Python `-m py_compile` passed for the nine changed Python files; focused JavaScript lint passed for the six management and two shared modules, with affected files rechecked after review changes. The policy passed existing JSON parsing diagnostics; scoped tracked/new-file whitespace checks emitted no errors and the focused sanitization scan found no machine paths or credentials. These inexpensive static commands address syntax, source mistakes and public projection drift, writing only normal caches and explicit runtime projections. `bin/site-code-update` changed only the two shared runtime projections, retaining the earlier Summary stylesheet projection; `--check` and `bin/site-validate` passed. Bounded review covered exact identities, filtering before limit, host/descendant independence, current prepared metadata, captured policy/plan binding, byte-preserving distribution, malformed-policy repair, control ownership and failure effects. Review corrected retained Recent errors and invalidated the old Working completion receipt before the Recent write. No blocking source finding remains. No tests or browser/UI checks were run; generation, VS Code launch, Publish and failure recovery remain unexercised.
- [x] **REC-3 — Closeout:** implementation and durable transfer are complete. User manual review remains pending; initial data takes effect on the next full Build or Publish. Retain this delivery and its Planned Features link for review/recent-work lookup. No temporary verification document or compatibility alias was added, and no documents were deleted.
