---
doc_id: dev-home
title: Dev Home
added_date: 2026-04-19
last_updated: 2026-07-15
summary: Repo-wide development workflow, testing, environment, and deployment references.
parent_id: ""
viewable: true
---
# Dev Home

## Repository Shape

- `site/` is the checked public GitHub Pages artifact. There is no deploy-time copy/build step.
- [Studio](/docs/?scope=studio&doc=studio) edits catalogue/editorial source and builds public catalogue payloads.
- [Analytics](/docs/?scope=studio&doc=analytics) owns canonical tag workflows and hosts Data Sharing.
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer) renders/manages document scopes; public routes reuse site-owned assets/config.
- [Admin](/docs/?scope=studio&doc=admin) runs/reviews operational audits, checks, activity, and test summaries.
- `processing/` is a separate Java/Processing project with its own Docs Viewer scope and future lifecycle; repository co-location does not make it a website module.

## Work Lifecycle

- [Development Workflow](/docs/?scope=studio&doc=development-workflow) — concept, architecture, roadmap, delivery, verification, documentation, closeout.
- [Development Checklist](/docs/?scope=studio&doc=development-checklist) — cross-cutting implementation guardrails.
- [Change Requests](/docs/?scope=studio&doc=change-requests) — feature parents and bounded active deliveries.
- [Testing](/docs/?scope=studio&doc=testing) and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks) — select evidence and profiles.

## Structure And Environment

- [Architecture](/docs/?scope=studio&doc=architecture) — cross-app structure and ownership.
- [Configuration Map](/docs/?scope=studio&doc=config-files-inventory) — find checked config/registry owners.
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) — public, local-app, shared, generated, and output roots.
- [Local Setup](/docs/?scope=studio&doc=local-setup) — local runners/environment.
- [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies) — dependency sources and workflow-specific tools.
- [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments) — `.codex`/Codespaces bootstrap.
- [GitHub Actions](/docs/?scope=studio&doc=github-actions) — current public-site validation/deploy workflow.

## Documentation Shape

Studio-scope Markdown is flat under `docs-viewer/source/studio/`; `parent_id` builds the navigation tree. Treat code/config/tests as exact authority and these docs as maps to capabilities, methodology, extension points, and known gaps.
