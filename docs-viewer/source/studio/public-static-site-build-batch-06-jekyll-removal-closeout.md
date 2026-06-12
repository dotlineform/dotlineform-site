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

- This batch must be re-planned after Batch 1 closes and after Batch 5 proves the static deploy path.
- Do not remove Jekyll-era files before replacement behavior is verified.
- Any retained Jekyll-era naming must have a non-Jekyll owner and a removal reason.
- The current Jekyll local preview stops being supported only in this batch, after Batch 5 has recorded a successful live static Actions artifact deploy.
- If Batch 5 has not recorded the production cutover, this batch is blocked.
- Retarget `bin/public-site-preview` to the verified static build-and-serve path rather than removing the operator-facing preview command.

## Deliverables

- Removal of `Gemfile`, `Gemfile.lock`, `.ruby-version`, Jekyll-specific `_config.yml` usage, `_layouts/`, `_includes/`, Jekyll collection stubs, and wrappers that invoke Bundler or Jekyll. Any retained item requires a non-Jekyll owner and removal reason in the closeout.
- Updated operator docs and setup docs for the static builder and preview path.
- Final verification results and closeout notes.
- Parent request and tracker status updates.
- A local-preview transition note naming that `bin/public-site-preview` now serves the static artifact, the removal or retained owner of `bin/public-site-preview-static`, and when the old Jekyll preview stopped being supported.

## Implementation and policy guidance

- Prefer direct reference updates over compatibility shims.
- Do not leave Ruby/Jekyll as a documented public-site build path.
- Keep generated site output untracked on `main`.
- Retarget old local preview wrappers only after the static preview command is documented and verified.

## Proposed verification set

- Full static public-site verification gate.
- Source/docs scans for stale Ruby, Bundler, Jekyll, Liquid, `_config.yml`, `_layouts`, and `_includes` command assumptions.
- Artifact surface and source-leak audits after removals.
- Browser smoke checks for the final static artifact.
- Changed-file sanitization scan for changed scripts, workflows, config, and docs.

## Tasks

### Batch 6: Jekyll Removal and Closeout

| ID | status | action |
| --- | --- | --- |
| 6.1 | planned | Re-plan this batch from Batch 1 Jekyll responsibility inventory and Batch 5 deploy results. |
| 6.2 | planned | Confirm Batch 5 recorded a successful live Actions artifact deploy; block this batch if cutover is incomplete. |
| 6.3 | planned | Remove Ruby/Jekyll build files and wrappers after replacement behavior is verified; record any retained item with owner and removal reason. |
| 6.4 | planned | Retarget `bin/public-site-preview` to the verified static build-and-serve path. |
| 6.5 | planned | Remove `bin/public-site-preview-static` after the default preview command serves static output, or retain it with a documented owner and reason. |
| 6.6 | planned | Update docs, setup commands, workflow docs, and source-organisation docs to make the static builder the only public build path. |
| 6.7 | planned | Run final verification gate and stale-reference scans. |
| 6.8 | planned | Close out the parent request, implementation tracker, and batch documents with verification results, retained risks, and follow-on work. |

## completed verification

- Not started.

## follow-on tasks

- Batch 6 creates follow-on requests only for cleanup that is deliberately outside the production migration.

## batch close

- Set this batch status and front matter `ui_status` to `done`.
- Set [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan) status to `done`.
- Update [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build) with closeout status and final verification results.
