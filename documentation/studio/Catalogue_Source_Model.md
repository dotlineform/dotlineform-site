---
draft: false
doc_id: d-20260519-000000-a0da45
title: Catalogue Source Model
added_date: "2026-05-19 00:00:00"
last_updated: "2026-10-12 20:09:28"
parent_id: d-20260401-000000-a11bf3

---
# Catalogue Source Model

## Canonical Families

Catalogue authoring source lives below `studio/data/canonical/catalogue/`:

| Family | Canonical location | Owns |
| --- | --- | --- |
| Works | `works.json` | Work identity, one Series membership, descriptive metadata, project-media references, downloads, links and media version |
| Series | `series.json` | Series identity and title |
| Galleries | `galleries.json` | Independent Gallery IDs and titles |
| Gallery membership | `galleries-by-work.json` | Sole canonical Work → Gallery ID arrays; no copied titles |
| Series–Gallery associations | `series-galleries.json` | Explicit Series → Gallery relevance arrays, independent of Work membership |

`studio/services/catalogue/catalogue_source.py` owns exact fields, normalization, omit-empty rules, serialization and validation. Works and Series use schema v2 with schema-only headers. Readers consume their record maps without count validation; serializers emit no record totals. Catalogue prose has no parallel Markdown source family.

`catalogue_galleries.py` owns the Gallery schemas `catalogue_source_galleries_v1` and `catalogue_source_galleries_by_work_v1`. Both headers contain only `schema`; readers and writers impose no record-count or complete-coverage requirement. Gallery records contain exactly `gallery_id` and `title`. IDs are exact strings, using at least three digits for Galleries and five digits for Works. Membership arrays contain distinct known Gallery IDs; missing Work entries mean no memberships. Missing source files, unknown Work/Gallery IDs and invalid headers fail validation. No membership is inferred from matching Series IDs.

`catalogue_series_galleries.py` owns `catalogue_source_series_galleries_v1`. Its header contains only `schema`; readers and writers impose no association-count requirement. `pairs_by_series` contains explicit Gallery ID arrays keyed by exact Series ID. Canonical validation checks current definition identities and sorted, unique relationships.

## Relationships And Identity

- Each Work has a stable `work_id` and exactly one `series_id` identifying an existing Series.
- Empty Series are valid. Series membership is held on Works; changing membership never requires a replacement member or deletion.
- Catalogue membership, document subjects, document `parent_id` and token composition are independent. None establishes another relationship.
- Catalogue Works and Series have no `status` or `published_date`. Series have no `primary_work_id` or `series_type`.
- A Work may belong to multiple independent Galleries, including Galleries spanning Series. The initial Series overview Galleries retain their original selections; later Series membership changes do not synchronise them.
- Former Details became ordinary Works. Canonical Detail data, schemas, source helpers and the completed one-time converter are removed. No parent identity, section order or former-parent Gallery association is retained.

## Metadata And Ordering

Project-media references identify a configured source, project folder, optional direct subfolder and filename without storing an absolute path. `media_source_id` is omitted for the configured default. Dimensions and `media_version` remain maintained media fields. Downloads and links remain optional Work-owned arrays. Supplied downloads identify a filename and explicit staging state; supplied links identify a URL. The UI supplies valid authored labels and complete resource input. Label completion belongs to UI authoring, not canonical model validation, and neither establishes that bytes or remote destinations are available. Save serialization and resource effect comparison, public Work generation and private Work Links projection/readers consume supplied filenames, URLs and labels unchanged, without repeated authoring-completeness checks, coercion, trimming, leading-apostrophe removal or substitute text. Missing required input surfaces at the operation that consumes it.

