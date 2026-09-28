---
draft: false
doc_id: d-20260714-234030-434069
title: Semantic Tokens Architecture
added_date: "2026-07-14 23:40:30"
last_updated: "2026-09-28 15:14:52"
summary: Describe explicit Catalogue tokens, the document-subject selection shortcut, source ownership, generated usage, and local/public resolution.
parent_id: d-20260725-153656-516b61
---
# Semantic Tokens Architecture

## Supported Source Forms

Catalogue tokens retain an exact Catalogue identity and authored occurrence fields. The supported forms are:

```md
[[catalogue:media:work:00638|3 symbols]]
[[catalogue:media:gallery:179|kylie structure 4 (details)]]
[[catalogue:image:work:00638|alt=3%20symbols]]
```

Media View text links accept an exact five-digit Work ID or an exact Gallery ID. Gallery IDs use three digits or at least four digits without a leading zero. The serializer escapes backslash, pipe and closing bracket in the required single-line label; the parser decodes only those escapes. Work image identity also uses five digits. Detail and Series token forms remain literal, produce no usage row and do not open Media View. The existing authored Series tokens in Working source were deliberately left unchanged when support was removed.

Image fields use deterministic percent encoding and canonical field order. Alt text is required. Captioned images also store placement (`full`, `left` or `right`) and boolean `fill_width`; summary is optional. Image tokens support Works only. Gallery grids open through text links, with no inline group image.

Tokens always include their Work or Gallery identity, including Work tokens inserted through Use document subject. Gallery selection is independent of document Subjects. Labels, alt text, captions and summaries are literal text; `title` and `metadata` are not data-binding commands. The experimental omitted-identity forms are retired without compatibility aliases.

The old three-part Catalogue text form and Concept tokens are retired. They have no parser, renderer, authoring control or compatibility alias. Ordinary document references use Markdown links through [Insert doc link](Source_Editor_Scripts.md).

## Parsing And Source Mutation

Python Build and browser Source parsing recognize the explicit Catalogue `media` and `image` forms. Parsed occurrences retain raw text and zero-based half-open `[start, end)` range. Inline code, fenced code and HTML comments are inactive. A collapsed caret activates a supported occurrence only when `start < caret < end`; a shared boundary between adjacent tokens activates neither.

Source remains directly editable. Malformed or unsupported strings remain ordinary literal source and do not activate a Catalogue Info view. Parser, source-range and retained media/image behavior have focused Python and JavaScript checks. The old frozen text-token fixture is retired.

The generic Source adapter owns the mounted target, current buffer revision, captured selection, pending occurrence fields and guarded replacement. The source-read response includes the safe Catalogue `subject` projection from that exact document's front matter; the adapter exposes it to the modal for selection. Add modals supply a serialized insertion. The Semantic token panel edits raw session-owned occurrence values that survive panel switches and closure. The single session Save validates and serializes all pending occurrences with metadata and body before one source write. The editor rejects a stale range or a different mounted target before changing the buffer. Neither a modal nor the panel saves or rebuilds independently; watcher generation and viewer refresh remain outside Save completion.

## Identity And Subject

A token records an occurrence in body content. It does not establish that the document is about that Work or Gallery. Document Subject metadata retains its independent association. Supported subjects are Work, Series and, where the collection enables it, Folder; None clears the declaration. Series is not a token or Media View target. Neither rendered media nor the usage index creates Subject metadata, public document associations or transitive relationships.

Catalogue owns canonical identities and media. Tokens select Catalogue media independently of document Subject. Use document subject supplies the exact selection once during insertion. Changing the document's subject later does not retarget existing tokens; Build, Info and audits use the identity stored in the token.

## Registry And Lookups

The checked configuration is `docs-viewer/config/semantic-tokens/registry.json`. It declares the Catalogue family, Work/Gallery target definitions, identity policy, named lookup fields, occurrence metadata and the Catalogue Info contribution. The retired text action and modal contributions have been removed.

The registry does not control which Source buttons a scope exposes. That proposed layer belongs to [Scope-configured Authoring Controls](Scope_Configured_Authoring_Controls.md). Parser, resolver and presentation implementations remain code-owned.

The private generated lookup is `docs-viewer/data/generated/semantic-tokens/target-lookup.json`. It contains Work rows and is not the authoring, Info, Build or Broken Links authority for the supported Catalogue tokens. Series rows were removed with the Series token target definition.

Media authoring and Info use generated Catalogue Work/Gallery data through the configured media provider. The shared Catalogue media modal offers Works for images and Work/Gallery selection for text links. Gallery search reads Studio's generated `galleries/galleries_index.json` through `/docs/catalogue-media-targets`; Gallery resolution reads the selected `galleries/index/<gallery_id>.json` through `/docs/catalogue-gallery`. Neither needs the private target lookup or a Gallery document. Current target validation precedes guarded insertion or Info updates. These paths do not read the usage index.

Both Add Catalogue image and Add Media View link offer Use document subject, initially unchecked. Checking it selects the subject in the modal and disables manual Catalogue selection until unchecked. The checkbox is enabled only for a Work subject from `work_id`; Series, Folder and absent subjects leave manual selection available. Both actions serialize the normal explicit Work identity form. Token Info reads the stored identity and preserves it when updating presentation.

