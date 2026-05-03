---
doc_id: scripts-run-checks
title: "Run Checks"
added_date: 2026-05-01
last_updated: 2026-05-03
parent_id: scripts
sort_order: 28
---
# Run Checks

`./scripts/run_checks.py` runs optional repo check profiles and writes local logs under `var/test-runs/`.

It is not a mandatory gate for every change. Use it when the change is broad enough that manual checks alone are not a good fit.

## Usage

List profiles:

```bash
./scripts/run_checks.py --list
```

Run a profile:

```bash
./scripts/run_checks.py --profile quick
```

Combine profiles:

```bash
./scripts/run_checks.py --profile quick --profile catalogue
```

Run the broad profile:

```bash
./scripts/run_checks.py --profile full
```

## Profiles

- `quick`
  Runs diff whitespace checks, lightweight Python syntax checks, the Studio ready-state audit, and Studio config JSON parsing.
- `catalogue`
  Runs catalogue field-registry verification and a representative field-aware build preview.
- `docs`
  Rebuilds Studio docs-viewer payloads and Studio docs search payloads.
- `studio-smoke`
  Builds the site to a temporary Jekyll destination for browser smoke checks.
- `full`
  Runs `quick`, `catalogue`, `docs`, and `studio-smoke`.

## Outputs

Each run creates:

- `var/test-runs/<run-id>/summary.md`
- `var/test-runs/<run-id>/summary.json`
- one `.log` file per command

The summary file is the path Codex should report in close-out.

## Related References

- [Testing](/docs/?scope=studio&doc=testing)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
