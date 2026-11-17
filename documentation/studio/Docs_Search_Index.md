---
draft: false
doc_id: d-20260813-214350-4c7a21
title: Docs Viewer Search Index
added_date: "2026-08-13 21:43:50"
last_updated: "2026-11-17"
summary: Durable structure, field policy, build ownership, ranking inputs, and extension boundary for Docs Viewer search indexes.
parent_id: d-20260602-160839-6d3cbb
---
# Docs Viewer Search Index

Docs Viewer uses one static inverted-index format across Working, Preview and the public reader. The browser receives one compact document table plus term-to-document posting lists. The index contains content and document identity; the consuming route owns stage and navigation context.

## Payload Contract

`docs-viewer/build/build_search.py` emits `docs_viewer_search_index_v4` with the following fields.

- a header containing schema, content version, generation time and document count;
- an ordered `fields` list for the scope;
- a deterministic `docs` table containing identity and title, with collection and display metadata where applicable; and
- a `terms` map whose field-specific sorted posting lists reference zero-based positions in `docs`.

Each exact target occurs once per scope. A term occurs once, and a row position occurs at most once in each term and field posting list. The content version hashes schema, fields, rows and terms. An identical rebuild preserves the saved bytes and timestamp.

The browser reads the active scope on demand and owns route construction. Ordinary and collection results use the existing document route with exact document and collection identity. A Gallery row has `kind: catalogue-gallery` and carries the exact Gallery ID in `id`. Selecting it opens the existing Media View. Result URLs live in the browser, which carries `search-scope` alongside `q` for reload and shared links.

Working alone builds Search. Each changed scope is queued as a completed file. Publish copies the selected files through Preview to the repository as exact bytes. A missing selected file fails at the transfer boundary. Manage reads the saved Working file through `/docs/search` with `search-scope`. Public reads the corresponding static artifact from its deployed snapshot.

Authoring changes reach Search at the next explicit refresh or Full Working Build. Manage suppresses known deleted targets while using the saved postings for all other matches.

## Scope And Eligibility

- **Portfolio** uses `index.json` and indexes titles of eligible ordinary pages, the portfolio landing pages, Context, Concepts, Moments and Catalogue Galleries. Catalogue Works and reference pages belong to their own search controls or scopes.
- **Context, Concepts and Moments** use `works.json`, `concepts.json` and `moments.json`. Each uses the workspace's full-text fields `title`, `heading`, `summary`, `body` and `code`.
- **Library and Living Memory** use `library.json` and `book.json`. They search title and summary, with Living Memory limited to its web edition.

The [shared selection owner](../../docs-viewer/services/docs_discovery_selection.py) excludes ordinary draft and unpublishable subtrees. Collection rows require eligible hosts and non-draft entries, with the Book's web edition derived from its management manifest. Portfolio takes Gallery titles from the prepared Catalogue Gallery search file when the Catalogue host is eligible. Recent selects its own collection coverage using `include_in_site_search`. [Recent contract](Generated_Data_Contracts.md#recent-contract)

Each scope is its own relevance corpus. Only its configured fields emit postings. Summary text contributes postings and stays out of the result rows. Collection IDs and display metadata support navigation and display.

## Source Boundary

Full text is derived from selected canonical Markdown through existing owners. Validated report declarations are projected away, semantic references contribute their visible title, configured media tokens are removed, and the shared Markdown renderer separates non-duplicate headings, readable prose, inline code, and fenced code.

Valid active Docs-owned `[[image:...]]` tokens and Gallery Media View tokens with `visible=false` are replaced with whitespace before Markdown text extraction. Their labels, alt text, captions, image summaries, identities and source syntax contribute no searchable terms. Literal code examples retain the existing code-field treatment. Source extraction changes take effect at the next explicit complete Working Search rebuild. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md#supported-source-forms) owns the token grammar.

Collection summaries use the same text tokenizer as other text fields. Missing or blank summaries contribute no terms. Body extraction excludes generated report hosts, link destinations, media paths, raw markup attributes, scripts and styles. The tokenizer excludes complete document IDs, date fragments and exact 64-character hexadecimal content digests. Image alt text and visible raw-HTML text remain searchable.

## Query And Ranking

`docs-viewer/runtime/js/shared/docs-viewer-search.js` owns browser postings, ranking and tie-breaking and is projected to `site/` for public use. A multi-term query intersects its normalized term matches. Text terms support prefixes from two characters. Standalone integers use exact title postings, including their comma-grouped forms. Each document appears at most once, and ties sort by title and then identity.

For the active search fields, relevance orders exact title, title, heading, summary, then body and code. The matcher uses the active scope's postings.

## Build And Extension

Manage **Refresh Search and Recent**, Full Working Build and `build_search.py --stage working --write` use one Search builder and queue each changed scope as it completes. Portfolio uses completed titles. Collection sources supply only the searchable metadata and body fields required by their scopes. Full Working Build carries its loaded sources forward. The explicit discovery refresh reads ordinary dates for Recent and performs no document or media generation. [Discovery refresh](../../docs-viewer/services/docs_discovery_refresh.py)

Working publishes `index.json` through `workspace/search` and each collection file through `workspace/search-<collection-id>`. Keep the scope contract with the [Search artifact names](../../docs-viewer/services/docs_search_scopes.py) and use the shared format, matcher and result list when extending it.
