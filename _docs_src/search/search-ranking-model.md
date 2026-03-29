---
doc-id: search-ranking-model
title: Search Ranking Model
last-updated: 2026-03-29
parent-id: search
sort-order: 40
---

# Search Ranking Model

## Purpose

This document defines how matching search records are prioritised and ordered.

Its purpose is to make the relevance model of the site search subsystem explicit and reviewable. It should explain which kinds of matches are treated as stronger or weaker, how field importance affects ranking, and how broad recall fields relate to more precise fields such as title or ID.

This document is about ranking policy. It is not a code walkthrough and it is not a schema document.

## Scope

This document applies to the ranking stage of client-side search.

It should cover:

- how matching records are prioritised
- how field importance affects score or ordering
- how different match types compare with one another
- how ties are resolved
- how fallback fields are treated
- how multi-field matches influence relevance

This document should define ranking intent clearly enough that the implemented behaviour can be checked against it.

## Relationship to other documents

This document should be read alongside:

- `search-index-schema.md`, which defines the available search fields
- `search-field-registry.md`, which defines which fields are searchable and their importance class
- `search-normalisation-rules.md`, which defines how values are transformed before matching
- `search-ui-behaviour.md`, which defines how ranked results are displayed
- `search-validation-checklist.md`, which defines how ranking behaviour should be tested

## Ranking principles

The ranking model should follow these principles:

### Predictable
Results should feel stable and understandable rather than arbitrary.

### Known-item friendly
When a user searches for a title, ID, or canonical series name, the intended item should rank highly.

### Structured-first
Matches in strong structured fields should outrank matches in broad derived or fallback fields.

### Recall without dominance
Broad support fields should help retrieve relevant items, but should not overpower more precise fields.

### Reviewable
Ranking rules should be describable in plain language without requiring inspection of the implementation code.

## Ranking stages

The ranking model can be described as a sequence of stages.

### 1. Candidate retrieval
The engine determines which records match the query at all.

This document does not define candidate retrieval in detail, but ranking policy assumes that only matching candidates reach the ranking stage.

### 2. Field-aware relevance assessment
The engine identifies which fields matched and what kind of match occurred.

Examples:
- exact title match
- title prefix match
- token match in title
- exact ID match
- series title match
- medium match
- year match
- fallback match in derived search text

### 3. Score or precedence assignment
The engine gives stronger priority to higher-value field matches and weaker priority to lower-value or fallback matches.

### 4. Tie-breaking
If two results are otherwise similar, tie-breaking rules determine which appears first.

## Ranking dimensions

Ranking should consider at least the following dimensions.

### Field importance
Matches in stronger fields should outrank matches in weaker fields.

Typical precedence:
- title-like fields
- ID-like fields
- canonical series labels
- tag labels
- medium or descriptive metadata
- year or broad low-information fields
- derived fallback fields

Codex should replace this generic list with the actual implemented or intended precedence.

### Match type strength
Not all matches within a field are equally strong.

Typical precedence:
- exact
- exact phrase
- phrase
- prefix
- token
- substring
- fallback broad-text hit

Codex should document the actual match modes used by the implementation.

### Multi-field reinforcement
A record that matches the query across more than one meaningful field may deserve a higher rank than a record that matches only weakly in one place.

Example:
A work that matches both title and series title may deserve stronger ranking than one that matches only in broad search text.

### Generic versus specific terms
Matches on generic or very common tokens should usually be weaker than matches on distinctive tokens.

If the current implementation does not account for this yet, that should be stated explicitly.

## Ranking table

This section should define the intended precedence of major match categories.

The table below is a template and should be replaced or completed by Codex based on the current implementation.

