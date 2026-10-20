---
draft: false
doc_id: d-20261020-165930-72e1b4
title: Subject Retirement Delivery
added_date: "2026-10-20 16:59:30"
last_updated: "2026-10-20"
summary: Delivery steps for Projects reference associations, Work Document Coverage retirement and independent document thumbnails with an existing-thumbnail reset.
ui_status: planned
parent_id: d-20261020-152027-c9f3a8
---
# Subject Retirement Delivery

Status: readiness complete; planned and ready for implementation. Implementation has not started and was not part of the readiness request. Parent: [Subject Retirement](../Subject_Retirement.md), which owns the agreed requirements, reference examples and exclusions. The [Projects Metadata Snapshot](Projects_Metadata_Snapshot.md) first delivery is already implemented.

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

- [ ] Refresh discovers Context documents from its existing manifest, reads each selected by-ID payload once and gathers distinct `catalogue.references[].target` Work/Gallery identities. Capture the existing Work → Series/folder facts and explicit Series–Gallery pairs in Projects' own snapshot.
- [ ] Replace browser Subject placement with Work/Gallery → Series → matching physical-folder placement. Deduplicate each row and retain unique-document counts, unmatched folders, grouping, search, sorting, TSV and exact destinations; remove Subject cues.
- [ ] Keep saved opening, refresh time and explicit Refresh semantics. An omitted reference envelope supplies no associations; plain Markdown links, incoming links and generated Related Links do not contribute.

Evidence/budget: focused static checks in step 4 and source review of the two join paths. Gate: no Links JSON reads or shared manifest/index extensions; browser controls remain for user manual review. Record: not started.

### 2 — Independent Thumb Action

- [ ] Add the shared document-level Thumb modal for the four authored collections, showing the current stored thumbnail and reusing existing Work lookup/search. Apply copies the selected Work thumbnail; Delete removes the document copy without a Work selection and is unavailable when none exists. Do not expose this action on Catalogue or ordinary Index documents.
- [ ] Keep browser selection and Python persistence separate. Resolve the exact source/destination once, carry the completed copy/removal into affected generated metadata/media references and normal publication effects, and update the mounted document/collection state without broad reloads.
- [ ] Make the saved thumbnail asset authoritative and retain generated `has_thumbnail`. Remove the source `thumbnail:` dependency, Create thumb controls and thumbnail-only pending-upload/Source Save paths; leave normal image uploads and tokens intact.
- [ ] Remove unused ordinary-document thumbnail projection/rendering branches and retire upload-thumbnail generation helpers when their callers are removed. Retain the shared document-thumbnail filename rule and supported collection metadata/rendering; preserve the separate ordinary Index/result SVG icon paths.

Evidence/budget: step 4's changed-owner diagnostics; manual modal/thumbnail interaction at closeout. Gate: no saved Work ID or dependency, no token/source-buffer coupling, no new relationship and no Catalogue-media mutation. Record: not started.

### 3 — Retire Work Document Coverage And Subject Machinery

- [ ] Remove Work Document Coverage's registry/loader/browser module, local endpoint/reader, private producer/output selection and maintenance branches, reviewing actual callers before deleting shared helpers. Do not recreate its all-Series audit in Projects.
- [ ] Remove Assign Subject and its remaining document authoring/validation/context/customisation paths, Subject-derived thumbnail fallback and management/public Subject projections. Preserve canonical Catalogue Work IDs, Work-to-Series membership and unrelated collection/media capabilities.
- [ ] Remove obsolete runtime aliases/dead paths; inspect references in existing tests without changing tests, fixtures or profiles.

Evidence/budget: bounded call-site/retired-reference inspection and step 4 diagnostics. Gate: Projects and Thumb are the replacement consumers; retire the live report host and old data in the coordinated cutover, without leaving an executable retired report block. Record: not started.

### 4 — Focused Verification And Public Code Projection

- [ ] Run changed-path JavaScript/Python lint, Python compilation and relevant read-only import/configuration diagnostics. Select no automatic test suite or browser automation; any test work needs its own agreed specification under [Test Contract Discipline](../Test_Contract_Discipline.md).
- [ ] Update the explicit public inventory for runtime removals/status changes where required, run `bin/site-code-update`, inspect the exact tracked projection, then run `bin/site-code-update --check` and `bin/site-validate`. Complete whitespace review.