An omitted resource field means no entries; an explicit field must be an array of objects. Explicit nulls, other non-arrays and non-object entries fail instead of becoming empty arrays or being dropped. The Studio resource reader checks only this representation for the records actually consumed, without a complete Catalogue audit. Save copies every entry, while download staging state remains server-owned. The editor copies authored fields for draft comparison and Save without re-normalizing or filtering them. New/batch server baselines omit these optional fields rather than initializing them; the UI draft uses empty arrays for its list controls. Canonical serialization retains its existing omission of genuinely empty arrays. The private Work Resources input does not repeat the editor's nonempty-URL check; the browser retains URL-safety checks, and file-processing owners retain basename/path, upload/reference, byte-limit and required-file checks.

The approved 2026-10-12 one-time cleanup removed 2,678 existing `links: null` fields from `works.json`, preserving every actual link/download entry and all other source values. Absence now represents those empty groups explicitly; runtime readers have no null-to-empty compatibility fallback. This representation-only cleanup requires no resource-generation or publication effects.

Series and Gallery members use ascending `work_id` order. Series `sort_fields` and the Series editor's sort field are retired. The shared ordering calculation feeds both Studio's exact Series lookup and generated Series member records.

Series source records contain only `series_id` and a non-empty `title`. Series `year` and `year_display` are retired from canonical data, validation, field inventory, generated Series records/indexes and the Series Media View caption. Work dates remain Work-owned, including dates displayed on Series member rows.

## Save And Delete

Ordinary Create/Save/Delete services check their request and operation requirements and use the existing source transaction writer without complete canonical family audits. Work persistence trusts UI-authored metadata and Series/Gallery choices; individual creation checks exact ID spelling/collision and existing saves require exact targets. Series Create/Save retain their target/identity and nonblank-title checks; Save checks the Series revision, and a combined Series/member write checks each supplied Work target and revision. Single and multiple Work deletion use exact selected IDs and remove only those Works' membership entries, preserving unrelated references. Series deletion retains its revision and saved-member guard. Gallery deletion retains its definition revision and complete saved-member confirmation. Required file envelopes, path/write confinement, local media completion and known-effect queues remain operation requirements. Reading, merging and serializing complete JSON maps or inspecting membership to determine an operation's scope are not complete validation audits.

The single/New Work Series field displays its selected title and ID in the search box. Typing searches for a replacement; choosing an exact result updates the one `series_id`. Leaving or cancelling an uncommitted search restores the selected label. Series has no separate selected pill.

The Work editor has a left-hand Series browser above a scrollable Member Works list, beside the existing Work search, metadata and preview panels. It reuses the loaded canonical Work/Series search projections and the shared thumbnail/ID/title record list. Choosing a Series filters by exact saved `series_id`; it changes browsing context only, with no Series Open/New actions or membership writes. Choosing a Work loads that exact record into the editor, with confirmation before discarding unsaved changes. Opening a Work directly initially seeds the browser from its saved Series; a subsequently chosen browsing Series stays independent of the Work's assignment. Saved Work titles and membership changes update the list from the returned canonical records. The wider layout applies only to this local route; on narrower editor columns the preview moves below the metadata form.

An edit icon beside the browser's Series search opens a title-only modal with OK, Cancel and New. Existing Series load their current title and revision before editing; OK saves that exact Series through the ordinary save/output flow. New clears the modal title and switches to creation without writing until OK. Creation uses the next numeric ID suggested from a fresh canonical search lookup, and the service rejects a collision. A saved new Series becomes the browsing context with an empty member list. Series title saves update the browser and Work picker labels while preserving the current Work draft and membership. Empty titles are disabled, errors remain visible, and pending saves block dismissal. The standalone Series editor route, modules, page text and dedicated styling are retired; Series management now belongs to the Work editor.

A delete icon beside Edit is enabled only for a selected Series with no saved member Works, while the editor is available. It previews and confirms the exact Series deletion; the service rechecks the record revision and required-Series membership rule before writing. Success removes the Series from search and clears the browser selection. The current Work draft is preserved and revalidated, including any unsaved assignment to the deleted Series. Output failures remain visible after the canonical deletion.

