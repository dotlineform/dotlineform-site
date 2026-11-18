---
draft: false
doc_id: d-20260605-125108-c68916
title: Generated Data Contracts
added_date: "2026-06-05 12:51:08"
last_updated: "2026-11-18"
summary: Public and manage Docs Viewer payload schemas, registered publication roots, read authority, publishing, and builder ownership contracts.
parent_id: d-20260331-000000-c313fd
---
# Docs Viewer generated data contracts

The workspace configuration selects local and public read locations. Manage reads Working output or local services. Public reads data from the deployed snapshot and configured media bases. Docs Review reads its package. [Working generation and publication](Builder.md) · [Projection contract](Projection_Contract.md)

## Workspace provider contract

Manage and Public compose the same provider with an explicit `docs_viewer_config_v4` workspace. It resolves routes and collection owners for document, Index, Search and Recent reads. Generated-data transport owns reads and retries. The optional Source adapter supplies authoring methods for Manage, where services enforce write capability. Related Links belongs to the built document payload. The local Links report uses its own saved aggregate. [Workspace provider](../../docs-viewer/runtime/js/shared/docs-viewer-workspace-provider.js) · [Related Links](Related_Links.md) · [Runtime](Docs_Viewer_Runtime.md)

### Catalogue Reference And Presentation

The optional `catalogue` document envelope uses `docs_catalogue_presentation_v1`. Its ordered `references` contain `reference_id`, exact `target: {kind, id}`, `presentation` (`entry`, `image` or `media`) and authored `options` where applicable. Media openers carry the literal label. Images retain caption choice, restricted summary HTML, placement, width and optional left size. Entry is identity-only at source.

A Catalogue document's `catalogue.work` holds its adopted facts, `entry`, `image`, `full_image`, optional `series_id` and ordered `galleries`. Gallery references carry ID, label and direct/Series relation. Entry resources carry label, kind and exact download identity or external URL. Regenerate adopts refreshed Work and Gallery facts. The reader resolves filenames using configured media bases and opens the exact selected Work or Gallery in Media View. Selected publication and static consumers use the same adopted Work inputs. [Projection code](../../docs-viewer/services/docs_catalogue_projection.py) · [Media View](Catalogue_Media_View.md) · [Catalogue lifecycle](Catalogue_Save_And_Refresh.md)

## Current Payload Roots

| Reader or artifact | Ordinary Docs | Portfolio Search |
| --- | --- | --- |
| Manage / Working | `working/generated/documents/` | `working/generated/search/` |
| Applied Preview | `preview/documents/` | `preview/search/` |
| Site-preview / Public | `site/assets/data/docs/` | `site/assets/data/search/analysis/` |

