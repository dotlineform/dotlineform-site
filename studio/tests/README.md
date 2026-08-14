# Tests

This directory holds Studio-owned deterministic tests and three retained browser boundaries.

- `python/` owns service, API, planner, generator, configuration, and data contracts.
- `smoke/` owns local Catalogue boot, local Tag boot, and representative public Catalogue boot only.

UI interaction, layout, copy, filtering, and modal behavior are accepted manually unless one of those integration boundaries is the actual risk.

Run checks through:

```bash
$HOME/miniconda3/bin/python3 tests/run_checks.py --profile quick
$HOME/miniconda3/bin/python3 tests/run_checks.py --profile studio
$HOME/miniconda3/bin/python3 tests/run_checks.py --profile studio-smoke
```

Local run logs are written under `var/test-runs/` and are not committed.
