---
doc_id: testing
title: Testing
added_date: 2026-05-01
last_updated: "2026-05-06 20:49"
parent_id: ""
sort_order: 135
---
# Testing

This repo uses lightweight, opt-in checks rather than a mandatory full test suite.

The goal is to give Codex a standard place to put repeatable checks, run logs, and verification notes when a change is too broad for manual review alone.

## When To Use Automated Checks

Run automated checks when the blast radius is large enough that manual checks are likely to miss something.

Good candidates:

- build planners and artifact selection
- schema or config contracts
- generated docs/search payloads
- source-data validation
- local write-server behavior
- Studio route behavior that can be smoke-tested reliably

Manual checks are still enough for small copy changes, narrow docs edits, and visual judgment that depends on feel, layout, or mobile ergonomics.

## Structure

- `tests/python/`
  Deterministic Python checks.
- `tests/smoke/`
  Focused browser smoke scripts.
- `tests/fixtures/`
  Small stable fixtures, only where existing repo data is not safe or sufficient.
- `var/test-runs/`
  Local check logs and summaries. This path is ignored by git.

## Runner

Use `./scripts/run_checks.py` to run one or more check profiles and write a local run summary.

Examples:

```bash
./scripts/run_checks.py --profile quick
./scripts/run_checks.py --profile catalogue
./scripts/run_checks.py --profile docs
./scripts/run_checks.py --profile studio-smoke
./scripts/run_checks.py --profile full
```

Profiles are intentionally coarse. Choose the smallest profile that matches the risk.
The `docs` profile includes Library import parser, Library import service, and Docs Management Server checks.
The `studio-smoke` profile builds a temporary Jekyll site and runs retained browser smoke scripts such as the data import route checks.
Those checks cover both the docs-management-unavailable state and a mocked Library import preview flow.

## Expected Close-Out

When Codex runs checks, the final response should report:

- which profiles ran
- pass/fail status
- the `var/test-runs/.../summary.md` path
- any failed command log paths
- manual checks still needed

Example:

```text
Automated checks:
- quick: pass
- catalogue: pass

Logs:
- var/test-runs/20260501-171530/summary.md

Manual checks:
- Open /studio/catalogue-field-registry/
- Search downloads
- Clear search
```

## Current Scope

The MVP framework is deliberately small:

- no pytest dependency
- no CI contract
- no automatic full-suite run before every change
- no broad fixture duplication

Add a new check only when it captures repeatable risk that would otherwise be hard to verify.
