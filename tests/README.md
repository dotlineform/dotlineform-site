# Repository Tests

This directory owns cross-repository assurance rather than application behavior.

- `run_checks.py` coordinates optional named evidence profiles and writes ignored summaries under `var/test-runs/`.
- `audits/` contains executable checks whose contract crosses application owners.
- `contracts/` contains the checked manifests consumed by those audits.
- focused application tests stay under the application that owns the behavior.

Do not move an application report, maintenance dashboard, stale audit mode, or UI workflow here merely because it can produce evidence. A cross-repository check must protect a current contract and remain independent of any retired Admin route. `bin/site-validate` owns deploy-root validation; the projection audit owns checked source/projection classification and leak checks.
