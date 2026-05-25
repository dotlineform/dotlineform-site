---
doc_id: site-request-docs-viewer-shell-extraction-baseline
title: Docs Viewer Shell Extraction Baseline
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: draft
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10025
viewable: true
---
# Docs Viewer Shell Extraction Baseline

This document records the current integrated-tree baseline before any Docs Viewer extraction file moves.
It completes `DVSE-006` from [Docs Viewer Shell Extraction Tasks](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-tasks).

## Summary

Baseline status: passed with one expected sandbox retry.

The first `docs-viewer-smoke` run built the temporary Jekyll site successfully but failed all localhost-based browser smoke steps because the Codex sandbox could not bind temporary `127.0.0.1` servers.
The same profile passed when rerun with elevated localhost permissions.
Treat the first failed run as an environment permission result, not a product regression.

## Check Results

| Area | Command | Result | Evidence |
| --- | --- | --- | --- |
| Docs Viewer smoke profile | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke` | Passed on elevated rerun | `var/test-runs/20260524-233531/summary.md` |
| Initial sandbox smoke attempt | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke` | Failed because localhost bind was blocked by sandbox | `var/test-runs/20260524-233448/summary.md` |
| Quick profile | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick` | Passed | `var/test-runs/20260524-233607/summary.md` |
| Local Studio Docs Viewer management shell | `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_docs_viewer.py` | Passed with elevated localhost permission | Temporary `/docs/?scope=studio&doc=docs-viewer&mode=manage` route loaded and management API checks passed |
| Studio docs builder dry run | `$HOME/.rbenv/shims/bundle exec ruby docs-viewer/build/build_docs.rb --scope studio` | Passed | 316 docs emitted, 0 payload writes, 0 stale removals, 0 warnings |
| Library docs builder dry run | `$HOME/.rbenv/shims/bundle exec ruby docs-viewer/build/build_docs.rb --scope library` | Passed | 15 docs emitted, 0 payload writes, 0 stale removals, 0 warnings |
| Analysis docs builder dry run | `$HOME/.rbenv/shims/bundle exec ruby docs-viewer/build/build_docs.rb --scope analysis` | Passed with existing content warning | 3 docs emitted, 0 payload writes, 0 stale removals, 1 unresolved semantic-reference warning |
| Studio search builder dry run | `$HOME/.rbenv/shims/bundle exec ruby docs-viewer/build/build_search.rb --scope studio` | Passed | Would write 0; skipped 1; path `assets/data/search/studio/index.json` |
| Library search builder dry run | `$HOME/.rbenv/shims/bundle exec ruby docs-viewer/build/build_search.rb --scope library` | Passed | Would write 0; skipped 1; path `assets/data/search/library/index.json` |
| Analysis search builder dry run | `$HOME/.rbenv/shims/bundle exec ruby docs-viewer/build/build_search.rb --scope analysis` | Passed | Would write 0; skipped 1; path `assets/data/search/analysis/index.json` |

## Coverage

The baseline covers:

- current public Jekyll build through the `docs-viewer-smoke` `jekyll-temp-build` step
- public `/library/` and `/analysis/` read-only Docs Viewer installs
- Docs Viewer index panel, management modal, management action workflow, and HTML import browser module smokes
- current Local Studio-hosted `/docs/` management shell and `/studio/api/docs/*` management API behavior
- Python syntax, quick Python pytest set, projection contract, Studio ready-state audit, Studio config JSON, and activity contract JSON
- dry-run docs and search builders for all configured Docs Viewer scopes

## Known Baseline Notes

- Analysis docs currently report an unresolved semantic reference: `work:00638002` from `analysis/3-symbols`.
- Dry-run builders reported no generated payload drift for Studio, Library, or Analysis.
- No generated docs/search payload rebuild was manually requested as part of this task.
- Localhost/browser smokes may need elevated permissions in Codex runs because they bind temporary loopback servers.

## Handoff To DVSE-007

Use this baseline to compare the first config slice.
If `DVSE-007` changes local service config, repeat at least:

- quick profile
- focused config parse or source config validation
- Docs Viewer smoke profile if public config URLs or generated data references change
- focused Local Studio link/config check if Studio starts rendering configured Docs Viewer service links
