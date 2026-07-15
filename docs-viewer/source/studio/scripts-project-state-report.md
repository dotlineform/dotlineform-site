---
doc_id: scripts-project-state-report
title: Project State Report
added_date: 2026-04-27
last_updated: 2026-07-15
parent_id: studio
viewable: true
---
# Project State Report

## Commands

Preview or write the report:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py --write
```

Include direct subfolders in folder discovery:

```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/project_state_report.py --write --include-subfolders
```

The persistent output is `var/studio/reports/project-state.md`.

## Boundary

The report compares canonical primary Work media references with files below the `projects` root resolved from `DOTLINEFORM_PROJECTS_BASE_DIR`.

It identifies unrepresented folders/images, unresolved catalogue paths, and incomplete Work media references. Known Work-detail subfolders are excluded so detail images are not treated as candidate primary Works.

The report is a local operational snapshot. It is not canonical source, Docs Viewer source, or an instruction to delete files automatically.

## Shared Use

`/studio/project-state/` calls the same builder through the Local Studio API and can open the resulting Markdown file through a separately confined local capability. The [Project State](/docs/?scope=studio&doc=project-state-page) page documents that operator workflow.

`studio/services/catalogue/project_state_report.py` owns scanning and report construction. Pipeline configuration owns the projects subpath; catalogue source helpers own Work loading.
