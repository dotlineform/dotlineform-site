---
draft: false
doc_id: d-20260719-182348-492a48
title: HTML Import Mapping
added_date: "2026-07-19 18:23:48"
last_updated: "2026-11-18"
summary: Durable semantic-HTML-to-canonical-Markdown rules for Docs Import.
parent_id: d-20260424-000000-fc8b5d

---

# HTML And Word Import Mapping

HTML and Word intake share a semantic HTML-to-Markdown converter. The format adapter supplies semantic content, and the import workflow owns identity, persistence and media preparation. A native import creates a fresh draft. [Intake workflow](Docs_Import.md#import-one-native-file)

## HTML Mapping

HTML title preference is a nonempty `<title>`, then the first nonempty `<h1>`, then the filename-derived fallback. H1–H6 retain their levels. Paragraphs and readable containers retain block order. Quotes become quoted lines, preformatted text becomes fenced code, and ordered/unordered lists retain nesting. Details uses its Summary as H3. A semantic key/callout becomes a quote, and legend content becomes comma-separated text. Unknown containers contribute readable children.

| Form | Markdown result |
| --- | --- |
| Strong/bold and emphasis | `**bold**` and `*emphasis*`. Outer spaces stay outside markers, preserving a bold label followed by text. |
| Code, links and breaks | Inline code, ordinary Markdown links and line breaks. Empty link labels can use the URL. Plain absolute URLs outside links/code become autolinks. |
| Subscript/superscript | Safe inline HTML forms. |
| Simple table | First row becomes a header. Shorter rows are padded. Block content within a cell is flattened. |
| Row/column span | Plain-text degradation with a warning. |
| Images and inline SVG | Candidates for the separate import-media preparation and SVG sanitizer. |

Prompt/meta classes or recognized textual prefixes are omitted by the converter's default and become blockquotes when included. Native HTML intake includes them, while staged intake exposes the checked-by-default option. Comments, head/script/meta/title and non-SVG style content are omitted from the body. Non-SVG serialized markup drops event/style/class/ID/target/rel attributes. SVG retains required structure through the separate sanitizer. [HTML converter](../../docs-viewer/services/docs_html_markdown.py) · [Media preparation](Media_And_Asset_Handling.md#import-materialization)

## Word Style Mapping

Mammoth converts the repository's fixed style map to semantic HTML, which is passed unchanged into the same converter.

| Word style | HTML and Markdown meaning |
| --- | --- |
| Title | H1 with the title marker. Supplies the document title. |
| Subtitle | Ordinary paragraph below the title. |
| Heading 1 through Heading 5 | H2 through H6. |
| Heading 6 | H6 with a lossy-clamp warning. |
| Unmapped paragraph style | Mammoth's default degradation and visible conversion warning. |

Without a mapped Title, the humanized filename supplies the document title. The first section heading retains its section role. Built-in style IDs and names are registered, and Mammoth defaults handle ordinary lists, links, emphasis and tables. The adapter disables embedded style maps and external file access. Embedded images proceed through import media preparation. [Word adapter](../../docs-viewer/services/docs_import_docx.py)

## Extension

Change a mapping for a representative content structure with a deliberate Markdown result and inspect its degradation. Preserve that format decision in the adapter or shared converter, with test work scoped through the repository policy. Original layout and canonical source syntax can be simplified during conversion. Structured package exchange has its own rendered-text fidelity boundary. [Package output](Document_Packages.md#package-output)
