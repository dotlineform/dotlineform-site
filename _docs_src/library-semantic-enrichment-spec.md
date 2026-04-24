---
doc_id: library-semantic-enrichment-spec
title: "Library Semantic Enrichment Spec"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: library
sort_order: 20
---

# Library Semantic Enrichment Spec

## Purpose

This spec captures a future workflow for improving Library docs with summary metadata and structure recommendations.

The immediate use case is practical Library maintenance:

- many imported Library docs do not have clear summary paragraphs
- future Library text search should be able to start from concise summaries before indexing full document text
- reviewing parent-child structure across a large, interrelated corpus is difficult from the tree alone
- external language-model tools can help, but the current browser-chat interface is awkward for bulk source-doc work

This is a planning spec, not a current runtime contract.

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

Reasons:

- the summary belongs to the source doc, not only to a generated search artifact
- diffs remain easy to review
- generated docs indexes and future search records can consume the same field
- the field can be maintained independently from rendered document prose

This spec does not yet add `summary` to the docs schema.
That should be a separate schema task covering all docs scopes or an explicit Library-only decision.

Current direction:

- `summary` should become required for Library docs once the enrichment workflow exists
- `summary` should be a shared docs-scope schema field across Docs Viewer scopes for consistency
- Library is the scope where summary population and relationship review are strategically important first
- shared docs schema consistency does not require identical search behavior across Catalogue, Library, and Studio

## Summary Export Format

A future exporter should write JSONL so files can be streamed, chunked, and recombined safely.

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

## Summary Import Format

Returned summaries should also use JSONL.

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

### Phase 2. Summary import preview/apply

Build a summary importer that validates returned JSONL and previews front-matter changes.

Apply mode should:

- create backups
- write source Markdown
- rebuild Library docs payloads
- optionally rebuild Library docs search after search starts consuming summaries

### Phase 3. Generated docs schema integration

Add `summary` to generated docs indexes and per-doc payloads if the field proves useful beyond source maintenance.

This phase should update:

- docs data-model docs
- docs builder behavior
- validation checks
- any UI surfaces that display summaries

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
- Library viewer summary display is a potential UI option, especially for search results.
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
