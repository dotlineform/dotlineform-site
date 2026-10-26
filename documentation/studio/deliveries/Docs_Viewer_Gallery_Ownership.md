---
draft: false
doc_id: d-20261026-212105-3df12a
title: Docs Viewer Gallery Ownership
added_date: "2026-10-26 21:21:05"
last_updated: "2026-10-26"
summary: Move Gallery authoring, membership and presentation data from Studio into Docs Viewer before extending Catalogue browsing and search.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Docs Viewer Gallery Ownership

## Resume Here

Implementation is deferred at the owner's request on 2026-10-26 during an approximately ten-day absence. Resume discussion when the owner returns, around 2026-11-05; no implementation stage has started, including the Studio UI editing freeze.

Next action: review and agree the bounded GO.1 change set, then remove Gallery editing controls from Studio while retaining existing JSON, memberships, Refresh and readers. Stage 2's exact schemas/storage/migration decisions need not block that first UI freeze. Obtain the relevant implementation approval before production edits.

Decisions to carry forward:

- Studio retains Works, Series and media preparation; all Gallery source, authoring and generation moves into Docs Viewer.
- Immediately after Studio Refresh, Catalogue Regenerate adopts only Studio's queue-selected Work facts into baked Catalogue document JSON. It is the only Docs consumer of raw Studio Work by-ID JSON.
- Catalogue documents are generated Work representations. Working and public use the same ready document/presentation read model, without a separate live Work resolver.
- Regenerate owns Studio-derived Work fields; Gallery Refresh/Save owns Gallery-derived fields in the same document. Both use the document projection/persistence owner and preserve the other section. No extra per-Work Gallery sidecar is needed.
- Regenerate and Publish trust their supplied queues. They do not scan referring documents, recheck upstream history, repair authoring references or expand their queues. Broken Links diagnoses references left after deletion for the author to resolve.
- Retire unused public raw Work JSON distribution while retaining the required upstream Working input. Keep public presentation performance as the layout criterion.
- The three stages remain Studio UI freeze, Gallery ownership/Work-adoption migration, then the new Gallery management report. Medium grouping, the single free-text Work date and Catalogue search improvements follow separately.

Planning handoff: changed repository documents are this delivery, `documentation/studio/Planned_Features.md` and `documentation/studio/Development_Checklist.md`. Targeted source/configuration inspection and selected read-only payload inspection informed the current/target tables; scoped `git diff --check` passed. This planning work performed no production edits, test changes/runs, migration, generation, Publish, commit, push or deployment. Current production still has the live Work reads and Studio Gallery ownership inventoried below. Before stage 2, agree the baked field/schema contract, shared document writer, Gallery source location, initial queue-selected snapshot conversion and selected public cleanup.

## Current And Next State

Status: proposed. The owner has agreed the ownership direction and a three-stage sequence: freeze Gallery editing in Studio, move Gallery sources and production into independent Docs Viewer workflows, then add the Gallery management report UI. Studio Refresh must cease all Gallery work. This document records the target; no production UI change, source migration, generated write or publication has been performed. Resolve each stage's bounded readiness decisions and obtain its implementation approval before starting it.

Outcome: Studio owns Work/Series authoring, generated inputs and media preparation. Catalogue Regenerate, run immediately after Studio Refresh, is the sole ordinary owner that adopts queued Studio Work records into baked Working Catalogue document data. That adopted snapshot defines the latest Work known to Docs Viewer. Downstream Work presentation/preparation and Gallery workflows use that document data rather than rereading Studio Work by-ID JSON. Docs independently owns Gallery source, editing, joins and generation; Studio Refresh performs no Gallery work, directly or through a callback.

This is the first delivery before improving the [Catalogue collection report](/docs/?doc=d-20260916-161504-f8c947). It establishes the Gallery authority that later report filtering and Gallery search will consume. Medium grouping and date interpretation remain follow-on work. This does not move Studio Work/Series authoring or media processing into Docs Viewer.

Parent: [Planned Features](../Planned_Features.md). Use [Development Checklist](../Development_Checklist.md) and [Development Workflow](../Development_Workflow.md) for implementation, review and closeout.

### Three Implementation Stages

| Stage | Change | Data and reading during the stage | Completion state |
| --- | --- | --- | --- |
| 1 — Freeze Studio Gallery editing | Remove Gallery membership and definition/association editing from the single/New/bulk Work editor, including Gallery edit/delete prompts | No Gallery JSON/schema, producer, Refresh or Docs consumer changes; preserve existing assignments in ordinary Work saves | Gallery authoring is unavailable; Studio Refresh continues to supply existing Gallery data to Docs Viewer |
| 2 — Move Gallery ownership and enforce Work adoption | Move Gallery sources/generation to Docs, remove all Gallery work from Studio, bake queued Work facts during Regenerate and switch downstream consumers to those Catalogue documents | Studio Work by-ID JSON is read only by queue-driven Regenerate. Gallery/output workflows use adopted Work snapshots and their own Gallery data. | Docs owns Gallery generation and consumes Work data through the adopted document boundary; editing stays frozen |
| 3 — Add Docs Viewer Gallery management | Create the local report UI for definitions, memberships and Series relevance links, with its own Refresh/Save operations | Refresh uses regenerated Work data and agreed Series definitions; Save changes only Gallery sources/derived output and downstream publication effects | Gallery authoring resumes without importing newer Work facts or involving Studio Refresh |

Each stage is a reviewable stopping point within this delivery. Stage 1 can establish the editing freeze before stage 2's exact storage/handoff design is complete. Medium/date/search enhancements wait until the complete ownership delivery, including the replacement editor, is accepted.

## Requirements

### Ownership

Galleries are curated Work selections for Docs Viewer presentation. They do not define a Work or its Series membership. Preserve independent identities, cross-Series membership, multiple Galleries per Work and valid empty Galleries. Membership references exact Work IDs; their facts resolve from regenerated Catalogue documents whose child IDs are those same Work IDs. A Work not yet adopted by Regenerate is not imported through a Gallery/read fallback.

The following tables record the current implementation on 2026-10-26 and the agreed target; they do not claim that the migration has happened.

