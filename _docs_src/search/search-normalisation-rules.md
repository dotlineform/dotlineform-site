---
doc_id: search-normalisation-rules
title: Search Normalisation Rules
last_updated: 2026-03-30
parent_id: search
sort_order: 50
---

# Search Normalisation Rules

## Purpose

This document defines how source values and user queries are normalized for the current search implementation.

Its purpose is to make the transformation layer explicit: how raw content becomes search-ready terms, how user input is standardized before matching, and where equivalence rules are shared or intentionally different between build time and query time.

This is a normalization-policy document. It is not the schema, ranking, or UI document.

## Scope

This document applies to two related processes:

- index-time normalization in `scripts/generate_work_pages.py`
- query-time normalization in `assets/js/search/search-page.js`

It covers:

- lowercasing
- whitespace handling
- punctuation and separator handling
- phrase retention
- token splitting
- deduplication
- numeric handling
- current non-features such as fuzzy or synonym expansion

## Relationship to other documents

- [Search Index Schema](/docs/?doc=search-index-schema) defines the indexed fields
- [Search Field Registry](/docs/?doc=search-field-registry) defines which fields participate in search
- [Search Ranking Model](/docs/?doc=search-ranking-model) defines how normalized matches are prioritized
- [Search Build Pipeline](/docs/?doc=search-build-pipeline) defines where index-time normalization occurs
- [Search Validation Checklist](/docs/?doc=search-validation-checklist) defines how normalization behaviour should be checked

## Normalisation principles

The current normalization layer follows these principles.

### Consistent enough for retrieval

Index-time and query-time rules are aligned around lowercase, whitespace cleanup, and token-oriented matching.

### Phrase plus token

The generator preserves normalized phrase forms and also emits split tokens.

### Conservative

The current implementation avoids stemming, fuzzy matching, or semantic inference.

### Deduplicated at build time

Derived search tokens are deduplicated during generation to keep the payload leaner and reduce repeated-match noise.

### Simpler at query time

The browser normalizes aggressively into a lowercase alphanumeric-and-space form for straightforward comparisons.

## Normalisation stages

### 1. Source value preparation

The generator reads source values such as:

- ids
- titles
- display metadata
- dates and years
- series ids
- series titles
- `medium_type`
- `storage`
- `series_type`
- tag ids for structural storage

### 2. Index-time normalization

The generator uses:

- `normalize_search_text(value)`
- `build_search_tokens(*values)`

This produces:

- normalized phrase values
- additional split tokens
- deduplicated `search_terms`
- derived `search_text`

### 3. Query-time normalization

The browser runtime uses:

- `normalize(value)`

This converts the user query into the form used for:

- exact string comparisons
- prefix checks
- token splitting
- broad substring matching

### 4. Matching preparation

The normalized query is split into query tokens and compared against:

- normalized `search_terms`
- normalized `search_text`
- runtime-normalized field variants such as `titleNorm`, `idNorm`, and metadata norms

## Core normalisation rules

Current broad rules:

| Rule | Applies at index time | Applies at query time | Notes |
|---|---|---|---|
| lowercase values | yes | yes | case-insensitive matching baseline |
| trim leading/trailing whitespace | yes | yes | basic cleanup |
| collapse repeated internal whitespace | yes | yes | stabilizes comparisons |
| preserve normalized phrase form | yes | no | generator keeps phrase tokens such as `2-bodies` or `c. 2020?` |
| split phrases into additional tokens | yes | yes | index and query both use token forms |
| replace non-alphanumeric separators with spaces for tokenization | yes | yes | key to slug/phrase equivalence |
| deduplicate repeated derived terms | yes | no | build-time only |
| preserve numeric tokens | yes | yes | important for ids, years, and numbered titles |

## Query normalisation rules

The runtime’s `normalize(value)` currently applies these rules:

- convert to string
- lowercase
- replace every run of non-alphanumeric characters with a single space
- collapse repeated spaces
- trim leading and trailing spaces

Examples:

- `Mixed Case` -> `mixed case`
- `2-bodies` -> `2 bodies`
- `c. 2020?` -> `c 2020`
- `2020-01-01` -> `2020 01 01`

### Lowercasing

All queries are lowercased before matching.

### Whitespace cleanup

Leading, trailing, and repeated internal spaces are normalized away.

### Punctuation handling

At query time, punctuation is not preserved as punctuation. It is reduced to spaces.

### Hyphen and separator handling

At query time, hyphens and similar separators are treated like spaces.

Practical equivalence:

- `2-bodies`
- `2 bodies`

both normalize toward the same query token structure.

### Tokenisation

The normalized query is split on spaces and empty tokens are removed.

There is no minimum token length filter in the current implementation.

### Numeric handling

Numeric fragments are preserved as tokens.

Examples:

- `00533` stays `00533`
- `2020-01-01` becomes tokens `2020`, `01`, `01`

Leading zeros are preserved because normalization is string-based, not numeric parsing.

## Index-time normalisation rules

The generator’s `normalize_search_text(value)` currently applies these rules:

- normalize text through the shared text normalization path
- lowercase
- collapse whitespace
- trim

Important current distinction:

- index-time phrase normalization preserves punctuation and separators in the normalized phrase form
- query-time normalization does not preserve them

