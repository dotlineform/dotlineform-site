---
doc_id: scripts-run-checks
title: Run Checks
added_date: 2026-05-01
last_updated: 2026-06-12
parent_id: dev-home
---
# Run Checks

`$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` runs optional repo check profiles and writes local logs under `var/admin/test-runs/`.

It is not a mandatory gate for every change. Use it when the change is broad enough that manual checks alone are not a good fit.

## Usage

List profiles:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --list
```

Run a profile:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick
```

Combine profiles:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick --profile catalogue
```

Run the broad profile:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile full
```

Keep the temporary public-site smoke-test build for debugging:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile docs-viewer-smoke --keep-temp-build
```

## Profiles

- `quick`
  Runs diff whitespace checks, lightweight Python syntax checks, grouped pytest checks for the quick-profile Python modules, the Studio ready-state audit, and Studio config/activity JSON parsing. The syntax check includes core catalogue/source helpers, the Admin audit runner, and core lightweight test modules.
- `catalogue`
  Runs grouped pytest checks for catalogue-profile Python modules and a representative field-aware build preview.
- `docs`
  Runs grouped pytest checks for Docs Viewer export, Library import, generated-read helpers, Docs Management service, Docs routes, Docs Broken Links behavior, and Docs Viewer contract fixtures from `docs-viewer/tests/python/`, plus Analytics-owned Data Sharing checks; then rebuilds generated Studio docs payloads and Studio docs search payloads.
- `docs-viewer-smoke`
  Builds the static public site to a temporary destination and runs retained Docs Viewer route, standalone service, and public read-only smoke checks. Browser module-contract suites are not required smoke targets.
- `studio-smoke`
  Builds the static public site to a temporary destination and runs retained Studio-owned browser smoke checks, including public-site theme behavior and catalogue route/module checks. Docs Viewer smoke checks live only in `docs-viewer-smoke`; Analytics smoke checks live only in `analytics-smoke`.
- `admin-smoke`
  Runs Admin home and Admin operational route smoke checks.
- `analytics-smoke`
  Runs Local Analytics route/API/module/modal/ready-state smoke checks for tag workflows and Analytics-owned Data Sharing prepare/review behavior.
- `ui-catalogue-smoke`
  Runs UI Catalogue Python checks plus route and modal-demo smoke checks for the Admin app.
- `full`
  Runs `quick`, `catalogue`, `docs`, `admin-smoke`, and `studio-smoke`. It does not run `docs-viewer-smoke`, `analytics-smoke`, or `ui-catalogue-smoke`; run those profiles explicitly when those browser/runtime surfaces are in scope.

## Outputs

Each run creates:

- `var/admin/test-runs/<run-id>/summary.md`
- `var/admin/test-runs/<run-id>/summary.json`
- one `.log` file per command

The summary file is the path Codex should report in close-out.
Smoke profiles use `/tmp/dlf-public-site-build` as a temporary static public-site destination.
The runner removes any existing temp build before `public-site-temp-build` and removes the temp build again after the profile finishes, unless `--keep-temp-build` is passed.

## Related References

- [Testing](/docs/?scope=studio&doc=testing)
- [Local Admin App](/docs/?scope=studio&doc=local-admin-app)
- [Browser Smoke Testing](/docs/?scope=studio&doc=smoke-testing)
- [Studio Ready-State Audit](/docs/?scope=studio&doc=scripts-audit-studio-ready-state)
- [Catalogue Field Registry Verification](/docs/?scope=studio&doc=scripts-verify-catalogue-field-registry)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
