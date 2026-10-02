---
draft: false
doc_id: d-20260605-125108-c68916
title: Generated Data Contracts
added_date: "2026-06-05 12:51:08"
last_updated: "2026-10-03 00:44:36"
summary: Public and manage Docs Viewer payload schemas, registered publication roots, read authority, publishing, and builder ownership contracts.
parent_id: d-20260331-000000-c313fd
---
# Docs Viewer Generated Data Contracts

This document records generated-data ownership for [Docs Viewer Runtime Boundary](Docs_Viewer_Runtime.md).
It separates public read-only route data from local/manage route data so payload-size and management-safety decisions have a durable home.

## Ownership Rules

- Public routes load only public-reader data needed for navigation, selected-document rendering, search, Recent, and reader-facing metadata.
- Manage routes may load manage generated data and local-service data, but manage needs should not force public payloads to carry management/tooling metadata.
- Public and manage payload names and shapes should be explicit route contracts, not incidental current renderer requirements.
- The workspace provider is the feature-facing collection-read owner. The generated-data runtime remains the read transport/retry owner; backend writes and management capability truth remain in management services.
- There should be no compatibility fallback to retired public payloads once a route contract has moved.
- Data Sharing document source-context reads are not generated-data runtime reads; they use Docs Viewer-owned helpers over the configured Working owner and source Markdown.
- `docs-viewer-workspace-provider.js` resolves current workspace URLs and delegates `readIndex`, `readDocument`, `readSearch`, `readRecent` and `readLinks` to the generated-data runtime.
- `readSource` and `writeSource` are absent from a provider unless a source adapter explicitly supplies them. Method or provider presence does not grant backend or write authority; the source endpoint remains capability-gated.

## Workspace Provider Contract

Public and Manage routes use one workspace-provider implementation. Each composition supplies one workspace from `docs_viewer_config_v4`, without a stages array. It adapts configured URLs to collection-facing methods so route, document, Search/Recents, report and Source Editor consumers do not reconstruct generated-data paths or choose a publishing stage. Local services resolve Working; public readers use repository/public data.

`readLinks` opens the exact document's separate relationship record through its configured URL base. `docs-viewer-generated-data-runtime.js` owns static-versus-local reads, generated-read capability checks, retry delays, reload paths and payload normalization.

Docs Review retains its separate package owner. No Preview browser provider or fallback to another workspace is available.

## Current Payload Roots

| Owner | Docs root | Search root |
| --- | --- | --- |
| Manage/local | `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/documents/` | `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/search/index.json` |
| Prepared artifact | `$DOTLINEFORM_DOCS_BASE_DIR/preview/documents/` | `$DOTLINEFORM_DOCS_BASE_DIR/preview/search/index.json` |
| Site-preview / public | `site/assets/data/docs/` | `site/assets/data/search/analysis/index.json` |

Working builders and management follow-through write local generated output. One Publish action captures eligible inputs, builds and verifies a fresh Preview artifact, then distributes that exact snapshot. There is no intermediate confirmation. Site-preview and public routes read the repository/public projection. Named collections use their configured `collections/<id>/documents/` generated/prepared roots and `site/assets/data/docs/<id>/` public destinations.

Scope-independent generated data has a separate owner. The semantic-token target lookup is reproducible application data at `docs-viewer/data/generated/semantic-tokens/target-lookup.json`, registered to the manage-only browser URL `/docs-viewer/data/generated/semantic-tokens/target-lookup.json`. It combines catalogue inputs into a focused target projection, so it is neither one scope's publication nor a public projection. `data/generated/` is not a fallback location for scope payloads.

## Collection Manifest Ownership

The [collection builder](../../docs-viewer/build/docs_builder/collection.py) produces one list manifest for the operation's existing build role. Working full and targeted collection builds generate only `manage-manifest.json`, including requested draft documents and the existing management metadata. Working does not generate, read or require a public `manifest.json`. The local generated collection route serves the management manifest and exact by-ID documents; public-manifest reads through that route are retired without a fallback.

The watcher passes changed/deleted document identities to the builder. Targeted Working builds read only the saved management manifest, validate its required metadata, merge selected rows, and use its membership and titles as rendering context. Unselected rows and document payloads remain intact. The manifest is written only when its projected contents change. Missing/invalid required management metadata fails with a complete collection Build instruction; no public-manifest agreement check or full-source fallback remains.

