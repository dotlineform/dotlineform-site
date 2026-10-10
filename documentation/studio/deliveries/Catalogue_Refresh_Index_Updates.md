---
draft: false
doc_id: d-20261010-143841-fba69a
title: Catalogue Refresh Index Updates
added_date: "2026-10-10 14:38:41"
last_updated: "2026-10-10 17:17:24"
summary: Gallery index count removed and Catalogue token pickers simplified to grey ID-first rows without subtitles; broader selected-row Refresh remains proposed.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Refresh Index Updates

## Outcome And Status

Make normal Refresh update the rows affected by supplied Catalogue mutations, preserving unaffected rows. Remove fields and dependency updates whose consumer benefit does not justify maintaining them. A single changed record should not trigger projection of the complete Catalogue or complete relationship report.

This is a proposed delivery, parented to [Planned Features](../Planned_Features.md), following the accepted [Gallery And Series Incremental Updates](Gallery_And_Series_Incremental_Updates.md). The user requested this proposal on 2026-10-10 and subsequently approved the Gallery count/subtitle cleanup first; that subset is delivered below. Broader row-update implementation, remaining field decisions and test work are not approved by that cleanup request. [Catalogue Save And Refresh](../Catalogue_Save_And_Refresh.md) and [Catalogue Indexes And Payloads](../Catalogue_Indexes_And_Payloads.md) own current behavior and receive the lasting changes at delivery.

The reason for this work is an operation whose scope follows its supplied changes. A measured slowdown is not a prerequisite for removing unnecessary rebuilding. Performance claims still require evidence; this proposal makes no measured speedup claim.

Paths starting with `working/` or `preview/` are relative to the configured `$DOTLINEFORM_DOCS_BASE_DIR`. Paths starting with `studio/`, `docs-viewer/` or `site/` are repository-relative. `<work_id>` and `<gallery_id>` stand for exact canonical identities. [Workspace configuration](../../../docs-viewer/config/workspace/docs-workspace.json) owns these locations.

## What Happens Currently

- v4 updates queue, `working/catalogue-updates-pending.json`, selects current/deleted Works, Galleries and Series, and exact shared output files.  
- **Refresh** writes:
    - selected Work records at `working/generated/catalogue/works/index/<work_id>.json` and 
    - Gallery records at `working/generated/catalogue/galleries/index/<gallery_id>.json`. 
- Selected aggregate builders construct:
    - the complete Works index (`working/generated/catalogue/works/works_index.json`),
    - Gallery index (`working/generated/catalogue/galleries/galleries_index.json`), 
    - Series–Gallery index (`working/generated/catalogue/series-galleries-index.json`) and 
    - private Series/Galleries report (`working/generated/catalogue/reports/series-galleries/metadata.json`). 
    - Unselected aggregate files are skipped.
    - Shared output is compared with saved content ignoring generation time; unchanged output retains its bytes and timestamp. This avoids unnecessary writes after complete construction, but does not avoid that construction.

The [generator](../../../studio/services/catalogue/generate_work_pages.py) projects every Work through the full scalar Work projection when the compact Works index is selected. After the Gallery count cleanup, it constructs a temporary member map only for selected Gallery by-ID output; index-only Refresh does not need that membership pass. For selected Gallery records it still builds a general Series/Work context, including Series titles, project-folder groups and Series membership maps, although the emitted member rows contain only Work identity, title and year fields.

The [Refresh owner](../../../studio/services/catalogue/catalogue_refresh_service.py), source loader and generator also repeat Gallery loading/validation: the Work/Series source loader reads and validates Galleries, Refresh reads them again, and the generator validates the loaded structures again. Full Work/Series source validation precedes projection. These passes must be assessed by their purpose, rather than automatically retained around a smaller row updater.

The private [Catalogue Works metadata producer](../../../studio/services/catalogue/catalogue_works_metadata.py) already replaces named Work rows in `working/generated/catalogue/reports/catalogue-works/metadata.json` and removes explicit deletions while preserving other rows. It is the data producer for the read-only Catalogue Works report; it does not edit canonical Catalogue data. It still parses and writes a complete aggregate file when needed.

Publish consumes completed Working output, retains unselected Preview output and applies selected destinations. This delivery changes Refresh construction, not that publication ownership.

## Consumer Findings And Proposed Field Decisions

### Gallery Counts

Before the cleanup, Gallery index `work_count`, in `working/generated/catalogue/galleries/galleries_index.json`, supplied an “N Work(s)” subtitle through the [Catalogue media-target service](../../../docs-viewer/services/docs_catalogue_media.py) to the [local Add Media View link picker](../../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js). The search target uses Gallery ID and title; the count did not determine Gallery identity, link resolution or member browsing. Gallery browsing continues to read `working/generated/catalogue/galleries/index/<gallery_id>.json` and its `member_works` rows.

