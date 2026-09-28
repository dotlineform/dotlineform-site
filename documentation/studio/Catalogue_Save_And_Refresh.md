---
draft: false
doc_id: d-20260927-223812-8042fc
title: Catalogue Save And Refresh
added_date: "2026-09-27 22:38:12"
last_updated: "2026-09-28 09:50:17"
summary: Current Catalogue Save completion and a proposed delivery to keep the Works editor current while moving broader generated readers to an explicit Refresh Catalogue action.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Save And Refresh

## State And Outcome

**Current:** Save persists canonical edits, completes local media, generates Catalogue consumer output and private report metadata, rewrites private Studio lookups, then refreshes the editor. There is no Refresh Catalogue button. **Proposed:** Save completes only the canonical edit, required local media and the reads needed for the Works editor to stay current; one explicit **Refresh Catalogue** action reconciles the other generated Catalogue readers. Implement this boundary before [Related Galleries](Related_Galleries.md). Hosting and source-location choices are separate [future options](Catalogue_Hosting_And_Storage_Options.md).

This document describes the shipped flow below and tracks one proposed delivery. A proposed step is not current behavior. [Catalogue Deployment](Catalogue_Deployment.md) remains the authority for the separate Docs Publish and public deployment workflow.

## What Save Currently Does

The same completion owner serves single/New Work Save, bulk Work Save, Work and Series create/save/delete, and Gallery definition operations. Work Save also owns its Gallery memberships. Definition-only Gallery operations do not prepare Work media. Bulk Work creation remains separate. The source of truth is `studio/data/canonical/catalogue/`; Working Catalogue output is configured beneath `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`.

| Phase | Current effect and owner |
| --- | --- |
| Validate and persist | The editor sends the applicable record, expected revision and Gallery membership expectations. Catalogue services validate exact IDs and conflicts against canonical Works, Series, Galleries and membership files. Changed source files are replaced through the canonical transaction; an unchanged or Gallery-only Work Save does not rewrite `works.json`. A successful transaction is a confirmed canonical Save even if later completion fails. |
| Select and prepare local media | `catalogue_output_service.py` compares previous/current canonical records and selects affected Works, both ends of Series changes and affected Galleries. For selected media-bearing Works, `catalogue_output_media.py` prepares required primaries and thumbnails from exact Projects-owned originals. The media transaction commits complete local bytes, measured dimensions and any changed `media_version` together. Staged download replacements use the configured media staging area; absent required local downloads fail. Save makes no R2 request or remote deletion. |
| Generate consumer Catalogue | `generate_work_pages.py` loads and projects the whole canonical corpus in memory even for a focused Save. `catalogue_output_selection.py` chooses affected by-ID Work/Series/Gallery files, including former/current memberships and Gallery co-members. The generator compares content versions before writing selected records, all three discovery indexes and `media-config.json`. Focused Save avoids a complete obsolete-file sweep, but selection and computation can still be broad. |
| Update private Docs readers | `catalogue_works_metadata.py` updates affected entries in `reports/catalogue-works/metadata.json`; a changed entry rewrites that aggregate once. `works_collection_metadata.py` updates affected Work/Series titles in `reports/works/manifest.json`. Both live under Working Catalogue output, remain private, and are outside the public Catalogue artifact inventory. Gallery-only definition changes do not update these two files. |
| Refresh private Studio lookups | `catalogue_lookup_refresh.py` runs a full export under `studio/data/generated/catalogue-lookup/`: Work search, Series search and every Series record are rewritten, with stale Series files removed. The Works editor's main search and focused reads use live canonical service projections, not these persisted files. Its subject picker still has a generated Catalogue provider dependency that must be traced before the split. |
| Finish the editor | The response carries current records, revisions, memberships and output diagnostics. The editor updates its in-memory lists and draft baseline; an existing single Work also performs a focused live read. Save busy state ends after this completion. A later editor read/refresh failure does not negate a confirmed canonical Save. |

An output/media failure preserves the canonical edit and reports saved-but-incomplete. A separate lookup attempt currently runs even after an earlier output failure; its error can replace the earlier output error in the response. Missing or invalid report metadata fails rather than triggering a complete rebuild. A retry of an unchanged Work Save is not guaranteed to repair a failed source-image change: persisted source fields can compare unchanged and timestamp planning can retain older rendition bytes. This inherited recovery weakness needs a separate agreed fix; the Save/Refresh split must not claim to solve it. No latency measurements or exhaustive failure-path exercise are recorded.

Current explicit maintenance commands remain available for complete generated JSON, private report metadata, Works collection titles and private Studio lookups. They are repair/initial-generation operations, not a user-facing Refresh Catalogue action:

```bash
python3 studio/services/catalogue/catalogue_json_build.py
python3 studio/services/catalogue/catalogue_works_metadata.py
python3 studio/services/catalogue/works_collection_metadata.py
python3 studio/services/catalogue/export_catalogue_lookup.py
```

