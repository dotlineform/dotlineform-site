---
draft: false
doc_id: d-20260927-164807-83bae2
title: Subject Associations Retirement - Delivery
added_date: "2026-09-27 16:48:07"
last_updated: "2026-09-27 17:37:42"
summary: Retire subject association files and the Catalogue document collection; render Catalogue list and Work detail reports directly from Studio generated JSON while retaining Works subjects in management metadata.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Subject Associations Retirement - Delivery

## Current And Next State

Proposed delivery under [Planned Features](Planned_Features.md). The agreed target removes `subject-associations.json` from every collection, uses management manifests for the remaining document-subject reports, and retires the Catalogue document collection entirely. The existing Catalogue report lists Works; selecting a Work opens a detail report that formats its data and image directly from Studio's existing generated Work JSON. No per-Work Markdown, document JSON or rendered HTML is required. Appearance and interaction remain as they are now. This document specifies the delivery; implementation has not started. The next step is read-only readiness and agreement of the implementation and verification boundary.

[Subject Associations](data/subject-associations.md) records the current data products, generation/publication rules and consumers. The action table below adapts its UI Action Map to the agreed target and adds Catalogue list browsing, Work Document Coverage and the adjacent Studio Work Save boundary. Keep that inventory in current-state language until implementation ships.

## Requirements

Deliver one observable outcome: Catalogue browsing uses Studio's existing generated Work records without a Catalogue document collection, and remaining document-subject reports use their management manifests without any `subject-associations.json` file. Existing visible report membership, subject cues and navigation are preserved.

- Remove association-file generation, readers, validation, publication handling and existing generated artifacts from all configured collections. Do not replace them with another lookup file initially.
- Keep canonical Works subject declarations in Markdown front matter: `work_id`, `series_id` or `folder_path`, with their existing validation and assignment rules. Retain normalized `authoring_subject` in the Works management manifest, including valid, none, malformed and conflicting states. This supports list icons, subject display, assignment context, report joins and grouping without a separate reverse index.
- Retire the Catalogue collection registration, per-Work Markdown/front matter, per-Work `doc_id` addressing, management/reader document manifests and by-ID document payloads. Preserve the ordinary Catalogue report host (`d-20260916-161504-f8c947`) and its place in the document tree, replacing its collection-backed report with the direct Work reader. The exact `work_id` in Studio's canonical and generated Work records owns entry identity.
- Use the existing Studio-generated Work inventory for the Catalogue list and the existing exact Work JSON for its detail report. The configured Working artifacts are currently `working/generated/catalogue/works/works_index.json` and `working/generated/catalogue/works/index/<work_id>.json`. Read those files through their owning Catalogue readers; do not copy them into a Docs collection, create a merged shadow payload or persist rendered HTML. Public readers use the existing prepared/public Catalogue data owner.
- Render the Work image and formatted descriptive data in the browser using the existing Catalogue presentation components where suitable. Preserve the current list/detail appearance, image behavior, Back behavior and list return state. The detail report is a view of a Work, not another source document or per-Work report-host document.
- Build in-memory subject groupings from management rows where document reports need them. Several Works documents may share one subject. Catalogue Works and the Works Subject column navigate directly to the Catalogue detail report with an exact Work-ID target; there is no Work-to-document mapping or missing-document check. Missing or invalid generated Work data fails through the existing Catalogue reader without a document-source fallback.
- Compose remaining document navigation from immutable document IDs and configured hosts, and Catalogue navigation from its ordinary report host plus exact `work_id`, through the owning route helpers. Persisted association `locations` and `access` wrappers are unnecessary. Keep Manage/public routing separate. Inspect existing Catalogue-subdocument links, bookmarks and selected-document entries, then explicitly convert or retire their old document targets as part of the cutover; do not leave compatibility aliases or silently infer Work identity.
- Remove association-only `subject_generation` receipts and cross-file matching gates. Update strict manifest readers and Project State input validation accordingly. Preserve Project State's own report-generation behavior through its report owner, without adding replacement manifests, freshness scans or synchronization receipts.
- Preserve complete and targeted builds for remaining collections. A targeted build merges selected rows with saved management metadata and leaves unselected document membership and subjects intact; it must not reopen every source to recreate a discarded reverse index. Catalogue Work output belongs solely to its existing Studio generator and Save/regeneration lifecycle, not Docs Build or the Markdown watcher.
- Preserve remaining documents' Working draft coverage and publication eligibility. Their management manifests remain private and excluded from Preview/public distribution. Publish prepares existing Catalogue JSON through its configured artifact inventory, without building or distributing a Catalogue document collection or association files. Resolve any live Catalogue per-document readiness/selection state explicitly at cutover; it must not become a second Work identity or hidden content authority.
- Preserve other collections' declared source fields and their existing supported management metadata. Their subject projection must no longer be enabled merely because an old association file exists. Ordinary documents do not acquire Works-specific subject behavior.