The Work editor places a multiple-selection Galleries field below Series for single and New Work editing. It searches canonical `galleries.json` by title or exact ID and displays removable selected pills. The service reads current membership from `galleries-by-work.json`; the editor sends UI-validated replacement `gallery_ids` separately from the Work record. Persistence checks the array representation without another endpoint/duplicate audit or membership revision comparison. Metadata and membership changes share one canonical transaction; clearing the selection removes that Work's membership entry. Gallery IDs/titles are never copied into `works.json`. Bulk Gallery editing uses the same canonical membership owner.

Save completes required local media after the canonical transaction and returns current canonical records and revisions to the editor. Membership reassignment updates canonical source immediately; generated Work, Series, Gallery and Docs metadata readers update on explicit Refresh Catalogue. A local media or editor-response failure preserves the saved canonical change and reports incomplete Save completion. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the workflow.

Deleting a Series with assigned Works is blocked by the required-Series rule; reassign those Works first. Deleting one or multiple Works removes their current entries from `galleries-by-work.json` in the same canonical transaction; Refresh Catalogue later removes obsolete generated records and updates former memberships. Work deletion leaves Gallery/Series definitions and shared media intact. The Studio Detail browser, section service, Detail read target and Detail mutation paths are retired. Studio's write context allows Works, Series, Gallery definitions and Work Gallery memberships. Bulk creation of ordinary Works belongs to a separate delivery.

Canonical files use stable schema headers and deterministic record ordering. Optional empty fields follow the source serializer's omission rules. Volatile write timestamps belong in operation logs, not source records.

## Validation And Field Changes

### Catalogue Source Audit