| Responsibility | Current owner | Target owner |
| --- | --- | --- |
| Work identity, descriptive metadata, Series membership and source-media declarations | Studio canonical model and Work editor | Studio |
| Series identity and title | Studio canonical model and Series controls | Studio |
| Image/file preparation and generated Work/Series inputs | Studio Save and Refresh Catalogue | Studio; no Gallery dependency; full Work by-ID output is input to Regenerate, not a general Docs runtime reader |
| Work facts adopted into Docs Viewer | Live reads can observe Studio Refresh output before Regenerate | Regenerate alone bakes queue-selected Work facts into Working Catalogue document JSON |
| Gallery identity and title | Studio Gallery definitions and editor controls | Docs Viewer |
| Exact Work–Gallery memberships | Studio membership source and single/bulk Work Save | Docs Viewer |
| Explicit Series–Gallery relevance links | Studio association source and Gallery controls | Docs Viewer; Series identity/title remain Studio-owned inputs |
| Gallery member records, lookup and relationship output | Studio Refresh Catalogue | Docs Viewer Gallery Refresh/Save; never invoked by Studio Refresh |
| Gallery links embedded in generated Work records | Studio Refresh Catalogue writes `work.galleries` | Remove them from Studio Work JSON; Gallery Refresh/Save updates the Gallery-derived section of affected Catalogue document JSON |
| Private Series and Galleries report data | Studio Refresh Catalogue; Docs Viewer reads/displays it | Docs Gallery Refresh/Save using adopted Work data and agreed Series definitions |
| Catalogue documents and manifests | Docs Regenerate/Build; current Working documents retain references only | Regenerate owns baked Work facts; Gallery workflows own derived Gallery fields in the same document. Both use the document projection/persistence owner and preserve each other's fields. |
| Media View, Gallery navigation and live/static Work presentation | Local provider reads Studio output; public uses prepared documents | Read adopted Work facts and Gallery references from the Catalogue document; retain Gallery by-ID reads for opening a Gallery and keep public layout performance-led |
| Selected public distribution | Docs Viewer Publish consumes completed Docs/Catalogue selections | Docs Viewer Publish continues to transfer completed selections |

The browser owns Gallery selection, Work search, membership choices, authoring feedback, sorting, counts and retained state over loaded data. Python owns persistence, queue-selected Work adoption, migration, required generation and handoff. Gallery management reads adopted Work documents, not Studio canonical records or Studio Work by-ID JSON. Studio neither reads Docs Gallery source nor calls its producer.

### One Catalogue Document Read Model

Catalogue child documents are generated Work representations, without an independently authored content body. Their by-ID JSON is the natural ready-to-display read model for both Working and public; it is not an authored document that requires a second live Work-record API to supply its main content. Ordinary authored documents and their references retain their own source/lifecycle.

Working should mirror the public document/presentation contract and read path: load the exact Catalogue document, reuse its baked Work/Gallery data and use the shared presentation reader/renderer. A Work referenced from another document resolves that same canonical Catalogue document by Work ID. Retire the separate local live Work-metadata resolver after snapshot conversion; no raw Studio fallback or per-Work Gallery lookup remains.

Regenerate supplies adopted Work facts and Gallery Refresh/Save supplies Gallery-derived fields through the document projection owner, keeping the ready presentation coherent. Local versus public resource URLs and capability composition remain with their existing boundaries; matching read models does not require exposing local paths or identical bytes in both destinations. Publish/Export preparation can adapt selected ready document data without resolving newer Studio metadata.

The structural/performance default is one ready Work document rather than multiple Work/relationship requests. Exact payload-size equivalence is not assumed or measured here; inspect representative completed output during the agreed conversion and investigate only an actual payload/request concern. No benchmark is required merely to adopt the existing public read model in Working.

### Catalogue Regenerate Defines The Latest Work

The agreed sequence is Studio Save → Studio Refresh → immediate Catalogue Regenerate → Docs consumption. Regenerate reads only the current/deleted Work selection supplied by Studio and its completed effects, bakes selected facts into the corresponding Working Catalogue by-ID document, and completes the existing handoff. No ordinary source scan, inventory expansion, dependency discovery, new queue or adoption ledger is introduced.

| Boundary | Target contract |
| --- | --- |
| Studio Work by-ID JSON | Upstream input read only by queue-driven Regenerate within Docs; never a runtime/preparation fallback |
| Working Catalogue by-ID document | Shared read model: Studio-derived Work facts updated only by Regenerate, and Gallery-derived fields updated by Gallery Refresh/Save |
| Local Entry/images/Media View | Reuse the baked snapshot; a reference in another document resolves the exact Catalogue document by Work ID |
| Gallery Refresh/Save and Work selection | Use adopted identity/title/metadata and Series membership with Docs-owned Gallery data; do not adopt Work changes themselves |
| Publish, Export and Prepare package | Use adopted Work document data and ready Gallery output; no raw Work JSON read or implicit Regenerate |
| Broken Links and Work-fact diagnostics | Diagnose the adopted document/presentation boundary rather than a newer Studio record |

Reuse a loaded Catalogue snapshot when available and resolve each exact required Work once per operation otherwise. A missing adopted snapshot is unavailable input; do not fall back to Studio output, repair it or run Regenerate silently. This is an explicit workflow, not a requirement for polling, freshness checks or another receipt.

Docs Viewer does not edit Work metadata. Referring documents can resolve the canonical regenerated Catalogue document without keeping another mutable Work copy. No scan, rebuild or automatic requeue of referring/related documents is required to adopt a Work. Related Links keeps its independent lifecycle and does not determine Work freshness. An explicitly selected referring document's preparation uses adopted data; unselected public documents keep their existing publication lifecycle.

#### Queue Authority And Broken References

Regenerate consumes Studio's queued effects without auditing what happened elsewhere. Publish consumes its queued effects without checking their provenance or repeating upstream eligibility/domain validation. Neither operation searches other documents to decide whether a selected Work deletion is safe, or expands its queue to repair references.

The deletion workflow is explicit:

1. Delete the Work in Studio and complete its ordinary Refresh handoff; the supplied queue identifies the deleted Work.
2. Regenerate deletes that exact Catalogue document and completes the existing selected removal/publication handoff. It does not inspect referring documents or reconstruct the deleted Work from another source.
3. Publish applies the queued public removals and completes those units. It neither blocks that deletion on incoming references nor edits unselected documents.
4. Any other authored document still referring to the deleted Work remains unchanged. The explicit Broken Links report diagnoses the missing target; the author resolves its source references through ordinary authoring operations.

Keep required selected-input reads, parsing, confinement and transfer verification at their existing boundaries. They do not authorize queue provenance, upstream-state or corpus/reference audits. Gallery-source choices likewise remain with their owning workflow: Regenerate/Publish do not scan or prune Gallery membership to protect a deletion; any additional deleted-member handling in Gallery Refresh/Save must be agreed explicitly rather than introduced as repair.

