---
doc_id: public-static-site-build-batch-06-jekyll-removal-closeout
title: Public Static Site Build Batch 6 Jekyll Removal and Closeout
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: done
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 6 Jekyll Removal and Closeout

This is the delivery specification for Batch 6 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: remove or retire Jekyll/Ruby build artifacts, update docs, rerun final verification, and close the migration.

## Batch 5 handoff

Batch 5 completed the production cutover from legacy Pages branch publishing to GitHub Actions Pages artifact publishing.

Cutover record:

- Deploy gate variable: `PUBLIC_SITE_PAGES_DEPLOY_ENABLED=true`, set at `2026-06-12T18:57:02Z`.
- Pages source command: `gh api --method PUT repos/dotlineform/dotlineform-site/pages -f build_type=workflow`.
- Pages source after cutover: `build_type: workflow`, custom domain `www.dotlineform.com`, custom 404 enabled, HTTPS enforced.
- Cutover deploy run: `27436556962`, workflow `Public site`, event `workflow_dispatch`, branch `main`, commit `d4874d961faf617370f2bc399a66d933a3de6e30`.
- Cutover artifact: Pages artifact `7600112973`, built from `_public_site/`.
- Cutover deployment completion: `2026-06-12T18:57:51Z`.
- Live site URL: `https://www.dotlineform.com/`.

Verified cutover behavior:

- The workflow built and audited `_public_site/`: 6899 copied public files, 11 rendered route pages, and 6912 checked files.
- `public-site/build/validate_artifact.py` passed: 6912 checked files and 44 Docs Viewer runtime modules.
- The `Deploy Pages artifact` job completed successfully.
- Live production smoke passed for `/series/`, `/series/?mode=moments`, `/recent/`, `/works/?work=00008&series=105`, `/catalogue/search/`, `/library/`, and `/analysis/`.
- Live production smoke confirmed work `00008` renders the `nerve.pdf` download link to `https://media.dotlineform.com/works/files/nerve.pdf`.
- Live production smoke reported no browser console errors for the checked route list.

Residual notes carried into this batch:

- `actions/deploy-pages@v5` logged a Node `punycode` deprecation warning during the successful deploy.
- Legacy Pages source is no longer active.
- This batch removes or retargets the local Jekyll/Ruby files and wrapper scripts.
- This batch adds scoped workflow path filters so unrelated `main` pushes do not rebuild or deploy the public site.

## Closeout summary

Replacement owners:

- `public-site/config/public-site.json` owns public-site assembly config and acts as the repo-root marker for Python tooling.
- `public_site_builder.render`, `static_routes`, `catalogue_routes`, and `docs_routes` own the former layout, include, and route-shell rendering responsibilities.
- `public-site/build/build_site.py` owns local and CI artifact creation.
- `public-site/build/validate_artifact.py` and `public_site_builder.audit` own source-leak and artifact-surface validation.
- `bin/public-site-preview` owns the operator-facing local static preview command.
- `.github/workflows/public-site.yml` owns production build, validation, artifact upload, and deploy.

Removed Jekyll-era files and stubs:

- `Gemfile`, `Gemfile.lock`, `.ruby-version`, and `_config.yml`.
- `_layouts/` and `_includes/`.
- old Markdown/Liquid public route stubs for root, about, 404, series, works, work details, moments, recent, catalogue search, library, and analysis.
- `bin/public-site-preview-static`, because the default preview command now serves the static artifact.

Retained Jekyll-era strings:

- `.nojekyll` remains a GitHub Pages artifact marker owned by `public-site/config/public-site.json`.
- Denylist entries for former Jekyll paths remain in artifact audits to prevent accidental source leakage if those names return.
- Historical migration docs can still mention Jekyll as prior-state context.

Local preview transition:

- `bin/public-site-preview` now builds `_public_site/` with the Python static builder and serves that directory with Python's HTTP server.
- The old Jekyll local preview stopped being supported in Batch 6, after the Batch 5 live Actions artifact deploy succeeded on 2026-06-12.
- `PUBLIC_SITE_HOST`, `PUBLIC_SITE_PORT`, `PUBLIC_SITE_DESTINATION`, and `PUBLIC_SITE_PYTHON` are the active wrapper environment variables.

## Steer for these tasks

- Batch 1 is closed; re-check this batch after Batch 5 proves the static deploy path.
- Do not remove Jekyll-era files before replacement behavior is verified.
- Any retained Jekyll-era naming must have a non-Jekyll owner and a removal reason.
- The current Jekyll local preview stops being supported only in this batch, after Batch 5 has recorded a successful live static Actions artifact deploy.
- Batch 5 production cutover is a required prerequisite for this batch.
- Retarget `bin/public-site-preview` to the verified static build-and-serve path rather than removing the operator-facing preview command.
- After live static deploy parity is proven, scope the public-site workflow triggers so unrelated `main` commits do not rebuild or deploy the public site.

## Batch 1 handoff

Jekyll-era removal candidates are:

- `Gemfile`, `Gemfile.lock`, `.ruby-version`, `_config.yml`, `_layouts/`, and `_includes/`.
- Bundler/Jekyll logic in `bin/public-site-build` and `bin/public-site-preview`.
- Unused includes `_includes/work_index_item.html` and `_includes/artist_line.html`, after Batch 3 confirms they still have no active route usage.
- Documentation and operator commands that present Ruby, Bundler, Jekyll, Liquid, `_config.yml`, `_layouts`, or `_includes` as the public build path.

Keep or retarget only with a named non-Jekyll owner:

- `bin/public-site-preview` remains the operator-facing preview command, but it must serve the static artifact after cutover.
- `bin/public-site-preview-static` is temporary during dual-running and must be removed or given a retained owner once the default preview command serves static output.
- Any retained file with Jekyll-era naming needs a closeout note that explains its new owner and why it remains.

## Deliverables

- Removal of `Gemfile`, `Gemfile.lock`, `.ruby-version`, Jekyll-specific `_config.yml` usage, `_layouts/`, `_includes/`, Jekyll collection stubs, and wrappers that invoke Bundler or Jekyll. Any retained item requires a non-Jekyll owner and removal reason in the closeout.
- Updated operator docs and setup docs for the static builder and preview path.
- Final verification results and closeout notes.
- Parent request and tracker status updates.
- A local-preview transition note naming that `bin/public-site-preview` now serves the static artifact, the removal or retained owner of `bin/public-site-preview-static`, and when the old Jekyll preview stopped being supported.
- Scoped public-site workflow triggers based on the verified builder inputs and public artifact owners.

## Implementation and policy guidance

- Prefer direct reference updates over compatibility shims.
- Do not leave Ruby/Jekyll as a documented public-site build path.
- Keep generated site output untracked on `main`.
- Retarget old local preview wrappers only after the static preview command is documented and verified.
- Keep the first production workflow unfiltered through Batch 5 cutover. Add workflow path filters in this batch only after the live Actions artifact deploy is verified.
- Derive path filters from `public-site/config/public-site.json`, route-renderer owners, public Docs Viewer config/runtime owners, generated public payload owners, root metadata artifacts, and workflow files. Do not use broad app-only assumptions.

## Proposed verification set

- Full static public-site verification gate.
- Remote workflow validation after adding path filters: a public-site-relevant commit triggers the workflow, and a non-public-site commit does not trigger it.
- Source/docs scans for stale Ruby, Bundler, Jekyll, Liquid, `_config.yml`, `_layouts`, and `_includes` command assumptions.
- Artifact surface and source-leak audits after removals.
- Browser smoke checks for the final static artifact.
- Changed-file sanitization scan for changed scripts, workflows, config, and docs.

## Tasks

### Batch 6: Jekyll Removal and Closeout

| ID | status | action |
| --- | --- | --- |
| 6.1 | done | Confirm the Batch 1 Jekyll responsibility inventory against the Batch 5 deploy results before removing files. |
| 6.2 | done | Confirm Batch 5 recorded a successful live Actions artifact deploy before starting removal work. |
| 6.3 | done | Remove Ruby/Jekyll build files and wrappers after replacement behavior is verified; record any retained item with owner and removal reason. |
| 6.4 | done | Retarget `bin/public-site-preview` to the verified static build-and-serve path. |
| 6.5 | done | Remove `bin/public-site-preview-static` after the default preview command serves static output. |
| 6.6 | done | Add scoped workflow path filters after live static deploy parity is proven. |
| 6.7 | done | Update docs, setup commands, workflow docs, and source-organisation docs to make the static builder the only public build path and remove stale Jekyll/Ruby/Liquid assumptions. |
| 6.8 | done | Run final verification gate and stale-reference scans. |
| 6.9 | done | Close out the parent request, implementation tracker, and batch documents with verification results, retained risks, and follow-on work. |

## completed verification

- Static build and audit passed:
  `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination /tmp/dlf-public-site-batch6 --audit`
  Result: 6899 copied public files, 11 rendered route pages, and 6912 audited files.
- Artifact validator passed:
  `$HOME/miniconda3/bin/python3 public-site/build/validate_artifact.py --destination /tmp/dlf-public-site-batch6 --expected-docs-runtime-count 44`
  Result: 6912 checked files and 44 Docs Viewer runtime modules.
- Workflow lint passed:
  `actionlint .github/workflows/public-site.yml`.
- Shell syntax passed:
  `bash -n bin/public-site-preview bin/public-site-build bin/local-all`.
- Focused pytest passed:
  `$HOME/miniconda3/bin/python3 -m pytest -q docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_docs_viewer_service.py studio/tests/python/test_publish_media_to_r2.py studio/tests/python/test_local_env.py studio/tests/python/test_studio_app_server.py analytics-app/tests/python/test_tags_data_sharing_adapter.py analytics-app/tests/python/test_analytics_data_sharing_api.py`
  Result: 85 passed.
- Quick profile passed:
  `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick --run-id batch6-final-quick`
  Summary: `var/admin/test-runs/batch6-final-quick/summary.md`.
- Public route browser smoke passed:
  `$HOME/miniconda3/bin/python3 studio/tests/smoke/public_route_simplification.py --site-root /tmp/dlf-public-site-batch6`.
- Public Docs Viewer read-only browser smoke passed:
  `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-public-site-batch6`.
- Retargeted preview command verified:
  `bin/public-site-preview --destination /tmp/dlf-public-site-preview-batch6 --port 4017`, then `curl -sS -I http://127.0.0.1:4017/series/` returned `HTTP/1.0 200 OK`.
- JSON validation passed for Admin check config and projection contract.

## follow-on tasks

- After the next public-site-relevant push, confirm the scoped workflow still triggers and deploys.
- After a later non-public-site commit to `main`, confirm the scoped workflow does not run.
- Continue the separate [Public JavaScript Runtime and Payload Review Request](/docs/?scope=studio&doc=site-request-public-js-runtime-payload-review).

## batch close

- Batch status is `done`.
- [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan) is ready to close after generated docs payloads are refreshed.
- [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) is ready to close after generated docs payloads are refreshed.
