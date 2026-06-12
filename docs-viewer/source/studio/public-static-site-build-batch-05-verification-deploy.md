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

- Batch 1 is closed; re-check this batch after Batches 2-4 define final script paths and smoke commands.
- Do not keep a branch/folder Pages source or Jekyll deploy fallback as part of normal operations.
- GitHub Actions remains thin deployment plumbing around the repo-owned builder.
- Start this batch with dual-running: the static Actions workflow runs checks and manual/non-deploy validation while the current Jekyll publishing path remains live.
- The exact cutover point is the GitHub Pages source change to Actions artifact deployment plus enabling the deploy workflow for `push` to `main`.
- Local preview dual-running remains available during this batch so failed production checks are reproduced against both the Jekyll baseline and static output.

## Batch 1 handoff

- Workflow validation must run `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit` before artifact upload.
- Workflow defaults are fixed: `pull_request` verifies only, `push` to `main` deploys after cutover, `workflow_dispatch` is enabled, first version has no path filters, concurrency cancels older in-flight Pages deploys, the environment is `github-pages`, and permissions are limited to Pages deployment needs.
- Current repo state supports local workflow authoring and `gh` inspection. `.github/` exists but has no repo-owned workflow file; `gh` is authenticated; current Pages is legacy branch publishing from `main /`.
- Production cutover is the explicit GitHub Pages source change from legacy branch/Jekyll publishing to Actions artifact deployment plus enabling the deploy job for `push` to `main`.
- Before cutover, the static workflow can run in manual/non-deploy dual-running mode while the current live site continues to publish through the legacy path.

## Batch 4 handoff

Batch 4 produced an audited static artifact at `_public_site/` with 6899 copied public files, 11 rendered route pages, and 6912 checked files.

The local build and audit command for the workflow gate is:

```bash
$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit
```

The Batch 5 workflow must run that command before uploading the Pages artifact. The first workflow version stays in dual-running mode: manual and verification runs are active, production deploy remains disabled until Pages source cutover is performed and recorded.

Use this route list for local static smoke, Jekyll baseline parity, and workflow artifact validation:

- `/series/`
- `/series/?mode=moments`
- `/recent/`
- `/works/?work=00008&series=105`
- `/catalogue/search/`
- `/library/`
- `/analysis/`

Use this Jekyll baseline command for local dual-running comparison:

```bash
$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build
```

Batch 4 copied 44 public Docs Viewer runtime modules under `docs-viewer/runtime/js`. The copied closure is rooted at `docs-viewer-public.js` plus `docs-viewer-metadata-info-view.js`. Artifact validation must confirm these source-only or private runtime surfaces are absent:

- `docs-viewer/runtime/js/docs-viewer-management*.js`
- `docs-viewer/runtime/js/docs-viewer-manage.js`
- `docs-viewer/runtime/js/docs-html-import*.js`
- `docs-viewer/runtime/js/reports/`
- `docs-viewer/source/`
- `docs-viewer/generated/docs/studio/`
- `docs-viewer/generated/docs/tmp/`

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
- Use no path filters for the first production workflow.

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
| 5.1 | planned | Confirm the Batch 1 workflow defaults and replace placeholders with final Batch 2-4 command outputs before implementation. |
| 5.2 | planned | Implement the GitHub Actions Pages artifact workflow. |
| 5.3 | planned | Run the static workflow in dual-running mode without changing the live Jekyll publishing path. |
| 5.4 | planned | Run local dual-preview parity checks against the same public route list before production cutover. |
| 5.5 | planned | Wire the full verification gate into pull request and `main` workflow paths. |
| 5.6 | planned | Validate the Pages artifact contents with the named build-plus-audit command and deployment plumbing before production cutover. |
| 5.7 | planned | Switch GitHub Pages source to Actions artifact deployment only after the verification gate passes. |
| 5.8 | planned | Verify a live static artifact deploy from `main`, then record the cutover timestamp, workflow run, artifact path, and residual risks for Jekyll removal. |

## completed verification

- Not started.

## follow-on tasks

- Update Batch 6 with exact files, docs, and commands to remove or rewrite after static deploy parity is proven, including any GitHub settings changed during cutover.

## batch close

- Add a handoff note to [Batch 6](/docs/?scope=studio&doc=public-static-site-build-batch-06-jekyll-removal-closeout).
- Set this batch status and front matter `ui_status` to `done` after the verification gate and Actions deployment path are verified.
