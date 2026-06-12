---
doc_id: public-static-site-build-batch-01-audit
title: Public Static Site Build Batch 1 Audit and Pre-Migration Decisions
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: done
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 1 Audit and Pre-Migration Decisions

This is the delivery specification for Batch 1 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: produce the inventories and decisions needed before static-builder implementation begins.

## Steer for these tasks

- This batch must resolve the flexible wording called out in [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build).
- No production deploy path changes belong in this batch.
- Do not delete active Jekyll-era files in this batch. Deletion of dead files requires audit evidence, a named file list, and proportional verification.
- The output must be compact decision/audit records consumed directly by later batches.
- The next batch must use this batch's audit output to refine builder module boundaries, copy allowlists, and verification commands.

## Deliverables

- A pre-implementation decision record in this batch document.
- A public-route inventory tied to [Public Route Model](/docs/?scope=studio&doc=public-route-model).
- A Jekyll responsibility inventory covering `_config.yml`, `_layouts/`, `_includes/`, Liquid route pages, wrappers, and GitHub Pages assumptions.
- A public artifact inventory covering route HTML outputs, public assets, generated public data, public Docs Viewer runtime/config/static files, root artifacts, and files that must never publish.
- A verification and source-leak audit seed list for later automation.
- A named list of small cleanup edits for dead files or stale docs. Batch 1 records this list but does not perform the cleanup.

## Pre-Implementation Decisions

These decisions are now fixed inputs for Batches 2-6.

| topic | decision | owner for implementation |
| --- | --- | --- |
| Route parity exclusions | No current route in [Public Route Model](/docs/?scope=studio&doc=public-route-model) is excluded from static-builder parity. `/palette/`, path-style work/series/work-detail/moment routes, `/docs/`, Studio, Admin, Analytics, logs, and local service routes remain excluded. | Batch 3 route renderers and Batch 5 smokes. |
| Rendering model | Do not use file-based HTML snippets in the first production-equivalent builder. Render route HTML through explicit Python helpers for layout, head metadata, navigation, footer, Docs Viewer shell, static pages, and catalogue shells. | Batch 2 builder skeleton and Batch 3 render helpers. |
| Output path policy | Local build, local static preview, CI verification, and Pages artifact upload default to `_public_site/`. A caller-supplied destination is an explicit override. Do not use `_site/` for the static builder. | Batch 2 CLI and preview wrapper; Batch 5 workflow. |
| Artifact-content validation command | Implement and use `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit` as the named build-plus-audit command. The workflow must run this command before uploading the Pages artifact. | Batch 2 CLI, Batch 4 audit rules, Batch 5 workflow. |
| GitHub Actions defaults | Keep the request defaults: `pull_request` builds and verifies without deploy, `push` to `main` builds/verifies/uploads/deploys after cutover, `workflow_dispatch` supports manual rebuild/redeploy, no first-version path filters, `github-pages` environment, and Pages-only deploy permissions. No repo-specific deviation is currently required. | Batch 5 workflow. |
| Cutover boundary | Existing GitHub Pages legacy branch/Jekyll publishing remains live until Batch 5 records a successful static artifact gate and explicitly changes the Pages source to Actions artifact deployment. | Batch 5. |

## Initial Audit Findings

### Public Route Inventory

The current public route files are:

| source file | route | classification | static-builder owner |
| --- | --- | --- | --- |
| `index.md` | `/` | static redirect/home shell | `routes.render_home_redirect()` |
| `about.md` plus `_layouts/about.html` | `/about/` | static page with remote home media config | `routes.render_about()` plus shared layout helper |
| `recent/index.md` | `/recent/` | catalogue shell driven by generated public data | `routes.render_recent()` |
| `series/index.md` | `/series/` and query states | catalogue shell | `routes.render_series()` |
| `works/index.md` | `/works/` and query states | catalogue work shell | `routes.render_works()` |
| `work-details/index.md` | `/work-details/` and query states | catalogue detail shell | `routes.render_work_details()` |
| `moments/index.md` | `/moments/` and query states | moment shell | `routes.render_moments()` |
| `catalogue/search/index.md` | `/catalogue/search/` | public catalogue search shell | `routes.render_catalogue_search()` |
| `library/index.md` | `/library/` | public read-only Docs Viewer shell | `routes.render_docs_viewer_route("library")` |
| `analysis/index.md` | `/analysis/` | public read-only Docs Viewer shell | `routes.render_docs_viewer_route("analysis")` |
| `404.html` | `/404.html` | root publishing artifact and error page | `routes.render_404()` |