This target differs from the implemented live-Working readers inventoried below. Stage 2 removes their bypass reads. Gallery Refresh/Save may update the Gallery-derived portion of Catalogue document JSON, but cannot change baked Studio-derived Work facts, add Work-adoption selections to Studio's queue or invoke Regenerate to import newer metadata. Regenerate is the sole Work metadata importer, not the sole writer of every derived field in the document.

### Independent Refresh And Save Owners

Studio Refresh produces upstream Work/Series data; immediate Regenerate adopts its selected Works into document snapshots. Gallery Refresh uses those adopted facts and Docs Gallery sources; Save persists supplied Gallery choices and completes affected output. Neither Gallery workflow imports raw Work records or returns to Studio Refresh. Gallery Refresh, saved-data reload and Work adoption have separate owners.

| Operation | Responsibility and completion |
| --- | --- |
| Studio Save/Refresh | Own Work/Series source, media, upstream inputs and exact queue effects; no Gallery source, dependency selection or generation |
| Catalogue Regenerate | Immediately adopt Studio's completed queue selection into baked Work documents, including selected creation/update/deletion and the existing publication handoff |
| Docs Gallery Refresh | Read adopted Catalogue Work data, agreed Series definitions and Gallery sources; produce Gallery output and reconcile its own relationships against adopted changes |
| Docs Gallery Save | Persist Gallery choices and finish affected output/publication handoff using adopted Work facts; no Work metadata edit, raw Work read, Studio Refresh, Regenerate or media processing |
| Saved-data reload/read | Display saved data only; do not silently perform Gallery generation or invoke Studio Refresh. |

GO.2 must provide the Docs-owned generation workflow while editing remains frozen. Agree its non-authoring invocation before cutover; GO.3 then exposes the report's authoring controls and Refresh/Save UI over that owner. Do not make Studio Refresh a temporary or permanent Gallery orchestrator between those stages.

### Downstream Contracts And Separate Gallery Data

Preserve Media View/Gallery navigation behavior, exact Gallery targets and the existing Regenerate/Publish responsibilities. Keep existing queue formats and semantic completion units rather than adding another queue, flags or publication ledger. The owner that finishes a derived artifact must supply its readiness/publication handoff; Studio cannot report Gallery-dependent output complete merely because its Work-only inputs are ready.

| Contract | Required treatment |
| --- | --- |
| Catalogue updates/publication queues | Preserve existing schema shapes, identity units, saved pending effects and successful-unit removal. Split producer/consumer responsibility between Studio Work/Series work and Docs Gallery/combined work. Studio Refresh must no longer consume, wait for or finish Gallery work; Gallery Save must not queue it for Studio Refresh. Agree the exact use of existing fields/completion owners in GO.0 before code changes. |
| Catalogue Regenerate | Keep Studio queue-only selection and existing handoff; bake the selected Work facts into document JSON. It is the sole Work adoption owner, with no Gallery authoring or joins. |
| Publish, including preparation | Read adopted Catalogue documents and ready Gallery data only. Retain selected preparation, Preview/distribution, verification and successful-unit removal; no Studio Work by-ID read, Work adoption, Gallery generation or Refresh. |
| Media View and Gallery/report readers | Resolve Work facts from adopted documents and Gallery links from Docs data. Preserve functionality and public targets; choose public layout through the performance gate below. |
| Work and Gallery output writers | Studio owns upstream Work files. Regenerate supplies Work-fact changes and Gallery workflows supply Gallery-field changes to one explicit Catalogue document projection/persistence owner. Neither overwrites the other owner's fields. |

Today, `C/works/index/<work_id>.json` mixes Studio facts with `work.galleries`, and live/static providers read it directly. Remove Gallery fields from Studio output. Regenerate imports selected Work facts into their Catalogue document, while Gallery Refresh/Save maintains that document's Gallery projection. Runtime/static presentation reads the resulting document; no second per-Work relationship file, standalone full Work dataset or patch to Studio output is needed.

#### Gallery Fields In Catalogue Documents

Gallery definitions, memberships and Series associations remain canonical Docs-owned authoring sources. The affected Catalogue documents contain their generated per-Work Gallery projection. Gallery Save/Refresh reads the adopted Work facts from those documents and updates only the Gallery-derived fields; it has no Studio Work-record dependency. The editor's service uses the document projection owner rather than performing an unrelated raw JSON patch or rewriting authored content.

| Document section/operation | Owner and effect |
| --- | --- |
| Studio-derived Work facts | Regenerate updates only Studio queue-selected Works and preserves Gallery-derived fields |
| Gallery-derived references | Gallery Refresh/Save updates affected document IDs from its known definition/membership/association effects and preserves adopted Work facts |
| Ordinary document generation | Carries forward both supplied/adopted sections without re-importing Studio metadata or losing Gallery fields |
| Local/static Work presentation | Reads the combined document data, reusing the current payload when it is already loaded |

Preserve direct versus Series-related Gallery semantics, direct-first ordering, duplicate removal by Gallery ID and relation labels in the generated document/presentation contract. Work Series membership comes only from the adopted Work facts. Keep the canonical membership/relevance sources distinct from their generated projection; editing the document's Gallery fields is not a second authoring source.

Agree the exact field layout and empty-Gallery representation before GO.2; the old `work.galleries` name describes the data being moved, not a requirement to mix its ownership into the Studio-derived snapshot object. Agree initialization for new Catalogue documents and how the explicit Gallery Refresh adopts changed Series membership after Regenerate. Do not add Studio callbacks, queue expansion, automatic source repair, locks or a concurrent-user model.

Gallery create/rename/delete and membership/association Save select only their affected document projections and required Gallery records/indexes. Complete those writes and queue publication effects before reporting success. Reuse loaded Work documents and known before/after selections; no scan/rebuild of arbitrary referring documents or full Work-record re-import is required. Existing `galleries/index/<gallery_id>.json` still serves the Gallery grid/member navigation; this change removes only the proposed extra per-Work Gallery sidecar.

#### Public Performance And Preparation Boundary

Public performance determines the served data layout. Clean source ownership does not require matching Working/public storage shapes, combining every public JSON file, or introducing extra runtime requests. Separate public files are acceptable if they provide a concrete consumer benefit without a material public performance regression; they are not assumed free merely because requests can run in parallel.

Source inspection of `docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js` establishes the current public path: Work presentation comes from `payload.catalogue.presentations`; navigating to another Work loads that Work's prepared Catalogue document and extracts its embedded presentation. The inspected public Work provider does not fetch raw `catalogue/works/index/<work_id>.json`. Opening a Gallery reads its existing Gallery record and media policy separately. This is request-path evidence, not measured deployed-site latency.

