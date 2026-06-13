---
doc_id: site-request-canonical-static-site-root
title: Canonical Static Site Root Request
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: change-requests
viewable: true
---
# Canonical Static Site Root Request

Status:

- planned

## Summary

Move the public site to a tracked canonical static root named `site/`, with public-site tooling moved to `site-tools/`.

The public site should no longer be treated as a generated artifact assembled from scattered repo paths.
The deployable static tree should be normal source-controlled site files.
Validation remains required, but validation should not generate route shells, copy files, or rebuild a deploy folder.

## Context

The current public-site workflow treats `_public_site/` as generated output.
`public-site/build/` copies allowlisted files, renders public route HTML, writes marker files, and validates the resulting artifact.

That model was useful while replacing older public-site assembly behavior, but it now creates an unnecessary second public tree:

- public HTML, CSS, JavaScript, data, and media are authored or generated outside `_public_site/`;
- the public-site builder stages those files into `_public_site/`;
- `_public_site/` is then the only tree that GitHub Pages actually needs.

If `_public_site/` contains everything needed to serve the site, then the clearer model is to make the deploy root canonical and stop copying files into it.
Because `_public_site/` implies generated output, the canonical root should be renamed to `site/`.

## Proposed Direction

Use this top-level layout:

```text
site/
  index.html
  404.html
  CNAME
  .nojekyll
  assets/
  series/
  works/
  work-details/
  moments/
  catalogue/
  library/
  analysis/

site-tools/
  validation and audit code
  focused tests
```

The deployment workflow should become:

```text
validate site/
upload site/
deploy
```

## Design Decisions

- The canonical public site root is `site/`.
- Public-site tooling moves to `site-tools/`.
- The validation command is `bin/site-validate`.
- No aliases or compatibility layers should be kept for retired public-site build commands or paths during this migration.
- Preview tooling should serve `site/` directly and should not rebuild or copy the public tree.
- `site-tools/` should be simpler than the current public-site build package because it no longer builds anything.
- Python validation code should still be modularized by responsibility when needed; do not replace the builder with one large monolithic validation file.
- Do not preserve the current Python package structure merely for continuity.
- Public URLs remain `/assets/...` because `site/` is the static document root and `site/assets/...` is served at `/assets/...`; this is not an alias, redirect, or compatibility layer.
- Do not add a new generated-payload review or gating copy outside `site/`; existing payload generation behavior should be retargeted to the new public output paths without changing publication workflow semantics.
- Delete the current generated-artifact marker file, `_public_site/.public-site-artifact`, during the move to `site/`; do not replace it with another deploy-root marker because `site/` is normal tracked source, not a deletable generated artifact.

## Page Shell Tradeoff

Making `site/index.html` and route-level `index.html` files canonical means the site no longer gets shared page shells, headers, footers, and script tags from a build-time template layer.
That is an acceptable tradeoff for the current public site because the route count is small and shell drift should remain manageable through normal review and validation.

If drift becomes painful, the next solution does not have to be a return to Jekyll-style build-time includes.
Established static-site options include:

- runtime shared components loaded by JavaScript for global header, nav, footer, theme controls, or route bootstrap;
- small static validation checks that assert required shell fragments, scripts, metadata, and nav links are present;
- editor snippets or templates for manually creating new pages;
- a deliberately narrow HTML synchronization tool that updates only agreed shell regions in existing canonical files;
- a lightweight static-site generator only if page count or shell complexity grows enough to justify build-time templating again.

The default direction for this request remains plain canonical HTML under `site/`.
Any shared-shell mechanism should be introduced only when it solves observed maintenance drift, not as an automatic replacement for the current builder.

## Goals

- Make `site/` the normal tracked canonical public web root.
- Rename current public-site tooling ownership to `site-tools/`.
- Remove `_public_site/` as a generated-output concept.
- Remove root-level `assets/` as a shadow public asset tree after producers and consumers are retargeted.
- Edit public HTML, CSS, JavaScript, icons, and route shells directly under `site/`.
- Point Studio public catalogue outputs at `site/assets/...`.
- Point Docs Viewer public docs, docs search, and public interactive assets at `site/assets/...`.
- Keep app-only assets and generated data under their owning app roots.
- Replace public-site build commands with `bin/site-validate` and direct static preview commands.
- Make GitHub Actions validate `site/` and upload it as the Pages artifact.

## Non-Goals

- Do not introduce a bundler, transpiler, or dynamic runtime build step.
- Do not move canonical Studio catalogue source into `site/`.
- Do not move Docs Viewer source Markdown into `site/`.
- Do not expose Studio, Admin, Analytics, local service, logs, or source management files in `site/`.
- Do not change public URL paths unless a specific follow-up decision approves it.
- Do not redesign catalogue, Docs Viewer, or search generated-data schemas as part of the root rename.

