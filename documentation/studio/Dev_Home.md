---
draft: false
doc_id: d-20260419-000000-d2e47b
title: Dev Home
added_date: "2026-04-19 00:00:00"
last_updated: "2026-11-18"
summary: Repo-wide development workflow, testing, environment, and deployment references.
parent_id: ""

---
# Dev Home

Start with the [Site Workflow Guide](../guide/README.md) for how the site fits together and how to publish and deploy changes.

## Project References

- [Site](Site.md) covers the public website, static preview and Pages deployment.
- [Studio](Studio.md) covers Catalogue authoring and Refresh.
- [Docs Viewer](Docs_Viewer.md) covers the public reader, Working, Publish and package review.
- [Processing](Processing.md) covers repository hosting and integration for the separate Java/Processing project.

## Work Lifecycle

- [Change the system safely](../guide/Change_The_System_Safely.md) — trace a change from its owner through verification and recovery.
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

Maintain Studio development and maintenance references under `documentation/studio/`. Keep each document's `doc_id` stable and use `parent_id` for its place in the documentation tree. Use the owning code and configuration for exact behaviour and the references here to find the relevant owner.