Default: prepare public presentation from the Catalogue document's adopted Work and Gallery sections. This preserves the public request pattern and avoids an additional per-Work Gallery lookup in local display as well. Neither local nor static resolution bypasses Regenerate for Work facts.

| Storage/consumer boundary | Work representation |
| --- | --- |
| Working Studio-generated Work file | Upstream facts read only by queue-driven Regenerate within Docs Viewer |
| Working Catalogue by-ID document | Regenerate-owned Work facts plus Gallery-owned derived references; explicit field ownership and one document projection writer |
| Local Working Media View provider | Uses the same ready document/presentation contract as public, with local resource routing; no live Work-metadata resolver or extra relationship lookup |
| Prepared public documents and public Media View — default | Keep existing embedded presentations and Gallery links, with no added relationship request |
| Raw Preview/repository Work JSON | Retire unused public distribution through explicit bounded cleanup; no replacement combined raw Work JSON is needed by the identified reader |
| Separate public Gallery relationship files — alternative | Publish/read only if a concrete use and proportionate comparison justify the additional request/payload/caching tradeoff |

Do not add a raw public Work recomposition/version pass for a field unused by the identified public reader. Retire that distribution separately from required upstream Working inputs and adopted snapshots. Agree selected public/Preview removals and inventory/transfer cleanup before writes; do not remove Working input or document data as part of public artifact retirement.

If separate public reads are proposed, compare the actual request path against this baseline: cold Work opening, navigation to another Work and warm repeat navigation, including representative mobile/high-latency conditions. Consider time to usable Work presentation and Gallery links, critical request dependency, transferred bytes and cache reuse, not JSON join time or request count alone. State the exact scenarios, acceptable difference, setup/runtime/write/network cost and approval before any prototype, benchmark or new test script. No automatic benchmark is required when the public request/payload path remains unchanged.

Gallery edits update affected document Gallery fields and select their publication units even when Studio Work facts are unchanged, including removal and the agreed empty representation. Reuse existing Work identity queue units/flags and successful-unit completion; do not add Work-adoption entries to Studio's queue. Existing Gallery records/lookups retain their targets. Publish consumes the completed selected documents: no canonical reads, eligibility calculation, Gallery generation, Refresh, corpus scan or freshness audit. Queue removal still follows complete selected Work/document/media transfer.

### Current Canonical Inputs

Repository-relative locations below describe the existing authority. Stage 1 leaves these files and their schemas unchanged. The configured Docs workspace, not a repository fallback, must own the new Gallery sources after stage 2. Agree their exact configuration entries and source paths before GO.2 implementation; no target source location is implicitly created by this document.

| Current source | Contents and current owner | Migration treatment |
| --- | --- | --- |
| `studio/data/canonical/catalogue/works.json` | Studio Work records, including title, `series_id`, `medium`, `year`, `year_display`, media/source declarations and other Work metadata | Remains Studio-owned; date-field changes are separate |
| `studio/data/canonical/catalogue/series.json` | Studio Series definitions | Remains Studio-owned |
| `studio/data/canonical/catalogue/galleries.json` | Studio Gallery IDs/titles; `catalogue_source_galleries_v1` | Move sole authority into configured Docs Working source storage |
| `studio/data/canonical/catalogue/galleries-by-work.json` | Studio Work ID → Gallery ID arrays; `catalogue_source_galleries_by_work_v1` | Move sole membership authority with the definitions; preserve exact selections |
| `studio/data/canonical/catalogue/series-galleries.json` | Studio explicit Series → Gallery relevance arrays; `catalogue_source_series_galleries_v1` | Move with Galleries; preserve the existing navigation relationship independently of Work membership |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/source/collections/catalogue/documents/<work_id>.md` | Docs Catalogue sources generated from selected refreshed Works | Regenerate owns source/document adoption; Gallery workflows resolve the resulting baked Work snapshot by exact Work ID |

Current source contracts are described by [Catalogue Source Model](../Catalogue_Source_Model.md). Gallery data already lives outside `works.json`, but its persistence and operation ownership are still coupled to Studio.

### Current Generated Data And Locations

The following inventory distinguishes producer ownership from physical storage. Studio writes consumer JSON inside the Docs workspace today; that location alone does not make its producer Docs Viewer.

In the table, `C` means `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. It is resolved by `docs-viewer/config/workspace/docs-workspace.json`. The inventory is a planning baseline, not a declaration that each saved artifact or deployed site has the same generation time.

| Current generated location | Producer and contents | Delivery treatment |
| --- | --- | --- |
| `C/works/index/<work_id>.json` | Studio Refresh; `work_record_v11` currently mixes Work facts, optional `series_id` and `work.galleries` | Work-only upstream input read by Regenerate; Gallery fields move out, downstream readers switch to adopted documents, and unused public distribution is retired |
| `C/galleries/index/<gallery_id>.json` | Studio Refresh; `gallery_record_v3` with Gallery ID/title and `member_works` containing exact Work IDs/titles | Docs Viewer Gallery Refresh/Save owns this output; retain the existing reader path/shape where no change is required |
| `C/galleries/galleries_index.json` | Studio Refresh; `catalogue_galleries_index_v3`, Gallery ID/title lookup, including empty Galleries | Preserve the lookup path/schema/shape and its readers; move the projection owner |
| `C/series-galleries-index.json` | Studio Refresh; `catalogue_series_galleries_index_v2`, explicit Series → Gallery ID/title links | Preserve path/schema/shape; move the relationship projection owner |
| `C/reports/series-galleries/metadata.json` | Studio Refresh; private `catalogue_series_galleries_report_v3` rows with Series/Gallery labels, missing-side placeholders and Gallery Work counts | Docs Viewer Gallery Refresh/Save owns this derived report input; preserve the report's reading behavior without a separate presentation redesign |
| `C/works/works_index.json` | Studio Refresh; `catalogue_works_index_v3`, compact Work IDs/titles | Remains a Studio-generated Work input; do not inflate this picker lookup into a general report dataset by default |
| `C/reports/catalogue-works/metadata.json` | Studio Refresh; private `catalogue_works_report_metadata_v3`, Work facts for local Catalogue Works/Medium reporting | Remains Studio-generated; supplies an existing local selection/report input where its fields are sufficient |
| `C/private/work-sources.json`, `C/private/work-resources.json`, `C/private/series.json` | Studio Refresh; portable Work placement/source facts, Work links/download filenames and Series definitions for local reports | Remain Studio-generated inputs with their current private boundary |
| `C/media-config.json` | Studio Refresh; shared public-safe image/thumbnail policy | Remains Studio-generated; Gallery edits produce no media |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/assets/works/{primary,thumbs,media/files}/` | Studio Save prepares Work image renditions, thumbnails and attachments under configured asset owners | Remains Studio-owned preparation; selected transfers retain the existing publication owner |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/collections/catalogue/documents/manage-manifest.json` and `manifest.json` | Docs Viewer Build and public-metadata projection; current list rows contain `doc_id`, `title`, `last_updated` and optional authored-thumbnail presence | Remain Docs-owned document listings; no new medium/date/Gallery search fields are delivered here |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/collections/catalogue/documents/by-id/<work_id>.json` | Docs Regenerate/Build; currently identity/reference-only content | Regenerate bakes adopted Work facts here; agree explicit initial conversion/queue selection before switching readers, while ordinary Regenerate stays Studio queue-only |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/search/index.json` | Docs Viewer explicit Search build; site-search `docs_viewer_search_index_v4` | Unchanged by this delivery; Catalogue subdocuments remain excluded by current policy |

