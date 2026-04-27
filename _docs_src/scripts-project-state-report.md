---
doc_id: scripts-project-state-report
title: "Project State Report"
added_date: 2026-04-27
last_updated: 2026-04-27
parent_id: scripts
sort_order: 65
---
# Project State Report

Script:

```bash
./scripts/project_state_report.py
```

## Purpose

This script reports source project folders and primary source images that are not represented by `assets/studio/data/catalogue/works.json`.

It is meant to replace the old habit of using `data/works.xlsx` to infer what still needs to be imported.

## Inputs

- `assets/studio/data/catalogue/works.json`
- `assets/studio/data/catalogue/work_details.json`, only to identify detail subfolders to skip
- `$DOTLINEFORM_PROJECTS_BASE_DIR/projects`

Do not pass `--projects-base-dir` during normal local or cloud runs. Set `DOTLINEFORM_PROJECTS_BASE_DIR` instead.

## Output

Default preview:

```bash
./scripts/project_state_report.py
```

Write the persistent Markdown report:

```bash
./scripts/project_state_report.py --write
```

Include source subfolders in the report:

```bash
./scripts/project_state_report.py --write --include-subfolders
```

The write target is:

```text
_docs_src/project-state.md
```

The generated document has `published: false`, so it is a local project-state artifact rather than a published Studio docs page.

## Scan Boundary

The report compares only primary work image data:

- `Works.project_folder`
- `Works.project_filename`

Work details are out of scope. Known detail subfolders from `work_details.json` and folders named `details` are skipped.

By default, the report scans every direct `/projects/<project_folder>` folder. Image mismatch sections still inspect only direct image files inside those folders.

With `--include-subfolders`, the report also includes `/projects/<project_folder>/<sub-folder>` directories. For image mismatches, the report lists direct source images only when their containing folder already matches a `Works.project_folder`. Folders that do not match `works.json` are reported once in the folder section with their direct image counts, which may be zero for non-image media folders.

## Studio Use

`/studio/project-state/` runs the same script through `POST /catalogue/project-state-report` on the local Catalogue Write Server. The page's `include sub-folders` checkbox sends `include_subfolders: true`; the default request sends `false`.

## Related References

- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
