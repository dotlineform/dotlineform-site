---
doc_id: risk-evidence-pack-metrics
title: Risk Evidence Pack Metrics
added_date: 2026-06-08
last_updated: 2026-06-08
parent_id: admin
---
# Risk Evidence Pack Metrics

This document lists the metrics currently emitted by `admin-app/checks/risk_evidence_pack.py`.

The risk evidence pack writes local run artifacts under `var/admin/risk/runs/<run-id>/`.
The source contract is [Risk Evidence Pack](/docs/?scope=studio&doc=risk-evidence-pack).

## Reporting Artifacts

These are the human-facing reports that are currently produced, or could be produced, from the collected metrics.
Current run artifacts are written directly by the evidence pack.
Derived reports can be rendered later from the JSON artifacts without rerunning the collectors.

| Report | Status | Metrics | Source artifact | Example report shape |
| --- | --- | --- | --- | --- |
| Files | derivable | filename, size, line count, family | `static-metrics.json` `largest_files`; `static-metrics.json` `by_family`; `script-family-inventory.json` `largest_files` | Terminal-style rows sorted by line count: `lines size path`, e.g. large JavaScript files under `docs-viewer/runtime/js/`. |
| Source totals | current summary / derivable detail | file count, line count, byte count | `static-metrics.json` `totals` | Compact summary by selected app root: total files, total lines, total bytes. |
| Source family totals | derivable | family, file count, line count, byte count | `static-metrics.json` `by_family` | Ranked table of source families by line count or byte size. |
| Extension mix | derivable | extension, file count | `static-metrics.json` `by_extension` | Count table for `.js`, `.py`, `.md`, `.json`, and other included extensions. |
| Largest source files | derivable | path, line count, byte count | `static-metrics.json` `largest_files` | Top-N source/config files by line count, useful for maintenance review. |
| Import/export overview | current summary / derivable detail | scanned file count, import count, export count, cross-app reference count | `static-metrics.json` `import_export.totals` | Compact dependency-shape summary for JavaScript, Python, and Ruby files. |
| Import/export by family | derivable | family, scanned files, imports, exports | `static-metrics.json` `import_export.by_family` | Ranked table showing which repo families carry the most import/export activity. |
| Cross-app references | derivable | source path, dependency specifier | `static-metrics.json` `import_export.cross_app_references` | Review list of dependencies crossing app or public asset JavaScript boundaries. |
| Per-file dependencies | derivable | path, family, imports, exports, dependency specifiers | `static-metrics.json` `import_export.files` | File-level dependency table for targeted ownership review. |
| Static search findings | current summary / derivable detail | fixture name, match count, matched path count, sampled path, line, excerpt | `static-searches.json` `patterns` | Fixture report grouped by search rule, with sampled excerpts for review. |
| TODO / FIXME inventory | derivable | marker count, matched file count, sampled path, line, excerpt | `static-searches.json` `todo_markers` | Action-marker report for `TODO`, `FIXME`, `HACK`, and `XXX`. |
| Browser state and storage inventory | derivable | match count, matched path count, sampled path, line, excerpt | `static-searches.json` `broad_browser_state`; `static-searches.json` `browser_storage` | Browser-global state and storage usage report. |
| Local URL inventory | derivable | match count, matched path count, sampled path, line, excerpt | `static-searches.json` `local_service_url` | Hard-coded localhost URL report. |
| Generated path reference inventory | derivable | match count, matched path count, sampled path, line, excerpt | `static-searches.json` `generated_path_reference` | Report of source references to generated payload roots. |
| Legacy wording inventory | derivable | match count, matched path count, sampled path, line, excerpt | `static-searches.json` `legacy_or_retired` | Review list for legacy, retired, deprecated, or compatibility wording. |
| Negative test assertion inventory | derivable | match count, matched path count, sampled path, line, excerpt | `static-searches.json` `negative_test_assertion_inventory` | Scoped test review report for negative or stale-behavior assertions. |
| Data Sharing stale generated-docs path inventory | derivable | match count, matched path count, sampled path, line, excerpt | `static-searches.json` `data_sharing_generated_docs_stale_path_inventory` | Scoped report for stale generated-docs path and metadata terms. |
| Generated payload inventory | current summary / derivable detail | payload file count, byte count, root | `generated-payloads.json` `totals`; `generated-payloads.json` `by_root` | Generated JSON payload count and size summary by root. |
| Largest generated payloads | derivable | path, byte count, JSON validity, top-level JSON type, top-level keys, array item count | `generated-payloads.json` `largest_payloads` | Top-N generated JSON files by byte size with shape notes. |
| JSON shape report | derivable | path, JSON validity, parse error, top-level type, keys, item count | `generated-payloads.json` `largest_payloads` | Payload-shape review for schema drift or unexpectedly large arrays/objects. |
| Script family inventory | current summary / derivable detail | family, Python file count, Ruby file count, line count, largest file | `script-family-inventory.json` `by_family` | Python/Ruby script-family table ranked by line count. |
| Largest script files | derivable | path, family, line count | `script-family-inventory.json` `largest_files` | Top-N Python/Ruby files by line count. |
| Git churn by family | derivable | family, touch count | `git-history.json` `by_family` | Recent edit-concentration table by family. |
| Top touched files | derivable | path, touch count | `git-history.json` `top_files` | Recent churn table for files touched most often in the configured history window. |
| JavaScript inventory guardrail | current summary / derivable detail | score mode, file count, line count, maintenance score, overlap risk, touches | `javascript-inventory-guardrail.json` | Docs Viewer JavaScript ownership or maintenance-risk report, depending on score mode. |
| Runtime profile results | current optional artifact / derivable detail | profile, exit code, summary path, Lighthouse status, Lighthouse reason | `runtime-checks.json` | Runtime evidence report linking each allowlisted smoke/check profile to its summary. |
| Subjective notes validation | current optional artifact / derivable detail | source path, destination path, record count, invalid line numbers | `subjective-notes.jsonl` plus subjective-notes metadata in `summary.json` | Operator/reviewer note validation report. |
| Run provenance | current artifact | command name, command text, working directory, start time, exit code, duration, stdout path, stderr excerpt | `commands.json` | Command execution ledger for command-backed producers. |
| Run manifest | current artifact | app, area, command version, created time, history window, omitted evidence, operator, repo commit, run id, selected evidence | `manifest.json` | Run identity and scope report. |
| Evidence summary | current artifact | artifact, status, compact summary, warnings | `summary.json`; `summary.md` | Human-readable run summary with one bullet per evidence artifact. |

