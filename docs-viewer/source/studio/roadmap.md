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
| concept | problem, desired capability, lasting purpose, and feature invariants | priority, implementation tracking, or exact code inventories |
| architecture | proposed structure, ownership, extension method, and pressure points | shipped current-state authority |
| delivery | one complete, verifiable outcome or a short sequence of independently finishable outcomes | the whole long-term feature vision |
| durable document | shipped behavior, current architecture, extension method, and known weak spots | proposal history |
| maintenance index | curated links to actionable gaps in durable documentation | design, priority, or implementation tracking |

A feature can begin with only a concept. Add architecture when the structure is useful to reason about. Add a delivery when there is a coherent result worth building. Empty layers are not required merely to complete the tree.

A useful concept may outlive implementation. It can become the durable feature overview when it still explains why the capability exists, its stable mental model, and the invariants future changes should preserve. Temporary proposed architecture and delivery documents should not survive merely to retain implementation history.

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

## Closeout Shape

During development:

```text
App Roadmap
  -> Feature Parent
       -> Concept
       -> Proposed Architecture
       -> Delivery
```

After the complete feature ships:

```text
Durable App Documentation
  -> Feature Concept promoted to current overview
```

- Rewrite a retained concept in current-state language and remove resolved options or proposal history.
- Its title may lose “Concept”; its immutable `doc_id` does not change.
- Reparent it to the appropriate durable app owner.
- Fold stable technical structure into that overview or another current architecture owner only when it remains useful.
- Delete the temporary feature router, proposed architecture, and delivery documents when they no longer route unresolved work.
- Keep the feature parent only if unresolved concept, architecture, or delivery children still need navigation.

Git retains the retired delivery sequence and implementation history.

## Working Rules

- Keep one complete outcome per delivery.
- Put ordering in the app roadmap, not in a feature opening paragraph.
- Preserve large ideas in concept and architecture without compressing them into one build.
- Split work before starting when a partly finished result would be a plausible stopping point.
- If implementation exposes another useful result, put it back on the roadmap rather than silently widening the current delivery.
- Update one durable documentation owner by default.
- Close a delivery only when the complete result works and its durable owner is current.
- Promote a useful concept into durable documentation instead of automatically deleting the feature's reason and mental model.

Git retains completed chronology. Roadmaps should preserve decisions and useful future direction, not become execution diaries.