**Implemented decision:** the picker count subtitle and persisted Gallery index `work_count` are removed. Gallery index rows contain only ID/title under `catalogue_galleries_index_v2`; the target reader requires that schema and emits empty Gallery metadata. Gallery membership changes update affected Gallery member output without selecting the Gallery search index. Gallery create, rename and delete still update that index. No count lookup, counter cache or v1 reader alias replaces the removed field. Aggregate header and Gallery by-ID member counts remain separately proposed for review.

### Compact Work Rows

The current Work index, `working/generated/catalogue/works/works_index.json`, supplies Work ID/title to the shared local Catalogue target lookup. Its exact consumers are:

- [Add/Edit Catalogue image](../../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js),
- [Add/Edit Media View link](../../../docs-viewer/runtime/js/management/source-editor/catalogue-media-modal.js),
- [document Work-subject selection](../../../docs-viewer/runtime/js/management/source-editor/subject-modal.js).
- Catalogue image and Work-subject selection offer Works only;
- Media View links offer Works and Galleries. Gallery targets come from `working/generated/catalogue/galleries/galleries_index.json` without subtitle metadata. Both Work-only pickers currently fetch the combined Work/Gallery lookup and filter it in the browser; this shared loading is not a reason to restore Gallery counts.

Explicit Catalogue design maintenance also uses the Work index's Work-ID inventory, then reads each selected Work's by-ID payload at `working/generated/catalogue/works/index/<work_id>.json`. The inspected production consumers do not use the compact index row's numeric `year` or `series_id`. Insert doc link reuses the list presentation component but reads a separate document-target lookup; it does not consume these Catalogue indexes. Other directives do not acquire a Catalogue lookup dependency merely because they are tokens.

**Proposed decision:** retain `work_id` and `title`; confirm the remaining compact-field decisions at implementation. The inspected consumers do not need index-row `year` or `series_id`; these fields remain in their authoritative and by-ID owners where used. A Series assignment change would no longer select the Work search index solely to maintain a duplicated Series identity. Project the retained compact fields directly, rather than constructing a full Work record and discarding most of it.

### Headers, Versions And Other Derived Fields

Review header `count` and content `version` in the aggregate index/report files identified above, separately from Gallery index row `work_count`. Some readers only validate their shape/self-consistency; the Python reader of `working/generated/catalogue/series-galleries-index.json` recomputes the complete content hash, while its browser reader validates identities and ordering without using that hash. A validation requirement is not, by itself, a product reason to persist a field.

Require a named consumer or a specific integrity requirement before retaining a derived field. Prefer deriving a display total from the already loaded map/list. Remove fields used only to validate their own duplication, updating producers and consumers together with explicit schema changes. Preserve a content version only where a concrete cache, comparison or integrity contract needs it; any retained complete-payload hash remains an explicitly acknowledged whole-file cost. Schema and successful generation time have separate contract/diagnostic purposes. Do not change Work image `media_version` as part of this review.

The readiness gate settles these aggregate-header decisions before implementation. It does not presume that every existing count/version must survive, or that every derived field must be removed. Header counts in `working/generated/catalogue/galleries/index/<gallery_id>.json` and the private report files need the same consumer-purpose review if their shaping changes in this slice.

## Proposed Normal Refresh

Read `working/catalogue-updates-pending.json` once. Load each required canonical authority once from `studio/data/canonical/catalogue/`: Work records in `works.json`, Series definitions in `series.json`, Gallery definitions in `galleries.json`, Work → Gallery membership in `galleries-by-work.json` and explicit Series → Gallery associations in `series-galleries.json`. Carry the loaded results through Refresh. Monolithic canonical files still require complete JSON parsing when needed; row updates do not make those reads random-access. Avoid loading an authority for an output that has no dependency on it.

Read each selected saved aggregate once. Validate the input envelope, exact identities and the rows/references consumed by the operation. Replace or remove rows using supplied identities and current authoritative values. Preserve unaffected rows and compare the old/new selected values to determine whether a write is needed. Serialize each changed aggregate once in its required deterministic order. An unchanged selected row must not lead to a timestamp-only write.

Keep one family-owned row projection and a straightforward merge into its saved map/list. The existing Works report updater is a useful pattern, not a requirement to introduce a generic patch engine, another queue or a database.

