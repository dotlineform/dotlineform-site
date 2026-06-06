# Tests

This directory holds lightweight, opt-in repo checks.

Use these checks when a change has enough blast radius that manual review alone is likely to miss regressions. Do not treat this as a mandatory enterprise-style suite for every small edit.

Run checks through:

```bash
$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick
```

Local run logs are written under `var/admin/test-runs/` and are not committed.