`docs-viewer/config/workspace/catalogue-artifacts.json` currently selects public Catalogue by-ID directories `works/index` and `galleries/index`, plus `media-config.json`, `series-galleries-index.json`, `works/works_index.json` and `galleries/galleries_index.json`. Private report and `private/` files are excluded.

Docs Viewer Publish applies selected Catalogue artifacts to `$DOTLINEFORM_DOCS_BASE_DIR/preview/catalogue/` and repository `site/assets/data/catalogue/`. Existing public Gallery/system artifacts retain their transfer owner. Catalogue documents have their separate configured owner: Working collection documents, Preview at `preview/collections/catalogue/documents/`, and repository output under `site/assets/data/docs/catalogue/`. Preserve existing public targets and default to the current artifact inventory; make any actual layout/inventory change explicit at the performance/consumer decision gate.

Gallery links also enter prepared document media presentations through the shared static preparer used by Publish, Export and Prepare package. Read the Catalogue document's ready Work/Gallery sections and preserve the public presentation contract; no extra lookup or canonical join belongs in preparation. [Catalogue Indexes And Payloads](../Catalogue_Indexes_And_Payloads.md), [Catalogue Media View](../Catalogue_Media_View.md) and [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) describe current boundaries.

### Current Working Work-Record Readers

This table records the current implementation before the adoption correction. Working documents currently contain references rather than baked Work facts, and several consumers read Studio output directly. Those reads are the implementation gap against the agreed Regenerate boundary, not authority for retaining a live bypass.

| Identified current reader | Purpose and owning boundary |
| --- | --- |
| Catalogue Regenerate | `docs_catalogue_regeneration.py` reads selected refreshed Work records and passes their identity/title to `docs_catalogue_work_record.py`, which produces an identity-only Entry token and Related links directive; it also carries required resource/handoff facts. It does not bake Work metadata or a Media View presentation into Working documents. |
| Local Entry/image/Media View provider | `docs-viewer-catalogue-live.js` calls `readCatalogueWork`; the source adapter/client and `docs_management_read_service.py` route reach `docs_catalogue_media.local_catalogue_work`. This resolves current Work facts and local download URLs for the mounted presentation, including references in other documents. |
| Shared static preparation | `docs_catalogue_static.CatalogueStaticInputs.work` reads each required Work record for selected presentation preparation. Callers are Publish, collection Export in `docs_static_html_export.py`, and document-content Prepare package in `docs_document_packages/rendered_content.py`. Loaded inputs/presentations are reused within that operation. |
| Explicit Broken Links report | `docs_broken_links.catalogue_target_reason` reads referenced Work records for generated-target/media diagnosis during the report's explicit audit. It is not a normal document-display or generation step. |
| Publish's raw Work metadata copy | Existing `docs_catalogue_publication.py` also copies selected Work metadata bytes to Preview/public. This is retained distribution, not a current public Work-presentation reader. Review its public necessity explicitly; it is separate from the required Working reads above. |

Target: only Regenerate retains a full Studio Work-record read. Local display, shared static preparation and Work-fact diagnostics switch to baked Catalogue documents. Public raw Work distribution is retired with its selected transfer cleanup. A referring document resolves the canonical adopted Work snapshot; no rebuild fanout is required.

Compact Work target lookup and Catalogue Works/Medium reports currently use their own indexes/private aggregates rather than full by-ID records. At readiness, identify which exposed Work facts must follow the adoption boundary and derive their Docs-facing projection from adopted documents. Do not use those aggregates as an alternate route to newer Work presentation/selection metadata, or copy private source/storage fields into public document output merely to reuse a report dataset.

Source/read-only inspection confirms the present gap: selected Working Catalogue `00008` has references without embedded Work presentation. [Public Work JSON Review](../Public_Work_JSON_Review.md) records the earlier live-Working implementation; this delivery's explicit Regenerate adoption rule supersedes that target. Its public Work reader was removed while physical JSON distribution remained, with no current public Docs Viewer reader identified.

Implement the adoption rule in stage 2: bake only Studio queue-selected Work facts during Regenerate, switch downstream resolution to that canonical snapshot and remove the direct-read route after callers migrate. Ordinary Build preserves supplied/already adopted facts and cannot reread Studio Work JSON; agree its narrow snapshot input path. Plan initial snapshot population as an explicitly approved queue-selected conversion before reader cutover, without adding a full-scan fallback to normal Regenerate.

### Current Operation Coupling To Remove

Studio's single and bulk Work Save carry `gallery_ids` independently of the Work record, persist the membership map and select Gallery-related output. Gallery create/rename/delete and Series–Gallery edits select generated Gallery/relationship effects. Studio's editor also discovers newly empty Galleries after membership removal and offers a delete prompt. Empty Galleries themselves remain valid.

Studio mutation effects currently flow through `$DOTLINEFORM_DOCS_BASE_DIR/working/catalogue-updates-pending.json` (`catalogue_updates_pending_v5`). Gallery/Series selections, `created_galleries`, `gallery_member_works` and selected shared outputs contribute to Studio Refresh today. Completed public effects enter `working/catalogue-publish-pending.json`; Docs Viewer Regenerate consumes ready Work effects separately. Preserve existing queue envelopes and pending effects, but move Gallery generation/consumption/completion to Docs Viewer. Existing Gallery-related pending units must acquire their new completion owner at cutover without being discarded or processed by Studio Refresh. Agree any exact saved-selection remapping required by the Work/combined artifact split; do not flush queues or add another ledger.

