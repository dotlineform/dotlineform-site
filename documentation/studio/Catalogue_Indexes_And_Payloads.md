---
draft: false
doc_id: d-20260519-202931-b05d27
title: Catalogue Indexes And Payloads
added_date: "2026-05-19 20:29:31"
last_updated: "2026-10-10 15:56:00"
parent_id: d-20260401-000000-a11bf3

---

# Catalogue Indexes And Payloads

## Generated Read Models

Refresh Catalogue owns the complete replaceable consumer output beneath `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`:

| Relative path | Contents |
| --- | --- |
| `media-config.json` | Shared primary-image and thumbnail rendition policy projected from the pipeline and site media configuration |
| `works/index/<work_id>.json` | Work metadata, optional `series_id`, direct Gallery IDs/titles in `work.galleries`, links, downloads and image facts |
| `galleries/index/<gallery_id>.json` | Independent Gallery ID/title and lightweight `member_works` in ascending Work-ID order |
| `works/works_index.json` | Compact Work identities, labels and Series membership |
| `galleries/galleries_index.json` | Compact Gallery identities and titles for Add Media View link search |
| `series-galleries-index.json` | Exact Series IDs mapped to associated Gallery IDs/current titles, including an empty list for a Series without associations |

Work thumbnails and primary renditions are shared local assets under `$DOTLINEFORM_DOCS_BASE_DIR/assets/works/`, prepared by Save rather than stored in the generated JSON tree. Private Catalogue Works and Series–Gallery report metadata also live beneath Working generated Catalogue output, outside the public Catalogue artifact inventory. The retired Works collection title metadata has no current producer or consumer.

`reports/series-galleries/metadata.json` uses `catalogue_series_galleries_report_v1` with a content-versioned header, generation time, row count and `rows`. Each row has `series: {series_id, title} | null` and `gallery: {gallery_id, title} | null`. The producer uses the same in-memory mapping emitted to `series-galleries-index.json`, adds current Series titles from the already validated records, includes every Series with no Galleries and appends every unassociated Gallery. No row has two null cells. [The focused report owner](../../studio/services/catalogue/catalogue_series_galleries_report.py) owns projection and saved-row validation; the existing Catalogue generator writes it during explicit Refresh. It requires neither new public Series files nor a runtime canonical/title join. [Reports](Reports.md) owns display and exact Gallery Media View behavior.

Each Work may have one Series or no Series, and zero or more direct Gallery memberships; empty Series and Galleries remain valid in canonical Catalogue data. The producer reads Gallery identities/titles from canonical `galleries.json` and Work membership from `galleries-by-work.json`. `work.galleries` is always an array of `{gallery_id, title}` entries, ordered by Gallery ID; absent memberships produce `[]`. Gallery records contain `gallery: {gallery_id, title}` and compact Work ID/title/year/year-display `member_works` rows. The separate canonical `series-galleries.json` owns explicit Series–Gallery relevance pairs, independent of Work membership after its one-time seed. Refresh derives `series-galleries-index.json` from those pairs and current Gallery titles, keyed by every valid Series ID and ordered by Series and Gallery ID. It has no Work member lists or per-Work related arrays. No image paths, rendition arrays or canonical inverse membership map are duplicated. There is no Catalogue publication filter, primary-Work requirement, Recent projection or Catalogue Search output in this producer. Generated Series by-ID records and the compact Series member-Works index remain retired; no Gallery relationship is inferred from Series membership.

The Gallery search index at `working/generated/catalogue/galleries/galleries_index.json` contains a `galleries` map keyed by exact Gallery ID, with each entry containing only `gallery_id` and `title`. It includes empty Galleries, orders keys by Gallery ID and carries no member lists or persisted Work counts. Add Media View link searches this generated lookup by ID/title through the Catalogue media-target service, then reads the selected Gallery's individual record. Gallery target metadata is empty. Add/Edit Catalogue image and Media View link show grey ID-first rows without type labels or subtitles; Work year metadata remains available in the lookup for document-subject selection. Gallery create/rename/delete selects this index; Work membership changes update affected Gallery member records without selecting it. The generator builds a temporary member lookup only when Gallery by-ID records are selected.

`studio/services/catalogue/generate_work_pages.py` owns the complete projection. `catalogue_series_galleries.py` validates and reads the canonical pair authority; `catalogue_generation_records.py` and `catalogue_generation_indexes.py` own Work/Gallery record and index shaping. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns refresh and cleanup.

## Exact Identity And Versions

