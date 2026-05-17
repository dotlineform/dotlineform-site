---
doc_id: site-change-log-guidance
title: Site Change Log Guidance
added_date: 2026-03-31
last_updated: "2026-05-06 20:58"
parent_id: site-change-log
sort_order: 1000
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
- shared layouts or site shell runtime in a way that changes the public or Studio experience beyond a local affordance
- generated JSON contracts used by the site
- non-search Studio feature behaviour at workflow, data, or server/API level
- site-level build pipeline or validation policy
- architecture boundaries in the wider site

Use these questions before adding an entry:

- did the change alter server behavior, service endpoints, generated data contracts, or build/write responsibilities?
- did it introduce a new module, route, workflow, or meaningful abstraction, or significantly change existing shared code?
- did it change user-facing behavior enough to require focused smoke testing, manual validation, or a product/design decision?
- would a future maintainer reasonably look in the change log to answer when this behavior or contract changed?

If the answer is no to all of those questions, do not add a site change-log entry.

Do not add an entry for:

- search-only changes
- formatting-only edits
- typo fixes
- internal cleanup with no behavioural or structural effect
- local copy, link-target, label, or small UI affordance changes that do not alter workflow semantics
- routine docs updates that explain or follow a small implementation change
- narrow bug fixes where the affected feature doc, script doc, or code diff is the better record

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

### 0. Keep the current page compact

Add new entries to [Site Change Log](/docs/?scope=studio&doc=site-change-log).

Keep older entries in dated archive child docs under the same parent when the current page becomes too long to edit comfortably.
Use flat `_docs/*.md` files with `parent_id: site-change-log` so the docs-viewer tree remains metadata-driven.

Current archive docs:

- [Site Change Log Archive: May 2026](/docs/?scope=studio&doc=site-change-log-2026-05)
- [Site Change Log Archive: April 2026](/docs/?scope=studio&doc=site-change-log-2026-04)
- [Site Change Log Archive: March 2026 And Earlier](/docs/?scope=studio&doc=site-change-log-2026-03-and-earlier)

Preferred archive threshold:

- keep roughly the latest 20-40 entries on the main page
- archive by month when practical
- use a broader oldest-history archive only when a period has too few entries to justify its own file

### 1. Keep search and non-search history separate

If a change is search-specific, log it in [Search Change Log](/docs/?scope=studio&doc=search-change-log).

If a change affects the broader site or non-search Studio features, log it in [Site Change Log](/docs/?scope=studio&doc=site-change-log).

If a change materially affects both, add short entries to both logs.

### 2. Write the entry in the same change set

If a change is meaningful enough to alter behaviour, architecture, data contracts, or maintenance burden, update the site change log in the same change set.

Do not add an entry merely because `_docs/` changed.
The focused owning doc should usually carry small implementation notes without promoting them into site history.

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
Do not create an entry for every small follow-up inside an already logged workflow unless it changes the settled contract or closes a meaningful phase.

### 6. Record effect, not just activity

Entries should describe behaviour, data flow, architecture, or maintenance impact.

Bad:

- “Updated site docs”
- “Changed result links to open in manage mode”

Good:

- “Moved work detail runtime to per-work JSON and retired the old aggregate work details index”
- “Moved document import/export dispatch behind adapter config”

### 7. Keep affected files selective

List the most important code paths, data artifacts, and docs only.

## Entry format

Use this exact structure:

## [YYYY-MM-DD] Short change title

**Status:** proposed \| implemented \| revised \| reverted

**Area:** works \| series \| moments \| site shell \| Studio \| build pipeline \| validation \| architecture

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

## Broken-link handling

Keep links in the current [Site Change Log](/docs/?scope=studio&doc=site-change-log) clean when writing new entries.

For archive docs, preserve historical wording unless a link no longer resolves.
The [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links) reports missing targets only, so visible link text can keep useful historical context.

When an archived entry points at a retired document:

- update the URL if there is a clear replacement doc
- keep the original visible link text when it is useful historical context
- convert the link to plain text only when there is no useful current target
- avoid creating stub docs solely to satisfy old changelog links

## Initial guidance for close / commit process

For any meaningful non-search site or Studio change, Codex should do this before final close-out:

1. update the relevant focused docs
2. add or revise the site change-log entry
3. archive older site change-log entries if the current page has grown beyond the preferred compact window
4. rebuild docs payloads if `_docs/` changed
5. include the site-log update in the final summary