## Ownership Model

`site/` owns only deployable public static files.

Studio owns:

- canonical catalogue source under `studio/data/canonical/...`;
- catalogue source validation and publication flows;
- catalogue public projections written to `site/assets/data/...`, `site/assets/works/index/...`, `site/assets/series/index/...`, and `site/assets/moments/index/...`;
- local media derivative generation for public thumbnails written under `site/assets/...`.

Docs Viewer owns:

- source docs under `docs-viewer/source/...`;
- working generated outputs under `docs-viewer/generated/...` where useful for management flows;
- public published docs and search payloads written to `site/assets/data/docs/...` and `site/assets/data/search/...`;
- public interactive docs assets written to `site/assets/docs/...`.

`site-tools/` owns:

- validation of the tracked public root;
- deploy-surface audits;
- required-file checks;
- forbidden-file and source-leak checks;
- size reporting and optional browser smoke helpers.

## Migration Tracker

Implementation tasks are tracked in [Canonical Static Site Root Migration Tasks](/docs/?scope=studio&doc=site-request-canonical-static-site-root-tasks).

## Validation Requirements

The validation command should check:

- required site files and routes exist;
- `site/` contains `.nojekyll`, `CNAME`, icons, manifest, and `404.html`;
- total size and largest file/path contributors are reported.

## Design-Time Constraints And Tests

The migration should keep source-boundary checks as design-time constraints and focused tests, not as the main pre-deploy validation contract.

These checks should prove:

- app-only roots such as Studio, Admin, Analytics, source docs, services, tests, logs, local env, and git metadata are not configured as public site inputs;
- public generators write only to approved `site/` output paths;
- public route config, app config, and validation manifests do not reference retired root-level `assets/` paths;
- local credentials, workbooks, generated Python caches, and source-management configs are not part of any public output plan;
- workflow configuration uploads `site/` and does not run retired build/copy commands.

The pre-deploy validator may still fail on obviously invalid files inside `site/` if they are present, but the primary prevention should be path ownership, config tests, and workflow tests.

## Site Audit Responsibilities

Site audits may check public content and runtime consistency, but those checks should not be bundled into deploy validation merely because they exist.

Audit checks can include:

- public JSON files parse and match expected top-level schemas;
- catalogue, docs, and search payloads remain internally consistent;
- public Docs Viewer route config points only at public assets under `/assets/...`;
- route smoke tests and browser console checks for representative public pages.

These checks answer whether the site is correct and internally consistent.
`bin/site-validate` answers whether the tracked static root is ready to upload as the deploy artifact.

## GitHub Actions Direction

The Pages workflow should not build or regenerate the public tree.

Expected shape:

```text
checkout
run site validation
upload site/ as the Pages artifact
deploy Pages artifact
```

## Open Decisions

- None.

## Path Config Requirement

Before moving files, verify whether each app already reads and writes public asset paths through configuration.
If it does, the migration should prefer changing the relevant config values over editing call sites.

The desired outcome is:

- Studio catalogue generation resolves public output paths from a small config surface.
- Docs Viewer public publish paths resolve from scope and route config.
- Analytics and Data Sharing read public catalogue indexes through config rather than hardcoded root `assets/` paths.
- Validation reads required public paths from the owning app configs where those paths already exist, and from a small validation-only manifest only for deploy-root requirements that are not owned by an app config.
- Remaining hardcoded `assets/` filesystem defaults are either removed, moved into config, or documented with a clear reason.

If these paths are already mostly config-driven, the migration should simplify to retargeting config plus updating tests and validation expectations.

## Risks

- Hidden hardcoded consumers may still read root-level `assets/` directly.
- Retargeting generators touches Studio, Docs Viewer, Analytics, Admin audit, tests, and GitHub Actions.
- Keeping temporary compatibility aliases could hide remaining coupling and should have explicit removal criteria.
- Docs Viewer public scopes currently distinguish working generated outputs from published public outputs; the migration must preserve that workflow where it is still useful.
- Public preview links from local Studio and Analytics must continue resolving to the served static root.

## Verification Expectations

- Focused tests for validation against `site/`.
- Focused tests for Studio catalogue generation paths.
- Focused tests for Docs Viewer public publish paths.
- Focused tests for Analytics/Data Sharing reads of public catalogue indexes.
- Admin projection-contract audit updated for `site/`.
- Public-site route/browser smoke checks for representative routes:
  - `/series/`
  - `/recent/`
  - `/works/`
  - `/work-details/`
  - `/moments/`
  - `/catalogue/search/`
  - `/library/`
  - `/analysis/`
- GitHub Actions workflow syntax or dry-run validation where practical.
