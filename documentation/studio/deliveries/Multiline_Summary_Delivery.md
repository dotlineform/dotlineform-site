---
draft: false
doc_id: d-20261007-122704-b0389d
title: Multiline Summary Delivery
added_date: "2026-10-07 12:27:04"
last_updated: "2026-10-07 14:42:04"
summary: Accepted multiline Summary source and rendering with consistent Package Prepare flattening, retained HTML Export breaks and recorded verification limits.
ui_status: complete
parent_id: d-20260428-000000-f5ff18
---
# Multiline Summary Delivery

## Current And Next State

Status: complete and accepted by the user on 2026-10-07, after spaces-based Summary authoring guidance. Source, document/Info rendering and HTML Export retain breaks; packages flatten both Summary fields and expanded Summary body text, with matching comparison normalization, as the user requested. Focused static checks, service import diagnostics, public runtime projection/site validation and Working docs-only reconciliation passed. No tests, browser automation, real package/Import/Export actions, Search rebuild, Publish, commit or push were run by Codex; detailed manual package/Export outcomes were not supplied. Retain this delivery for consequence lookup pending manual archive. This delivery is parented to [Planned Features](../Planned_Features.md) and extends [Builder's Summary block](../Builder.md#summary-block).

The shared front-matter owner now reads scalar fields and Summary literal-block spans for the builder, source services and relevant Import readers. General formatting, targeted Source normalization, timestamps, collection placement and Review materialization use that owner. Builder metadata preserves internal newlines; reader/Info output represents them safely. Package source records and package-only rendering use one whitespace-flattening policy, and returned current-summary comparison uses the same policy. Export consumes generated HTML with shared snapshot/portable Summary styling. There is no full YAML migration, new package shape or added return authority.

## Requirements

The complete result lets an author maintain line and paragraph breaks once in front-matter Summary, retain them through source edits, document builds, readers and HTML Export, and deliberately flatten them at the Package Prepare boundary.

- Accept standard YAML literal-block authoring for `summary` using `|` and `|-`; generated multiline front matter uses `|-`. Folded `>` blocks, `|+`, explicit indentation indicators, nested YAML, anchors, tags and a full YAML migration remain separate scope decisions.
- Preserve internal line breaks and blank lines as plain-text content. Normalize CRLF/CR to LF and trim outer whitespace, including the final newline; blank-line runs represent paragraph boundaries in rendered output. Keep existing single-line values and double-quoted `\n` input valid, without compatibility aliases or a bulk source conversion.
- Keep parsing, validation and serialization consistent across ordinary and configured collection sources, Source Save, metadata/body rewrites, package Review and supported returned Import. Literal-block contents may contain colons, `#`, field-looking text or indented `---`; those are Summary text, not metadata fields, comments or closing delimiters. Malformed blocks must produce useful source errors rather than silently becoming unrelated fields.
- Preserve Summary's string type in by-ID and list metadata. Apply Summary-specific text handling without changing whitespace or field-type behavior for titles, identities, dates, readiness, Subject or other metadata. A change to actual Summary content or internal breaks follows existing `last_updated`/Recent rules; changing between equivalent source representations should not manufacture a content change.
- Render escaped plain text with explicit HTML line breaks within paragraphs and paragraph elements for blank-line boundaries. Markdown, HTML and directive-looking text inside Summary remain literal. Keep the existing Summary panel style and empty-summary omission. The Info panel must display the same line/paragraph meaning safely, without adding another Markdown interpretation path.
- Flatten whitespace consistently in Package Prepare's `summary`, `current_summary` and expanded `[[summary]]` content while preserving unrelated body paragraphs. Normalize both values for returned current-summary comparison. Supported returned Import applies the supplied string: a flattened return can remove source breaks, while an externally authored multiline return is written using `|-`. Both HTML Export outputs preserve reader breaks. YAML syntax belongs in Markdown front matter; structured package fields contain strings, and HTML contains rendered text. These policies require no package schema change.
- Search continues to normalize whitespace for indexing its Summary metadata field and omit active `[[summary]]` directives from body terms. Multiline authoring does not add YAML markers to searchable Summary text, change Search membership or require an automatic Search rebuild.

## Deliverables

- Consistent literal-block reading and source writing through the existing source/build owners, with shared parsing responsibility where practical instead of two independently extended grammars. The implementation must preserve existing scalar field semantics; introducing a full YAML parser requires a separate decision if it changes those semantics.
- Summary-specific metadata preservation, multiline `[[summary]]` output and safe Info-panel presentation in local and public readers. Do not change image-token or Catalogue-image summaries under this document-Summary feature.
- Package Prepare that flattens Summary before field mapping and before body rendering, with matching returned baseline comparison and unchanged existing conversion for unrelated content. Supported return handling retains the supplied value rather than reconstructing discarded breaks. Selection, missing-summary filtering, provenance and collection return eligibility continue through their current owners.
- HTML Export and `portable.html` that retain the generated Summary's breaks, with any necessary snapshot styling contained in the existing Export owner. Export remains a consumer of generated content and does not begin reading or rebuilding canonical source.
- Required shared/public runtime projection, an explicitly scoped Working generated-output reconciliation, and durable authoring/package/Export guidance. Public document data updates through the existing separately authorized Publish operation.

### Representation At Each Boundary

| Boundary | Intended representation and consequence |
| --- | --- |
| Markdown source | `summary: \|` or `summary: \|-` followed by indented literal text; canonical multiline writes use `\|-`. |
| Parsed/source/build metadata | One string with real newline characters; do not carry the `\|` marker or indentation used only to delimit the block. |
| Generated JSON | A string encoded with JSON `\n` escapes; JSON parsing restores newlines. |
| JSON/JSONL packages | Flattened `summary` and `current_summary` strings; no YAML markers or Summary line breaks. Each JSONL record remains one physical line. |
| Generated document and Export HTML | Escaped text with explicit paragraph/line-break markup; preserve meaning without relying on `white-space` CSS alone. |
| Package Markdown/plain-text body | Expanded Summary is one paragraph because the package-only renderer receives a flattened value; unrelated body paragraphs retain their existing conversion behavior. |
| Supported returned package applied to source | Apply the supplied string. A flat return removes breaks; an externally supplied multiline value is written using `\|-`. Import authority and field ownership are unchanged. |
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

This excerpt omits normal identity, dates and readiness fields. Summary remains plain text. `|` includes a final newline in the parsed value; `|-` removes it. Summary normalization trims outer whitespace, so that final newline has no display or Recent significance. The literal-block syntax reference is the [YAML block scalar specification](https://yaml.org/spec/1.2.2/#81-block-scalar-styles).

Source Save retains its current completion boundary and the watcher performs normal document projection work. Metadata-only operations preserve the Summary value and do not edit field-looking lines inside it. Package Prepare emits, for example, `"summary": "First line. Second line. Another paragraph."` and the same normalized `current_summary`. Existing whole-package Import applies the supplied Summary rather than restoring the original breaks. Externally supplied newline-containing values remain supported and are written as readable multiline source.

Package Prepare reads current source through its builder-backed context, then projects flattened Summary into source records and a temporary document value for package rendering without mutating canonical source. Its body contains expanded Summary only when the document actually includes `[[summary]]`; there is no automatic placement or deduplication between body text and Summary fields. HTML Export reads generated payloads, so it reflects multiline output only after the owning document build has produced it. Existing exported folders, already prepared packages and saved public document data do not change when runtime code changes.

## Delivery Steps

### MS-0 — Readiness

- [x] Confirm `|`/`|-` support, Summary-only scope, newline/outer-whitespace semantics, existing scalar preservation and the complete source → render → package/Export outcome.
- [x] Confirm the implementation order and broad ownership across source/build, reader, package and Export. No full YAML migration, new package schema/profile, return authority or unrelated multiline field support was needed.

Verification budget: concise read-only inspection of the owning boundaries and current policy. Gate: specification coherent and implementation approved. Record: complete; user approval and subsequent package-flattening choice define the implemented scope.

### MS-1 — Parsing And Source Rewrites

- [x] Implement consistent literal-block parsing and validation without changing unrelated scalar types or accepted single-line authoring.
- [x] Preserve Summary through Source Save, general formatting, timestamp updates, collection-placement rewrites and supported Import writes. Field detection identifies complete field spans and ignores indented Summary content.
- [x] Compare semantic Summary content under the agreed whitespace rules for existing edit timestamps and Recent behavior; preserve body text and unrelated fields.

Verification budget: focused changed-Python lint/syntax and bounded review of indentation, blank lines, field-looking text and rewrite safety; static diagnostics took less than a second and wrote only normal caches. Gate: source/build/write owners share the same field parser and serializer. Record: complete; `docs_front_matter.py` replaces duplicate scalar parsing and line-scanned mutation with literal-block spans. Ordinary Markdown import retains its existing policy of ignoring metadata other than Title while safely reading Summary blocks; supported package intake uses the shared grammar. Real Source Save/rewrite edge cases remain manually unconfirmed.

### MS-2 — Metadata And Reader Rendering

- [x] Replace Summary's blanket whitespace flattening at its owning builder boundary while retaining Search's separate normalization and other metadata semantics.
- [x] Render Summary paragraphs and intra-paragraph breaks explicitly and safely; retain empty/literal-token behavior and existing panel styling.
- [x] Update Info-panel Summary presentation through safe text nodes and explicit elements, sharing ordinary/collection payload semantics.

Verification budget: changed-source lint/syntax and bounded review of escaping and metadata handoff. Gate: implementation coherent; user accepted delivery closeout. Record: complete; `summary_directive.py` emits escaped paragraphs/`<br>`, related-links presentation builds safe DOM nodes, and shared CSS supplies paragraph spacing. JS lint and Python syntax passed. Codex exercised no browser or multiline rendering behavior; no detailed manual rendering results were recorded.

### MS-3 — Packages, Review And Returned Import

- [x] Flatten `summary` and `current_summary` consistently before existing package mappings, retaining missing-summary filtering and tree/profile contracts.
- [x] Flatten package-only Summary rendering before existing HTML → Markdown/plain-text conversion, without changing unrelated body content or converter semantics.
- [x] Normalize both sides of current-summary comparison; retain supplied return values through existing read-only Review and whole-package Import. Multiline Review/source formatting uses `|-`, and retained canonical-Markdown intake reads complete field spans without a new export profile or return path.

Verification budget: focused static/import diagnostics and bounded review of mappings, package-only rendering, comparison and Import ownership. Gate: consistent flattening without changed eligibility/mutation authority; evidence limits explicit. Record: complete; package source records and rendering use one `flatten_summary` helper, and returned comparison uses the same whitespace policy. A read-only import diagnostic for source management, package routes, ordinary import preview and HTML Export passed with `.env.local` exported; it took less than a second and launched no server. No real package, Review materialization or Import action was run; those write external artifacts or canonical source and remain manual verification gates.

### MS-4 — Export, Projection And Generated Follow-Through

- [x] Preserve explicit Summary breaks in both HTML Export outputs and their own styles, without source reads, automatic rebuilds or YAML syntax in Export.
- [x] Run shared runtime projection, review the exact two-file `site/` delta, then run projection check and site validation; no inventory update was needed.
- [x] Reconcile ordinary Working documents and all four configured collections using intentional full docs-only builds with `--skip-media-builds --skip-browser-config`; avoid source migration and registered-media work. Search and public document data remain separately requested operations.

Verification budget: projection/check/site validation and the authorized global parser/renderer reconciliation across the configured existing Working source owners; no media production, browser startup or network effects. Gate: runtime projection verified and generated/public boundaries accounted for. Record: complete; `bin/site-code-update` changed only projected `docs-viewer-related-links.js` and `docs-viewer.css`; its `--check` and `bin/site-validate` passed. `build_docs.py --stage working --write --skip-media-builds --skip-browser-config` completed for ordinary documents (33), then with `--collection` for works (238), concepts (246), moments (58) and catalogue (4,616), totaling 5,191 documents with zero warnings. These builds took seconds, wrote one ordinary Recent/index output and two existing Catalogue by-ID payloads, removed nothing and changed no collection manifests/relationships. No real HTML Export or public-data Publish was run.

### MS-5 — Code Review

- [x] Review the bounded final diff for duplicated parser rules, accidental full-YAML semantics, block-content mistaken for metadata, unsafe HTML insertion, unrelated Summary fields, compatibility residue and publication ownership drift.
- [x] Reconcile completion claims with exact evidence and resolve in-scope findings; rerun only affected checks.

Verification budget: bounded final-diff/source review; no repository audit or automatic suite. Gate: no blocking review finding remains, with behavioral limits explicit. Record: complete; review covered shared grammar/scalar preservation, complete block replacement, delimiter/field-looking content, semantic edit dates, escaped HTML/safe DOM, package-only flattening and comparison, return authority and exact public projection. The package decision avoided unnecessary changes to the general HTML-to-Markdown converter. One unused import found by lint was removed; subsequent Python lint/syntax passed. Tests/browser automation were not run; user acceptance does not extend the recorded verification coverage.

### MS-6 — Documentation And Closeout

- [x] Transfer syntax/source semantics to [Builder](../Builder.md) and [Source Editor Endpoints](../Source_Editor_Endpoints.md), reader presentation to [Info Panel](../Info_Panel.md), and package/Export consequences to [Package Prepare](../Package_Prepare.md), [Docs Review](../Docs_Review.md) and [Export](../Export.md).
- [x] Record selected evidence, user acceptance on 2026-10-07, Working reconciliation and separate public-data/commit/push outcomes.
- [x] Update this delivery and Planned Features; retain both for consequence lookup pending manual archive. No document deletion is proposed now.

Verification budget: documentation/source/diff review without repeating runtime checks solely for closeout. Gate: complete and accepted; durable owners current and publication remains separate. Record: user authorized closure on 2026-10-07 after the spaces-based indentation guidance; Builder now records that guidance. Code review is not applicable to this final documentation-only status edit; a bounded source/diff review reuses the implementation evidence above. No tests/fixtures/harnesses were changed or run, and no Docs/Search rebuild was triggered by repository documentation edits. Retain the delivery and Planned Features link for the user-requested consequence record until manual archive.

## Follow-on And Verification Policy

Full YAML adoption, additional block-scalar forms or multiline metadata fields, rich-text Summary content, new package profiles, and broader test-suite cleanup remain separate proposals if needed. Existing package/export artifacts are not retrofitted, and Search is not rebuilt for this feature.

[Development Checklist](../Development_Checklist.md), [Testing](../Testing.md) and [Test Contract Discipline](../Test_Contract_Discipline.md) govern implementation and evidence selection. No tests, fixtures, harnesses, profile changes, temporary regression scripts or browser automation are approved by this planning document. Any proposed test work needs its own bounded specification and durable coverage record outside this delivery. Existing checks must be inspected for actual coverage and cost before selection; static evidence and manual review should be reported at their actual limits.
