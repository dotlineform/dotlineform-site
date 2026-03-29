---
doc_id: search-config-architecture
title: Search Config Architecture
last_updated: 2026-03-29
parent_id: search
sort_order: 100
---

# Search Config Architecture

## Purpose

This document defines which parts of the site search system are treated as configurable policy and which parts remain implementation code.

The aim is to make the search subsystem easier to review, refine, and maintain. Search behaviour should not depend unnecessarily on values or rules buried inside JavaScript when those rules are likely to be discussed and adjusted as part of ongoing design work.

This document sits above the individual search config files and explains why they exist, what they control, and what they do not control. It explains the architecture choice; the registry and ranking docs should define the actual rules.

## Principle

The search system is divided into two layers:

- **Policy**: rules and settings that define what should be searchable, how important different fields are, and how the search interface should behave.
- **Mechanism**: the implementation code that performs tokenisation, matching, scoring execution, index loading, and result rendering.

Policy should be externalised where practical. Mechanism should remain in code.

## Externalised policy layers

The following layers should be defined outside the core search engine code.

### 1. Field registry

This layer defines which fields participate in search and how each field should be treated.

Examples:
- whether a field is searchable
- whether a field is filterable
- whether a field is displayed in results
- whether a field is treated as high, medium, or low importance
- whether a field supports phrase matching, token matching, or exact matching
- whether a field is tokenised or treated as a whole value

This layer expresses search design intent, not matching implementation.

### 2. Ranking policy

This layer defines the relative importance of matches across fields and match types.

Examples:
- title match outranks medium match
- exact phrase outranks token match
- series title match outranks year match
- multiple matched fields may receive a bonus
- generic fallback text should carry the lowest weight

This layer should express ranking priorities clearly and explicitly so they can be reviewed without reading scoring code.

### 3. Runtime UI behaviour

This layer defines how the search interface behaves in the browser.

Examples:
- minimum query length
- debounce interval
- maximum number of results
- whether results are grouped by content type
- content-type display order
- empty-state message
- whether scoped search is enabled

This layer controls user-facing behaviour rather than search relevance logic.

## Non-externalised layers

The following parts of the search system should remain in implementation code.

### Matching engine
The code that normalises queries, tokenises input, compares query terms against indexed data, and computes result scores.

### Tokenisation and normalisation implementation
The underlying functions that apply normalisation rules, split text into tokens, and perform exact, prefix, or token-level comparisons.

### Index loading and caching
The code that fetches the search index, stores it in memory, and manages lazy loading or partition loading.

### DOM rendering and interaction
The code that renders result items, handles keyboard navigation, focus states, click selection, and any other DOM-specific behaviour.

### Performance optimisations
Implementation details such as precomputed lookups, cached normalised values, or future inverted-index structures.

## Build-time vs runtime policy

Search policy exists in two different phases and should be kept conceptually separate.

### Build-time policy
Build-time policy determines how source content is transformed into the search index.

Examples:
- which source fields are included in the index
- whether slug values are expanded into spaced values
- whether aliases are added
- whether duplicate terms are removed
- whether derived search terms are emitted

Build-time policy affects index generation.

### Runtime policy
Runtime policy determines how the browser uses the generated index.

Examples:
- which indexed fields are searched first
- how fields are weighted
- how many results are shown
- when searching begins
- how results are grouped and displayed

Runtime policy affects browser behaviour only.

## Why this architecture is used

This split is intended to improve the following:

### Reviewability
Search rules can be inspected directly in small, focused files rather than inferred from implementation code.

### Maintainability
Common adjustments such as field weighting or UI limits can be changed without editing core matching logic.

### Clarity
The distinction between search design decisions and technical implementation becomes explicit.

### Stability
The matching engine can evolve internally without repeatedly changing the higher-level search policy surface.

### Collaboration
Policy documents and config files can be reviewed independently of JavaScript implementation details.

## Limits of externalisation

Not all search behaviour should be moved into config.

Over-externalisation can make the system harder to understand if low-level implementation details are represented indirectly through many configuration options. Config should be used for stable, reviewable policy decisions, not for every internal algorithmic choice.

The goal is not to eliminate code decisions. The goal is to expose the search rules that are likely to be discussed, tuned, and reviewed over time.

## Change rules

The following update rules apply:

- If a new searchable field is added, update the field registry documentation and config.
- If ranking priorities change, update the ranking model documentation and config.
- If search UI behaviour changes, update the UI behaviour documentation and runtime config.
- If tokenisation or matching algorithms change, update implementation documentation and code, not policy config unless the policy surface itself changes.
- If index generation rules change, update the build pipeline documentation and any build-time config.

## Initial target config surface

The initial externalised config surface should cover:

- searchable field registry
- ranking weights / ranking policy
- runtime UI behaviour

Other areas can remain in code until there is a clear need to expose them.