---
doc_id: public-static-site-build-batch-04-assets-docs-viewer
title: Public Static Site Build Batch 4 Public Asset and Docs Viewer Artifact Assembly
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 4 Public Asset and Docs Viewer Artifact Assembly

This is the delivery specification for Batch 4 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: copy only the publishable public assets and generated payloads needed by the static route shells.

## Steer for these tasks

- This batch must be re-planned after Batch 1 closes.
- Use explicit allowlists from the Batch 1 artifact inventory.
- The generated artifact must contain public runtime files and must not contain source-only trees.

## Deliverables

- Public asset copy rules for CSS, JavaScript, images, thumbnails, public data payloads, catalogue/search payloads, and root metadata files.
- Public Docs Viewer copy rules for runtime modules, static CSS, public config, route config, and generated public docs/search payloads.
- Source-leak and projection-contract audits against the generated artifact.

## Implementation and policy guidance

- Keep domain-owned generated payloads with their current owners; the public-site builder assembles deployable copies.
- Do not copy Docs Viewer services, source docs, management runtime, private route config, or Studio docs payloads.
- Do not rely on Jekyll `_config.yml exclude` behavior.

## Proposed verification set

- Artifact surface audit.
- Projection contract audit.
- Browser smoke checks for public routes affected by copied assets.
- Static asset existence checks for Docs Viewer public mounts.

## Tasks

### Batch 4: Public Asset and Docs Viewer Artifact Assembly

| ID | status | action |
| --- | --- | --- |
| 4.1 | planned | Re-plan this batch from Batch 1 public asset and Docs Viewer inventories. |
| 4.2 | planned | Implement allowlisted static asset and public data copy rules. |
| 4.3 | planned | Implement allowlisted public Docs Viewer artifact copy rules. |
| 4.4 | planned | Implement source-leak and projection-contract audits. |
| 4.5 | planned | Record the complete public artifact surface for Batch 5 deployment checks. |

## completed verification

- Not started.

## follow-on tasks

- Update Batch 5 with exact artifact audit and smoke commands.

## batch close

- Add a handoff note to [Batch 5](/docs/?scope=studio&doc=public-static-site-build-batch-05-verification-deploy).
- Set this batch status and front matter `ui_status` to `done` after asset assembly and audits are verified.
