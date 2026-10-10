---
draft: false
doc_id: d-20260428-000000-f5ff18
title: Planned Features
added_date: "2026-04-28 00:00:00"
last_updated: "2026-10-10 16:57:25"
summary: This explains the delivery model and workflows to implement new repo and application features.
ui_status: planned
parent_id: ""
---
# Planned Features

## Structure

```text
Feature (one short snapshot or parent)
   -> Concept (optional)
   -> Architecture (optional)
   -> Delivery (optional, one or more)
```

| layer | owns | does not own |
| --- | --- | --- |
| feature | one coherent snapshot and, when needed, navigation and internal order for its concept, architecture, and bounded deliveries | app-level scheduling, prerequisite tracking, or a transcript of the discussion that produced it |
| concept | problem, desired capability, lasting purpose, and feature invariants | priority, implementation tracking, or exact code inventories |
| architecture | proposed structure, ownership, extension method, and pressure points | shipped current-state authority |
| delivery | one complete, verifiable outcome | the whole long-term feature vision or a partly complete sequence |
| durable document | shipped behavior, current architecture, extension method, and known weak spots | proposal history |
| maintenance index | curated links to actionable gaps in durable documentation | design, priority, or implementation tracking |

- **durable** means outside this planned features document hierarchy.
- A feature may be half a page and need no children. It may be completed immediately or parked for later. Add concept, architecture, or delivery documents only when separating those responsibilities makes the feature easier to understand or deliver.

## Feature Rule

- If a change is complicated enough to need its own documentation, it is a feature.
- A feature snapshots one coherent result from free-flowing discussion; it does not preserve the whole discussion.
- A feature may be an internal refactor, maintenance improvement, workflow change, or visible capability. Size and visibility do not create different planning levels.
- A genuinely complex feature may have several delivery documents or phases. Each delivery must still be independently complete, and the feature parent owns their navigation and internal order.
- Do not introduce initiatives, epics, enablers, stories, or improvement tiers. The feature boundary is enough.
- Small direct changes that do not need feature documentation continue through the normal development workflow.

Before implementation is safe, a feature may have no delivery document or a clearly **proposed delivery** used to test whether the feature is implementable, worthwhile, and coherently bounded. A proposed delivery is not permission or readiness to start. Promote it to planned only when any dependencies are satisfied and it is safe to implement; mark it active only when work starts.

A useful concept may outlive implementation. It can become the durable feature overview when it still explains why the capability exists, its stable mental model, and the invariants future changes should preserve. Temporary proposed architecture and delivery documents should not survive merely to retain implementation history.

## Delivery Shape

A delivery uses one linear structure whether it needs one implementation step or ten:

**Requirements**
  - a more detailed description of why we are doing this, what the end state is.

**Deliverables**
  - new or change artifacts, so there are no surprises when we are implementing

**Process**
  - describe what the target workflow is, how the user will operate the implementation

**Delivery Steps**
  - X.0 — Readiness
  - X.1…X.n — Implementation
  - X.n+1 — Code Review
  - X.n+2 — Closeout

**Follow-on**
  - requirements and deliverables that surfaced during delivery and were not appropriate to implement immediately, so may be done here or described in subsequent feature or delivery docs.

The complete result states one observable outcome. The requirements boundary says what is and is not part of that result. Put stable reasoning, architecture, examples, and extension discussion in concept or architecture documents rather than repeating them in the delivery document.

Every delivery step has:

- checklist items for its concrete deliverables;
- a **proportional** verification budget when it changes an executable contract;
- an explicit gate describing when to stop and what receives manual review; and
- a **compact** record, updated during implementation, naming status, changed owners, unexpected complexity or deviation, exact completed evidence, and the gate outcome.

Use checkboxes and the record to make partial progress visible. Do not turn checkpoint records into implementation diaries, paste extensive command output, or accumulate repeated descriptions of already accepted contracts.

### Readiness Step

The first step is a concise read-only readiness check. It confirms that the specification is coherent against the current product, names broad authority and credible blast radius, confirms the delivery sequence, and records genuine stop conditions.

Readiness is **not** a file-by-file audit, frozen implementation design, line-count estimate, fixture, prototype, production diff, exact final schema, or complete test plan. If implementation uncertainty requires working code or generated output to resolve, put that work in an explicitly approved implementation step rather than disguising it as readiness.

