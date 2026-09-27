---
draft: false
doc_id: d-20260419-000000-d2e47b
title: Dev Home
added_date: "2026-04-19 00:00:00"
last_updated: "2026-09-03 21:37:12"
summary: Repo-wide development workflow, testing, environment, and deployment references.
parent_id: ""

---
# Dev Home

## Repository Shape

- `site/` is the checked public GitHub Pages artifact. There is no deploy-time copy/build step.
- [Site](Site.md) owns the public catalogue, route, shell, design, and runtime documentation.
- [Studio](Studio.md) edits catalogue/editorial source and builds public catalogue payloads.
- [Docs Viewer](Docs_Viewer.md) renders/manages document scopes; public routes reuse site-owned assets/config.
- [Processing](Processing.md) owns repository hosting and integration for the separate Java/Processing project; its own Docs Viewer scope retains conceptual and technical documentation.

## Work Lifecycle

- [Development Workflow](Development_Workflow.md) — concept, architecture, feature delivery, verification, documentation, closeout.
- [Development Checklist](Development_Checklist.md) — cross-cutting implementation guardrails.
- [Planned Features](Planned_Features.md) — short-term feature direction and bounded deliveries.
- [Testing](Testing.md) and [Run Checks](Run_Checks.md) — select evidence and profiles.

## Structure And Environment

- [Architecture](System_Architecture.md) — cross-app structure and ownership.
- [Configuration Map](Configuration_Map.md) — find checked config/registry owners.
- [Source Tree Ownership](Source_Tree_Ownership.md) — public, local-app, shared, generated, and output roots.
- [Local Setup](Local_Setup.md) — local runners/environment.
- [Runtime Dependencies](Runtime_Dependencies.md) — dependency sources and workflow-specific tools.
- [Cloud Environments](Cloud_Environments.md) — `.codex`/Codespaces bootstrap.
- [GitHub Actions](GitHub_Actions.md) — current public-site validation/deploy workflow.

## Documentation Shape

Studio-scope Markdown is flat under `docs-viewer/scopes/studio/source/`; `parent_id` builds the navigation tree. Treat current code and configuration as executable authority, focused tests as evidence, and these docs as maps to capabilities, methodology, extension points, and known gaps.