## Build And Runtime Resolution

Work and Gallery text links and Work images are rendered as HTML markers carrying exact Catalogue identity and authored presentation. A Gallery marker uses `data-docs-media-kind="catalogue-gallery"` and its exact Gallery ID. Build records these occurrences without requiring the private lookup or resolving a media URL. Their usage-row `href` is empty because the media provider resolves the presentation at runtime.

The browser resolves those markers using generated Catalogue data and the shared [Media View](Catalogue_Media_View.md) presentation. This is also the public path: it requires public generated Catalogue data, not local authoring endpoints or document existence.

Empty Galleries open an empty grid. A missing Gallery or selected image produces runtime failure feedback without replacing its identity. Series token forms and Gallery image forms remain literal source and produce no usage row.

The builder escapes authored labels and presentation fields. Media fragments are restored after Markdown processing so authored labels remain literal text. Build does not mutate authored source or choose a replacement identity.

## Generated Usage And Audit

Each workspace stage owns one `generated/documents/semantic-tokens/index.json` covering ordinary documents and all configured collections. Rows retain exact `source_stage`, `source_collection` and `source_doc_id`, with an empty collection for ordinary documents. The dataset retains its stage. Raw tokens, source ranges, family/type/identity, occurrence titles and destinations remain intact; repeated occurrences stay separate. The report displays exact supported Work or Gallery identity.

The existing `semantic_token_artifacts.py` owner combines occurrences collected during rendering with the saved index. Each sequential Save/Build replaces its built documents' occurrences and removes deleted members of that collection while preserving other documents and collections. Removing the last token removes that document's rows. Full main builds preserve child contributions, and child builds preserve main and sibling contributions. Index writing completes within the ordinary synchronous Build sequence. There are no child token indexes, per-document token stores, additional Markdown scans for token extraction or build-overlap mitigations.

Publication flags, draft state and Subjects do not filter generated usage. Source-field validation remains owned by the existing document model; usage does not make an otherwise unsupported front-matter field valid. Supported document Move rebuilds the target and source collections in order, retaining the new source identity and removing the old one.

The [Semantic Tokens Report](Semantic_Tokens_Report.md) pairs indexed occurrences with exact generated document titles and managed URLs through the current collection-location owner. Those source summaries belong to the read response, not another saved index. Missing source payloads or ambiguous collection hosts fail visibly without choosing another document. The read-only [Docs Broken Links](Broken_Links.md) audit scans source and checks current generated Catalogue Work media or exact Gallery membership records. It distinguishes `missing_gallery` from `missing_media`. An unresolved target may require correction in Catalogue or its generated data; the audit does not retarget source or change publication state.

Ordinary document relationships remain separately owned by [Document Build](Builder.md). Token usage does not write `links.json`, `links-by-id`, Catalogue records or inferred document relationships.

## Public Boundary

Public readers consume rendered document HTML and public generated Catalogue data. The private registry, management lookup and local usage index are not public dependencies. Publication selection, accepted snapshots and deployment remain owned by their existing workflows; Source insertion and token retirement do not run those operations.

See [Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) for the authoring and Info surfaces.

## Focused Grammar Evidence

The following selection is historical evidence, not validation of the current Detail-free grammar. Its Detail assertions and the subject/media/report fixtures that include retired Detail fields need a separately approved test update. No test files or fixtures changed during the 2026-09-23 consumer retirement.

The existing `docs-viewer/tests/python/test_semantic_tokens_catalogue.py` selection has two pure checks. `test_media_parser_preserves_literal_labels_ranges_and_code_boundaries` supplies escaped explicit Work links, adjacent occurrences, inline/fenced code and comments; it asserts decoded literal labels, source ranges, caret activation and inactive code/comment content. `test_visual_occurrence_parser_is_canonical_and_context_aware` supplies explicit primary/Detail images and captions, summaries, placement and width fields; it asserts canonical serialization, presentation retention, source ranges and rejection of its listed malformed field/identity forms.

These checks read the repository token registry and call Python parser/serializer functions without mocks, media reads, source writes, Build, browsers or network. The selection protects explicit syntax; it does not exercise source-response projection, modal behavior, Info editing, audit integration or public rendering. Its initial measured run on 2026-09-16 took 0.08 seconds inside pytest, excluding process setup; inspection and diagnosis remain bounded to this file. No test authoring or maintenance change accompanied the subject shortcut implementation.

Run the pure selection with the required import paths and `--noconftest`: the shared Docs fixture still imports the retired `docs_scope_config` API, while these functions need no fixtures. This command does not establish that other tests work without their fixtures. Python and pytest may write local caches.

```bash
set -a
source .env.local
set +a
PYTHONPATH="docs-viewer/services:studio/shared/python:studio/services:studio/app/server" "$HOME/miniconda3/bin/python3" -m pytest --noconftest docs-viewer/tests/python/test_semantic_tokens_catalogue.py -q
```
