---
doc_id: scripts-run-checks
title: Run Checks
added_date: 2026-05-01
last_updated: 2026-05-15
parent_id: site-docs
sort_order: 5000
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
  Runs diff whitespace checks, lightweight Python syntax checks, grouped pytest checks for the quick-profile Python modules, the Studio ready-state audit, and Studio config/activity JSON parsing. The syntax check includes core catalogue/source helpers, the Studio audit service script, and core lightweight test modules.
- `catalogue`
  Runs grouped pytest checks for catalogue-profile Python modules and a representative field-aware build preview.
- `docs`
  Runs grouped pytest checks for Docs Viewer export, Library import, generated-read helpers, Docs Management service, Docs routes, and Docs Broken Links behavior, then rebuilds Studio docs-viewer payloads and Studio docs search payloads.
- `docs-viewer-smoke`
  Builds the site to a temporary Jekyll destination and runs retained Docs Viewer smoke checks for direct loads, search route state, link interception, history, hash fragments, Library scope loading, and management modal behavior.
- `studio-smoke`
  Builds the site to a temporary Jekyll destination and runs retained browser smoke checks, including the Docs Viewer route smoke, the UI Catalogue modal demo, Studio data import route checks with docs-management unavailable, and a mocked Library import preview flow.
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
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
