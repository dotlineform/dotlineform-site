---
draft: false
doc_id: d-20260519-000000-a0da45
title: Catalogue Source Model
added_date: "2026-05-19 00:00:00"
last_updated: "2026-10-07 17:11:09"
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

`studio/services/catalogue/catalogue_source.py` owns exact fields, normalization, omit-empty rules, serialization and validation. Works and Series use schema v2. Catalogue prose has no parallel Markdown source family.

`catalogue_galleries.py` owns the Gallery schemas `catalogue_source_galleries_v1` and `catalogue_source_galleries_by_work_v1`. Both sources have a schema/count header. Gallery records contain exactly `gallery_id` and `title`. IDs are exact strings, using at least three digits for Galleries and five digits for Works. Membership arrays contain distinct known Gallery IDs; missing Work entries mean no memberships. Missing source files, unknown Work/Gallery IDs and inconsistent headers fail validation. No membership is inferred from matching Series IDs.

## Relationships And Identity

- Each Work has a stable `work_id` and exactly one `series_id` identifying an existing Series.
- Empty Series are valid. Series membership is held on Works; changing membership never requires a replacement member or deletion.
- Catalogue membership, document subjects, document `parent_id` and token composition are independent. None establishes another relationship.
- Catalogue Works and Series have no `status` or `published_date`. Series have no `primary_work_id` or `series_type`.
- A Work may belong to multiple independent Galleries, including Galleries spanning Series. The initial Series overview Galleries retain their original selections; later Series membership changes do not synchronise them.
- Former Details became ordinary Works. Canonical Detail aggregate files are retired and rejected by the runtime loader; the completed one-time converter that read them has been removed. No parent identity, section order or former-parent Gallery association is retained.

## Metadata And Ordering

Project-media references identify a configured source, project folder, optional direct subfolder and filename without storing an absolute path. `media_source_id` is omitted for the configured default. Dimensions and `media_version` remain maintained media fields. Downloads and links remain optional Work-owned arrays.

Series and Gallery members use ascending `work_id` order. Series `sort_fields` and the Series editor's sort field are retired. The shared ordering calculation feeds both Studio's exact Series lookup and generated Series member records.

Series source records contain only `series_id` and a non-empty `title`. Series `year` and `year_display` are retired from canonical data, validation, field inventory, generated Series records/indexes and the Series Media View caption. Work dates remain Work-owned, including dates displayed on Series member rows.

## Save And Delete

Services validate the combined canonical state and use the existing source transaction writer. Saves and deletes use opaque server-issued record revisions; a stale edit is rejected. A combined Series/member save checks the Series and every changed Work before writing either family.

The single/New Work Series field displays its selected title and ID in the search box. Typing searches for a replacement; choosing an exact result updates the one `series_id`. Leaving or cancelling an uncommitted search restores the selected label. Series has no separate selected pill.

The Work editor has a left-hand Series browser above a scrollable Member Works list, beside the existing Work search, metadata and preview panels. It reuses the loaded canonical Work/Series search projections and the shared thumbnail/ID/title record list. Choosing a Series filters by exact saved `series_id`; it changes browsing context only, with no Series Open/New actions or membership writes. Choosing a Work loads that exact record into the editor, with confirmation before discarding unsaved changes. Opening a Work directly initially seeds the browser from its saved Series; a subsequently chosen browsing Series stays independent of the Work's assignment. Saved Work titles and membership changes update the list from the returned canonical records. The wider layout applies only to this local route; on narrower editor columns the preview moves below the metadata form.

An edit icon beside the browser's Series search opens a title-only modal with OK, Cancel and New. Existing Series load their current title and revision before editing; OK saves that exact Series through the ordinary save/output flow. New clears the modal title and switches to creation without writing until OK. Creation uses the next numeric ID suggested from a fresh canonical search lookup, and the service rejects a collision. A saved new Series becomes the browsing context with an empty member list. Series title saves update the browser and Work picker labels while preserving the current Work draft and membership. Empty titles are disabled, errors remain visible, and pending saves block dismissal. The standalone Series editor route, modules, page text and dedicated styling are retired; Series management now belongs to the Work editor.

A delete icon beside Edit is enabled only for a selected Series with no saved member Works, while the editor is available. It previews and confirms the exact Series deletion; the service rechecks the record revision and required-Series membership rule before writing. Success removes the Series from search and clears the browser selection. The current Work draft is preserved and revalidated, including any unsaved assignment to the deleted Series. Output failures remain visible after the canonical deletion.

