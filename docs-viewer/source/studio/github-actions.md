---
doc_id: github-actions
title: GitHub Actions
added_date: "2026-06-12 15:35"
last_updated: "2026-06-13"
parent_id: dev-home
---
# GitHub Actions

**What can be done locally / in VS Code**

- Create `.github/workflows/public-site.yml`.
- Add the validation command the workflow will run.
- Run the same validation/smoke commands locally.
- Commit and push the workflow like any other file.
- Add `workflow_dispatch` so the workflow can be run manually from GitHub later.

Current local and remote state:

- `.github/workflows/public-site.yml` exists locally as the repo-owned public-site workflow.
- `gh` is installed at `/opt/homebrew/bin/gh`.
- `gh` is authenticated as `dotlineform` with `repo` and `workflow` scopes.
- `gh repo view` reports `dotlineform/dotlineform-site`, default branch `main`, public visibility, and admin viewer permission.
- GitHub Actions are enabled for the repo and allowed actions are set to `all`.
- The repo-owned `Public site` workflow is active on GitHub.
- GitHub Pages currently reports `build_type: workflow`, custom domain `www.dotlineform.com`, custom 404 enabled, and HTTPS enforced.
- Repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` is set to `true`.
- Production cutover run `27436556962` deployed Pages artifact `7600112973` to `https://www.dotlineform.com/`.

So from this session Codex can create and inspect workflow files locally, use `gh` to inspect repo/Pages/Actions state, trigger workflow runs, and inspect workflow logs. Production deployment now runs through the repo-owned `Public site` workflow.

**How `site/` is uploaded**

The static site directory is committed source. GitHub Actions validates `site/`, uploads that directory as the Pages artifact, then deploys that artifact through GitHub Pages.

The workflow shape is:

```yaml
- name: Validate static site
  run: python site-tools/site_validate.py

- name: Upload Pages artifact
  uses: actions/upload-pages-artifact@v5
  with:
    path: site

- name: Deploy to GitHub Pages
  uses: actions/deploy-pages@v5
```

The runner sequence is:

- Check out the repository.
- Run static-site validation.
- Package exactly `site/` with `actions/upload-pages-artifact`.
- Publish that artifact with `actions/deploy-pages`.

The local `site/` directory is the same tracked deploy root uploaded by the workflow.

**Deployment gate**

The repo-owned workflow validates `site/`, configures Pages, uploads the Pages artifact, and deploys when the deployment gate passes.

The deploy job runs only when all of these are true:

- The workflow event is a `push` or `workflow_dispatch`.
- The workflow ref is `refs/heads/main`.
- The repository variable `PUBLIC_SITE_PAGES_DEPLOY_ENABLED` is set to `true`.

**Scoped workflow triggers**

The workflow is scoped with `paths` filters on `pull_request` and `push` so unrelated commits to `main` do not rebuild or deploy the public site.

The filter includes the workflow file, `site/`, and `site-tools/`.

`workflow_dispatch` remains unfiltered so a manual run can still rebuild and deploy the public artifact when needed.

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

The site validator runs on GitHub's Actions runner during deployment validation. Validation and deployment failures are inspected in the GitHub Actions run logs first, then reproduced locally with the same validation command.

Use this local reproduction command for validation failures:

```bash
bin/site-validate
```

Debugging sequence:

- Inspect the GitHub Actions run log to identify the failing step.
- Classify the failure as validation, artifact upload, permissions, or Pages deployment.
- Reproduce validation failures locally with the same command.
- Fix repo-owned site files, validation config, or content issues locally.
- Push the fix and rerun the GitHub workflow.

Validation failures normally reproduce locally. GitHub-only failures include Pages permissions, Pages environment settings, artifact deployment plumbing, and runner-specific filesystem assumptions such as filename case sensitivity.

**What happened on GitHub**

- The workflow file exists on GitHub and runs as `Public site`.
- Manual runs use `workflow_dispatch`; GitHub supports running those from the Actions tab, GitHub CLI, or REST API.
- Pages custom workflow deployment is enabled for the repo's Pages source.
- The actual cutover was: GitHub Pages source changed from branch publishing to GitHub Actions artifact publishing.

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
- Inspect or adjust the Pages-source configuration through `gh api` only after explicit approval, because it changes how the live site is deployed.

**What remains user-owned**

- Confirm before any command changes the live Pages source.
- Confirm any GitHub environment protection rules.
- Complete any GitHub browser approval prompt for first remote workflow runs.
- Handle custom domain/DNS changes. No DNS change is planned for the static-site workflow migration.

The current production path is:

- validate `site/` in GitHub Actions,
- upload the Pages artifact,
- deploy through `actions/deploy-pages`.
