---
doc_id: tasks-template
title: Tasks Template
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: ""
parent_id: dev-home
viewable: true
---
# [Implementation Name]

This is the tracker for implementing [link to request document].

## Status

### just done

- bullet points to state what was delivered in the last completed task
- only include older tasks where context is relevant and important
- refresh this section at the completion of a task

### steer for next task

- bullet points stating:
    - what is the next task to be delivered
    - what concerns or risks need to be addressed
    - what technical details are important to be considered

### baseline verification set

State the verification set for before and after extraction slices, to be run only when the touched area warrants it.

For example:

- Core checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick`.
- Docs Viewer smoke checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`.
- Local Studio smoke checks that prove Studio links and integration still work.
- Public Jekyll build check: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`.
- Public scope checks for `/library/` and `/analysis/` when scope registration, generated payload locations, route shells, or public Docs Viewer runtime behavior changes.
- Focused Python, Ruby, and JavaScript syntax/import checks for moved files.
- Focused tests for Docs Viewer management write APIs, source/scope config, New Scope, generated-data builders, and local service launchers when those areas move.

Codex sandbox note: local service, browser, and temporary localhost checks will need elevated permissions even when the product code is healthy.

### general steer

- This section should highlight key points from the original proposal.
- Development guidances in `development-workflow.md` need to be followed or called out if there is conflict with the implementation.
- Prefer direct reference updates over compatibility shims for old paths.
- Use sibling docs for large inventories, target layouts, contract tables, or path maps so this tracker remains a concise sequential task list.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | description + key deliverables |

The last tasks should close out the implementation:

- Update command docs, local setup docs, Docs Viewer portable setup, runtime boundary docs, source organisation docs, config docs, and script docs to describe any changed boundary, service config, route ownership, runner behavior, service ownership, and retired current-state assumptions.
- confirm any removed paths or artifacts are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic.
- Run the agreed final verification set: quick profile, Docs Viewer smoke profile, focused Local Studio integration smokes, public Jekyll build, public scope checks, syntax/import checks, and any changed-doc link/path checks.
- Close out the parent request and this tracker:
    - update statuses,
    - summarize moved paths,
    - record verification results and generated payload status,
    - copy durable decisions/contracts into permanent owning docs,
    - note remaining risks or follow-on work before these request docs are marked 'done'.
