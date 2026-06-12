---
doc_id: github-actions
title: GitHub Actions
added_date: "2026-06-12 15:35"
last_updated: "2026-06-12 15:47"
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

- `.github/` exists locally but does not yet contain repo-owned workflow files.
- `gh` is installed at `/opt/homebrew/bin/gh`.
- `gh` is authenticated as `dotlineform` with `repo` and `workflow` scopes.
- `gh repo view` reports `dotlineform/dotlineform-site`, default branch `main`, public visibility, and admin viewer permission.
- GitHub Actions are enabled for the repo and allowed actions are set to `all`.
- The only workflow currently listed is GitHub's `pages-build-deployment`, which belongs to the current Pages path rather than a repo-owned workflow file.
- GitHub Pages currently reports `build_type: legacy`, source `main /`, custom domain `www.dotlineform.com`, custom 404 enabled, and HTTPS enforced.

So from this session Codex can create and inspect workflow files locally, use `gh` to inspect repo/Pages/Actions state, and after a workflow has been pushed, trigger and inspect workflow runs. Production cutover remains an explicit approval step because it changes the live deployment source.

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
- Push branches or workflow commits if explicitly asked to publish local changes.
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
