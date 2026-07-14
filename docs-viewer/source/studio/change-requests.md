---
doc_id: change-requests
title: Change Requests
added_date: 2026-04-28
last_updated: 2026-07-14
parent_id: ""
---
# Change Requests

Change requests are delivery contracts for work that is ready to implement. Each request owns one complete, verifiable outcome and closes when that outcome is delivered.

## Keep The Layers Separate

| layer | owns | does not own |
| --- | --- | --- |
| feature parent | navigation between the feature's concept, architecture, and delivery documents | detailed discussion or implementation tracking |
| concept | the problem, desired capability, options, and open questions | priority or implementation tracking |
| architecture | the proposed structure, ownership boundaries, extension method, and known pressure points | shipped current-state authority or delivery sequence |
| roadmap | delivery order, importance, dependency, and status | detailed design or task history |
| change request | one finishable outcome that is ready to implement | the whole long-term feature vision |
| task tracker | optional coordination inside one request | multiple independently useful deliverables |
| durable document | shipped behavior, current architecture, extension method, and known weak spots | proposal history |

A long discussion is not automatically a change request. Keep it as a concept until its decisions are clear enough to split into roadmap deliverables.

For a substantial feature, add one short feature parent beneath Change Requests. Use children to keep concept, architecture, and promoted delivery requests separate. The parent is a router, not another place to repeat their content.

The feature does not need to be made artificially simple. Preserve the long-term aim and the architecture it exposes in those children; make only each promoted delivery request small enough to finish.

```text
Change Requests
  -> Feature Parent
       -> Concept
       -> Architecture
       -> Promoted Delivery Request

Product Roadmap
  -> orders the feature's finishable deliverables
```

## Promotion Gate

Create a request only when all of these are true:

- its outcome is useful and coherent on its own
- prerequisite deliverables are complete or genuinely part of this one outcome
- the in-scope and out-of-scope boundaries are explicit
- no open decision can fundamentally change the proposed outcome
- the code and configuration owners to inspect are known
- completion can be proved with a focused verification set
- one durable document has been named to receive shipped behavior

If a request needs several independently valuable phases, put those phases on the roadmap and create separate requests as they become ready. Do not use a large task tracker to conceal an oversized request.

## Request Shape

Keep a request short and operational:

1. **Outcome** — the complete result this request will deliver.
2. **Why now** — the roadmap dependency or problem that makes it current.
3. **In scope** — only the work required for that outcome.
4. **Not in scope** — adjacent capability that belongs to later roadmap rows.
5. **Code authority** — the likely owners to inspect, not an exhaustive file list.
6. **Done when** — observable behavior, focused verification, cleanup, and durable-doc transfer.

Implementation notes may change after code inspection. The request should constrain the outcome and boundaries, not pretend to be a second implementation authority.

## During Delivery

- Keep the request complete: do not mark a half-implemented phase as a finished request.
- Use a task tracker only when coordination inside the bounded request is genuinely difficult.
- If implementation exposes another useful outcome, add it to the roadmap rather than silently widening the request.
- Update one durable owner by default. Adjacent code changes do not create a requirement to update every adjacent document.

## Closeout

A request is done only when its whole outcome works, verification is recorded, temporary or compatibility paths are removed, and shipped behavior is captured by the named durable owner.

Move later ideas back to the roadmap. Let Git retain superseded discussion, completed checklists, and implementation chronology.
