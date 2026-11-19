---
draft: false
doc_id: d-20260715-094411-2b6e65
title: Document Identity
added_date: "2026-07-15 09:44:11"
last_updated: "2026-11-19"
parent_id: d-20260424-000000-50b63f
summary: Immutable document codes, timestamp provenance, creation boundaries, and the distinction between identity and human navigation.
---

# Document Identity And Source Grammar

## Identity Contract

Ordinary and authored collection documents use `d-YYYYMMDD-HHMMSS-xxxxxx`, with six lowercase hexadecimal characters. New/Import captures one local creation timestamp for the ID and `added_date`. The allocator proposes the identity, and the owning create checks its exact destination. Canonical Markdown filenames match `doc_id`. Rename and Position preserve identity. [Identity primitives](../../docs-viewer/services/docs_document_identity.py) · [Creation](Source_Mutation_Endpoints.md#post-docscreate)

An exact document target includes its configured collection and ID. Catalogue documents use the five-digit Work ID, including leading zeroes, with `collection: catalogue`. Quote a numeric Catalogue `doc_id` in front matter. Review additionally carries package identity and accepts safe package-record IDs. [Collection ownership](Collections_And_Books.md) · [Review identity](Docs_Review.md#package-contract)

## Source Grammar

Canonical document source combines a leading front-matter block and Markdown body.

```markdown
---
doc_id: d-20261118-200000-a1b2c3
title: Surface studies
added_date: "2026-11-18 20:00:00"
last_updated: "2026-11-18 20:00:00"
draft: true
summary: |-
  First line.
  Second line.
---
# Surface studies
```

`docs_front_matter.py` parses scalar key/value fields, boolean values and integer values, quoted strings, Summary literal blocks using `|` or `|-`, and the defined Book provenance blocks. Source Save uses its strict parser. The supported grammar is smaller than general YAML. Quote an ID or text that must retain numeric-looking spelling. Multiline Summary preserves internal breaks, and serialization writes it with `|-`. [Front-matter parser](../../docs-viewer/services/docs_front_matter.py) · [Complete Source Save](Source_Editing.md#post-docssourcesave)

Ordinary organisation comes from `index-order.json`. Collection membership comes from configured storage and the exact target. Source `parent_id` cannot establish either. Boolean Draft belongs to authored documents, while Catalogue has its intrinsic eligibility. Book curation and provenance use their dedicated fields and owner. [Source organisation](Source_Organisation.md#document-and-collection-identity) · [Books](Collections_And_Books.md)

## Parsing And Rendering

| Step | Owner and result |
| --- | --- |
| Resolve and parse | The source owner reads the exact file, establishes its identity, fields, report declaration and body, and carries the prepared record onward. |
| Project special content | The payload builder projects reports and resolves supported document-media and Catalogue forms. |
| Render Markdown | The shared CommonMark renderer enables tables and raw HTML. Its extensions expand icons, Date, standalone Summary, Related Links and the Book TOC at their defined contexts. |
| Finish reader output | Link rewriting preserves target IDs and collection selectors in reader-relative query URLs. By-ID output carries `content_html`, metadata and prepared Catalogue references. |

[Source loader](../../docs-viewer/build/docs_builder/source.py) · [Payload pipeline](../../docs-viewer/build/docs_builder/payloads.py) · [Shared renderer](../../studio/shared/python/markdown_renderer.py) · [Link rewriting](../../docs-viewer/build/docs_builder/rendering.py)

The shared renderer uses CommonMark with its built-in table rule and no external plugins. It permits raw authored HTML and does not sanitize it; imported/untrusted HTML passes through the explicit import sanitizer. Summary renderers use the separate `zero` preset with emphasis/escape only; document Summary adds newline/break handling. They render inline without raw HTML, links, images, code or nested semantic directives. Image Summary retains its existing newline representation. [Summary implementation](../../docs-viewer/build/docs_builder/summary_formatting.py) · [Import sanitization](HTML_Import_Mapping.md)

Put `[[summary]]`, `[[links|Further reading]]` and `[[toc]]` on their own lines. `[[date]]` emits `date_display` or `date`. Directive-like examples in literal code and comments remain examples. Token-specific syntax and context rules belong to their parser. Restricted Summary emphasis is rendered separately and does not expand nested directives. [Summary and Date](Builder.md#source-contract) · [Supported references](Document_And_Catalogue_References.md) · [Report source](Reports.md#source-contract)

## Document Links

**Insert doc link** writes an ordinary Markdown link with exact document identity. Authored `/docs/?doc=<id>` links add `collection=<id>` for a named owner. Build converts recognized reader locations into query-relative output, allowing the active reader to compose navigation. A label can differ from the target's current Title. [Link authoring](Source_Editing.md#directives)

The relationship builder retains unique directed endpoints keyed by collection and ID. Supported Work references contribute exact Catalogue document edges. Gallery references retain their separate media/Context role. Rendering a Related section consumes prepared relationships. Explicit Broken Links diagnoses unresolved targets independently. [Relationships](Related_Links.md) · [Audit](Broken_Links.md#inputs-and-destination-checks)

## Date Provenance

`added_date` records creation. `last_updated` records an edit. Full lifecycle timestamps use `YYYY-MM-DD HH:MM:SS`. Legacy date-only source remains readable. `date` and `date_display` are authored content rendered by `[[date]]`. Lists project an ISO display date. [List dates](Generated_Data_Contracts.md#list-date-projections)

Source Save sets `last_updated` to the save time when the normalized body, Title or Summary changes. Status, Draft and date-field edits by themselves preserve the saved timestamp. Dedicated Draft and exact Rebuild preserve saved dates. For a deliberate timestamp correction or an external content edit, set the intended timestamp in the Markdown and run exact Rebuild. [Source Save](Source_Editing.md#post-docssourcesave)

## Diagrams

Author a diagram externally and import its finished SVG with Source **Add image**. Save sanitizes the SVG and stores it under the document's media owner. Keep the editable diagram source with its external project. The SVG has its authored appearance. For an expand control, put `<!-- dotlineform:image-detail -->` immediately before the image or token. [Image Detail](Document_Image_Detail.md) · [SVG ownership](Media_And_Asset_Handling.md#add-a-new-image-or-download)

Repository Markdown under `documentation/` follows its repository editing workflow. Published Docs diagrams use the imported SVG path above.

## Exchange Boundary

Native import converts content into a fresh local draft. A prepared package contains rendered-derived text and preserved record IDs/provenance. Omit its `content` field when a return should preserve the canonical body. Review displays a separately retained package projection. [Format conversion](HTML_Import_Mapping.md) · [Round trip and overwrite fields](Document_Packages.md) · [Review authority](Docs_Review.md)
