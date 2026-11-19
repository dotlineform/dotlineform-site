---
draft: false
doc_id: d-20260519-202931-b05d27
title: Catalogue Indexes And Payloads
added_date: "2026-05-19 20:29:31"
last_updated: "2026-11-18"
parent_id: d-20260519-000000-a0da45

---
# Catalogue Indexes and Payloads

Studio Refresh owns replaceable generated records, selected by the updates queue. Regenerate adopts exact Work facts into Docs Viewer. Public reads the adopted Catalogue documents and selected public artifacts. Use [Catalogue lifecycle](Catalogue_Save_And_Refresh.md) to follow a selection across those handoffs.

## Generated Read Models

Paths are relative to `working/generated/catalogue/` in the configured Docs workspace.

| Path | Data and consumer |
| --- | --- |
| `works/index/<work_id>.json` | Refreshed Work metadata, direct Galleries, Series identity, links/downloads and image facts. Working input for Regenerate. |
| `galleries/index/<gallery_id>.json` | Exact Gallery title and lightweight `member_works` rows. Public and Working Media View consume `gallery_record_v3`. |
| `works/works_index.json`, `galleries/galleries_index.json` | Compact ID/title maps. Gallery picker reads the Gallery index. The active Docs Source chooser gets Work rows from the adopted Catalogue management manifest. |
| `galleries/report-search.json` | Gallery titles, optional descriptions and markers, and direct Gallery memberships by Work. Used by Catalogue collection browsing and search. |
| `series-galleries-index.json` | Exact Series-to-Gallery IDs and current titles including Series with no associations. Used in Work adoption and available in Public. |
| `media-config.json` | Shared portable primary and thumbnail rendition rules. |
| `private/work-sources.json`, `private/work-resources.json`, `private/series.json` | Private reusable report inputs. |
| `reports/catalogue-works/metadata.json`, `reports/series-galleries/metadata.json` | Private report-specific read models. |

The public inventory contains Gallery records and named system files. Work by-ID handoff JSON and private report inputs remain in Working. Public Work metadata is part of the Catalogue document. [Inventory](../../docs-viewer/config/workspace/catalogue-artifacts.json) · [Catalogue target lookup](Document_And_Catalogue_References.md#catalogue-target-lookup) · [Public payload](Generated_Data_Contracts.md#catalogue-reference-and-presentation)

## Shared Private Report Inputs

| Input and schema | Rows and consumers |
| --- | --- |
| `work-sources.json` / `catalogue_work_sources_v1` | `works` map with exact Work identity/title, optional Series and source/folder/filename declarations. Projects, Uncataloged Images and Missing Source Files. |
| `work-resources.json` / `catalogue_work_resources_v1` | `works` map with exact Work identity/title, authored-order links and download filenames. Work Links and Work Downloads. |
| `series.json` / `catalogue_series_definitions_v1` | `series` map with all definitions, including Series without Works. Projects. |

The shared inputs preserve the saved declarations independently of filesystem existence. Their headers hold schema and generation time. Selected Refresh merges affected rows and keeps unchanged bytes and time. Missing required saved inputs call for explicit maintenance. `catalogue_works_report_metadata_v3` carries a schema header and Work map. The private `catalogue_series_galleries_report_v3` carries exact Series/Gallery rows with a Gallery direct-member count and placeholders for empty Series or unassociated Galleries. The public Series–Gallery relationship index carries links without counts. [Report inputs](../../studio/services/catalogue/catalogue_report_inputs.py) · [Repair commands](Catalogue_Save_And_Refresh.md#private-report-input-maintenance) · [Reports](Reports.md)

## Work And Gallery Projections

Gallery records preserve the producer's Work-ID order. Media View sorts already-loaded rows by title for browsing. A title/membership mutation can select exact changed member rows. Existing Gallery Refresh preserves other members; a queued new Gallery projects the complete initial membership. An unchanged record keeps its generation timestamp and bytes. Gallery title and Series relevance are separate from direct membership, and a title change can require refreshing Work facts and relationship rows without rebuilding member rows. [Gallery record producer](../../studio/services/catalogue/catalogue_gallery_records.py) · [Reader behaviour](Catalogue_Media_View.md#gallery-presentations)

Refresh copies authored titles, metadata, resources and source declarations as supplied by their authoring owners. Downstream projections preserve values rather than inventing defaults. Work storage and private source details stay out of public Work presentation. `header.version` compares the saved Work payload's content. `media_version` tracks changes to stored image renditions. Both remain distinct from the retired browser response hash.

## Media And Documents

The Work payload includes `width_px`, `height_px` and `media_version`. The shared media policy supplies actual filename/rendition rules, so records need no per-image rendition arrays. Route configuration supplies the asset roots. Responsive display accounts for the source width. Gallery target rows use lightweight IDs/titles and load full Work documents only on selection. Exact Work records carry no parallel document relationships. Related Links remains with Docs Viewer. [Media View](Catalogue_Media_View.md) · [Related Links](Related_Links.md) · [Publication destinations](Catalogue_Save_And_Refresh.md#storage-and-selection)
