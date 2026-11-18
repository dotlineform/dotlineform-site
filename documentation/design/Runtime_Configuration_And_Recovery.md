---
draft: false
doc_id: d-20261118-190455-3a1e67
title: Runtime Configuration And Recovery
added_date: "2026-11-18 19:04:55"
last_updated: "2026-11-18"
summary: Rationale for explicit configuration owners, browser projections and phase-specific local recovery.
parent_id: d-20261118-151521-a0f9c3
---
# Runtime configuration and recovery

## Keep authority at its owner

The local environment binds a machine to existing storage and service addresses. Checked workspace config expresses document and destination policy. Generated browser config exposes reader URLs and display metadata. This keeps private paths and credentials within local services and gives each changed setting an explicit projection path. Public uses a read-only entrypoint and static config, so local capability changes stay with the local process. [Configuration owners](../reference/Configuration_And_Extension_Points.md)

Code registration owns executable behavior and each app kind's imports. A JSON flag can select a known contribution, while the local service still checks its operation inputs and storage boundary. The same distinction explains why opening a healthy route does not establish authoring or Publish availability. [Runtime trace](../reference/Runtime_Module_Ownership.md#trace-a-failure)

## Separate code release from content publication

The public site has no deploy-time build. Shared/public code is canonical under `docs-viewer/`, with a manifest-selected tracked projection in `site/`. Local apps can consume canonical code directly, and Pages can deploy the reviewed site snapshot. Workspace browser configuration uses that code-release path. Document and Catalogue output uses the prepared publication queues. [Projection contract](../reference/Projection_Contract.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Recover the completed phase

The sibling runners let a developer start the service involved in a failure. The integrated supervisor stops the session when a child exits, making a cross-app startup failure visible. At the operation level, source persistence, generation, queue handoff, transfer and display have separate completion points. Recovery uses the saved state and the failed owner. A blanket rebuild or repeated create can do unnecessary work or duplicate an already completed change. [Local recovery](../reference/Local_Setup.md#recover-the-failed-owner) · [Recorded evidence and follow-ups](../deliveries/Runtime_Configuration_And_Recovery_Review.md)
