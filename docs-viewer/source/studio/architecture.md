---
doc_id: architecture
title: Architecture
added_date: 2026-03-31
last_updated: "2026-05-06 20:49"
parent_id: ""
---
# Architecture

This section describes the current site building blocks and runtime boundaries.

Use this section for:

- public route structure
- generated artifact flow into runtime pages
- shared shell behavior
- cross-page runtime ordering rules
- how the current JSON-led catalogue workflow feeds those runtime surfaces

## References

- **[Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)** for the maintained boundary between Studio source, Docs Viewer source, public Jekyll source, generated output, and local working output
- **[Data Flow](/docs/?scope=studio&doc=data-flow)** for which generated artifacts each public route reads at runtime
- **[Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)** for the shared shell, scope split, and docs-viewer shell boundary
- **[Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)** for canonical ordering across generated artifacts and runtime pages
- **[Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)** for the guardrail on when docs scopes should and should not fork the shared viewer runtime
- **[Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)** for the live rebuild path that refreshes the main runtime JSON artifacts used by public catalogue pages
