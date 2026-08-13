# Python Checks

Put deterministic pytest checks here when they verify repo behavior better than a manual checklist.

Good candidates:

- registry or schema contracts
- planner behavior
- generated-data invariants
- focused regression checks for script behavior

Keep each file aligned to one service, model, planner, generator, or configuration owner. Browser route boot belongs in the deliberately small `studio/tests/smoke/` suite.