- **Works index — `working/generated/catalogue/works/works_index.json`:** upsert compact rows for queued current Works; remove queued deleted Works. Do not project other Works. The existing Work metadata flag is sufficient to select a candidate; row comparison handles changes outside the compact fields without a new per-field history.
- **Gallery index — `working/generated/catalogue/galleries/galleries_index.json`:** upsert ID/title for selected current Gallery definitions; remove selected deleted Galleries. Select the file only for retained-field changes. Other reasons to update a Gallery's member payload do not automatically select its search index.
- **Series–Gallery index — `working/generated/catalogue/series-galleries-index.json`:** replace the association list only for selected current Series; remove selected deleted Series. A Gallery rename/delete uses the old/new associated Series endpoints already captured by mutation owners. A current empty Series remains an explicit empty list. Work Series assignment and direct Gallery membership do not alter this independent relationship map.
- **Series/Galleries report — `working/generated/catalogue/reports/series-galleries/metadata.json`:** replace rows involving selected Series/Gallery endpoints and preserve unrelated rows. Use exact pair identity, plus empty-Series and unassociated-Gallery identities, in a temporary in-memory map. Re-evaluate empty/unassociated status only for affected definitions against current explicit associations. Capture both ends of removed pairs before mutation so the remaining endpoint's placeholder can be restored. This does not require a new persisted inverse index or association counter.
- **Gallery member rows — `working/generated/catalogue/galleries/index/<gallery_id>.json`, inside `member_works`:** merge queued current/deleted Work rows into existing selected Gallery records using final membership. Reproject only affected Work rows; preserve unrelated members. A Gallery rename changes its definition without reconstructing every member row. Initial creation constructs that new Gallery's actual members once. Remove the general Series/Work context from this compact projection.
- **Catalogue Works report — `working/generated/catalogue/reports/catalogue-works/metadata.json`:** retain selected-row updates through its existing owner. Apply agreed header simplification consistently; the report stays read-only and private.

Membership queries may still require a pass over the loaded Work → Gallery map or Series → Gallery associations. If needed, build only the relevant temporary lookup once per action, with its purpose explicit. Do not manufacture a persistent reverse map, background cache or change journal to avoid that pass. The removed Gallery count dependency eliminates the count-only pass for its search index.

## Queue Completion And Failure

Reuse the v4 queue families and selected output identities in `working/catalogue-updates-pending.json` and `working/catalogue-publish-pending.json`. No new queue file, row-patch queue or publication progress flag is proposed. An output selector and its identity families together supply the operation's candidates; an identity array alone does not select every index.

Keep two selections distinct within Refresh: unfinished Work handoff and pending shared-row candidates. A Work can already have `refreshed: true` when a later shared-output failure occurs. A rerun must still use that Work's queued identity for an unfinished shared index or Gallery-member update. Do not derive shared-row candidates solely from false Work readiness. Work IDs remain available until the owning shared Refresh succeeds; update the handoff ordering if necessary to guarantee that prerequisite before Regenerate removes them.

Upserting a current value and removing an explicit deletion are safe to repeat. Preserve completed effects on failure, retain unfinished shared selections and report the point reached. Forward completed public selections before removing them from updates; preserve the existing timestamps and per-Work publication progress owners. No automatic rollback, backups or recovery scans are added.

Missing or malformed saved aggregates fail visibly. They do not trigger a complete rebuild during ordinary Refresh. A separately invoked maintenance operation creates a baseline, repairs output or applies a global schema/projection change. It uses the same row projections, but has explicit whole-output authority. Empty new definitions must still be handled without inventing affected Works.

## Validation, Storage And Real Costs

Validate exact selected source records, retained output shape and referenced identities as they are used. Remove repeated reads/validation of the same loaded inputs. Global audits such as duplicate-title checks belong at canonical mutation boundaries and explicitly invoked complete validation; normal Refresh must not repeat a full corpus audit merely because one record changed. Extract focused validators where necessary rather than passing an artificial partial corpus to an existing complete validator. Before changing validation ownership, confirm that all canonical mutation owners enforce the relevant invariant; deliberate external canonical changes require the explicit validation/maintenance path.

One JSON aggregate remains one storage unit. Parsing the saved file, visiting its entries to establish a temporary keyed view, deterministic ordering and serialization can still scale with its size. A required membership query or retained content hash can also be a whole-input pass. The outcome is selected semantic projection and dependency work, not a claim of constant-time Refresh or an in-place JSON byte patch.

Do not add sharding, persistent indexes, a database or browser-side canonical access in this delivery. Reconsider storage only as a separate outcome if these acknowledged costs later warrant it. Avoid optional index reads/writes when their selected row values did not change.

## Scope And Cutover

This delivery covers normal Refresh's compact indexes, private relationship/report data and Gallery member-row projection, together with the mutation selectors and consumer changes required by the retained field decisions. Work media handoff, authored documents, Regenerate, Search and synchronous operation ownership keep their existing boundaries.

