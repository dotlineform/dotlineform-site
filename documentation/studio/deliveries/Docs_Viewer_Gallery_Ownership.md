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

## Current And Next State

Status: proposed. The owner has agreed the ownership direction and requested this specification. Production implementation, source migration, generated writes and publication have not been authorized by that documentation request. GO.0 must resolve the bounded readiness decisions before implementation approval.

Outcome: manage Galleries entirely in local Docs Viewer and use those same Docs-owned definitions and Work memberships for Media View, related Gallery links and public Gallery output. Studio continues to define Works and Series and prepare their media. Gallery editing no longer requires Studio Work Save or Studio Refresh Catalogue.

This is the first delivery before improving the [Catalogue collection report](/docs/?doc=d-20260916-161504-f8c947). It establishes the Gallery authority that later report filtering and Gallery search will consume. Medium grouping and date interpretation remain follow-on work. This does not move Studio Work/Series authoring or media processing into Docs Viewer.

Parent: [Planned Features](../Planned_Features.md). Use [Development Checklist](../Development_Checklist.md) and [Development Workflow](../Development_Workflow.md) for implementation, review and closeout.

## Requirements

### Ownership

Galleries are curated Work selections for Docs Viewer presentation. They do not define a Work or its Series membership. Preserve independent Gallery identities, cross-Series membership, multiple Galleries per Work and valid empty Galleries. Membership references exact Work IDs, not Catalogue document IDs or document availability.

The following tables record the current implementation on 2026-10-26 and the agreed target; they do not claim that the migration has happened.

| Responsibility | Current owner | Target owner |
| --- | --- | --- |
| Work identity, descriptive metadata, Series membership and source-media declarations | Studio canonical model and Work editor | Studio |
| Series identity and title | Studio canonical model and Series controls | Studio |
| Image/file preparation and generated Work facts | Studio Save and Refresh Catalogue | Studio |
| Gallery identity and title | Studio Gallery definitions and editor controls | Docs Viewer |
| Exact Work–Gallery memberships | Studio membership source and single/bulk Work Save | Docs Viewer |
| Explicit Series–Gallery relevance links | Studio association source and Gallery controls | Docs Viewer; Series identity/title remain Studio-owned inputs |
| Gallery member records, lookup and relationship output | Studio Refresh Catalogue | Docs Viewer generation |
| Gallery links embedded in generated Work records | Studio Refresh Catalogue writes `work.galleries` | Docs Viewer composes presentation links from its own Gallery data; Studio Work output ceases to own them |
| Private Series and Galleries report data | Studio Refresh Catalogue; Docs Viewer reads/displays it | Docs Viewer |
| Catalogue document sources, generated documents and collection manifests | Docs Viewer Regenerate/Build | Docs Viewer |
| Media View, Gallery navigation and live/static Work presentation | Docs Viewer using Studio-generated Gallery inputs | Docs Viewer using Docs-owned Gallery inputs and Studio-generated Work/media facts |
| Selected public distribution | Docs Viewer Publish consumes completed Docs/Catalogue selections | Docs Viewer Publish continues to transfer completed selections |

The browser owns Gallery selection, Work search, membership choices, authoring feedback, sorting, counts and retained view state when the required data is loaded. Python owns confined persistence, the explicit source migration, required generated/public artifacts and transfer. Docs Viewer consumes completed Studio-generated Work/Series facts rather than opening Studio canonical records during ordinary Gallery management.

### Current Canonical Inputs

Repository-relative locations below describe the existing authority. The configured Docs workspace, not a repository fallback, must own the new Gallery sources. GO.0 will select their exact configuration entries and source paths before code changes; no target source location is implicitly created by this document.

