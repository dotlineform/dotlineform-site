---
draft: false
doc_id: d-20260519-202931-b05d27
title: Catalogue Indexes And Payloads
added_date: "2026-05-19 20:29:31"
last_updated: "2026-10-10 19:35:17"
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
| `works/works_index.json` | Compact Work identities and titles for Catalogue target lookup |
| `galleries/galleries_index.json` | Compact Gallery identities and titles for Add Media View link search |
| `series-galleries-index.json` | Exact Series IDs mapped to associated Gallery IDs/current titles, including an empty list for a Series without associations |
| `reports/work-document-coverage/manifest.json` | Private refreshed Series IDs/titles and member Work IDs for local documentation coverage, including empty Series |
| `private/work-sources.json` | Shared private Work placement, titles, optional Series identity and portable source declarations |
| `private/work-resources.json` | Shared private Work identities/titles, authored links and exact download filenames |
| `private/series.json` | Shared private Series definitions, including empty Series |

Work thumbnails and primary renditions are shared local assets under `$DOTLINEFORM_DOCS_BASE_DIR/assets/works/`, prepared by Save rather than stored in the generated JSON tree. Private Catalogue Works and Series–Gallery report metadata also live beneath Working generated Catalogue output, outside the public Catalogue artifact inventory. The retired Works collection title metadata has no current producer or consumer.

`reports/series-galleries/metadata.json` uses `catalogue_series_galleries_report_v1` with a content-versioned header, generation time, row count and `rows`. Each row has `series: {series_id, title} | null` and `gallery: {gallery_id, title} | null`. The producer uses the same in-memory mapping emitted to `series-galleries-index.json`, adds current Series titles from the already validated records, includes every Series with no Galleries and appends every unassociated Gallery. No row has two null cells. [The focused report owner](../../studio/services/catalogue/catalogue_series_galleries_report.py) owns projection and saved-row validation; the existing Catalogue generator writes it during explicit Refresh. It requires neither new public Series files nor a runtime canonical/title join. [Reports](Reports.md) owns display and exact Gallery Media View behavior.

`reports/work-document-coverage/manifest.json` uses `catalogue_work_document_coverage_v1`, with only schema and generation time in its header. Its `series` array contains exact `series_id`, `title` and ascending distinct `work_ids`, ordered by Series ID and including empty Series. Refresh projects it only when membership or Series-definition changes select it; Work title/year/media and Gallery-only edits do not. [Its focused owner](../../studio/services/catalogue/catalogue_work_document_coverage.py) builds the minimal facts and validates the saved file. Docs Viewer serves it through the read-only local `/docs/work-document-coverage` endpoint, without reading canonical records. It stays outside the public artifact inventory and publication queue. [Works Report](Works_Report_Concept_And_Architecture.md) owns the browser join with generated Context documents.

## Shared Private Report Inputs

[The Catalogue report-input owner](../../studio/services/catalogue/catalogue_report_inputs.py) serializes and validates the three `private/` aggregates independently of any final report output. Each payload has exactly `header` and its record map; the header contains only `schema` and `generated_at_utc`, supporting Refresh's existing comparison that ignores generation time. Maps use exact identity keys and repeat the same identity in each row. They contain no absolute workspace roots, public URLs, media revisions, counts or content hashes.

| Input/schema | Record contract | Consumers |
| --- | --- | --- |
| `work-sources.json` / `catalogue_work_sources_v1` | `works` map; required `work_id` and `title`; optional `series_id`, `media_source_id`, `project_folder`, `project_subfolder` and `project_filename`, preserving authored declarations and their absence/null values where valid | Projects, Uncataloged Images, Missing Source Files, Folders Without Works |
| `work-resources.json` / `catalogue_work_resources_v1` | `works` map; `work_id`, `title`, `links: [{label, url}]` and `download_filenames: [filename]`; arrays retain authored order and may be empty | Work Links, Work Downloads |
| `series.json` / `catalogue_series_definitions_v1` | `series` map; `series_id` and `title` for every definition, including Series without Works | Projects |

Every Work remains in both Work aggregates. Physical existence never decides whether a source declaration or download reference is projected. Saved-input readers validate only their own minimal schema and facts, resolve the configured Working Catalogue root and open those files once. Reports do not read canonical Catalogue records, generate missing inputs or borrow another report's metadata. Missing or invalid inputs fail with the owning Refresh instruction; [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md#private-report-input-maintenance) documents explicit repair of an unselected input. Runtime configuration continues to own media-root resolution and each report retains its separate live filesystem scope.

