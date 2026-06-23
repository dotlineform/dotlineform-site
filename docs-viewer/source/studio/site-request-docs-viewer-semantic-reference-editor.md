---
doc_id: site-request-docs-viewer-semantic-reference-editor
title: Docs Viewer Semantic Reference Editor Request
added_date: 2026-05-27
last_updated: 2026-06-23
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Semantic Reference Editor Request

Status: v2 backlog

This request now tracks enhancements beyond the current Semantic References Editor.
Related source-editing workflows for external exchange and returned text writeback are tracked separately in [Shareable Content Blocks Request](/docs/?scope=studio&doc=site-request-shareable-content-blocks).

Current implemented behavior is documented in:

- [Semantic References Editor](/docs/?scope=studio&doc=docs-viewer-semantic-references-editor)
- [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation)
- [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references)

## Current Baseline

The current v1 editor integration:

- runs only in manage-mode Markdown source editing
- hosts `semantic-token-picker` in the existing info panel
- reads supported token kinds from the semantic-reference registry
- reads picker targets from the generated semantic target lookup
- uses selected source text as a search seed and replacement range
- supports manual picker search when no text is selected
- inserts `[[ref:<kind>:<id>|<target title>]]`
- always uses the selected target title as the inserted label
- inserts at the current caret when no text is selected
- keeps all changes in the local source buffer until `Rebuild doc`

The current implementation intentionally does not validate target existence as source-write authority.
Missing, stale, draft, unpublished, or deleted targets remain report/audit concerns rather than builder or write failures.

## V2 Goals

V2 should improve authoring speed without changing the ownership model.

Useful enhancement areas:

- richer insertion-point assistance
- direct id entry
- exact target lookup for high-cardinality kinds
- additional token kinds
- semantic directive actions beyond links
- better audits for suspicious token-like text
- optional label editing workflows after insertion

These enhancements should still use the registry and generated browser-safe data where possible.
They should not add server endpoints or write-path validation unless the data cannot safely be supplied through static config/generated artifacts.

## Deferred Enhancements

### Cursor Seed Expansion

When the source editor has a collapsed cursor, the picker could detect the word or id around the cursor and use it as the search query.

Open decisions:

- punctuation-boundary rules
- Markdown-link boundary rules
- whether expansion should be preview-only or alter the replacement range
- how to avoid surprising replacement of nearby prose

### Direct Id Entry

The editor could support exact id entry for users who already know a target id.

Examples:

- `00638`
- `005`
- `lotus-pond`

Open decisions:

- whether direct id entry shares the search input or gets a distinct mode
- whether id matches should rank ahead of title matches only when the query looks id-like
- whether direct id entry should require an exact generated target record before insertion

### Exact Target Records

Some future token kinds may have too many records, ambiguous titles, or id-heavy workflows.
Those kinds may need generated exact-target records in addition to the title-weighted target lookup.

Open decisions:

- file shape for exact-target records
- whether exact records are per kind, per prefix, or per id
- how high-cardinality kinds affect browser payload size
- whether exact records should be loaded lazily

### Additional Token Kinds

Current v1 kinds are:

- `work`
- `series`
- `moment`

Potential future kinds include:

- `work_detail`
- tags
- tag aliases
- other repo-local semantic targets

Adding a kind should normally require:

- a new registry kind record
- a target lookup generator update if the kind is picker-searchable
- Python and JavaScript normalizer support only if the kind needs a new id shape
- focused tests for registry normalization, rendered output, and lookup rows

Adding a kind should not require:

- new info-panel host code
- new source editor lifecycle code
- new source read/write/rebuild endpoints
- hardcoded supported-kind lists in route controllers

### Semantic Directive Actions

Future semantic tokens may need actions beyond linking to a target.
For example, a `tag` target could support both:

- `link`: link to the corresponding Analysis doc
- `field`: insert a canonical field value such as the tag description

This likely means reintroducing registry `actions`, with stricter ownership than the original exploratory schema.
The useful rule is:

```text
kind + action = supported semantic directive
```

Example capability shape:

- `tag + link`: render a link to the Analysis doc for the tag
- `tag + field`: render a canonical value from `analytics-app/data/canonical/tag-registry.json`
- `tag + related_works`: render links to works using the tag from `analytics-app/data/canonical/tag-assignments.json`
- `work + link`: current semantic reference behavior
- `series + link`: current semantic reference behavior

Actions should not all be treated as route variants.
A link action owns route construction and reference artifacts.
A field action owns data-source resolution, allowed fields, escaping/rendering, missing-value behavior, and provenance.
A related-list action owns relationship lookup, sorting, empty-state behavior, and link rendering.

Possible readable source forms:

```md
[[ref:tag:slow-looking]]
[[field:tag:slow-looking:description]]
[[list:tag-related-works:slow-looking]]
```

The registry should say which kind/action pairs are allowed and which resolver owns them.
Focused resolver modules should implement the behavior; the builder should not grow ad hoc per-token feature branches.

Open decisions:

- whether to use separate token families such as `ref`, `field`, and `list`, or one generic semantic token with action attributes
- how to represent allowed field names and missing-value behavior in the registry
- whether generated field/list output emits separate provenance artifacts
- how much data can be safely shipped in browser-safe lookup artifacts for editor assistance
- whether tag docs require one doc per tag in the Analysis scope before `tag + link` is enabled

### Label Editing

The current editor inserts the target title as the label.
That keeps generated link text canonical at insertion time.

Future label editing could support:

- editing the inserted label after insertion
- preserving a deliberate author label while still choosing a canonical target
- warning when a label differs from the target title

Open decisions:

- whether label warnings belong in the source editor or semantic references report
- whether custom labels are common enough to justify UI
- whether the picker should ever offer a custom label field before insertion

### Suspicious Token Audits

The semantic references report could scan for suspicious token-like text that the builder leaves literal.

Examples:

- unsupported kind
- invalid id
- unsupported action
- malformed brackets or separators

This should remain report/audit behavior.
It should not turn builder success or source writes into semantic validation failures.

## V2 Constraints

Future enhancements should preserve these constraints:

- source editing remains owned by the Markdown source editor
- token insertion remains local until `Rebuild doc`
- supported kinds and route behavior come from the semantic-reference registry
- semantic directive actions come from registry-declared kind/action pairs
- browser-side target assistance uses generated browser-safe data where practical
- the picker remains a manage-only info-panel hosted view
- public Docs Viewer routes do not load semantic picker UI or CSS
- the builder remains the final parse/render authority during rebuild
- reports own stale-target and suspicious-token auditing

## Risks To Watch

- direct id workflows could make the picker feel like a validation form rather than an authoring helper
- high-cardinality target kinds could make browser lookup payloads too large
- custom label support could reintroduce misspelled or inconsistent link text
- cursor expansion could replace unintended text if boundaries are unclear
- target-existence checks could drift into build/write failure behavior that belongs in reports
