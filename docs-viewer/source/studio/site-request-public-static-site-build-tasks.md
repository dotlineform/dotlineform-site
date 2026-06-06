---
doc_id: site-request-public-static-site-build-tasks
title: Public Static Site Build Tasks
added_date: 2026-06-02
last_updated: 2026-06-02
ui_status: draft
parent_id: site-request-public-static-site-build
---
# Public Static Site Build Tasks

This is the tracker for implementing [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build).

## Status

### just done

- Created this child tracker from `tasks-template.md`.
- The parent request now records resolved migration decisions for builder ownership, rendering, config, route generation, route parity, output, artifact copy policy, local preview, GitHub Actions deployment, verification, Jekyll removal, and deployment failure handling.

### steer for next task

- Start with a source/build responsibility inventory before adding builder code.
- Keep the new implementation under `public-site/`; `bin/public-site-build` and `bin/public-site-preview` should remain thin operator-facing wrappers.
- Do not switch production deploy, remove Jekyll, or remove Jekyll-era files until static output parity and the verification gate pass.
- Treat `/palette/` as excluded from public-site parity; palette inspection is owned by the UI Catalogue app at `/admin/ui-catalogue/palette/`.

### baseline verification set

Use proportional verification per slice. The final deployment switch requires the full gate below, but early slices should run only the checks touched by that slice.

- Python syntax/import checks for new builder modules: `$HOME/miniconda3/bin/python3 -m py_compile public-site/build/build_site.py`.
- Focused Python tests for `public-site/` modules once tests exist.
- Static builder dry run and write run once implemented:
  - `$HOME/miniconda3/bin/python3 public-site/build/build_site.py`
  - `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --write --output _public_site`
- Public build surface audit against `_public_site/`.
- Projection contract audit against `_public_site/`.
- Focused browser smoke tests for all simplified public catalogue routes, public Docs Viewer `/library/` and `/analysis/`, and `404.html`.
- Source and docs scans for stale Jekyll/Ruby command paths, Liquid assumptions, and retired collection-route dependencies.
- Artifact-root checks for `.nojekyll`, `CNAME`, favicon/site manifest files, and `404.html`.
- Artifact size report for `_public_site/`, including total size and the largest file/folder contributors.
- GitHub Actions workflow validation or dry run proving the Pages artifact contains only intended static output.
- Before Jekyll removal only, use the current Jekyll output as a parity reference where useful.

Codex sandbox note: local service, browser, temporary localhost, and Playwright checks will need elevated permissions even when the product code is healthy.

### general steer

