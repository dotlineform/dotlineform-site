---
draft: false
doc_id: d-20260523-224407-911c73
title: Projection Contract Validation
added_date: "2026-05-23 22:44:07"
last_updated: "2026-11-18"
parent_id: d-20260331-000000-4a16b0

---
# Projection Contract Audit

Former cross-boundary projection audit and manifest. It records what the scope-era audit covered and the limits of that evidence. [Current reference](../studio/Run_Checks.md)

`tests/audits/projection_contract.py` reads the checked `tests/contracts/projection_contract.json` manifest. It checks configured artifact paths and exclusions, scans selected JSON for listed source-only fields and checks selected public assets for prohibited source references.

The manifest still contains former Analysis scope paths and the retired document-locations output. Treat it as an older audit specification. The current public boundaries and checks are described in [Projection Contract](../studio/Projection_Contract.md#current-enforcement). Revising the audit or its profile membership belongs to separate [test work](../studio/Test_Contract_Discipline.md).
