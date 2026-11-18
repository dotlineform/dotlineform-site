---
draft: false
doc_id: d-20261118-235200-9870c4
title: Review Test Policy And Checks
added_date: "2026-11-18 23:50:00"
last_updated: "2026-11-18"
summary: Retirement of the suspended site test suite, retained verification and historical recovery.
parent_id: d-20260419-000000-d2e47b
ui_status: done
---
# Review Test Policy And Checks

The suspended suite had become expensive to maintain and diagnose. Many assertions targeted retired contracts or implementation details, and the suite gave limited evidence about workflows people used. The user approved retiring it and retaining a small foundation for future tests of specific features or workflows. [Verification](../development/Verification.md) · [Test Contract Discipline](../development/Test_Contract_Discipline.md)

## Delivered

- Removed the 182 tracked files in the former `docs-viewer/tests/`, `studio/tests/`, `site-tools/tests/` and `tests/` trees. They included Python tests, JavaScript contracts, browser smokes, fixtures, audit tooling and manifests, and `tests/run_checks.py` with all profiles.
- Removed the test-only CI paths, lint scope and Ruff exceptions. The five source lint scopes, explicit-path lint and Pages validation remain available. The App service still pins pytest through its development requirements, so the duplicate root pin was removed.
- Moved and condensed Test Contract Discipline with its original identity. Retired the other four review inputs from Working. Updated current guidance, historical references and the follow-up tracker.

## Verification And Limits

The diff accounts for all 182 approved paths. `bin/lint --list` matched the five remaining CI commands, and review confirmed that the four test-only triggers were removed. The lint JSON and Ruff TOML parsed. The Pages workflow still calls the site validator. The requirements include still resolves to the App service's pytest pin. Reference, identity and whitespace review completed the change. Verification was static. Site runtime, deploy artifact, native App and Processing were outside the change.

The former projection audit's private-field scan covered Catalogue archive JSON that had already been retired. The Catalogue consistency audit used the former standalone Series, Work and Detail layout. The route audit checked initial markup and missed the installed public route and Docs Review. For affected changes, inspect selected public output and review the owning route or producer as described in the current guidance. [Projection Contract](../reference/Projection_Contract.md#current-enforcement) · [Route Ready State](../reference/Route_Ready_State.md#nested-import-and-verification)

## Recovery

The pre-retirement Git revision is `eb46b263aa35457bc8cf9a05b1f780a1f66a78d3`. It contains all four test trees and the earlier guidance and coverage records under `documentation/_working/testing/`. Use that revision to recover a named case if a future delivery establishes the need, then assess it against the current owner and contract.

The early HTTP disconnect test is an example of recoverable focused coverage. Its historical specification describes which resets were suppressed and which failures remained visible. The earlier delivery records six passing cases and the manual evidence limits. [Former coverage and path](../reference/Local_Runners.md#focused-disconnect-test-coverage) · [Earlier run evidence](Runtime_Configuration_And_Recovery_Review.md#early-disconnect-delivery)