### Verification Budget

After inspecting the owners for an implementation step, record only the existing evidence justified by that step and its cost. A short note is sufficient for a small selection; use a table when it makes several checks easier to understand:

| contract or credible risk | existing evidence and coverage record | expected cost and side effects | why this evidence is needed |
| --- | --- | --- | --- |
| example changed contract | exact existing selection or source/manual review | setup, runtime, resources, token/diagnosis effort, writes/network, or unknowns | the specific regression it can catch |

Use the table proportionally. Documentation-only or trivial steps may state that no executable evidence is warranted. Do not add a row merely to make the table look complete.

Test creation, updates, refactoring, deletion, fixtures, harnesses, and collection changes are separately specified and approved delivery work. Product delivery approval and a verification-budget row do not authorize them. A small test needs a proportionately small specification; do not build test code before agreeing its purpose, coverage, cost, and acceptance. [Test Contract Discipline](Test_Contract_Discipline.md) owns that specification and its maintained coverage record, which lives under Testing or a durable app/domain owner outside this feature hierarchy. Link it from the delivery.

Evidence outside the accepted budget requires explaining the newly discovered risk before proceeding. No test layer or profile is automatic. Test commands and coverage descriptions belong in the durable test record; the delivery records only the selected command, result, and material omissions. An unapproved test proposal does not hold up an otherwise complete fix unless the user has made it an acceptance requirement. Stop when sufficient evidence is available; rerun only for a relevant change, failure, or unresolved risk.

### Code Review Step

Every material code or config delivery has a distinct code-review step after implementation and its selected evidence. Review the bounded production, test, config, documentation, and generated diff for ownership drift, duplicated contracts, compatibility residue, hidden coupling, dead paths, missing failure behavior, and excessive tests. Record findings and their resolution, then rerun only evidence affected by review changes.

A documentation-only delivery may mark code review not applicable, with the reason, and perform a bounded source/diff review instead. Code review is not replaced by approval of readiness or by a passing test run.

### Closeout Step

Closeout confirms the complete result, updates the durable owner, records remaining omissions or risks, and presents the explicit retain-or-retire recommendation for temporary feature, concept, architecture, delivery, and verification documents. It does not repeat implementation verification without a concrete reason.

## Closeout Shape

During development:

```text
Feature Parent
  -> Concept
  -> Proposed Architecture
  -> Delivery (one or more)
```

After the complete feature ships:

- Complete the durable documentation transfer. New durable documents may need to be created - do not try to compress all information into the closest matching document.
- Present a closeout list covering the feature parent, concept, proposed architecture, deliveries, and any temporary working or verification siblings. For each document, name its durable destination.
- Do not delete any documents without approval.
- A review hold does not need a new lifecycle status. The feature may point to the shipped durable owner while the source documents remain available for comparison or reuse. The feature parent may be kept if immediately useful for subsequent features to refer to.
- When needing to retain the concept, rewrite in current-state language and remove resolved options or proposal history.

Delivery closeout uses evidence proportional to the change. A status-only documentation closeout may need only source review and confirmation that required generated follow-through completed. Rebuilds, generated-record audits, broad test profiles, lint sweeps, and repository-wide diff checks belong only when the changed contract or uncertain generated state gives them a concrete failure to catch.

## Working Rules

- Studio Development guidance in [Development Checklist](Development_Checklist.md) needs to be followed.
- Keep one complete outcome per delivery.
- Let a complex feature contain several deliveries or phases.
- Feature documents assume their required environment exists, and state where possible what this means in practice.
- Split work before starting when a partly finished result would be a plausible stopping point.
- If implementation exposes another useful result, add it to the feature parent rather than silently widening the current delivery.
- Update one durable documentation owner by default. *durable* means outside this Planned parent hierarchy.
- Create a new durable document if a suitable one does not already exist. Do not overload an existing document just because it seems to be the appropriate place.
- Feature documents are **not** durable documents. They enter the explicit closeout list when their routing or decision value is exhausted.
- Close a delivery when the complete result works and its durable owner is current.
- Feature documents should be updated with useful decisions and future direction without becoming long execution diaries.

## Reviews