| Current source | Contents and current owner | Migration treatment |
| --- | --- | --- |
| `studio/data/canonical/catalogue/works.json` | Studio Work records, including title, `series_id`, `medium`, `year`, `year_display`, media/source declarations and other Work metadata | Remains Studio-owned; date-field changes are separate |
| `studio/data/canonical/catalogue/series.json` | Studio Series definitions | Remains Studio-owned |
| `studio/data/canonical/catalogue/galleries.json` | Studio Gallery IDs/titles; `catalogue_source_galleries_v1` | Move sole authority into configured Docs Working source storage |
| `studio/data/canonical/catalogue/galleries-by-work.json` | Studio Work ID → Gallery ID arrays; `catalogue_source_galleries_by_work_v1` | Move sole membership authority with the definitions; preserve exact selections |
| `studio/data/canonical/catalogue/series-galleries.json` | Studio explicit Series → Gallery relevance arrays; `catalogue_source_series_galleries_v1` | Move with Galleries; preserve the existing navigation relationship independently of Work membership |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/source/collections/catalogue/documents/<work_id>.md` | Docs Viewer Catalogue document sources, generated from selected refreshed Works | Remain Docs-owned; Gallery membership does not depend on these documents existing |

Current source contracts are described by [Catalogue Source Model](../Catalogue_Source_Model.md). Gallery data already lives outside `works.json`, but its persistence and operation ownership are still coupled to Studio.

### Current Generated Data And Locations

The following inventory distinguishes producer ownership from physical storage. Studio writes consumer JSON inside the Docs workspace today; that location alone does not make its producer Docs Viewer.

In the table, `C` means `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. It is resolved by `docs-viewer/config/workspace/docs-workspace.json`. The inventory is a planning baseline, not a declaration that each saved artifact or deployed site has the same generation time.

