---
draft: false
doc_id: d-20261020-165930-72e1b4
title: Subject Retirement Delivery
added_date: "2026-10-20 16:59:30"
last_updated: "2026-10-20"
summary: Delivery steps for Projects reference associations, Work Document Coverage retirement and independent document thumbnails with an existing-thumbnail reset.
ui_status: done
parent_id: d-20261020-152027-c9f3a8
---
# Subject Retirement Delivery

Status: complete; the user accepted closeout on 2026-10-20. Implementation, review, source cleanup, thumbnail reset and saved Projects cutover are complete. Manual Projects/Thumb interactions remain unverified in the recorded evidence and continue through normal use. Parent: [Subject Retirement](../Subject_Retirement.md); durable behavior lives in [Reports](../Reports.md), [Media And Asset Handling](../Media_And_Asset_Handling.md) and [Generated Data Contracts](../Generated_Data_Contracts.md). Publish, deployment, commit and push remain separate.

## Requirements

Replace document Subjects with the agreed token-based Projects associations, retire Work Document Coverage and give all four authored collections one independent Thumb action. Reset existing authored thumbnails so the user can recreate them manually. The source Work supplies copied bytes only; no Work ID, relationship or dependency is retained with a document thumbnail.

Python owns configured filesystem reads/writes, generation and publication handoffs. The browser owns Work search/selection, modal state, Projects joins and report presentation. Keep Catalogue Work/Series identities, Catalogue thumbnails, body media, Related Links, draft publication rules and the user's gradual placeholder cleanup outside the change. Projects remains Context-only and folder-based; its all-Series coverage is not expanded.

Ordinary documents in the Index retain SVG icons. They have no existing thumbnail use to migrate and do not gain the Thumb action or join the reset. Generic thumbnail handling in shared code does not establish a requirement to preserve an unused ordinary-document thumbnail feature; remove obsolete field/upload dependencies through their shared owners while preserving ordinary document and image behavior.

## Deliverables

- Projects' existing saved snapshot captures Work/Gallery targets from document JSON and explicit Catalogue relationships, with browser-owned Series/folder placement and no Subject or Links JSON dependency.
- One document-level Thumb menu/modal for Library, Context, Concepts and Moments: Work search, Apply and Delete thumbnail, preserving existing document ownership and `<doc_id>-thumb.webp` naming.
- File-owned thumbnail presence with generated `has_thumbnail`; no authored `thumbnail:` field, token ownership or Source Save thumbnail-upload handling.
- Retirement of Work Document Coverage, its report host, private data/producer and maintenance wiring, plus remaining Subject authoring, declarations and generated projections.
- One agreed reset of existing thumbnails in those four collections, with exact generated/publication follow-through and durable documentation updates.

## Process

Projects opens its saved snapshot and changes only through explicit Run/Refresh. Thumb Apply/Delete complete independently of Source Save and update the affected document's thumbnail state. After the reset, the user manually creates Moments and Context thumbnails; Library and Concepts expose the same action. No automatic thumbnail recreation occurs.

The steps below are one coordinated delivery, not independently released migrations. Adopt the changed readers, producers and live data together without compatibility aliases. Publish, deployment, commit and push remain separate explicit actions.

## Delivery Steps

### 0 — Readiness

- [x] Confirm the broad owners, the implemented snapshot prerequisite, the four collection write boundaries and the remaining Subject/thumbnail consumers with read-only inspection.
- [x] Resolve any affected owner outside the agreed collections before expanding the write scope; check the report-host removal and existing publication handoffs without building an inventory or prototype merely for approval.

Evidence/budget: bounded source/configuration review only, minutes rather than an executable run. Gate: one coherent implementation/cutover is safe; stop for scope changes such as additional collection writes or a replacement all-Series audit.

Record (2026-10-20): confirmed Projects' saved GET/explicit Refresh prerequisite, existing typed document references and Refresh-owned Catalogue inputs; browser placement and Work selection remain frontend decisions. The four named authored collections have configured document-media owners, and Catalogue retains its separate owner. Work Document Coverage has an independently removable private pipeline and maintained report host. Existing exact-target deletion, generated metadata/media-reference and publication handoffs cover the required effects; the cutover must also clear the retired coverage queue selector and project affected shared runtime code. No data inventory, prototype, build, test, service action or live write was performed.

