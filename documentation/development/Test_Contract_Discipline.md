---
draft: false
doc_id: d-20260627-212121-7cf7de
title: Test Contract Discipline
added_date: "2026-06-27 21:21:40"
last_updated: "2026-11-18"
summary: When to add a focused test and how to document, isolate and run it.
parent_id: d-20260419-000000-d2e47b
---
# Test Contract Discipline

Propose a test for a specific failure with a meaningful user or operational consequence. Explain why automation is worth the setup, authoring, run, maintenance and diagnosis costs. Agree the scope before changing tests or their fixtures and helpers, including temporary regression scripts. Use [Verification](Verification.md) for ordinary development checks and manual acceptance.

## Choose The Smallest Useful Test

Use the lowest layer that can demonstrate the failure. A parser or generator check can prove a saved data contract. A focused service or HTTP check can prove request handling and persistence. Use a browser for a failure that depends on browser integration, such as route boot, module wiring or public/local capability boundaries. Review presentation, focus, interaction and visible completion in the owning UI.

Keep the test with the app or tool that owns the behaviour. Add shared fixtures and runner tooling only when approved tests need them. An executable check should exercise a single named boundary and expose the input, action and expected result clearly.

## Record The Contract And Cost

Keep one proportionate specification and coverage record with the durable app or domain documentation. Record the behaviour and consequence, exact selection and command, scenarios and assertions, fixtures or substitutes, real components exercised, file/network effects, limits, and when the check is worth running. Include a rough estimate of material setup, run and maintenance costs. Record selected results in the delivery and link to the coverage record.

If an assertion fails, establish whether the agreed behaviour changed or the fixture, expectation or environment drifted. Use that result to diagnose the failure within the agreed scope.

## Run The Selected Test

Use the owning tool directly. For an approved Python test, use the project interpreter from the repository root:

```bash
python3 -m pytest <test-path> -k <selector>
```

Scope setup and teardown to the selected case. When a Docs service needs storage, supply a temporary `DOTLINEFORM_DOCS_BASE_DIR` before importing the service. For Projects-owned media or packages, supply an independent temporary `DOTLINEFORM_PROJECTS_BASE_DIR` where required. Pass the corresponding explicit base-directory flags for builder commands. Keep test writes in those isolated roots. For an approved Python browser check, use the project Playwright environment and any required loopback/browser permissions.

Report what the run exercised, what it established and the material limits. The [site test retirement record](../deliveries/Review_Test_Policy_And_Checks.md) identifies historical scripts and coverage available in Git. Native App and Processing use their own project guidance.
