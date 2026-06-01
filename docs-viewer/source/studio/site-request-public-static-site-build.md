---
doc_id: site-request-public-static-site-build
title: Public Static Site Build Request
added_date: 2026-06-01
last_updated: 2026-06-01
ui_status: draft
parent_id: change-requests
viewable: true
---
# Public Static Site Build Request

Status:

- draft
- This request defines the migration spec for replacing the public Jekyll/Liquid build with a repo-owned static public-site build.
- Do not create an implementation task list until the open questions in this request have been answered or deliberately deferred.
- [Public Route Simplification Request](/docs/?scope=studio&doc=site-request-public-route-simplification) should be completed first so this migration can consume the resulting route contract.

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

## Proposed Defaults

Use these defaults unless the open questions produce a better migration spec:

- use GitHub Actions Pages deployment with `actions/upload-pages-artifact` and `actions/deploy-pages`
- write local build output to an ignored directory rather than tracked `_site`
- include `.nojekyll` at the root of the generated artifact
- implement the public builder in Python, reusing existing generated catalogue/docs/search payload contracts where possible
- keep `assets/js/`, `assets/css/`, public Docs Viewer runtime files, and public generated data paths stable
- replace Liquid layouts/includes with explicit templates or rendering helpers owned by the public-site builder
- preserve `bin/public-site-preview` and `bin/public-site-build` command names at first, but retarget them to the new builder
- use existing public build surface audits as migration verification rather than relying on visual spot checks alone
- make the first local preview implementation build once and serve the generated static output
- treat preview watch mode as a local convenience follow-up, not as the production build path

## Design Areas

The migration has two design surfaces: the public builder and the GitHub Actions deployment workflow.
Most decisions belong to the builder.
Actions should stay as thin deployment plumbing around that builder.

### Public Builder

The public builder is responsible for deciding what the public static site is.
It replaces Jekyll's implicit build decisions with explicit repo-owned behavior.

Design areas:

- input contract:
  define which source files, generated public payloads, config files, templates, runtime assets, and media artifacts the builder may read
- output contract:
  define the generated directory shape, including `.nojekyll`, `CNAME`, root files, route HTML, public assets, public generated data, and Docs Viewer public runtime payloads
- route generation:
  define how index routes and per-record routes are enumerated for works, series, moments, work details, catalogue search, Library, and Analysis
- template and component model:
  define how `_layouts/` and `_includes/` are replaced without carrying over broad Liquid semantics
- config model:
  define the public-site config replacement for URL, base path, media origins, thumbnail origins, Docs Viewer route/config paths, and public runtime flags
- copy and exclusion policy:
  use a positive publish allowlist where practical, so local source, Studio-only source, manage-only Docs Viewer source, logs, tests, and `var/` output are never copied by default
- generated data policy:
  define which public generated payloads must already exist before the build, which can be produced by the public builder, and which remain owned by existing catalogue/docs/search builders
- asset versioning:
  replace `site.time`-based Liquid cache keys with a deterministic build version or content/version policy
- local preview:
  define whether preview is static serving of generated output, a watch-and-rebuild command, or a separate preview wrapper around the same build output
- verification hooks:
  make public build surface audit, projection contract audit, route smoke checks, Docs Viewer public install checks, and stale Jekyll/Ruby reference scans part of the builder closeout path

### Local Preview And Watch Mode

The first replacement for Jekyll preview should be intentionally simple:

```text
bin/public-site-preview
  -> run the public builder once
  -> serve the generated static output directory
  -> print the local preview URL
```

This keeps local preview, CI build, and production artifact generation aligned.
The preview server should not become a separate source of public-site truth.

Watch mode can be added as a local iteration convenience after the build-once preview path is working:

```text
bin/public-site-preview --watch
  -> run the public builder once
  -> serve the generated static output directory
  -> watch selected public inputs
  -> copy CSS, JavaScript, and static asset changes through quickly
  -> rerun the public builder for templates, config, route inputs, and generated data changes
```

CSS and JavaScript iteration should not require a full conceptual rebuild when the changed file can be copied directly into the output tree.
If asset versioning uses generated query strings or content hashes, watch mode must either keep preview cache keys stable or rerender the route shells that reference the changed assets.

