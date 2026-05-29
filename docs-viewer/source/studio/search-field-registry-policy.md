---
doc_id: search-field-registry-policy
title: Search Field Policy
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: search-field-registry
---
# Search Field Policy

## Searchability rules

Current inclusion logic in practice:

- fields are actively searchable in v1 when the runtime gives them direct matching behaviour or when they contribute materially through the derived fields
- fields remain non-searchable when they are purely navigational or when using them now would add more noise than value

Current policy split:

- direct active search fields:
  - `id`
  - `title`
  - `series_titles`
  - `medium_type`
  - `series_type`
  - `search_terms`
  - `search_text`
- indirect searchable fields through derivation:
  - `year`
  - `date`
  - `display_meta`
  - `series_ids`
- present but not active in v1 search:
  - `kind`
  - `href`
  - `tag_ids`
  - `tag_labels`

## Filterability rules

Current implemented filter surface:

- `kind`

Current fields that could support structured filters if that capability is enabled:

- `kind`
- `year`
- `date`
- `series_ids`
- `medium_type`
- `series_type`
- `tag_ids`

Current fields that should not become structured filters:

- `title`
- `href`
- `search_terms`
- `search_text`
- `display_meta`

V1 intentionally keeps filtering minimal and explicit.

## Display rules

Current v1 result display roles:

- `kind` as a small type label
- `title` as the primary result label and link text
- `href` as the link destination
- `id` as the secondary identifier line
- `display_meta` as secondary metadata when present
- `medium_type` added to work metadata rows when present
- `series_titles` added to work metadata rows when present
- `series_type` added to series metadata rows when present

Current fields stored but not displayed:

- `year`
- `date`
- `series_ids`
- `tag_ids`
- `tag_labels`
- `search_terms`
- `search_text`

## Importance classes

Current meaning of the registry importance labels:

### High

Fields strongly associated with known-item lookup and primary relevance.

Current examples:

- `id`
- `title`
- `search_terms` as a derived support field

### Medium

Fields useful for discovery and context, but weaker than title or id.

Current examples:

- `series_titles`
- `medium_type`
- `series_ids` as structured context

### Low-medium

Fields that help recall in narrower cases but should not dominate results.

Current examples:

- `series_type`

### Low

Fields that support recall but should remain weak and contextual.

Current examples:

- `year`
- `date`
- `display_meta`
- `search_text`

### None

Fields not intended to contribute to relevance in v1.

Current examples:

- `kind`
- `href`
- `tag_ids`
- `tag_labels`

## Match mode policy

Current field-policy fit by match mode:

- `id`
  - exact
  - prefix
- `title`
  - exact
  - prefix
  - token-oriented title matching
- `series_titles`
  - contains
- `medium_type`
  - contains
- `series_type`
  - contains
- `search_terms`
  - exact
  - prefix
- `search_text`
  - substring fallback

Fields like `year`, `date`, and `display_meta` do not currently have dedicated independent match policies; they enter the runtime through `search_terms` and `search_text`.

## Derived field policy

Current derived fields:

- `search_terms`
- `search_text`

Why they exist:

- to make the browser runtime simpler
- to avoid reconstructing heterogeneous field bundles for every query
- to provide one explicit exact/prefix support field and one broad fallback field

Current policy:

- derived fields are useful for v1 simplicity and performance
- derived fields should not erase the distinction between stronger structured matches and weaker fallback matches
- `search_terms` is a primary support field
- `search_text` is a fallback field only
- derived fields currently lose some field provenance, which is acceptable for v1 but may need refinement later

## Common field-policy questions

Current answers in v1:

- should a field remain searchable if it duplicates stronger fields
  - only if it improves recall without overwhelming ranking
- should a display field also be searchable
  - sometimes; `display_meta` is an example of a displayed field that contributes indirectly through derivation
- should canonical ids and human-readable labels both be indexed
  - yes
- should derived fields be used only as fallback
  - `search_text` yes; `search_terms` no, because it is central to v1 matching
- should empty array fields still be present in the schema
  - yes, where empty-list semantics are meaningful

## Further Refinement


## Out of scope for this document

This document does not define:

- full raw schema structure
- low-level normalization rules
- exact scoring numbers
- UI event handling
- generator implementation details