Boundary resolved: ordinary Index documents use SVG icons and the user confirmed they have never had thumbnails. Shared metadata/media helpers' generic thumbnail capability is not evidence of a product feature requiring migration or a second model. Keep the Thumb action and thumbnail reset scoped to Library, Context, Concepts and Moments, preserve ordinary Index icon presentation, and do not add ordinary thumbnail writes or migration. Readiness gate passed with no outstanding scope blocker; implementation remains the next step.

Code distinction: `has_document_thumbnail()` reads the authored thumbnail flag, and ordinary by-ID/committed/Selected/media-reference paths propagate it; Selected's reader even has an ordinary-workspace thumbnail URL branch. This is real but unused ordinary-document thumbnail plumbing, not SVG icon support. Retire those obsolete thumbnail paths rather than preserving them as icons. Keep the separate sidebar/result SVG icon rendering, and retain/adapt shared filename, generated `has_thumbnail` and collection-thumbnail rendering needed by the four supported collections.

### 1 — Projects Reference Associations

- [x] Refresh discovers Context documents from its existing manifest, reads each selected by-ID payload once and gathers distinct `catalogue.references[].target` Work/Gallery identities. Capture the existing Work → Series/folder facts and explicit Series–Gallery pairs in Projects' own snapshot.
- [x] Replace browser Subject placement with Work/Gallery → Series → matching physical-folder placement. Deduplicate each row and retain unique-document counts, unmatched folders, grouping, search, sorting, TSV and exact destinations; remove Subject cues.
- [x] Keep saved opening, refresh time and explicit Refresh semantics. An omitted reference envelope supplies no associations; plain Markdown links, incoming links and generated Related Links do not contribute.

Evidence/budget: focused static checks in step 4 and source review of the two join paths. Gate passed: no Links JSON reads or shared manifest/index extensions. Record: snapshot captures distinct Work/Gallery targets and explicit Series–Gallery pairs; the browser joins them through Series to matching folders, deduplicates row placements and counts unique documents. Grouping, sorting/search/TSV, Finder/document navigation and explicit saved freshness remain. UI interaction is unexercised.

### 2 — Independent Thumb Action

- [x] Add the shared document-level Thumb modal for the four authored collections, showing the current stored thumbnail and reusing existing Work lookup/search. Apply copies the selected Work thumbnail; Delete removes the document copy without a Work selection and is unavailable when none exists. Do not expose this action on Catalogue or ordinary Index documents.
- [x] Keep browser selection and Python persistence separate. Resolve the exact source/destination once, carry the completed copy/removal into affected generated metadata/media references and normal publication effects, and update the mounted document/collection state without broad reloads.
- [x] Make the saved thumbnail asset authoritative and retain generated `has_thumbnail`. Remove the source `thumbnail:` dependency, Create thumb controls and thumbnail-only pending-upload/Source Save paths; leave normal image uploads and tokens intact.
- [x] Remove unused ordinary-document thumbnail projection/rendering branches and retire upload-thumbnail generation helpers when their callers are removed. Retain the shared document-thumbnail filename rule and supported collection metadata/rendering; preserve the separate ordinary Index/result SVG icon paths.

Evidence/budget: step 4's changed-owner diagnostics; manual modal/thumbnail interaction at closeout. Gate passed. Record: Edit → Thumb is shared by the four authored collections and hidden for Index/Catalogue. Apply/Delete updates exact saved by-ID, collection and Selected metadata plus queued artwork effects without Source writes, body rendering or Links generation. Existing queued body media survives; explicit reapply cancels an exact removal. File discovery owns has_thumbnail; tokens and Source Save have no thumbnail output. Failure context records target/phase/completed effects, without rollback. Modal Apply/replace/Delete/reopen remains for manual confirmation.

### 3 — Retire Work Document Coverage And Subject Machinery

