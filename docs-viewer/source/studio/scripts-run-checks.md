---
doc_id: scripts-run-checks
title: Run Checks
added_date: 2026-05-01
last_updated: 2026-05-15
parent_id: dev-home
---
# Run Checks

`$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` runs optional repo check profiles and writes local logs under `var/test-runs/`.

It is not a mandatory gate for every change. Use it when the change is broad enough that manual checks alone are not a good fit.

## Usage

List profiles:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --list
```

Run a profile:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick
```

Combine profiles:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick --profile catalogue
```

Run the broad profile:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile full
```

Keep the temporary Jekyll smoke-test build for debugging:

```bash
$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke --keep-temp-build
```

## Profiles

- `quick`
  Runs diff whitespace checks, lightweight Python syntax checks, grouped pytest checks for the quick-profile Python modules, the Studio ready-state audit, and Studio config/activity JSON parsing. The syntax check includes core catalogue/source helpers, the Studio audit service script, and core lightweight test modules.
- `catalogue`
  Runs grouped pytest checks for catalogue-profile Python modules and a representative field-aware build preview.
- `docs`
  Runs grouped pytest checks for Docs Viewer export, Library import, generated-read helpers, Docs Management service, Docs routes, and Docs Broken Links behavior from `docs-viewer/tests/python/`, plus shared Data Sharing checks that remain under `studio/tests/python/`; then rebuilds generated Studio docs payloads and Studio docs search payloads.
- `docs-viewer-smoke`
  Builds the site to a temporary Jekyll destination and runs Docs Viewer smoke checks from `docs-viewer/tests/smoke/` for the standalone service, public read-only installs, browser modules, and management UI behavior.
- `studio-smoke`
  Builds the site to a temporary Jekyll destination and runs retained Studio-owned browser smoke checks, including the UI Catalogue modal demo, Studio data import route checks with docs-service unavailable, and a mocked Library import preview flow. Docs Viewer smoke checks live only in `docs-viewer-smoke`.
- `full`
  Runs `quick`, `catalogue`, `docs`, and `studio-smoke`. It does not run `docs-viewer-smoke`; run that profile explicitly when Docs Viewer browser behavior is in scope.

## Outputs

Each run creates:

- `var/test-runs/<run-id>/summary.md`
- `var/test-runs/<run-id>/summary.json`
- one `.log` file per command

The summary file is the path Codex should report in close-out.
Smoke profiles use `/tmp/dlf-jekyll-build` as a temporary Jekyll destination.
The runner removes any existing temp build before `jekyll-temp-build` and removes the temp build again after the profile finishes, unless `--keep-temp-build` is passed.

## Related References

- [Testing](/docs/?scope=studio&doc=testing)
- [Studio Smoke Testing](/docs/?scope=studio&doc=studio-smoke-testing)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
