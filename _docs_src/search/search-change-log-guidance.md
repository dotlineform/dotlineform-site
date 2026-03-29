---
doc_id: search-change-log-guidance
title: Search Change Log Guidance
last_updated: 2026-03-29
parent_id: search
sort_order: 2
---

# Search Change Log

## Purpose

This document records meaningful changes to the site search subsystem over time.

Its purpose is to provide a concise, structured history of changes to search architecture, schema, field policy, normalisation, ranking, UI behaviour, and build pipeline behaviour so that the evolution of the system can be reviewed without relying on memory or scattered implementation notes.

This is not a diary and not a full technical narrative. Each entry should be brief, factual, and traceable to the relevant search documents.

- keep search_change_log.md as one file;
- make entries concise and uniform;
- when an entry grows beyond, say, a short structured block, move the long reasoning into a dedicated note and link it from the log.

## Scope

This log should capture changes that affect one or more of the following:

- search index schema
- search field registry
- normalisation rules
- ranking model
- UI behaviour
- build pipeline
- indexed content scope
- search config architecture
- validation process

This log should not be used for trivial wording fixes, formatting changes, or routine code cleanup unless those changes affect search behaviour, search data, or search maintainability in a meaningful way.

## Relationship to other documents

This document should be read alongside:

- `search_overview.md`
- `search_policy_externalisation.md`
- `search_index_schema.md`
- `search_field_registry.md`
- `search_normalisation_rules.md`
- `search_ranking_model.md`
- `search_ui_behaviour.md`
- `search_build_pipeline.md`
- `search_validation_checklist.md`

## Logging principles

The change log should follow these principles:

### Concise
Each entry should summarise the change clearly without becoming a design essay.

### Factual
Entries should describe what changed, not speculate beyond the change itself.

### Traceable
Each entry should point to the affected search documents or config files.

### Behaviour-focused
Entries should explain the effect of the change on search data, search behaviour, or search maintainability.

### Selective
Only meaningful changes should be logged.

## When to add an entry

Add a change-log entry when:

- a search field is added, removed, renamed, or reclassified
- a ranking rule or weight changes
- a normalisation rule changes
- the search UI trigger or result behaviour changes
- the search index build source or output structure changes
- a new content type is added to or removed from indexing
- a config layer is externalised or refactored
- a validation rule or regression test set changes materially
- a bug fix changes actual search behaviour

Do not add an entry for:
- typo fixes in documentation
- purely internal refactors with no behavioural or structural effect
- formatting-only changes
- comments added to code with no change in behaviour

## Entry format

Each entry should use the following structure.

### [YYYY-MM-DD] Short change title

**Status:** proposed | implemented | revised | reverted

**Area:** schema | field registry | normalisation | ranking | UI | build pipeline | validation | architecture

**Summary:**  
A short statement of what changed.

**Reason:**  
Why the change was made.

**Effect:**  
What effect the change has on search behaviour, search data, or maintenance.

**Affected files/docs:**  
List the main docs, config files, or implementation areas affected.

**Notes:**  
Optional brief notes on follow-up work, migration implications, or unresolved consequences.

## Interpretation of status values

proposed: The change has been agreed conceptually or drafted but is not yet fully implemented.

implemented: The change is now present in the current search system.

revised: An earlier change has been materially adjusted without being fully removed.

reverted: A previously implemented change has been rolled back.


## Interpretation of area values

schema: Changes to the structure of search index records or top-level index output.

field registry: Changes to which fields are searchable, filterable, displayed, or weighted by class.

normalisation: Changes to how source values or queries are transformed before matching.

ranking: Changes to match precedence, field weighting, tie-breaking, or fallback behaviour.

UI: Changes to search input behaviour, result display, keyboard interaction, or scoped modes.

build pipeline: Changes to source inputs, record construction, output paths, or validation during generation.

validation: Changes to regression queries, checklist coverage, or search QA rules.

architecture: Changes to the overall design boundary, such as externalising config or restructuring responsibilities.


## Change log maintenance rules

- Keep entries ordered newest first unless the repo uses a different standard consistently.
- Prefer one meaningful entry per logical change rather than many tiny entries.
- If a change affects multiple search documents, record it once with a clear affected-files list.
- If a proposed change is later implemented, either update the status or add a second implemented entry, depending on the project’s preferred logging style.
- If a change is reverted, add a new entry rather than silently editing history.


## Out of scope for this document

This document should not contain:

- full rule definitions
- code snippets unless strictly necessary
- full implementation explanations
- unresolved brainstorming not tied to an actual proposed or implemented change

Those belong in the main search design documents.

## Recommended entry style

Entries should answer five questions quickly:

What changed?
Why was it changed?
What is the practical effect?
Which documents or files now need to be read differently?
Is there any follow-up implication?

Avoid long prose. The supporting documents should hold the detailed rules; the change log should record the fact and significance of the change.


## Initial entries

Codex should populate the first real entries based on the current search v1 implementation and the documentation split that introduced the current search doc set.

Likely initial entries may include:

- creation of the search documentation set
- adoption of config/policy externalisation for selected search layers
- implementation of v1 client-side search index and runtime search
- any major schema decisions already present in the generated index
- any known ranking or duplication issues identified during review



# Example entries

## [2026-03-29] Created search documentation set

Status: proposed

Area: architecture

#### Summary:
Split the search documentation into focused documents covering overview, schema, field registry, normalisation, ranking, UI behaviour, build pipeline, validation, and change history.

#### Reason:
The previous single-document approach was too difficult to review and maintain as search design became more detailed.

#### Effect:
Search design can now be reviewed one concern at a time, and implementation can be compared against smaller, more targeted documents.

#### Affected files/docs:

- search_overview.md
- search_policy_externalisation.md
- search_index_schema.md
- search_field_registry.md
- search_normalisation_rules.md
- search_ranking_model.md
- search_ui_behaviour.md
- search_build_pipeline.md
- search_validation_checklist.md
- search_change_log.md

#### Notes:

Codex should populate each document from the implemented v1 search behaviour.


## [2026-03-29] Defined policy externalisation boundary for search

Status: proposed

Area: architecture

#### Summary:
Defined field registry, ranking policy, and runtime UI behaviour as the initial policy layers to be externalised from implementation code.

#### Reason:
These parts of the search system are likely to be reviewed and adjusted repeatedly and are easier to maintain when separated from core engine code.

#### Effect:
Search policy becomes easier to inspect and refine without reading search-engine internals.

#### Affected files/docs:

- search_policy_externalisation.md
- search_field_registry.md
- search_ranking_model.md
- search_ui_behaviour.md

#### Notes:
Tokenisation, matching implementation, rendering, and cache/loading logic remain in code for now.
