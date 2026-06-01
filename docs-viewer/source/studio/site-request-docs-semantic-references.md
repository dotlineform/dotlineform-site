---
doc_id: site-request-docs-semantic-references
title: Docs Semantic References Request
added_date: 2026-05-18
last_updated: 2026-05-19
ui_status: paused
parent_id: site-request-docs-semantic-references-v2
viewable: true
---
# Docs Semantic References Request

Status:

- Implemented v1
- affected-doc build input is implemented
- see remaining follow-up section


## Summary

Add an authored semantic-reference token for Docs Viewer Markdown.

Implementation note:

- v1 is implemented in `docs-viewer/build/build_docs.py` for `work`, `series`, and `moment` references.
- Generated relationship artifacts are written under `assets/data/docs/scopes/<scope>/references/`.
- The management report is [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references).

The immediate need is to write a normal inline link to a catalogue work while also recording that the source doc semantically references a stable persisted record such as `work:00638`.

The wider design should allow the same mechanism to later support tags, terms, docs, concepts, people, or other registries without turning ordinary prose search into the relationship model.

Semantic links in this request are a dotlineform/Studio integration, not a generic portable Docs Viewer engine.
The referenced objects, such as works, series, moments, and tags, are owned and maintained by Studio and the public dotlineform site.
They are publicly surfaced only through this repo's Docs Viewer public installs, such as `/analysis/`, `/library/`, or future public routes in this repo that opt into the generated relationship data.

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
- validate that the semantic reference type and action are supported
- emit a generated relationship index that can power reverse-reference views

## Goals

- keep authoring lightweight inside Markdown
- preserve normal link behavior and accessibility
- avoid requiring raw HTML for common semantic links
- support a generated relationship index separate from text search
- validate semantic reference types and actions against an allowlist
- design the token grammar so future registries such as tags can use the same pipeline
- keep v1 narrow enough to implement safely in the existing docs builder

## Non-Goals

- do not infer all semantic relationships from plain words automatically
- do not replace Docs Viewer search
- do not require every catalogue link to become semantic
- do not build tag popups, term pages, or reference dashboards in v1
- do not introduce a generic database or runtime graph service
- do not make public pages depend on local Studio write services
- do not make Docs Viewer validate that a referenced Studio-owned object actually exists
- do not make semantic links a portable Docs Viewer feature for arbitrary installs

## Authoring Syntax

Use a custom inline reference token:

```md
[[ref:<kind>:<id>|<label>]]
```

The label may be omitted:

```md
[[ref:<kind>:<id>]]
```

Rules:

- `ref` identifies the token family
- `<kind>` identifies an allowed semantic type, such as `work`, `series`, `moment`, or `tag`
- `<id>` is the stable host-owned id for that type
- `<label>` is optional visible inline text
- when `<label>` is omitted, v1 may use host lookup data for a title when available, otherwise it should fall back to a stable visible id label
- an explicit `<label>` overrides the resolved title
- the target id may contain additional colons; parse the first segment after `ref:` as the kind, then treat the remaining text before `|` as the id

Optional modifiers may follow the token:

```md
[[ref:<kind>:<id>|<label>]]{action=link}
```

The default v1 action is `link`.
V1 should use a closed action allowlist.
Unsupported actions should warn and render as inert annotated text rather than as links.

Initial allowlist:

- `link`

Future actions can be reserved for later allowlist expansion, for example:

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
  "source_path": "docs-viewer/source/studio/example-doc.md",
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

The docs build should emit incremental relationship artifacts alongside the normal docs index and per-doc payloads.

The output should not be a single all-scope registry blob that rewrites whenever one source doc changes.
The current docs watcher already rebuilds the affected scope only, and `build_docs.py` already writes unchanged docs payloads incrementally.
Semantic-reference output should preserve that behavior by diffing and writing per-doc and per-target files.

Proposed paths:

- `assets/data/docs/scopes/<scope>/references/index.json`
- `assets/data/docs/scopes/<scope>/references/by-doc/<doc_id>.json`
- `assets/data/docs/scopes/<scope>/references/by-target/<target_kind>/<target_id_slug>.json`

The per-doc file is the canonical source for references authored by one doc:

```json
{
  "header": {
    "schema": "docs_semantic_references_by_doc_v1",
    "scope": "studio",
    "doc_id": "example-doc",
    "count": 1
  },
  "references": [
    {
      "source_scope": "studio",
      "source_doc_id": "example-doc",
      "source_title": "Example Doc",
      "source_path": "docs-viewer/source/studio/example-doc.md",
      "target_kind": "work",
      "target_id": "00638",
      "target_key": "work:00638",
      "target_href": "/works/00638/",
      "label": "3 symbols",
      "action": "link",
      "ordinal": 1
    }
  ]
}
```

The per-target file is a derived reverse lookup bucket:

```json
{
  "header": {
    "schema": "docs_semantic_references_by_target_v1",
    "scope": "studio",
    "count": 1
  },
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

The scope-level `references/index.json` should stay small.
It can list target summaries and output metadata needed by runtime reports, but it should avoid duplicating every reference when per-target buckets can serve reverse lookups.

This artifact should be separate from the docs search index.
Search is optimized for text matching; semantic references are relationship data.

### Watcher And Incremental Build Behavior

The v1 implementation should integrate with the current docs watcher without changing the watcher protocol.

Current watcher behavior:

- a changed Studio doc rebuilds only the `studio` docs scope
- a changed Library doc rebuilds only the `library` docs scope
- docs search can be targeted to affected `doc_id`s
- `build_docs.py` still parses the rebuilt scope, then writes only changed generated files

Semantic references should use the same pattern:

- parse references while building the affected scope
- compare generated per-doc reference JSON with existing `references/by-doc/<doc_id>.json`
- compare generated per-target buckets with existing `references/by-target/...`
- write only changed per-doc files, changed per-target files, and changed reference index metadata
- remove stale per-doc and per-target files when references or docs are deleted

For a single-doc edit that changes `[[ref:work:00638|3 symbols]]` to `[[ref:work:00639|3 symbols]]`, the expected writes should be limited to:

- the changed rendered doc payload, if the rendered HTML changed
- `references/by-doc/<doc_id>.json`
- `references/by-target/work/00638.json`
- `references/by-target/work/00639.json`
- `references/index.json` only if target summaries or counts changed

The implementation should avoid rewriting unrelated target buckets.

## Registry Resolver Model

Add a small resolver layer that maps an allowed `kind` to host-specific URL and optional display-title behavior.
The resolver validates supported semantic types; it does not make target existence a Docs Viewer validity rule.
For example, `work:00001` and `work:99999` are both syntactically valid work references as far as Docs Viewer is concerned, even if only one exists in Studio-owned work data.
Missing public targets can still behave like normal broken links, such as a URL that returns a 404.

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
- display title if available from host data
- canonical `href`

V1 rendering policy:

- allowed semantic types with allowed actions render as normal links using the type/id URL pattern
- target ids are not checked for existence by Docs Viewer
- missing target ids can therefore produce normal broken public links
- unsupported semantic types warn or error and render as inert annotated text
- unsupported actions warn only and render as inert annotated text
- warning-only behavior keeps local docs readable while making diagnostics visible in build output and reports

The docs builder should not hard-code tag, work, or series policy directly into token parsing.
Parsing should produce a neutral token object, and the resolver should own registry-specific behavior.

## V1 Implementation Plan

### Task 1. Define Token Parser

Add a parser for inline semantic-reference tokens before Markdown is rendered.

Minimum behavior:

- detect `[[ref:<kind>:<id>|<label>]]`
- detect `[[ref:<kind>:<id>]]` with omitted label
- detect optional trailing modifiers such as `{action=link}`
- escape rendered labels
- preserve unknown or malformed tokens as visible text with a build warning
- ignore tokens inside fenced code blocks and inline code

### Task 2. Add Catalogue Record Resolvers

Implement v1 resolvers for:

- work ids
- series ids
- moment ids

Resolvers should use host-specific URL rules and optional lookup data, then return canonical public hrefs:

- `/works/<work_id>/`
- `/series/<series_id-or-slug>/` with the slug lookup required by the current route model
- `/moments/<moment_id>/`

Docs Viewer does not validate that the target id exists in Studio-owned data.
If a valid semantic type and id produce a public URL that has no matching object, the rendered link behaves like any other broken link.

### Task 3. Render Semantic Links

During docs build, replace each valid token with normal HTML:

```html
<a href="..." data-ref-kind="..." data-ref-id="..." data-ref-action="...">...</a>
```

The emitted HTML should remain accessible and usable without Docs Viewer JavaScript.

When a token is malformed, uses an unsupported semantic type, or uses an unsupported action, render inert annotated text instead of a link.
The exact HTML can be decided during implementation, but it should not navigate.
For example:

```html
<span data-ref-kind="work-detail" data-ref-id="00001-001" data-ref-status="unsupported-kind">detail</span>
```

### Task 4. Emit Incremental Reference Artifacts

Collect all parsed references for supported semantic types while building each scope and write the incremental reference artifacts under that scope's generated docs data output.

The artifacts should include enough source metadata for reverse-reference UI:

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

The write plan should report:

- changed per-doc reference files
- changed per-target reference files
- stale per-doc reference files removed
- stale per-target reference files removed
- whether the reference index metadata changed

### Task 5. Validate References

Add validation coverage for:

- unsupported target kinds
- malformed tokens
- label escaping
- duplicate references in one doc
- tokens inside code blocks
- generated reference artifact stability
- unchanged unrelated target buckets staying untouched during single-doc edits

The existing broken-links audit can later read semantic references too, but v1 should warn clearly during docs build.

### Task 6. Add A Management Report

Add a Docs Viewer report that lists semantic references.

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

Once the generated reference artifacts are stable, public work, series, moment, or tag pages could show "Referenced in docs" sections.

That should be a later change because it affects public page layout and generated public data dependencies.

## Remaining Follow-Up After V1

### Affected-Doc Build Input

Implemented on 2026-05-19.
`build_docs.py` now accepts targeted same-scope docs payload input:

```sh
./docs-viewer/build/build_docs.py --scope studio --write --only-doc-ids example-doc
```

Current behavior:

- the caller must select exactly one scope
- the builder still rebuilds the scope index from current source metadata
- selected docs are rendered and written through the normal per-doc payload path
- selected docs' semantic-reference by-doc records are refreshed
- semantic-reference by-target buckets are derived from refreshed selected by-doc records plus existing unselected by-doc records, so stale target buckets are removed when selected docs move or drop references
- orchestration falls back to a full same-scope docs payload rebuild when existing generated output is missing or incomplete

Implemented orchestration:

- docs-management mutation planners pass targeted docs ids when their dependency rules are explicit
- Docs Import source writes pass targeted docs ids for create and overwrite
- Library returned-package summary and hierarchy apply writes pass targeted docs ids for changed source docs
- the live watcher passes targeted docs ids for source changes whose affected ids can be computed from its parsed snapshot
- source-config settings writes, explicit rebuilds, missing generated output, and ambiguous watcher changes remain full-scope fallbacks

Remaining follow-up:

- resolver-data changes outside docs source, such as catalogue title or route changes, should trigger a full same-scope docs payload rebuild until they have explicit affected-id rules
- future resolver kinds should define their targeted rebuild dependencies before using targeted docs payload writes

### Reference-Aware Broken Link Audit

Extend the broken-links audit to understand semantic references after v1 output exists.
The audit can then report broken semantic-reference hrefs or unsupported semantic tokens separately from ordinary broken `href` links.

## Decisions

- v1 validates supported semantic types and actions, not target existence
- v1 links can therefore point to missing Studio/public objects and behave like ordinary broken links
- omitted labels use the current host title when available and otherwise fall back to a stable id label
- explicit labels override resolved titles
- v1 includes `series` support, including slug lookup required by the current route model
- `action` uses a closed allowlist from the start
- actions outside the allowlist warn and render as inert annotated text
- reverse-reference reports are Docs Viewer reports
- semantic links are dotlineform/Studio-specific and are not part of portable Docs Viewer core

## Acceptance Criteria

- author can write `[[ref:work:00638|3 symbols]]` in a Docs Viewer Markdown source doc
- author can write `[[ref:work:00638]]` and get the current resolved work title as link text
- rendered document shows a normal link to `/works/00638/`
- rendered link includes stable `data-ref-*` attributes
- generated scope data includes a semantic reference record for `work:00638`
- single-doc edits only rewrite changed per-doc/per-target reference artifacts
- syntactically valid ids for allowed semantic types render as links even when the target object does not exist
- unsupported semantic types such as `work-detail` produce clear diagnostics
- unsupported actions warn and render as inert annotated text
- series semantic references resolve the current public series route
- normal Markdown links continue to behave as plain links with no semantic relationship
- the implementation leaves room for `[[ref:tag:subject:nature|nature]]` without changing the token grammar