These commands preview changes by default; append `--write` to apply an intentional repair. They have different output scopes: the JSON builder does not prepare primary media or refresh private Studio lookups, and the report metadata commands do no media, Docs Build or Search work. Use their own documented targeted flags only for deliberate repair.

## Requirements

Save must validate and persist the exact edit, retain conflict and membership checks, complete media and version changes required for immediate editor previews, and return current records for the editor's lists, labels, pickers and reopening. Metadata-only and membership-only edits should skip unrelated image work. Remove Save-time whole-Catalogue projection and exports once no editor reader depends on them. Preserve clear canonical-saved versus editor/media-incomplete outcomes.

Refresh Catalogue must use current canonical records to reconcile generated Work/Series/Gallery by-ID data, discovery indexes, media policy and the private Docs Catalogue Works and Works collection metadata used by reports. Include retained private Studio lookup exports only where an actual consumer still needs them; retire unused exports through an explicit consumer review rather than maintaining a second accidental authority. Refresh must handle renamed, moved and deleted identities and former memberships, including a complete reconciliation path when prior generated output cannot supply invalidation targets. The visible operation is one awaited action with success or actionable failure feedback.

The Works editor must show confirmed Save values immediately and after reopening even when Refresh has not run. A generated Docs reader may intentionally show the previous refreshed state until Refresh succeeds. This changes the current Catalogue Works expectation of displaying the latest Save; update its reader contract and user-facing freshness explanation when implementing the split. Show a Catalogue-wide refresh-needed state that survives leaving and reopening the editor; it must distinguish unsaved edits, an incomplete Save and a completed Refresh. A failed Refresh preserves canonical changes and does not claim that downstream readers are current. Define the smallest reliable freshness receipt/status mechanism during implementation; do not assume a pending-publication ledger or background rebuild.

Refresh is local generation. It does not prepare Preview, transfer R2 media, run Docs Build or Search, commit, push, or deploy. Docs Publish continues to capture the current generated Catalogue files and distribute its completed Preview under its existing owner. If Publish runs while Refresh is needed, it can capture older Catalogue JSON; the editor workflow must make that consequence clear. An enforced Publish gate is a separate decision. The private report files must remain outside public publication.

## Deliverables And Process

- A reusable Catalogue service boundary for immediate Save completion and explicit complete Refresh, with no duplicate source authority or compatibility endpoint.
- A **Refresh Catalogue** control in the Works editor, with awaited busy/result feedback and a persistent, truthful refresh-needed indication.
- Updated current-state documentation and proportionate evidence for editor freshness, generated readers, failure boundaries and the separate Publish path. Tests or fixtures require their own agreed specification.

1. Edit and Save a Work, membership or definition. The editor reflects the confirmed canonical result and any required current local media without waiting for consumer-wide generation.
2. Continue editing; the Catalogue-wide status indicates that generated readers may lag. No selected Work is treated as the whole refresh scope.
3. Select **Refresh Catalogue**. The action reconciles its owned output from current source, reports completion or the incomplete step, and clears the refresh-needed state only after verification of the required output.
4. Use the existing Docs Publish action separately when the refreshed local result is ready for Preview and public distribution.

## Delivery Steps

- [ ] **CSR-0 — Readiness:** confirm the current editor and report consumers at a broad owner level, especially the subject picker and generated media dependencies; confirm which outputs can leave Save and which must remain immediate. Record credible failure/recovery and performance risks without freezing a file-by-file design. Gate: approve one coherent Save/Refresh boundary before implementation.
- [ ] **CSR-1 — Save:** keep exact canonical validation and editor/media completion, remove unnecessary consumer generation and full private export from its awaited path, and preserve honest reporting of the inherited image-retry limit. Preserve all Work/Series/Gallery and bulk/delete variants. Select focused existing diagnostics after inspecting coverage and cost; manual editor freshness review is required. Gate: Save remains current across edit, reopen and media cases while deferred readers are clearly identified.
- [ ] **CSR-2 — Refresh:** add the Catalogue service operation and Works editor control/status. Reconcile the complete owned output set and removals, verify the result before marking it current, and preserve saved source on failure. Review report/subject consumers and the separate Publish handoff with focused existing checks and manual UI review. Gate: one Refresh makes the intended Working readers current and reports incomplete output honestly.
- [ ] **CSR-3 — Code review:** review source authority, hidden editor dependencies, redundant full-corpus work, deletion/former-membership handling, media/version ownership, partial writes, private/public separation and compatibility residue. Resolve findings and rerun only affected evidence. Gate: bounded diff and failure semantics accepted.
- [ ] **CSR-4 — Closeout:** update this document to shipped behavior and the [Development Checklist](Development_Checklist.md) if a durable guardrail changed; record measured limits and accepted evidence, then decide whether the delivery checklist can be retired while retaining a durable Save/Refresh owner. Gate: current behavior and remaining risks are clear.

Current record: documentation consolidation only. No service, generated data, media, test, browser, Publish or deployment change has been made for CSR-0–4.
