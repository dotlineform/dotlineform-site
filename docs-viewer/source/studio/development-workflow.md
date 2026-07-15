---
doc_id: development-workflow
title: Development Workflow
added_date: 2026-05-23
last_updated: 2026-07-15
parent_id: dev-home
viewable: true
---
# Development Workflow

## Purpose

Use this page to move work from an idea to one complete, verifiable delivery. Use [Development Checklist](/docs/?scope=studio&doc=development-checklist) for implementation guardrails after the owning boundary is known.

## Fast Path

1. Name the user/maintenance outcome and the current code/config owner.
2. Decide whether this is a small direct change, concept exploration, or roadmap delivery.
3. Resolve decisions that would fundamentally change the outcome.
4. Split the work until one request can finish completely.
5. Implement through current owners; do not create transitional aliases as an end state.
6. Run the smallest evidence that proves the changed contract.
7. Update one durable documentation owner when its behavior/navigation changed.
8. Close only when the complete outcome ships; put later outcomes back on the roadmap.

## Concept, Architecture, Roadmap, Delivery

```text
broad need or discussion
  -> concept (what/why/open questions)
  -> proposed architecture (structure/ownership/weak spots)
  -> roadmap (priority and finishable sequence)
  -> one delivery request per complete outcome
  -> code + focused evidence
  -> durable owner updated
```

### Concept

Use a concept document when useful questions remain open. It may explain the long-term aim without pretending the entire aim is one request.

### Feature Parent

A substantial feature may have one short parent under [Change Requests](/docs/?scope=studio&doc=change-requests). It routes between concept, proposed architecture, roadmap, and active delivery documents. It does not repeat them.

### Roadmap

The owning roadmap states priority, sequence, dependencies, current status, and the active delivery request. “This must precede that” belongs here, not as a note buried at the top of one request.

Every roadmap row should be independently useful and finishable. Split a row before work starts if “partly complete” would be an acceptable stopping state.

### Delivery Request

One request owns one complete result and one documentation boundary. It may cross modules, but every change must serve the same verifiable outcome. Use a child task tracker only when coordination inside that bounded result genuinely needs one.

Small fixes, documentation cleanup, and mechanical maintenance normally need none of this machinery.

## Shape The Slice

Before editing:

- identify authoritative source, generated outputs, config, browser/server boundary, and write owner;
- name the responsibility added/moved and the module that will own it afterward;
- note the main benefit and meaningful risks;
- separate shell/rendering, validation/planning, mutation, and generated follow-through;
- prefer existing primitives/providers/services over route-local duplication;
- investigate first when deleting config or compatibility code; history explains but does not prove current use.

If implementation reveals another useful outcome, add/split it on the roadmap. Do not silently widen the active request.

## Verify Proportionally

Choose the lowest layer that proves the durable contract:

| Change | Usual evidence |
| --- | --- |
| documentation | source review, links/build when publication follow-through is in scope, `git diff --check` |
| pure model/parser/planner | focused unit/pytest |
| local service/API | direct function or HTTP contract test |
| generator | dry run, output-shape check, then explicit write if required |
| route/module integration | focused browser smoke only when the browser boundary is the risk |
| visual/tactile UI | manual or temporary browser inspection |
| broad cross-app contract | narrowest relevant `run_checks.py` profile |

Loopback/browser checks may need elevated local permissions. Do not run broad profiles merely to produce more evidence.

[Testing](/docs/?scope=studio&doc=testing) owns test policy; [Run Checks](/docs/?scope=studio&doc=scripts-run-checks) owns current profile inventory.

## Documentation Boundary

Update a durable doc only when its current workflow, architecture, methodology, extension rule, weak spot, or navigation changed.

- Code/config/tests remain exact authority.
- Overview docs map capabilities and owners; they do not list every module/field/route.
- Focused contract docs may contain exact inventories when the inventory is the point.
- A change request records delivery decisions, not permanent implementation detail.
- Avoid generic Related lists; link only to an authority, prerequisite, or next action.
- Do not update several docs “in case” some wording becomes useful later.

Generated docs/search payloads follow source changes only when the task or watcher owns that follow-through.

## Closeout

Report:

- the outcome and important changed owners;
- focused verification and result;
- generated artifacts written or intentionally not rebuilt;
- known gaps/risks;
- any separate roadmap outcome created.

Mark a delivery request done only when its whole outcome works, durable docs describe shipped behavior, and remaining work is genuinely separate. Never hide unfinished phases inside a completed request.
