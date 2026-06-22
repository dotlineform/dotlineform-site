---
doc_id: scripts-project-state-report
title: Project State Report
added_date: 2026-04-27
last_updated: 2026-06-22
parent_id: studio
viewable: true
---
# Project State Report

Script:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py
```

## Purpose

This script reports source project folders and primary source images that are not represented by `studio/data/canonical/catalogue/works.json`.

It is meant to replace ad hoc catalogue/source-folder comparisons when deciding what still needs to be imported.

## Inputs

- `studio/data/canonical/catalogue/works.json`
- `studio/data/canonical/catalogue/work_details/`, only to identify detail subfolder paths to skip
- `DOTLINEFORM_PROJECTS_BASE_DIR` from `var/local/site.env`, resolving to a folder that contains `projects/`

Do not pass `--projects-base-dir` during normal local runs. Set `DOTLINEFORM_PROJECTS_BASE_DIR` in `var/local/site.env` instead.
Cloud/Codespaces runs can provide the same key through platform environment configuration.

## Output

Default preview:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py
```

Write the persistent Markdown report:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py --write
```

Include source subfolders in the report:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py --write --include-subfolders
```

The write target is:

```text
var/studio/reports/project-state.md
```

The generated Markdown is a local operational report snapshot.
It is not Docs Viewer source and does not use Docs Viewer front matter.

## Scan Boundary

The report compares only primary work image data:

- `Works.project_folder`
- `Works.project_filename`

Work details are out of scope. Known `details_subfolder` paths from per-work detail-source files and folders named `details` are skipped.

By default, the report scans every direct `/projects/<project_folder>` folder. Image mismatch sections still inspect only direct image files inside those folders.

With `--include-subfolders`, the report also includes `/projects/<project_folder>/<sub-folder>` directories. For image mismatches, the report lists direct source images only when their containing folder already matches a `Works.project_folder`. Folders that do not match `works.json` are reported once in the folder section with their direct image counts, which may be zero for non-image media folders.

## Studio Use

`/studio/project-state/` runs the same report builder through `POST /studio/api/catalogue/project-state-report` on the local Studio app server.
The page's `include sub-folders` checkbox sends `include_subfolders: true`; the default request sends `false`.
The local app adapter reads `DOTLINEFORM_PROJECTS_BASE_DIR` through the served repo's local environment contract, then reuses the script's report builder and Studio activity logging behavior.
The page opens the latest report through `POST /studio/api/catalogue/project-state-open-report`, which is restricted to the Project State report under `var/studio/reports/`.

## Related References

- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Source Utilities](/docs/?scope=studio&doc=scripts-catalogue-source)