Work title/deletion and Series membership changes become Docs Work facts only through Regenerate's Studio-selected adoption. Gallery workflows resolve consequences against that adopted state and their own associations; Studio does not discover Gallery targets. Gallery effects may select required prepared Work/Gallery publication output, but never import Work metadata or require scanning/rebuilding related documents. Reuse existing effect identities, without callbacks, canonical Studio reads, polling, repair or downstream agreement audits.

### Editing Freeze

Stage 1 removes Gallery controls and user-facing mutation entry points from Studio's Work editor, covering single, New and bulk modes, Gallery create/rename/delete, membership add/remove and the Series relevance controls reached through Gallery editing. Remove the old newly empty Gallery delete prompts from that UI flow as well. This is an authoring freeze in the agreed single-user application model; do not add a new API permission mode, persisted freeze flag or runtime feature switch.

The UI removal must preserve saved memberships in the existing single/bulk Save contracts. Hiding controls must not initialize a replacement empty list, clear selections or turn an unrelated Work Save into a Gallery edit. Keep existing internal Gallery data and backend contracts where the unchanged Work lifecycle still requires them; remove those dependencies in stage 2 rather than combining the ownership migration with the freeze.

Stage 1 itself changes no canonical/generated JSON, schemas or Gallery production. Existing Work/Series lifecycle effects, including Work deletion's membership cleanup and title-driven generated updates, continue through their current owners while Studio still owns the data. The freeze prevents deliberate Gallery authoring; it does not suspend those existing lifecycle effects or prevent ordinary Work/Series editing.

After stage 2, Gallery reading/generation continues through the independent Docs workflow while editing remains frozen. Studio Refresh is already Gallery-free at that point. Stage 3 is the only point at which the replacement Gallery editor becomes available. No temporary second editor, Studio generation callback or alternate source writer is needed between stages.

### Target Workflow

After stage 3, a local Docs Viewer Gallery management report owns Gallery create/rename/delete, viewing member Works, searching available Works, adding/removing selected memberships and editing the existing Series relevance links. Reuse existing generated Work/Series inputs and narrow report/selection components where they fit. Agree the exact local host and whether the existing Series and Galleries report becomes the management entry point before GO.3 implementation.

Gallery Refresh uses the last regenerated Catalogue Work snapshots and agreed Series definitions to build Gallery data. Save awaits Gallery persistence, affected output and publication handoff. Neither operation imports raw Work data, invokes Regenerate/Studio Refresh or leaves Gallery work for Studio. Regenerate is already complete for the adopted Work state; subsequent Gallery edits have their own publication effects. Saved-data reload does not generate, and Gallery Save does not edit Work facts or prepare media.

Preserve Gallery IDs and existing authored Gallery references, direct versus Series-related links, Gallery Media View/Work navigation, empty-state behavior and Back behavior. Preserve the ability to keep an empty Gallery. Reconcile the old editor's empty-Gallery prompt explicitly during UI design rather than adding automatic deletion or assuming its choreography belongs in the new report.

The migration establishes one canonical Gallery source owner and one independent Docs Gallery generation owner. Remove Studio Gallery controls in stage 1; retire its Gallery source mutations, dependencies, queue processing and generation at stage 2 cutover. Unchanged backend retention during stage 1 serves the existing source/lifecycle owner and is not a new compatibility interface. Do not leave dual writers, Studio-to-Gallery generation callbacks, canonical shadow copies, old-field readers, compatibility endpoints or hidden fallbacks after cutover.

## Deliverables

- A Studio Gallery editing freeze that removes its user-facing controls while preserving existing JSON, saved memberships, Refresh and Docs Viewer reading.
- Configured Docs-owned canonical Gallery definitions, Work memberships and Series associations, with an explicit migration preserving current identities and selections.
- Queue-only Regenerate adoption into baked Working Catalogue Work documents, with local/static/diagnostic consumers migrated away from direct Studio Work-record reads and no related-document rebuild fanout.
- A local Gallery management workflow over adopted Work snapshots and agreed Series definitions, with browser-owned choices and independent Docs Refresh/Save services.
- Docs-owned Gallery sources/member/report output and Gallery-derived fields in Catalogue document JSON, with explicit field owners and one document projection/persistence path; preserve embedded public presentation by default.
- Removal of all Gallery authoring, source dependencies and processing from Studio Save/Refresh, while retaining Studio Work/Series operations and media preparation.
- Existing queue formats and pending effects preserved with explicit completion ownership for Studio Work/Series versus Docs Gallery/combined work; no additional ledger or speculative conversion.
- A current durable Gallery owner document at closeout, with affected existing ownership/configuration guidance corrected within this delivery's boundary.

## Process

During stages 1 and 2, continue ordinary Work/Series operations and Gallery reading through the stage's current owner; Gallery editing stays unavailable. Stage 2 already provides independent Docs Gallery Refresh without the new authoring controls. The completed workflow after stage 3 is:

1. Create/edit Works and Series in Studio, run Studio Refresh, then immediately Catalogue Regenerate. Regenerate adopts only Studio's queue selection into baked Catalogue Work documents; Studio performs no Gallery work.
2. Open local Docs Viewer Gallery management, choose or create a Gallery and use loaded Work data to inspect/add/remove exact members. Edit its title and optional existing Series relevance relationships there.
3. Use Gallery Refresh/Save over that adopted Work state to complete Gallery output and publication effects. These operations do not trigger another Work adoption or require Regenerate for a Gallery-only change. Local display and referencing documents resolve Work facts from baked Catalogue data.
4. Publish the completed selected Gallery/presentation effects, including current preparation, through the existing Docs Viewer Publish action when explicitly requested. Public reading consumes finished output; it does not read local authoring sources.

## Delivery Steps

### GO.0 — Readiness And Implementation Agreement

