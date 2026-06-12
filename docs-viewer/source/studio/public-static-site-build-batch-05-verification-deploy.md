---
doc_id: public-static-site-build-batch-05-verification-deploy
title: Public Static Site Build Batch 5 Verification Gate and GitHub Pages Actions Deploy
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 5 Verification Gate and GitHub Pages Actions Deploy

This is the delivery specification for Batch 5 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: make the static builder the GitHub Pages artifact deployment path after the verification gate passes.

## Steer for these tasks

- This batch must be re-planned after Batch 1 closes and again after Batches 2-4 define exact build and audit commands.
- Do not keep a branch/folder Pages source or Jekyll deploy fallback as part of normal operations.
- GitHub Actions remains thin deployment plumbing around the repo-owned builder.
- Start this batch with dual-running: the static Actions workflow runs checks and manual/non-deploy validation while the current Jekyll publishing path remains live.
- The exact cutover point is the GitHub Pages source change to Actions artifact deployment plus enabling the deploy workflow for `push` to `main`.
- Local preview dual-running remains available during this batch so failed production checks are reproduced against both the Jekyll baseline and static output.

## Deliverables

- GitHub Actions workflow for pull request verification, `main` deploy, and manual `workflow_dispatch`.
- Artifact upload/deploy configuration for GitHub Pages.
- Full verification gate with exact commands.
- Workflow/artifact validation proving only the intended static output is deployed.
- A cutover record naming when the live site stops using the current Jekyll path and starts using the Actions artifact path.

## Implementation and policy guidance

- Production deploys through GitHub Actions Pages artifacts only.
- Until cutover is performed and recorded, the existing Jekyll publishing path remains the live path.
- After cutover, commits to `main` update the live site only when the Actions workflow succeeds and deploys the generated artifact.
- Use workflow concurrency so newer `main` deploys cancel older in-flight deploys.
- Keep workflow permissions limited to Pages deployment requirements.
- Avoid path filters for the first production workflow.

## Proposed verification set

- Static public-site build success.
- Artifact surface audit.
- Projection contract audit.
- Focused browser smoke tests for all simplified public catalogue routes.
- Focused browser smoke tests for `/library/` and `/analysis/`.
- Local preview parity checks against the Jekyll baseline and static output before production cutover.
- Artifact-root checks for `.nojekyll`, `CNAME`, favicon/site manifest files, and `404.html`.
- Workflow syntax validation and the artifact-content validation command named during Batch 1.

## Tasks

### Batch 5: Verification Gate and GitHub Pages Actions Deploy

| ID | status | action |
| --- | --- | --- |
| 5.1 | planned | Re-plan this batch from Batch 1 decisions and Batches 2-4 command outputs. |
| 5.2 | planned | Implement the GitHub Actions Pages artifact workflow. |
| 5.3 | planned | Run the static workflow in dual-running mode without changing the live Jekyll publishing path. |
| 5.4 | planned | Run local dual-preview parity checks against the same public route list before production cutover. |
| 5.5 | planned | Wire the full verification gate into pull request and `main` workflow paths. |
| 5.6 | planned | Validate the Pages artifact contents and deployment plumbing before production cutover. |
| 5.7 | planned | Switch GitHub Pages source to Actions artifact deployment only after the verification gate passes. |
| 5.8 | planned | Verify a live static artifact deploy from `main`, then record the cutover timestamp, workflow run, artifact path, and residual risks for Jekyll removal. |

## completed verification

- Not started.

## follow-on tasks

- Update Batch 6 with exact files, docs, and commands to remove or rewrite after static deploy parity is proven.

## batch close

- Add a handoff note to [Batch 6](/docs/?scope=studio&doc=public-static-site-build-batch-06-jekyll-removal-closeout).
- Set this batch status and front matter `ui_status` to `done` after the verification gate and Actions deployment path are verified.