The inventory matches [Public Route Model](/docs/?scope=studio&doc=public-route-model). Retired path-style routes and `/palette/` remain deliberately excluded.

### Jekyll Responsibility Inventory

| current item | current responsibility | replacement owner |
| --- | --- | --- |
| `_layouts/default.html` | HTML document shell, title/description, favicons, main CSS, body class, nav, footer, global scripts, cache-busting timestamp | `public_site_builder.render.render_page()`, `render_head()`, `render_nav()`, `render_footer()`, and deterministic asset version helper |
| `_layouts/about.html` | About page hero/image/link rendering from front matter and media config | `routes.render_about()` with structured page data |
| `_includes/nav_item.html` | Active/current nav item markup | `render_nav_item()` |
| `_includes/docs_viewer_readonly_route.html` | Read-only public Docs Viewer route wrapper | `render_docs_viewer_route()` |
| `_includes/docs_viewer_shell.html` | Docs Viewer CSS link, mount attributes, search labels, and public JS entrypoint | `render_docs_viewer_shell()` |
| `_includes/work_index_item.html` | Legacy work-card include; no active route usage found | cleanup candidate; Batch 3 must confirm active usage before adding a replacement |
| `_includes/artist_line.html` | Legacy artist metadata include; no active route usage found | cleanup candidate; Batch 3 must confirm active usage before adding a replacement |
| Liquid route pages | Page-level data injection, URL generation, `site.data.pipeline` access, cache-busted asset links | Route-specific Python renderers plus JSON/config readers |
| `bin/public-site-build` | Jekyll build wrapper | Retarget in Batch 2 to static builder |
| `bin/public-site-preview` | Jekyll serve wrapper | Keep as Jekyll preview baseline through Batch 5; retarget in Batch 6 |

### `_config.yml` Ownership Inventory

| key or section | classification | replacement owner |
| --- | --- | --- |
| `title`, `url`, `baseurl`, `live_url`, `timezone` | public-site config | `public-site/config/public-site.json` |
| `docs_viewer_config_url`, `docs_viewer_route_config_url`, Docs Viewer route flags | public Docs Viewer assembly config | `public-site/config/public-site.json` plus Docs Viewer public config files |
| `thumb_base`, `thumb_works`, `thumb_work_details`, `thumb_moments` | public media/thumb path config | `public-site/config/public-site.json` |
| `media_base`, `media_image_works`, `media_files_works`, `media_image_work_details`, `media_image_moments` | public remote media/file path config | `public-site/config/public-site.json` |
| `home_media_base`, `home_media_prefix` | public about/home media config | `public-site/config/public-site.json` |
| `enable_details_hash_scroll`, `public_runtime_text` | public runtime config/text | `public-site/config/public-site.json` or route-renderer data attributes |
| `defaults` | Jekyll-only default layout assignment | obsolete after route renderers own page layout |
| `exclude` | Jekyll-only source hiding | replace with positive copy allowlists and artifact audit denylist |

The static builder must not answer the old question of whether `_config.yml exclude` can name only a root directory. The artifact boundary replaces Jekyll excludes with allowlisted copies.

### Public Docs Viewer Inventory

Public Docs Viewer routes must remain deployable from `/docs-viewer/...` and `/assets/data/...`.

Allowlist:

- `docs-viewer/runtime/js/docs-viewer-public.js` and the runtime modules reachable from that entrypoint.
- `docs-viewer/static/css/docs-viewer.css`, `docs-viewer/static/css/docs-viewer-reports.css`, and any public CSS dependency required by the public runtime.
- `docs-viewer/config/defaults/docs-viewer-public-config.json`.
- `docs-viewer/config/routes/docs-viewer-public-routes.json`.
- `docs-viewer/config/ui-text/public.json`.
- Public docs payloads for `analysis` and `library`: `assets/data/docs/scopes/{analysis,library}/...`.
- Public docs search payloads: `assets/data/search/{analysis,library}/index.json`.

Denylist:

- `docs-viewer/config/defaults/docs-viewer-config.json`.
- `docs-viewer/config/defaults/docs-viewer-service.json`.
- `docs-viewer/config/routes/docs-viewer-routes.json`.
- `docs-viewer/config/scopes/`, `docs-viewer/config/schema/`, and `docs-viewer/config/reports/`.
- `docs-viewer/source/`, `docs-viewer/services/`, `docs-viewer/build/`, `docs-viewer/bin/`, `docs-viewer/shell/`, `docs-viewer/tests/`, and management runtime modules.
- `docs-viewer/runtime/js/reports/`, because the current public route config has no public hosted report views.
- Generated `studio` and `tmp` docs/search payloads.

Current note: `_config.yml` defaults `docs_viewer_route_config_url` to `/docs-viewer/config/routes/docs-viewer-routes.json`, while the deployable public artifact currently contains `docs-viewer-public-routes.json`. Batch 3 must render `/library/` and `/analysis/` with the public route config path.

### Public Catalogue, Search, and Media Inventory

Copy or reference these public inputs:

- Catalogue index payloads: `assets/data/series_index.json`, `assets/data/works_index.json`, `assets/data/moments_index.json`, and `assets/data/recent_index.json`.
- Per-record payloads: `assets/series/index/*.json`, `assets/works/index/*.json`, and `assets/moments/index/*.json`.
- Public search payloads: `assets/data/search/catalogue/index.json`, `assets/data/search/library/index.json`, `assets/data/search/analysis/index.json`, and `assets/data/search/policy.json`.
- Public JS: `assets/js/public-catalogue-runtime.js`, `assets/js/work.js`, `assets/js/moment.js`, `assets/js/swipe-nav.js`, `assets/js/catalogue-search.js`, `assets/js/search/*.js`, `assets/js/site-nav.js`, and `assets/js/theme-toggle.js`.
- Public CSS: `assets/css/main.css`.
- Public thumbnails/images: `assets/works/img/`, `assets/work_details/img/`, `assets/moments/img/`, `assets/series/index/`, and `assets/site/dotlineform.png`.
- Remote media and files remain referenced through configured origins, including `https://media.dotlineform.com/works/files` for work downloads such as `nerve.pdf`.
- `_data/pipeline.json` is a builder input for path decisions and provenance, not a public artifact to copy wholesale.

### Site-Root Artifact Inventory

Root artifact allowlist:

- `CNAME`
- `favicon.ico`
- `favicon-16x16.png`
- `favicon-32x32.png`
- `apple-touch-icon.png`
- `apple-touch-icon-precomposed.png`
- `android-chrome-192x192.png`
- `android-chrome-512x512.png`
- `safari-pinned-tab.svg`
- `site.webmanifest`
- `404.html` as rendered output, not raw Liquid
- `.nojekyll` generated at artifact root

Deliberately exclude root source/tooling files such as `README.md`, `AGENTS.md`, `LICENSE`, `Gemfile`, `Gemfile.lock`, `.ruby-version`, `requirements.txt`, and local build scripts.

### Source-Leak Audit Seed List

The current `_site/` build includes files that should not be in the static artifact, including `Gemfile`, `Gemfile.lock`, `README.md`, `AGENTS.md`, `requirements.txt`, `bin/public-site-build`, `bin/public-site-preview`, `bin/local-*`, `data/*.xlsx`, and `.DS_Store` files. Batch 4 must turn this into an artifact audit.

Initial denylist patterns:

- `.git/`, `.github/`, `.codex/`, `.devcontainer/`, `.vscode/`, `.pytest_cache/`, `.pycache/`, `__pycache__/`, `.bundle/`, `node_modules/`, `vendor/`, `_site/`, `_public_site/`, `var/`, `logs/`
- `Gemfile`, `Gemfile.lock`, `.ruby-version`, `_config.yml`, `_layouts/`, `_includes/`
- `README.md`, `AGENTS.md`, `LICENSE`, `requirements.txt`, `*.xlsx`, `*.xls`, `*.pyc`, `.DS_Store`
- `admin-app/`, `analytics-app/`, `studio/`, `data/`, `data-sharing/`
- `docs-viewer/source/`, `docs-viewer/services/`, `docs-viewer/build/`, `docs-viewer/bin/`, `docs-viewer/shell/`, `docs-viewer/tests/`
- `docs-viewer/runtime/js/docs-html-import*.js`, `docs-viewer/runtime/js/docs-viewer-manage.js`, and `docs-viewer/runtime/js/docs-viewer-management*.js`
- `docs-viewer/config/defaults/docs-viewer-config.json`, `docs-viewer/config/defaults/docs-viewer-service.json`, `docs-viewer/config/routes/docs-viewer-routes.json`, private scopes/schema/reports config, and generated `studio`/`tmp` docs/search payloads

### GitHub Actions and Pages State

Current state from the local `gh` setup:

- `.github/` exists locally and currently has no workflow files.
- `gh` is installed at `/opt/homebrew/bin/gh` and authenticated as `dotlineform` with `repo` and `workflow` scopes.
- The repo is `dotlineform/dotlineform-site`; the default branch is `main`; viewer permission is admin.
- GitHub Actions are enabled for the repo.
- The only workflow currently listed is GitHub's `pages-build-deployment`, which belongs to the current legacy Pages path.
- GitHub Pages currently reports legacy branch publishing from `main /`, custom domain `www.dotlineform.com`, HTTPS enforced, and custom 404 enabled.

Batch 5 can therefore create a repo-owned workflow locally, push it when approved, trigger `workflow_dispatch` runs after it exists on GitHub, inspect runs/logs with `gh`, and perform the Pages source cutover only after explicit approval.

### Cleanup Candidates

Record these for Batch 6 or a named pre-closeout cleanup after replacement owners are verified:

- Batch 6 removes `_includes/work_index_item.html` after Batch 3 confirms it remains unused.
- Batch 6 removes `_includes/artist_line.html` after Batch 3 confirms it remains unused.
- Remove or retarget `bin/public-site-build` and `bin/public-site-preview` after the static builder and preview are verified.
- Remove `Gemfile`, `Gemfile.lock`, `.ruby-version`, `_config.yml`, `_layouts/`, and remaining `_includes/` after Batch 5 records a live static artifact deploy.
- Rewrite docs that still present Ruby, Bundler, Jekyll, Liquid, `_config.yml`, `_layouts`, or `_includes` as the public build path.

## Implementation and policy guidance

- Start from current code and generated public inputs, not historical request text.
- Record decisions before implementation when current docs and source scans provide enough evidence.
- Record audit findings before implementation when the answer depends on current file usage.
- Keep GitHub Pages as the host and GitHub Actions artifact deployment as the production direction.
- Keep generated public output untracked on `main`.
- Do not introduce a parallel Jekyll fallback path.

## Proposed verification set

- `git diff --check -- docs-viewer/source/studio/public-static-site-build-implementation-plan.md docs-viewer/source/studio/public-static-site-build-batch-*.md`
- Focused scans used by the audit, recorded in the completed verification section.
- Public Jekyll build is required when this batch changes active public route templates, includes, layouts, or config.

## Tasks

### Batch 1: Audit and Pre-Migration Decisions