These files are absent from `catalogue-artifacts.json`, Preview, repository distribution and publication selections. Studio's general Catalogue output route rejects `private/`; only local report services consume the saved files. [Reports](Reports.md) owns their joins and presentation. Work Document Coverage retains its separate manifest.

## Work And Gallery Projections

Each Work may have one Series or no Series, and zero or more direct Gallery memberships; empty Series and Galleries remain valid in canonical Catalogue data. The producer reads Gallery identities/titles from canonical `galleries.json` and Work membership from `galleries-by-work.json`. `work.galleries` is always an array of `{gallery_id, title}` entries, ordered by Gallery ID; absent memberships produce `[]`. Gallery records contain `gallery: {gallery_id, title}` and exact Work ID/title-only `member_works` rows. Member rows read the already loaded canonical Works map directly; Gallery generation builds no Series/Work context, enriched Work copies or project-folder groups. Work year fields remain in canonical Work records and full by-ID payloads. The separate canonical `series-galleries.json` owns explicit Series–Gallery relevance pairs, independent of Work membership after its one-time seed. Refresh derives `series-galleries-index.json` from those pairs and current Gallery titles, keyed by every valid Series ID and ordered by Series and Gallery ID. It has no Work member lists or per-Work related arrays. No image paths, rendition arrays or canonical inverse membership map are duplicated. There is no Catalogue publication filter, primary-Work requirement, Recent projection or Catalogue Search output in this producer. Generated Series by-ID records and the compact Series member-Works index remain retired; no Gallery relationship is inferred from Series membership.

The Work search index at `working/generated/catalogue/works/works_index.json` contains a `works` map keyed by exact Work ID, with each entry containing only `work_id` and `title`, ordered by Work ID. Catalogue image, Media View link and document Work-subject selection search this generated lookup by ID/title. Explicit Catalogue design maintenance uses its Work-ID inventory, then reads selected by-ID payloads. Index rows are projected directly from canonical ID/title without constructing full Work records. Work create/delete/title changes select the index; year and Series-only changes do not. Year, year-display and Series identity remain in their canonical and by-ID owners where used.

The Gallery search index at `working/generated/catalogue/galleries/galleries_index.json` contains a `galleries` map keyed by exact Gallery ID, with each entry containing only `gallery_id` and `title`. It includes empty Galleries, orders keys by Gallery ID and carries no member lists or persisted Work counts. Add Media View link searches this generated lookup by ID/title through the Catalogue media-target service, then reads the selected Gallery's individual record. Work and Gallery target metadata are empty. Catalogue image, Media View link and Work-subject selection show grey ID-first rows without type labels or subtitles. Gallery create/rename/delete selects this index; Work membership changes update affected Gallery member records without selecting it. The generator builds a temporary member lookup only when Gallery by-ID records are selected.

`studio/services/catalogue/generate_work_pages.py` owns the complete projection. `catalogue_series_galleries.py` validates and reads the canonical pair authority; `catalogue_generation_records.py` and `catalogue_generation_indexes.py` own Work/Gallery record and index shaping. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns refresh and cleanup.

## Exact Identity And Versions

Work payloads use `work_record_v11`. Each contains only `header` and `work`; the header carries schema, content version and generation time, while `work.work_id` carries the exact Work identity. The retired Detail count, sections and `documents` array are absent, and the header does not duplicate the Work ID. Gallery payloads use `gallery_record_v3`; their headers contain exactly `schema`, `generated_at_utc` and `gallery_id`, with no member count or content version. Local and public readers require v3, the exact three header fields with a nonempty generation time, and exactly `work_id`/`title` per member, without an older-schema fallback. Member totals come from the already loaded list; Gallery generation computes no payload hash. Index headers use `catalogue_works_index_v2`, `catalogue_galleries_index_v2` and `catalogue_series_galleries_index_v1`; index counts are their entry counts, including all valid Series in the Series–Gallery index. Work index v2 removes row `year`, `year_display` and `series_id`; Gallery index v2 removes row `work_count`. Both lookup readers require v2 and exact ID/title rows, with no v1 fallback. Shared media policy uses `catalogue_media_config_v1` with a content version and generation time.

