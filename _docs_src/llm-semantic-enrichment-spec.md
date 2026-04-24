---
doc_id: llm-semantic-enrichment-spec
title: "LLM Semantic Enrichment Spec"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: llm
sort_order: 20
---

# LLM Semantic Enrichment Spec

## Purpose

This spec defines a shared direction for using LLMs to enrich semantic data across the site.

It exists because several workstreams are converging on the same underlying problem:

- work tagging assistance
- dimension recommendation
- Library summary generation
- Library structure review
- future semantic audits or registry-quality checks

These should not become unrelated ad hoc LLM integrations.
They should share principles, data boundaries, validation patterns, and audit expectations while still allowing each domain workflow to diverge where the product need is different.

This is a planning spec, not an implementation contract.

## Related Workstreams

Current related docs:

- [LLM-Assisted Dimension Recommendation](/docs/?scope=studio&doc=llm-dimension)
- [Generic LLM Helper Pattern](/docs/?scope=studio&doc=generic-llm-helper-pattern)
- [Library Semantic Enrichment Spec](/docs/?scope=studio&doc=library-semantic-enrichment-spec)
- [Tag Editor](/docs/?scope=studio&doc=tag-editor)
- [Tag Registry](/docs/?scope=studio&doc=tag-registry)

The dimension docs still refer to catalogue dimensions as a conceptual model.
The dimensions workflow has not been implemented yet and should be treated as exploratory model design.

The Library semantic enrichment work is more concrete in its source-doc workflow, but still needs schema and UI decisions before implementation.

## Core Principles

### 1. LLM output is advisory

LLM output should propose, explain, cluster, rank, or draft.
It should not become canonical site data until a human or validated apply workflow accepts it.

This applies to:

- suggested tags
- suggested dimensions
- Library summaries
- parent/structure recommendations
- registry strain notes

### 2. Semantic tasks need structured contracts

LLM tasks should use structured inputs and structured outputs.
The system should avoid relying on one-off freeform prompts when the result will feed a workflow.

The shared pattern is:

```text
inputs + instruction + output_schema -> validated LLM response
```

The orchestration layer can be shared, but task contracts should remain explicit and domain-specific.

### 3. Domain workflows may diverge

Shared orchestration does not mean shared UI, shared persistence, or shared search behavior.

Examples:

- work tagging suggestions need work/series context, tag registry context, and accept/reject UI
- dimension recommendation needs image/process context plus conceptual registry context
- Library summary generation needs source-doc text export, batch review, and front-matter writes
- Library structure review needs hierarchy-aware corpus context and report-first recommendations

The point of this spec is to keep the workstreams aware of each other, not to flatten them into one generic product surface.

### 4. Canonical state stays outside the LLM response

LLM responses should be treated as proposals or working artifacts until applied.

Canonical state remains in the owning source systems:

- Studio tag data for tag registry, aliases, groups, and assignments
- future catalogue dimension or scoring data if that model is implemented
- Library source Markdown front matter for summaries
- generated docs/search artifacts only after explicit rebuilds

### 5. Workflow design matters as much as model output

A clever LLM call can still fail if the user cannot select inputs, review output, understand confidence, and apply only the useful changes.

Every semantic-enrichment workflow should define:

- the user entry point
- input selection
- preview/review
- validation
- apply behavior
- undo/backups or audit trail

## Supported Use Cases

### Work tagging assistance

Goal:

- suggest useful tags for a work or series
- surface likely canonical tags and aliases
- explain why a tag may fit
- distinguish confident suggestions from weak candidates

Likely inputs:

- work title
- series context
- existing tags
- work/series prose or short descriptions
- image summaries or visual context
- tag registry, groups, and aliases

Likely outputs:

- candidate tag ids
- reasons
- confidence
- warnings about ambiguity
- possible missing registry terms

Initial persistence direction:

- suggestions should be reviewed in Studio before becoming tag assignments
- accepted suggestions should write through the existing Studio tag data model
- rejected or ignored suggestions may optionally be kept in an audit trace later

### Dimension recommendation

Goal:

- recommend relevant dimensions for a work or series
- identify dimensions probably not useful
- explain semantic overlap or ambiguity
- detect registry/model strain

This use case remains conceptual until the catalogue dimension model is implemented.

Likely inputs:

- work image context
- production method
- current tags
- series context
- dimension registry or candidate dimension set
- prior scoring notes if available

Likely outputs:

- recommended base dimensions
- recommended selectable dimensions
- non-recommended dimensions
- reasons
- confidence
- caveats
- registry strain signals

Initial persistence direction:

- recommendations should be advisory
- accepted results should eventually write into whatever dimension/scoring model is implemented
- registry strain signals should feed model review, not automatic registry mutation

### Library summary generation

Goal:

- draft required summaries for Library docs
- use summaries later as the first text source for Library search
- display summaries as optional Docs Viewer metadata

Likely inputs:

- `doc_id`
- title
- parent context
- headings
- current summary, if present
- plain-text `source_text` derived from rendered content

Likely outputs:

- summary paragraph
- optional confidence or caveat
- optional notes about source ambiguity

Initial persistence direction:

- accepted summaries should be written to Library source Markdown front matter
- export/import JSONL files remain ephemeral working artifacts
- generated docs/search artifacts should update only through normal rebuilds

### Library structure review

Goal:

- recommend better parent-child placement across a large Library corpus
- identify likely thematic clusters
- identify docs that need new parent/category docs

Likely inputs:

- `doc_id`
- title
- current parent
- parent title
- summary
- headings
- current ancestor/sibling context

Likely outputs:

- recommended parent id
- recommendation type
- confidence
- reason
- suggested new parent/category title where needed

Initial persistence direction:

- report-first only
- parent/category docs may be created manually before moves are applied
- any apply workflow should reuse docs-management validation and backup expectations

### Future semantic audits

Possible future tasks:

- detect inconsistent tag usage
- detect near-duplicate tags or aliases
- detect docs missing usable summaries
- detect Library docs whose title/summary/body are misaligned
- detect dimension definitions that overlap too strongly
- identify repeated semantic patterns that suggest model evolution

These should begin as reports, not automatic changes.

## Shared Workflow Pattern

Every LLM semantic-enrichment workflow should follow the same broad lifecycle.

### 1. Select inputs

The user or script selects the records to process.

Examples:

- one work
- one series
- a set of works
- selected Library docs
- a Library subtree
- all docs missing summaries

Selection UI should match the domain.
For example, Library bulk export needs a hierarchical checklist because the Library corpus may become book-like, while work tagging may start from a work or series editor.

### 2. Build context

The system gathers only the context required for the task.

Context should be:

- explicit
- bounded
- reproducible
- tied to stable ids
- easy to inspect in an export or debug report

### 3. Run advisory task

The LLM receives a structured task envelope and returns structured output.

The output should include:

- proposed values
- reasoning
- confidence where useful
- caveats where useful
- task/version metadata where useful

### 4. Validate response

The system validates the response before showing or applying it.

Validation may include:

- required keys exist
- ids exist in the current source model
- suggested tags belong to the registry or are flagged as new candidates
- summaries are non-empty and within agreed limits
- parent recommendations point to valid docs or are marked as new-parent suggestions

### 5. Review in UI or report

The user should see the result in a form that supports judgement.

Good review surfaces should show:

- proposed value
- current value
- reason
- confidence
- warnings
- apply/reject/edit choices where appropriate

### 6. Apply through domain writer

Accepted changes should write through the domain's normal source boundary.

Examples:

- tag assignment writes through Studio tag data
- Library summary writes source Markdown front matter
- Library structure changes use docs-management move/metadata rules

The LLM helper itself should not bypass domain validation.

### 7. Preserve trace where useful

Some workflows may benefit from storing traces.

Possible trace fields:

- task type
- model/provider
- prompt or instruction version
- input ids
- output payload
- accepted/rejected status
- timestamp

Trace storage should be deliberate.
Not every ephemeral export file needs to become persistent history.

## Data Boundaries

### Working artifacts

Working artifacts include:

- JSONL exports
- returned JSONL imports
- recommendation reports
- temporary model responses

