---
draft: false
doc_id: d-20260813-214350-4c7a21
title: Docs Viewer Search Index
added_date: "2026-08-13 21:43:50"
last_updated: "2026-10-16"
summary: Durable structure, field policy, build ownership, ranking inputs, and extension boundary for Docs Viewer search indexes.
parent_id: d-20260602-160839-6d3cbb
---
# Docs Viewer Search Index

Docs Viewer uses one static inverted-index format across Working, Preview and the public reader. The browser receives one compact document table plus term-to-document posting lists. The index contains content and document identity; the consuming route owns stage and navigation context.

## Payload Contract

`docs-viewer/build/build_search.py` emits `docs_viewer_search_index_v4` with:

- a header containing schema, content version, generation time and document count;
- an ordered `fields` list copied from the workspace's `search_fields` policy;
- a deterministic `docs` table containing identity, title, update, parent, display context and any structured collection target; and
- a `terms` map whose field-specific sorted posting lists reference zero-based positions in `docs`.

Each exact ordinary or `{collection, doc_id}` target occurs once. A term occurs once, and a document position occurs at most once in each term/field posting list. The content version hashes schema, fields, document metadata and terms; it excludes generation time and stage. An identical complete rebuild skips its write.

Search JSON contains no stage, result `href` or content URL. Browser readers validate the supported schema and obtain the index location from their configured provider. Result navigation uses document ID and exact collection/report-host identity with the active local or public route. The separate public document-location producer and unused picker/index are retired.

Working alone builds Search. Completion writes and queues only changed index content. Publish copies the queued file through Preview to the repository with its generation time, content version and collection display labels unchanged. It performs no Search schema/content audit, freshness check, label rewriting or rehashing. A missing selected file fails at the transfer boundary without rebuilding it; there is no separate preparation plan or snapshot workflow.

Ordinary source edits may leave Search stale. Preview copies that saved corpus even when it differs from the eligible document set. Coverage and readiness are decided by the Working Search build; document completeness checks do not require Search membership equality and copying applies no second filter.

Parent title, document identity, and update time remain in the document table without emitting postings. The workspace uses ordered searchable fields `title`, `heading`, `summary`, `body`, and `code`. Summary text contributes postings without being duplicated in the document table. A field-policy change takes effect on the next Working Search refresh and reaches Preview/repository through Publish.

## Current Corpus Composition

Site Search includes eligible ordinary documents plus Works subdocs. Each configured collection requires an explicit boolean `include_in_site_search`; `DocsStageConfig.site_search_collections` owns the selected set for Search and Recents. Both use [the shared metadata selector](../../docs-viewer/services/docs_discovery_selection.py) for ordinary subtree exclusions and flat eligible collection entries. Catalogue has fixed document eligibility and no draft field; other collections use their boolean draft state. Catalogue, Concepts and Moments remain excluded by configuration. A collection delivery explicitly chooses its inclusion policy; registration does not imply inclusion. Ordinary collection landing pages remain ordinary candidates regardless of their subdocs' inclusion policy. [Generated Data Contracts](Generated_Data_Contracts.md#recent-contract) owns Recents generation and copying.

Manage discovery refresh supplies one saved metadata selection and selected source records shared with Recent. Full maintenance supplies already loaded sources and completed in-memory metadata instead. Both read `unpublishable.json` once, inherit ordinary draft/ignored subtree exclusions and include only configured Search collections whose report host survives. Flat Catalogue rows omit draft; other collection rows require `draft: false`. Search does not reopen supplied sources, manifests or by-ID output to audit agreement. Discovery refresh builds no documents; full maintenance builds ordinary/non-Catalogue owners independently of Search coverage and retains exact Catalogue dependency ownership.

The standalone Search command selects before reading searchable content. It traverses saved Working `index-tree.json` and reads only included/eligible-host collection `manage-manifest.json` metadata. Excluded collections and hosts cause no manifest, source or by-ID content reads for their subdocs. Both entrypoints use the same selection rules and Search projection.

