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

- **[How the site fits together](../guide/How_The_Site_Fits_Together.md)** for the active site and app boundaries, with earlier design goals in the **[Knowledge System Vision](../deliveries/Knowledge_System_Vision.md)**
- **[Source Tree Ownership](Source_Tree_Ownership.md)** for the maintained boundary between Studio source, Docs Viewer source, public source, generated output, and local working output
- **[Projection Contract](Projection_Contract.md)** for canonical source, local projection, and public projection boundaries
- **[Projection Contract Validation](../deliveries/Projection_Contract_Validation.md)** for the older cross-boundary audit and its review boundary
- **[Local Runners](Local_Runners.md)** for Studio and Docs Viewer service composition and **[Publish and deploy](../guide/Publish_And_Deploy.md)** for the current publication sequence
- **[Shared Artifact Patterns](Shared_Artifact_Patterns.md)** for reuse that crosses app ownership
- **[Data Models Diagrams](Data_Models_Diagrams.md)** for bounded logical and projection maps plus the shared method for producing them
- **[Site](Site.md)** for the active public reader, checked deploy artifact and separately frozen Catalogue
