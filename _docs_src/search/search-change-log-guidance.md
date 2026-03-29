---
doc_id: search-change-log-guidance
title: Search Change Log Guidance
last_updated: 2026-03-29
parent_id: search
sort_order: 2
---

# Search Change Log Guidance

## Purpose

This document defines how the search change log should be maintained.

The search change log is intended to be the short historical record of meaningful search changes across:

- implementation
- schema
- field policy
- normalization
- ranking
- UI behaviour
- build pipeline
- validation
- architecture

It should help future review of search development without forcing someone to reconstruct intent from raw git history alone.

## Why this matters in this repo

In the current working model, search implementation and most search documentation updates are being written by Codex.

That makes a disciplined change log more important, not less.

Reason:

- Codex can implement multiple related changes in one session
- docs can be updated alongside code quickly
- without a disciplined log, it becomes harder later to answer:
  - what changed
  - why it changed
  - whether the change was implemented or only planned
  - which files and documents should be read together

The change log should therefore become part of the normal search close-out process.

## Scope

Add a search change-log entry when a change materially affects one or more of:

- search index schema
- field participation
- normalization rules
- ranking behaviour
- UI behaviour
- build pipeline or artifact generation
- indexed content scope
- search config architecture
- validation or regression process

Do not add an entry for:

- formatting-only edits
- typo fixes
- generic cleanup with no search effect
- doc wording changes that do not alter search design, behaviour, or maintainability in a meaningful way

## Relationship to other documents

Use the change log alongside:

- [Search Overview](/docs/?doc=search-overview)
- [Search Index Schema](/docs/?doc=search-index-schema)
- [Search Field Registry](/docs/?doc=search-field-registry)
- [Search Normalisation Rules](/docs/?doc=search-normalisation-rules)
- [Search Ranking Model](/docs/?doc=search-ranking-model)
- [Search UI Behaviour](/docs/?doc=search-ui-behaviour)
- [Search Build Pipeline](/docs/?doc=search-build-pipeline)
- [Search Validation Checklist](/docs/?doc=search-validation-checklist)
- [Search Config Architecture](/docs/?doc=search-config-architecture)

The change log records the fact of change. The other search docs define the resulting system.

## Repo-specific maintenance rules

These rules should be treated as the standard for this repo and environment.

### 1. Write the entry in the same change set

If a search change is meaningful enough to alter behaviour, structure, or maintenance burden, update [Search Change Log](/docs/?doc=search-change-log) in the same change set.

Do not leave the log as a later cleanup task.

### 2. Codex writes the entry at close-out

Because Codex is currently the main author of search changes, Codex should draft the change-log entry during close-out.

The entry should reflect:

- the implemented change
- the reason for the change
- the practical effect
- the main affected docs/files

This should happen before or alongside the final code-close summary, not after the fact from memory.

### 3. Newest first

Entries should be ordered newest first.

This matches how the log will most often be read during active development.

### 4. One entry per logical search change

Prefer one entry per meaningful search change set.

Examples:

- good:
  - one entry for “implemented Studio search v1”
  - one entry for “introduced batched result expansion”
- bad:
  - separate entries for a JS file, a CSS file, and a doc file that all belong to the same functional change

### 5. Use absolute dates

Always use `YYYY-MM-DD`.

Do not use “today”, “yesterday”, or session-relative language.

### 6. Status must reflect repo reality

Use:

- `implemented` only when the behaviour or structure is actually in the repo
- `proposed` only when the log is recording an agreed design direction that is not yet implemented
- `revised` when an existing implemented behaviour is materially changed
- `reverted` when a previous implemented change is backed out

Do not mark something `implemented` just because it has been discussed.

### 7. Record effect, not just activity

An entry should explain the effect on search, not merely that files were edited.

Bad:

- “Updated search docs”

Good:

- “Split the search documentation into focused documents so schema, ranking, normalization, UI behaviour, and pipeline rules can be reviewed independently”

### 8. Affected files/docs should be selective

List the most important files and documents only.

Do not turn the log into a raw dump of every touched file.

Focus on:

- key implementation files
- key config files
- key documents that must now be read differently

## Logging principles

### Concise

Each entry should be short enough to scan quickly.

### Factual

Describe what changed and why. Do not pad entries with generic narrative.

### Traceable

Make it easy to identify the implementation or documentation surface affected.

### Behaviour-focused

Explain the effect on search behaviour, search data, or maintainability.

### Durable

Write entries so they remain useful months later, when the specific session context is gone.

## When to add an entry

Add a change-log entry when:

- a field is added, removed, renamed, activated, deactivated, or reclassified
- ranking precedence changes
- normalization rules change
- the search UI trigger, state model, or result presentation changes
- search index generation or source inputs change
- a new content type is indexed or excluded
- search config boundaries or policy externalization changes
- validation procedure changes materially
- a bug fix changes actual user-visible search behaviour

## Entry format

Use this exact structure:

## [YYYY-MM-DD] Short change title

**Status:** proposed | implemented | revised | reverted

**Area:** schema | field registry | normalisation | ranking | UI | build pipeline | validation | architecture

**Summary:**  
Short statement of what changed.

**Reason:**  
Why the change was made.

**Effect:**  
What practical effect the change has on search behaviour, data, or maintainability.

**Affected files/docs:**  
- `path`
- `path`

**Notes:**  
Optional short follow-up note, migration note, or unresolved consequence.

## Interpretation of status values

### proposed

Use when the change is documented and agreed directionally but not implemented yet.

### implemented

Use when the change is present in the repo and reflected in the current system.

### revised

Use when a previously implemented behaviour is materially changed but not removed entirely.

### reverted

Use when a previous implemented change is rolled back.

## Interpretation of area values

### schema

Changes to the search index structure or serialized contract.

### field registry

Changes to which fields are active, displayed, filterable, or reserved.

### normalisation

Changes to index-time or query-time transformation rules.

### ranking

Changes to precedence bands, tie-breaking, or fallback behaviour.

### UI

Changes to the search page or result interaction model.

### build pipeline

Changes to inputs, generation flow, output artifact behaviour, or build-time validation.

### validation

Changes to regression queries, QA rules, or checklist process.

### architecture

Changes to the structural boundary between docs, config, and code.

## What should stay out of the log

Do not put these in the change log:

- full design rationale essays
- implementation walkthroughs
- long code excerpts
- unresolved brainstorming with no associated change
- copyediting history

Those belong in the focused search docs.

## Recommended style for Codex-authored entries

Because Codex is currently authoring most search work, entries should follow these style rules:

- write in plain factual prose
- avoid self-reference such as “I changed”
- avoid process narration such as “after reviewing”
- prefer behaviour and effect over implementation trivia
- mention docs and code together when both changed as part of one logical search change

## Initial guidance for close / commit process

For any meaningful search change, Codex should do this before final close-out:

1. update the relevant focused search docs
2. add or revise the search change-log entry
3. rebuild docs payloads
4. include the search-log update in the final summary

This should become the standard search close / commit flow in this repo.