- [x] Remove Work Document Coverage's registry/loader/browser module, local endpoint/reader, private producer/output selection and maintenance branches, reviewing actual callers before deleting shared helpers. Do not recreate its all-Series audit in Projects.
- [x] Remove Assign Subject and its remaining document authoring/validation/context/customisation paths, Subject-derived thumbnail fallback and management/public Subject projections. Preserve canonical Catalogue Work IDs, Work-to-Series membership and unrelated collection/media capabilities.
- [x] Remove obsolete runtime aliases/dead paths; inspect references in existing tests without changing tests, fixtures or profiles.

Evidence/budget: bounded call-site/retired-reference inspection and step 4 diagnostics. Gate passed. Record: retired the coverage registry/loader/browser/service/producer/CLI and private selectors, including Coverage-only former/new Series queue endpoints. Retired Subject assignment/context/customisations, source/generated projections, shortcut controls, classifiers, cues and unused image-upload thumbnail production. The old preview_works customisation alias is removed. Canonical Catalogue identity/membership and independent lineage interfaces remain. Legacy tests were inspected for references but left unchanged.

### 4 — Focused Verification And Public Code Projection

- [x] Run changed-path JavaScript/Python lint, Python compilation and relevant read-only import/configuration diagnostics. Select no automatic test suite or browser automation; any test work needs its own agreed specification under [Test Contract Discipline](../Test_Contract_Discipline.md).
- [x] Update the explicit public inventory for runtime removals/status changes where required, run `bin/site-code-update`, inspect the exact tracked projection, then run `bin/site-code-update --check` and `bin/site-validate`. Complete whitespace review.

Evidence/budget: seconds to a few minutes, with lint/bytecode outputs and required tracked runtime projection writes; no network, browser startup, media production or live reset. Gate passed before cutover and repeated only for review fixes. Record: explicit changed-owner lint passed for 35 Python and 23 JavaScript files; changed Python compilation and management/configuration/queue imports passed. Public projection changed four shared files and removed the Subject classifier, with its explicit inventory entry removed; projection check and site validation passed (104 projected files, 71 runtime modules). Whitespace passed. No test code, suite or browser automation was used.

### 5 — Source Cutover And Agreed Thumbnail Reset

- [x] Remove obsolete document Subject/thumbnail declarations through their canonical authored-source owners. Preserve identities, content, dates and draft values; do not convert or delete the user's placeholder documents. Resolve any source-owner scope discovered in readiness before writing it.
- [x] Delete every existing document-owned thumbnail in Library, Context, Concepts and Moments, including manually created ones, through configured owners. Leave Catalogue thumbnails and body images intact; do not regenerate replacements.
- [x] Retire Work Document Coverage's live host/navigation and private generated artifact through their owning operations. Remove only its retired private-output selector from the existing updates queue before adopting the new allowlist, preserving unrelated Work/Series/Gallery and publication selections. Capture the exact required public document/media removals.
- [x] Regenerate affected document/manifest/Selected thumbnail and Subject metadata using exact document selections. Use a complete collection docs-only reconciliation only where the changed generator contract requires it, with media builds skipped. Preserve Search/Recent; do not run a complete Working Build or Catalogue Refresh as incidental cleanup.
- [x] Queue exact finished document/thumbnail effects through the normal handoff, then run Projects Refresh once to adopt its new snapshot contract. Record completed operations, counts and any failure; do not rerun merely to demonstrate idempotence.

Evidence/budget: these are normal delivery writes, not tests. Cost depends on affected sources/thumbnails and required generation; determine the bounded selection during implementation, without benchmarking. Inspect required output once. Gate passed. Record: span-preserving patches removed 12 work_id, 139 folder_path and 39 thumbnail declarations across 151 Context and 38 Moments sources (189 documents), preserving content/identity/dates/draft. The normal Delete owner retired the coverage host and updated ordinary navigation from 20 to 19 documents; its private artifact and ignore-list entry are gone. The updates queue had no retired selector, and unrelated selections were retained. One docs-only complete Context reconciliation rendered 159 documents, updated its manifest and removed the already-orphaned payload; targeted Moments generation rendered/wrote 38 of 59 documents and updated its manifest. Both produced zero warnings/Links changes. The existing publication owner saved 40 exact thumb removals before unlink (two Context, including one orphan, and 38 Moments). Library/Concepts had no affected data. One Projects Refresh at 2026-10-20T17:36:02Z saved 208 folders, 159 documents, 4,618 Works and 139 Series; eight documents contain targets. Read-only output diagnostics confirmed zero stored thumbnails/manifest Subject or thumbnail flags in all four collections and 40 queued removals. An initial maintenance import-path error stopped before reset writes; the corrected owning operation completed once. No media production, Search/Recent rebuild, Catalogue Refresh or Publish occurred.

