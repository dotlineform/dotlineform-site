---
doc_id: search-result-shaping
title: Search Result Shaping
last_updated: 2026-03-31
parent_id: ""
sort_order: 200
published: false
---

# Search Result Shaping

## Purpose

This document defines the site-specific rules that shape the final visible search results after initial retrieval and ranking.

Its purpose is to make explicit how the site handles redundancy, hierarchy, and diversity in search output. The search engine may correctly retrieve and rank many relevant records, but the final list shown to the user should also reflect the structure of the site and avoid flooding the top results with near-duplicates.

This document is about post-ranking result policy. It is not a schema document, not a low-level ranking document, and not a code walkthrough.

## Scope

This document applies to the runtime stage after candidate retrieval and initial ranking.

It should cover:

- parent-child result consolidation
- family or sibling result suppression and collapse
- result diversification across content types or media types
- protection of highly specific matches
- caps or diminishing returns for repeated clusters
- how shaped results differ from raw ranked results

This document should define the site-specific result-policy layer rather than the generic relevance engine.

## Relationship to other documents

This document should be read alongside:

- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Next Steps](/docs/?scope=studio&doc=search-next-steps)

## Why result shaping exists

A flat ranked list is not always the best user experience on a site with structured content relationships.

Examples of common failure modes:

- a series title query returns the series plus many nearly identical child works
- one family of works occupies most of the top results
- one media type, such as still images, buries a distinct but relevant result type such as video
- the one unusual or informative result is pushed far down by many repetitive matches

Result shaping exists to address these problems without weakening the underlying search engine.

The aim is not to ignore relevance. The aim is to stop redundant result clusters from dominating the visible result list.

## Core principle

The search subsystem should be treated as having three stages:

1. **Retrieval**  
   Determine which records match the query.

2. **Ranking**  
   Order matches by relevance.

3. **Result shaping**  
   Adjust the visible result list to reduce redundancy and surface distinct, informative matches.

Result shaping should not replace ranking. It should refine the final visible result order and composition.

## Result-shaping principles

The result-shaping layer should follow these principles:

### Preserve specific intent
If a user’s query clearly targets a specific item, that item should remain visible even if a parent or sibling group also matches.

### Prefer representatives over repetition
Where many similar results cluster around one family or parent entity, the system should prefer a representative result plus limited supporting results rather than a long repetitive list.

### Preserve diversity where relevance is comparable
If one distinct result type is reasonably close in relevance to many repeated results of another type, the distinct result should have a fair chance to surface early.

### Use site structure explicitly
Result shaping should use relationships such as series → works rather than pretending the result set is flat.

### Be query-sensitive
The same group of records may need different treatment depending on the query.

## Site structures relevant to result shaping

This section should define the site-specific structures used for shaping.

Examples may include:

- parent series and child works
- sibling works within the same series
- media type groupings such as image, video, text
- content kind groupings such as work, series, note, theme
- naming families where many titles share the same base pattern

Codex should replace this placeholder section with the actual current structures available in the implementation and search data.

## Shaping dimensions

Result shaping may operate across one or more dimensions.

### Parent-child hierarchy
Used when one result is a structural parent of many similar child results.

Example:
- series → works

### Family or sibling grouping
Used when many records belong to the same family and differ only slightly.

Example:
- `grid 1`, `grid 2`, `grid 3` within one series

### Content kind
Used to avoid one kind of result overwhelming others.

Example:
- work
- series
- note

### Media type
Used to surface distinct result formats when relevant.

Example:
- image
- video
- text

Codex should state which of these dimensions are currently available and which are future-facing.

## Query-intent sensitivity

Result shaping should respond to the likely specificity of the query.

Typical distinctions include:

### Broad family-name query
A query that appears to target a family, series, or shared title stem.

Example:
- `grid`

Likely behaviour:
- prefer the parent series
- collapse or suppress derivative child works

### Specific item query
A query that appears to target an individual item.

Example:
- `grid 7`

Likely behaviour:
- keep the specific work visible
- do not suppress it merely because its parent series also matches

### Metadata query
A query targeting a medium, tag, year, or other broad metadata field.

Example:
- `digital print`

Likely behaviour:
- do not automatically collapse all sibling works merely because they share a series
- allow multiple individually relevant works to remain visible

Codex should document the actual current or intended query-specific distinctions.

## Shaping stages

The shaping layer may be described as a sequence of stages.

### 1. Protect highly specific matches
Results that strongly satisfy likely user intent should be preserved before other shaping rules are applied.

Examples:
- exact title match
- near-exact title phrase match
- exact or near-exact ID match
- specific child work match such as `grid 7`

### 2. Group related results
Group results by shaping dimensions such as parent series, family, media type, or content kind.

### 3. Consolidate redundant groups
If a group contains many near-duplicate or derivative results, prefer a representative result and limit the visible repetition.

### 4. Diversify where appropriate
If many results from one kind or type dominate the top list, allow distinct kinds or types to surface when relevance is close.