| ID | status | action |
| --- | --- | --- |
| 1.1 | done | Inventory all public route pages and classify each route as static page, catalogue shell, Docs Viewer shell, search shell, root artifact, or intentionally excluded route. |
| 1.2 | done | Compare the route inventory with [Public Route Model](/docs/?scope=studio&doc=public-route-model), and record any route exclusions or gaps that need a pre-implementation decision. |
| 1.3 | done | Inventory `_layouts/`, `_includes/`, and Liquid-rendered public route pages; name the static-builder render helper or component that will replace each item. |
| 1.4 | done | Inventory public-site values currently read from `_config.yml`; classify each as public-site config, domain-owned config, generated-data config, or obsolete Jekyll-only setting. |
| 1.5 | done | Inventory public Docs Viewer files that must remain deployable from `/docs-viewer/...`, including runtime modules, static CSS, public defaults, public route config, and generated public docs/search payloads. |
| 1.6 | done | Inventory public catalogue/search/moment/work payloads and media path config that the static builder must copy or reference. |
| 1.7 | done | Inventory site-root publishing artifacts, including `CNAME`, favicon files, `apple-touch-icon` files, `safari-pinned-tab.svg`, `site.webmanifest`, and `404.html`; record missing or deliberately excluded artifacts explicitly. |
| 1.8 | done | Inventory source-only paths that must never appear in the public artifact, including Studio, Analytics app internals, Docs Viewer services/source/build internals, logs, local config, caches, and generated private docs payloads. |
| 1.9 | done | Decide whether file-based HTML snippets are allowed in the builder; record the Python-helper-only decision for the first production-equivalent builder. |
| 1.10 | done | Decide whether CI uses `_public_site/` or an isolated temporary output path; record the exact path policy for local build, preview, CI verification, and Pages artifact upload. |
| 1.11 | done | Name the exact artifact-content validation command or audit script expected for the GitHub Actions workflow. |
| 1.12 | done | Decide whether workflow permissions, Pages environment, deploy triggers, or concurrency differ from the request defaults; record each deviation or confirm no deviations. |
| 1.13 | done | Identify stale Jekyll/Ruby/Liquid references in source docs, scripts, workflow files, and operator commands that need rewrite during closeout. |
| 1.14 | done | Convert audit findings into follow-on task updates for Batches 2-6, adding detail where the current plan is intentionally coarse. |

## completed verification

- `find`/`rg` inventories for public route files, `_layouts/`, `_includes/`, root files, root directories, `assets/`, `docs-viewer/`, `_site/docs-viewer/`, and generated docs/search payloads.
- `rg -n "site\\.|page\\.|include\\.|relative_url|absolute_url|site\\.data" _layouts _includes index.md about.md 404.html series works work-details moments recent catalogue/search library analysis --glob '*.{html,md}'`
- `find _site -maxdepth 3 -type f | rg -n "(^|/)(AGENTS|README|Gemfile|requirements|bin/|data/|\\.DS_Store|\\.git|_config|docs-viewer/(build|services|source|tests|shell)|studio/|admin-app/|analytics-app/|var/|logs/)"`
- `$HOME/miniconda3/bin/python3` JSON inspections for `_data/pipeline.json`, public Docs Viewer config/route config, work `00008`, and public search/catalogue payload shape.
- `command -v gh` and `gh auth status` confirmed local GitHub CLI availability and authentication.

## follow-on tasks

- Batch 2 must implement the decided `_public_site/` output policy, `.nojekyll`, root allowlist, initial denylist audit, and static preview wrapper.
- Batch 3 must implement the named route renderers and make `/library/` and `/analysis/` use `docs-viewer-public-routes.json`.
- Batch 4 must convert the allowlists and denylists above into artifact copy and audit code.
- Batch 5 must use the exact build-plus-audit command and the GitHub defaults recorded above.
- Batch 6 must verify unused includes before deleting them and rewrite stale Jekyll/Ruby/Liquid docs and wrappers only after live static deploy is recorded.

## batch close

- Batch 1 is complete. Batch 2 starts from the decisions, route/helper names, copy allowlists, denylist seeds, and exact audit command recorded in this document.