Publish selects eligible source inputs and invokes the same builder in its temporary Preview workspace. Those collection builds generate only the existing public `manifest.json` projection. They do not construct private authoring-subject metadata or a management manifest. The completed snapshot and distribution retain the existing public filename, fields and validation, and the snapshot boundary continues excluding management artifacts. Publish has no dependency on Working's public-manifest output.

Identity, date and field meanings remain unchanged. Collection diagnostics report the selected `manifest_filename` and one `manifest_changed` count; the former separate management-manifest count is retired.

## Route Payload Contract

| Capability | Public route source | Manage route source | Notes |
| --- | --- | --- | --- |
| Navigation tree | `index-tree.json` | `index-tree.json` | Public and manage tree nodes share the same nested structure. |
| Selected document render | by-id payload | by-id payload | By-id payloads remain in scope for selected documents. |
| Info-panel metadata | selected by-id payload | selected by-id payload | Public reader metadata is limited to title, summary, and last updated. |
| Search | search payload | search payload | Search runtime reads separate search payloads. |
| Recent | unchanged copy of Working `recent.json` | Working generated `recent.json` | One stage-independent payload lists recently edited documents; readers own navigation. |
| Management metadata/actions | not public route data | management services and manage payloads as needed | Public tree/by-id payloads should not carry management-only metadata. |

## List Date Projections

All collection reader and management manifests, Search result metadata, Recents and Selected Documents use populated update dates in canonical `YYYY-MM-DD` form. The ordinary builder's in-memory flat rows use the same projection; no flat index file is written. List inventories omit `added_date`; source Markdown and by-ID document payloads retain their original `added_date` and `last_updated` precision for exact document metadata and source/output consistency checks. Collection reader manifests include `last_updated` even when they previously exposed only identity, title and subject. Ordinary navigation trees retain their authored order and carry no update dates.

Recency sorting uses the projected update date; entries updated on the same day use the owning report's deterministic title/identity ties. List dates derive from existing source timestamps or dates. Undated documents retain an empty update value, sort after dated report entries and are excluded from Recents; creation dates are never substituted. Catalogue, Works and Selected Documents continue to require populated update dates. Malformed populated source or projected dates fail at their owning operation. Targeted collection builds require the current shape of their operation's saved manifest, using only management metadata in Working, and direct users to a complete collection Build when migration is needed. Search compares source and by-ID update values at their original precision and their date projection with collection management metadata.

## `index-tree.json` Contract

Public and Manage `index-tree.json` use the same nested document structure. A publish-capable Manage projection may additionally carry `publishable: false` on excluded rows; included rows and every local collection row omit the field. The public Publish projection strips this management field.

`docs` is an array of root nodes. Child relationships are expressed with each node's optional `children` array.
Generated tree nodes do not carry `parent_id`; `docs-viewer-tree-payload-adapter.js` derives runtime-only parent ids while normalizing the nested payload for existing renderer and management state.

Public `index-tree.json` nodes should stay as close as possible to:

- `doc_id`
- `title`
- `children`, only when non-empty
- `publishable: false`, only in a publish-capable private Manage projection
- `ui_status`
- `content_url`
- `report_id`, only when the document hosts a registered report

Fields excluded from public `index-tree.json`:

- `summary`
- `last_updated`
- `viewer_url`
- `content_text_length`
- default or derivable values

`publishable` is a public-projection gate, not a generic tree field. It is absent from local and public reader projections. `ui_status` remains separate presentation metadata. `report_id` is projected directly from the document's validated report descriptor so the shared index renderer can identify exact report-host roles without loading every by-ID payload; it does not carry report configuration or grant loader access.

## By-Id Payload Contract

Selected document loading stays by-id.
The public info panel reads selected-document metadata from the selected by-id payload, not public tree rows and not `index.json`.

Public reader-facing by-id metadata for the info panel is:

- title
- summary
- last updated

Public by-id payloads should not expose source path, visibility state, UI status internals, management-only fields, or editable metadata concepts for the public info panel.
Manage mode can keep a richer metadata surface, but it should hydrate selected-document metadata from selected by-id payloads rather than public tree/index rows.