Working/Preview paths are relative to the configured Docs workspace. Each named collection has configured document and media roots. Working generates eligible public views alongside local management metadata. Publish applies their queued bytes to Preview and distribution. [Workspace config](../../docs-viewer/config/workspace/docs-workspace.json) · [Eligibility and queue](Builder.md#publish-preparation)

## Local Generated Reads

Ordinary Working reads use the [GET dispatcher](../../docs-viewer/services/docs_management_read_service.py) and [generated-read helpers](../../docs-viewer/services/docs_generated_reads.py). They resolve configured output without modifying source/generated files or adding operation logs.

| Request | Saved input |
| --- | --- |
| `GET /docs/index-tree` | Ordinary Working `index-tree.json`, including drafts |
| `GET /docs/doc?doc_id=<id>` | Exact immutable-ID `by-id/<id>.json`; resolution does not consult the tree or follow its `content_url` |
| `GET /docs/recent` | Saved `recent.json`, currently v3 |
| `GET /docs/search?search-scope=<scope>` | The configured Search artifact for that discovery scope; default Portfolio |
| `GET /docs/workspace-links` | Configured saved aggregate for the diagnostic Links report |
| `GET /docs/generated/external/<collection>/…` | Only `manage-manifest.json` or `by-id/<id>.json` beneath that configured collection output, with collection-specific identity validation |

Ordinary generated requests reject retired workspace selectors and the collection selector; collection output uses its configured artifact route. Ordinary JSON helpers require an object and report missing/malformed files. The collection file route confines the selected existing JSON path and serves its bytes. Source metadata has its separate management read owner. [Local service map](Endpoint_Overview.md)

Reads preserve saved discovery and document state. Recover missing output through its owning Build rather than using a read as generation. Local HTTP revalidation can return unchanged bytes through the browser cache; [caching](Docs_Viewer_Runtime.md#local-http-caching) is separate from source/publication eligibility.

## Collection Manifest Ownership

Working `manage-manifest.json` has the complete saved rows for an owner. Public `manifest.json` carries eligible reader rows. Both have a root `docs` array. Book management also carries its authored order and private edition/provenance fields. Exact builds merge selected rows into saved metadata. Complete collection builds project all current rows. Media presence contributes `has_thumbnail: true`; the field is otherwise omitted. Context rows may carry `catalogue_targets` (`work_ids`, `gallery_ids`) for Media View links. [Collection builder](../../docs-viewer/build/docs_builder/collection.py) · [Public metadata](../../docs-viewer/services/docs_publication_metadata.py) · [Context link inputs](Catalogue_Media_View.md#what-links-appear)

## List Date Projections

Collection manifests carry `added_date` and `last_updated` at day precision. Markdown and by-ID payloads keep full timestamps. **Last added** uses the addition day, with same-day rows ordered by title and identity. Undated entries follow dated entries. Selected and Search metadata use the update day. Ordinary Index uses authored order. [Date provenance](Document_Identity.md#date-provenance)

## Index-tree.json contract

Ordinary navigation is nested `docs` under `generated_at` and `schema`. Nodes carry `doc_id`, `title`, non-empty `children`, applicable `ui_status` and `report_id` on hosts. The adapter derives parent IDs from the tree. The Working `index-tree.json` additionally carries boolean `draft` and includes draft nodes. Working writes the eligible `public-index-tree.json` beside it. Publish uses that output as the deployed `index-tree.json`. A changed projection advances its generation time. Readers fetch selected document metadata by ID.

## By-ID payload contract

The by-ID payload represents one document and its rendered body. It carries exact timestamps and authored `summary` where supplied. `summary_html` contains the completed restricted-emphasis paragraphs for the Summary block and Info panel. An eligible ordinary or non-Catalogue by-ID document retains `draft: false`. Catalogue omits that field. A host's `report` descriptor carries its `id`, with `collection` only for `docs_collection`. The Index carries the smaller `report_id` field. [Summary](Builder.md#summary-block) · [Reports](Reports.md#build-and-payload-flow)

## Search contract

The reader loads the active scope. Manage uses `/docs/search` with `search-scope`; Public uses the configured static index family. Changed scope files are queued separately and Publish transfers their saved bytes. [Search index contract](Reader_Discovery_And_Return.md#payload-contract)

## Recent Contract

`docs_recent_v3` carries `schema`, `limit`, `generated_at` and `docs`. It selects up to 20 eligible additions from Context, Concepts, Moments and Catalogue Galleries with eligible hosts. It applies exact Recent exclusions to document targets. It sorts by addition day with title and identity breaking ties. The reader keeps the saved order. Document rows carry `doc_id`, `title`, `timestamp`, `collection`, `report_doc_id` and `collection_title`. Gallery rows carry `kind: catalogue-gallery`, `id`, `title` and `timestamp`. Both use the addition day as `timestamp`.

**Refresh Search and Recent** uses saved metadata and one Gallery read. Full Working Build supplies metadata it has just generated. An ordinary complete document Build can also generate Recent from saved portfolio collection and Gallery inputs. Targeted document operations preserve it. Changed Recent completion queues the exact file, and Publish copies those bytes. [Recent producer](../../docs-viewer/services/docs_recent_payload.py) · [Recent exclusions](Source_Organisation.md#recent-exclusions) · [Working rebuild](Builder.md#working-rebuild)

## Document package inputs

The package helpers `source_context`, `source_records` and `rendered_content` read the configured source and its rendered content for direct package workflows. They have their own input contract independently of the reader indexes and saved payloads. [Prepare package](Document_Packages.md)
