---
doc_id: data-models
title: Data Models
last_updated: 2026-03-31
parent_id: ""
sort_order: 23
---

# Data Models

This section is the main reference for the site’s current checked-in data contracts.

It covers:

- generated JSON artifacts that the runtime reads directly
- source Markdown files where the Markdown itself acts as a route or identity record
- how those artifacts map onto the three live scopes:
  - `catalogue`
  - `studio`
  - `library`
- the shared patterns that recur across scopes

It does not try to replace:

- [Config](/docs/?scope=studio&doc=config), which owns config files and loader modules
- [Scripts](/docs/?scope=studio&doc=scripts), which owns command usage and build mechanics
- [Architecture](/docs/?scope=studio&doc=architecture), which owns route/runtime boundaries

## How To Read This Section

Read it in this order:

1. **[Shared Patterns](/docs/?scope=studio&doc=data-models-shared)** for the common conventions used across generated artifacts
2. **[Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)** for public works, series, moments, and catalogue search data
3. **[Studio Scope](/docs/?scope=studio&doc=data-models-studio)** for Studio tag data plus the Studio docs corpus and Studio docs search data
4. **[Library Scope](/docs/?scope=studio&doc=data-models-library)** for the Library docs corpus and Library docs search data

## Practical Rule

When a schema or artifact contract changes:

- update the relevant scope doc here
- update the consumer doc in the owning section if runtime behavior also changed
- update [Scripts](/docs/?scope=studio&doc=scripts) if the writer or validator contract changed

If a model family becomes too dense for one scope doc, split out a child doc for that family rather than turning the scope doc into a field-by-field dump.