Examples:

- `2-bodies` -> normalized phrase `2-bodies`
- `c. 2020?` -> normalized phrase `c. 2020?`
- `2020-01-01` -> normalized phrase `2020-01-01`

The generator then builds additional split tokens from those phrase forms.

### Structured fields

Structured values are passed into `build_search_tokens(...)` in their normalized text form.

The generator does not currently store separate original-form and normalized-form fields for search. Instead it emits:

- structured display fields in their ordinary serialized form
- derived normalized fields in `search_terms` and `search_text`

### Derived fields

For each normalized phrase value, `build_search_tokens(...)` emits:

1. the full normalized phrase token
2. additional split tokens created by replacing non-alphanumeric separators with spaces and splitting

Examples:

- `2-bodies` -> `["2-bodies", "2", "bodies"]`
- `2 bodies monoprint` -> `["2 bodies monoprint", "2", "bodies", "monoprint"]`
- `c. 2020?` -> `["c. 2020?", "c", "2020"]`
- `2020-01-01` -> `["2020-01-01", "2020", "01"]`

### Duplicate handling

`build_search_tokens(...)` deduplicates tokens while preserving first-seen order.

If the same token is encountered again from another source field, it is not re-added.

### Empty-value handling

Empty or blank normalized values are skipped and do not contribute tokens.

## Field-specific normalisation rules

### `id`

Current treatment:

- preserved as a string
- lowercased, if applicable
- retained as a full token in `search_terms`
- not numerically rewritten

Implication:

- leading zeros are preserved
- prefix matching can still work on code-like ids

### `title`

Current treatment:

- full normalized title phrase is retained
- additional split title tokens are emitted

Example:

- `2 bodies monoprint` -> phrase token plus `2`, `bodies`, `monoprint`

### `series_ids`

Current treatment:

- slug-like ids are retained in phrase form
- separator-split variants are also emitted

Example:

- `2-bodies` -> both slug-form phrase and split token equivalents

### `series_titles`

Current treatment:

- full normalized phrase is retained
- split tokens are also emitted

### `medium_type`, `storage`, `series_type`

Current treatment:

- retained as normalized phrases
- split into additional tokens where separators or spaces exist

### `tag_ids` and `tag_labels`

Current treatment:

- tag ids are normalized when read from tag assignments
- tag labels are normalized when stored structurally
- neither is currently included in the derived `search_terms` build set

This is an intentional current limitation, not an omission in the documentation.

## Equivalence rules

Current effective equivalences include:

- uppercase and lowercase forms
- repeated whitespace and single whitespace
- hyphenated forms and spaced-token query forms
- punctuation-separated forms and tokenized query forms, via split-token matching

Examples:

- `2-bodies` can match `2 bodies`
- `c. 2020?` can match `c 2020`
- `2020-01-01` can contribute matches for `2020` or `01`

Important non-equivalence:

- the current system does not expand semantically different labels into one another
- there is no built-in synonym map such as `bw` -> `black and white`

## Deduplication policy

Current deduplication behaviour:

- `search_terms` is deduplicated at build time
- `search_text` is built from the deduplicated `search_terms` list
- repeated query tokens are not explicitly deduplicated before matching, but matching is presence-based rather than frequency-based

Practical consequence:

- repeated source terms do not amplify score through repeated derived token emission
- repeated presence in fallback text does not create additive ranking strength

## Numeric and code-like value policy

Current policy:

- ids remain string values
- leading zeros are preserved
- years may enter search as textual tokens derived from structured numeric values
- numeric fragments from dates are preserved during tokenization
- there is no special stop-word or frequency suppression for common years

Examples:

- `00533` remains distinct from `533`
- `2025` from a year field becomes a searchable token
- `2020-01-01` contributes `2020` and `01`

## Alias and synonym policy

Current implementation status:

- no alias expansion is currently part of the search normalization layer
- no synonym expansion is currently applied at index time or query time
- tag aliases exist elsewhere in the Studio/tagging system, but they are not currently incorporated into v1 search normalization

## Unsupported or intentionally excluded transformations

Current non-features:

- stemming
- fuzzy matching
- typo correction
- singular/plural expansion
- accent folding
- phonetic equivalence
- semantic synonym inference
- alias expansion into search tokens

These are intentionally absent from v1.

## Current implementation summary

Current normalization behaviour in practice:

- both build time and query time lowercase and normalize whitespace
- build time preserves normalized phrase forms and also emits split tokens
- query time normalizes more aggressively to alphanumeric-and-space text
- derived search tokens are deduplicated during generation
- ids, years, and date fragments remain searchable as strings
- no alias, synonym, or fuzzy layer is currently present

## Known limitations or open normalisation questions

Current normalization questions for later work:

- whether the asymmetry between index-time phrase preservation and query-time aggressive separator reduction should remain
- whether generic date fragments such as `01` are too permissive
- whether tags should eventually enter derived token generation
- whether some very common metadata tokens should be filtered or classified differently
- whether field-specific provenance should be preserved more explicitly in derived search terms

## Out of scope for this document

This document does not define:

- the full index schema
- the ranking model
- result UI behaviour
- overall pipeline orchestration beyond where normalization occurs
- line-by-line implementation commentary
