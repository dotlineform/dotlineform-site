---
draft: false
doc_id: d-20260714-234030-434069
title: Semantic Tokens Architecture
added_date: "2026-07-14 23:40:30"
last_updated: "2026-10-01 13:20:00"
summary: Describe explicit Catalogue tokens, source ownership, document relationships, and local/public media resolution.
parent_id: d-20260725-153656-516b61
---
# Semantic Tokens Architecture

## Supported Source Forms

Catalogue tokens retain an exact Catalogue identity and authored occurrence fields. The supported forms are:

```md
[[catalogue:media:work:00638|3 symbols]]
[[catalogue:media:gallery:179|kylie structure 4 (details)]]
[[catalogue:image:work:00638|use_work_title_caption=true&include_work_metadata=true&placement=left&fill_width=true]]
```

Media View text links accept an exact five-digit Work ID or an exact Gallery ID. Gallery IDs use three digits or at least four digits without a leading zero. The serializer escapes backslash, pipe and closing bracket in the required single-line label; the parser decodes only those escapes. Work image identity also uses five digits. Detail and Series token forms remain literal and do not open Media View. The existing authored Series tokens in Working source were deliberately left unchanged when support was removed.

Image fields use deterministic percent encoding and canonical field order. Work images require explicit boolean `use_work_title_caption` and `include_work_metadata` choices, placement (`full`, `left` or `right`) and boolean `fill_width`; `summary` is the only optional authored text. The token stores no literal Work title, alt text, caption or metadata. Image tokens support Works only. Gallery grids open through text links, with no inline group image.

Tokens always include their Work or Gallery identity, including Work tokens inserted through Use document subject. Gallery selection is independent of document Subjects. Media View link labels and image summaries are authored literal text; the image choices instruct Build to resolve the exact generated Work record. The experimental omitted-identity forms are retired without compatibility aliases.

The old three-part Catalogue text form and Concept tokens are retired. They have no parser, renderer, authoring control or compatibility alias. Ordinary document references use Markdown links through [Insert doc link](Source_Editor_Scripts.md).

## Parsing And Source Mutation

Python Build and browser Source parsing recognize the explicit Catalogue `media` and `image` forms. Parsed occurrences retain raw text and zero-based half-open `[start, end)` range. Inline code, fenced code and HTML comments are inactive. A collapsed caret activates a supported occurrence only when `start < caret < end`; a shared boundary between adjacent tokens activates neither.

Source remains directly editable. Malformed or unsupported strings remain ordinary literal source and do not activate a Catalogue Info view. Parser, source-range and retained media/image behavior have focused Python and JavaScript checks. The old frozen text-token fixture is retired.

The generic Source adapter owns the mounted target, current buffer revision, captured selection, pending occurrence fields and guarded replacement. The source-read response includes the safe Catalogue `subject` projection from that exact document's front matter; the adapter exposes it to the modal for selection. Add modals supply a serialized insertion. The Semantic token panel edits raw session-owned occurrence values that survive panel switches and closure. The single session Save validates and serializes all pending occurrences with metadata and body before one source write. The editor rejects a stale range or a different mounted target before changing the buffer. Neither a modal nor the panel saves or rebuilds independently; watcher generation and viewer refresh remain outside Save completion.

## Identity And Subject

A token records an occurrence in body content. It does not establish that the document is about that Work or Gallery. Document Subject metadata retains its independent association. Supported subjects are Work, Series and, where the collection enables it, Folder; None clears the declaration. Series is not a token or Media View target. Work tokens create direct document relationships to Catalogue; they do not create Subject metadata or transitive relationships.

Catalogue owns canonical identities and media. Tokens select Catalogue media independently of document Subject. Use document subject supplies the exact selection once during insertion. Changing the document's subject later does not retarget existing tokens; Build, Info and audits use the identity stored in the token.

## Registry And Lookups

The checked configuration is `docs-viewer/config/semantic-tokens/registry.json`. It declares the Catalogue family, Work/Gallery target definitions, identity policy, named lookup fields, occurrence metadata and the Catalogue Info contribution. The retired text action and modal contributions have been removed.

The registry does not control which Source buttons a scope exposes. That proposed layer belongs to [Scope-configured Authoring Controls](Scope_Configured_Authoring_Controls.md). Parser, resolver and presentation implementations remain code-owned.

The private generated lookup is `docs-viewer/data/generated/semantic-tokens/target-lookup.json`. It contains Work rows and is not the authoring, Info, Build or Broken Links authority for the supported Catalogue tokens. Series rows were removed with the Series token target definition.

Media authoring and Info use generated Catalogue Work/Gallery data through the configured media provider. The shared Catalogue media modal offers Works for images and Work/Gallery selection for text links. Gallery search reads Studio's generated `galleries/galleries_index.json` through `/docs/catalogue-media-targets`; Gallery resolution reads the selected `galleries/index/<gallery_id>.json` through `/docs/catalogue-gallery`. Neither needs the private target lookup or a Gallery document. Current media validation precedes guarded insertion or Info updates; provider failures remain visible and Source Save revalidates pending token edits.

Both Add Catalogue image and Add Media View link offer Use document subject, initially unchecked. Checking it selects the subject in the modal and disables manual Catalogue selection until unchecked. The checkbox is enabled only for a Work subject from `work_id`; Series, Folder and absent subjects leave manual selection available. Both actions serialize the normal explicit Work identity form. Token Info reads the stored identity and preserves it when updating presentation.

