---
doc_id: site-request-public-static-site-build
title: Public Static Site Build Request
added_date: 2026-06-01
last_updated: 2026-06-02
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Public Static Site Build Request

Status:

- in-progress
- This request defines the migration spec for replacing the public Jekyll/Liquid build with a repo-owned static public-site build.
- The migration decisions have been resolved and can be used to create an implementation task list.
- [Public Route Simplification Request](/docs/?scope=studio&doc=site-request-public-route-simplification) has been completed first so this migration can consume the resulting route contract.

## Task Tracker

Use [Public Static Site Build Tasks](/docs/?scope=studio&doc=site-request-public-static-site-build-tasks) for the implementation sequence, task status, and verification checklist.

## Summary

Replace the public site's implicit GitHub Pages Jekyll build with an explicit static-site build owned by this repository.

The target keeps GitHub Pages as the public host, but changes how the published files are produced:

```text
commit to main
  -> GitHub Actions workflow
  -> repo-owned public-site builder
  -> untracked static output directory
  -> GitHub Pages artifact upload
  -> GitHub Pages deploy
```

The output should not be tracked in the main branch.
GitHub Pages should deploy a generated artifact with `.nojekyll` at the artifact root, rather than running Jekyll against the source tree.

## Context

[Rubyless App Runtimes Request](/docs/?scope=studio&doc=site-request-rubyless-app-runtimes) removed Ruby/Jekyll from app runtimes and app-facing builders.
It intentionally left Jekyll as the manual public-site preview/build layer until the public site itself could be replaced.

This request should not redesign public routes.
It should consume the route contract produced by [Public Route Simplification Request](/docs/?scope=studio&doc=site-request-public-route-simplification).

The current public build is still Jekyll-owned:

- GitHub Pages runs an implicit Jekyll build when repository content changes.
- Local public preview/build wrappers call `bundle exec jekyll serve` and `bundle exec jekyll build`.
- `_config.yml` defines site values, collections, permalinks, defaults, and publish exclusions.
- `_layouts/` and `_includes/` contain Liquid templates for public routes.
- `_works/`, `_series/`, `_moments/`, and `_work_details/` provide Jekyll collection stubs for route generation.
- public route pages such as `/series/`, `/recent/`, `/library/`, `/analysis/`, and `/catalogue/search/` still use Liquid for shell rendering and config injection.

GitHub Pages without Jekyll publishes static files as-is from a configured source or Actions artifact.
Because the current source tree is not the final static site, adding `.nojekyll` to the existing source root is not sufficient.
The missing replacement is a deterministic static builder that produces the deployable HTML, assets, and public runtime payload surface that Jekyll currently emits.

## Target Architecture

```text
Source and generated public inputs
  - public route templates or components
  - public CSS/JS/assets
  - generated catalogue JSON and docs/search payloads
  - public-site config

Repo-owned public builder
  - expands public routes
  - renders HTML shells
  - copies publishable assets and generated payloads
  - excludes local, Studio-only, and manage-only source
  - writes an untracked static output directory with .nojekyll

GitHub Actions
  - runs the builder in CI
  - uploads the static output as a Pages artifact
  - deploys to GitHub Pages

GitHub Pages
  - hosts the static artifact
  - does not run Jekyll or Liquid
```

Ruby, Bundler, Jekyll, Liquid, `Gemfile`, `Gemfile.lock`, and `.ruby-version` should be removable after the replacement builder and deployment workflow are verified.

## Goals

- replace the implicit GitHub Pages Jekyll build with an explicit GitHub Actions artifact deployment
- keep public site output untracked on `main`
- generate public route HTML without Jekyll collections or Liquid templates
- preserve the current public route surface, canonical URLs, custom domain behavior, and static asset paths unless deliberately changed
- start from the simplified route model once the predecessor route request has defined it
- keep public read-only Docs Viewer installs for `/library/` and `/analysis/`
- keep generated catalogue, search, docs, media, CSS, and JavaScript payload ownership explicit
- make local public preview/build use the same builder path as CI
- keep public build surface checks and source-leak checks in the verification path
- retire Jekyll/Ruby docs and commands only after the static builder is the production path

## Non-Goals

- changing the public site host away from GitHub Pages
- tracking the full generated site output on `main`
- replacing Studio, Analytics, Docs Viewer management, or UI Catalogue app runtimes
- changing catalogue source schemas just to remove Jekyll
- changing public visual design or route behavior unless required by the build migration
- designing the simplified public route model itself; that belongs in a separate predecessor request
- publishing local `/docs/` management routes, Studio routes, Studio docs payloads, canonical source data, logs, or `var/` output
- adding a server-side runtime to production GitHub Pages

## Migration Decisions

### Builder Ownership

