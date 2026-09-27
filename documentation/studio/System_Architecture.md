---
draft: false
doc_id: d-20260331-000000-4a16b0
title: Architecture
added_date: "2026-03-31 00:00:00"
last_updated: "2026-08-08 21:53:38"
summary: Cross-repository ownership, projections, shared artifact patterns, and system-level architecture references.
parent_id: ""
---
# Architecture

This section describes cross-repository ownership and contracts that do not belong to one app or public surface.

Use this section for:

- system-level purpose and boundaries
- source, generated, public, and working ownership
- cross-domain projection rules and validation
- shared artifact patterns

## References

- **[Knowledge System Vision](Knowledge_System_Vision.md)** for the cross-system purpose of Studio, Analytics, Docs Viewer, Data Sharing, semantic tokens, and the hybrid Analysis scope
- **[Source Tree Ownership](Source_Tree_Ownership.md)** for the maintained boundary between Studio source, Docs Viewer source, public source, generated output, and local working output
- **[Projection Contract](Projection_Contract.md)** for canonical source, local projection, and public projection boundaries
- **[Projection Contract Validation](Projection_Contract_Validation.md)** for executable cross-boundary enforcement
- **[Local Authoring Service And Publication Boundaries](Local_Authoring_And_Publication.md)** for the accepted Studio/Docs Viewer server composition, shared publication vocabulary, domain-specific publication timing, and reconsideration triggers
- **[Shared Artifact Patterns](Shared_Artifact_Patterns.md)** for reuse that crosses app ownership
- **[Data Models Diagrams](Data_Models_Diagrams.md)** for bounded logical and projection maps plus the shared method for producing them
- **[Site](Site.md)** for the public catalogue, routes, shell, design, and runtime data flow