Evidence/budget: seconds to a few minutes, with lint/bytecode outputs and required tracked runtime projection writes; no network, browser startup, media production or live reset. Gate: the selected static evidence passes before cutover; it is not browser or lifecycle acceptance. Record: not started.

### 5 — Source Cutover And Agreed Thumbnail Reset

- [ ] Remove obsolete document Subject/thumbnail declarations through their canonical authored-source owners. Preserve identities, content, dates and draft values; do not convert or delete the user's placeholder documents. Resolve any source-owner scope discovered in readiness before writing it.
- [ ] Delete every existing document-owned thumbnail in Library, Context, Concepts and Moments, including manually created ones, through configured owners. Leave Catalogue thumbnails and body images intact; do not regenerate replacements.
- [ ] Retire Work Document Coverage's live host/navigation and private generated artifact through their owning operations. Remove only its retired private-output selector from the existing updates queue before adopting the new allowlist, preserving unrelated Work/Series/Gallery and publication selections. Capture the exact required public document/media removals.
- [ ] Regenerate affected document/manifest/Selected thumbnail and Subject metadata using exact document selections. Use a complete collection docs-only reconciliation only where the changed generator contract requires it, with media builds skipped. Preserve Search/Recent; do not run a complete Working Build or Catalogue Refresh as incidental cleanup.
- [ ] Queue exact finished document/thumbnail effects through the normal handoff, then run Projects Refresh once to adopt its new snapshot contract. Record completed operations, counts and any failure; do not rerun merely to demonstrate idempotence.

Evidence/budget: these are normal delivery writes, not tests. Cost depends on affected sources/thumbnails and required generation; determine the bounded selection during implementation, without benchmarking. Inspect required output once. Gate: the authored collections start without thumbnails, retired data has no live consumer, unrelated assets/queues are preserved and public removals await ordinary Publish. Record: not started.

### 6 — Code Review

- [ ] Perform the distinct [Redundancy And Defensive Behavior Review](../Development_Checklist.md#redundancy-and-defensive-behavior-review) over the changed operation and reused helpers: normal/empty/failure paths, ownership, repeated reads, scope, validation, obsolete fallbacks, aliases and publication effects.
- [ ] Confirm that Projects reads only its snapshot on opening; Thumb persists no Work dependency; the reset touches only agreed owned artifacts; readers/Publish trust completed metadata. Record findings, removals and justified safeguards here, then repeat only evidence affected by fixes.

Evidence/budget: bounded source/diff review, with time proportional to the final change; no new audit framework or automatic suite. Gate: resolve material findings before closeout and state the limits of static/live-operation evidence. Record: not started.

### 7 — Documentation And Closeout

- [ ] Transfer shipped behavior to [Reports](../Reports.md), [Media And Asset Handling](../Media_And_Asset_Handling.md), [Generated Data Contracts](../Generated_Data_Contracts.md) and the current Subject/authoring owners as required; keep durable guardrails in Development Checklist. Reconcile this delivery and the parent/Planned Features status.
- [ ] Record exact checks and live reset/generation outcomes, runtime restart/reload instructions and remaining omissions. User manual review covers Projects associations/grouping/navigation and Thumb Apply/replace/Delete/reopen across all four collections; do not require deleting a real Work merely to demonstrate copy independence.
- [ ] Recommend which proposal/delivery/historical report documents to retain or retire and name their durable destinations. Repository-document deletion, tests, Publish, deployment, commit and push require their own scope/action.

Evidence/budget: bounded documentation/whitespace review, reusing accepted evidence; manual interaction belongs to the user. Gate: implemented scope and data cutover are complete, durable owners are current and manual acceptance is accurately recorded. Record: not started.

## Follow-on

Plain Markdown Catalogue links, broader Projects collection coverage, all-Series auditing and alternative thumbnail sources are outside this delivery. Test changes, if needed, require a separate durable specification and approval; existing tests do not define the retirement contract.