- [ ] Confirm the three stage boundaries and the user-visible freeze/reopening points against current controls, Save contracts, generation and consumers.
- [ ] Enforce the agreed snapshot boundary: immediate queue-driven Regenerate is the only Studio Work by-ID reader and the only Work adoption owner. Agree baked document contents, ordinary Build preservation, downstream reader migration and explicit initial snapshot population; no referring-document fanout or new queue.
- [ ] Preserve queue-only deletion: Regenerate/Publish consume exact selected removals without upstream-history or incoming-reference audits. Broken authored references remain for Broken Links and author resolution; do not introduce automatic unlinking, dependency requeueing or Gallery pruning.
- [ ] Before GO.1, identify the complete Studio Gallery editing surface and how ordinary Work saves preserve existing memberships after its removal; agree the narrow change set and evidence.
- [ ] Before GO.2, agree Gallery source storage and the Catalogue document's separate Work/Gallery field contracts, shared projection/persistence path, preservation/initialization rules and independent generation invocation during the freeze. No extra per-Work Gallery sidecar. Confirm snapshot readers and public raw Work retirement.
- [ ] Trace public consumers and approve exact raw Work artifact retirement/inventory cleanup. Default to embedded prepared presentations; any alternative public relationship request needs a concrete benefit and scoped performance evidence. No benchmark/prototype/test code without its separate approved scope.
- [ ] Before GO.2, assign processing/readiness/publication completion for each existing queue unit, including pending Gallery work and Work/Series changes adopted by Docs generation. Preserve queue formats and downstream Regenerate/Publish roles without routing Gallery work through Studio Refresh.
- [ ] Before GO.3, agree the management entry point, membership/association interactions, treatment of newly empty Galleries and browser/service responsibilities for the report's own Refresh/Save completion.
- [ ] Obtain implementation approval for the relevant stage before editing production code. Specify any proposed test work separately before creating or changing tests.

Verification budget: targeted read-only source/configuration and relevant saved-input inspection only. No prototype, mutation, migration, generation, runtime service or test execution is needed to decide readiness. Existing tests are not accepted evidence merely because their names mention Galleries.

Gate: GO.1 may proceed after its bounded UI/Save readiness and approval. GO.2 requires a Gallery-free Studio, queue-only Regenerate snapshot adoption with explicit initial population, downstream snapshot readers and independent Docs Gallery generation. GO.3 requires agreed authoring interactions over that owner. Raise unagreed input/schema changes, wider Studio migration, synchronization/recovery machinery or a new Search lifecycle before implementation.

Record: proposed. Last queue-driven Regenerate defines the adopted Work state. Current live reads bypass that boundary and must migrate to baked Catalogue documents, including preparation and diagnostics. Gallery workflows use those snapshots and never adopt Studio Work facts themselves. Raw public Work distribution has no identified reader and is slated for explicit cleanup; public embedded presentations remain the default. Exact snapshot/schema, initial queue-selected conversion, Gallery storage and completion wiring remain to be agreed. No production/generated changes or performance comparison has occurred.

### GO.1 — Stage 1: Freeze Gallery Editing In Studio

- [ ] Remove Gallery membership editing from single/New/bulk Work UI and remove its Gallery create/edit/delete and Series-association entry points and empty-Gallery cleanup prompts.
- [ ] Preserve loaded Gallery memberships and the existing ordinary Work Save/bulk Save contracts; do not clear assignments when controls disappear.
- [ ] Leave Gallery JSON/schema, backend source/production ownership, queues, Refresh and Docs Viewer readers unchanged.
- [ ] Review changed UI and Save paths for stale callbacks, unintended writes and hidden Gallery edit entry points; complete a bounded redundancy/defensive review before accepting the stage.
- [ ] Present the frozen editor and preserved ordinary Work/Refresh/Media View behavior for manual confirmation, distinguishing source review from any actual writes performed.

Verification budget: changed-path JavaScript lint, whitespace and focused source/diff review address module/control removal and saved-membership preservation at an expected cost of seconds, without data or service writes. Manual editor confirmation covers the absent controls and ordinary Save behavior; agree any real Save/Refresh exercise and its targets before execution. No JSON migration, generation, API freeze machinery, public runtime projection or automated browser/test work is required merely to remove local editor controls.

Gate: Gallery authoring is unavailable in the Studio UI, ordinary Work saves retain existing memberships, and Refresh still supplies Gallery data exactly through its current owner. This is the intended frozen stopping point before migration.

Record: not started.

### GO.2 — Stage 2: Move Gallery Data, Production And Consumers

- [ ] Move the three canonical JSON families into configured Docs-owned source storage, preserving Gallery IDs, titles, memberships and Series associations.
- [ ] Implement Regenerate-only adoption of Studio's completed queue selection into baked Catalogue Work JSON; preserve adopted facts during ordinary Build and seed initial snapshots through the approved explicit selection before switching readers.
- [ ] Migrate local Entry/images/Media View to the shared ready document/presentation contract used by public; migrate static preparation and Work-fact diagnostics to the same baked Catalogue data. Reuse loaded payloads and exact Work-ID resolution, then retire the separate live Work resolver/direct-read entry points without a Studio fallback.
- [ ] Implement independent Gallery Refresh/generation over adopted Work snapshots and agreed Series definitions, with an invocation while editing is frozen. No callback or raw Work read from Gallery workflows.
- [ ] Remove Gallery source access, joins, generation, cleanup, dependency selection and Gallery queue processing from Studio Save/Refresh; retain only Work/Series facts/effects and media preparation there.
- [ ] Remove `work.galleries` from Studio inputs. Implement Gallery-source projection into affected Catalogue document Gallery fields through the shared document writer, preserving adopted Work facts and Series-related semantics. Regenerate/ordinary Build preserve Gallery-owned fields; no sidecar or duplicate standalone Work dataset.
- [ ] Prepare selected public documents from their ready adopted Work/Gallery data, retaining embedded presentation by default. Retire raw public Work copying and perform agreed selected Preview/repository cleanup; do not delete upstream inputs or adopt newer facts during preparation.
- [ ] Assign the existing queued units to their correct processing/completion owner, including pending Gallery effects and required affected Work/document output. Retain queue formats and downstream Regenerate/Publish responsibilities; no producer may mark another owner's unfinished output ready.
- [ ] Review exact source migration inputs and expected writes, preserving pending effects. Perform only the agreed source/output conversion; no automatic queue flush, extra ledger or speculative bulk document conversion.
- [ ] Confirm Working and public use the shared ready Catalogue document/presentation model, with only required resource/capability differences. No raw Work or per-Work relationship reads remain in display/preparation. Follow required projection/site checks for actual public runtime changes.
- [ ] Review the ownership/consumer cutover and complete a bounded redundancy/defensive review before accepting the stage; obtain manual reading/Media View confirmation.

Verification budget: choose exact changed-path lint, Python syntax, JSON parsing and whitespace checks once owners are known; static cost is expected to be seconds without data/service writes. Review all full Work-record call paths for Regenerate-only reads, Studio for absence of Gallery work, and generation for selected snapshot/output completion. Agree initial snapshot conversion, source/public cleanup and exact generation diagnostics before writes; do not create an unapproved regression script. Public runtime changes require `bin/site-code-update`, exact projection review, `bin/site-code-update --check` and `bin/site-validate`. No broad media generation, queue flush or Search rebuild follows automatically. Publish, deployment and Git actions retain separate authorization.

