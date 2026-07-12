---
doc_id: site-request-docs-viewer-architecture-refactor-roadmap
title: Docs Viewer Remaining Architecture Work
added_date: 2026-07-10
last_updated: 2026-07-12
ui_status: in-progress
summary: Trigger-based candidates for remaining Docs Viewer lifecycle, command, routing, config, test, and CSS architecture work.
parent_id: change-requests
viewable: true
---
# Docs Viewer Remaining Architecture Work

## Status

The foundation refactor and Docs Review integration are complete. Explicit app contexts, provider boundaries, route-feature startup, view/mode/control projection, focused management workflow owners, and the reviewed-package collection workflow now have durable implementation and documentation owners.

This request tracks only architecture work that may still be useful. None of the items below is scheduled merely because a file is large or because it appeared in the original assessment.

## Decision

Retire the completed assessment and phase history from this request.

Future architecture changes should begin only when a current feature, recurring defect, ownership conflict, or verification problem provides a concrete trigger. Each material change should become a bounded child request or implementation task with its own behavior boundary and checks.

The current architecture is documented by:

- [Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership)
- [Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces)
- [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)

Those documents, not this request, own shipped behavior.

## Remaining Finding 1: Scope Lifecycle And Mutation Ownership

`docs-viewer/services/docs_scope_manifest.py` still combines several responsibilities:

- manifest storage and validation
- create planning and apply
- delete planning and apply
- owned-path policy
- route/build file planning
- public publication follow-through

The current service is functional and plan-first. Splitting it is worthwhile only when create and delete behavior need to change independently, repeated conflicts make ownership unclear, or a smaller boundary materially improves failure isolation and service-level testing.

Potential bounded slices:

- extract a manifest repository without moving create/delete policy into it
- separate create plan/apply from delete plan/apply
- keep path containment and ownership checks explicit at each write boundary
- keep rebuild orchestration in `docs-viewer/services/docs_write_rebuild.py`
- review source-config and manifest duplication only after the write owners are explicit

Do not combine this work with new scope lifecycle features or a schema migration unless a separate product request requires them.

## Remaining Finding 2: Management Command Families

The management coordinator now delegates import initialization, metadata, settings, scope lifecycle, event routing, and explicit state-domain queries to focused owners. Their current boundaries are recorded in [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership).

The only remaining candidate is to split action command families when a family gains independent state, lifecycle, authorization, or failure handling. A command-count or coordinator line-count threshold is not sufficient reason.

Any such slice should:

- keep backend write authority in the existing service clients and action owners
- expose narrow commands rather than another broad management facade
- move callers and tests with the owner in the same change
- avoid compatibility aliases or duplicate command paths

There is no standing task to split command families pre-emptively.

## Remaining Finding 3: Backend Service Routing

Local static serving and API-family dispatch may be separated if handler branching begins to obscure containment, authorization, or service startup behavior.

The trigger should be a concrete route-family change or recurring dispatch defect. A slice must preserve:

- explicit backend capability checks
- public/manage/review service separation
- safe static-root and external-workspace containment
- thin HTTP dispatch over service-owned behavior

Do not introduce a general routing framework for the current endpoint set.

## Remaining Finding 4: Config Projection Ownership

Docs Viewer legitimately has several configuration layers:

- canonical checked-in app and scope configuration
- browser-safe projections
- route records
- local service configuration
- code-owned controller, view, mode, and command definitions

Potential cleanup remains where the same derived fact is stored in more than one layer or where browser-visible config appears to grant backend authority.

A config slice should start with one duplicated field or ambiguous owner and establish:

- the canonical owner
- the projection path
- the consumers
- the validation boundary
- the migration and removal of the duplicate field

Do not consolidate distinct config purposes into one large schema.

## Remaining Finding 5: Test Contract Quality

Public import-graph and static-asset boundary checks remain valuable. Pure module and service tests should remain the default proof for ownership, parser, provider, plan, and mutation contracts.

Potential cleanup:

- replace source-string assertions with module or service contract checks when practical
- remove tests that preserve obsolete module layout rather than behavior
- keep browser smoke coverage for durable route boot, module wiring, and client/server agreement
- avoid permanent browser coverage for copy, focus timing, modal choreography, or layout

[Testing](/docs/?scope=studio&doc=testing) and [Development Checklist](/docs/?scope=studio&doc=development-checklist) own the durable test policy. This request should not duplicate their full check matrix.

## Remaining Finding 6: CSS Ownership

Toolbar, hosted-view, management, report, and Docs Review surfaces now have clearer runtime owners. That makes focused CSS cleanup possible, but not automatically necessary.

Potential work:

- audit base, manage, report, and review selectors against their component owners
- remove duplicated rules when one shared component contract exists
- keep management and review CSS out of public routes
- replace transitional route-specific classes only when all consumers can move together
- preserve host-token fallbacks for portable installs

[CSS Cascade Design](/docs/?scope=studio&doc=docs-viewer-css-cascade-design) owns the current stylesheet contract. CSS consolidation should be proposed there or in a dedicated child request when a concrete ownership boundary is ready.

## Work Owned Elsewhere

Keep these projects out of this request:

- documentation entrypoints, consolidation, summaries, and request cleanup — [Docs Viewer Documentation Cleanup](/docs/?scope=studio&doc=docs-viewer-documentation-register)
- exact-source JSONL and asset export — [Data Sharing Full Document Export Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)
- reviewed-package inspection — [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
- reviewed JSON/JSONL collection import — [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- future documentation search ranking or result-discovery work — create a separate request when there is an agreed search problem and outcome
- later catalogue-media or other cross-app workspace-root migrations — create separate requests around the owning application and path contract

## Slice Gate

Before starting one of the remaining candidates, record:

1. the current problem or product trigger
2. the current owner and affected consumers
3. the smallest responsibility that can move independently
4. behavior that must remain unchanged
5. the focused verification set
6. the durable documentation owner to update

If those points cannot be stated concretely, leave the current architecture in place.

## Guardrails

- Preserve current public, manage, and review behavior unless a separate product request changes it.
- Do not add compatibility aliases for moved modules, routes, fields, or config keys.
- Move callers, tests, and documentation with an ownership change.
- Do not let browser config grant backend read or write authority.
- Keep external user-workspace paths explicit and marker-rooted; do not derive them by joining untrusted values onto `repo_root`.
- Do not introduce plugin or framework machinery for a small fixed set of app contexts, views, commands, or endpoints.
- Prefer responsibility and contract evidence over file length.

## Completion

This request can close without implementing every candidate. It is complete when each remaining finding has either:

- produced a bounded active child request because a concrete trigger exists
- been transferred to a more specific current owner
- or been deliberately dropped because the current implementation remains adequate

Do not retain completed child-task chronology here after its durable outcomes have moved to the owning architecture or reference documents.
