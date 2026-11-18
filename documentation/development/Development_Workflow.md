---
draft: false
doc_id: d-20260523-000000-bf7161
title: Development Workflow
added_date: "2026-05-23 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260419-000000-d2e47b

---
# Development Workflow

Move one user or maintenance outcome through implementation, review and acceptance. Use [Development Checklist](Development_Checklist.md) for guardrails. Small fixes and documentation edits usually need no delivery document.

## Planning And Delivery

Review [Working](../_working/README.md) for relevant active work. When a change needs a plan, write one concise document there with:

- the outcome, scope and meaningful benefits/risks;
- the intended user workflow and deliverables;
- ordered implementation steps, current/next state and completion gates;
- decisions still needed and genuinely separate follow-ons.

A larger feature can have a short parent and several independently complete deliveries. Add a concept, architecture note or child tracker only when it resolves real uncertainty or coordination. No central feature register or extra planning hierarchy is required. Proposed work is not implementation approval; mark work planned when its real prerequisites are satisfied and active when it starts.

The first delivery step is a short read-only sanity check against current owners: confirm a coherent result, broad authority, credible blast radius and stop conditions. Exact file inventories, frozen schemas, fixtures, prototypes and full test plans belong to separately authorised implementation when needed.

## Implementation

Choose the authoritative owner before the language or helper. State browser responsibility, concrete server work, source/configuration, outputs and completion effects. Inspect only enough of those owners and reused helpers to make the next safe change. Carry resolved inputs forward and keep consequential I/O visible.

Implement one complete result. If another useful outcome appears, record it separately rather than silently widening the delivery. A temporary sibling note can preserve detailed work between sessions when needed; link it from the delivery and remove it after transferring useful conclusions. Keep the delivery itself to current/next state, decisions, checkboxes and gates.

## Verify Proportionally

Use [Verification](Verification.md): focused static diagnostics, the required runtime projection/validation for affected public files, bounded code review and relevant manual acceptance. Explain what the selected evidence proves, its effects and important omissions. Ordinary check reporting belongs in the session or a compact delivery record.

Automated test scripts/profiles remain suspended pending the separate [test/check review](../_working/Review_Test_Policy_And_Checks.md). Their retirement, replacement or reactivation is separate work. Do not create or modify tests as incidental feature work.

For each material code/config delivery, retain a distinct review step after implementation and selected checks, including the [Redundancy And Defensive Behavior Review](Development_Checklist.md#redundancy-and-defensive-behavior-review). Record findings/resolutions and rerun only evidence affected by changes or unresolved risks. A documentation-only delivery uses bounded source/link review.

## Documentation Boundary

Keep current behaviour, owners and extension rules in Reference; reusable reasoning and tradeoffs in Design; active work in Working. Preserve a completed record in Deliveries only when its decisions, acceptance or verification history remain useful. A durable concept can be compiled into Design while its shipped behaviour has a Reference owner.

Update the smallest set of docs whose meaning or navigation changed. Do not mirror module/field inventories into overviews or accumulate transcripts. Links may lead to code, another maintained owner or useful delivery evidence; the current reference must still explain current behaviour without requiring a historical record.

Repository Markdown is edited directly with `apply_patch`, preserving surviving `doc_id` and `title` and repairing links/parents when files move or merge. Each paragraph/list item stays on one source line. Repository documentation edits require no Docs or Search build. External Working source edits have their own [exact generation workflow](../reference/Source_Organisation.md#explicit-external-edit-and-media-rebuilds); the watcher is retired.

## Closeout

Close only when the whole agreed result works, its durable owner is current and remaining outcomes are genuinely separate. Record the outcome, changed owners, selected evidence/results, generated effects, material limits and manual gates. Do not present scoped static evidence as application-wide acceptance.

Transfer useful material from temporary documents to its maintained home, then retain or retire those documents deliberately within the authorised scope. Move useful completed records to Deliveries. Reuse implementation evidence: a status-only closeout is bookkeeping, not another build/test/review programme. Commit, push, Publish and deployment retain their own explicit authority.