## Build And Runtime Resolution

Work and Gallery text links and Work images are rendered as HTML markers carrying exact Catalogue identity. A Gallery marker uses `data-docs-media-kind="catalogue-gallery"` and its exact Gallery ID. The media provider resolves the presentation at runtime. The Links builder separately extracts Work document relationships from the authored tokens before rendering.

For each Work image, the shared document builder reads `works/index/<work_id>.json` from the configured stage, validates the exact Work identity and required title, and reuses that record within one build. A missing or invalid media record fails image rendering; this is separate from document-link construction, which does not check the Catalogue document. The current `work.title` always supplies image alt text; `use_work_title_caption` controls its separate visible bold caption. When `include_work_metadata` is true, Build renders nonempty `year_display`, nonempty `medium_caption`, positive height × width × optional depth in centimetres, and `cat. <work_id>` as separate escaped lines in that order. It omits the dimensions line without both height and width. Authored `summary` follows the metadata with the existing figure gap; the figure also supports metadata or summary without a visible title caption. Generated HTML contains static text, including explicit metadata line breaks. Targeted and full Working builds use this path. Publish copies its already-captured Catalogue JSON into the temporary Preview build workspace before the same renderer runs; it does not reread live Working JSON during that build.

The browser resolves those markers using generated Catalogue data and the shared [Media View](Catalogue_Media_View.md) presentation. This is also the public path: it requires public generated Catalogue data, not local authoring endpoints or document existence.

Empty Galleries open an empty grid. A missing Gallery or selected image produces runtime failure feedback without replacing its identity. Series token forms and Gallery image forms remain literal source.

The builder escapes authored labels, Work-derived text and presentation fields. Media fragments are restored after Markdown processing so authored labels remain literal text. Build does not mutate authored source or choose a replacement identity. The browser still resolves the actual image and Media View from the marker's exact Work identity and current Catalogue consumer data.

## Document Relationships And Audit

Supported Work image and Work Media View text tokens create an outgoing relationship to `{collection: "catalogue", doc_id: "<work_id>"}` through the existing [Document Build](Builder.md) Links owner. Repeated references produce one relationship and maintain the reciprocal incoming summary. Gallery Media View tokens produce no document relationship. A Catalogue document's token for its own Work renders normally and contributes no self-relationship.

The Links builder constructs document relationships without checking destination existence or link validity. Saved records and current source metadata supply titles where available; missing metadata falls back to the authored label or document ID and never prevents relationship creation. Explicit document deletion removes its record and associated relationships. Existing Working publication exclusions remain owned by the Links policy. Subjects do not create these token relationships.

Catalogue sources end with their Work image token, a blank line and `[[links|related links]]`. Related links renders recorded incoming and outgoing document relationships from the same refreshed in-memory records. The directive alone creates no graph record. [Related Links](Related_Links.md) describes the rebuild sequence and sparse record behavior.

The stored semantic occurrence index and [Semantic Tokens report](Semantic_Tokens_Report.md) are retired. Raw text and source positions remain in the live parsers for Source editing and audits; Build no longer stores occurrence rows. The read-only [Docs Broken Links](Broken_Links.md) audit independently scans source and checks current generated Catalogue Work media or exact Gallery membership records. It distinguishes `missing_gallery` from `missing_media`. The audit does not retarget source or change publication state.

## Public Boundary

Public readers consume rendered document HTML, including Related links, and public generated Catalogue data. The private registry and management lookup are not public dependencies. Publication selection, accepted snapshots and deployment remain owned by their existing workflows; Source insertion and token retirement do not run those operations.

See [Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) for the authoring and Info surfaces.

## Focused Grammar Evidence

The following selection is historical evidence, not validation of the current bound-image grammar. Its literal image fields and Detail assertions, along with subject/media/report fixtures containing retired Detail fields, need a separately approved test update. No test files or fixtures changed during the 2026-09-23 consumer retirement or the bound-image delivery.

The existing `docs-viewer/tests/python/test_semantic_tokens_catalogue.py` selection has two pure checks. `test_media_parser_preserves_literal_labels_ranges_and_code_boundaries` supplies escaped explicit Work links, adjacent occurrences, inline/fenced code and comments; it asserts decoded literal labels, source ranges, caret activation and inactive code/comment content. `test_visual_occurrence_parser_is_canonical_and_context_aware` supplies explicit primary/Detail images and captions, summaries, placement and width fields; it asserts canonical serialization, presentation retention, source ranges and rejection of its listed malformed field/identity forms.

These checks read the repository token registry and call Python parser/serializer functions without mocks, media reads, source writes, Build, browsers or network. The selection protects explicit syntax; it does not exercise source-response projection, modal behavior, Info editing, audit integration or public rendering. Its initial measured run on 2026-09-16 took 0.08 seconds inside pytest, excluding process setup; inspection and diagnosis remain bounded to this file. No test authoring or maintenance change accompanied the subject shortcut implementation.

Run the pure selection with the required import paths and `--noconftest`: the shared Docs fixture still imports the retired `docs_scope_config` API, while these functions need no fixtures. This command does not establish that other tests work without their fixtures. Python and pytest may write local caches.

```bash
set -a
source .env.local
set +a
PYTHONPATH="docs-viewer/services:studio/shared/python:studio/services:studio/app/server" "$HOME/miniconda3/bin/python3" -m pytest --noconftest docs-viewer/tests/python/test_semantic_tokens_catalogue.py -q
```
