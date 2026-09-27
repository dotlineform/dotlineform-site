---
draft: false
doc_id: d-20260927-191938-974cc3
title: Subject Associations To Manifests - Delivery
added_date: "2026-09-27 19:19:38"
last_updated: "2026-09-27 19:19:38"
summary: Retire subject-associations.json from all collections and derive existing report associations and navigation from management manifests without changing front matter or collection ownership.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Subject Associations To Manifests - Delivery

Proposed, not started, under [Planned Features](Planned_Features.md). [Subject Associations](data/subject-associations.md) records current behavior. The [Catalogue retirement option](Subject_Associations_Retirement_Delivery.md) remains separate.

## Requirements

Remove `subject-associations.json` from every collection while preserving current report results, icons and navigation. Reports derive the required associations from existing `manage-manifest.json` rows instead.

- Change no front matter, document IDs, assignment rules or readiness. Keep Catalogue's collection, source, Regenerate and document JSON.
- Use existing `authoring_subject` rows and metadata; introduce no manifest schema change or replacement lookup.
- Catalogue Works and the Works Subject column derive `work_id → doc_id` from Catalogue's management manifest. Preserve ambiguity errors and plain text for missing mappings. Compose exact links using existing route helpers and configured hosts.
- Project State groups Works manifest rows by valid subject. Preserve multiple documents per subject, placement, diagnostics, icons and exact document links; invalid subjects remain management evidence.
- Remove association generation, reads, validation and publication handling. Remove cross-file receipt comparisons; retain manifest `subject_generation` where existing reports consume it.
- Preserve full/targeted builds and unselected metadata. Required subject projection must not depend on an old association file. Preserve reader manifests, publication eligibility and management-manifest privacy.

## Deliverables

Manifest-based readers; removal of association producers/helpers, read allowances and Preview/distribution branches; owner-confined cleanup of Working/Preview association files. Invalidate the Preview receipt if cleanup changes its snapshot. Preserve source, registrations, media and unrelated output. Update the durable inventory at closeout.

## Process And UI Actions

Existing completion boundaries remain unchanged. Builds maintain manifests; reports derive mappings in memory.

| Action | Change Required |
| --- | --- |
| Assign/Change Subject; source editing; Source Editor Save | Preserve source writes and completion/watcher behavior; omit association output. |
| Build, Regenerate, document create/import/delete | Maintain manifests and targeted merges; generate no association file. |
| Open Catalogue Works | Read Catalogue's management manifest for links; retain private Work/Series metadata. |
| Open Works collection | Preserve subject display/icons; change only Catalogue navigation's mapping input. |
| Project State Run/Refresh | Derive grouping and navigation from the Works manifest without a second-file join. |
| Catalogue, Work Document Coverage, links and Series media | Preserve behavior and existing manifest contracts. |
| Publish | Omit association generation/validation/distribution handling; preserve eligibility and private-data exclusion. |
| Studio Work Save | Unchanged; Catalogue document Regenerate remains separate. |

## Delivery Steps

### SM-0 — Readiness

- [ ] Confirm manifests supply all consumers without source/schema changes; agree implementation and verification scope.

Evidence: read-only inspection. Record: proposed. Gate: authorize implementation; stop if a broader contract change is required.

### SM-1 — Implementation

- [ ] Migrate readers, retire association code/artifacts and update the durable inventory.

Evidence budget: changed-file lint and focused module/service/output diagnostics, selected before non-trivial runs. Rebuild affected document owners only when reconciliation is required; no automatic Search rebuild or Publish. Test changes require separate approval under [Test Contract Discipline](Test_Contract_Discipline.md). Record: not started. Gate: complete cutover without fallbacks; record evidence and Preview receipt state.

### SM-2 — Code Review

- [ ] Review identity, grouping, targeted builds, unchanged front matter/schema, cleanup and dead paths; resolve findings.

Evidence: bounded diff/output review. Record: not started. Gate: no unresolved findings; manually confirm Catalogue Works links, Works Subject links and Project State.

### SM-3 — Closeout

- [ ] Record acceptance, durable transfer, artifact state and separate test/publication work; recommend retaining or retiring this document.

Evidence: reuse accepted results. Record: not started. Gate: consumers work without association files. Publish, commit, push and document deletion remain separately authorized.

## Follow-on

Catalogue retirement, receipt/schema simplification, smaller lookups and Related Links remain separate decisions.
