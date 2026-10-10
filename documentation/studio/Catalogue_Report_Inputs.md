---
draft: false
doc_id: d-20261010-184615-e471b8
title: Catalogue Report Inputs
added_date: "2026-10-10 18:46:15"
last_updated: "2026-10-10 20:01:05"
summary: Refresh-owned Catalogue report inputs implemented, reviewed and closed; further verification continues during normal report use.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Report Inputs

## Purpose And Status

Catalogue facts consumed by Docs Viewer reports advance through Studio Refresh. Before this delivery, six reports read canonical Catalogue records directly, allowing saved edits to appear before Working Catalogue output had been refreshed and producing inconsistent Work titles, memberships, source registrations, links or download references across readers.

The user approved implementation through code review on 2026-10-10 after CRI.0 readiness and accepted delivery closeout later that day, with further testing to happen during normal report use. Three shared private inputs are populated and all six reader migrations are implemented and reviewed, retaining live filesystem inspection. CRI.0–CRI.6 is complete; acceptance does not claim that the full manual scenarios were exercised. Work Document Coverage retains its independent private manifest.

[Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the operation boundary, [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) owns generated contracts, and [Reports](Reports.md) owns report behavior and evidence limits. This delivery tracks implementation and acceptance; those durable owners describe the resulting contracts.

## The Refresh Boundary

| Input or action | Owner and timing |
| --- | --- |
| Canonical Catalogue records | Studio Save persists authoring changes and queues their known effects. Reports must not read these records directly. |
| Generated Catalogue facts | Explicit Studio Refresh writes selected Working projections. Reports read the saved result through their local data service. |
| Generated Context/document facts | Their existing Docs Save/Build owner advances them separately. Catalogue Refresh does not rebuild these documents. |
| Physical files and folders | A report run inspects the current configured filesystem where its question requires it. Catalogue Refresh does not replace this inspection. |
| Final report rows | The report joins its supplied inputs and applies its own coverage, matching and presentation rules. Running a report does not perform Catalogue Refresh. |

A report may therefore combine refreshed registrations with files that have changed since Refresh. That is useful: deleting an original image should make Missing Source Files report it on its next run. Saving a different source registration in Studio should change the expected path only after Catalogue Refresh. Each input retains its own explicit owner; this is not a promise that all documents and physical files form one simultaneous snapshot.

“Reads Studio data” needs this ownership distinction. A Studio HTTP route serving saved generated Catalogue JSON respects Refresh. A Docs service opening `studio/data/canonical/catalogue/works.json` bypasses Refresh even though its browser never calls the Studio API. Editor navigation links also do not determine the report's data authority.

## Sharing Generated Data

Reports may share Catalogue-owned generated data. A report should not depend on another report's output: its columns, filters, schema and generation lifecycle could change or disappear for reasons unrelated to the consuming report. A shared projection needs a Catalogue owner and an explicit contract independent of any one report.

The current compact `works/works_index.json` contains only Work IDs and titles. It cannot supply Series membership, source paths, links or downloads. Full Work by-ID payloads contain Series identity, links and downloads, but omit private source declarations. They are suitable for selected Work reads; reading thousands of individual files for every whole-corpus report run adds unnecessary filesystem work. The Series–Gallery index has Series IDs and Gallery associations, without the Series titles or Work memberships needed here.

The implemented inputs are three private Catalogue aggregates produced from the records already loaded by Refresh:

| Catalogue-owned facts | Minimum content needed by these consumers | Consumers |
| --- | --- | --- |
| Work placement and source registrations | Exact Work ID; title where needed; optional Series ID; declared `media_source_id`, `project_folder`, `project_subfolder` and `project_filename`, preserving absence where valid | Projects, Uncataloged Images, Missing Source Files, Folders Without Works |
| Work resource references | Exact Work ID and title; authored link labels/URLs; exact download filenames | Work Links, Work Downloads |
| Series definitions | Every exact Series ID and title, including definitions with no Works | Projects |

Storage is the `private/` folder beneath the configured Working generated Catalogue root:

```text
$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/private/
    work-sources.json
    work-resources.json
    series.json
```

`work-sources.json` supplies Work placement and source registrations; `work-resources.json` supplies link and download references; `series.json` supplies Series definitions. Resolve the Catalogue root through [workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json). Refresh owns writes and reports read the saved files. These private inputs stay outside Preview, Publish, the public artifact inventory and the publication queue.

The proposed folder, filenames and grouping are confirmed. The combined resource aggregate avoids duplicated Work identity/title data; its download input is an array of exact filenames. [Shared Private Report Inputs](Catalogue_Indexes_And_Payloads.md#shared-private-report-inputs) owns the minimal schemas.

Store portable source declarations, resolving absolute project roots through the existing runtime configuration. Do not add private paths to public Work payloads or put unused fields back into the recently simplified Work/Gallery lookup and member rows.

Validate the generated schema, exact identities and the facts each reader needs. Do not make a report require unrelated canonical Work fields such as year, medium, image dimensions or editor state. Shared producer validation belongs to the projection's owner; reports should not copy the Studio editor's full-record validator. Add header fields only for an actual consumer need, rather than default counts or content hashes.

Work Document Coverage's dedicated manifest remains a valid independent input. Projects must not borrow it, Catalogue Works metadata or Series and Galleries metadata to obtain convenient fields. If membership later becomes a shared Catalogue contract, explicitly promote that contract and migrate its consumers together; reuse is not implicit merely because a report manifest contains the desired information.

## Scope Of The Six Reader Migrations

### Projects / Project State (`project_state`)

Projects now reads refreshed Work placement and Series definitions through `docs_project_state.py`, joining them with live immediate project folders and the separately generated Context management manifest. It uses Work IDs, declared first-level project folders, Work-to-Series membership and Series IDs/titles.

Replace the canonical read with refreshed Work placement facts and Catalogue-owned Series definitions. Retain every Series definition, including empty Series, so relationship diagnostics do not depend on which Series happen to have Works. Keep the live immediate-folder scan, generated Context input, unmatched physical folders, current placement rules and document associations. Changing the source must not silently change how `project_folder` is interpreted across configured media sources; any correction to that behavior is a separate requirement.

### Work Downloads (`work_downloads`)

Work Downloads now reads refreshed Work titles and download filenames through `docs_work_downloads.py`, then scans direct regular files in the configured Working `assets.work_files` family. Catalogue Refresh owns adoption of staged attachment references and their Working files.

Read refreshed Work IDs, titles and download filenames from the Catalogue resource projection. Keep the filesystem scan live and confined to the existing Working file family. Preserve exact-filename matching, shared files appearing for each referencing Work, unassigned files, missing-file rows, placeholder exclusions and Finder actions. Do not infer ownership from Work ID prefixes or replace the live scan with a generated list of files.

### Work Links (`work_links`)

Work Links now reads refreshed Work IDs/titles and authored link labels/URLs through `docs_work_links.py`. It performs no filesystem scan or destination request. The former shared canonical resource loader is removed.

Read those same minimal facts from the refreshed Catalogue resource projection. Retain one row per authored link, exact Catalogue document navigation and the existing safe browser URL action. Do not add network link checking or a saved final-report snapshot to this migration.

### Uncataloged Images (`uncataloged_files`)

The registry calls this report Uncataloged Files; its scope is image files. `docs_uncataloged_files.py` now reads refreshed primary-source registrations and scans the source folders represented by them. Work title is not needed by this consumer.

Read registrations from the refreshed Catalogue source projection, then scan the represented source directories live. Preserve the shared supported-image extension policy, physical file-identity matching and configured path confinement. Keep its represented-folder scope: scanning every source-root descendant would be a separate scope change. Physical existence must never determine whether a registration is included in the generated input.

### Missing Source Files (`missing_source_files`)

Missing Source Files now reads refreshed source declarations and Work titles through `docs_missing_source_files.py`, resolves expected paths through configured media roots and checks the current filesystem. Its Studio URL remains an independent editor navigation link.

Read Work IDs/titles and complete source declarations from the refreshed Catalogue source projection. Keep live source-file existence checks, current physical path-equivalence handling and the editor action. Refresh must retain declared sources even when their files are absent, or the report would lose the very rows it needs to diagnose.

### Folders Without Works (`folders_without_works`)

Folders Without Works now reads refreshed primary-source declarations through `docs_folders_without_works.py`, then recursively scans every configured Work media source root. Zero directly registered Works determines rows; descendant Work counts are derived separately.

Use refreshed source registrations for membership counts while retaining the live recursive scan. Preserve empty, hidden and non-image folders, exclusion of symlinks and root containers, physical folder-identity handling, and failure on unreadable roots/folders. A declared Work still counts in an existing folder when its primary image is missing. This report's scan scope differs deliberately from immediate-only Projects and represented-folder Uncataloged Images.

## Recommendations For The Other Reports

The remaining ten registered reports need no Catalogue-input migration for this proposal. Their existing read boundaries remain distinct:

| Report | Current boundary and recommendation |
| --- | --- |
| Catalogue Works (`catalogue_works`) | Reads private Refresh-generated `reports/catalogue-works/metadata.json`, served through Studio. Keep that saved input; serving through Studio is not a canonical read. Other reports should not borrow its metadata. |
| Series and Galleries (`series_galleries`) | Reads private Refresh-generated `reports/series-galleries/metadata.json`. Keep its dedicated association rows; do not use them as a shared Series-definition lookup. |
| Work Document Coverage / Works (`works`) | Reads private Refresh-generated `reports/work-document-coverage/manifest.json` and generated Context metadata. Keep this independent input and join. |
| Docs Broken Links (`docs_broken_links`) | Opens its saved audit; explicit Refresh scans document/source/media inputs. Catalogue token checks already use generated Catalogue readers. Keep live inspection within that report operation. |
| Docs Media (`docs_media`) | Opens saved report metadata; explicit Run/Refresh scans its Docs-owned source and media inputs. Keep those filesystem inspections live when the report runs. |
| Selected Documents (`selected_documents`) | Uses Docs-owned generated document metadata. Keep its existing owner; no live canonical Catalogue input needs replacing. |
| Links (`workspace_links`) | Uses the saved Docs-owned relationship aggregate. This is shared document relationship data, not the output of an unrelated report. Keep its existing build/Refresh owner. |
| Unpublishable (`unpublishable`) | Reads the current Docs-owned publication policy and exact source titles. Keep these explicit live policy/source reads; Studio Refresh does not own them. |
| Reports List (`reports_list`) | Uses Docs-owned report configuration/metadata. Keep its configuration boundary. |
| Docs Collection (`docs_collection`) | Uses the configured collection's generated inventory and by-ID documents. Keep that collection's existing generation owner. |

Report-specific saved audits remain appropriate when persistence is part of that report's own behavior. The restriction concerns other reports using those audits as their upstream data authority.

## Implementation Boundary

Start by confirming the neutral projection grouping, minimal fields and owning serializers against these consumers. Then add private Refresh outputs and mutation-owned selections using the existing updates queue, followed by the six reader migrations. Refresh should project selected facts from its already loaded validated Catalogue records; report runs should read those saved facts without generation, reconciliation or canonical fallbacks.

Selection must follow the facts actually changed: Work creation/deletion, titles where consumed, source declarations, resource references, Work Series membership and Series definition/title changes. Capture deletion effects before canonical records are removed, including empty Series. Preserve unrelated output and queues. Changes to year, medium or Gallery membership should not select these projections unless a documented consumer is subsequently added that needs those facts.

Create the initial private inputs through an explicit Catalogue Refresh/maintenance action before cutting over readers. Missing or invalid inputs should fail visibly with the owning Refresh instruction; do not silently read canonical records or generate a replacement during a report run. No compatibility aliases or dual-source fallbacks are needed. Update report descriptions and durable ownership documentation to match the refreshed inputs.

This result does not require changing report columns, scan scopes, navigation, Finder actions, ordinary Docs generation, Search or Publish. It also does not require the separately proposed broader selected-row Refresh optimisation. Keep public JSON contracts compact and leave report inputs private.

## Delivery Steps

CRI.0–CRI.6 is complete with scoped static/production-input evidence, bounded code review and explicit user closeout acceptance. Further report verification will happen during normal use. No test authoring, filesystem report run, browser automation, Docs/Search build, Publish or Git action has been performed. Normal Refresh advances selected report inputs within the same operation; the private-input maintenance action is for initial setup or explicit repair after any queued Work Refresh is complete.

### CRI.0 — Readiness

- [x] Confirm the outcome and broad owners: Studio mutations select effects, Catalogue Refresh writes private inputs, and Docs report services consume them alongside their existing document/filesystem inputs.
- [x] Confirm the six reader migrations form one bounded result and that the other ten reports need no input migration.
- [x] Identify credible failure risks: incomplete update selection, private data entering publication, lost registrations for missing files, changed scan scope and hidden report dependencies.
- [x] Confirm the sequence and verification budget, preserving unrelated work and pending Catalogue selections.

Verification budget: bounded read-only source/configuration review; no generation, filesystem inventory or executable test work is needed for readiness.

Gate: confirm readiness and obtain implementation approval before CRI.1. If the result requires new report behavior, a broader Refresh redesign or public payload changes, resolve that scope change before proceeding.

Record: readiness complete and implementation through code review approved on 2026-10-10. Source/configuration review confirmed the former six canonical readers, mutation-owned v4 selection/private Refresh outputs, configured Working storage and inventory-limited publication. The other ten report inputs need no migration. No scheduling dependency or public contract change was identified; readiness touched no queues, generated inputs or tests.

The sequence remains private input contracts/selection and explicit initial population, then Projects, resources and source-report migration, code review and manual closeout. Exact minimal schemas remain CRI.1 work. Initial population must be limited to these inputs and preserve unrelated queue selections; stop if its owning action requires broader reconciliation or consumes unrelated work. Review mutation selection for creation/deletion, titles, sources, resources, Work Series reassignment and empty Series definition/title changes. Retain missing-file registrations and each existing scan scope. Verification remains the stated source review, changed-owner diagnostics and single initial projection, with real report behavior left to manual acceptance; new test work needs separate approval.

### CRI.1 — Private Catalogue Inputs And Refresh Ownership

- [x] Confirm the minimal projection contracts and implement the proposed `private/work-sources.json`, `private/work-resources.json` and `private/series.json`, or record a justified adjustment to their grouping.
- [x] Add Catalogue-owned serializers and saved-input readers that validate their own identities and facts without requiring the full canonical Work/editor schema.
- [x] Integrate generation into the existing selected private Refresh output mechanism, using records already loaded by Refresh.
- [x] Select outputs from relevant old/new mutation facts, including deletion effects captured before removal, Work reassignment and empty Series definition/title changes.
- [x] Keep the new inputs outside Preview, public artifact inventory and publication queues; preserve unrelated selections and existing queue failure behavior.
- [x] Populate the initial saved inputs through an explicit owning Refresh action before switching any report reader. Missing or invalid inputs must require Refresh without a canonical fallback.

Verification budget: changed-owner lint/syntax, scoped mutation/selection review and one explicit initial private projection with its existing production reader diagnostics. Inspect the required output once. This writes the new private inputs and owning Refresh state; it must not introduce Docs/Search builds, media production or publication. Select exact existing diagnostics after inspecting their effects; generation cost remains unknown until the owning path is inspected. New test code requires separate approval.

Gate: all required private inputs are valid, selection covers their consumed facts and publication exclusion is confirmed. Stop if initial population requires a broader reconciliation or if an unrelated queue/output would be changed without an owning reason.

Record: implemented. Catalogue-owned serializers/readers, old/new Work selectors and Series definition/title/deletion selections use the v4 shared-output family. Studio rejects `private/`; public inventory/filtering exclude it. Lint/syntax passed for nine changed producer/server files. The explicit `catalogue_json_build.py --write --private-report-inputs` action wrote exactly three files before reader cutover, with no deletions or broader reconciliation. Production readers validated 4,619 Works per Work aggregate and 140 Series, including three links and six download references. Initial generation took about 0.12 seconds locally; this is run evidence, not a benchmark. Both queues were empty on the subsequent strict production-state read. Maintenance preserves unrelated selections/readiness, publication bytes and the full Refresh timestamp by construction; queued/failure variants remain unexercised. Gate passed at the inspected input/selection/publication boundary.

### CRI.2 — Projects Reader Migration

- [x] Replace canonical Works/Series reads with the private Work placement and Series-definition inputs.
- [x] Retain the generated Context management manifest and the live immediate project-folder scan.
- [x] Preserve empty Series definitions, unmatched physical folders, existing placement interpretation, document associations and relationship diagnostics.
- [x] Retain current service responses and navigation unless an essential input error needs the owning Refresh instruction.

Verification budget: changed-owner lint/syntax and bounded composition/source review. Manual report review covers existing folder/document associations, adoption of a saved Catalogue change only after Refresh and observation of a physical folder change on the next run. No automated browser suite or new fixture is included.

Gate: Projects no longer reads canonical Catalogue records or another report's metadata, and its placement/scan behavior is preserved. A discovered placement correction is separately scoped.

Record: implemented. Projects reads saved source/placement and Series maps while retaining its Context manifest, immediate-folder scan, first-level placement, document associations, unmatched folders and response keys. Changed-reader lint/syntax/import diagnostics passed. The input-boundary gate passed; real Projects behavior and Save/Refresh/physical-folder timing remain manual acceptance.

### CRI.3 — Work Links And Downloads Reader Migration

- [x] Replace canonical Work resource reads with the private Catalogue resource input.
- [x] Preserve authored link labels/URLs, Work titles and exact document targets without adding destination checks.
- [x] Keep the Work Downloads direct-file scan live, preserving exact filenames, shared references, unassigned files, missing-file rows and Finder confinement.
- [x] Preserve current response shapes and the absence of saved final-report snapshots.

Verification budget: changed-owner lint/syntax and scoped reader/matching review. Manual review covers links changing after Catalogue Refresh and a staged download reference appearing with its transferred Working file after Refresh. Physical file changes should still appear on the next report run. Any automated selection must be existing, relevant and documented; test authoring is separately approved.

Gate: neither report reads canonical Works; the download join uses refreshed references and current Working files, and no network-checking or attachment-management behavior has been added.

Record: implemented. Work Links/Downloads consume the resource aggregate; the canonical loader is removed. Minimal resource validation belongs to Catalogue; live direct-file matching and Finder confinement remain with Downloads. Changed-reader lint/syntax/import diagnostics and scoped matching review passed. The input-boundary gate passed; staged attachments, physical-file changes and interactions remain manual acceptance.

### CRI.4 — Source Filesystem Report Migrations

- [x] Move Uncataloged Images, Missing Source Files and Folders Without Works to the private Catalogue source-registration input.
- [x] Preserve absent-file registrations in the generated data and retain each report's existing live filesystem operations.
- [x] Preserve represented-folder image scanning for Uncataloged Images, exact expected-source checks for Missing Source Files and recursive configured-root folder scanning for Folders Without Works.
- [x] Preserve physical identity/path-equivalence handling, symlink/root exclusions, missing-file membership semantics, existing failure behavior and local actions.
- [x] Remove unused canonical-loading paths once their callers have migrated, without introducing compatibility aliases or duplicated validators.

Verification budget: changed-owner lint/syntax and scoped input/path review first. Manual runs cover an existing missing source, an unregistered supported image and a folder with zero direct Work membership, plus adoption of changed registrations only after Refresh. Full filesystem scan cost depends on the configured roots; record the chosen existing run and its expected scope before executing it. Do not add repeated recursive scans or new test scripts as closeout evidence.

Gate: all three reports read refreshed registrations, retain their distinct scan scopes and observe physical changes on the next applicable run. Stop and resolve any requirement to broaden traversal, change identity matching or suppress registrations based on file existence.

Record: implemented. All three consume refreshed sources; filesystem operations retain their scope and matching. Projection retains declarations independently of physical existence. Lint/syntax/import diagnostics passed for all six migrated services; registry JSON parses. No filesystem report run occurred. The input-boundary gate passed; real missing-source/image/folder and Refresh/physical-change cases remain manual acceptance. Existing canonical-path fixtures are unreviewed and untouched; [Reports](Reports.md) records the test gaps.

### CRI.5 — Code Review

- [x] Review the bounded production/configuration/documentation and private generated delta for ownership drift, report coupling, compatibility residue, duplicated contracts and dead canonical readers.
- [x] Confirm the six reports have no canonical Catalogue read path or fallback and that their data sources do not depend on another report's output.
- [x] Review mutation selection, initial-input failure messages and private/public boundaries against the completion concerns below.
- [x] Resolve findings and rerun only evidence affected by those fixes. Apply the required public runtime projection/site checks if an inventoried shared runtime file was changed.

Verification budget: one bounded review of the implemented change and its selected evidence; no broad test profile or repeated generated audit is automatic.

Gate: material findings are resolved or explicitly scoped, and remaining evidence limits are recorded. Passing lint does not substitute for this ownership review.

Record: complete on 2026-10-10. Bounded production/configuration/documentation diff review and the existing initial saved-input evidence found no remaining canonical read/fallback or report-output dependency in the six services. Reviewed single/batch/bulk Work and Series member selectors, exact deletion capture, empty Series selection, private/public exclusion, path confinement and unchanged scan/matching owners. Resolved repair guidance for an unselected missing/invalid input and added a maintenance gate requiring queued Work handoff first, preventing staged references from advancing early. Removed the unreachable Projects canonical Series-normalization/issue path; malformed saved identities fail input validation, while unknown exact Series relationships retain row diagnostics. Targeted lint/syntax/import diagnostics passed again for the three review-changed owners. No represented shared/public runtime file changed, so site projection/validation is not required for this delivery. Material findings are resolved at the inspected boundary; real mutation/partial-failure, filesystem and interaction evidence remains manual and unverified.

### CRI.6 — Closeout

- [x] Confirm all six migrations are complete and record the selected evidence, user closeout acceptance and any unverified variants without claiming broader coverage.
- [x] Update [Reports](Reports.md), [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) and [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) where their shipped contracts changed; update report descriptions that still imply direct canonical reads.
- [x] State any required service restart/reload and confirm the private inputs need no Publish operation.
- [x] Update this proposal and its Planned Features entry to the actual result, and present a retain-or-retire recommendation for this document and any temporary working notes. Document deletion, commit and push remain explicit actions.

Verification budget: reconcile recorded evidence and perform a bounded durable-document review. Do not repeat builds, scans or tests solely to close the delivery.

Gate: the shipped owners describe the implemented contracts and the user explicitly accepts closeout with the remaining evidence limits recorded. User acceptance may defer full scenario verification to normal use; diagnostics alone do not establish acceptance.

Record: complete; user accepted closeout on 2026-10-10 and stated that full testing will happen as the reports are used. Real Save/Refresh timing, filesystem changes, staged downloads, interactions and failure variants remain unverified. Durable owners and the six registry descriptions reflect refreshed inputs. Restart Local Studio and the Docs Viewer management service, then reload their pages if the updated code has not yet been loaded. Private inputs require no Publish operation. This status-only closeout reuses CRI.5 review and implementation evidence; additional code review is not applicable because no runtime code changed. Closeout list: retain Planned Features as the delivery parent; retain this completed delivery for recent evidence lookup pending manual archive; lasting contracts belong to Reports, Catalogue Indexes And Payloads, and Catalogue Save And Refresh. No temporary working notes were created, and no document deletion or Git action was performed.

## Completion Evidence

The observable result is that all six reports use refreshed Catalogue facts, continue to observe relevant physical changes on their next run, and have no data dependency on another report's output.

- Confirm a saved Catalogue title, relationship, resource or source-path change remains absent from the consuming report until Catalogue Refresh, then appears after Refresh.
- Confirm adding/removing physical files or folders appears on the next applicable report run without Catalogue Refresh, using the report's existing scan scope.
- Confirm missing generated inputs report a Refresh error without a canonical fallback, and empty Series, missing primary sources, shared downloads and unassigned files retain their existing meaning.
- Review the report loaders and backend readers for direct canonical Catalogue reads and accidental dependencies on report metadata.
- Review private-output selection and publication exclusion, then run proportionate existing lint/syntax/whitespace diagnostics for changed owners. UI behavior remains manual review.

These remain verification concerns for normal report use, not an approved test implementation or an open delivery gate. Existing tests require relevant coverage review before execution; test changes need their own specification under [Testing](Testing.md) and [Test Contract Discipline](Test_Contract_Discipline.md). Runtime changes and initial inputs are implemented, and the user accepted closeout with the recorded evidence limits.