For standalone Search, the source model loads only selected filenames from their configured boundaries. Missing or invalid required metadata and selected source inconsistencies stop the build without replacing the saved index. Its ordinary sources agree with the tree's identity, title, draft state and parent placement; selected collection sources and by-ID payloads agree on exact identity, title and update value at its original precision, with the same projected management date. Those saved-input prerequisites do not participate in the complete Rebuild's prepared-record path. Search never discovers substitute IDs, scans every source as a fallback, or rebuilds document projections itself.

Child rows retain `id` as document identity and add exact `collection`, `report_doc_id`, and display-only `collection_title`. The browser constructs the canonical parent URL from that structured identity and the active Manage or public route, preserving the child as `subdoc`. Document-table `last_updated` and the compact `display_meta` line use `YYYY-MM-DD` update dates plus configured collection title without making collection structure searchable. Source and by-ID timestamps retain their original precision.

The combined index remains one complete artifact and one relevance corpus. Excluded documents contribute neither result rows nor terms. Search does not create per-collection indexes, make collection structure searchable, or control Index and Recents payload generation.

## Source Boundary

Full text is derived from selected canonical Markdown through existing owners. Validated report declarations are projected away, semantic references contribute their visible title, configured media tokens are removed, and the shared Markdown renderer separates non-duplicate headings, readable prose, inline code, and fenced code.

Valid active Docs-owned `[[image:...]]` tokens are replaced with whitespace before Markdown text extraction. Their alt, caption, image summary, identity and source syntax contribute no searchable terms. Literal code examples retain the existing code-field treatment. Existing Markdown image alt, HTML figure text and Catalogue token extraction keep their current behavior pending a separate image-content policy review. This source-extraction change takes effect only at an explicit complete Working Search rebuild; it does not change fields, membership, ranking or rebuild scheduling. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md#docs-owned-images) owns the new image grammar.

Title and summary are explicit authored front-matter inputs. Ordinary and collection summaries use the same text tokenizer as other text fields; missing or blank summaries contribute no terms. Other front-matter fields remain excluded. Body extraction excludes generated report hosts, link destinations, media paths, raw markup attributes, scripts, and styles; the tokenizer excludes complete document IDs, date fragments, and exact 64-character hexadecimal content digests. Image alt text and visible raw-HTML text remain searchable.

## Query And Ranking

`docs-viewer/runtime/js/shared/docs-viewer-search.js` is the sole browser postings, ranking, and tie-breaking owner, projected to `site/` for public use. A multi-term query intersects its normalized term matches; prefix matching begins at three characters; each document appears at most once; ties sort by title and then identity.

The generic score order is exact identity, exact title, title, heading, summary, parent title, body/code, then update metadata. Only fields enabled by the workspace participate. The active order is therefore exact title, title, heading, summary, then body/code; parent context is display-only.

Short prefix searches can be broad after full-text adoption. For example, the accepted Studio `reg` query returns 145 documents while its two established title matches remain first. Snippets, highlighting, stemming, synonyms, typo correction, term-frequency scoring, phrase positions, section results, and deep links are not part of this index.

## Build And Extension

Every explicit Search refresh rebuilds the complete Working index. Ordinary and collection authoring changes leave Search unchanged until Manage **Refresh Search and Recent**, a maintenance rebuild or `build_search.py --stage working --write`. [Discovery refresh](../../docs-viewer/services/docs_discovery_refresh.py) shares one metadata selection and selected source reads with Recent, without document rendering or media production. The Search builder supplies document/write/skip diagnostics and queues only newly written output; an unchanged content version preserves the saved bytes, timestamp and pending selections. Publish copies queued bytes unchanged. No path patches postings or maintains a separate collection index.

Search requires completed Working membership/collection metadata and reads only selected canonical source content. Ordinary application writes already own their exact generation; external source or policy changes require their owning generation before discovery refresh. Change field policy through the workspace's ordered `search_fields` and collection coverage through `include_in_site_search`, then refresh discovery. Test changes require their own agreed specification. Do not add a second schema, tokenizer, cache, reader, query engine, or collection-name branch.