The static builder should live under a new top-level `public-site/` boundary.
This keeps production public-site build logic separate from Studio local app services and makes the Jekyll replacement visible as its own repo-owned domain.

Initial shape:

```text
public-site/
  build/
    build_site.py
    public_site_builder/
      config.py
      routes.py
      render.py
      copy.py
      audit.py
  config/
    public-site.json
  templates/
  tests/
```

`bin/public-site-build` and `bin/public-site-preview` should be preserved at first, but retargeted to `public-site/build/build_site.py`.
Avoid placing the builder under `studio/services/`, `docs-viewer/`, or a generic `builder/` directory because it owns the whole public artifact: route HTML, public assets, generated public data, public Docs Viewer installs, site-root publishing artifacts, `.nojekyll`, and deployment surface checks.

### Rendering Model

HTML rendering should use explicit Python rendering helpers/components rather than a general template engine.
The public site has a small number of stable page shells, and the migration goal is to replace Jekyll/Liquid without recreating broad template semantics.

Rendering should keep shared layout pieces in focused Python helpers for head metadata, navigation, asset includes, footer, Docs Viewer shell mounting, and catalogue route shells.
Page renderers should pass structured data into those helpers and return complete HTML files.
If file-based HTML snippets are useful, keep them narrow and static, not as a new general-purpose template language.

This keeps the build dependency surface small, makes escaping and URL generation explicit, and avoids carrying over Liquid-era indirection for pages that are not expected to change frequently.

### Config Model

`public-site/config/public-site.json` should replace the public-site parts of `_config.yml`.
This file owns production public-site build and deploy assembly config, not every domain config in the repo.

`public-site.json` should define:

- canonical site URL and base URL behavior
- custom domain and artifact-root expectations such as `CNAME`
- media and thumbnail origins
- public route flags
- deterministic asset/versioning policy
- static copy allowlists and exclusions
- Docs Viewer public mount and config paths for `/library/` and `/analysis/`

Catalogue projections, Docs Viewer scope config, search config, source schemas, and other domain-owned configs should stay with their current owners.
The public-site builder may read those existing configs and generated outputs as inputs, but `public-site.json` should define how they are assembled into the deployable public artifact.

### Route Generation

Routes should be generated directly from the simplified public route contract in [Public Route Simplification Request](/docs/?scope=studio&doc=site-request-public-route-simplification) and from public catalogue projections or generated public data.
Jekyll collection stubs are not static-builder inputs.

The builder should emit fixed route shells for the canonical public routes, including `/series/`, `/works/`, `/work-details/`, `/moments/`, `/catalogue/search/`, `/library/`, and `/analysis/`.
Individual moment pages may remain path routes such as `/moments/a-doll-story/`, but they should be enumerated from public moment records rather than from `_moments` stubs.

Remaining `_works/`, `_series/`, `_work_details/`, and related Jekyll collection outputs are build-layer artifacts only while Jekyll remains the public build layer.
They are not durable route contracts and should be removable once the static builder produces the fixed shells and individual moment pages directly.

### Route Parity

The first production-equivalent static builder should provide parity for all public routes in the simplified route contract.
The post-simplification public route surface is small enough that the first production-equivalent static builder should not stage only a subset.

Required parity includes the public root and static pages, fixed catalogue shells, query-state catalogue routes, individual moment pages, catalogue search, public Docs Viewer installs for Library and Analysis, site-root publishing artifacts, and `404.html`.
The route list should be derived from [Public Route Simplification Request](/docs/?scope=studio&doc=site-request-public-route-simplification) plus current top-level public pages and site-root publishing artifacts that remain intentionally public.
`/palette/` is excluded from static public-site parity; palette inspection is owned by the UI Catalogue app at `/ui-catalogue/palette/`.

If a current public route is deliberately excluded, the implementation task list must name it and explain why before production deploy switches to the static builder.

### Output Directory

Local static public-site output should be written to ignored `_public_site/`.
This keeps the generated output visibly analogous to `_site` while avoiding Jekyll-specific naming.

The builder's default local destination should be `_public_site/`, and `bin/public-site-build` plus `bin/public-site-preview` should use that path unless an explicit destination is provided.
CI may use `_public_site/` or an isolated temporary path, but it should upload only the generated output directory as the Pages artifact.
Do not use `_site/` for the replacement builder because that path remains associated with Jekyll and can confuse parity checks during migration.

### Artifact Copy Policy

Current site-root source files in `dotlineform-site/` should remain the source of truth for the first static-builder implementation, then be copied into the generated artifact root through an explicit allowlist.
This preserves current custom-domain and browser metadata behavior without inventing a new asset ownership move during the build migration.