| Rank band | Match example | Relative strength | Notes |
|---|---|---|---|
| 1 | Exact title match | strongest | Typical best known-item result |
| 2 | Title prefix match | very high | Strong partial known-item lookup |
| 3 | Exact ID match | very high | Important for catalogue-style retrieval |
| 4 | Series title match | high | Useful for grouped discovery |
| 5 | Tag label match | medium | Useful for thematic discovery |
| 6 | Medium type match | medium | Useful but usually weaker than title |
| 7 | Year match | low | Often broad and ambiguous |
| 8 | Derived search text match | lowest | Recall support only |

This table does not need to include implementation-specific numbers if the model is not score-based in a numeric sense. Relative precedence is the important part.

## Field-level ranking notes

This section should define how important individual fields contribute to ranking.

Suggested pattern:

### title
Expected ranking role:
One of the strongest fields in the system.

Typical strong matches:
- exact phrase
- prefix
- token match on distinctive title terms

Notes:
Title matches should usually outrank metadata-only matches.

### id
Expected ranking role:
Strong known-item retrieval field.

Typical strong matches:
- exact ID
- prefix ID, if supported

Notes:
Numeric or code-like matches may need careful handling to avoid broad accidental hits.

### series-titles
Expected ranking role:
High-value contextual field, especially for grouped discovery.

Notes:
Should usually outrank broad descriptive or fallback fields.

### search-text
Expected ranking role:
Low-priority fallback field.

Notes:
Useful for recall, but should not outrank structured field matches.

Codex should extend this pattern for the actual current field set.

## Tie-breaking policy

This section should define what happens when two records receive similar relevance.

Possible tie-breakers include:
- stronger content type priority
- shorter or cleaner title match
- fewer indirections between query and result
- stable source order
- recency or year, if intentionally used
- deterministic alphabetical fallback

Codex should document the actual current tie-breaking behaviour, even if it is simple.

If tie-breaking is currently just source order or array order, that should be stated explicitly.

## Duplicate-term and repeated-match policy

This section should clarify whether repeated occurrences of a term within a record increase ranking strength.

Examples of questions to answer:
- does the same term appearing twice in `search-text` increase score?
- are duplicated derived terms intentional or accidental?
- does the system count occurrences or only field-level presence?
- should repeated matches in fallback fields remain weaker than a single strong title match?

This section is important because duplicated index content can distort ranking if occurrence count affects score.

## Derived field ranking policy

Derived fields often flatten multiple values together and can be useful for recall, but they usually reduce precision.

This section should define:

- which derived fields contribute to ranking
- whether they are used only as fallback
- whether they carry lower weight than structured fields
- whether field provenance is lost in a way that affects ranking precision

Examples:
- `search-terms` may be used for broad token recall
- `search-text` may support substring or fallback matches
- both may need lower precedence than structured fields such as `title` or `series-titles`

## Content-type priority

If the site search includes multiple content types, this section should define whether type affects ranking.

Examples:
- whether works and series are mixed into a single result order
- whether one content type is preferred for ambiguous matches
- whether grouped display affects perceived ranking but not raw score
- whether exact title match in a note should outrank weak metadata match in a work

Codex should document the current behaviour if multiple content types are included.

## Current implementation summary

This section should briefly summarise how ranking currently works in practice.

Examples of useful statements:
- whether ranking is currently field-aware or mostly flat
- whether the engine uses numeric scoring or ordered precedence rules
- whether broad search fields currently dominate too much
- whether duplicate terms may influence results unintentionally
- whether tie-breaking is explicit or implicit

This section should be factual and concise.

## Known limitations or open ranking questions

This section should capture unresolved ranking issues only.

Examples:
- whether title-related terms are overweighted due to duplication
- whether year matches are too strong or too weak
- whether derived fields should be demoted further
- whether exact ID matches should outrank title prefix matches
- whether ranking should later become more field-aware
- whether multi-field bonuses should be introduced or adjusted

## Out of scope for this document

This document should not define:

- the full index schema
- low-level normalisation code
- UI markup
- build pipeline steps
- keyboard interaction behaviour
- validation procedure details

Those belong in other search documents.