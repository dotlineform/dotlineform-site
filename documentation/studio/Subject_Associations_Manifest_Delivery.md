---
draft: false
doc_id: d-20260927-191938-974cc3
title: Subject Associations To Manifests - Delivery
added_date: "2026-09-27 19:19:38"
last_updated: "2026-10-03 17:35:06"
summary: Retire subject-associations.json from all collections and derive existing report associations and navigation from management manifests without changing front matter or collection ownership.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Subject Associations To Manifests - Delivery

Complete under [Planned Features](Planned_Features.md). SM-0 through SM-3 passed, including user confirmation of all three manual interactions. [Subject Associations](data/subject-associations.md) records maintained behavior. This delivery is retained pending a separately authorized archival or deletion decision. The superseded Catalogue retirement proposal was retired on 2026-10-03; Catalogue stays and future Subject work is separate.

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

- [x] Confirm manifests supply all consumers without source/schema changes.
- [x] Agree implementation and verification scope.

Evidence: read-only owner/configuration and saved-manifest inspection on 2026-09-27. Record: manifests supply the three consumers without source/schema changes. The user authorized SM-1 and focused lint, syntax and output diagnostics. No test changes, automatic Search rebuild or Publish were authorized. Gate: passed; stop if a broader contract change is required.

### SM-1 — Implementation

- [x] Migrate readers, retire association code/artifacts and update the durable inventory.

Evidence budget: changed-file lint and focused module/service/output diagnostics, selected before non-trivial runs. Rebuild affected document owners only when reconciliation is required; no automatic Search rebuild or Publish. Test changes require separate approval under [Test Contract Discipline](Test_Contract_Discipline.md).

Record: implemented without association fallbacks. The shared Catalogue navigation reader uses private manifest rows; Project State groups Works rows directly. Required subject projection and targeted merges retain manifest generation. The local browser projection now supplies the existing configured report host; public configuration is unchanged. Association helpers, writes, read allowance, Preview validation and distribution branches are removed. Durable inventory and directly affected Catalogue/customisation guidance are updated. Cleanup removed three Working files (Works, Moments, Catalogue) and two Preview files (Works, Catalogue); all configured association files are absent. Preview's completion receipt was already absent and remains absent. No document-source or manifest-schema changes were made.

Evidence: explicit changed-file Python lint (ten files), JavaScript lint (two files) and Python compilation passed. Project State producer output with a fixed timestamp was byte-identical before/after, including 234 placements from 244 manifest rows. Dry-run `docs-viewer/build/build_docs.py --stage working --collection works --skip-media-builds --diagnostics` passed; targeted dry runs using the same options plus `--only-doc-ids d-20260801-212422-43b47c` for Works and `--only-doc-ids d-20260923-101144-8ee4cf` for Catalogue passed. All three reported zero document/manifest changes and zero warnings, so no write rebuild was required. `bin/site-code-update` changed only the shared config-controller projection; `bin/site-code-update --check` and `bin/site-validate` passed. Active production code has no association-file references. Tests were not changed or run; existing association-product and Project State path fixtures need separately approved review. No Search rebuild or Publish was run. Gate: SM-1 complete; stop for SM-2 code review and manual confirmation of the three interactions.

### SM-2 — Code Review

- [x] Review identity, grouping, targeted builds, unchanged front matter/schema, cleanup and dead paths; resolve findings.
- [x] Manually confirm Catalogue Works links, Works Subject links and Project State.

Evidence: bounded production/configuration/documentation/projection diff and caller review on 2026-09-27, reusing SM-1 output evidence. Record: no unresolved findings and no code corrections required. Both navigation consumers receive normalized Manage configuration and retain plain text for absent mappings and errors for ambiguity. Configured hosts own routes; Project State retains every valid document per subject and its presentation ordering. Targeted metadata merges, reader manifests, management-manifest privacy and publication eligibility remain intact. Removed helper/validator signatures have no stale production callers; source, collection configuration, test files and public browser configuration are unchanged. Canonical/projected config-controller bytes match. Current configured Working/Preview association files and the Preview receipt are absent. The user explicitly confirmed all three manual interactions pass. Gate: passed.

### SM-3 — Closeout

- [x] Record acceptance, durable transfer, artifact state and separate test/publication work; recommend retaining or retiring this document.

Evidence: reuse accepted SM-1 and SM-2 results; the closeout edit requires only `git diff --check`. Record: accepted. Consumers work without association files, with user-confirmed navigation and Project State behavior. Maintained behavior is transferred to [Subject Associations](data/subject-associations.md), [Catalogue Works](Catalogue_Works.md) and the directly affected subject section of [Sub-Scope Customisation Architecture](Sub_Scope_Customisation_Architecture.md). No document-source or manifest reconciliation was required; only the local browser configuration and one tracked shared-runtime projection were refreshed. The five obsolete external artifacts are removed and Preview has no completion receipt. Existing tests that depend on retired association products or Project State path inputs need separately specified and authorized review; this is separate from the accepted product cutover. Publish and its live distribution evidence remain separate, as do Search rebuilds and Git/public deployment. Recommend manually archiving this completed delivery after closeout review; retain it until that action or deletion is explicitly authorized. Gate: passed; Publish, commit, push and document deletion were not performed.

## Follow-on

After closeout, the user corrected Context's navigation requirement: Work subjects open Media View like Series subjects. Context's Catalogue document lookup was removed; Catalogue Works and Project State retain their manifest-based readers. Focused JavaScript lint and whitespace checks passed for this small UI correction; its revised Work interaction awaits manual confirmation. The completed delivery evidence above records the behavior accepted at its closeout.

Catalogue retirement, receipt/schema simplification, smaller lookups and Related Links remain separate decisions.
