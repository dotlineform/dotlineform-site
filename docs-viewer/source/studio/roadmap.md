---
doc_id: roadmap
title: Roadmap
added_date: 2026-04-28
last_updated: 2026-07-15
parent_id: ""
---
# Roadmap

Roadmaps are where ideas become understandable, comparable, and eventually deliverable. They do not grant permission to work and they are not backlogs of implied obligations.

## Structure

```text
Roadmap
  -> App Roadmap
       -> Feature
            -> Concept
            -> Architecture
            -> Delivery
```

| layer | owns | does not own |
| --- | --- | --- |
| app roadmap | relative importance, sequence, dependencies, and current delivery | detailed feature discussion |
| feature | navigation between its concept, architecture, and delivery documents | duplicated design or implementation history |
| concept | problem, desired capability, options, and open questions | priority or implementation tracking |
| architecture | proposed structure, ownership, extension method, and pressure points | shipped current-state authority |
| delivery | one complete, verifiable outcome or a short sequence of independently finishable outcomes | the whole long-term feature vision |
| durable document | shipped behavior, current architecture, extension method, and known weak spots | proposal history |
| maintenance index | curated links to actionable gaps in durable documentation | design, priority, or implementation tracking |

A feature can begin with only a concept. Add architecture when the structure is useful to reason about. Add a delivery when there is a coherent result worth building. Empty layers are not required merely to complete the tree.

## App Roadmaps

- [Docs Viewer Roadmap](/docs/?scope=studio&doc=docs-viewer-roadmap)
- [Studio Roadmap](/docs/?scope=studio&doc=studio-roadmap)
- [Analytics Roadmap](/docs/?scope=studio&doc=analytics-roadmap)
- [Admin Roadmap](/docs/?scope=studio&doc=admin-roadmap)
- [Repository Roadmap](/docs/?scope=studio&doc=repository-roadmap)

## Delivery Shape

A delivery should state:

1. the complete result;
2. why it matters now in the owning roadmap;
3. what is and is not part of the result;
4. the likely code/config authority to inspect;
5. observable completion and focused evidence;
6. the durable document that receives shipped behavior.

Implementation notes may change after code inspection. A delivery constrains the outcome and boundary, not the exact implementation.

## Working Rules

- Keep one complete outcome per delivery.
- Put ordering in the app roadmap, not in a feature opening paragraph.
- Preserve large ideas in concept and architecture without compressing them into one build.
- Split work before starting when a partly finished result would be a plausible stopping point.
- If implementation exposes another useful result, put it back on the roadmap rather than silently widening the current delivery.
- Update one durable documentation owner by default.
- Close a delivery only when the complete result works and its durable owner is current.

Git retains completed chronology. Roadmaps should preserve decisions and useful future direction, not become execution diaries.