Example file report shape:

```text
   lines      size  path
     997       36K  ./docs-viewer/runtime/js/docs-viewer-management.js
     905       32K  ./docs-viewer/runtime/js/docs-viewer-app-runtime.js
     562       28K  ./docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js
```

## Metric Fields

| Artifact | Metric | Description |
| --- | --- | --- |
| `manifest.json` | `app` | Selected app scope for the run: `public-site`, `studio`, `admin`, `analytics`, `docs-viewer`, or `all`. |
| `manifest.json` | `area` | Operator-provided risk area slug used to label the evidence run. |
| `manifest.json` | `command_version` | Evidence runner command contract version. |
| `manifest.json` | `created_at_utc` | UTC timestamp for the run directory creation. |
| `manifest.json` | `history_window` | Git history window used by the touch-count producer. |
| `manifest.json` | `omitted_evidence` | Evidence categories intentionally omitted from the run, such as runtime checks, subjective notes, route exposure, or compact generated summaries. |
| `manifest.json` | `operator` | Local operator name from the runtime environment. |
| `manifest.json` | `repo_commit` | Current Git commit hash when it can be resolved. |
| `manifest.json` | `run_id` | Stable local identifier for the evidence run. |
| `manifest.json` | `selected_evidence` | Sorted list of artifact families collected in the run. |
| `commands.json` | `name` | Recorded command name for command-backed producers. |
| `commands.json` | `command` | Command argv list used by a command-backed producer. |
| `commands.json` | `command_text` | Shell-quoted command text for human review. |
| `commands.json` | `cwd` | Working directory for the recorded command. |
| `commands.json` | `started_at_utc` | UTC timestamp for command start. |
| `commands.json` | `exit_code` | Process exit code for the recorded command. |
| `commands.json` | `duration_seconds` | Elapsed command runtime in seconds. |
| `commands.json` | `stdout_path` | Artifact path where command stdout was saved, when applicable. |
| `commands.json` | `stderr_excerpt` | Truncated stderr excerpt for failed or noisy commands. |
| `static-metrics.json` | `roots` | Source roots selected for the requested app scope. |
| `static-metrics.json` | `totals.files` | Count of source/config files included in static metrics after exclusions. |
| `static-metrics.json` | `totals.lines` | Total line count across included source/config files. |
| `static-metrics.json` | `totals.bytes` | Total byte size across included source/config files. |
| `static-metrics.json` | `by_extension` | File counts grouped by extension. |
| `static-metrics.json` | `by_family.files` | Included source/config file count grouped by repo family. |
| `static-metrics.json` | `by_family.lines` | Included source/config line count grouped by repo family. |
| `static-metrics.json` | `by_family.bytes` | Included source/config byte size grouped by repo family. |
| `static-metrics.json` | `largest_files.path` | Path for each largest included source/config file. |
| `static-metrics.json` | `largest_files.lines` | Line count for each largest included source/config file. |
| `static-metrics.json` | `largest_files.bytes` | Byte size for each largest included source/config file. |
| `static-metrics.json` | `import_export.totals.files` | Count of JavaScript, Python, and Ruby files scanned for import/export evidence. |
| `static-metrics.json` | `import_export.totals.imports` | Total import, `from`, `require`, or `load` statements found in scanned files. |
| `static-metrics.json` | `import_export.totals.exports` | Total JavaScript export statements found in scanned files. |
| `static-metrics.json` | `import_export.totals.cross_app_references` | Count of dependencies that reference another app or public asset JavaScript family. |
| `static-metrics.json` | `import_export.by_family.files` | Import/export scanned file count grouped by repo family. |
| `static-metrics.json` | `import_export.by_family.imports` | Import count grouped by repo family. |
| `static-metrics.json` | `import_export.by_family.exports` | Export count grouped by repo family. |
| `static-metrics.json` | `import_export.cross_app_references.path` | File path containing a cross-app dependency reference. |
| `static-metrics.json` | `import_export.cross_app_references.dependency` | Dependency specifier that matched a cross-app or public asset JavaScript marker. |
| `static-metrics.json` | `import_export.files.path` | Path for each import/export scanned file. |
| `static-metrics.json` | `import_export.files.family` | Repo family assigned to each import/export scanned file. |
| `static-metrics.json` | `import_export.files.imports` | Import count for each scanned file. |
| `static-metrics.json` | `import_export.files.exports` | Export count for each scanned file. |
| `static-metrics.json` | `import_export.files.dependencies` | Up to 50 parsed dependency specifiers for each scanned file. |
| `static-searches.json` | `patterns.name` | Static-search fixture name. |
| `static-searches.json` | `patterns.pattern` | Regular expression used for the fixture. |
| `static-searches.json` | `patterns.include_prefixes` | Optional path prefixes that constrain a fixture to a narrower source set. |
| `static-searches.json` | `patterns.match_count` | Total regex match count for the fixture. |
| `static-searches.json` | `patterns.matched_path_count` | Count of distinct files matched by the fixture. |
| `static-searches.json` | `patterns.matches.path` | File path for a sampled match. |
| `static-searches.json` | `patterns.matches.line` | Line number for a sampled match. |
| `static-searches.json` | `patterns.matches.excerpt` | Truncated source excerpt for a sampled match. |
| `static-searches.json` | `todo_markers` | Search fixture for `TODO`, `FIXME`, `HACK`, and `XXX` markers. |
| `static-searches.json` | `broad_browser_state` | Search fixture for broad browser-global state/config references. |
| `static-searches.json` | `browser_storage` | Search fixture for `localStorage` and `sessionStorage` references. |
| `static-searches.json` | `local_service_url` | Search fixture for hard-coded `127.0.0.1` or `localhost` URLs with ports. |
| `static-searches.json` | `generated_path_reference` | Search fixture for references to generated payload roots. |
| `static-searches.json` | `legacy_or_retired` | Search fixture for legacy, retired, deprecated, or compatibility wording. |
| `static-searches.json` | `negative_test_assertion_inventory` | Scoped search fixture for negative or stale-behavior assertions in test trees. |
| `static-searches.json` | `data_sharing_generated_docs_stale_path_inventory` | Scoped search fixture for stale generated-docs path and metadata terms in Data Sharing and docs import/export surfaces. |
| `generated-payloads.json` | `roots` | Generated JSON payload roots scanned by the producer. |
| `generated-payloads.json` | `totals.files` | Count of generated JSON payload files found. |
| `generated-payloads.json` | `totals.bytes` | Total byte size of generated JSON payload files. |
| `generated-payloads.json` | `by_root.files` | Generated JSON payload count grouped by root. |
| `generated-payloads.json` | `by_root.bytes` | Generated JSON byte size grouped by root. |
| `generated-payloads.json` | `largest_payloads.path` | Path for each largest generated JSON payload. |
| `generated-payloads.json` | `largest_payloads.bytes` | Byte size for each largest generated JSON payload. |
| `generated-payloads.json` | `largest_payloads.valid_json` | Whether a generated payload parsed as JSON. |
| `generated-payloads.json` | `largest_payloads.error` | JSON parse or read error when a payload is invalid. |
| `generated-payloads.json` | `largest_payloads.top_level_type` | Parsed top-level JSON type. |
| `generated-payloads.json` | `largest_payloads.top_level_keys` | Up to 30 top-level object keys for object payloads. |
| `generated-payloads.json` | `largest_payloads.items` | Item count for array payloads. |
| `script-family-inventory.json` | `roots` | Python/Ruby script-family roots scanned by the producer. |
| `script-family-inventory.json` | `excluded_path_parts` | Path parts excluded from the script inventory, including tests, smokes, and caches. |
| `script-family-inventory.json` | `totals.files` | Count of included Python and Ruby files. |
| `script-family-inventory.json` | `totals.lines` | Total line count across included Python and Ruby files. |
| `script-family-inventory.json` | `totals.python` | Count of included Python files. |
| `script-family-inventory.json` | `totals.ruby` | Count of included Ruby files. |
| `script-family-inventory.json` | `by_family.files` | Included Python/Ruby file count grouped by script family. |
| `script-family-inventory.json` | `by_family.lines` | Included Python/Ruby line count grouped by script family. |
| `script-family-inventory.json` | `by_family.python` | Included Python file count grouped by script family. |
| `script-family-inventory.json` | `by_family.ruby` | Included Ruby file count grouped by script family. |
| `script-family-inventory.json` | `by_family.largest_file` | Largest file path and line count inside each script family. |
| `script-family-inventory.json` | `largest_files.path` | Path for each largest included Python/Ruby file. |
| `script-family-inventory.json` | `largest_files.family` | Script family for each largest included Python/Ruby file. |
| `script-family-inventory.json` | `largest_files.lines` | Line count for each largest included Python/Ruby file. |
| `git-history.json` | `since` | Git history window used for the touch-count scan. |
| `git-history.json` | `status` | Producer status, usually `passed` or `failed`. |
| `git-history.json` | `commit_count` | Count of commits touching the selected app roots inside the history window. |
| `git-history.json` | `by_family.touches` | File touch count grouped by repo family. |
| `git-history.json` | `top_files.path` | File path for each frequently touched file. |
| `git-history.json` | `top_files.touches` | Touch count for each frequently touched file. |
| `javascript-inventory-guardrail.json` | `score_mode` | Indicates whether the guardrail used the current unscored Docs Viewer inventory or the older scored inventory shape. |
| `javascript-inventory-guardrail.json` | `totals.files` | Count of JavaScript inventory rows parsed. |
| `javascript-inventory-guardrail.json` | `totals.lines` | Total line count across inventory rows. |
| `javascript-inventory-guardrail.json` | `totals.maintenance_2_files` | Count of rows with maintenance score at least 2 when using a scored inventory. |
| `javascript-inventory-guardrail.json` | `totals.maintenance_2_lines` | Total line count for rows with maintenance score at least 2 when using a scored inventory. |
| `javascript-inventory-guardrail.json` | `totals.maintenance_2_file_percent` | Percentage of inventory rows with maintenance score at least 2. |
| `javascript-inventory-guardrail.json` | `totals.maintenance_2_line_percent` | Percentage of inventory lines in rows with maintenance score at least 2. |
| `javascript-inventory-guardrail.json` | `totals.maintenance_2_overlap_files` | Count of maintenance-risk rows that also have structural, performance, or architectural overlap risk. |
| `javascript-inventory-guardrail.json` | `files_by_maintenance` | Count of inventory rows grouped by maintenance score. |
| `javascript-inventory-guardrail.json` | `lines_by_maintenance` | Line count grouped by maintenance score. |
| `javascript-inventory-guardrail.json` | `maintenance_2_by_family` | Files, lines, and recent touches for high-maintenance rows grouped by family. |
| `javascript-inventory-guardrail.json` | `maintenance_2_overlap_files` | Rows with maintenance score at least 2 and overlapping structural, performance, or architectural score at least 2. |
| `javascript-inventory-guardrail.json` | `top_maintenance_risk_files` | Highest-ranked maintenance-risk rows by line count, touch count, risk, and path. |
| `runtime-checks.json` | `status` | Runtime evidence status: `omitted`, `passed`, `failed`, or `deferred`. |
| `runtime-checks.json` | `profiles.profile` | Allowlisted runtime check profile requested. |
| `runtime-checks.json` | `profiles.exit_code` | Exit code from the check-run profile command. |
| `runtime-checks.json` | `profiles.summary_path` | Summary path for the check-run profile, when produced. |
| `runtime-checks.json` | `lighthouse.status` | Lighthouse hook status, currently omitted or deferred. |
| `runtime-checks.json` | `lighthouse.reason` | Reason the Lighthouse hook was omitted or deferred. |
| `subjective-notes.jsonl` | `status` | Subjective-notes copy/validation status. |
| `subjective-notes.jsonl` | `source` | Source JSONL path copied into the run. |
| `subjective-notes.jsonl` | `path` | Destination JSONL path inside the run directory. |
| `subjective-notes.jsonl` | `records` | Count of non-empty subjective-note records copied. |
| `subjective-notes.jsonl` | `invalid_lines` | Line numbers that are not valid JSON. |
| `summary.json` | `status` | Overall evidence status, failed when any evidence item is failed or deferred. |
| `summary.json` | `evidence.artifact` | Artifact name represented in the summary. |
| `summary.json` | `evidence.status` | Status for each summarized artifact. |
| `summary.json` | `evidence.summary` | Human-readable compact metric summary for each artifact. |
| `summary.json` | `warnings` | Run warnings derived from failed or deferred producers. |
| `summary.md` | Evidence bullets | Markdown rendering of the compact artifact status and summary metrics. |
