---
draft: false
doc_id: d-20261118-235200-9870c4
title: Review Test Policy And Checks
added_date: "2026-11-18 23:50:00"
last_updated: "2026-11-18"
summary: Decide the future of suspended automated tests, harnesses and profiles separately from documentation cleanup.
parent_id: d-20261118-235100-64ad2e
ui_status: proposed
---
# Review Test Policy And Checks

## Current Position

Automated test scripts/profiles have been suspended. Focused static checks, built-in delivery code review and manual/normal-use acceptance have supplied the recent evidence. That practice does not certify unexercised behaviour or prove that every script can safely disappear.

The user considers complete retirement of the old scripts likely. Decide this here as separate work: the documentation cleanup authorises no test deletion, fixture migration, profile change or suite reactivation. [Current verification](../development/Verification.md) and the existing approval boundaries in [AGENTS](../../AGENTS.md#checks-and-test-policy) remain in force.

## Review Inputs

The five earlier guidance records retain their identities, coverage descriptions and historical evidence under `testing/`. They are review inputs, not instructions to run suspended checks:

- [Testing](testing/Testing.md): previous selection policy and mixed coverage/retirement records.
- [Test Contract Discipline](testing/Test_Contract_Discipline.md): specification, cost and approval rules.
- [Run Checks](testing/Run_Checks.md): runner/profile intent, old command recipes and output conventions.
- [Pytest](testing/Pytest.md): collection/fixture boundaries and known limitations.
- [Browser Smoke Testing](testing/Browser_Smoke_Testing.md): former retained browser boundaries and harness mechanics.

The [documentation rationalisation record](Documentation_Code_Follow_Ups.md#code-and-file-follow-ups) identifies concrete obsolete scope, watcher, source, Search, package, media and Catalogue test assumptions. Read the actual selected code before using any record as current coverage. Profile membership and old green results are not approval or assurance.

## Decisions And Next Work

- [ ] Identify the concrete regressions worth protecting and what static diagnostics, bounded code review and manual use already cover.
- [ ] Inspect the suspended scripts, fixtures/harnesses, runner/profile membership and CI callers only to decide their actual remaining value and dependencies.
- [ ] Propose a bounded retirement/replacement set, including any small worthwhile checks hidden in broad collections. Keep lint, syntax, runtime projection and deploy-root validation distinct from test-suite retirement.
- [ ] Agree a concise future policy: explicit required checks versus risk-selected evidence, test-work approval, useful coverage records and realistic maintenance/run costs.
- [ ] Obtain approval for the concrete script/profile/test change set before implementing it; preserve relevant coverage/acceptance history and remove obsolete documentation inputs once their decisions are compiled.

No new run is required merely to inventory or retire an obsolete script. Any selected execution needs its own purpose, effects and proportionate budget. Do not alter production behaviour to satisfy a retired test.
