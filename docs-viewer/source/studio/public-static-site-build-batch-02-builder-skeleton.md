---
doc_id: public-static-site-build-batch-02-builder-skeleton
title: Public Static Site Build Batch 2 Builder Skeleton and Artifact Contract
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: done
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 2 Builder Skeleton and Artifact Contract

This is the delivery specification for Batch 2 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: create the `public-site/` builder boundary and the initial static artifact contract.

## Steer for these tasks

- Batch 1 is closed; use its decisions as implementation inputs.
- Define builder modules, config fields, output path policy, and copy/audit allowlists from the Batch 1 inventories.
- Keep the first builder small: create enough structure to emit an artifact root, `.nojekyll`, root publishing artifacts, and placeholder or parity shells selected by the refined plan.
- Keep the existing Jekyll local preview and production publishing path intact. The static builder introduced here is a parallel path and parity target, not the live path.
- Do not add file-based HTML snippets or a general template engine in this batch.

## Batch 1 handoff

- Default output path is `_public_site/` for local build, local static preview, CI verification, and Pages artifact upload.
- Implement `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit` as the exact build-plus-audit command that Batch 5 will run in GitHub Actions.
- Create `public-site/config/public-site.json` with public-site assembly values formerly owned by `_config.yml`: site identity, URL/base URL, media and thumbnail origins, public runtime text, Docs Viewer public mount/config paths, root artifact expectations, copy allowlists, and denylist audit rules.
- Keep domain-owned configs and generated payloads with their current owners. The builder reads them as inputs and assembles deployable copies.
- Root artifact allowlist starts with `CNAME`, favicons, app icons, `safari-pinned-tab.svg`, `site.webmanifest`, rendered `404.html`, and generated `.nojekyll`.
- Initial source-leak audit must fail on root source/tooling files, local app directories, Jekyll files, private Docs Viewer files, `.DS_Store`, caches, logs, and private generated docs/search payloads.

## Deliverables

- `public-site/build/build_site.py` and focused builder modules under `public-site/build/public_site_builder/`.
- `public-site/config/public-site.json` with only public-site assembly settings.
- `bin/public-site-build` wrapper for the static builder.
- `bin/public-site-preview-static` temporary static preview command that builds `_public_site/` and serves it with a simple local static HTTP server.
- Initial artifact output under the chosen `_public_site/` policy.
- Initial artifact audit command.

## Implementation and policy guidance

- The builder owns route HTML, public assets, generated public data, public Docs Viewer installs, root publishing artifacts, `.nojekyll`, and deployment surface checks.
- Do not copy arbitrary repo-root content.
- Do not add a general template engine. Batch 1 must record a rendering-model decision change before this batch uses one.

## Proposed verification set

- Python syntax/import checks for new builder modules.
- Build command writes the chosen output directory.
- Candidate static preview serves `_public_site/` over HTTP.
- Existing Jekyll preview command still works and remains the default preview baseline.
- Artifact root contains `.nojekyll` and the expected root publishing artifacts for this batch.
- Source-leak audit passes for the initial copy surface.

## Tasks

### Batch 2: Builder Skeleton and Artifact Contract

| ID | status | action |
| --- | --- | --- |
| 2.1 | done | Convert the Batch 1 handoff into module boundaries, CLI options, config fields, copy allowlists, and audit denylist tests before implementation starts. |
| 2.2 | done | Create the `public-site/` builder package, config file, and command wrappers. |
| 2.3 | done | Implement output-directory handling and artifact-root initialization with `.nojekyll`. |
| 2.4 | done | Implement the initial root artifact allowlist and source-leak audit shell, including the current `_site/` leak seeds from Batch 1. |
| 2.5 | done | Add `bin/public-site-preview-static` as the temporary static preview command that builds `_public_site/` once and serves it over HTTP. |
| 2.6 | done | Confirm the existing Jekyll preview and deploy path are still untouched and available as the parity baseline. |
| 2.7 | done | Record exact verification commands and update Batch 3 with route-rendering prerequisites and the final render helper module names. |

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile public-site/build/build_site.py public-site/build/public_site_builder/*.py public-site/tests/test_build_site.py`
- `bash -n bin/public-site-build bin/public-site-preview bin/public-site-preview-static`
- `$HOME/miniconda3/bin/python3 -m json.tool public-site/config/public-site.json`
- `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit`
- `bin/public-site-build --destination _public_site --audit`
- `bin/public-site-preview-static --port 4012`, then `curl -sS -I http://127.0.0.1:4012/404.html`; returned `HTTP/1.0 200 OK`; server stopped after verification.
- `$HOME/miniconda3/bin/python3 -m pytest -q public-site/tests/test_build_site.py`; 3 tests passed.

## follow-on tasks

- Batch 3 must extend `public_site_builder.render` and add route rendering modules without replacing the artifact guardrails introduced here.
- Batch 3 must replace the initial minimal `404.html` renderer with the shared page/layout helpers used by all route shells.
- Batch 4 must extend the copy/audit layer in `public_site_builder.builder` and `public_site_builder.audit` rather than adding a second artifact assembly path.

## batch close

- Batch 2 is complete. Batch 3 starts from `public-site/build/build_site.py`, `public_site_builder.config`, `public_site_builder.builder`, `public_site_builder.render`, and `public_site_builder.audit`.