Gate: Studio has no Gallery dependency; Regenerate alone adopts its queue-selected Work facts into baked documents. Local/static/Gallery consumers cannot bypass that snapshot. Independent Gallery generation and existing downstream queues work from adopted inputs; Gallery editing remains frozen until GO.3.

Record: not started.

### GO.3 — Stage 3: Add Docs Viewer Gallery Management

- [ ] Create the agreed local Gallery report UI for definitions, current members, available-Work search, membership changes and existing Series relevance relationships.
- [ ] Keep selection, grouping/counts, feedback and retained state in the browser over adopted Catalogue Work data, agreed Series definitions and Docs Gallery data.
- [ ] Implement Refresh/Save over GO.2: persist selected Gallery source choices, project affected Catalogue document Gallery fields while preserving adopted Work facts, complete Gallery outputs and queue publication effects. Never import Work metadata or expand Studio's Regenerate queue.
- [ ] Preserve valid empty Galleries and agree any explicit delete prompts without restoring Studio Gallery controls or adding automatic cleanup.
- [ ] Review the authoring path and complete a bounded redundancy/defensive review before accepting the stage; present management, Media View and return behavior for manual confirmation.

Verification budget: changed-path JavaScript/Python lint, syntax/whitespace and scoped source review address wiring, source ownership, selected derived-output completion and existing queue effects; static cost is expected to be seconds. Agree exact authoring/Refresh targets and source/generated/queue writes before execution. UI selection feel, empty states and navigation receive manual review. Existing test execution requires inspected coverage and an agreed budget; creating/updating tests, fixtures, harnesses or temporary regression scripts requires separate approval under [Test Contract Discipline](../Test_Contract_Discipline.md). No browser suite is automatically added or run.

Gate: Gallery authoring resumes entirely in Docs Viewer over last-Regenerate Work snapshots. Refresh/Save finishes Gallery output and selects publication effects without Studio involvement or a new Work adoption; Publish/preparation consumes completed adopted data. Medium/date/search changes remain outside this stage.

Record: not started.

### GO.4 — Final Code And Redundancy Review

- [ ] Independently review complete removal of Gallery work from Studio, independent Docs Refresh/Save completion, source/output writer boundaries and existing queue handoffs; confirm preserved reading behavior and Regenerate/Publish/preparation responsibilities.
- [ ] Trace selected Work deletion through queue consumption and public removal: no referring-document/corpus scan, deletion preflight, upstream-state revalidation or repair is hidden in reused helpers. Broken Links remains the explicit diagnostic owner for leftover authored references.
- [ ] Complete the mandatory Redundancy And Defensive Behavior Review in Development Checklist, tracing normal, empty and unchanged operations and reused helpers beyond changed lines.
- [ ] Challenge raw Work reads outside Regenerate, implicit adoption, field ownership violations, independent JSON patch writers, loss of Gallery fields during Regenerate/Build, extra per-Work Gallery files, related-document rebuild fanout, Gallery-created Studio adoption selections, callbacks, duplicate Work snapshots, repeated joins/hash passes, unnecessary reads/scans/media work, downstream audits, compatibility branches and recovery policies. Preserve required selected publication completion.
- [ ] Retain and justify actual local-write authority, exact-target and path/symlink confinement, parsing/sanitization, missing-input failures and selected transfer checks at their owning boundaries.
- [ ] Record findings, removals and justified safeguards; resolve them and rerun only the evidence affected by corrections.

Verification budget: bounded final source/diff and selected generated-output review, reusing GO.1–GO.3 evidence and each stage's review. No broad audit or suite follows automatically from review.

Gate: no unresolved finding that breaks the agreed ownership/workflow; completion claims match the actual migration, manual observations and public-data evidence.

Record: not started.

### GO.5 — Durable Ownership And Closeout

- [ ] Record accepted Gallery management, Regenerate-only Work adoption and downstream snapshot resolution, completed conversion/source relocation and separate publication/deployment state.
- [ ] Establish the durable Docs Viewer Gallery owner and correct the affected Studio source/output/lifecycle, Media View and workspace/public-inventory documentation; keep future medium/date/search design outside shipped documentation.
- [ ] Confirm retired Studio Gallery authorities are removed and one configured source remains, with ordinary Git/source recovery rather than aliases or automatic backups.
- [ ] Update Planned Features routing and retain the follow-on requirements below as proposed work.
- [ ] Present this delivery's retain-or-retire recommendation and durable destinations. Do not delete documentation without approval.

Verification budget: bounded documentation and final state/diff review; reuse completed implementation evidence. No Search rebuild or repeated full generation is a closeout requirement.

Gate: the complete Gallery ownership move is accepted and its durable owner is current. This prerequisite does not itself approve follow-on Catalogue work.

Record: not started.

## Follow-on

After this delivery, specify the Catalogue report improvements against Docs-owned Gallery data and Studio-generated Work facts. These are subsequent complete deliveries, outside all three implementation stages above.

- **Medium groups:** local Docs Viewer report assignment of distinct descriptive medium values to search/report groups such as Drawings, Paintings, Digital and Video. Groups support icon filters and remain separate from canonical Work metadata. Preserve exact authored medium descriptions; agree assignment cardinality and how unassigned media appear before implementation.
- **Single date text:** retain the current `year_display` content as the single authoritative free-text Work date and retire separately maintained numeric `year` through its Studio authoring/import/generated consumers. Derive ordering and year/range search interpretation in the browser, preserving the display text. Agree start/end ordering, abbreviated ranges, separate dates and suggestion semantics; ascending start-year ordering is a proposal, not an implemented rule.
- **Catalogue filtering and Gallery discovery:** prepare compact public-safe browsing data from the respective owners, with no per-Work loading merely to filter. Show a compact matching-Galleries section above matching Works, with clear type/count information and separate Work pagination. Gallery-title matches return Galleries rather than automatically expanding every member into Work results; specific Work queries retain useful direct matches. Medium/date filtering of Gallery results needs an explicit rule.

The current Catalogue document manifest is already Docs-generated and can be enriched or accompanied by a narrow report projection when that follow-on is specified. Medium mapping can be resolved in loaded browser data instead of duplicated into every row. Lightweight title/ID/description matching, structured filtering and derived date ordering are the agreed direction; these requirements do not justify a new full-text index, runtime search service, automatic site Search rebuild or changes to site-search collection coverage.