| Current generated location | Producer and contents | Delivery treatment |
| --- | --- | --- |
| `C/works/index/<work_id>.json` | Studio Refresh; `work_record_v11` with Work metadata/media facts, optional `series_id`, and direct Gallery ID/title entries in `work.galleries` | Studio retains Work facts; remove its Gallery enrichment and adopt Docs-owned presentation composition through the affected consumers |
| `C/galleries/index/<gallery_id>.json` | Studio Refresh; `gallery_record_v3` with Gallery ID/title and `member_works` containing exact Work IDs/titles | Docs Viewer owns required Gallery output and its completion |
| `C/galleries/galleries_index.json` | Studio Refresh; `catalogue_galleries_index_v3`, Gallery ID/title lookup, including empty Galleries | Docs Viewer owns the Gallery lookup used by Media View link selection and later search |
| `C/series-galleries-index.json` | Studio Refresh; `catalogue_series_galleries_index_v2`, explicit Series → Gallery ID/title links | Docs Viewer owns the relationship projection |
| `C/reports/series-galleries/metadata.json` | Studio Refresh; private `catalogue_series_galleries_report_v3` rows with Series/Gallery labels, missing-side placeholders and Gallery Work counts | Move the report's data authority into Docs Viewer; decide whether this saved projection remains necessary once its browser has the relevant facts |
| `C/works/works_index.json` | Studio Refresh; `catalogue_works_index_v3`, compact Work IDs/titles | Remains a Studio-generated Work input; do not inflate this picker lookup into a general report dataset by default |
| `C/reports/catalogue-works/metadata.json` | Studio Refresh; private `catalogue_works_report_metadata_v3`, Work facts for local Catalogue Works/Medium reporting | Remains Studio-generated; supplies an existing local selection/report input where its fields are sufficient |
| `C/private/work-sources.json`, `C/private/work-resources.json`, `C/private/series.json` | Studio Refresh; portable Work placement/source facts, Work links/download filenames and Series definitions for local reports | Remain Studio-generated inputs with their current private boundary |
| `C/media-config.json` | Studio Refresh; shared public-safe image/thumbnail policy | Remains Studio-generated; Gallery edits produce no media |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/assets/works/{primary,thumbs,media/files}/` | Studio Save prepares Work image renditions, thumbnails and attachments under configured asset owners | Remains Studio-owned preparation; selected transfers retain the existing publication owner |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/collections/catalogue/documents/manage-manifest.json` and `manifest.json` | Docs Viewer Build and public-metadata projection; current list rows contain `doc_id`, `title`, `last_updated` and optional authored-thumbnail presence | Remain Docs-owned document listings; no new medium/date/Gallery search fields are delivered here |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/collections/catalogue/documents/by-id/<work_id>.json` | Docs Viewer Regenerate/Build; prepared Catalogue document content and semantic media references | Remain Docs-owned; update only affected presentation contracts/artifacts required by the ownership migration |
| `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/search/index.json` | Docs Viewer explicit Search build; site-search `docs_viewer_search_index_v4` | Unchanged by this delivery; Catalogue subdocuments remain excluded by current policy |

`docs-viewer/config/workspace/catalogue-artifacts.json` currently selects public Catalogue by-ID directories `works/index` and `galleries/index`, plus `media-config.json`, `series-galleries-index.json`, `works/works_index.json` and `galleries/galleries_index.json`. Private report and `private/` files are excluded.

Docs Viewer Publish transfers selected Catalogue artifacts to `$DOTLINEFORM_DOCS_BASE_DIR/preview/catalogue/` and the repository `site/assets/data/catalogue/`, preserving their selected relative paths. Catalogue document output has its separate configured owner: Working collection documents, Preview at `preview/collections/catalogue/documents/`, and repository output under `site/assets/data/docs/catalogue/`, including `manifest.json` and `by-id/`. Existing served Gallery paths need not move merely because their producer changes.

Gallery links also enter prepared document media presentations through Docs Viewer's static preparer, including output used by Publish, Export and Prepare package. Those consumers must resolve the new Gallery authority; changing only the live Media View reader is insufficient. [Catalogue Indexes And Payloads](../Catalogue_Indexes_And_Payloads.md), [Catalogue Media View](../Catalogue_Media_View.md) and [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) describe the current producer/consumer boundaries.

### Current Operation Coupling To Remove

Studio's single and bulk Work Save carry `gallery_ids` independently of the Work record, persist the membership map and select Gallery-related output. Gallery create/rename/delete and Series–Gallery edits select generated Gallery/relationship effects. Studio's editor also discovers newly empty Galleries after membership removal and offers a delete prompt. Empty Galleries themselves remain valid.

Studio mutation effects currently flow through `$DOTLINEFORM_DOCS_BASE_DIR/working/catalogue-updates-pending.json` (`catalogue_updates_pending_v5`). Gallery/Series selections, `created_galleries`, `gallery_member_works` and selected shared outputs contribute to Refresh. Completed public effects enter `working/catalogue-publish-pending.json`; Docs Viewer Regenerate consumes ready Work effects separately. Migrate relevant selections deliberately while preserving unrelated Work/media/document work; do not flush whole queues or introduce another publication ledger.

Work title changes/deletion and Series title changes/deletion remain genuine cross-owner inputs after the move. Carry exact affected identities and completed generated facts through the existing handoff so Docs Viewer can update affected Gallery labels, memberships and association/report output. Choose that handoff in GO.0. Do not retain Studio Gallery ownership as a convenience, rescan the canonical corpus during Gallery operations, or introduce polling, a general synchronization service or downstream agreement audits.

### Target Workflow

A local Docs Viewer Gallery management report owns Gallery create/rename/delete, viewing member Works, searching available Works, adding/removing selected memberships and editing the existing Series relevance links. Reuse existing generated Work/Series inputs and narrow report/selection components where they fit. The exact local host and whether the existing Series and Galleries report becomes the management entry point are GO.0 decisions.

Saving a Gallery change awaits its required persistence and preparation, returns completed effects and refreshes the affected local view. Public changes are selected for the existing Publish operation. Merely opening/reloading the report reads saved data. Studio Save/Refresh, document regeneration and Work media processing are not prerequisites for a Gallery-only edit.

Preserve Gallery IDs and existing authored Gallery references, direct versus Series-related links, Gallery Media View/Work navigation, empty-state behavior and Back behavior. Preserve the ability to keep an empty Gallery. Reconcile the old editor's empty-Gallery prompt explicitly during UI design rather than adding automatic deletion or assuming its choreography belongs in the new report.

The migration establishes one canonical Gallery source owner and one generation owner. Remove retired Studio Gallery controls, mutation paths and producer dependencies at cutover. Do not leave dual writers, canonical shadow copies, old-field readers, compatibility endpoints or hidden fallbacks.

## Deliverables

- Configured Docs-owned canonical Gallery definitions, Work memberships and Series associations, with an explicit migration preserving current identities and selections.
- A local Gallery management workflow over completed Studio-generated Work/Series inputs, with browser-owned choices and narrow persistence/preparation services.
- Docs-owned Gallery lookup/member/relationship output and related-link composition for live, prepared and public consumers.
- Removal of Gallery authoring and generation responsibilities from Studio while retaining Studio Work/Series operations and media preparation.
- An explicit affected-Work/Series handoff, selected publication effects and migration treatment for pending work and embedded prepared presentations.
- A current durable Gallery owner document at closeout, with affected existing ownership/configuration guidance corrected within this delivery's boundary.

## Process

1. Continue creating/editing Works and Series in Studio and completing their existing generated-data handoff.
2. Open local Docs Viewer Gallery management, choose or create a Gallery and use loaded Work data to inspect/add/remove exact members. Edit its title and optional existing Series relevance relationships there.
3. Save and await the Gallery operation's persistence, affected output preparation and local completion. Preview the Gallery through existing Media View.
4. Publish the completed selected Gallery/presentation effects through the existing Docs Viewer Publish action when explicitly requested. Public reading consumes finished output; it does not read local authoring sources.

## Delivery Steps

### GO.0 — Readiness And Implementation Agreement

- [ ] Confirm the complete ownership change against current authoring, generated Work enrichment, Gallery consumers and selected publication effects.
- [ ] Agree the configured Docs Gallery source boundary, local management entry point and required generated output; decide whether to retain or replace the private Series/Galleries report projection.
- [ ] Agree the narrow handoff for Work title/deletion and Series title/deletion effects, including the operation that completes dependent Gallery changes.
- [ ] Define the one-time source and queued-effect migration, affected prepared-document conversion and retirement of Studio Gallery writers; preserve unrelated pending effects.
- [ ] Confirm the management interactions, treatment of newly empty Galleries, required manual review and proportionate verification budget.
- [ ] Present the intended production change set and obtain implementation approval. Specify any proposed test work separately before creating or changing tests.

Verification budget: targeted read-only source/configuration and relevant saved-input inspection only. No prototype, mutation, migration, generation, runtime service or test execution is needed to decide readiness. Existing tests are not accepted evidence merely because their names mention Galleries.

Gate: proceed only with an agreed source owner, complete cross-owner handoff, bounded migration and implementation approval. Raise any need for wider Studio migration, new synchronization/recovery machinery or a new Search lifecycle before implementing it.

Record: proposed. Documentation inspection identified the current owners, paths, embedded Gallery links and affected mutation/queue boundaries. Exact target storage, UI composition, handoff completion and live migration remain undecided. No implementation or generated writes have occurred.

### GO.1 — Implement The Complete Ownership Change

- [ ] Implement Docs-owned persistence and the local Gallery management workflow, with browser-owned membership/association choices and selected completed effects.
- [ ] Move required Gallery generation and live/static presentation composition; update private report consumers without duplicate saved representations unless each has a concrete consumer need.
- [ ] Remove Gallery fields/controls and canonical/producer dependencies from Studio Work and Gallery operations, preserving ordinary Work/Series behavior and media completion.
- [ ] Implement the agreed affected-Work/Series handoff and adapt publication selection to the new Gallery producer without changing Publish into a builder or auditor.
- [ ] Prepare and review the explicit migration/conversion inputs and expected writes; execute live migration/generated follow-through only within the agreed write scope.
- [ ] Project changed public runtime files through the canonical-to-site inventory where applicable, inspect the exact tracked output and complete its required projection/site checks.
- [ ] Present local management, Media View and public-preview behavior for the owner's manual review; record individual observations and remaining omissions.

Verification budget: select exact changed-path Python/JavaScript lint, Python syntax, JSON parsing and whitespace checks after the implementation owners are known; expected local cost is seconds, without service or data writes. A bounded migration/generation diagnostic and the agreed single write conversion address preservation and current consumer wiring; identify exact targets, side effects and cost before execution. Public runtime changes require `bin/site-code-update`, exact projection review, `bin/site-code-update --check` and `bin/site-validate`. Existing test execution needs an inspected coverage selection and budget; creating/updating any tests, fixtures, harnesses or temporary regression scripts requires separate approval under [Test Contract Discipline](../Test_Contract_Discipline.md). UI design, selection feel and navigation receive manual review; no browser suite is automatically added or run.

Gate: one working Docs-owned Gallery workflow, no remaining Studio Gallery writer and a concrete reviewable migration with preserved identities, memberships, references and selected effects. Public Publish, deployment and Git actions retain their separate authorization; they are not implied by implementation approval.

Record: not started.

### GO.2 — Code And Redundancy Review

- [ ] Independently review final ownership, source migration, Studio removals, known-effect handoff, generated consumers, publication selection and prepared presentation changes.
- [ ] Complete the mandatory Redundancy And Defensive Behavior Review in Development Checklist, tracing normal, empty and unchanged operations and reused helpers beyond changed lines.
- [ ] Challenge repeated source/configuration reads, per-Work Gallery reads, complete-corpus scans, regenerated Work/media output, duplicate relationship/count data, schema audits of completed handoffs, fallback/compatibility branches and unrequested recovery policies.
- [ ] Retain and justify actual local-write authority, exact-target and path/symlink confinement, parsing/sanitization, missing-input failures and selected transfer checks at their owning boundaries.
- [ ] Record findings, removals and justified safeguards; resolve them and rerun only the evidence affected by corrections.

Verification budget: bounded final source/diff and selected generated-output review, reusing GO.1 evidence. No broad audit or suite follows automatically from review.

Gate: no unresolved finding that breaks the agreed ownership/workflow; completion claims match the actual migration, manual observations and public-data evidence.

Record: not started.

### GO.3 — Durable Ownership And Closeout

- [ ] Record accepted local management and reading behavior, completed migration/conversion and any still-separate publication/deployment state.
- [ ] Establish the durable Docs Viewer Gallery owner and correct the affected Studio source/output/lifecycle, Media View and workspace/public-inventory documentation; keep future medium/date/search design outside shipped documentation.
- [ ] Confirm retired Studio Gallery authorities are removed and one configured source remains, with ordinary Git/source recovery rather than aliases or automatic backups.
- [ ] Update Planned Features routing and retain the follow-on requirements below as proposed work.
- [ ] Present this delivery's retain-or-retire recommendation and durable destinations. Do not delete documentation without approval.

Verification budget: bounded documentation and final state/diff review; reuse completed implementation evidence. No Search rebuild or repeated full generation is a closeout requirement.

Gate: the complete Gallery ownership move is accepted and its durable owner is current. This prerequisite does not itself approve follow-on Catalogue work.

Record: not started.

## Follow-on

After this delivery, specify the Catalogue report improvements against Docs-owned Gallery data and Studio-generated Work facts. These are subsequent complete deliveries, not additional GO.1 scope.

- **Medium groups:** local Docs Viewer report assignment of distinct descriptive medium values to search/report groups such as Drawings, Paintings, Digital and Video. Groups support icon filters and remain separate from canonical Work metadata. Preserve exact authored medium descriptions; agree assignment cardinality and how unassigned media appear before implementation.
- **Single date text:** retain the current `year_display` content as the single authoritative free-text Work date and retire separately maintained numeric `year` through its Studio authoring/import/generated consumers. Derive ordering and year/range search interpretation in the browser, preserving the display text. Agree start/end ordering, abbreviated ranges, separate dates and suggestion semantics; ascending start-year ordering is a proposal, not an implemented rule.
- **Catalogue filtering and Gallery discovery:** prepare compact public-safe browsing data from the respective owners, with no per-Work loading merely to filter. Show a compact matching-Galleries section above matching Works, with clear type/count information and separate Work pagination. Gallery-title matches return Galleries rather than automatically expanding every member into Work results; specific Work queries retain useful direct matches. Medium/date filtering of Gallery results needs an explicit rule.

The current Catalogue document manifest is already Docs-generated and can be enriched or accompanied by a narrow report projection when that follow-on is specified. Medium mapping can be resolved in loaded browser data instead of duplicated into every row. Lightweight title/ID/description matching, structured filtering and derived date ordering are the agreed direction; these requirements do not justify a new full-text index, runtime search service, automatic site Search rebuild or changes to site-search collection coverage.
