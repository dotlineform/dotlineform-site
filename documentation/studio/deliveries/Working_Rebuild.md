---
draft: false
doc_id: d-20261013-174714-7e41a9
title: Working Rebuild
added_date: "2026-10-13 17:47:14"
last_updated: "2026-10-13 17:47:14"
parent_id: d-20260428-000000-f5ff18
---
# Working Rebuild

Status: implementation complete; manual verification pending. The user approved M.20's eight proposed changes on 2026-10-13. [Builder](../Builder.md#working-rebuild), [Source Mutation Endpoints](../Source_Mutation_Endpoints.md#post-docsrebuild) and [Search Index](../Docs_Search_Index.md) own the durable contracts; [User Facing Rules](../data/User_Facing_Rules.md) M.20 records review/evidence and acceptance state.

## Requirements

Complete Rebuild docs and Search remains one synchronous Working action over every configured document collection and required registered media/discovery output. Carry authoritative inputs through existing builders without source/configuration rereads, downstream agreement audits, subprocess diagnostic parsing or Working hash inventories. Complete all relationship updates before rendering their sections. Preserve source/schema/path safety, producer sanitization/byte verification, complete rendering, discovery coverage/readiness, Selected membership and stop-on-failure behavior.

Catalogue participates through saved document source rendering. Refresh, source Regenerate, Publish, publication queue handoffs, test migration and live data execution retain separate scope. Preview retains its independent byte inventories and publication verification.

## Deliverables And Process

One empty `/docs/rebuild` request loads configuration, canonical sources and Selected; produces referenced media; completes relationships; renders documents; refreshes Selected and shared discovery output; aggregates final Links; projects browser configuration; and records Working completion last. The UI awaits required refreshes, requires no displayed/default document to start and preserves completed-build evidence when refresh fails. The response identifies the reached phase and completed steps when generation stops.

## Delivery Steps

- [x] Readiness — approved finishable M.20 slice, owning service/build/browser boundaries identified, clean starting worktree, no live execution or test work authorized.
- [x] Implementation — all eight changes implemented through the existing document/media/Links/discovery owners; durable contracts updated.
- [x] Verification — focused Python/JavaScript lint, compilation, existing CLI import diagnostics and whitespace checks passed. These checks cost seconds, require no live workspace writes or network and provide static/import evidence only. No tests or profiles ran.
- [x] Code review — reviewed final source/diff for ownership, carried inputs, transfer/removal ordering, discovery membership, failure phases and busy completion. Corrected transferred-record ordering and the policy reader's hidden configuration reload. No compatibility alias remains in the retired full-build path.
- [x] Implementation closeout — M.20 is implemented with manual verification pending; local management code has no public projection delta. Retain this delivery while acceptance remains open.
- [ ] Manual acceptance — restart Docs Viewer and reload; exercise ordinary/collection and no-displayed-target rebuilds, cross-collection Related links/title changes, stale removals/transfers, referenced/unreferenced persistent Mermaid, Search/Recent coverage/exclusions, Selected metadata, partial generation failure and completed-build refresh failure.

## Follow-on

Live Build/media execution and manual review remain explicit actions. Runtime/memory improvements are inferred from removed work, without measured performance evidence. Existing lifecycle/rebuild/Search tests target retired contracts; migration and behavioral coverage require their own approved specification under [Test Contract Discipline](../Test_Contract_Discipline.md). M.19/M.27 publication handoff gaps remain with Incremental Document Publish.