- [Public Work JSON Review](Public_Work_JSON_Review.md) — Broader Work-payload/presentation and shared rebuild proposals remain separately scoped. Its active [Incremental Updates](deliveries/Incremental_updates.md) delivery implements staged media, mutation-owned queues, queue-only Regenerate and per-Work Publish with a final shared pass. Durable workflow/ownership documentation is current independently of further testing. Focused verification passed; the user confirmed new Work addition and subsequent deletion through to R2 on 2026-10-10 and perceived quicker Publish. Managed-file and other manual variants remain unverified. [Gallery And Series Incremental Updates](deliveries/Gallery_And_Series_Incremental_Updates.md) extends both queues to v4 and is complete and accepted on 2026-10-10 after the user confirmed the Refresh queue handoff; shared Publish and failure variants were not itemised as tested. Removing Catalogue document editing remains a follow-on. Aggregate handoff, baked media, Gallery loading and Media View contract retirement remain open. The Catalogue Image metadata option/field removal and Working token migration were delivered independently.

## Ad-hoc Deliveries

Store new standalone delivery documents for bounded work that does not need a separate feature parent under `documentation/studio/deliveries/`. Parent them directly to this document and keep implementation state, decisions and completion gates in the delivery. At closeout, transfer lasting details to the durable owner and review whether the delivery and its link should be retained.

- [Catalogue Refresh Index Updates](deliveries/Catalogue_Refresh_Index_Updates.md) — Gallery picker count subtitle and stored row count removal implemented on 2026-10-10; focused Working v2 conversion completed and its index is queued for Publish. Modal review remains manual. Broader selected-row Refresh for compact indexes, relationship reports and Gallery member output, remaining field/header decisions and their cutover remain proposed.

- [Source Save And Watcher Retirement Delivery](deliveries/Source_Save_And_Watcher_Retirement_Delivery.md) — Complete; user accepted normal and collection document authoring, Draft and starred changes on 2026-10-08 and reported a much quicker experience. Save awaits exact document/Links generation and fresh display silently; the filesystem watcher is retired. Rare media edits use Rebuild docs and Search. Retained for recent-delivery/evidence lookup pending manual archive alongside the completed polling follow-on.
- [Browser Polling Retirement Delivery](deliveries/Browser_Polling_Retirement_Delivery.md) — Complete; user accepted closeout on 2026-10-08. Recurring Working reads are removed; content-changing actions own exact refreshes, while Draft retains metadata projection. Changed-source lint, whitespace, shared/public projection and site validation passed; acceptance did not itemise individual manual scenarios. External/other-tab changes require explicit rebuild and refresh/reopen. Retained for recent-delivery/evidence lookup pending manual archive.

- [Work Deletion Delivery](deliveries/Work_Deletion_Delivery.md) — Implemented and reviewed; awaiting user manual acceptance. Single and multiple Work deletion share exact-ID intent, one confirmation and a combined canonical Work/membership write. Lint, syntax and import diagnostics passed; tests remain pending separate review and untouched. Restart Local Studio and force-reload the editor for manual review.