The allowlist should include current `dotlineform-site/` publishing artifacts such as `CNAME`, favicon files, `apple-touch-icon` files, `safari-pinned-tab.svg`, `site.webmanifest`, and `404.html` where applicable.
The builder should not copy arbitrary site-root files by default.
If these artifacts later move under `public-site/`, that should be a separate ownership cleanup after the static-builder deployment path is verified.

### Local Preview

Local preview should use a Python preview command that runs the public builder once, serves the generated static output directory, and prints the local preview URL.
`bin/public-site-preview` should remain the operator-facing wrapper and dispatch to the public-site preview/build implementation.

The first implementation should not include watch mode.
CSS/JavaScript fast-copy watching, template/data rebuild watching, and any richer preview rebuild loop should be deferred until the one-shot build-and-serve path is production-equivalent.
The preview server should remain a convenience wrapper over generated static output, not a separate source of public-site behavior.

Watch mode is not a deployment mechanism.
The production GitHub Actions path should always run the normal one-shot builder and upload the resulting artifact.

### GitHub Actions Deployment

Production should deploy through GitHub Actions Pages artifacts only.
Do not keep a branch/folder Pages publishing source as an active fallback path.

The workflow should build the public static output, verify it, upload only the generated output directory with `.nojekyll` at the artifact root, and deploy that artifact through GitHub Pages.
Actions should stay as thin deployment plumbing around the builder and should not contain public-site build rules that belong in the builder.

Trigger policy:

- `pull_request`:
  build and run the full verification gate, but do not deploy
- `push` to `main`:
  build, run the full verification gate, upload the Pages artifact, and deploy
- `workflow_dispatch`:
  allow a manual rebuild/redeploy from `main`

Avoid path filters for the first production workflow because the public artifact depends on templates, assets, generated data, Docs Viewer payloads, catalogue payloads, config, site-root publishing artifacts, and workflow code.
Once the builder emits stable input diagnostics, path filters can be reconsidered as an optimization.
Use workflow concurrency for Pages deploys so newer `main` deploys cancel older in-flight deploys.

The workflow should install only the Python and dependency set required by the public builder and verification checks.
Workflow permissions should stay limited to the Pages deployment requirements and use the standard `github-pages` environment unless a repo-specific reason emerges.

### Verification Gate

All listed checks are required before switching production deployment to the static builder.
The implementation should not treat these as optional spot checks.

The deployment gate should include:

- static public-site build success
- public build surface audit against `_public_site/` or the selected build output
- projection contract audit against the built output
- focused browser smoke tests for all simplified public catalogue routes
- focused browser smoke tests for public Docs Viewer `/library/` and `/analysis/`
- source and docs scans for stale Jekyll/Ruby command paths, Liquid assumptions, and retired collection-route dependencies
- artifact-root checks for `.nojekyll`, `CNAME`, favicon/site manifest files, and `404.html`
- production workflow dry run or equivalent CI validation that proves the Actions artifact contains only the intended static output

The implementation task list should name the exact commands and smoke targets.
Switching production deploy is not complete until the verification gate passes and the closeout records the results.

### Jekyll Removal

Jekyll/Ruby build artifacts should be removed as part of the static public-site builder implementation after parity verification passes.
Do not defer Jekyll removal to a separate cleanup request unless implementation discovers a specific blocker.

The implementation should remove or retire `Gemfile`, `Gemfile.lock`, `.ruby-version`, Jekyll-specific `_config.yml` usage, `_layouts/`, `_includes/`, Jekyll collection stubs, and wrapper logic that invokes Bundler or Jekyll.
Documentation and verification commands should be updated in the same change so the repo no longer presents Ruby/Jekyll as the public-site build path.
Any retained file or command with Jekyll-era naming must have an explicit owner and removal reason in the implementation closeout.

### Deployment Failure Policy

The fallback plan is to fix the static builder, workflow, or generated artifact problem and redeploy a corrected Actions artifact.
Do not maintain or document a parallel Jekyll/branch publishing fallback as part of normal operations.

Before Jekyll removal and production deployment switch, the verification gate should reduce the chance of a failed artifact deploy.
If deployment still fails, treat it as an implementation defect: inspect the failed workflow/artifact, correct the builder or workflow, rerun the required checks, and deploy again.
A previous successful Actions artifact may be redeployed only if that path is available through GitHub Pages and does not require reintroducing Jekyll.

## Acceptance Criteria For The Spec

- the replacement for each Jekyll responsibility is named before implementation begins
- build inputs, generated output, and deploy artifact boundaries are explicit
- public source/projection leak protections remain part of the plan
- local preview and CI deploy use the same build path
- the migration does not require tracking generated site output on `main`
- the task list can be split into small, verifiable slices from the resolved migration decisions