The delivery does not implement a unified Related Links model, introduce subject-derived document relationship edges, change token grammar, remove Works' source subject fields, change Works subject-assignment availability, redesign report presentation or add a replacement `work-docs.json`. Works subject fields can feed existing or future token-insertion choices directly; this does not require another JSON product. Canonical Work editing remains in Studio. Other collection registrations, media ownership, package workflows and Search policy retain their existing owners; obsolete Catalogue document references within those boundaries must be reconciled explicitly.

## Deliverables

- Collection builder and subject helpers that project required management/reader metadata without association files or their receipts.
- A Catalogue list report and Work detail report over existing Studio-generated Work JSON, with exact Work-ID navigation shared by Catalogue Works and the Working Works Subject column. Remove the Work-to-document link reader and Catalogue collection list adapter.
- Project State grouping and document navigation derived from the Works management manifest, plus updated strict manifest handling in Work Document Coverage.
- Removal of the retired generated-artifact read allowance, Preview association validation and distribution exclusion branch. Current consumer owners are linked in [Subject Associations](data/subject-associations.md#active-consumer-owners); generated-read, snapshot and distribution owners remain responsible for their own boundaries.
- Removal of Catalogue document Regenerate, source templates, collection-specific code/configuration and obsolete browser/public collection registration. Retain Studio's Work generator, canonical Work data, generated Catalogue artifacts, media and the ordinary report host. Identify owned collection folders and old document-target references before cleanup; [Source Organisation](Source_Organisation.md#collection-deliveries) owns the retirement boundary.
- Explicit cleanup of Catalogue collection source/generated/Preview/public document output and stale association files beneath remaining configured owners. If cleanup changes a completed Preview snapshot, invalidate its completion receipt; a subsequent separately authorized Publish prepares a fresh complete snapshot. Delete only the specifically retired source/generated products; preserve unrelated source, generated Catalogue JSON and shared media. Do not add backup trees or compatibility aliases.
- Updated durable data documentation describing remaining manifest ownership, direct Catalogue Work views, action/freshness rules and report requirements. Historical observations remain identified as historical.

## Process And UI Action Changes

The Catalogue list looks and behaves as it does now. Selecting a Work opens the formatted Work detail report; Back restores the list context. Both views read existing Studio-generated Catalogue data, and the browser creates the presentation without persisting HTML. Studio Save updates that same data through its existing producer; no Catalogue document Regenerate/Build step follows.

For remaining document collections, subject changes write canonical source and collection builds maintain management/reader manifests. Reports derive their required groupings and icons from those rows. Document links use exact document identities and configured hosts; Work links target the Catalogue detail report by Work ID. There is no lookup-generation or repair action.

| UI Action | Current Data Path | Target Data Path And Simplification | Completion Or Freshness Boundary |
| --- | --- | --- | --- |
| Assign Subject / Change Subject, including clearing it | Writes the configured front-matter field group and rebuilds management metadata plus the reverse index. | Keep the source write and normalized management subject update; remove the association write and receipt. Assignment eligibility and the current non-empty Folder restriction are unchanged. | The management operation awaits its existing source-write and collection-build follow-through. |
| Open Source and edit canonical Markdown | A subject change updates management rows and can add, replace or remove associations. | Preserve canonical fields; the watcher updates document and manifest projections without an association file. | Watcher generation remains independent after the file changes. |
| Source Editor Save | Saves body and editable Title/Summary while preserving subject fields; subsequent generation may rewrite the association product. | Keep Save and field preservation; generation updates the existing manifests only. Save does not become a subject-assignment action. | Save completes at canonical persistence; watcher generation remains independent. |
| Working document Build or collection document rebuild | Normalizes subjects, writes the management manifest and recomputes a reverse index, including reconstruction after targeted merges. | Project required fields directly into manifests. Full builds reconcile the owner; targeted builds merge selected rows without a second aggregate product or receipt. | Successful Build owns its generated result; preserve unselected rows during targeted builds. |
| Catalogue document Regenerate | Reads Studio-generated Work JSON, writes per-Work Markdown tokens and rebuilds document manifests/payloads and associations. | Remove this action and its entire document-source/build pipeline. The list/detail reports use the existing Work generator's output directly. | Studio Save or the owning Catalogue data regeneration updates the reader product; no Docs rebuild follows. |
| Document create, import or delete within a collection | Its collection rebuild can add/remove subject-bearing document rows and reverse-index entries. | Reconcile manifest membership and subjects through the existing source operation. Preserve document-delete recovery and exact ownership; no separate index needs reconciliation. | The source operation's existing collection build owns the required follow-through. |
| Publish | Builds private associations and Catalogue document output in temporary Preview storage; distribution excludes associations but copies the Catalogue document collection. | Generate neither association files nor a Catalogue document collection. Prepare/distribute existing Catalogue JSON through its current inventory and publish the ordinary report host/runtime. Private management manifests stay excluded. | One awaited Publish through the existing owners. No live Working rebuild, Search rebuild or additional confirmation is introduced. |
| Open Catalogue report | Loads the Catalogue collection manifest and presents its generated document rows. | Read the existing generated Work inventory and present the same Work list. The report no longer declares or loads a document collection. | Required Catalogue data loads block readiness; no Docs collection manifest or lookup read. |
| Select a Work in Catalogue / return to list | Loads `<doc_id>.json` and displays the built token HTML, then returns through collection navigation. | Open a Work detail report using exact `work_id`, read its existing Studio JSON and format the image/data in the browser. Preserve Back and list return state; persist no rendered HTML. | The exact Work read completes before detail readiness; navigation writes no generated data. |
| Open Catalogue Works | Reads Catalogue associations alongside private Work/Series report metadata and builds Work ID/title links. | Keep private report metadata; compose direct Work detail report links from each exact Work ID. Remove the association/manifest mapping read entirely. | Existing metadata read blocks readiness; no additional document-link data load. |
| Open Working Works collection | Subject display/icons already come from management metadata; Catalogue associations supply Work Subject navigation. | Keep Works subject rows and icon selection. Compose direct Work detail report links from their exact Work IDs; Series Media View and Folder actions retain their owners. | Existing subject-contribution loading boundary; no Catalogue document mapping or association-file read. |
| Open Work Document Coverage | Joins Works management subjects with canonical Work/Series lookup data; its strict manifest validator requires `subject_generation`. | Keep the subject joins and coverage behavior, but accept the revised manifest without an association receipt. No reverse index or separate icon lookup is needed. | Existing report read/readiness boundary; the report does not build or repair inputs. |
| Project State Run/Refresh | Joins Works associations with a matching management manifest, then uses subjects to place documents against project folders and Catalogue data. Associations also supply document URLs and subject cues. | Read one Works management manifest, derive subject groups in memory and compose exact document links. Preserve Folder/Work/Series placement, shared-subject membership, diagnostics and icons. Remove the duplicate membership and generation-receipt join. | Run/Refresh returns the assembled report; it does not rebuild document inputs. Retain the existing folder/Catalogue reads. |
| Follow a document link, Work link or open a Series gallery | Uses an exact document/association destination or the separate Media View owner. | Follow an exact remaining document target, direct Catalogue Work report target or the same Media View action. Reconcile retired Catalogue-subdoc URLs explicitly. No new subject-derived Related Links are created. | Navigation only; no generated-data writes. |
| Studio Work Save | Updates generated Work JSON and private Catalogue Works metadata; separately generated Catalogue documents can remain stale until Regenerate. | Retain Studio's single producer. Catalogue list/detail views read its existing generated output, so the independent document refresh step disappears. | Existing Studio Save completion/cache-refresh boundary; no Catalogue Markdown watcher or Docs rebuild. |
| Catalogue per-Work document authoring and flags | Entries carry ordinary collection document identities, source and readiness/selection metadata despite their generated content. | Retire the per-Work document action/flag paths with the collection. Keep canonical Work editing in Studio and ordinary host-document actions; explicitly reconcile any saved old targets. | Retirement is an owned delivery cutover, not a generic collection-delete UI action. |

## Delivery Steps

### SA-0 — Readiness

- [ ] Confirm the requirements against the current collection build, report and navigation owners, including the strict Work Document Coverage and Project State readers.
- [ ] Confirm the existing Work inventory/record payloads can supply the Catalogue list and formatted detail view without persisted HTML or another generated representation.
- [ ] Confirm exact Work-ID report navigation, remaining Works subject metadata, Manage/public data ownership and the Catalogue report-host identity.
- [ ] Identify old Catalogue document targets and any per-entry readiness/selection state requiring explicit conversion or retirement; do not preserve a collection solely for those references.
- [ ] Identify credible stop conditions: loss of report membership/navigation, a second Work output producer, accidental public exposure of private report data, or cleanup outside the retired owner's boundary.
- [ ] Agree the implementation slice and a proportionate verification budget. Test/fixture/harness changes require their own specification and approval under [Test Contract Discipline](Test_Contract_Discipline.md).

Verification budget: read-only owner inspection and bounded document review. No executable tests, prototypes, builds, workspace cleanup or publication in readiness.

Record: proposed; current consumers and action dependencies have been identified for this specification. Readiness is not yet completed.

Gate: accept readiness and authorize implementation before production or generated-output changes.

### SA-1 — Implement Direct Catalogue Views And Retire Redundant Products

- [ ] Build Catalogue list/detail reports over existing Studio-generated JSON with Work-ID navigation and preserved presentation/return behavior. Preserve the ordinary host identity; generate no HTML or extra Work payload.
- [ ] Move Catalogue Works and Works Subject navigation to exact Work report targets and remove their mapping reader.
- [ ] Update remaining collection metadata projection and full/targeted builds; retain Works source subject normalization and migrate Project State/Work Document Coverage with the manifest receipt removal.
- [ ] Retire Catalogue collection registration, document Regenerate/templates, document-specific adapters and per-Work authoring integration. Reconcile old source links and saved targets through exact known identities, without aliases.
- [ ] Remove association generation, helpers with no remaining owner, read allowances, snapshot validation and distribution handling. No compatibility reader or fallback remains.
- [ ] Reconcile affected Working outputs through the owning complete collection Build where the global builder contract changed, skipping media builds when only document outputs are in scope. Do not rebuild Search merely to finish this delivery.
- [ ] Remove owned Catalogue document products and remaining obsolete association artifacts; preserve generated Studio Catalogue data and media. Record any Preview receipt invalidation. Publish, distribution, commit and push require their own explicit authorization.
- [ ] Update [Subject Associations](data/subject-associations.md) to the shipped model and inspect affected runtime/site projections through the existing inventory when represented public code changes.

Verification budget: select changed-file lint, service/module/config diagnostics and proportionate existing generated-output inspection after the affected owners are known. Record exact commands, cost and write effects before a non-trivial run. Focus on exact Work reads/routes, single-producer ownership, full/targeted metadata preservation for remaining collections, report grouping/navigation, absence of retired collection/association products and public/private isolation. Existing tests must have inspected coverage before reliance; test authoring, retargeting, deletion or fixture changes are not authorized by this document. Catalogue appearance, image formatting, Back and preserved list state remain manual review. Do not run a real Publish or broad suites solely for evidence.

Record: not started; no implementation commands or generated-output changes authorized by document creation.

Gate: the whole consumer/producer cutover and owned cleanup are reviewable, with selected evidence recorded and no fallback to the retired file. Present manual review of Catalogue, Catalogue Works, Works Subject navigation, Work Document Coverage and Project State, plus any separately authorized site-preview review.

### SA-2 — Code Review

- [ ] Review the bounded code/config/generated/documentation delta for duplicate Work payloads, persisted HTML, identity inference, old Catalogue document addressing, stale receipt requirements, dead loaders/helpers and accidental public exposure.
- [ ] Check targeted-build preservation and owner-confined cleanup; resolve findings within the agreed slice.
- [ ] Rerun only evidence affected by a review correction.

Verification budget: bounded source/diff and selected output review; further executable evidence requires a concrete unresolved risk.

Record: not started.

Gate: no unresolved findings in the delivered boundary; material evidence limits and manual-review outcomes are explicit.

### SA-3 — Closeout

- [ ] Record user acceptance of preserved report behavior and navigation, plus the exact completed verification and remaining separately scoped work.
- [ ] Transfer shipped behavior to the durable data owner and record Working/Preview artifact state and any outstanding authorized publication step.
- [ ] Present this delivery's retain-or-retire recommendation and durable destination; do not delete it without approval.

Verification budget: use accepted implementation/review evidence; no automatic rebuild or repeat suite.

Record: not started.

Gate: Catalogue uses existing Studio JSON without a document collection or persisted HTML, all association files are retired, and durable documentation describes current behavior. Historical tests still asserting the old products are identified as separately scoped test work, not retained production contracts.

## Follow-on

A compact subject lookup for remaining document reports is deferred unless measured payload or processing cost justifies another projection. Catalogue requires no Work-to-document lookup. Unified Related Links presentation, subject-derived relationship edges and semantic-token action simplification belong to later deliveries after their current data/action inventories are understood.
