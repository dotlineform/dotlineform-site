---
draft: false
doc_id: d-20260428-000000-f5ff18
title: Planned Features
added_date: "2026-04-28 00:00:00"
last_updated: "2026-11-17"
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

## Proposed Features

- [Export Book](Export_Book.md) — Compare PDF and EPUB for whole-Book export from the saved Tree and for reading downloaded editions.

- [Portfolio Books](Portfolio_Books.md) — Curate downloadable books from Catalogue, Context, Concepts and Moments, starting with Moments.

- [Mobile Layouts](deliveries/Mobile_Layouts.md) — Review public navigation, reading and media on small screens, including Catalogue and Media View.

- [Site Optimisation](deliveries/Site_Optimisation.md) — Measure public site payloads and loading, including Catalogue and Media View, before choosing improvements.

- [Docs Viewer App Roadmap](Docs_Viewer_App_Roadmap.md) — Proposed standalone Mac/iPad reader progressing to local management through one capability release at a time. Each Swift release aligns with an agreed web behavior/resource baseline; ongoing web additions do not automatically expand it. Reuse the existing reader and native foundation, improve only the responsibility seams needed by the next capability, and treat historical native proposals as background requiring reconciliation. DVA.R1 ordinary reading is the next candidate; workspace/access, release scope and implementation approval remain open.

## Reviews

- [Public Index Search Scopes](Public_Index_Search_Scopes.md) — Complete and accepted locally on 2026-11-17. Keep the delivery pending manual archive. The [Search guide](Docs_Viewer_Search.md) and [Search Index contract](Docs_Search_Index.md) own the current behaviour and files. Deploy Public remains a separate release action.

