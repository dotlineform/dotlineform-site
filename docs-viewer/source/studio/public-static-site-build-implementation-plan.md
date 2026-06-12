---
doc_id: public-static-site-build-implementation-plan
title: Public Static Site Build Implementation Plan
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: in-progress
parent_id: site-request-public-static-site-build
---
# Public Static Site Build Implementation Plan

This is the tracker for implementing [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build).

The first phase is the audit and pre-migration work. Later phases are intentionally scoped at batch level until Batch 1 has produced the route, asset, config, and Jekyll-responsibility inventories that the implementation depends on.

### batch 1 summary

Batch 1 is complete. It fixed these implementation inputs:

- Static parity includes every canonical route in [Public Route Model](/docs/?scope=studio&doc=public-route-model); retired path-style routes, `/palette/`, `/docs/`, Studio, Admin, Analytics, logs, and local service routes stay excluded.
- The first builder uses Python render helpers, not file-based HTML snippets or a general template engine.
- Local build, local static preview, CI verification, and Pages artifact upload use `_public_site/` by default.
- The named build-plus-audit command for workflow validation is `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit`.
- GitHub Actions uses the request defaults: `pull_request` verifies only, `push` to `main` deploys after cutover, `workflow_dispatch` is enabled, no first-version path filters, `github-pages` environment, and Pages-only deploy permissions.
- The artifact audit must be allowlist-driven. Current Jekyll output leaks root/tooling files into `_site/`; the static artifact must exclude them.
- Public Docs Viewer route shells must use `docs-viewer-public-routes.json`, not the private/manage route registry.

### batch 2 summary

Batch 2 is complete. It introduced the static builder boundary and initial artifact contract:

- `public-site/config/public-site.json` owns the first public-site assembly config.
- `public-site/build/build_site.py` builds `_public_site/` and supports `--destination` plus `--audit`.
- `public_site_builder.builder` initializes guarded artifact output, writes `.nojekyll`, copies root browser/domain artifacts, and renders the initial non-Liquid `404.html`.
- `public_site_builder.audit` verifies required files, source-leak denylist patterns, and absence of Liquid tokens in generated HTML.
- `bin/public-site-build` now invokes the static builder.
- `bin/public-site-preview-static` builds and serves `_public_site/` as the static comparison target.
- `bin/public-site-preview` remains the Jekyll preview baseline for dual-running.

### baseline verification set

Run the checks that match the touched area.

- Docs-only edits: `git diff --check -- <changed-docs>`.
- Public Jekyll parity baseline while Jekyll is still active: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`.
- Public route browser checks when route shells, public runtime assets, or public Docs Viewer mounts change.
- Public build surface/source-leak checks after the static artifact builder exists.
- Python syntax/import checks for new `public-site/` builder modules.
- Docs Viewer payload rebuilds are not required for routine source-doc edits; let the docs watcher or explicit docs build own generated payload updates.

Codex sandbox note: local service, browser, and temporary localhost checks require elevated localhost permissions when the sandbox cannot reach loopback directly, even when the product code is healthy.

### general steer

- Treat [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) as the migration contract.
- Treat [Public Route Model](/docs/?scope=studio&doc=public-route-model) as the route contract.
- Start with inventories and decisions. Do not delete Jekyll-era files, wrappers, layouts, includes, or config until their replacement owner is named.
- Keep the static builder allowlist-driven. The generated artifact is the public boundary.
- Do not add compatibility aliases. A batch that requires one must record the owner, removal criterion, and reason before implementation.
- Later batches must be re-planned after Batch 1 closes, using the audit output instead of assumptions.

### dual-running and cutover policy

- Batches 1-4 must not change the production publishing source. Existing GitHub Pages Jekyll publishing remains the live path, and commits to `main` continue to update the live site through the current path.
- Local preview has its own dual-running period. The existing Jekyll preview remains the baseline, and a new static preview serves `_public_site/` as the static comparison target.
- Batch 2 introduces `bin/public-site-preview-static` as the temporary static preview command. The default `bin/public-site-preview` must keep its current Jekyll behavior until Batch 6 retargets it.
- During migration, local parity checks must be able to serve the Jekyll output and `_public_site/` on different ports and smoke the same public route list against both.
- Batch 5 owns the dual-running period: the static GitHub Actions workflow runs checks, manual builds, and non-deploy validation while the current Jekyll path remains live.
- The production cutover happens only when GitHub Pages is configured to deploy from the GitHub Actions Pages artifact instead of the current branch/Jekyll source, and the deploy workflow is enabled for `push` to `main`.
- After cutover, commits to `main` update the live site only when the Actions workflow succeeds and deploys the generated artifact.
- Batch 6 retargets `bin/public-site-preview` to the static build-and-serve path, then removes Ruby/Bundler tooling, `_config.yml`, `_layouts`, and `_includes` after a successful static Actions artifact deploy has been verified on the live site.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | title |
| --- | --- | --- |
| 1 | done | [Audit and Pre-Migration Decisions](/docs/?scope=studio&doc=public-static-site-build-batch-01-audit) |
| 2 | done | [Builder Skeleton and Artifact Contract](/docs/?scope=studio&doc=public-static-site-build-batch-02-builder-skeleton) |
| 3 | planned | [Public Route Rendering Parity](/docs/?scope=studio&doc=public-static-site-build-batch-03-route-parity) |
| 4 | planned | [Public Asset and Docs Viewer Artifact Assembly](/docs/?scope=studio&doc=public-static-site-build-batch-04-assets-docs-viewer) |
| 5 | planned | [Verification Gate and GitHub Pages Actions Deploy](/docs/?scope=studio&doc=public-static-site-build-batch-05-verification-deploy) |
| 6 | planned | [Jekyll Removal and Closeout](/docs/?scope=studio&doc=public-static-site-build-batch-06-jekyll-removal-closeout) |

The final batch includes the named closeout tasks from the tracker template: update docs, cleanup, verification, and close out.

### task: update docs

- Update command docs, local setup docs, public preview docs, deployment docs, and source organisation docs to describe the static builder, artifact boundary, local preview command, and GitHub Actions deployment path.
- Replace stale Ruby, Bundler, Jekyll, Liquid, `_config.yml`, `_layouts`, and `_includes` assumptions after the static builder is production-equivalent.

### task: cleanup

- Confirm removed Jekyll-era paths are not retained through import aliases, copied files, wrapper shims, or dual-build fallback logic.
- Confirm source-only directories are absent from the generated public artifact.

### task: verification

- Run the full verification gate defined in Batch 5 and repeat the closeout checks in Batch 6 after Jekyll removal.
- Record exact commands, smoke targets, artifact output path, and results in the final batch closeout.

### task: close out

- Close out the parent request and this tracker:
  - update statuses,
  - summarize replacement owners for former Jekyll responsibilities,
  - record verification results and generated payload status,
  - copy durable decisions into permanent owning docs,
  - note remaining risks or follow-on work before marking request docs done.
