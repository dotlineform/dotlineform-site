---
draft: false
doc_id: d-20260930-202255-229278
title: Icon Tokens
added_date: "2026-09-30 20:22:55"
last_updated: "2026-09-30 20:25:33"
summary: Manual extensionless SVG icon tokens, inline Source insertion, portable rendering and export behaviour.
parent_id: d-20260331-000000-c313fd
---
# Icon Tokens

Use an icon token to insert one saved SVG icon into normal document content:

```markdown
[[icon:refresh-cw]] Refresh the document.
```

The name is the exact filename stem from [the canonical icon folder](../../docs-viewer/static/icons/). The example selects `refresh-cw.svg`. Other examples include `sprout`, `dlf-work`, `star` and `file-text`. Lowercase letters, digits, hyphens and underscores are accepted; filenames resolve case-sensitively. The supported form is extensionless and contains no directory, URL or extra presentation fields.

## Source Editor

Place the cursor and choose **Directives → Insert icon**. The action inserts `[[icon:refresh-cw]]` inline and selects `refresh-cw`, ready for replacement with another filename stem. It adds no line breaks or spaces. If source text is selected, the directive is inserted before that text and preserves it.

The action changes only the editor buffer through its existing captured-range and revision guard. Save persists the source; the Working watcher independently rebuilds the document. There is no picker, modal or icon-specific Info editor.

## Rendering

Document Build expands the token into a monochrome SVG mask at `1em`, aligned with the text baseline and tinted with the surrounding text colour. A coloured source drawing also supplies a silhouette. Normal authored spaces control separation from adjacent text. Icons are inline content and have no button or diagram-detail behaviour.

The exact SVG is read from the canonical icon folder and sanitized. External SVG DTD declarations are discarded without loading them; entity declarations and unsafe SVG content fail. Missing files, invalid stems and unsafe artwork stop the document build with a diagnostic identifying the document and icon. Fix the source token or artwork and rerun the owning build.

Markdown parsing keeps tokens literal in inline/fenced/indented code, comments, escaped text, raw HTML attributes, HTML code content and image alt text. A token in normal text, a heading, a list item or a link label renders as an icon. Icons add no document relationships or Catalogue semantic-usage records.

An authored icon exposes its filename stem as its accessible name. It also carries a visually hidden copy of its source token for text conversion. Keep meaningful prose beside an icon when the filename alone would not explain it.

## Portability And Exports

The generated document HTML embeds the sanitized SVG as a small data-URL mask together with its inline sizing and tint rules. Local/public readers, Docs Review and HTML exports therefore display the same prepared markup without an icon fetch, a machine-specific path or a separate asset-transfer rule. Publication distributes this completed content through the existing snapshot workflow.

Markdown and plain-text conversions retain the readable `[[icon:name]]` token. Source packages retain the token as authoring syntax; rebuilding it requires the matching canonical SVG. Ordinary emoji remain unchanged.

The tradeoff is a small artwork payload for each rendered occurrence. A builder caches requested SVG bytes for its current operation, so repeated uses do not reopen and sanitize the same file. Rebuilding a document captures the current artwork; changing an SVG does not automatically rebuild every document using it.

## Ownership And Extension

[InlineIconRenderer](../../docs-viewer/build/docs_builder/inline_icons.py) owns exact lookup, sanitization, markup and Markdown integration. Ordinary and collection builders use it through [payload generation](../../docs-viewer/build/docs_builder/payloads.py). [Directive actions](../../docs-viewer/runtime/js/management/source-editor/directive-actions.js) owns the menu entry and selected filename placeholder.

Generated content can use the renderer directly and receive the same result as a manual token. Collection-to-icon selection and the [Related Links](Related_Links.md) presentation remain separate work. [Toolbar Icons](Toolbar_Icons.md) owns interface icon styling and its explicit public asset projection.