- [Source Save Media Adoption](Media_And_Asset_Handling.md#source-save-media-adoption) and [Document Delete Media Cleanup](Media_And_Asset_Handling.md#document-delete-media-cleanup) — User-approved, implemented and reviewed on 2026-10-18; awaiting normal-use acceptance after a Docs Viewer service restart and Manage reload. Save copies selected foreign document-owned media and rewrites active references through its existing handoff. Delete removes selected documents' owned folders and thumbnails, including unused files, after saving exact public removals. The agreed workflow saves the destination before deleting the original. Focused Python/JavaScript lint, Python compilation, service imports and whitespace checks passed. No tests, live Save/Delete, Build or Publish ran.

- [Import Media Preparation](Docs_Import_Architecture.md#import-media-preparation) — Implemented and reviewed on 2026-10-18; awaiting normal-use acceptance. Conversion reuses one resolved media owner, prepares inline bytes once and constructs final document-owned plans before materialisation. The distinct redundancy/defensive review removed re-extraction, count audits at materialisation, repeated binding, retargeting, unused media-link helper aliases and raw-source fallback; retained strict authoring sanitization and selected filesystem/storage checks. Review preserved source-derived package image titles and ordinary Review destination resolution. Eight changed Python owners passed lint, compilation and module-import diagnostics; read-only conversion of the reported Brain Structure HTML passed through the CLI and the configured library owner, with one prepared SVG and no warnings. No tests, live import writes, generation or Publish ran. Tests using old helper signatures remain unchanged and require a separately approved migration; no compatibility aliases were added. Restart the Docs Viewer service for manual acceptance.

- [Catalogue Report Inputs](Catalogue_Report_Inputs.md) — Complete; user accepted closeout on 2026-10-10, with further testing during normal report use. Three Catalogue-owned private Refresh inputs are populated, and all six reader migrations are implemented and reviewed, retaining live filesystem scans and independent outputs. Changed-owner diagnostics and initial production-reader validation passed; tests and full real report/mutation/failure scenarios remain unexercised. Retained for recent-delivery/evidence lookup pending manual archive.
- [Public Work JSON Review](Public_Work_JSON_Review.md) — Complete and user-accepted on 2026-10-19. Reference-only Build, live Manage resolution, shared static Publish/Export/Prepare package preparation and public prepared navigation are delivered with unchanged queue rules. Conversion wrote 4,628 Working payloads; normal Publish completed 4,623 eligible units and 40 selected-media effects without removals. Focused diagnostics, distinct source review, runtime projection and site validation passed. Export creation/replacement and two package dry-runs passed; the nerve snapshot has eight files/three media objects. The user accepted the 800px Export correction, confirmed compact Catalogue Related Links styling and requested closeout with remaining checks continuing through normal use. Tests remain unchanged and unrun; commit, push and deployment remain separate explicit actions. Current contracts belong to [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation), [Catalogue Media View](Catalogue_Media_View.md), [Builder](Builder.md#publish-preparation), [Export](Export.md) and [Package Prepare](Package_Prepare.md). The closed delivery and retired handoff are retained pending manual archive. Physical Catalogue JSON distribution is unchanged. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) and [Catalogue Deployment](Catalogue_Deployment.md) own the working incremental lifecycle, including staged media, queued Refresh and Regenerate, and selected publication. [Docs Viewer Runtime](Docs_Viewer_Runtime.md#document-action-context-and-toolbar-placement) owns the action resolver and Catalogue editing restrictions. Aggregate replacement, shared Full Rebuild optimisation and physical Catalogue JSON removal after cutover/consumer review remain separately scoped. The Catalogue Image metadata option/field removal and Working token migration were delivered independently.

## Ad-hoc Deliveries

- [Thumbnail from a document image](Media_And_Asset_Handling.md#assigned-document-thumbnails) — Complete and accepted by the user on 2026-11-14. **Edit → Thumb** can replace the document thumbnail with a rendered raster, SVG or Catalogue image. The implementation review confirmed reuse of the active document mount and thumbnail publication queue, with image decoding and the pixel bound checked before replacement. Focused lint, Python compilation, whitespace, public projection and site validation passed. Acceptance covers the workflow in use. Individual image types, deletion and failure cases were not separately reported.

- [Left-aligned Catalogue image sizes](Semantic_Tokens_Source_Editor_UI.md#catalogue-image) — Implemented and reviewed on 2026-11-12. Build derives thumbnail identity from Work ID and the loaded rendition policy. Working and public resolve the prepared identity through their configured asset bases. Review traced the 50% candidate set, the 33% single primary, the thumbnail's native width and the exact Publish and Export asset selections. A read-only diagnostic using Work `00638` confirmed the three prepared file selections and read the packaged assets, including the larger link target for Export. Lint, Python compilation, whitespace, public projection and site validation passed. The dialog, browser layout and live actions remain manual checks after restarting Docs Viewer and hard reloading.

- [Numeric title search](Docs_Search_Tokenizer.md#query-semantics) — Implemented and reviewed on 2026-11-12. The Working generator and retained title updates share the title-only rule. The browser reads numeric title postings directly and intersects them with the existing text constraints. Review confirmed that numbers in other text fields and components of technical compounds stay outside numeric matching. The Working Search rebuild queued its output for Publish and added 232 bytes of numeric title postings across 156 documents. A read of the generated index confirmed that `10,000` and `10000` both return **10,000**, that `10` does not match it by prefix and that the numeric postings belong only to titles. Focused lint, Python compilation, whitespace, public projection and site validation passed.

- [Index follows the displayed document](Docs_Viewer_Runtime.md#retained-index-views) — Implemented and statically reviewed on 2026-11-12. The sidebar uses the displayed record and loaded Index configuration to mark an exact row or the containing collection. Review traced fresh opens, retained history, loading and errors, and the transition from Search or Recent back to the tree. The former route-supplied selection and separate state were removed. Hidden tracking uses mounted rows and defers ancestor expansion and scrolling until the tree is visible. Focused JavaScript lint, whitespace, public projection and site validation passed. Navigation and tree reveal remain manual checks after hard reload.

- [Image text wrapping](Semantic_Tokens_Source_Editor_UI.md#wrap-body-text) — Implemented for Catalogue and ordinary image tokens on 2026-11-12. The Source modals share placement controls and record both wrapping choices in the existing field. The ordinary image modal uses the wider standard card. Review traced the ordinary figure and the Catalogue reference slot through shared CSS, and confirmed that Image detail still targets the ordinary figure. The reading column determines whether the figure floats, and following headings clear it. Existing media inputs and authoring validation serve both placements. Focused JavaScript and Python lint, Python compilation, whitespace, projection and site validation passed. Browser layout and live Source Save remain manual checks after restarting Docs Viewer and hard reloading.

- [Subject Retirement](Subject_Retirement.md) — Complete; user accepted closeout on 2026-10-20. Projects uses Work/Gallery token references through Series to physical folders, Work Document Coverage is retired, and four authored collections share independent Thumb copies. Reset removed 40 thumbnails and obsolete declarations from 189 documents. Durable owners are Reports, Media And Asset Handling, Generated Data Contracts and Source/Catalogue lifecycle documentation. Retained for recent-delivery lookup pending manual archive; Publish and Git actions remain separate.

Store new standalone delivery documents for bounded work that does not need a separate feature parent under `documentation/studio/deliveries/`. Parent them directly to this document and keep implementation state, decisions and completion gates in the delivery. At closeout, transfer lasting details to the durable owner and review whether the delivery and its link should be retained.

- [Catalogue Documents And Metadata](Catalogue_Documents_And_Metadata.md) — Complete and accepted on 2026-10-07. The refined Entry pilot is accepted and Full reconciliation converted all 4,618 Working Catalogue documents to Entry plus `context`, with no additions, retitles, deletions or warnings. Retained for metadata decisions and recent-work lookup pending manual archive; Publish and Git actions remain separate.