Work payloads use `work_record_v11`. Each contains only `header` and `work`; the header carries schema, content version and generation time, while `work.work_id` carries the exact Work identity. The retired Detail count, sections and `documents` array are absent, and the header does not duplicate the Work ID. Gallery payloads use `gallery_record_v1`; their headers also carry the exact Gallery ID and member count. Index headers use `catalogue_works_index_v1`, `catalogue_galleries_index_v2` and `catalogue_series_galleries_index_v1`; index counts are their entry counts, including all valid Series in the Series–Gallery index. Gallery index v2 removes row `work_count`; the target reader requires v2 and exact ID/title rows, with no v1 fallback. Shared media policy uses `catalogue_media_config_v1` with a content version and generation time.

The 2026-10-10 Gallery count/subtitle cleanup passed changed-source lint, syntax and bounded source review. From empty v4 queues, a focused Refresh wrote only `galleries/galleries_index.json` and queued that file for publication. The current generated index contains 300 ID/title rows under v2; the production target reader returned Gallery `meta: []` and retained a Work's year metadata. No tests, browser interaction or Publish ran for this cleanup; modal presentation remains for user review. Restart Local Studio and the Docs management service and reload their pages to adopt the changed Python modules. Preview/repository counterparts advance through the next explicit Publish.

Detail folders and their discovery indexes are retired. Active generation neither recreates an empty Detail index nor scans retired thumbnails. Series `sort_fields` is retired; both Studio's Series lookup and consumer members use ascending exact Work IDs. No relationship is inferred from a document, title, route or thumbnail filename.

Content versions include schema and projected content. A generation timestamp alone does not force a rewrite. Confirmed per-image `media_version` is separate from the payload version.

## Media And Documents

Every Work represents a primary image. Records retain exact Work identity, `media_version`, `width_px` and `height_px`; they contain no `media.primary` or `media.thumbnails` arrays or image-presence flags. Former Details become ordinary Works with renamed Catalogue media, unchanged original project paths and unchanged media versions. Work downloads retain their individual filenames and projected remote URLs.

`catalogue_media_policy.py` projects only consumer-safe fields from `_data/pipeline.json` and `site-tools/config/site-tools.json`: primary widths, suffix and Work image base, format, media-version query naming, and thumbnail sizes/suffix. It supplies no `preferred_width` and no private source paths or encoding commands. Refresh Catalogue regenerates the policy with complete JSON generation. Route configuration supplies the local or public thumbnail base; it does not duplicate rendition sizes or filename rules.

The shared Docs Viewer resolver constructs filenames from policy and exact identity. Responsive candidates use actual width descriptors capped at source width, with duplicate widths removed because the producer does not upscale. Raw-image links use the largest configured filename independently of the embedded resource. Thumbnail existence reporting and reconciliation enumerate expected derivatives from canonical records and pipeline policy, independently of consumer JSON arrays. The shared media-policy change preserved filenames; the separately owned Gallery conversion renames former Detail media into the Work family while preserving bytes and versions. [Catalogue Media View](Catalogue_Media_View.md) owns responsive display and reader behavior.

Work `documents` arrays and their URL/title normalization are retired as of 2026-10-07. Refresh omits the field rather than emitting an empty placeholder. Docs Viewer document relationships belong to the separate Links owner and render through Related links; neither Work JSON nor the proposed Catalogue Entry maintains a second relationship list. Studio does not derive document associations or choose a canonical document. Catalogue prose has no parallel Markdown source or `content_html` field.

## Consumer Boundaries

Studio Work and Series search, focused records and Gallery definitions read live canonical service projections. The historical `studio/data/generated/catalogue-lookup/` files are retired and removed; the live API payload builders remain. Studio serves shared local thumbnails through the configured `/docs/assets/` route; `/studio/catalogue-output/` serves generated Catalogue data and private report metadata.

Local Docs Viewer reads the latest refreshed Work and Gallery records, shared media configuration and `/docs/catalogue-series-galleries` through its Catalogue service; Work reads include direct Gallery memberships. Exact Gallery tokens and Work Gallery links open the individual Gallery through `/docs/catalogue-gallery?gallery_id=<gallery_id>`. Series remains a document Subject and canonical Catalogue grouping, without a generated Series by-ID reader or Media View target. Studio edits Gallery definitions, Work memberships and explicit Series–Gallery pairs through the Works editor. `docs-viewer/config/workspace/catalogue-artifacts.json` selects the new index with the other Catalogue JSON for Preview and repository distribution; the public reader uses `/assets/data/catalogue/series-galleries-index.json` from route configuration. Refreshing local Catalogue data alone does not deploy it. The frozen legacy payloads under `site/archive/` have their own historical shape and are outside active generation.

Change the owning serializer and focused evidence when a demonstrated consumer need changes this contract. Keep source-only metadata, Studio lookup fields and future publication dependencies under their respective owners.
