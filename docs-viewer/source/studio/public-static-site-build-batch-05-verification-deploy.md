---
doc_id: public-static-site-build-batch-05-verification-deploy
title: Public Static Site Build Batch 5 Verification Gate and GitHub Pages Actions Deploy
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: done
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

## Local implementation status

- `.github/workflows/public-site.yml` defines the repo-owned public-site workflow.
- `public-site/build/validate_artifact.py` validates the Pages artifact after the build-plus-audit command.
- The workflow runs on `pull_request`, `push` to `main`, and `workflow_dispatch`.
- The build job uses `actions/checkout@v6`, `actions/setup-python@v6`, `actions/configure-pages@v6`, and `actions/upload-pages-artifact@v5`.
- The deploy job uses `actions/deploy-pages@v5`.
- The deploy job is gated and remains inactive until a `main` push or `workflow_dispatch` run has repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` set to `true`.
- The workflow file is local only until committed and pushed.
- GitHub Pages still reports legacy branch publishing from `main /`; production cutover has not been performed.

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
| 5.1 | done | Confirm the Batch 1 workflow defaults and replace placeholders with final Batch 2-4 command outputs before implementation. |
| 5.2 | done | Implement the GitHub Actions Pages artifact workflow. |
| 5.3 | done | Run the static workflow in dual-running mode without changing the live Jekyll publishing path. |
| 5.4 | done | Run local dual-preview parity checks against the same public route list before production cutover. |
| 5.5 | done | Wire the full verification gate into pull request and `main` workflow paths. |
| 5.6 | done | Validate the Pages artifact contents with the named build-plus-audit command and deployment plumbing before production cutover. |
| 5.7 | done | Switch GitHub Pages source to Actions artifact deployment only after the verification gate passes. |
| 5.8 | done | Verify a live static artifact deploy from `main`, then record the cutover timestamp, workflow run, artifact path, and residual risks for Jekyll removal. |

## completed verification

- `gh repo view --json nameWithOwner,defaultBranchRef,visibility,viewerPermission` confirmed `dotlineform/dotlineform-site`, default branch `main`, public visibility, and admin viewer permission.
- `gh api repos/dotlineform/dotlineform-site/pages` confirmed current Pages state remains `build_type: legacy`, source `main /`, custom domain `www.dotlineform.com`, and HTTPS enforced.
- `$HOME/miniconda3/bin/python3 -m py_compile public-site/build/build_site.py public-site/build/validate_artifact.py public-site/build/public_site_builder/*.py` passed.
- `$HOME/miniconda3/bin/python3 -m pytest public-site/tests/test_build_site.py` passed: 3 tests.
- `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit` passed: 6899 copied public files, 11 rendered route pages, 6912 checked files.
- `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination /tmp/dlf-public-site-batch5 --audit` passed for a fresh temp artifact.
- `$HOME/miniconda3/bin/python3 public-site/build/validate_artifact.py --destination /tmp/dlf-public-site-batch5 --expected-docs-runtime-count 44` passed: 6912 files checked and 44 Docs Viewer runtime modules.
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/public-site.yml"); puts "workflow YAML parsed"'` passed.
- `git diff --check -- .github/workflows/public-site.yml public-site/build/validate_artifact.py` passed.
- `actionlint -version` reported `1.7.12`.
- `actionlint .github/workflows/public-site.yml` passed with no findings.
- Remote run `27434384898` for workflow `Public site` completed successfully on `main` push at commit `e1d7f4c405cff7e5e3a5280acf8b1c9249f4e572`.
- Remote run `27434384898` built and audited `_public_site/`: 6899 copied public files, 11 rendered route pages, and 6912 checked files.
- Remote run `27434384898` validated the artifact and uploaded Pages artifact `7599255347`.
- Remote run `27434384898` skipped the `Deploy Pages artifact` job because `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` was empty.
- `gh api repos/dotlineform/dotlineform-site/pages` still reports legacy Pages publishing from `main /`.
- The first remote run used older Pages action major versions and reported a Node.js 20 deprecation warning from `actions/configure-pages@v5` and the upload artifact dependency. The local workflow has been updated to `actions/configure-pages@v6`, `actions/upload-pages-artifact@v5`, and `actions/deploy-pages@v5` for the next remote validation run.
- Remote run `27434950394` for workflow `Public site` completed successfully on `main` push at commit `5dba605c6a3c01dd06119c3a9c3a85401157f1d1`.
- Remote run `27434950394` built and audited `_public_site/`: 6899 copied public files, 11 rendered route pages, and 6912 checked files.
- Remote run `27434950394` validated the artifact, uploaded Pages artifact `7599482687`, and skipped the `Deploy Pages artifact` job because `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` was empty.
- Remote run `27434950394` no longer reported the Node.js 20 deprecation warning after the Pages action version update.
- Remote run `27436272044` for workflow `Public site` completed successfully on `main` push at commit `d4874d961faf617370f2bc399a66d933a3de6e30`.
- Remote run `27436272044` confirmed the deploy gate supports `push` and `workflow_dispatch` events on `refs/heads/main`.
- Remote run `27436272044` built and audited `_public_site/`: 6899 copied public files, 11 rendered route pages, and 6912 checked files.
- Remote run `27436272044` validated the artifact, uploaded Pages artifact `7599997898`, and skipped the `Deploy Pages artifact` job because `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` was empty.
- Local dual-preview parity passed against fresh temporary outputs:
  - Jekyll baseline: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`, served on `http://127.0.0.1:8181`.
  - Static artifact: `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination /tmp/dlf-public-site-batch5-static --audit`, served on `http://127.0.0.1:8182`.
- Local dual-preview smoke passed for both Jekyll and static outputs on `/series/`, `/series/?mode=moments`, `/recent/`, `/works/?work=00008&series=105`, `/catalogue/search/`, `/library/`, and `/analysis/`.
- Local dual-preview smoke confirmed matching key route state: 80 work grid items, 56 moment grid items, 12 recent items, work `00008` title `nerve`, `nerve.pdf` download link to `https://media.dotlineform.com/works/files/nerve.pdf`, catalogue search ready text `Enter a search query.`, and public Docs Viewer `library` and `analysis` route IDs.
- Local dual-preview smoke reported no browser console errors for the checked route list.
- Temporary parity servers on ports `8181` and `8182` were stopped after verification.
- Cutover setting `PUBLIC_SITE_PAGES_DEPLOY_ENABLED=true` was set at `2026-06-12T18:57:02Z`.
- GitHub Pages source was switched to workflow publishing with `gh api --method PUT repos/dotlineform/dotlineform-site/pages -f build_type=workflow`.
- `gh api repos/dotlineform/dotlineform-site/pages` confirmed `build_type: workflow`, custom domain `www.dotlineform.com`, custom 404 enabled, and HTTPS enforced.
- Manual cutover deploy run `27436556962` for workflow `Public site` completed successfully via `workflow_dispatch` at commit `d4874d961faf617370f2bc399a66d933a3de6e30`.
- Manual cutover deploy run `27436556962` built and audited `_public_site/`: 6899 copied public files, 11 rendered route pages, and 6912 checked files.
- Manual cutover deploy run `27436556962` validated the artifact, uploaded Pages artifact `7600112973`, and deployed it to `https://www.dotlineform.com/`.
- Manual cutover deploy run `27436556962` completed the `Deploy Pages artifact` job successfully at `2026-06-12T18:57:51Z`.
- Live production smoke passed after cutover on `/series/`, `/series/?mode=moments`, `/recent/`, `/works/?work=00008&series=105`, `/catalogue/search/`, `/library/`, and `/analysis/`.
- Live production smoke confirmed key route state: 80 work grid items, 56 moment grid items, 12 recent items, work `00008` title `nerve`, `nerve.pdf` download link to `https://media.dotlineform.com/works/files/nerve.pdf`, catalogue search ready text `Enter a search query.`, and public Docs Viewer `library` and `analysis` route IDs.
- Live production smoke reported no browser console errors for the checked route list.
- Residual deploy-log note: `actions/deploy-pages@v5` emitted a Node `punycode` deprecation warning, but the Pages deployment reported success.

## follow-on tasks

- Batch 6 can start because live Actions artifact deployment is verified.
- Batch 6 must remove or retarget Jekyll/Ruby public-build paths, retarget `bin/public-site-preview`, and add scoped workflow path filters after closeout verification.

## batch close

- Handoff note added to [Batch 6](/docs/?scope=studio&doc=public-static-site-build-batch-06-jekyll-removal-closeout).
- Batch 5 is complete.
