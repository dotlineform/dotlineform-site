---
doc_id: library-semantic-enrichment-spec
title: "Library Semantic Enrichment Spec"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: library
sort_order: 20
---

# Library Semantic Enrichment Spec

## Sections

- [Purpose](#purpose)
- [Problems To Solve](#problems-to-solve)
- [Proposed Source Metadata](#proposed-source-metadata)
- [Docs Viewer Summary Display](#docs-viewer-summary-display)
- [Summary Export Format](#summary-export-format)
- [Summary Import Format](#summary-import-format)
- [Bulk Export Selection UI](#bulk-export-selection-ui)
- [Structure Review Export Format](#structure-review-export-format)
- [Structure Recommendation Format](#structure-recommendation-format)
- [Role Of Codex And ChatGPT](#role-of-codex-and-chatgpt)
- [Suggested Phases](#suggested-phases)
- [Risks](#risks)
- [Current Decisions](#current-decisions)
- [Remaining Open Questions](#remaining-open-questions)

## Purpose

This spec captures a future workflow for improving Library docs with summary metadata and structure recommendations.

The immediate use case is practical Library maintenance:

- many imported Library docs do not have clear summary paragraphs
- future Library text search should be able to start from concise summaries before indexing full document text
- reviewing parent-child structure across a large, interrelated corpus is difficult from the tree alone
- external language-model tools can help, but the current browser-chat interface is awkward for bulk source-doc work

This is a planning spec, not a current runtime contract.
The workflow should be UI/workflow-led: a technically clever export/import command will still fail if the Studio Library surface does not make selection, review, and apply decisions understandable.

## Problems To Solve

### 1. Summary enrichment

Library docs need short, reliable summaries that can later support:

- better search index terms
- result snippets
- review dashboards
- quick human scanning during structure review

The summaries should be generated in a way that is:

- batchable across dozens or hundreds of docs
- machine-readable
- reviewable in diffs before source files are changed
- tied to stable `doc_id` values rather than filenames alone

### 2. Structure review

Library docs are semantically interrelated.
Choosing parent-child structure is not a simple filename or chronology problem.

The system needs a way to help review:

- whether a doc belongs under its current parent
- which docs form natural thematic clusters
- where a doc overlaps multiple possible parents
- which recommendations are high-confidence versus speculative

This should be advisory first.
Automatic structure writes are higher risk than summary writes because they change navigation and meaning.

### 3. Bulk language-model handoff

The normal chat interface is not efficient for more than a small batch of long documents.
The site needs an export/import workflow that can hand documents to a language model in a structured format, then validate returned summaries or recommendations before applying anything.

Codex can perform some of this work directly because it has filesystem access.
The same workflow should still support export files that can be pasted into or uploaded to another tool when that is useful.

## Proposed Source Metadata

Summary text should eventually live in Library source Markdown front matter:

```yaml
summary: "A concise paragraph describing the document."
```

The current field is plain text, not rendered Markdown or HTML.
The metadata editor and local write service normalize whitespace to one paragraph, so line breaks are collapsed and formatting markers such as `**bold**` display literally.

Reasons:

- the summary belongs to the source doc, not only to a generated search artifact
- diffs remain easy to review
- generated docs indexes and future search records can consume the same field
- the field can be maintained independently from rendered document prose
- the Docs Viewer can expose the same metadata near the updated date without forcing the summary to become part of the authored body

The initial schema task adds `summary` as an optional shared docs-scope field.
Library is the first expected population workflow, but the generated docs contract can carry the same field for any scope when present.

Current direction:

- `summary` should become required for Library docs once the enrichment workflow exists
- `summary` should be a shared docs-scope schema field across Docs Viewer scopes for consistency
- Library is the scope where summary population and relationship review are strategically important first
- the Docs Viewer should be able to display `summary` as optional metadata when present, especially in Library
- shared docs schema consistency does not require identical search behavior across Catalogue, Library, and Studio

## Docs Viewer Summary Display

Summary text should not need to be a visible heading or paragraph inside the document body.
The rendered document body can stay focused on the authored source content, while the summary remains reusable metadata.

When a generated docs payload includes `summary`, the Docs Viewer should be able to display it in the metadata area near the ancestor path and updated date.

Reasons:

- a reader can quickly understand what the doc is about before reading the full body
- the same field can support search, export, and human review
- summary display can be optional and scope-sensitive without changing source-body conventions
- Library docs benefit most because they are reference/research documents rather than implementation notes

Initial display direction:

- show the summary below the updated date when present
- keep it visually secondary and aligned to the Docs Viewer metadata/content measure
- do not require Studio docs to display summaries until that scope has a real use for them
- consider a later UI option for showing summaries in Library search and recently-added results

## Summary Export Format

A future exporter should write JSONL so files can be streamed, chunked, and recombined safely.
Export files are ephemeral working artifacts, not canonical source.
They should be created on demand with the selected options applied and should be safe to delete.

Expected location:

```text
var/docs/semantic-review/<timestamp>/summaries.jsonl
```

Canonical state remains in source Markdown front matter and generated docs/search artifacts after rebuilds.

Candidate row shape:

```json
{"doc_id":"defining-information-for-cross-boundary-comparisons-concepts","title":"Defining \"Information\" for Cross-Boundary Comparisons — Concepts","parent_id":"","headings":["Generated","Prompt"],"current_summary":"","source_text":"..."}
```

Required fields:

- `doc_id`
- `title`
- `parent_id`
- `headings`
- `current_summary`
- `source_text`

Useful export options:

- `--scope library`
- `--batch-size 20`
- `--only-missing-summary`
- `--include-body`
- `--max-chars-per-doc`
- `--output var/docs/semantic-review/<timestamp>/summaries.jsonl`

The exporter should report:

- docs exported
- docs skipped because they already have summaries
- docs truncated by character limit
- unpublished docs excluded

### `source_text` format

`source_text` should be plain UTF-8 text derived from rendered content, not raw Markdown or raw HTML.

Rules:

- omit YAML front matter
- omit HTML tags
- omit the document title when it is already present in the `title` field
- preserve paragraph breaks with blank lines
- preserve list items as separate lines
- preserve headings as text, while also exposing headings in the structured `headings` field
- preserve blockquotes as separate lines, optionally prefixed with `> `
- omit code blocks or replace them with a short marker unless the document is code-heavy
- normalize whitespace enough for model input without destroying paragraph structure

Reasons:

- summary generation should spend attention on document meaning rather than markup
- plain text is portable between Codex, ChatGPT, and future tooling
- rendered-derived text avoids HTML import noise while still reflecting what the reader sees
- keeping `headings` structured means `source_text` does not need to preserve hierarchy perfectly

Optional future/debug fields may include `source_markdown`, but the default LLM handoff field should be `source_text`.
`content_html` should not be part of summary export by default.

## Summary Import Format

Returned summaries should also use JSONL.
Returned JSONL is also an ephemeral working artifact until validated and applied.

Candidate row shape:

```json
{"doc_id":"defining-information-for-cross-boundary-comparisons-concepts","summary":"A concise paragraph describing the document's core question and argument."}
```

The importer should:

- validate every `doc_id`
- reject duplicate rows
- reject rows for unpublished or missing docs unless explicitly allowed
- reject empty summaries
- optionally enforce a character or sentence limit
- preview changes before writing
- preserve existing front matter ordering
- write backups before modifying source files
- rebuild the affected docs scope after an apply run

Summary import should be implemented before structure import because it is lower risk and creates useful context for later structure review.

## Bulk Export Selection UI

Bulk export needs a Studio Library UI that supports selecting many docs from the current Library hierarchy.
The Library hierarchy is likely to become deeper than the Studio docs hierarchy because Library behaves more like a book, with parts, chapters, and pages.

Recommended UI shape:

- hierarchical checklist of Library docs
- indentation to show depth
- expand/collapse controls for branches
- checkbox per doc
- selecting a parent selects all descendants
- deselecting a child puts ancestors into an indeterminate state
- select all and clear controls
- option to limit the view/export to docs missing summaries
- optional include/exclude archived docs control

The UI should show basic operational counts:

- selected docs
- selected docs missing summaries
- estimated exported characters or size
- number of batches that will be created

Export options should be visible before the export runs:

- include body text
- maximum characters per doc
- batch size
- output format

The exporter should resolve the UI selection to an explicit set of `doc_id` values before writing JSONL.
The exported file should not depend on parent-selection state, because imports and later validation should operate against explicit doc ids.

Reasons:

- a flat list will not scale to a book-like Library hierarchy
- users need to select meaningful branches, not individual docs one by one
- parent selection makes large exports practical
- explicit exported `doc_id` rows keep import validation simple and deterministic
- selection and review are part of the product workflow, not merely decoration around a script

## Structure Review Export Format

Structure review does not need full body text once summaries exist.

Candidate row shape:

```json
{"doc_id":"...","title":"...","parent_id":"...","parent_title":"...","summary":"...","headings":["..."]}
```

This export should include all published Library docs, not only docs missing summaries, because relationship review depends on corpus-wide context.

The exporter may also include derived fields later:

- ancestor trail
- sibling titles
- outgoing doc links
- inbound doc links
- tags or detected themes if those become part of the Library model

## Structure Recommendation Format

Returned structure recommendations should be advisory JSONL or JSON.

Candidate row shape:

```json
{"doc_id":"...","recommended_parent_id":"...","confidence":"medium","reason":"Shares the strongest summary-level theme with the recommended parent, but also overlaps another cluster."}
```

The system should distinguish:

- high-confidence parent changes
- low-confidence candidates requiring manual review
- docs that should remain at root
- docs that need a new parent/category doc before they can be placed cleanly

Initial implementation should generate reports only.
Applying parent changes should remain a later, explicit task.

## Role Of Codex And ChatGPT

### Codex

Codex is a good fit for:

- creating and validating export files
- reading source docs directly
- producing first-pass summaries or structure reports in batches
- applying validated JSONL imports
- updating source Markdown and generated docs payloads

### ChatGPT UI

The ChatGPT UI remains useful for:

- higher-level semantic review
- trying different prompt strategies
- reviewing a batch as a human-facing conversation
- refining taxonomy or clustering ideas before those ideas become system rules

The workflow should not depend on manually pasting source documents one at a time.

## Suggested Phases

### Phase 1. Read-only audit and export

Build a read-only Library semantic export command.

Outputs:

- summary-enrichment JSONL
- structure-review JSONL
- a short report of counts, missing summaries, and truncation

No source writes.
The first export UI should be able to call this read-only path and show the same report back to the user.

### Phase 2. Summary import preview/apply

Build a summary importer that validates returned JSONL and previews front-matter changes.

Apply mode should:

- create backups
- write source Markdown
- rebuild Library docs payloads
- optionally rebuild Library docs search after search starts consuming summaries

### Phase 3. Generated docs schema integration

Add `summary` to generated docs indexes and per-doc payloads, plus the shared metadata editor, without changing docs search behavior.

This phase should update:

- docs data-model docs
- docs builder behavior
- validation checks
- any UI surfaces that display summaries

Current task:

- add optional `summary` front matter to the generated docs schema
- add `summary` to the Edit metadata modal so imported Library docs can be summarized during manual review
- display non-empty summaries in the Docs Viewer metadata area below the updated date
- keep Library search unchanged until the separate search-integration phase

### Phase 4. Search integration

Update Library docs search so summary text participates in search.

Initial direction:

- start with summary-only text indexing rather than full body text
- defer full body text search until there is evidence that it improves usability
- allow search behavior to diverge by domain priority across Catalogue, Library, and Studio

### Phase 5. Structure recommendation report

Build a report-only workflow for suggested parent changes.

Outputs:

- recommendations by doc
- confidence levels
- explanations
- proposed new grouping/category docs where needed

Structure review should expect that some recommendations need new parent/category docs.
Those parent docs can be created manually before any move/apply workflow runs.

### Phase 6. Structure apply tools

Only after report review, consider an apply flow for parent changes.

This should probably reuse Docs Viewer management validation rules for:

- valid `parent_id`
- duplicate `doc_id` protection
- `_archive` handling
- source backups
- same-scope docs rebuilds

## Risks

- language-model summaries may be plausible but inaccurate
- generated summaries can flatten nuance or overstate conclusions
- bulk imports can create many small source changes that are hard to review
- parent-child recommendations may impose a false hierarchy on documents that are naturally cross-linked
- adding `summary` to the schema before search requirements are clear could create churn

## Current Decisions

- `summary` should become required for Library docs once the workflow exists.
- `summary` should be modeled as a shared docs-scope field across Docs Viewer scopes.
- Library is the first and most important scope for actually populating summaries and reviewing semantic relationships.
- Library search should initially use summary text rather than full body text.
- Full body text search remains an unproven later option.
- Library viewer summary display should be supported as document metadata when `summary` is present.
- Library search/recently-added summary display remains a potential UI option.
- Summary export/import JSONL files are ephemeral working artifacts, not canonical state.
- Summary export `source_text` should be plain text derived from rendered content, not raw Markdown or raw HTML.
- Bulk export selection should be hierarchical and checkbox-driven, with parent selection applying to descendants.
- Structure review should support recommendations that depend on new parent/category docs.
- New parent/category docs can be created manually before document moves are applied.
- A Studio Library page should become the user-facing entry point for running export/import/review scripts and seeing basic reports.
- Search behavior may fork by domain priority even if docs-source schema stays shared.

## Remaining Open Questions

- What exact validation rule makes a Library summary acceptable?
- Should non-Library docs scopes require `summary`, allow it optionally, or only carry the schema field when present?
- Should Library search result snippets display summary directly, or use summary only for matching/ranking?
- Should the Library viewer offer a user option to show summaries in search and recently-added lists?
- What basic report shape should the Studio Library semantic-enrichment page show first?
- Should structure recommendations include suggested new parent/category doc titles?
- Should code-heavy Library docs ever include code blocks in `source_text`, or should code always be summarized from surrounding prose?