- [Rebuild Displayed Document Delivery](deliveries/Rebuild_Displayed_Document_Delivery.md) — Implemented and reviewed; awaiting user manual menu/reload acceptance. Edit doc → Rebuild targets the displayed ordinary or collection document, preserves source dates and omits Search/media production. Direct service builds, lint/syntax and shared forced-reload projection/site validation passed; restart the Docs Viewer service and hard-refresh the local reader.
- [Catalogue Documents And Metadata](Catalogue_Documents_And_Metadata.md) — Complete and accepted on 2026-10-07. The refined Entry pilot is accepted and Full reconciliation converted all 4,618 Working Catalogue documents to Entry plus `context`, with no additions, retitles, deletions or warnings. Retained for metadata decisions and recent-work lookup pending manual archive; Publish and Git actions remain separate.
- [Multiline Summary Delivery](deliveries/Multiline_Summary_Delivery.md) — Complete and accepted on 2026-10-07. Summary supports `|`/`|-`, safe source rewrites and multiline reader/HTML Export output; Package Prepare consistently flattens both fields and expanded Summary content with matching return comparison. Shared runtime projection/site validation and all Working document/collection reconciliation passed; tests, real package/Import/Export actions and Publish were not run by Codex. Retained for consequence lookup pending manual archive.
- [Series Galleries Report Delivery](deliveries/Series_Galleries_Report_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Private Refresh-generated data and a local host display all saved Series–Gallery pairs, empty Series and unassociated Galleries, with sortable columns and Gallery Media View links. Initial metadata and the host are generated; restart Docs Viewer to load the new endpoint, then review sorting and Media View/Back.
- [Work Subfolder Import Delivery](deliveries/Work_Subfolder_Import_Delivery.md) — Complete and accepted on 2026-10-06. New Work imports all direct supported images from a selected subfolder through shared folder confirmation and one awaited creation/media operation; IDs advance above the highest canonical ID and manual import tracking stays with existing reports. Retained for recent-work lookup pending manual archive.
- [Docs Static Image Conversion Delivery](deliveries/Docs_Static_Image_Conversion_Delivery.md) — Complete and accepted on 2026-10-06. Docs-owned 800px-long-edge WebP conversion is delivered; the user confirmed a successful Add image saved at 800px. Retained for recent-work lookup pending manual archive.
- [Broken Links Snapshot Delivery](deliveries/Broken_Links_Snapshot_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Saved scans load on open, Refresh audits and saves, and a progress cursor replaces running messages. Persistence and presentation remain manual review gates.
- [Docs Media Collections Delivery](deliveries/Docs_Media_Collections_Delivery.md) — Complete and accepted on 2026-10-04. Saved ordinary/collection media report excludes thumbnails and refreshes each document owner once; collection selection controls the orphan/total counts. Retained for recent-delivery lookup pending manual archive.
- [Work Editor Media Delivery](deliveries/Work_Editor_Media_Delivery.md) — Complete and accepted on 2026-10-04. Native attachments with automatic Work ID naming and intentional replacement, confirmed same-path image regeneration and Finder links are delivered. Durable Save/authoring documentation is current; retained for recent-work lookup pending manual archive.
- [Docs Native Media Picker Delivery](deliveries/Docs_Native_Media_Picker_Delivery.md) — Complete and accepted on 2026-10-04. Shared filename/folder-open controls, standard toolbar hover style/size and native single-file upload retain Docs-owned naming, decisions, thumbnails and Source Save. Durable intake documentation is current; retained for recent-work lookup pending manual archive.
- [Work Downloads Report Delivery](deliveries/Work_Downloads_Report_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Two-column local reconciliation of canonical Work download references and saved files, with Catalogue document links and Finder reveal actions. Reports is current and the report host has its watcher-generated payload.
- [Work Links And Report Sorting Delivery](deliveries/Work_Links_And_Report_Sorting_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Local Work Links displays authored labels opening in new tabs, and both Work resource reports have sortable columns with retained selection. Reports is current; the new host has its watcher-generated payload and explicit publication exclusion.
- [Folders Without Works Report Delivery](deliveries/Folders_Without_Works_Report_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Recursive local folder inspection across configured Work source roots, including empty/non-image folders and a descendant Work count. The host is generated; restart Docs Viewer to load the new endpoint, then review usefulness and presentation.
- [Subject And Context Thumbnails Delivery](deliveries/Subject_And_Context_Thumbnails_Delivery.md) — Complete and accepted on 2026-10-05. Scalar Subjects, authored-first Context thumbnails, Working reconciliation and runtime projection are delivered; the user confirmed successful Publish and accepted the result. Retained for recent-work lookup pending manual archive.
- [Summary Token Delivery](deliveries/Summary_Token_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Summary expansion, dedicated grey-panel styling, public stylesheet projection and the final Directives **Summary** menu item are delivered; Builder owns expansion and Source Editor Scripts owns insertion. No document/Search build or Publish was performed.
- [Assign Subject In Source Editor](deliveries/Assign_Subject_In_Source_Editor.md) — User approved on 2026-10-10. Implemented as a Source Directives helper over the current unsaved front matter; Apply prepares/replaces that buffer, while Save owns persistence and generation. Open Subject folder also uses the current buffer in Directives, remaining disabled for Work or None. The separate immediate-write path and unused Document Info metadata plumbing/browser contribution are retired. Static checks passed; manual Source/Subject/Finder review remains.
- [Recent Exclusions Delivery](deliveries/Recent_Exclusions_Delivery.md) — Implemented and reviewed; awaiting user manual review and acceptance. Editable exact-target exclusions, local Recent VS Code action and fresh shared Recents during Publish preparation; Source Organisation and Generated Data Contracts own the durable behavior. Initial policy applies on the next full Build or Publish; neither was performed.