The Work editor places a multiple-selection Galleries field below Series for single and New Work editing. It searches canonical `galleries.json` by title or exact ID and displays removable selected pills. The service reads current membership from `galleries-by-work.json`; the editor sends replacement `gallery_ids` separately from the Work record, with `expected_gallery_ids` holding the loaded membership set. Save rejects stale membership, duplicates and unknown Gallery IDs before writing. Metadata and membership changes share one canonical transaction; clearing the selection removes that Work's membership entry. Gallery IDs/titles are never copied into `works.json`. Bulk Gallery editing uses the same canonical membership owner.

Save completes required local media after the canonical transaction and returns current canonical records and revisions to the editor. Membership reassignment updates canonical source immediately; generated Work, Series, Gallery and Docs metadata readers update on explicit Refresh Catalogue. A local media or editor-response failure preserves the saved canonical change and reports incomplete Save completion. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the workflow.

Deleting a Series with assigned Works is blocked by the required-Series rule; reassign those Works first. Deleting a Work removes its entry from `galleries-by-work.json` in the same canonical transaction; Refresh Catalogue later removes its obsolete generated record and updates former memberships. Shared or remote media cleanup is separate. The Studio Detail browser, section service, Detail read target and Detail mutation paths are retired. Studio's write context allows Works, Series, Gallery definitions and Work Gallery memberships. Bulk creation of ordinary Works belongs to a separate delivery.

Canonical files use stable schema headers and deterministic record ordering. Optional empty fields follow the source serializer's omission rules. Volatile write timestamps belong in operation logs, not source records.

## Validation And Field Changes

Run the read-only canonical validator with:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/validate_catalogue_source.py
```

It checks allowed fields, exact IDs and map keys, required Series membership, media metadata and the two canonical Gallery sources. Work imports require `series_id` and reject retired Work columns.

When changing a field, update its source definition, serializer, validation, editor and affected read projections together. The [Catalogue Field Registry](Catalogue_Field_Registry.md) inventories current source fields and output families; it does not plan Save or own serialization.

Work `provenance` and `artist` are retired. Neither field belongs in canonical `works.json`, the Work editor, create/save requests, bulk updates or generated Work projections. The 2026-10-07 retirement removed both keys from all 4,618 canonical Works, including the one populated provenance value; all artist values were empty. Other metadata and Work identities remain intact.

## Output Boundary

Ordinary Studio Catalogue production is available. Save maintains canonical source and required local Work media; Refresh Catalogue reconciles generated Work, Series and Gallery records, indexes and private Docs metadata beneath `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`. The generator reads both canonical Gallery sources, writes individual `galleries/index/<gallery_id>.json` records and embeds Gallery IDs/titles in `work.galleries`. Gallery changes appear in current and former member Works after Refresh. Download staging resolves through `catalogue/media-staging/` under the configured Projects workspace; ready thumbnails use shared Docs `assets/works/thumbs/`. Docs Viewer reads the refreshed Gallery lookup and individual records for exact Gallery tokens, search and Media View. The historical `studio/data/generated/catalogue-lookup/` files are retired and removed; Studio lookup APIs read live canonical projections.

Refresh Catalogue is the explicit local generated-reader action; there is no separate media-publish or per-record publication action. Full JSON maintenance is available without media conversion or upload. The frozen site and media archive remain outside active writes. Docs Publish owns public acceptance; Save alone does not make a record public or refresh Docs semantic lookups, and Publish does not run Refresh or enforce its receipt.

Generated output is replaceable data, not another canonical source. Empty internal Detail maps and residual consumer contracts remain outside the retired Studio editor boundary; they do not load old source data or resolve old identities to converted Works. Studio's focused Work projection contains no Detail sections.

## One-time Gallery Conversion

The completed Gallery conversion allocated Work IDs in exact Detail UID order and section Gallery IDs in exact section-ID order, then wrote canonical Works, Series, Galleries and memberships. Its reviewed plan recorded source hashes and exact local and R2 media mappings. This migration bookkeeping is historical, not a current canonical relationship. The one-time converter and its helpers have been removed. Current Catalogue changes use Save and Refresh Catalogue; any future migration needs its own reviewed plan and implementation.
