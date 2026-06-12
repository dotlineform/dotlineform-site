---
doc_id: public-static-site-build-batch-06-jekyll-removal-closeout
title: Public Static Site Build Batch 6 Jekyll Removal and Closeout
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 6 Jekyll Removal and Closeout

This is the delivery specification for Batch 6 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: remove or retire Jekyll/Ruby build artifacts, update docs, rerun final verification, and close the migration.

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
| 6.1 | planned | Confirm the Batch 1 Jekyll responsibility inventory against the Batch 5 deploy results before removing files. |
| 6.2 | planned | Confirm Batch 5 recorded a successful live Actions artifact deploy before starting removal work. |
| 6.3 | planned | Remove Ruby/Jekyll build files and wrappers after replacement behavior is verified; record any retained item with owner and removal reason. |
| 6.4 | planned | Retarget `bin/public-site-preview` to the verified static build-and-serve path. |
| 6.5 | planned | Remove `bin/public-site-preview-static` after the default preview command serves static output, or retain it with a documented owner and reason. |
| 6.6 | planned | Add scoped workflow path filters after live static deploy parity is proven, then verify public-site-relevant commits trigger the workflow and unrelated commits do not. |
| 6.7 | planned | Update docs, setup commands, workflow docs, and source-organisation docs to make the static builder the only public build path and remove stale Jekyll/Ruby/Liquid assumptions. |
| 6.8 | planned | Run final verification gate and stale-reference scans. |
| 6.9 | planned | Close out the parent request, implementation tracker, and batch documents with verification results, retained risks, and follow-on work. |

## completed verification

- Not started.

## follow-on tasks

- Batch 6 creates follow-on requests only for cleanup that is deliberately outside the production migration.

## batch close

- Set this batch status and front matter `ui_status` to `done`.
- Set [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan) status to `done`.
- Update [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) with closeout status and final verification results.