### 6 — Code Review

- [x] Perform the distinct [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) over the changed operation and reused helpers: normal/empty/failure paths, ownership, repeated reads, scope, validation, obsolete fallbacks, aliases and publication effects.
- [x] Confirm that Projects reads only its snapshot on opening; Thumb persists no Work dependency; the reset touches only agreed owned artifacts; readers/Publish trust completed metadata. Record findings, removals and justified safeguards here, then repeat only evidence affected by fixes.

Evidence/budget: bounded source/diff review, with time proportional to the final change; no new audit framework or automatic suite. Gate passed. Record: distinct review traced Projects empty/unmatched/multiple-target/multiple-folder paths; Thumb initial/copy/replace/delete/failure/queue paths; and normal Source Save/Delete/Build consumers. Review carried completed thumbnail presence from authoring/import into generation without repeated file probes, and removed obsolete Source metadata arguments from body-media extraction, kept thumbnails out of token-owned removal, removed unused coverage endpoint selections and restored unrelated media-list filtering. It retained correction-friendly Source reads, existing JSON parsing, exact request identities, configured path/symlink confinement, safe rendering and the normal queue-before-unlink contract. Work IDs select bytes only and are never persisted. There are no new corpus audits, freshness checks, hashes, read-backs, canonical fallbacks, compatibility aliases or recovery ledgers. Static evidence and the real cleanup/build operations do not exercise modal/browser behavior.

### 7 — Documentation And Closeout

- [x] Transfer shipped behavior to [Reports](../Reports.md), [Media And Asset Handling](../Media_And_Asset_Handling.md), [Generated Data Contracts](../Generated_Data_Contracts.md) and the current Subject/authoring owners as required; keep durable guardrails in Development Checklist. Reconcile this delivery and the parent/Planned Features status.
- [x] Record exact checks and live reset/generation outcomes, runtime restart/reload instructions and remaining omissions. User manual review covers Projects associations/grouping/navigation and Thumb Apply/replace/Delete/reopen across all four collections; do not require deleting a real Work merely to demonstrate copy independence.
- [x] Recommend which proposal/delivery/historical report documents to retain or retire and name their durable destinations. Repository-document deletion, tests, Publish, deployment, commit and push require their own scope/action.

Evidence/budget: bounded documentation/whitespace review, reusing accepted evidence; manual interaction belongs to the user. Closeout accepted on 2026-10-20. Record: durable report, media, generated-data, Source, Catalogue-input/lifecycle and checklist owners describe current behavior; historical Subject/report proposals are marked retired. Restart both local services and force-reload Manage before normal use. Projects association/grouping/navigation, Thumb Apply/replace/Delete/reopen across the four collections, Catalogue/Index exclusion, token independence and retained-list artwork updates remain unverified in the recorded manual evidence. Tests, live Thumb interactions, Publish, deployment, commit and push were not performed by Codex. Closeout adds no new implementation or verification claim.

## Follow-on

Plain Markdown Catalogue links, broader Projects collection coverage, all-Series auditing and alternative thumbnail sources are outside this delivery. Test changes, if needed, require a separate durable specification and approval; existing tests do not define the retirement contract.

## Document Retention Recommendation

Retain this closed delivery and the parent for recent-delivery lookup and source/relationship examples pending manual archive. Reports, Media And Asset Handling, Generated Data Contracts, Source Organisation/Source Editor Endpoints and Catalogue lifecycle/input documents own lasting behavior. Subject Associations is now a concise retirement pointer. The historical Works Report, Catalogue Subject Selection Shortcut, Assign Subject In Source Editor and Subject And Context Thumbnails delivery are eligible for retirement; no repository documents were deleted.