- Follow [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) as the implementation contract.
- Follow [Public Route Model](/docs/?scope=studio&doc=public-route-model) for the durable public route model.
- Generate fixed route shells and individual moment pages from public route contracts and public generated data, not from Jekyll collection stubs.
- Use explicit Python rendering helpers/components rather than a general template engine.
- Keep existing domain-owned configs with their owners; `public-site/config/public-site.json` assembles the deployable public artifact.
- Use positive copy allowlists. Do not copy arbitrary site-root files, local source, Studio-only source, manage-only Docs Viewer source, logs, tests, or `var/` output.
- Preserve generated output as untracked `_public_site/`.
- Use repair-forward deployment handling: fix the static builder/workflow/artifact and redeploy a corrected Actions artifact.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current Jekyll responsibilities, public route files, Liquid includes/layout behavior, site-root publishing artifacts, generated public data inputs, Docs Viewer public install inputs, asset paths, and existing public build audits. Deliverable: concise responsibility map in a sibling inventory note. |
| 2 | planned | Scaffold the `public-site/` boundary with `build/build_site.py`, the `public_site_builder/` module package, `config/public-site.json`, and placeholder tests. Keep the builder inert or dry-run only until input/output contracts are explicit. |
| 3 | planned | Implement config loading and validation for `public-site/config/public-site.json`. Preserve domain-owned configs with their current owners and read them only as inputs. |
| 4 | planned | Implement output directory handling for ignored `_public_site/`, including clean write behavior, `.nojekyll` generation, and diagnostics that identify the selected output directory. Do not write into `_site/`. |
| 5 | planned | Implement artifact copy allowlists for site-root publishing artifacts and public static assets. Include `CNAME`, favicon files, `apple-touch-icon` files, `safari-pinned-tab.svg`, `site.webmanifest`, `404.html` where applicable, public CSS/JS/assets, public generated data, and public Docs Viewer runtime payloads. |
| 6 | planned | Implement explicit Python rendering helpers/components to replace the needed `_layouts/` and `_includes/` behavior: document shell, head metadata, navigation, asset includes, footer, Docs Viewer shell mounting, catalogue route shells, canonical URLs, and deterministic asset versioning. Do not recreate Liquid semantics or broad template inheritance. |
| 7 | planned | Render all fixed public route shells from [Public Route Model](/docs/?scope=studio&doc=public-route-model): `/`, `/about/`, `/recent/`, `/series/`, `/works/`, `/work-details/`, `/moments/`, `/catalogue/search/`, `/library/`, `/analysis/`, and `404.html`. Exclude `/palette/` from public-site parity because palette inspection is owned by the UI Catalogue app at `/admin/ui-catalogue/palette/`. |
| 8 | planned | Generate individual moment pages from public moment records or generated public data, not from `_moments` stubs. Confirm no builder input depends on `_works/`, `_series/`, `_work_details/`, or `_moments` collection stubs. |
| 9 | planned | Integrate public catalogue projections/generated public data, catalogue search payloads, Docs Viewer public docs/search payloads, and media/static assets without widening the publish surface. |
| 10 | planned | Add public build surface audit and source/projection leak checks for `_public_site/`. Fail on Studio-only source, manage-only Docs Viewer source, logs, tests, `var/`, local service files, Jekyll collection stubs, or derivable/private source data appearing in the artifact. |
| 11 | planned | Retarget `bin/public-site-build` to the Python static builder while preserving the command name and adding destination/output controls needed by local and CI runs. |
| 12 | planned | Retarget `bin/public-site-preview` to run the Python builder once, serve `_public_site/`, and print the local preview URL. Defer watch mode, CSS/JS fast-copy, and rebuild loops. |
| 13 | planned | Add focused unit tests and command tests for config loading, route enumeration, rendering helpers, output writes, copy allowlists, and audit failures. Run syntax/import checks for new Python modules. |
| 14 | planned | Add or update browser smoke coverage for all simplified public catalogue routes, individual moment pages, `/catalogue/search/`, `/library/`, `/analysis/`, `/moments/`, and `404.html` against `_public_site/`. |
| 15 | planned | Add the GitHub Actions Pages workflow: `pull_request` build/verify only, `push` to `main` build/verify/upload/deploy, `workflow_dispatch` manual rebuild/redeploy from `main`, Pages concurrency, limited permissions, and standard `github-pages` environment. Avoid path filters in the first production workflow. |
| 16 | planned | Add an artifact size report for `_public_site/`. Report total size plus the largest file and folder contributors, and include a documented warning threshold, initially `250 MB`, so accidental broad copies are visible before Pages upload. |
| 17 | planned | Run the full verification gate against `_public_site/` and the Actions artifact shape. Record command results, artifact size output, and any remaining risks before switching production deployment. |
| 18 | planned | After static parity and verification pass, remove or retire Jekyll/Ruby build artifacts and paths: `Gemfile`, `Gemfile.lock`, `.ruby-version`, Jekyll-specific `_config.yml` usage, `_layouts/`, `_includes/`, Jekyll collection stubs, and Bundler/Jekyll wrapper logic. |
| 19 | planned | Update owning docs for public build commands, local preview behavior, source organisation, config ownership, public route ownership, verification commands, GitHub Pages deployment, and retired Jekyll/Ruby assumptions. Do not rebuild Docs Viewer payloads manually. |
| 20 | planned | Close out the implementation: update this tracker and the parent request statuses, summarize moved/removed paths, record verification results and generated payload status, confirm `/palette/` ownership handling, and note any deliberately retained Jekyll-era file with owner/removal reason. |

## Closeout Requirements

Closeout should confirm:

- the static builder lives under `public-site/`
- `bin/public-site-build` and `bin/public-site-preview` dispatch to the Python builder path
- local output defaults to ignored `_public_site/`
- production deploy uses GitHub Actions Pages artifacts only
- all simplified public routes and intentionally public top-level pages are present in the generated artifact
- `/palette/` is no longer treated as a public-site parity route, and `/admin/ui-catalogue/palette/` remains the UI Catalogue-owned palette reference route
- individual moment pages are generated from public moment records or generated public data
- Jekyll collection stubs are not builder inputs
- generated artifact root includes `.nojekyll`, `CNAME`, favicon/site manifest files, and `404.html`
- source/projection leak checks pass
- artifact size report is recorded, including total size and largest contributors
- public Docs Viewer `/library/` and `/analysis/` work from the generated artifact
- Jekyll/Ruby build artifacts and docs are removed or explicitly justified if retained
- final verification commands and results are recorded
- docs payloads were not manually rebuilt unless a separate explicit docs-build task required it
