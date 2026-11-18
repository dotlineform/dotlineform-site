---
draft: false
doc_id: d-20261118-190455-5d9c20
title: Runtime Configuration And Recovery Review
added_date: "2026-11-18 19:04:55"
last_updated: "2026-11-18"
summary: Preserved runtime and local-startup evidence, superseded setup assumptions and remaining code follow-ups.
parent_id: d-20261118-151521-a0f9c3
---
# Runtime configuration and recovery review

## Consolidated records

The 2026-11-18 review consolidated ten Studio pages into four reference owners for configuration, runtime modules, local setup and runners. The former environment, toolchain, recovery, preview, health and configuration-map satellites were retired after redirecting links and checking document identities. Original snapshots remain in Git at `c76f6608ef` under `documentation/studio/`. The runner's approved early-disconnect coverage description remains with its durable owner. [Current reference](../reference/Local_Setup.md) · [Design rationale](../design/Runtime_Configuration_And_Recovery.md)

Older setup suggested activating a named Conda environment while the launchers preferred the Miniconda base executable. The current setup names the interpreter actually selected. Earlier configuration text also mentioned removed collection-lifecycle and workspace-export workflows. Current collection registration is design-time-owned, and Export uses checked collection documents. [Runners](../reference/Local_Runners.md) · [Collection ownership](../reference/Source_Organisation.md#collection-deliveries) · [Export](../reference/Export.md)

## Earlier configuration walkthrough

The workflow-guide review changed the default document in a disposable copy, generated both canonical browser files, projected the public copy and passed projection/site validation. A deliberately missing public by-ID target produced an exact diagnostic. Restoring the original setting and regenerating passed both checks. That evidence covers config generation, projection and missing-default recovery. Bare-route interaction, live authoring, Publish and deployment were outside the walkthrough. [Recorded walkthrough](Site_Workflow_Guide_Triage.md#guide-walkthrough)

## Early disconnect delivery

The approved 2026-10-24 selection passed all six cases in 0.04 seconds. Focused lint, preview `--help` and source review covered the shared exception boundary and the three server integrations. It suppressed only a reset before the initial request-line read. Actual browser reset timing and live logging remained unverified. [Former coverage and selector](../reference/Local_Runners.md#focused-disconnect-test-coverage)

## Current review and remaining work

Source inspection traced runner bindings, environment precedence, workspace loading, served routes, capability responses, browser projection and static public loading. It found a disabled-Studio supervisor failure and the standalone Docs runner's workspace-environment gap. The tracker retains those code follow-ups. The later suite retirement resolved the stale Settings, scope configuration and public-boundary test findings. [Follow-up tracker](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups) · [Site test retirement](Review_Test_Policy_And_Checks.md)

This documentation batch checked redirected paths, headings, identities and whitespace. It did not start services, exercise browser flows, change configuration, run runtime tests or write to the external workspace.

## Later Local Service Map Review

The later documentation review consolidated Endpoint Overview, Generated Read Endpoints, Management Operations, Rebuild And Audit Endpoints and Scripts Overview. [One service map](../reference/Endpoint_Overview.md) now points to the current saved-read and mutation owners. Original versions remain at the Git recovery point above. The review removed Recent v2 examples, unregistered media-list URLs and the universal JSON `no-store` claim, and kept required local-target confinement and completed-effect reporting.

The 13 October 2026 mutation review implemented one browser-confirmed `/docs/delete` request using the complete loaded subtree or exact flat-collection target. The owner carried saved tree/Selected state and known deleted IDs through confined source/generated removal and awaited caller/fallback navigation. It retired preview/apply routes, disk revisions, generic plans, repeated preflights and automatic restoration without aliases. Failures retained completed effects and distinguished persistence/generation from browser projection/display. Focused Python/JavaScript lint, compilation/import diagnostics, bounded source/diff review, public projection/site validation and whitespace checks passed. No tests, browser or live mutation/failure cases ran; collapsed-subtree/flat deletion, caller return, busy completion and partial failures remained manual acceptance. The later design-time configuration change superseded its deletion-time default-clearing case. [Current mutation boundary](../reference/Source_Mutation_Endpoints.md#completion-and-recovery) · [Rule-review retirement and original records](Rationalise_Documentation.md#data-model-and-rule-review-retirement)

This preserved evidence establishes no new live failure coverage. Retained generated-read tests still require tree membership/scope APIs; metadata/mutation and collection-delete tests still use retired assignment, revision and preview/apply/automatic-recovery contracts. The tracker records separately scoped test review.

Current source inspection followed a Concepts readiness change through caller, HTTP dispatch, exact generation, committed-record projection and later queue-only Publish. Documentation path, anchor, identity and whitespace checks provide the evidence for this batch; it ran no service/UI operation, runtime test, Build, publication or deployment. Live development guidance remains in its separate follow-on.

## Architecture And Entry Point Consolidation

The next documentation batch retired the Architecture and Site link hubs in favour of the guide, repository map and public-shell owner. It shortened Docs Viewer to an app/authority/reference map and Source Tree Ownership to current roots and handoffs. Their original versions remain at the Git recovery point above. Source Tree's lint, shared-frontend, compatibility and placement rules were carried unchanged into Reference for the separate live-guidance review.

[Shared Artifact Patterns](../design/Shared_Artifact_Patterns.md) now preserves the rationale for independent shells, navigation, exact content and discovery. The former generic assurance suggestions called for a source/model owner, projection contract, schema/fixture checks, cross-reference audits and a rebuild path. That checklist supplies no specific test specification, current coverage or automatic run requirement; the separate guidance follow-on and maintained Testing policy own those decisions.

The review checked workspace, route/projection configuration and code ownership. It retained the frozen Catalogue's existing history rather than duplicating it, and did not reinterpret co-located Processing/native code as website runtime. Processing's older scope/integration assertions remain for their own batch; its collection-naming mismatch with live instructions is recorded in the tracker. Documentation link/identity checks provide this batch's evidence, with no runtime, media, publication or deployment operation.