Watch mode is not a deployment mechanism.
The production GitHub Actions path should always run the normal one-shot builder and upload the resulting artifact.

### GitHub Actions

The GitHub Actions workflow is responsible for running the builder and publishing its output.
It should not contain public-site build rules that belong in the builder.

Design areas:

- trigger policy:
  decide whether the first workflow is manual-only, branch-scoped, deploy-on-main, or a staged combination while parity is being established
- environment setup:
  install only the Python and dependency set required by the public builder and verification checks
- build command:
  run the same public build command used by local preview/build
- verification gate:
  fail deployment when the agreed public build checks fail
- artifact upload:
  upload only the generated static output directory as the Pages artifact
- deployment:
  use GitHub Pages artifact deployment rather than branch-tracked generated output
- rollback:
  define whether rollback uses the previous successful Actions artifact, temporary re-enable of the old Jekyll Pages source, or another documented path
- permissions and environment:
  keep workflow permissions limited to the Pages deployment requirements and use the standard `github-pages` environment unless a repo-specific reason emerges

## Migration Spec Questions

Answer these before creating the implementation task list.

1. Builder ownership and path:
   Should the static builder live under a new public-site boundary, under `studio/services/`, or another existing owner?
   The path should make it clear that this is production public-site build logic, not a Studio local app service.

2. Template approach:
   Should HTML rendering use a small template engine, explicit Python string/component rendering, or a hybrid?
   The decision should account for maintainability of the current layout/include behavior without recreating Liquid semantics accidentally.

3. Config model:
   What replaces `_config.yml` as the public-site config source?
   The replacement must preserve public URLs, media origins, thumbnail origins, route flags, Docs Viewer public config paths, and exclusion policy in a machine-readable form.

4. Route generation source:
   Should public work, series, moment, and work-detail pages continue to use generated stub files as route inputs, or should the builder generate routes directly from public catalogue projections or canonical source through existing projection builders?
   The choice must preserve source/projection boundaries and avoid publishing Studio-only fields.

5. Local preview behavior:
   Should local preview be a static file server over the generated output, a Python preview command with rebuild support, or a watcher plus static server?
   The command should replace Jekyll preview without reintroducing app-service coupling.

6. GitHub Pages configuration:
   Should production deploy only through Actions artifacts, or should a fallback branch/folder publishing source remain documented?
   The preferred answer is Actions-only unless there is an operational reason to keep a fallback.

7. Output directory:
   What ignored local output path should replace `_site` for the new public build?
   The path should avoid confusion with Jekyll while remaining obvious to tests and preview commands.

8. Public route parity:
   Which routes are required for the first production-equivalent cut after the route simplification request?
   The static-builder migration should follow the simplified canonical route model rather than carrying assumptions from the pre-simplification route surface.

9. Jekyll removal timing:
   Should Jekyll files be removed in the same implementation request after parity verification, or in a final cleanup request?
   Candidate removals include `Gemfile`, `Gemfile.lock`, `.ruby-version`, Jekyll-specific `_config.yml` usage, `_layouts/`, `_includes/`, and Jekyll collection stubs.

10. Verification gate:
    What is the minimum automated verification set before switching production deploy?
    Expected checks include static build success, public build surface audit, projection contract audit against the built output, focused browser smoke tests for public catalogue routes, public Docs Viewer `/library/` and `/analysis/`, and source scans for stale Jekyll/Ruby command paths.

11. Custom domain artifacts:
    Where should `CNAME`, favicon/site manifest files, and other root-level publishing artifacts be sourced from and copied into the generated artifact?

12. Deployment rollback:
    What is the fallback plan if the first Actions artifact deploy fails after Jekyll is disabled?
    The migration should define whether rollback means re-enabling the old Pages/Jekyll source temporarily or redeploying a previous successful Actions artifact.

## Acceptance Criteria For The Spec

- the replacement for each Jekyll responsibility is named before implementation begins
- build inputs, generated output, and deploy artifact boundaries are explicit
- public source/projection leak protections remain part of the plan
- local preview and CI deploy use the same build path
- the migration does not require tracking generated site output on `main`
- the task list can be split into small, verifiable slices after the open questions are resolved
