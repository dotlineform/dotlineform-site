---
doc_id: site-change-log-guidance
title: Site Change Log Guidance
last_updated: 2026-03-31
parent_id: ""
sort_order: 100
---

# Site Change Log Guidance

## Purpose

This document defines how the main site change log should be maintained.

The site change log is the historical record for meaningful non-search changes across:

- works, series, and moments runtime behaviour
- shared site shell behaviour
- non-search Studio features
- site and Studio UI patterns outside search
- content-generation and JSON data-flow changes that affect the wider site
- site-level architecture and validation changes

Search has its own dedicated change log and should remain separate.

## Why this matters in this repo

This repo now has two different levels of change history need:

- [Search Change Log](/docs/?scope=studio&doc=search-change-log) for the search subsystem
- [Site Change Log](/docs/?scope=studio&doc=site-change-log) for the rest of the site and non-search Studio evolution

That split is useful because search is already a distinct subsystem, while the rest of the site is more stable but still changes in meaningful ways.

Without a dedicated non-search site log, later review becomes harder when trying to answer:

- when the site runtime changed
- when data flow changed
- when a Studio feature changed
- whether a change was architectural, behavioural, or only internal cleanup

## Scope

Add a site change-log entry when a change materially affects one or more of:

- works, series, or moments behaviour
- shared layouts or site shell runtime
- generated JSON contracts used by the site
- non-search Studio feature behaviour
- site-level build pipeline or validation
- architecture boundaries in the wider site

Do not add an entry for:

- search-only changes
- formatting-only edits
- typo fixes
- internal cleanup with no behavioural or structural effect

## Relationship to other documents

Use the site change log alongside:

- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- relevant Studio docs for non-search features

Search-specific history belongs in:

- [Search Change Log](/docs/?scope=studio&doc=search-change-log)

## Repo-specific maintenance rules

### 1. Keep search and non-search history separate

If a change is search-specific, log it in [Search Change Log](/docs/?scope=studio&doc=search-change-log).

If a change affects the broader site or non-search Studio features, log it in [Site Change Log](/docs/?scope=studio&doc=site-change-log).

If a change materially affects both, add short entries to both logs.

### 2. Write the entry in the same change set

If a change is meaningful enough to alter behaviour, architecture, data contracts, or maintenance burden, update the site change log in the same change set.

### 3. Codex writes the entry at close-out

Because Codex is currently writing most implementation work in this repo, Codex should draft the site change-log entry during close-out.

The entry should capture:

- what changed
- why it changed
- the practical effect
- the main affected docs/files

### 4. Newest first

Keep entries ordered newest first.

### 5. One entry per logical change

Prefer one entry per meaningful site change set.

Do not create one entry per file.

### 6. Record effect, not just activity

Entries should describe behaviour, data flow, architecture, or maintenance impact.

Bad:

- “Updated site docs”

Good:

- “Moved work detail runtime to per-work JSON and retired the old aggregate work details index”

### 7. Keep affected files selective

List the most important code paths, data artifacts, and docs only.

## Entry format

Use this exact structure:

## [YYYY-MM-DD] Short change title

**Status:** proposed | implemented | revised | reverted

**Area:** works | series | moments | site shell | Studio | build pipeline | validation | architecture

**Summary:**  
Short statement of what changed.

**Reason:**  
Why the change was made.

**Effect:**  
What practical effect the change has on the site, its data flow, or its maintainability.

**Affected files/docs:**  
- `path`
- `path`

**Notes:**  
Optional short follow-up or migration note.

## Interpretation of status values

### proposed

Documented and agreed direction, not yet implemented.

### implemented

Present in the repo and part of the current system.

### revised

A previously implemented behaviour was materially changed.

### reverted

A previously implemented change was rolled back.

## Interpretation of area values

### works

Changes to works runtime, works pages, or works data contracts.

### series

Changes to series runtime, series pages, or series data contracts.

### moments

Changes to moments runtime, moments pages, or moments data contracts.

### site shell

Changes to shared layouts, navigation, shell runtime, or site-wide UI behaviour.

### Studio

Changes to non-search Studio features and shared Studio behaviour.

### build pipeline

Changes to generation flow, source inputs, generated artifacts, or pipeline behaviour affecting the wider site.

### validation

Changes to checks, audits, or QA process for the wider site.

### architecture

Changes to higher-level structure, boundaries, or long-lived design decisions.

## Recommended style for Codex-authored entries

- write in plain factual prose
- avoid self-reference
- avoid long implementation narrative
- mention code and docs together when both changed as one logical change
- focus on the effect of the change rather than the activity of editing files

## Initial guidance for close / commit process

For any meaningful non-search site or Studio change, Codex should do this before final close-out:

1. update the relevant focused docs
2. add or revise the site change-log entry
3. rebuild docs payloads if `_docs_src/` changed
4. include the site-log update in the final summary
