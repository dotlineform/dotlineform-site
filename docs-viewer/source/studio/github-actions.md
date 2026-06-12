---
doc_id: github-actions
title: GitHub Actions
added_date: "2026-06-12 15:35"
last_updated: "2026-06-12 19:24"
parent_id: dev-home
---
# GitHub Actions

Relates to [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build).

The Actions workflow itself is just repo code, but the Pages cutover is a GitHub repo setting.

**What can be done locally / in VS Code**

- Create `.github/workflows/public-site.yml`.
- Add the builder commands the workflow will run.
- Run the same build/audit/smoke commands locally.
- Commit and push the workflow like any other file.
- Add `workflow_dispatch` so the workflow can be run manually from GitHub later.

Current local and remote state:

- `.github/workflows/public-site.yml` exists locally as the repo-owned public-site workflow.
- `gh` is installed at `/opt/homebrew/bin/gh`.
- `gh` is authenticated as `dotlineform` with `repo` and `workflow` scopes.
- `gh repo view` reports `dotlineform/dotlineform-site`, default branch `main`, public visibility, and admin viewer permission.
- GitHub Actions are enabled for the repo and allowed actions are set to `all`.
- The only workflow currently listed is GitHub's `pages-build-deployment`, which belongs to the current Pages path rather than a repo-owned workflow file.
- GitHub Pages currently reports `build_type: legacy`, source `main /`, custom domain `www.dotlineform.com`, custom 404 enabled, and HTTPS enforced.
- The local public-site workflow is not active on GitHub until it is committed and pushed.

So from this session Codex can create and inspect workflow files locally, use `gh` to inspect repo/Pages/Actions state, and after a workflow has been pushed, trigger and inspect workflow runs. Production cutover remains an explicit approval step because it changes the live deployment source.

**How `_public_site/` is uploaded**

The static artifact directory is build output, not committed source. In Batch 5, GitHub Actions will create `_public_site/` on the Actions runner, upload that directory as the Pages artifact, then deploy that artifact through GitHub Pages.

The workflow shape is:

```yaml
- name: Build static public site
  run: python public-site/build/build_site.py --destination _public_site --audit

- name: Upload Pages artifact
  uses: actions/upload-pages-artifact@v5
  with:
    path: _public_site

- name: Deploy to GitHub Pages
  uses: actions/deploy-pages@v5
```

The runner sequence is:

- Check out the repository.
- Run the static public-site builder.
- Create a fresh `_public_site/` directory on the runner.
- Package exactly `_public_site/` with `actions/upload-pages-artifact`.
- Publish that artifact with `actions/deploy-pages`.

The local `_public_site/` directory is only preview/test output. The deployed `_public_site/` is created fresh by the workflow run.

**Deployment gate**

The first repo-owned workflow is dual-running by default. It builds, audits, validates, configures Pages, and uploads the Pages artifact, but it does not deploy until the live cutover is explicitly enabled.

The deploy job runs only when all of these are true:

- The workflow event is a `push`.
- The pushed ref is `refs/heads/main`.
- The repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` is set to `true`.

Until that repository variable is enabled and the GitHub Pages source is switched to Actions artifact publishing, the current legacy Pages path remains live.

**Where `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` is set**

`PUBLIC_SITE_PAGES_DEPLOY_ENABLED` is a GitHub Actions repository variable. It is not a tracked repo file and it is not stored in local environment files.

Set it in the GitHub repository UI:

```text
Settings -> Secrets and variables -> Actions -> Variables -> Repository variables
```

The deploy gate reads it as:

```yaml
PUBLIC_SITE_PAGES_DEPLOY_ENABLED: ${{ vars.PUBLIC_SITE_PAGES_DEPLOY_ENABLED }}
```

Allowed cutover value:

```text
PUBLIC_SITE_PAGES_DEPLOY_ENABLED=true
```

Absent, empty, or any value other than exactly `true` keeps the deploy job skipped. Setting this variable is only one part of cutover; GitHub Pages must also be switched from legacy branch publishing to Actions artifact publishing.

**How workflow failures are debugged**

The public-site Python builder runs on GitHub's Actions runner during Batch 5 deployment validation. Build and deployment failures are inspected in the GitHub Actions run logs first, then reproduced locally with the same build-plus-audit command.

Use this local reproduction command for builder and artifact-audit failures:

```bash
$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit
```

Debugging sequence:

- Inspect the GitHub Actions run log to identify the failing step.
- Classify the failure as build, audit, artifact upload, permissions, or Pages deployment.
- Reproduce build and audit failures locally with the same command.
- Fix repo-owned builder, config, or content issues locally.
- Push the fix and rerun the GitHub workflow.

Build and audit failures normally reproduce locally. GitHub-only failures include Pages permissions, Pages environment settings, artifact deployment plumbing, and runner-specific filesystem assumptions such as filename case sensitivity.

**What must happen on GitHub**

- GitHub Actions runs only after the workflow file exists on GitHub.
- Manual runs require `workflow_dispatch`; GitHub supports running those from the Actions tab, GitHub CLI, or REST API.
- Pages custom workflow deployment must be enabled/configured for the repo’s Pages source.
- The actual cutover is: GitHub Pages source changes from branch/Jekyll publishing to GitHub Actions artifact publishing.

Officially, GitHub Pages custom workflows use Actions plus the Pages artifact/deploy actions, and the deploy job needs `pages: write` and `id-token: write` permissions with a Pages environment, typically `github-pages`: [GitHub custom workflows for Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

GitHub also documents that custom workflows must be enabled through the Pages publishing source setup: [configure publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Manual runs are via `workflow_dispatch`: [manually run a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

**What Codex can do**

- Write the workflow YAML.
- Write/adjust `public-site` build and preview scripts.
- Run local parity checks.
- Run local syntax/build/audit checks.
- Prepare the exact GitHub settings checklist.
- Inspect GitHub repo, Pages, Actions, workflow, and run state with `gh`.
- Trigger `workflow_dispatch` runs with `gh workflow run ...` after the workflow file exists on GitHub.
- Inspect workflow run status and logs with `gh run list`, `gh run view`, and related commands.
- Push branches or workflow commits only after the user explicitly asks to publish local changes.
- Prepare or execute the Pages-source cutover through `gh api` only after explicit approval, because it changes how the live site is deployed.

**What remains user-owned**

- Confirm before any command changes the live Pages source.
- Confirm any GitHub environment protection rules.
- Complete any GitHub browser approval prompt for first remote workflow runs.
- Handle custom domain/DNS changes. No DNS change is planned for the static-builder migration.

The planned safe sequence is still:

- build workflow locally,
- push it in non-deploy/dual-running mode,
- manually verify remote runs,
- then switch Pages to Actions artifact deployment only after the artifact passes checks.
