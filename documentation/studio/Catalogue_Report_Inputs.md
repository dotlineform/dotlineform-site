---
draft: false
doc_id: d-20261010-184615-e471b8
title: Catalogue Report Inputs
added_date: "2026-10-10 18:46:15"
last_updated: "2026-10-10 19:20:05"
summary: Proposed Refresh-owned Catalogue inputs for reports, independent report outputs and live filesystem inspection.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Report Inputs

## Purpose And Status

Catalogue facts consumed by Docs Viewer reports should advance through Studio Refresh. Six reports currently read canonical Catalogue records directly, so a saved Studio edit can appear in a report before the corresponding Working Catalogue output has been refreshed. This can produce conflicting Work titles, memberships, source registrations, links or download references across readers.

The agreed direction is to respect Refresh for Catalogue facts while keeping filesystem inspection live. This document recommends the inputs and changes for each report. The six migrations and new shared projections are proposed; creating this document does not approve or implement them. Work Document Coverage already uses its own private Refresh-owned manifest.

[Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the operation boundary, [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) owns current generated Catalogue contracts, and [Reports](Reports.md) owns current report behavior. This proposal supplements those documents without changing their shipped contracts.

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

The recommended starting point is a small set of private Catalogue aggregates produced from the records already loaded by Refresh:

| Catalogue-owned facts | Minimum content needed by these consumers | Consumers |
| --- | --- | --- |
| Work placement and source registrations | Exact Work ID; title where needed; optional Series ID; declared `media_source_id`, `project_folder`, `project_subfolder` and `project_filename`, preserving absence where valid | Projects, Uncataloged Images, Missing Source Files, Folders Without Works |
| Work resource references | Exact Work ID and title; authored link labels/URLs; exact download filenames | Work Links, Work Downloads |
| Series definitions | Every exact Series ID and title, including definitions with no Works | Projects |

The recommended storage is a new `private/` folder beneath the configured Working generated Catalogue root:

```text
$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/private/
    work-sources.json
    work-resources.json
    series.json
```

`work-sources.json` supplies Work placement and source registrations; `work-resources.json` supplies link and download references; `series.json` supplies Series definitions. Resolve the Catalogue root through [workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json). Refresh owns writes and reports read the saved files. These private inputs stay outside Preview, Publish, the public artifact inventory and the publication queue.

The folder, filenames and grouping are proposed; confirm them and the minimal schemas when implementation starts. Separate link and download aggregates are reasonable if they make field ownership or update selection simpler; a combined resource aggregate avoids duplicated Work identity/title data. Either choice must remain Catalogue-owned and independent of final report rows.

Store portable source declarations, resolving absolute project roots through the existing runtime configuration. Do not add private paths to public Work payloads or put unused fields back into the recently simplified Work/Gallery lookup and member rows.

Validate the generated schema, exact identities and the facts each reader needs. Do not make a report require unrelated canonical Work fields such as year, medium, image dimensions or editor state. Shared producer validation belongs to the projection's owner; reports should not copy the Studio editor's full-record validator. Add header fields only for an actual consumer need, rather than default counts or content hashes.

Work Document Coverage's dedicated manifest remains a valid independent input. Projects must not borrow it, Catalogue Works metadata or Series and Galleries metadata to obtain convenient fields. If membership later becomes a shared Catalogue contract, explicitly promote that contract and migrate its consumers together; reuse is not implicit merely because a report manifest contains the desired information.

## Recommended Changes For The Six Affected Reports

### Projects / Project State (`project_state`)

Current behavior reads canonical Works and Series through `docs_project_state.py`, joining them with live immediate project folders and the separately generated Context management manifest. It uses Work IDs, declared first-level project folders, Work-to-Series membership and Series IDs/titles. Saved Studio changes can therefore precede the Catalogue data used elsewhere in Docs Viewer.

Replace the canonical read with refreshed Work placement facts and Catalogue-owned Series definitions. Retain every Series definition, including empty Series, so relationship diagnostics do not depend on which Series happen to have Works. Keep the live immediate-folder scan, generated Context input, unmatched physical folders, current placement rules and document associations. Changing the source must not silently change how `project_folder` is interpreted across configured media sources; any correction to that behavior is a separate requirement.

### Work Downloads (`work_downloads`)

Current behavior reads canonical Work titles and download filenames through `docs_work_downloads.py` and `docs_work_resources.py`, then scans direct regular files in the configured Working `assets.work_files` family. A newly saved attachment reference can appear as missing before Refresh transfers its staged file into Working.

Read refreshed Work IDs, titles and download filenames from the Catalogue resource projection. Keep the filesystem scan live and confined to the existing Working file family. Preserve exact-filename matching, shared files appearing for each referencing Work, unassigned files, missing-file rows, placeholder exclusions and Finder actions. Do not infer ownership from Work ID prefixes or replace the live scan with a generated list of files.

### Work Links (`work_links`)

Current behavior reads canonical Work IDs/titles and authored link labels/URLs through `docs_work_links.py` and `docs_work_resources.py`. It performs no filesystem scan or destination request, so its entire Catalogue input currently advances on Save rather than Refresh.

Read those same minimal facts from the refreshed Catalogue resource projection. Retain one row per authored link, exact Catalogue document navigation and the existing safe browser URL action. Do not add network link checking or a saved final-report snapshot to this migration.

### Uncataloged Images (`uncataloged_files`)

The registry calls this report Uncataloged Files; its current scope is image files. `docs_uncataloged_files.py` reads canonical primary-source registrations and scans the source folders represented by those registrations. The relevant facts are Work identity, media source, folder, optional subfolder and filename; Work title is not needed.

Read registrations from the refreshed Catalogue source projection, then scan the represented source directories live. Preserve the shared supported-image extension policy, physical file-identity matching and configured path confinement. Keep its represented-folder scope: scanning every source-root descendant would be a separate scope change. Physical existence must never determine whether a registration is included in the generated input.

### Missing Source Files (`missing_source_files`)

Current behavior reads canonical source declarations and Work titles through `docs_missing_source_files.py`, resolves expected paths through configured media roots and checks the current filesystem. Its Studio URL is also used for an editor navigation link; that link is independent of the canonical data read.

Read Work IDs/titles and complete source declarations from the refreshed Catalogue source projection. Keep live source-file existence checks, current physical path-equivalence handling and the editor action. Refresh must retain declared sources even when their files are absent, or the report would lose the very rows it needs to diagnose.

### Folders Without Works (`folders_without_works`)

Current behavior reads canonical primary-source declarations through `docs_folders_without_works.py` and `docs_work_resources.py`, then recursively scans every configured Work media source root. A row means the folder has zero directly registered Works; its descendant Work count is derived separately.

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

## Implementation Recommendation

Start by confirming the neutral projection grouping, minimal fields and owning serializers against these consumers. Then add private Refresh outputs and mutation-owned selections using the existing updates queue, followed by the six reader migrations. Refresh should project selected facts from its already loaded validated Catalogue records; report runs should read those saved facts without generation, reconciliation or canonical fallbacks.

Selection must follow the facts actually changed: Work creation/deletion, titles where consumed, source declarations, resource references, Work Series membership and Series definition/title changes. Capture deletion effects before canonical records are removed, including empty Series. Preserve unrelated output and queues. Changes to year, medium or Gallery membership should not select these projections unless a documented consumer is subsequently added that needs those facts.

Create the initial private inputs through an explicit Catalogue Refresh/maintenance action before cutting over readers. Missing or invalid inputs should fail visibly with the owning Refresh instruction; do not silently read canonical records or generate a replacement during a report run. No compatibility aliases or dual-source fallbacks are needed. Update report descriptions and durable ownership documentation to match the refreshed inputs.

This result does not require changing report columns, scan scopes, navigation, Finder actions, ordinary Docs generation, Search or Publish. It also does not require the separately proposed broader selected-row Refresh optimisation. Keep public JSON contracts compact and leave report inputs private.

## Delivery Steps

The delivery remains proposed. All steps below are outstanding; implementation requires its own approval. The current result is this documented proposal, and the next step is CRI.0. Resolve exact schemas and output grouping during approved implementation rather than expanding readiness into a complete code design.

### CRI.0 — Readiness

- [ ] Confirm the outcome and broad owners: Studio mutations select effects, Catalogue Refresh writes private inputs, and Docs report services consume them alongside their existing document/filesystem inputs.
- [ ] Confirm the six reader migrations form one bounded result and that the other ten reports need no input migration.
- [ ] Identify credible failure risks: incomplete update selection, private data entering publication, lost registrations for missing files, changed scan scope and hidden report dependencies.
- [ ] Confirm the sequence and verification budget, preserving unrelated work and pending Catalogue selections.

Verification budget: bounded read-only source/configuration review; no generation, filesystem inventory or executable test work is needed for readiness.

Gate: confirm readiness and obtain implementation approval before CRI.1. If the result requires new report behavior, a broader Refresh redesign or public payload changes, resolve that scope change before proceeding.

Record: proposed; implementation owners and risks are described above. No runtime or generated changes have been made for this delivery.

### CRI.1 — Private Catalogue Inputs And Refresh Ownership

- [ ] Confirm the minimal projection contracts and implement the proposed `private/work-sources.json`, `private/work-resources.json` and `private/series.json`, or record a justified adjustment to their grouping.
- [ ] Add Catalogue-owned serializers and saved-input readers that validate their own identities and facts without requiring the full canonical Work/editor schema.
- [ ] Integrate generation into the existing selected private Refresh output mechanism, using records already loaded by Refresh.
- [ ] Select outputs from relevant old/new mutation facts, including deletion effects captured before removal, Work reassignment and empty Series definition/title changes.
- [ ] Keep the new inputs outside Preview, public artifact inventory and publication queues; preserve unrelated selections and existing queue failure behavior.
- [ ] Populate the initial saved inputs through an explicit owning Refresh action before switching any report reader. Missing or invalid inputs must require Refresh without a canonical fallback.

Verification budget: changed-owner lint/syntax, scoped mutation/selection review and one explicit initial private projection with its existing production reader diagnostics. Inspect the required output once. This writes the new private inputs and owning Refresh state; it must not introduce Docs/Search builds, media production or publication. Select exact existing diagnostics after inspecting their effects; generation cost remains unknown until the owning path is inspected. New test code requires separate approval.

Gate: all required private inputs are valid, selection covers their consumed facts and publication exclusion is confirmed. Stop if initial population requires a broader reconciliation or if an unrelated queue/output would be changed without an owning reason.

Record: proposed; no schemas, serializers, selectors or initial generated files implemented.

### CRI.2 — Projects Reader Migration

- [ ] Replace canonical Works/Series reads with the private Work placement and Series-definition inputs.
- [ ] Retain the generated Context management manifest and the live immediate project-folder scan.
- [ ] Preserve empty Series definitions, unmatched physical folders, existing placement interpretation, document associations and relationship diagnostics.
- [ ] Retain current service responses and navigation unless an essential input error needs the owning Refresh instruction.

Verification budget: changed-owner lint/syntax and bounded composition/source review. Manual report review covers existing folder/document associations, adoption of a saved Catalogue change only after Refresh and observation of a physical folder change on the next run. No automated browser suite or new fixture is included.

Gate: Projects no longer reads canonical Catalogue records or another report's metadata, and its placement/scan behavior is preserved. A discovered placement correction is separately scoped.

Record: proposed; Projects still uses its current canonical Catalogue reader.

### CRI.3 — Work Links And Downloads Reader Migration

- [ ] Replace canonical Work resource reads with the private Catalogue resource input.
- [ ] Preserve authored link labels/URLs, Work titles and exact document targets without adding destination checks.
- [ ] Keep the Work Downloads direct-file scan live, preserving exact filenames, shared references, unassigned files, missing-file rows and Finder confinement.
- [ ] Preserve current response shapes and the absence of saved final-report snapshots.

Verification budget: changed-owner lint/syntax and scoped reader/matching review. Manual review covers links changing after Catalogue Refresh and a staged download reference appearing with its transferred Working file after Refresh. Physical file changes should still appear on the next report run. Any automated selection must be existing, relevant and documented; test authoring is separately approved.

Gate: neither report reads canonical Works; the download join uses refreshed references and current Working files, and no network-checking or attachment-management behavior has been added.

Record: proposed; both reports still use their current canonical resource reader.

### CRI.4 — Source Filesystem Report Migrations

- [ ] Move Uncataloged Images, Missing Source Files and Folders Without Works to the private Catalogue source-registration input.
- [ ] Preserve absent-file registrations in the generated data and retain each report's existing live filesystem operations.
- [ ] Preserve represented-folder image scanning for Uncataloged Images, exact expected-source checks for Missing Source Files and recursive configured-root folder scanning for Folders Without Works.
- [ ] Preserve physical identity/path-equivalence handling, symlink/root exclusions, missing-file membership semantics, existing failure behavior and local actions.
- [ ] Remove unused canonical-loading paths once their callers have migrated, without introducing compatibility aliases or duplicated validators.

Verification budget: changed-owner lint/syntax and scoped input/path review first. Manual runs cover an existing missing source, an unregistered supported image and a folder with zero direct Work membership, plus adoption of changed registrations only after Refresh. Full filesystem scan cost depends on the configured roots; record the chosen existing run and its expected scope before executing it. Do not add repeated recursive scans or new test scripts as closeout evidence.

Gate: all three reports read refreshed registrations, retain their distinct scan scopes and observe physical changes on the next applicable run. Stop and resolve any requirement to broaden traversal, change identity matching or suppress registrations based on file existence.

Record: proposed; all three reports still use their current canonical source readers.

### CRI.5 — Code Review

- [ ] Review the bounded production/configuration/documentation and private generated delta for ownership drift, report coupling, compatibility residue, duplicated contracts and dead canonical readers.
- [ ] Confirm the six reports have no canonical Catalogue read path or fallback and that their data sources do not depend on another report's output.
- [ ] Review mutation selection, initial-input failure messages and private/public boundaries against the completion concerns below.
- [ ] Resolve findings and rerun only evidence affected by those fixes. Apply the required public runtime projection/site checks if an inventoried shared runtime file was changed.

Verification budget: one bounded review of the implemented change and its selected evidence; no broad test profile or repeated generated audit is automatic.

Gate: material findings are resolved or explicitly scoped, and remaining evidence limits are recorded. Passing lint does not substitute for this ownership review.

Record: proposed; code review awaits implementation.

### CRI.6 — Closeout

- [ ] Confirm all six migrations are complete and record the selected evidence, manual acceptance and any unverified variants without claiming broader coverage.
- [ ] Update [Reports](Reports.md), [Catalogue Indexes And Payloads](Catalogue_Indexes_And_Payloads.md) and [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) where their shipped contracts changed; update report descriptions that still imply direct canonical reads.
- [ ] State any required service restart/reload and confirm the private inputs need no Publish operation.
- [ ] Update this proposal and its Planned Features entry to the actual result, and present a retain-or-retire recommendation for this document and any temporary working notes. Document deletion, commit and push remain explicit actions.

Verification budget: reconcile recorded evidence and perform a bounded durable-document review. Do not repeat builds, scans or tests solely to close the delivery.

Gate: the shipped owners describe the implemented contracts and the user has reviewed the report behavior. Retain an explicit manual-review gate for any unaccepted behavior; do not mark the complete result accepted from diagnostics alone.

Record: proposed; closeout awaits the complete implementation and review.

## Completion Evidence For A Future Delivery

The observable result is that all six reports use refreshed Catalogue facts, continue to observe relevant physical changes on their next run, and have no data dependency on another report's output.

- Confirm a saved Catalogue title, relationship, resource or source-path change remains absent from the consuming report until Catalogue Refresh, then appears after Refresh.
- Confirm adding/removing physical files or folders appears on the next applicable report run without Catalogue Refresh, using the report's existing scan scope.
- Confirm missing generated inputs report a Refresh error without a canonical fallback, and empty Series, missing primary sources, shared downloads and unassigned files retain their existing meaning.
- Review the report loaders and backend readers for direct canonical Catalogue reads and accidental dependencies on report metadata.
- Review private-output selection and publication exclusion, then run proportionate existing lint/syntax/whitespace diagnostics for changed owners. UI behavior remains manual review.

These are acceptance concerns, not an approved test implementation. Review relevant existing coverage before selecting executable checks; any test creation or modification needs its own agreed specification under [Testing](Testing.md) and [Test Contract Discipline](Test_Contract_Discipline.md). No new tests, runtime changes or generated output are part of this documentation request.
