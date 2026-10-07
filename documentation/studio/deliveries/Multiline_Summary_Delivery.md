---
draft: false
doc_id: d-20261007-122704-b0389d
title: Multiline Summary Delivery
added_date: "2026-10-07 12:27:04"
last_updated: "2026-10-07 12:27:04"
summary: Proposed preservation of Summary line and paragraph breaks through front matter, source rewrites, document rendering, packages and HTML Export.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Multiline Summary Delivery

## Current And Next State

Status: proposed; documentation only. The user requested this delivery to retain the consequences and separate implementation pieces discussed on 2026-10-07. Code implementation, tests, generated-data changes and publication have not been authorized by that request. Next: confirm the bounded syntax and whitespace rules at readiness, then obtain implementation approval. This delivery is parented to [Planned Features](../Planned_Features.md) and extends the existing [Summary block](../Builder.md#summary-block).

Current source inspection found separate front-matter readers in the builder and source model, builder whitespace normalization that flattens Summary, source-rewrite helpers that scan individual lines, escaped single-paragraph Summary rendering, and an Info panel that assigns Summary to one paragraph's text content. Package Prepare takes Summary from the builder's source record; its Summary field mappings and returned-record handling already carry strings without their own whitespace flattening. Package body conversion starts from rendered HTML, while [Export](../Export.md) starts from saved generated HTML and writes both a browseable snapshot and `portable.html`. This records the starting point, not implementation readiness or behavioral verification.

## Requirements

The complete result lets an author maintain line and paragraph breaks once in front-matter Summary and retain that meaning through source edits, document builds, the reader, packages, returned import and HTML Export.

- Accept standard YAML literal-block authoring for `summary`. The proposed bounded syntax is `|` and `|-`; generated multiline front matter uses `|-`. Confirm this limit at readiness. Folded `>` blocks, `|+`, explicit indentation indicators, nested YAML, anchors, tags and a full YAML migration are separate scope decisions.
- Preserve internal line breaks and blank lines as plain-text content. Normalize line endings consistently and define treatment of outer whitespace and the final newline before implementation; the proposed display behavior omits outer blank lines and preserves internal line/paragraph boundaries. Keep existing single-line values and double-quoted `\n` input valid, without compatibility aliases or a bulk source conversion.
- Keep parsing, validation and serialization consistent across ordinary and configured collection sources, Source Save, metadata/body rewrites, package Review and supported returned Import. Literal-block contents may contain colons, `#`, field-looking text or indented `---`; those are Summary text, not metadata fields, comments or closing delimiters. Malformed blocks must produce useful source errors rather than silently becoming unrelated fields.
- Preserve Summary's string type in by-ID and list metadata. Apply Summary-specific text handling without changing whitespace or field-type behavior for titles, identities, dates, readiness, Subject or other metadata. A change to actual Summary content or internal breaks follows existing `last_updated`/Recent rules; changing between equivalent source representations should not manufacture a content change.
- Render escaped plain text with explicit HTML line breaks within paragraphs and paragraph elements for blank-line boundaries. Markdown, HTML and directive-looking text inside Summary remain literal. Keep the existing Summary panel style and empty-summary omission. The Info panel must display the same line/paragraph meaning safely, without adding another Markdown interpretation path.
- Preserve line/paragraph meaning in Package Prepare's `summary` and `current_summary`, rendered-derived Markdown/plain-text `content`, supported returned-package review/import, and both HTML Export outputs. YAML syntax belongs in Markdown front matter; structured package fields contain decoded strings, and HTML contains rendered text. No package schema change is proposed solely because strings contain newlines.
- Search continues to normalize whitespace for indexing its Summary metadata field and omit active `[[summary]]` directives from body terms. Multiline authoring does not add YAML markers to searchable Summary text, change Search membership or require an automatic Search rebuild.

## Deliverables

- Consistent literal-block reading and source writing through the existing source/build owners, with shared parsing responsibility where practical instead of two independently extended grammars. The implementation must preserve existing scalar field semantics; introducing a full YAML parser requires a separate decision if it changes those semantics.
- Summary-specific metadata preservation, multiline `[[summary]]` output and safe Info-panel presentation in local and public readers. Do not change image-token or Catalogue-image summaries under this document-Summary feature.
- Package Prepare and supported return handling that preserve multiline strings, plus rendered-content conversion that retains explicit breaks. Existing selection, missing-summary filtering, provenance and collection return-eligibility rules continue through their current owners.
- HTML Export and `portable.html` that retain the generated Summary's breaks, with any necessary snapshot styling contained in the existing Export owner. Export remains a consumer of generated content and does not begin reading or rebuilding canonical source.
- Required shared/public runtime projection, an explicitly scoped Working generated-output reconciliation, and durable authoring/package/Export guidance. Public document data updates through the existing separately authorized Publish operation.

### Representation At Each Boundary

| Boundary | Intended representation and consequence |
| --- | --- |
| Markdown source | `summary: \|` or `summary: \|-` followed by indented literal text; canonical multiline writes use `\|-`. |
| Parsed/source/build metadata | One string with real newline characters; do not carry the `\|` marker or indentation used only to delimit the block. |
| JSON/JSONL packages and generated JSON | A string encoded with JSON `\n` escapes. JSON parsing restores newlines; keep each JSONL record on one physical line. |
| Generated document and Export HTML | Escaped text with explicit paragraph/line-break markup; preserve meaning without relying on `white-space` CSS alone. |
| Package Markdown/plain-text body | Converted rendered content retains line/paragraph meaning, even when its textual representation differs from canonical source. |
| Supported returned package applied to source | Preserve decoded Summary breaks and serialize multiline front matter using `\|-`; preserve existing Import authority and field ownership. |
| Search | Normalized text for indexing; literal-block markers and source indentation are not content. |

## Process

The author writes Summary in Source, keeps `[[summary]]` as a standalone body directive where desired, and saves through the existing workflow:

```md
---
summary: |-
  First line.
  Second line.

  Another paragraph.
---

[[summary]]
```

This excerpt omits normal identity, dates and readiness fields. Summary remains plain text. `|` includes a final newline in the parsed YAML value; `|-` removes it. The agreed normalization rules determine whether that outer newline has any display or Recent significance. The literal-block syntax reference is the [YAML block scalar specification](https://yaml.org/spec/1.2.2/#81-block-scalar-styles).

Source Save retains its current completion boundary and the watcher performs normal document projection work. Metadata-only operations must preserve the Summary value and must not edit field-looking lines inside it. A returned supported package carries, for example, `"summary": "First line.\nSecond line.\n\nAnother paragraph."`; existing whole-package Import applies the string and writes readable multiline source.

Package Prepare reads current source, so it must receive the newline-preserving Summary through its existing builder-backed source context. Its body may contain the expanded Summary only when the document actually includes `[[summary]]`; this feature adds no automatic placement or deduplication between body text and Summary fields. HTML Export reads generated payloads, so it reflects multiline output only after the owning document build has produced it. Existing exported folders, already prepared packages and saved public document data do not change when runtime code changes.

## Delivery Steps

### MS-0 — Readiness

- [ ] Confirm `|`/`|-` support, Summary-only scope, newline/outer-whitespace semantics, existing scalar preservation and the complete source → render → package/Export outcome.
- [ ] Confirm the implementation order and broad ownership across source/build, reader, package and Export. Stop for an explicit scope decision if a full YAML migration, new package schema/profile, new return authority or unrelated multiline field support becomes necessary.

Verification budget: concise read-only inspection of the owning boundaries and current policy; no prototypes, generated writes or executable tests. Gate: the specification is coherent and implementation is explicitly approved. Record: proposed; the discussion and source observations are captured above, but this gate has not been completed.

### MS-1 — Parsing And Source Rewrites

- [ ] Implement consistent literal-block parsing and validation without changing unrelated scalar types or accepted single-line authoring.
- [ ] Preserve Summary through Source Save, general formatting, timestamp updates, collection-placement rewrites and supported Import writes. Field detection must identify top-level metadata and ignore indented Summary content; generic source rewrites must not leave orphaned block lines.
- [ ] Compare semantic Summary content under the agreed whitespace rules for existing edit timestamps and Recent behavior; preserve body text and unrelated fields.

Verification budget: focused changed-Python lint/syntax and bounded source review for indentation, blank lines, field-looking text and rewrite safety; normally seconds for diagnostics, with source-review cost dependent on the final diff. Tests or temporary regression scripts require their own approved specification. Gate: parsing and all in-scope write paths agree on the same Summary value; any behavioral evidence gaps are named. Record: not started.

### MS-2 — Metadata And Reader Rendering

- [ ] Replace Summary's blanket whitespace flattening at its owning builder boundary while retaining Search's separate normalization and other metadata semantics.
- [ ] Render Summary paragraphs and intra-paragraph breaks explicitly and safely; retain empty/literal-token behavior and existing panel styling.
- [ ] Update Info-panel Summary presentation and any in-scope reader consumer that would otherwise flatten or misinterpret the multiline string. Check ordinary and configured collection payloads through their shared owners.

Verification budget: changed-source lint/syntax and bounded review of escaping, metadata handoff and generated HTML shape; inexpensive static diagnostics do not prove rendering behavior. User manual review covers line/paragraph spacing, Info-panel presentation and empty/literal content. No browser automation is implied. Gate: document and Info-panel behavior is coherent, and visual acceptance or its pending state is recorded. Record: not started.

### MS-3 — Packages, Review And Returned Import

- [ ] Preserve `summary` and `current_summary` as JSON strings with newline escapes, retain missing-summary filtering for whitespace-only values, and keep existing tree/profile mappings within their current contracts.
- [ ] Inspect rendered HTML → Markdown/plain-text conversion and change it only where necessary to retain the Summary's explicit line/paragraph breaks. CSS-only preservation is insufficient for these converters.
- [ ] Carry multiline strings through supported returned-record normalization, read-only Docs Review materialization and whole-package Import, then serialize readable multiline Summary source. Check any retained canonical-Markdown package intake against the same source parser without introducing a new export profile or return path.

Verification budget: focused static diagnostics and bounded review of field mapping, conversion, JSON/JSONL serialization and existing review/import ownership. Real package preparation writes exports/provenance; review materialization writes review output; Import mutates canonical source. Record exact selections, effects and costs before exercising these operations. Tests, new fixtures and executable regression scripts remain separately approved work. Gate: the package string and rendered-body boundaries preserve meaning without changing eligibility or mutation authority; behavioral evidence limits are explicit. Record: not started.

### MS-4 — Export, Projection And Generated Follow-Through

- [ ] Preserve explicit Summary breaks in the browseable HTML snapshot and `portable.html`, accounting for their own rendering/styles. Do not add source reads, automatic rebuilds or YAML syntax to HTML Export.
- [ ] For changed inventoried shared runtime files, run `bin/site-code-update`, inspect the exact `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate`. Update the inventory only if a file's public status actually changes.
- [ ] Agree the necessary Working document reconciliation because a global parser/renderer contract is changing. Use an intentional docs-only reconciliation with `--skip-media-builds` when authorized; avoid source migration and registered-media work. Record that Search stays unchanged until separately requested and public document data awaits authorized Publish.

Verification budget: public projection/check/site validation for actual shared changes; runtime/cost depends on the final inventory and should be recorded before running. Existing Export actions write external snapshot folders, and generated reconciliation writes Working output, so define the real selection and write effects before execution. User manual review covers both Export representations and public presentation. Gate: required runtime projection is verified, generated follow-through is accounted for, and existing packages/exports/public data are not represented as automatically updated. Record: not started.

### MS-5 — Code Review

- [ ] Review the final bounded diff for duplicated parser rules, accidental full-YAML semantics, block-content mistaken for metadata, unsafe HTML insertion, newline loss in conversions, unrelated Summary fields, compatibility residue and publication ownership drift.
- [ ] Reconcile completion claims with exact evidence and resolve in-scope findings; rerun only checks affected by review changes.

Verification budget: bounded final-diff review and only justified follow-up diagnostics; no repository audit or automatic suite. Gate: findings are resolved or explicitly scoped for later work, and material evidence gaps remain visible. Record: not started.

### MS-6 — Documentation And Closeout

- [ ] Transfer shipped syntax and normalization/rendering rules to [Builder](../Builder.md), source rewrite/edit semantics to their durable owner, and package/Export consequences to [Package Prepare](../Package_Prepare.md), [Docs Review](../Docs_Review.md) and [Export](../Export.md) where their contracts changed.
- [ ] Record selected evidence, user acceptance or pending manual gates, Working/public generated status and separately requested Publish/commit/push outcomes.
- [ ] Update this delivery and Planned Features, then present a retain-or-retire recommendation after durable transfer. Keep the delivery for consequence lookup while useful; do not delete it without approval.

Verification budget: documentation/source/diff review, with no repeated runtime checks solely for closeout. Gate: one complete multiline-Summary outcome is delivered and durable owners are current; publication and manual-review limits are explicit. Record: not started.

## Follow-on And Verification Policy

Full YAML adoption, additional block-scalar forms or multiline metadata fields, rich-text Summary content, new package profiles, and broader test-suite cleanup are separate proposals if needed. There is no proposed requirement to retrofit existing package/export artifacts or rebuild Search for this feature.

[Development Checklist](../Development_Checklist.md), [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md) govern implementation and evidence selection. No tests, fixtures, harnesses, profile changes, temporary regression scripts or browser automation are approved by this planning document. Any proposed test work needs its own bounded specification and durable coverage record outside this delivery. Existing checks must be inspected for actual coverage and cost before selection; static evidence and manual review should be reported at their actual limits.