Read existing Working aggregates and the selected canonical authorities; update the selected aggregates/Gallery records and private reports at the paths above. Public publication still receives complete finished JSON files through `working/catalogue-publish-pending.json` and the existing snapshot owner. Public counterparts keep the same relative filenames beneath `preview/catalogue/` and tracked `site/assets/data/catalogue/`; for example, `working/generated/catalogue/works/works_index.json` supplies `preview/catalogue/works/works_index.json` and `site/assets/data/catalogue/works/works_index.json`. Private `reports/catalogue-works/metadata.json` and `reports/series-galleries/metadata.json` remain Working-only. No browser or Publish applies row patches. Public artifact-inventory reduction is a separate proposal: the current Work/Gallery lookup consumers are local, but this slice does not silently remove files from published ownership.

Field removals require explicit output schema changes and one agreed baseline conversion of affected files. Keep both queue schemas at v4 if their fields/meaning remain unchanged. Use a completed lifecycle baseline for cutover, update producers/readers together and regenerate only the outputs whose contracts changed. Do not regenerate media, documents or Search for an index-only conversion. Old schema readers, optional legacy fields and fallback generation are not end-state compatibility paths.

## Delivery Steps

[x] **RI-UI — Gallery Count And Subtitle Cleanup:** user approved this subset on 2026-10-10. Generator, target reader and membership-change selection are updated; a focused Refresh from empty queues converted only the Working Gallery index to v2 and queued it for the next Publish. Changed-source lint, syntax and source review passed. The production reader accepted all 300 ID/title rows and returned empty Gallery subtitle metadata while retaining Work year metadata. No tests, browser interaction or Publish ran. Restart the owning services and reload their pages for manual modal review. Broader steps below remain proposed.

[x] **RI-UI-2 — Catalogue Token Picker Rows:** user requested grey ID-first rows, removal of visible type labels and Work year subtitles in Catalogue image and Media View link on 2026-10-10. Both Add/Edit modes now opt into the shared picker's ID/title layout; its default presentation remains with subject/document-link callers. Two changed JavaScript modules passed lint and bounded source review; whitespace checks passed. Local source-editor CSS supplies the two-column layout; the follow-up uses the search icon's theme colour and the smaller caption font size for IDs. These management modules/styles are outside the public projection inventory. No generated data, queues, tests or browser interaction were changed/run for this UI subset; force-reload Docs Viewer for manual visual review.

[x] **RI-UI-3 — Numeric ID Search:** user requested searches that ignore leading zeroes on 2026-10-10. The shared `semantic-token-targets.js` matcher normalises numeric IDs and numeric query tokens for identity comparisons, including type-qualified and prefix matching, while retaining exact-match priority and existing title matching. Catalogue image, Media View link and Work-subject selection share this behaviour. Canonical/displayed IDs and saved token identities retain their leading zeroes. Changed-source lint, bounded source review and whitespace checks passed; no generated data, queues, tests or browser interaction were changed/run. Force-reload Docs Viewer for manual review.

**RI-0 — Readiness:**

- agree the bounded row-update outcome, consumer-backed field removals, validation ownership and cutover.

Gate: the user approves the implementation slice and the Gallery subtitle/header decisions are explicit. Read-only review has identified current consumers and repeated construction; no runtime changes have been made.

[ ] **RI-1 — Implement:**

- simplify retained projections/dependencies and add selected map/list updates through the existing Refresh owners.

Gate: a one-record change performs no unrelated row projection or complete aggregate reconstruction; reruns retain the required candidates and empty/deleted relationship endpoints remain correct.

[ ] **RI-2 — Verify:**

- agree proportionate evidence for preserved unrelated rows, exact deletions, unchanged-row writes, relationship placeholders and a shared failure after Work readiness.
- New or changed test code needs a separately approved specification under [Test Contract Discipline](../Test_Contract_Discipline.md), maintained outside this delivery.

Gate: selected evidence and remaining limits are recorded; existing tests are inspected before relying on them. Browser presentation remains user review unless an automation boundary is separately approved.

[ ] **RI-3 — Cutover And Closeout:**

- apply the agreed output-only baseline conversion, confirm the picker and Refresh behavior, and transfer current contracts to the durable owners.

Gate: the complete outcome is accepted, schema/publication consequences are accounted for and no implicit full-rebuild fallback remains. Live Publish, Git actions and public deployment retain their explicit-action boundaries.

Current record: Gallery count/subtitle cleanup is implemented and its focused Working conversion completed at `2026-10-10T14:35:54Z`. Only `galleries/galleries_index.json` was written; no Work/report/media handoff was selected. The updates queue is empty and the publication queue selects that Gallery index, preserving its prior Work-publication timestamp. No canonical data, documents, Search, Preview or repository public payloads were changed, and no tests, browser interaction, Publish, commit or push ran. Remaining row-update and field/header proposals are unchanged.