A complete canonical audit checks every record or relationship in its supplied families, including identities unrelated to any selected authoring action. The **Catalogue source audit** is the existing read-only CLI; run it deliberately from the repository root after external canonical edits, during model/configuration maintenance or when diagnosing source integrity:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py
```

The default source directory is `studio/data/canonical/catalogue/`. `--source-dir <path>` selects another existing source directory, resolved relative to the command's working directory when relative. There is no family selector: each invocation reads and audits all five stores listed under Canonical Families.

- Work/Series validation checks allowed record fields, normalized identities and map-key agreement, exactly one existing Series reference per Work, configured media-source identity, required positive whole-number media versions and explicit image/download staging booleans. Optional downloads/links may be omitted; explicit fields must have array/object representation (including rejecting null) and a nonempty filename/URL respectively. The explicit audit does not check label completeness.
- Gallery validation checks exact IDs, definition shape/identity, nonempty trimmed titles and every Work–Gallery membership's representation, distinct Gallery IDs and existing endpoints. Duplicate Gallery titles remain valid.
- Series–Gallery validation checks exact existing definition endpoints and sorted, unique, nonempty relationship arrays and sorted Series keys.

Successful validation prints the source location, Work/Series counts and `Validation passed.` and exits `0`. Reported validation errors print `Validation failed:` and their messages, then exit `1`; missing/unreadable/malformed input stops with a nonzero error. Gallery and relationship audits report their first failure each. The command writes no canonical data, generated artifacts or queues, scans no media directories, checks no download bytes and makes no remote URL/network requests. It does not run Refresh, Regenerate, Search or Publish. Python imports may populate local ignored bytecode caches.

Ordinary Create/Save/Delete and normal queue-selected Refresh never invoke the complete audit functions. Explicit repair commands retain the following audits before projecting their selected output family:

| CLI selection | Complete canonical audit scope |
| --- | --- |
| `catalogue_json_build.py --write --private-report-inputs` | All Works and Series |
| `catalogue_json_build.py --write --work-document-coverage` | All Works and Series |
| `catalogue_json_build.py --write --compact-indexes` | All Works/Series and Gallery definitions/memberships |
| `catalogue_json_build.py --write --series-galleries` | All five canonical stores |
| `catalogue_json_build.py --write --gallery-records` | All five canonical stores |

The full repair command shape is `python3 studio/services/catalogue/catalogue_json_build.py --write <one-repair-flag>`, using the project interpreter. These are mutually exclusive write operations, not read-only audit selectors; their queue prerequisites and Working/output/publication handoffs remain documented under [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#refresh-boundary). Running `catalogue_json_build.py --write` without a repair selector performs normal queued Refresh without complete canonical audits. No automatic audit schedule or new command alias is introduced.

### Field Changes

Work imports require `series_id` and reject retired Work columns.

When changing a field, update its source definition, serializer, validation, editor and affected read projections together. The [Catalogue Field Registry](Catalogue_Field_Registry.md) inventories current source fields and output families; it does not plan Save or own serialization.

Work `provenance` and `artist` are retired. Neither field belongs in canonical `works.json`, the Work editor, create/save requests, bulk updates or generated Work projections. The 2026-10-07 retirement removed both keys from all 4,618 canonical Works, including the one populated provenance value; all artist values were empty. Other metadata and Work identities remain intact.

`medium` is the single descriptive text field for a Work's materials, process and support. The 2026-10-07 migration renamed each corrected `medium_caption` value to `medium` and removed `medium_type` from all 4,618 Works. It preserves descriptions exactly and deliberately retires the separate category distinction. The editor, request validation, field inventory, Work JSON, private report and document/Media View metadata use only `medium`, without old-field aliases. The Medium migration introduced `work_record_v10`; the private Works report uses `catalogue_works_report_metadata_v2` and one expanded Medium column.

Generated Work JSON now uses `work_record_v11`, retiring the unused `documents` array and its URL/title normalization. The field was generated-only and always empty; no canonical data or editor field needed migration. Document relationships retain their separate Docs Viewer Links authority. Work `series_id` remains available to Media View for Series-related Gallery resolution.

## Output Boundary

Ordinary Studio Catalogue production is available. Save maintains canonical source and required local Work media; Refresh Catalogue reconciles generated Work, Series and Gallery records, indexes and private Docs metadata beneath `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. The generator reads both canonical Gallery sources, writes individual `galleries/index/<gallery_id>.json` records and embeds Gallery IDs/titles in `work.galleries`. Gallery changes appear in current and former member Works after Refresh. Download staging resolves through `catalogue/media-staging/` under the configured Projects workspace; ready thumbnails use shared Docs `assets/works/thumbs/`. Docs Viewer reads the refreshed Gallery lookup and individual records for exact Gallery tokens, search and Media View. The historical `studio/data/generated/catalogue-lookup/` files are retired and removed; Studio lookup APIs read live canonical projections.

Refresh Catalogue is the explicit local generated-reader action; there is no separate media-publish or per-record publication action. Full JSON maintenance is available without media conversion or upload. The frozen site and media archive remain outside active writes. Docs Publish owns public acceptance; Save alone does not make a record public or refresh Docs semantic lookups, and Publish does not run Refresh or enforce its receipt.

Generated output is replaceable data, not another canonical source. The Work/Series source model contains only those two record maps. Detail serialization, parsing, validation, sorting and transaction expansion are removed, along with the unused generated Detail projection and Detail field-registry families. Studio's focused Work projection contains no Detail sections. Historical test fixtures still describe the retired Detail model and require separately agreed test maintenance; [Catalogue Per-Work Detail Source](Catalogue_Per_Work_Detail_Source.md) records that evidence boundary.

## One-time Gallery Conversion

The completed Gallery conversion allocated Work IDs in exact Detail UID order and section Gallery IDs in exact section-ID order, then wrote canonical Works, Series, Galleries and memberships. Its reviewed plan recorded source hashes and exact local and R2 media mappings. This migration bookkeeping is historical, not a current canonical relationship. The one-time converter and its helpers have been removed. Current Catalogue changes use Save and Refresh Catalogue; any future migration needs its own reviewed plan and implementation.