The 2026-10-10 Work compact-field cleanup passed changed-source lint and syntax checks. From empty v4 queues, a focused Refresh wrote only `works/works_index.json` and queued that file for publication. The production lookup reader accepted all 4,619 Work ID/title rows and the existing 300 Gallery rows; Work and Gallery lookup metadata are empty. No tests, browser interaction or Publish ran for this cleanup. Restart Local Studio and the Docs management service and reload their pages to adopt the changed Python modules. Preview/repository counterparts advance through the next explicit Publish.

The Gallery header cleanup converted only the 300 current Working Gallery by-ID records, containing 4,619 member references. The strict production reader accepted every v3 record and its three-field header. Changed-source lint/syntax, public projection check and site structural validation passed; no tests or browser interaction ran. The user subsequently confirmed Publish, closing the v3 cutover gate.

Detail folders and their discovery indexes are retired. Active generation neither recreates an empty Detail index nor scans retired thumbnails. Series `sort_fields` is retired; both Studio's Series lookup and consumer members use ascending exact Work IDs. No relationship is inferred from a document, title, route or thumbnail filename.

Where emitted, content versions include schema and projected content. Normal Refresh and the standalone generator compare projected content directly while ignoring generation time, so unchanged Gallery output retains its bytes without a persisted hash. A generation timestamp alone does not force a rewrite. Publish verifies artifact bytes separately from payload fields. Confirmed per-image `media_version` is separate from the payload version.

## Media And Documents

Every Work represents a primary image. Records retain exact Work identity, `media_version`, `width_px` and `height_px`; they contain no `media.primary` or `media.thumbnails` arrays or image-presence flags. Former Details become ordinary Works with renamed Catalogue media, unchanged original project paths and unchanged media versions. Work downloads retain their individual filenames and projected remote URLs.

`catalogue_media_policy.py` projects only consumer-safe fields from `_data/pipeline.json` and `site-tools/config/site-tools.json`: primary widths, suffix and Work image base, format, media-version query naming, and thumbnail sizes/suffix. It supplies no `preferred_width` and no private source paths or encoding commands. Refresh Catalogue regenerates the policy with complete JSON generation. Route configuration supplies the local or public thumbnail base; it does not duplicate rendition sizes or filename rules.

The shared Docs Viewer resolver constructs filenames from policy and exact identity. Responsive candidates use actual width descriptors capped at source width, with duplicate widths removed because the producer does not upscale. Raw-image links use the largest configured filename independently of the embedded resource. Thumbnail existence reporting and reconciliation enumerate expected derivatives from canonical records and pipeline policy, independently of consumer JSON arrays. The shared media-policy change preserved filenames; the separately owned Gallery conversion renames former Detail media into the Work family while preserving bytes and versions. [Catalogue Media View](Catalogue_Media_View.md) owns responsive display and reader behavior.

Work `documents` arrays and their URL/title normalization are retired as of 2026-10-07. Refresh omits the field rather than emitting an empty placeholder. Docs Viewer document relationships belong to the separate Links owner and render through Related links; neither Work JSON nor the proposed Catalogue Entry maintains a second relationship list. Studio does not derive document associations or choose a canonical document. Catalogue prose has no parallel Markdown source or `content_html` field.

## Consumer Boundaries

Studio Work and Series search, focused records and Gallery definitions read live canonical service projections. The historical `studio/data/generated/catalogue-lookup/` files are retired and removed; the live API payload builders remain. Studio serves shared local thumbnails through the configured `/docs/assets/` route; `/studio/catalogue-output/` serves generated Catalogue data and private report metadata.

Local Docs Viewer reads the latest refreshed Work and Gallery records, shared media configuration and `/docs/catalogue-series-galleries` through its Catalogue service; Work reads include direct Gallery memberships. Exact Gallery tokens and Work Gallery links open the individual Gallery through `/docs/catalogue-gallery?gallery_id=<gallery_id>`. Series remains a canonical Catalogue grouping, without a generated Series by-ID reader or Media View target. Studio edits Gallery definitions, Work memberships and explicit Series–Gallery pairs through the Works editor. `docs-viewer/config/workspace/catalogue-artifacts.json` selects the new index with the other Catalogue JSON for Preview and repository distribution; the public reader uses `/assets/data/catalogue/series-galleries-index.json` from route configuration. Refreshing local Catalogue data alone does not deploy it. The frozen legacy payloads under `site/archive/` have their own historical shape and are outside active generation.

Change the owning serializer and focused evidence when a demonstrated consumer need changes this contract. Keep source-only metadata, Studio lookup fields and future publication dependencies under their respective owners.
