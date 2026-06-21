---
doc_id: site-request-docs-viewer-runtime-js-ownership-split
title: Docs Viewer Runtime JavaScript Ownership Split Request
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: change-requests
viewable: true
---
# Docs Viewer Runtime JavaScript Ownership Split Request

Status:

- done

## Summary

Split Docs Viewer runtime JavaScript into explicit site-owned public/shared runtime and Docs Viewer-owned local management/runtime areas.

After the static-site migration, `site/` is the checked-in public deploy root.
The public-site GitHub Actions workflow no longer watches `docs-viewer/runtime/js/**`; it validates and uploads `site/` directly.
This request is therefore no longer about reducing workflow trigger noise.
It is about making `site/docs-viewer/runtime/js/` the canonical owner of the public read-only Docs Viewer runtime, with local Docs Viewer management code importing those modules when it shares runtime behavior.
Folder-level organization is part of the design check: if ownership and responsibility are correct, the file tree should make that visible.

## Context

This request originally existed because the public-site workflow included this path filter:

- `docs-viewer/runtime/js/**`

That filter was intentionally conservative, but it was too broad for ongoing development.
It has been removed by the canonical static-site-root migration.
The workflow now watches the deploy root and site toolchain:

- `site/**`
- `site-tools/**`
- `bin/site-validate`
- `.github/workflows/public-site.yml`

Before this migration, `docs-viewer/runtime/js/` contained public read-only runtime modules, shared shell modules, local Studio/management modules, import workflow modules, and reporting modules.
The canonical public deploy root contained the public runtime subset at `site/docs-viewer/runtime/js/`.
Those public runtime modules were duplicated between `site/docs-viewer/runtime/js/` and `docs-viewer/runtime/js/`.

The New Scope public-disable fix changed `docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js`.
That module is loaded from management code and is not part of the public runtime in `site/`, but the source tree layout still does not make that ownership obvious.

Docs Viewer is not expected to be a standalone local-only product in this repository.
It exists here to make the public `/library/` and `/analysis/` scopes possible.
If Docs Viewer is ever packaged separately as a local-only product, that package can draw in the public runtimes from `site/` explicitly.

## Original Problem

The pre-migration folder boundary did not express runtime ownership.

As a result:

- public runtime modules were duplicated between `site/docs-viewer/runtime/js/` and `docs-viewer/runtime/js/`
- future runtime refactors could drift between the canonical public runtime and the local duplicate
- reviewers had to infer ownership from filenames, import tests, and the duplicated files
- static import boundaries were partly guarded by tests, but the source tree did not communicate those boundaries
- management, import, and report modules were adjacent to duplicated public modules in the source runtime directory
- public-only and public/shared modules were not separated by folder in the public runtime tree
- local management code did not make it obvious when it was reusing the public runtime

## Goals

- Define stable Docs Viewer JavaScript ownership areas.
- Make `site/docs-viewer/runtime/js/` the canonical source for public read-only runtime modules.
- Make shared public/management runtime modules site-owned when the public site needs them.
- Split site-owned runtime modules into `public/` and `shared/` folders so public ownership is visible in the deploy tree.
- Remove duplicated public/shared runtime modules from `docs-viewer/runtime/js/`.
- Move local management-only modules into a Docs Viewer-owned management area.
- Move import-workflow-only modules into a Docs Viewer-owned import area.
- Move report-only modules into a Docs Viewer-owned report area.
- Update local Docs Viewer management imports so shared/public runtime behavior is imported from `site/docs-viewer/runtime/js/`.
- Update static imports and dynamic imports after the move.
- Update `site-tools` validation expectations for the checked-in public runtime.
- Keep existing public Docs Viewer behavior for `/library/` and `/analysis/`.
- Keep existing local Studio Docs Viewer management behavior.

## Non-Goals

- Do not introduce a JavaScript bundler or transpiler.
- Do not convert classic public catalogue scripts under `assets/js/`; that belongs to the public JavaScript runtime and payload review request.
- Do not redesign the Docs Viewer public route contract.
- Do not change generated docs payload schemas.
- Do not remove management features from the local Studio runtime.
- Do not reintroduce a public-site build or copy process.
- Do not add compatibility shims for old runtime paths during this migration.
- Do not add a neutral shared runtime source tree for this repository.

## Design Decision

`site/docs-viewer/runtime/js/` owns public and shared Docs Viewer runtime JavaScript.
If a runtime module is required by the public `/library/` or `/analysis/` scopes, the canonical file lives under `site/`.
The site-owned runtime is split by purpose:

- `site/docs-viewer/runtime/js/public/` for public read-only entrypoints and public-only modules
- `site/docs-viewer/runtime/js/shared/` for modules used by both public scopes and local management

`docs-viewer/runtime/js/` owns local-only runtime JavaScript:

- management modules
- source/import workflow modules
- report modules
- local-only integration modules

