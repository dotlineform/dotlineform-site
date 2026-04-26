---
doc_id: user-guide-docs-html-import
title: "Docs HTML Import"
added_date: 2026-04-24
last_updated: 2026-04-26
parent_id: user-guide
sort_order: 20
---
# Docs HTML Import

Use this page when you have a staged self-contained HTML export that should become a Library, Analysis, or Studio docs source doc.

The Studio route is:

- `/studio/docs-import/`

## Before You Start

Put the original HTML file in:

- `var/docs/import-staging/`

This staging directory is repo-local and untracked, so it is a practical place to keep the original export nearby while you test imports.

## What The Page Does

The import page:

- lists staged `.html` files from `var/docs/import-staging/`
- lets you choose whether the imported doc should publish into `library`, `analysis`, or `studio`
- optionally keeps clearly identifiable prompt/meta blocks
- converts the HTML into a best-attempt Markdown source doc
- keeps literal pipe characters in source text as text, including mathematical notation such as `I(X;Y|Z)`
- validates the generated Markdown through the current Jekyll docs renderer before write success
- writes a new doc immediately when the target is free
- asks for explicit confirmation before overwriting an existing doc

## Basic Workflow

1. Open `/studio/docs-import/`.
2. Choose the staged HTML file.
3. Choose the publish scope:
   - `library` for the public Library viewer
   - `analysis` for the public Analysis viewer
   - `studio` for the Studio docs viewer
4. Decide whether to include obvious prompt/meta blocks.
5. Click `Import`.

If the generated import target does not already exist, the importer writes the new Markdown source doc immediately.

New `library` and `analysis` imports use the same default import behavior: they are generated and opened for review through manage-mode viewer links before becoming normal public tree items.

## Prompt / Meta Option

When `Include obvious prompt/meta blocks` is enabled:

- clearly identifiable prompt/meta sections are kept
- they are simplified into wrapped quoted prose

When it is disabled:

- those sections are dropped when the importer can identify them clearly

If you are unsure, start with the option off and only enable it when the prompt/meta content is part of the document you actually want to keep.

## Overwrite Behavior

If the generated import target already matches an existing doc:

- the page shows a warning naming the existing target
- nothing is overwritten yet
- you must explicitly confirm overwrite to replace that source doc

Overwrite keeps:

- the existing `doc_id`
- the existing filename
- the existing `parent_id`
- the existing `sort_order`

Before overwrite, the importer creates an untracked backup under:

- `var/docs/backups/`

## What To Expect In The Result

After a successful import, the page reports:

- whether the operation created or overwrote a doc
- the target scope
- the final `doc_id`
- the imported title
- the original staged source path
- the viewer link for the imported doc
- any non-routine conversion warnings

## Current Practical Limits

This importer is intentionally best-effort.

Expect good results for:

- normal prose docs
- headings and lists
- simple tables
- external links
- plain-text `http://` and `https://` URLs, which become clickable autolinks
- inline SVG diagrams
- technical notation that needs safe inline HTML such as subscripts

Expect simplified output for:

- presentation-heavy layout wrappers
- interactive disclosure UI such as `details/summary`
- prompt/meta shells
- image cases where the source is unclear or awkward for Markdown

## Related References

- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