These are not canonical state.
They should usually live under `var/` and be safe to delete.

### Canonical source data

Canonical source data remains domain-owned.

Examples:

- `_docs_library_src/*.md` for Library summary front matter
- `assets/studio/data/tag_assignments.json`
- `assets/studio/data/tag_registry.json`
- future catalogue dimension/scoring source if implemented

### Generated data

Generated data should only be updated by existing builders or explicit new builders.

Examples:

- docs indexes and per-doc payloads
- docs search indexes
- catalogue search indexes
- future recommendation/report artifacts if intentionally published

## Output Contracts

Each semantic-enrichment task should define its own output schema.

Shared conventions:

- use stable ids, not labels alone
- include reasons for recommendations
- include confidence when it helps review
- distinguish existing canonical ids from new candidate concepts
- distinguish apply-ready suggestions from report-only observations
- reject malformed responses before they reach source writes

Candidate task families:

- `recommend_tags`
- `recommend_dimensions`
- `summarise_docs`
- `recommend_doc_structure`
- `detect_registry_strain`
- `audit_semantic_consistency`

Task names should be explicit and versionable.

## Relationship To Search

LLM enrichment can improve search, but search should not drive every enrichment decision.

Current direction:

- Library search should initially use summaries before considering full body text
- catalogue search may benefit from tags and future dimension data
- Studio docs search may not need the same summary population effort as Library
- search behavior can diverge by domain priority even when the underlying docs schema is shared

The search pipeline should consume accepted canonical metadata, not raw unreviewed LLM responses.

## Pre-Implementation Decisions

Before implementing any LLM semantic-enrichment workflow, decide:

- what source data is canonical for the workflow
- what the user-facing entry point is
- whether the workflow is single-record, batch, or both
- what gets exported and in what format
- whether returned results are imported, displayed as reports, or both
- what validation blocks apply
- whether accepted changes write source immediately or stage a patch
- what backup or audit trace is required
- what generated artifacts need rebuilding after apply

These decisions should be made per workflow, but using this shared checklist.

## Suggested Implementation Phases

### Phase 1. Shared contracts and read-only exports

Define structured request/response schemas for the first concrete workflows.

Likely first candidates:

- Library summary export/import contract
- tag recommendation contract for works or series

The first implementation should favor read-only exports and reports where possible.

### Phase 2. Library summary workflow

Implement the lower-risk Library summary path:

- hierarchical selection UI
- JSONL export
- returned summary validation
- preview/apply front-matter writes
- docs rebuild
- optional Docs Viewer metadata display

This is a strong first use case because it is additive and easy to diff.

### Phase 3. Tagging assistance workflow

Implement advisory tag suggestions:

- choose one entry point, probably work or series context
- include registry and alias context
- show reasons/confidence
- allow accept/reject/edit
- write accepted tag assignments through existing Studio tag writers

This has higher product value but more UI and governance complexity than summary import.

### Phase 4. Dimension recommendation prototype

Only after the dimension model has a real source schema, implement a prototype for dimension recommendation.

Until then, dimension notes should continue to inform model design without becoming runtime requirements.

### Phase 5. Structure review reports

Implement Library structure recommendation reports after summaries exist.

This should stay report-first until new parent docs and move/apply behavior are clearly reviewed.

## Risks

- LLM output can be plausible but wrong
- semantic output may flatten nuance or overstate certainty
- batch apply workflows can create large hard-to-review diffs
- different domains may need different UX, despite shared orchestration
- the system may become too abstract if it prioritizes a generic helper over concrete workflow needs
- model/provider behavior may change, so validation and human review must remain central

## Open Questions

- Which use case should be implemented first: Library summaries or tagging assistance?
- Should LLM traces be stored persistently, and if so where?
- Should accepted LLM suggestions record their origin in source data, or only in logs?
- What confidence vocabulary should be used across workflows?
- Should new candidate tags/dimensions be suggested in the same flow as existing registry values, or separated into a governance report?
- What local or external model/provider boundary is acceptable for source content?
- How should image-derived context be produced before work tagging or dimension recommendation?