Local Docs Viewer management code may import from `site/docs-viewer/runtime/js/` when it shares public runtime behavior.
That is an intentional dependency in this repository because Docs Viewer exists here to serve and maintain public Docs Viewer scopes.
Those imports should be normal browser module imports through the served URL graph, not filesystem-looking paths into `site/`.

There is no workflow build step that copies runtime JavaScript from `docs-viewer/` to `site/`.
There is no generated public runtime artifact outside the tracked `site/` tree.
This migration intentionally changes public module URLs where needed to make ownership visible in the file tree.
There will be no compatibility aliases for old flat runtime paths.

The local Docs Viewer service should own an explicit static route-prefix map:

- `/docs-viewer/runtime/js/public/...` serves `site/docs-viewer/runtime/js/public/...`
- `/docs-viewer/runtime/js/shared/...` serves `site/docs-viewer/runtime/js/shared/...`
- `/docs-viewer/runtime/js/management/...` serves `docs-viewer/runtime/js/management/...`
- `/docs-viewer/runtime/js/import/...` serves `docs-viewer/runtime/js/import/...`
- `/docs-viewer/runtime/js/reports/...` serves `docs-viewer/runtime/js/reports/...`
- `/docs-viewer/runtime/js/local/...` serves `docs-viewer/runtime/js/local/...`, if needed

With that route map, a management module can import a shared module as `../shared/name.js`.
The browser resolves the import to `/docs-viewer/runtime/js/shared/name.js`; the local service resolves that URL to the site-owned file.

`site-tools` validation should use a small explicit manifest for the public Docs Viewer runtime.
That is consistent with the broader static deploy model: `site/` contains the deployable files, and validation checks the declared deploy surface rather than deriving or generating it.
The manifest should declare the site-owned runtime entrypoints and allowed public/shared module files or prefixes.
Validation should fail when `site/docs-viewer/runtime/js/` contains files outside the manifest, including management, import, report, or local-only runtime modules.

## Proposed Ownership Areas

Use directory names that make source ownership clear:

- `site/docs-viewer/runtime/js/public/` for public read-only runtime modules
- `site/docs-viewer/runtime/js/shared/` for runtime modules shared by public scopes and local management
- `docs-viewer/runtime/js/management/` for local management modules
- `docs-viewer/runtime/js/import/` for local source/import workflow modules
- `docs-viewer/runtime/js/reports/` for local report modules
- `docs-viewer/runtime/js/local/` or similarly named folders only where a local-only module does not fit the management/import/report categories

The exact file placement must be decided from an import graph audit before files move.

The public URL contract is the `site/` file tree.
Because there will be no compatibility layer, public URLs should move directly to the new ownership paths in `site/` and be verified as part of the same migration.

## Audit Requirements

The first implementation batch must record:

- the current public runtime files checked in under `site/docs-viewer/runtime/js/`
- all static imports from public runtime entrypoints
- all dynamic imports reachable from public runtime entrypoints
- all management-only modules and their dynamic import boundaries
- all import-workflow-only modules and their entrypoints
- all report-only modules and their entrypoints
- files that are duplicated between `site/docs-viewer/runtime/js/` and `docs-viewer/runtime/js/`
- files that are used by both public and management runtimes and should become site-owned imports
- files in `docs-viewer/runtime/js/` that are local-only and should remain Docs Viewer-owned
- existing tests and validation that guard public runtime membership

## Decisions Needed

No open design decisions remain.
The implementation should proceed as one ownership migration after the audit and file placement map are recorded.
The repository should not intentionally pause in a mixed state where public/shared runtime files remain duplicated between `site/` and `docs-viewer/`.

## Implementation Tracker

| Task | Status | Description |
| --- | --- | --- |
| 1 | done | Recorded the runtime inventory and import graph: public entrypoint, public/shared static graph, management-only modules, import-workflow-only modules, report-only modules, duplicated public/shared files, and local-only files. |
| 2 | done | Produced and applied the file placement map for `site/docs-viewer/runtime/js/public/`, `site/docs-viewer/runtime/js/shared/`, `docs-viewer/runtime/js/management/`, `docs-viewer/runtime/js/import/`, and `docs-viewer/runtime/js/reports/`. No `docs-viewer/runtime/js/local/` files were needed. |
| 3 | done | Moved site-owned runtime modules into `site/docs-viewer/runtime/js/public/` and `site/docs-viewer/runtime/js/shared/`, then updated public route entrypoints and public runtime imports to the new ownership paths. |
| 4 | done | Moved local-only management, import, and report modules into their Docs Viewer-owned folders, updated static and dynamic imports, and made local management imports use site-owned shared/public modules through served URL paths. |
| 5 | done | Removed duplicated public/shared runtime files from `docs-viewer/runtime/js/`; `site/` is now the only owner of those modules. |
| 6 | done | Updated the local Docs Viewer service static route-prefix map so public/shared runtime URLs resolve from `site/` and local-only runtime URLs resolve from `docs-viewer/`. |
| 7 | done | Added the explicit public Docs Viewer runtime manifest and updated `site-tools` validation to enforce it. |
| 8 | done | Updated tests for public import graphs, management import graphs, service routing, duplicate-runtime absence, public runtime manifest validation, and Admin target-map ownership paths. |
| 9 | done | Updated stable Docs Viewer/runtime documentation for the new ownership model and served URL prefixes. |
| 10 | done | Ran verification: focused Python tests, `bin/site-validate`, public Docs Viewer browser smoke for `/library/` and `/analysis/`, local Docs Viewer management smoke, and actionlint for `.github/workflows/public-site.yml`. |

