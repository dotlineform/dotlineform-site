---
doc_id: site-request-report-git-history
title: Git History Report
added_date: 2026-06-09
last_updated: 2026-06-09
ui_status: draft
parent_id: site-request-admin-checks-reports
viewable: true
---
# Git History Report

This document describes a possible future report for [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports).

## Purpose

The `git-history` report would provide recent-change evidence for files selected by a checks run.

It should answer questions such as:

- which selected files changed recently
- which files have high recent churn
- which selected files have not changed in a long time
- which reports or file profiles should show recent commit context

## Inputs

- selected scope, family, area, and route filters from the run manifest
- selected files resolved through `target_map_resolver.py`
- report options such as history window, maximum commits per file, or since date

Possible options:

| Option | Purpose |
| --- | --- |
| `since` | Git revision or date window, such as `90 days ago`. |
| `max_commits_per_file` | Maximum commit samples to keep for each file. |

## Output

Artifacts:

```text
var/admin/checks/<run-id>/git-history/
  report.json
  report.md
  report.csv
```

Likely JSON and CSV fields:

- `path`
- `commit_count`
- `last_commit`
- `last_commit_date`
- `last_commit_subject`
- `last_commit_author`
- `recent_commits[]`

The stable join key for file-level consumers should be repo-relative `path`.

## Calculation Method

The report should resolve the selected file set first.
Then it should query git history for those paths using explicit argv lists, not shell command strings.

The implementation should keep command use narrow and deterministic, for example:

```text
git log --since <window> -- <path>
```

The producer should summarize per-file commit counts and keep bounded commit samples.

## Dependency Use

`file-profile` or other compound reports could depend on `git-history` to show recent change context for one selected file.

The `git-history` report should remain independent and reusable.
It should not know about the file-profile report.

## Non-Goals

- no blame-level line ownership in the first version
- no remote repository or hosting API calls
- no unbounded full-history scans by default
- no interpretation of change risk beyond reporting the evidence
