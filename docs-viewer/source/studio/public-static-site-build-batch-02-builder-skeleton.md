---
doc_id: public-static-site-build-batch-02-builder-skeleton
title: Public Static Site Build Batch 2 Builder Skeleton and Artifact Contract
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 2 Builder Skeleton and Artifact Contract

This is the delivery specification for Batch 2 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: create the `public-site/` builder boundary and the initial static artifact contract.

## Steer for these tasks

- This batch must be re-planned after Batch 1 closes.
- Use the Batch 1 inventories to define builder modules, config fields, output path policy, and copy/audit allowlists.
- Keep the first builder small: create enough structure to emit an artifact root, `.nojekyll`, root publishing artifacts, and placeholder or parity shells selected by the refined plan.
- Keep the existing Jekyll local preview and production publishing path intact. The static builder introduced here is a parallel path and parity target, not the live path.

## Deliverables

- `public-site/build/build_site.py` and focused builder modules under `public-site/build/public_site_builder/`.
- `public-site/config/public-site.json` with only public-site assembly settings.
- `bin/public-site-build` wrapper for the static builder.
- `bin/public-site-preview-static` temporary static preview command that builds `_public_site/` and serves it with a simple local static HTTP server.
- Initial artifact output under the chosen `_public_site/` policy.
- Initial artifact audit command.

## Implementation and policy guidance

- The builder owns route HTML, public assets, generated public data, public Docs Viewer installs, root publishing artifacts, `.nojekyll`, and deployment surface checks.
- Do not copy arbitrary repo-root content.
- Do not add a general template engine. Batch 1 must record a rendering-model decision change before this batch uses one.

## Proposed verification set

- Python syntax/import checks for new builder modules.
- Build command writes the chosen output directory.
- Candidate static preview serves `_public_site/` over HTTP.
- Existing Jekyll preview command still works and remains the default preview baseline.
- Artifact root contains `.nojekyll` and the expected root publishing artifacts for this batch.
- Source-leak audit passes for the initial copy surface.

## Tasks

### Batch 2: Builder Skeleton and Artifact Contract

| ID | status | action |
| --- | --- | --- |
| 2.1 | planned | Re-plan this batch from Batch 1 audit findings before implementation starts. |
| 2.2 | planned | Create the `public-site/` builder package, config file, and command wrappers. |
| 2.3 | planned | Implement output-directory handling and artifact-root initialization with `.nojekyll`. |
| 2.4 | planned | Implement the initial root artifact allowlist and source-leak audit shell. |
| 2.5 | planned | Add `bin/public-site-preview-static` as the temporary static preview command that builds `_public_site/` once and serves it over HTTP. |
| 2.6 | planned | Confirm the existing Jekyll preview and deploy path are still untouched and available as the parity baseline. |
| 2.7 | planned | Record exact verification commands and update Batch 3 with route-rendering prerequisites. |

## completed verification

- Not started.

## follow-on tasks

- Fill in route rendering tasks after Batch 1 and Batch 2 identify the final render-helper boundaries.

## batch close

- Add a handoff note to [Batch 3](/docs/?scope=studio&doc=public-static-site-build-batch-03-route-parity).
- Set this batch status and front matter `ui_status` to `done` after the builder skeleton and artifact contract are verified.