## Implementation Result

The runtime ownership split is implemented.

Site-owned runtime:

- `site/docs-viewer/runtime/js/public/docs-viewer-public.js`
- `site/docs-viewer/runtime/js/shared/*.js`

Docs Viewer-owned local runtime:

- `docs-viewer/runtime/js/management/*.js`
- `docs-viewer/runtime/js/management/source-editor/source-editor.js`
- `docs-viewer/runtime/js/import/*.js`
- `docs-viewer/runtime/js/reports/*.js`

No public/shared runtime files remain duplicated under `docs-viewer/runtime/js/`.
No root-level `.js` files remain under `site/docs-viewer/runtime/js/` or `docs-viewer/runtime/js/`.

The local Docs Viewer service route map is now explicit:

- `/docs-viewer/runtime/js/public/...` resolves from `site/docs-viewer/runtime/js/public/...`
- `/docs-viewer/runtime/js/shared/...` resolves from `site/docs-viewer/runtime/js/shared/...`
- `/docs-viewer/runtime/js/management/...` resolves from `docs-viewer/runtime/js/management/...`
- `/docs-viewer/runtime/js/import/...` resolves from `docs-viewer/runtime/js/import/...`
- `/docs-viewer/runtime/js/reports/...` resolves from `docs-viewer/runtime/js/reports/...`

`site-tools/config/site-tools.json` now declares the public Docs Viewer runtime manifest.
`bin/site-validate` validates that `site/docs-viewer/runtime/js/` matches that manifest and rejects extra runtime files outside it.

## Completed Verification

- Route-aware JavaScript import check: all imports resolve through the new served URL prefixes.
- Duplicate/root runtime check: no root-level runtime `.js` files remain under `site/docs-viewer/runtime/js/` or `docs-viewer/runtime/js/`, and no public/shared filenames are duplicated under `docs-viewer/runtime/js/`.
- Focused tests: `$HOME/miniconda3/bin/python3 -m pytest -q docs-viewer/tests/python/test_docs_viewer_service.py site-tools/tests/test_site_validate.py admin-app/tests/python/test_target_map_resolver.py admin-app/tests/python/test_target_map_report.py admin-app/tests/python/test_files_report.py admin-app/tests/python/test_admin_checks_api.py admin-app/tests/python/test_run_reports.py`
- Result: `55 passed`.
- Site validation: `bin/site-validate`.
- Result: `Site validation passed: 47 required files; 9 required directories; 44 Docs Viewer runtime modules`.
- Browser smoke: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root site`.
- Result: public Docs Viewer read-only OK for `/library/` and `/analysis/`.
- Browser smoke: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`.
- Result: Docs Viewer service manage shell OK for `/docs/?scope=studio&doc=docs-viewer`.
- Syntax/workflow checks: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py site-tools/site_tools/config.py site-tools/site_tools/validation.py site-tools/site_validate.py`; `actionlint .github/workflows/public-site.yml`.

## Verification Expectations

- Focused import graph check for the public runtime.
- Focused import graph check for local management runtime imports from site-owned shared/public modules.
- Focused service routing tests proving public/shared runtime URLs resolve from `site/` and local-only runtime URLs resolve from `docs-viewer/`.
- `bin/site-validate`.
- Validation proving management, import, and report runtime files are absent from `site/docs-viewer/runtime/js/`.
- Validation proving public/shared runtime files are not duplicated under `docs-viewer/runtime/js/`.
- Validation proving site-owned runtime files live under `site/docs-viewer/runtime/js/public/` or `site/docs-viewer/runtime/js/shared/`.
- Validation proving `site/docs-viewer/runtime/js/` matches the explicit public runtime manifest.
- Public Docs Viewer browser smoke for `/library/` and `/analysis/`.
- Local Studio Docs Viewer management smoke, including New Scope modal behavior.
- Actionlint validation for `.github/workflows/public-site.yml`.
- A source-only management JS change should not require a `site/` deploy-root change unless it affects shared runtime behavior.

## Related Docs

- [GitHub Actions](/docs/?scope=studio&doc=github-actions)
- [Public JavaScript Runtime and Payload Review Request](/docs/?scope=studio&doc=site-request-public-js-runtime-payload-review)
- [Portable Static Docs Viewer Install Request](/docs/?scope=studio&doc=site-request-data-driven-public-docs-scope-routes)
