---
doc_id: architecture
title: Architecture
last_updated: 2026-03-31
parent_id: ""
sort_order: 90
---
# Architecture

This section describes the current site building blocks and runtime boundaries.

Use this section for:

- public route structure
- generated artifact flow into runtime pages
- shared shell behavior
- cross-page runtime ordering rules
- how the current JSON-led catalogue workflow feeds those runtime surfaces

This section does not try to be the canonical home for:

- UI structure, CSS, or interaction design
  use [Design](/docs/?scope=studio&doc=design)
- detailed JSON or worksheet schema documentation
  keep that in focused data-model docs rather than embedding large schema explanations here

Related references:

- **[Data Flow](/docs/?scope=studio&doc=data-flow)** for which generated artifacts each public route reads at runtime
- **[Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)** for the shared shell, scope split, and docs-viewer shell boundary
- **[Sorting Architecture](/docs/?scope=studio&doc=sorting-architecture)** for canonical ordering across generated artifacts and runtime pages
- **[Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)** for the guardrail on when docs scopes should and should not fork the shared viewer runtime
- **[Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)** for the live rebuild path that refreshes the main runtime JSON artifacts used by public catalogue pages
- **[Site Change Log](/docs/?scope=studio&doc=site-change-log)** for the history of meaningful non-search site and Studio changes
- **[Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)** for maintenance rules and entry format
