---
doc_id: project-state-page
title: "Project State Page"
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: studio
sort_order: 42
---
# Project State Page

Route:

- `/studio/project-state/`

This page runs the project-state report and writes `_docs_src/project-state.md`.

## Current Scope

The report compares:

- source project folders under `$DOTLINEFORM_PROJECTS_BASE_DIR/projects`
- primary work image references from `assets/studio/data/catalogue/works.json`

Work details are out of scope. The scanner skips known detail subfolders and folders named `details` so detail images are not treated as missing primary work imports.

The report currently includes:

- source folders that do not match any `Works.project_folder`
- top-level source images inside represented folders that do not match any `Works.project_folder` plus `Works.project_filename`
- catalogue folders and primary image references that no longer resolve to scanned source files
- work records missing `project_folder` or `project_filename`

The page shows the output path and summary counts after a successful run. The Markdown file is intentionally `published: false`; use the page's file-open command to inspect the source document locally.

The `include sub-folders` checkbox is off by default. When unchecked, the report scans only direct `/projects/<project_folder>` directories and their direct image files. When checked, the report also includes `/projects/<project_folder>/<sub-folder>` directories, while still skipping detail folders.

## Related References

- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
