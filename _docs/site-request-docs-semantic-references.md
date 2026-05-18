---
doc_id: site-request-docs-semantic-references
title: Docs Semantic References Request
added_date: 2026-05-18
last_updated: 2026-05-18
parent_id: change-requests
sort_order: 71000
---
# Docs Semantic References Request

Status:

- proposed

## Summary

Add an authored semantic-reference token for Docs Viewer Markdown.

The immediate need is to write a normal inline link to a catalogue work while also recording that the source doc semantically references a stable persisted record such as `work:00638`.

The wider design should allow the same mechanism to later support tags, terms, docs, concepts, people, or other registries without turning ordinary prose search into the relationship model.

## Problem

A normal Markdown link only records a browser destination:

```md
[3 symbols](/works/00638/)
```

That link does not say why the target matters.
If several docs refer to work `00638`, the current way to find them is effectively a search problem.
Search can find URL text, labels, and nearby prose, but it cannot reliably distinguish a real semantic reference from an incidental link.

The docs system needs a small authored marker that can mean:

- render this as a usable link
- identify the persisted object being referenced
- validate that the target exists
- emit a generated relationship index that can power reverse-reference views

## Goals

- keep authoring lightweight inside Markdown
- preserve normal link behavior and accessibility
- avoid requiring raw HTML for common semantic links
- support a generated relationship index separate from text search
- validate references against the appropriate registry
- design the token grammar so future registries such as tags can use the same pipeline
- keep v1 narrow enough to implement safely in the existing docs builder

## Non-Goals

- do not infer all semantic relationships from plain words automatically
- do not replace Docs Viewer search
- do not require every catalogue link to become semantic
- do not build tag popups, term pages, or reference dashboards in v1
- do not introduce a generic database or runtime graph service
- do not make public pages depend on local Studio write services

## Authoring Syntax

Use a custom inline reference token:

```md
[[ref:<kind>:<id>|<label>]]
```

Rules:

- `ref` identifies the token family
- `<kind>` identifies the target registry, such as `work`, `series`, `moment`, or `tag`
- `<id>` is the stable registry id
- `<label>` is the visible inline text
- the target id may contain additional colons; parse the first segment after `ref:` as the kind, then treat the remaining text before `|` as the id

Optional modifiers may follow the token:

```md
[[ref:<kind>:<id>|<label>]]{action=link}
```

The default v1 action is `link`.
Future actions can be reserved without implementing them immediately, for example:

- `definition`
- `references`
- `popover`

## Current Work-Link Example

Source Markdown:

```md
The project connects back to [[ref:work:00638|3 symbols]].
```

V1 resolver behavior:

- target kind: `work`
- target id: `00638`
- registry source: catalogue work records
- fallback href: `/works/00638/`
- label: `3 symbols`
- action: `link`

Rendered HTML:

```html
<a href="/works/00638/" data-ref-kind="work" data-ref-id="00638" data-ref-action="link">3 symbols</a>
```

Generated reference record:

```json
{
  "source_scope": "studio",
  "source_doc_id": "example-doc",
  "source_title": "Example Doc",
  "source_path": "_docs/example-doc.md",
  "target_kind": "work",
  "target_id": "00638",
  "target_key": "work:00638",
  "target_href": "/works/00638/",
  "label": "3 symbols",
  "action": "link"
}
```

This gives the browser a normal link and gives the generated data layer a stable relationship.

## Future Tag Example

Source Markdown:

```md
This section is about [[ref:tag:subject:nature|nature]].
```

Possible future resolver behavior:

- target kind: `tag`
- target id: `subject:nature`
- registry source: tag registry
- label: `nature`
- default action: `link`
- fallback href: a tag search route, tag report route, or future tag page

Possible rendered HTML:

```html
<a href="/search/?scope=catalogue&q=tag%3Asubject%3Anature" data-ref-kind="tag" data-ref-id="subject:nature" data-ref-action="link">nature</a>
```

If a future author wants a richer interaction, the Markdown could specify it:

```md
[[ref:tag:subject:nature|nature]]{action=definition}
```

Possible enhanced HTML:

```html
<a href="/search/?scope=catalogue&q=tag%3Asubject%3Anature" data-ref-kind="tag" data-ref-id="subject:nature" data-ref-action="definition">nature</a>
```

The link remains useful without JavaScript.
Docs Viewer or a future public runtime can progressively enhance `data-ref-action="definition"` into a popup, side panel, or report link.

## Generated Relationship Index

The docs build should emit a scope-level relationship artifact alongside the normal docs index and per-doc payloads.

Proposed path:

- `assets/data/docs/scopes/<scope>/references.json`

Proposed top-level shape:

```json
{
  "header": {
    "schema": "docs_semantic_references_v1",
    "scope": "studio",
    "count": 1
  },
  "references": [],
  "targets": []
}
```

`references[]` should be the canonical flat list.
`targets[]` can be a derived grouping for fast reverse lookup:

```json
{
  "target_key": "work:00638",
  "target_kind": "work",
  "target_id": "00638",
  "target_href": "/works/00638/",
  "count": 1,
  "references": [
    {
      "source_scope": "studio",
      "source_doc_id": "example-doc",
      "source_title": "Example Doc",
      "label": "3 symbols",
      "action": "link"
    }
  ]
}
```

This artifact should be separate from the docs search index.
Search is optimized for text matching; semantic references are relationship data.

## Registry Resolver Model

Add a small resolver layer that maps `kind` to a registry-specific lookup.

Initial registry kinds:

- `work`
- `series`
- `moment`

Future registry kinds:

- `tag`
- `term`
- `doc`
- `concept`
- `person`

Each resolver should return:

- normalized `target_kind`
- normalized `target_id`
- `target_key`
- display title if available
- canonical `href`
- existence/status metadata
- warnings when the id is missing, unpublished, or not linkable

The docs builder should not hard-code tag, work, or series policy directly into token parsing.
Parsing should produce a neutral token object, and the resolver should own registry-specific behavior.

## V1 Implementation Plan

### Task 1. Define Token Parser

Add a parser for inline semantic-reference tokens before Markdown is rendered.

Minimum behavior:

- detect `[[ref:<kind>:<id>|<label>]]`
- detect optional trailing modifiers such as `{action=link}`
- escape rendered labels
- preserve unknown or malformed tokens as visible text with a build warning
- ignore tokens inside fenced code blocks and inline code

### Task 2. Add Catalogue Record Resolvers

Implement v1 resolvers for:

- work ids
- series ids
- moment ids

Resolvers should read existing catalogue source or generated lookup data, then return canonical public hrefs:

- `/works/<work_id>/`
- `/series/<series_id-or-slug>/` if the current route model requires slug resolution
- `/moments/<moment_id>/`

The implementation must decide whether v1 allows references to draft/unpublished catalogue records.
If it allows them, the generated reference record should carry status metadata and the rendered href should have a safe fallback.

### Task 3. Render Semantic Links

During docs build, replace each valid token with normal HTML:

```html
<a href="..." data-ref-kind="..." data-ref-id="..." data-ref-action="...">...</a>
```

The emitted HTML should remain accessible and usable without Docs Viewer JavaScript.

### Task 4. Emit `references.json`

Collect all resolved references while building each scope and write `references.json` under that scope's generated docs data output.

The artifact should include enough source metadata for reverse-reference UI:

- source scope
- source doc id
- source title
- source path
- label
- target kind
- target id
- target href
- action
- ordinal or source order where useful

### Task 5. Validate References

Add validation coverage for:

- missing target ids
- unsupported target kinds
- malformed tokens
- label escaping
- duplicate references in one doc
- tokens inside code blocks
- generated `references.json` stability

The existing broken-links audit can later read semantic references too, but v1 should at minimum fail or warn clearly during docs build.

### Task 6. Add A Management Report

Add a Docs Viewer report or Studio maintenance page that lists semantic references.

Minimum useful view:

- target kind
- target id
- target href
- reference count
- source doc links

This gives the feature immediate value without needing to place reverse-reference panels on public work pages.

### Task 7. Document Authoring Rules

Update the owning docs after implementation:

- Docs Viewer authoring docs
- Docs Viewer builder docs
- catalogue/docs relationship notes if needed

The docs should explain when to use a semantic reference instead of a normal link.

## Future Extensions

### Tags

Add `tag` as a resolver kind after the tag registry route and desired display behavior are clear.

Possible tag actions:

- `link`: open a tag search or tag page
- `definition`: show the tag definition if one exists
- `references`: show docs and catalogue records that reference the tag

### Terms

Add a lightweight controlled vocabulary registry for terms that are not catalogue records and not canonical tags.

Possible term actions:

- `definition`
- `references`
- `link`

### Public Reverse References

Once `references.json` is stable, public work, series, moment, or tag pages could show "Referenced in docs" sections.

That should be a later change because it affects public page layout and generated public data dependencies.

## Open Decisions

- Should v1 references to draft catalogue records render as links, warnings, or inert annotated text?
- Should unresolved semantic references fail the build or warn only?
- Should labels be required, or should `[[ref:work:00638]]` resolve the current title automatically?
- Should the first implementation support `series` slug lookup, or start with `work` only?
- Should `action` be limited to a closed allowlist from the start?
- Should reverse-reference reports be Docs Viewer reports, Studio pages, or both?

## Acceptance Criteria

- author can write `[[ref:work:00638|3 symbols]]` in a Docs Viewer Markdown source doc
- rendered document shows a normal link to `/works/00638/`
- rendered link includes stable `data-ref-*` attributes
- generated scope data includes a semantic reference record for `work:00638`
- invalid ids produce clear diagnostics
- normal Markdown links continue to behave as plain links with no semantic relationship
- the implementation leaves room for `[[ref:tag:subject:nature|nature]]` without changing the token grammar