## Search Contract

Search runtime reads the separate search payload through `search_index_url`, such as:

- Public: `/assets/data/search/analysis/index.json`
- Manage: `/docs/search`, resolved to configured Working output

Search build inputs should not depend on retired public docs `index.json`.
That is a builder-source responsibility, not a public search runtime capability change.

## Recent Contract

Recents uses one `docs_recent_v2` artifact with `schema`, `limit`, `generated_at` and `docs`. Working alone generates it at its configured `generated/documents/recent.json` location. The workspace's `recent_limit` is 20. Recents always uses document updates; the added-based mode, route `recent_basis` setting and payload `basis` field are retired. Different stage or public variants are not generated.

Each row carries exact `doc_id`, title, one date-only update `timestamp` (`YYYY-MM-DD`) and optional parent context. Collection rows additionally carry `collection`, `report_doc_id` and `collection_title`. Rows contain no stage, result URL or `content_url`. The active route resolves navigation from exact document/collection/host identity. Recents and Search share result navigation but load independent artifacts.

Search and Recents use [the shared metadata selector](../../docs-viewer/services/docs_discovery_selection.py): ordinary documents plus the explicitly included Works collection, with draft/unpublishable ordinary branches excluded, the included collection host required to survive, and flat eligible collection rows selected independently. Catalogue rows have fixed document eligibility and omit `draft`; other collection rows use explicit boolean draft state. Eligible Catalogue, Concepts and Moments landing pages remain ordinary candidates; their subdocs remain excluded by configuration. Processing's empty Docs collection was retired on 2026-09-27. Recents applies all selection before date sorting and limiting.

The [Recents builder](../../docs-viewer/build/docs_builder/payloads.py) reuses current ordinary records and their in-memory tree. Included collections supply compact Working `manage-manifest.json` metadata: identity, title and date-only `last_updated`, plus explicit draft state for collections other than Catalogue. Full and targeted collection builds maintain the date field. Recents does not open collection Markdown or by-ID bodies, read Search, or fall back to a source scan. Missing/invalid required metadata fails clearly. Manage Rebuild refreshes included collection metadata before the ordinary build generates Recents once; direct full Working document builds require current saved collection metadata.

Full Working document builds own generation. Targeted ordinary builds, collection-only builds, source saves and watcher passes preserve saved Recents, including when authoring falls back to a full document rebuild. A saved list can retain an old title or target until its next owning build. Opening Recents only reads JSON, and the ordinary tree does not gain timestamp fields.

Publish preparation validates and captures saved Working Recents alongside Search, binds its exact bytes into the plan and copies it before recording the temporary build's completion manifest. Snapshot assembly and distribution preserve those bytes without URL/label rewriting, reserialization, sorting, limiting or timestamp changes. Missing/invalid Recents fails without regeneration. Edits are unavailable during the synchronous operation, so no intermediate freshness check is needed. Recents freshness after ordinary edits and equality with prepared document membership are not required. The separate `.publish/recent.json` variant is retired. [The payload validator](../../docs-viewer/services/docs_recent_payload.py) owns allowed copied fields and identity checks.

## Public Flat `index.json` Retirement

Public flat `site/assets/data/docs/scopes/<scope>/index.json` is retired from the Docs Viewer route contract.
Public Docs Viewer routes do not publish or load it.
The route contract is covered by:

- `index-tree.json` covers navigation
- by-id payloads cover selected-document rendering and info-panel metadata
- search reads its separate search payload
- Recent reads its small generated payload

Document-package needs for richer document data are covered by `docs_document_packages.source_context`, `docs_document_packages.source_records`, and `docs_document_packages.rendered_content`.
Those helpers read configured docs source and source-rendered content for direct document-package workflows.
It must not fall back to public flat indexes, generated by-id payloads, search payloads, Recent payloads, manage/local generated indexes, or generated metadata JSON.
Other tooling needs for richer generated data still need their own owning contract.

Private collection `manage-manifest.json` files remain owned by configured Working generated storage and are not public route dependencies. Reader targets, Links/backlinks and semantic usage carry exact document/collection identities without stage fields. Storage/build completion receipts retain internal provenance. [Configuration And Extension Points](Configuration_And_Extension_Points.md) owns current identity and service contracts.