### 5. Emit final visible list
Return the shaped result list for display.

Codex should describe the actual or intended runtime flow if it is already implemented or planned.

## Parent-child consolidation policy

This section should define how the system handles cases where a parent series and many child works all match.

Questions to answer:
- When should the parent series stand in for many matching works?
- When should child works be hidden, collapsed, demoted, or still shown?
- How many child works, if any, should remain visible alongside the parent?
- What counts as a child work being independently relevant rather than derivative?

Suggested structure:

### When to prefer the parent
Examples:
- query exactly matches the series title
- query matches only the shared family stem
- child matches are mainly inherited from shared family naming

### When to keep child works visible
Examples:
- child title contains a distinguishing token strongly matched by the query
- child matches another strong field independently
- query appears to target a specific individual work

### Child-result handling modes
Possible modes:
- suppress
- collapse under parent
- demote
- show limited exemplars

Codex should document the actual intended policy and current implementation status.

## Family-cap policy

This section should define how many closely related results from the same family should be allowed near the top of the visible list.

Questions to answer:
- Is there a cap for sibling results from the same series or family?
- Is the cap hard or soft?
- Does it vary by result position?
- Are family caps bypassed for specific-intent queries?

Examples:
- no more than 2 items from the same family in the first 10 visible results
- allow more siblings only when the query clearly targets them

This section should define policy, not algorithmic detail.

## Diversity policy

This section should define when the system should surface distinct result types rather than continue showing many similar items.

Questions to answer:
- Should the system try to surface different content kinds when relevance is close?
- Should the system try to surface different media types when relevance is close?
- What kinds of diversity matter most on this site?
- Should diversity be a soft preference or a strong rule?

Examples:
- one video result should not be buried beneath many similar photo results if relevance is comparable
- one series result may deserve earlier placement among many child works

This is not a generic fairness policy. It is a site-specific information-value policy.

## Specific-match protection

This section should define which matches are protected from suppression or demotion.

Examples:
- exact work title match
- exact ID match
- strong title phrase match
- clearly specific child title query

Questions to answer:
- Which match types override family consolidation?
- Which match types override diversity caps?
- Is there a threshold below which a result is considered too weak to protect?

Codex should relate this section to the ranking model where relevant.

## Representative-result policy

This section should define what should be shown when a group is consolidated.

Examples:
- show only the parent series
- show the parent series plus 1–2 exemplar works
- show a parent result plus a label such as “12 works in this series”
- show one result per media type within a family

Questions to answer:
- What is the representative result for a group?
- Should collapsed children be countable or expandable in the UI?
- Should representatives differ by content kind?

This section is important because shaping affects not just order but visible composition.

## Relationship data required from the index

Result shaping depends on the search data exposing enough site structure.

This section should define what runtime shaping needs the index to provide.

Examples:
- `series_id` or equivalent parent relationship for works
- content `kind`
- media type
- family or group identifier, if distinct from series
- title or title-token fields sufficient to detect derivative naming
- possibly signals distinguishing own-title match from inherited family match

Codex should document what data already exists and what may need to be added later.

## Current implementation summary

This section should briefly describe whether result shaping is currently:

- not yet implemented
- partly implemented through ranking alone
- implemented informally in UI logic
- implemented as an explicit shaping stage

If not yet implemented, this section should say so clearly and describe the current behaviour as a baseline.

## Example scenarios

This section should contain concrete examples from the site.

At minimum, include examples like:

### Query: `grid`
Expected behaviour:
- show series `grid`
- suppress, collapse, or limit derivative works such as `grid 1`, `grid 2`, etc.

### Query: `grid 7`
Expected behaviour:
- show work `grid 7` prominently
- do not suppress the specific work because its parent series also matches

### Query: `digital print`
Expected behaviour:
- allow relevant works to appear even if many belong to one series
- do not treat this purely as a family-name query

### Query: one video match plus many photo matches
Expected behaviour:
- ensure the video has a fair chance to appear early if relevance is comparable

Codex should replace these placeholders with real site examples where possible.

## Configuration surface

If result shaping is or will be externally configurable, this section should define the policy surface.

Possible configurable areas:
- enable/disable family consolidation
- parent-child handling mode
- family result caps
- diversity dimensions
- score-distance threshold for diversity
- number of exemplars shown from a collapsed group
- specific-match protection threshold

This section should define policy areas rather than implementation format.

## Known limitations or open shaping questions

This section should capture unresolved shaping issues only.

Examples:
- whether current ranking preserves enough field provenance for shaping decisions
- whether family IDs need to be made more explicit in the index
- whether diversity should apply across kind, media type, or both
- whether collapsed child counts should be exposed in UI
- whether shaping rules should be query-length-sensitive
- whether broad metadata queries need a different shaping regime

## Out of scope for this document

This document should not define:

- raw schema semantics already covered elsewhere
- low-level ranking formulas
- low-level tokenisation rules
- DOM implementation details
- build-script mechanics beyond required relationship data

Those belong in other search documents.
