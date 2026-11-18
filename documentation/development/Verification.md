---
draft: false
doc_id: d-20261118-235000-c02e17
title: Verification
added_date: "2026-11-18 23:50:00"
last_updated: "2026-11-18"
summary: Current static checks, required public validation, bounded code review and manual acceptance.
parent_id: d-20260419-000000-d2e47b
---
# Verification

Current site development uses focused static diagnostics, implementation review and relevant manual checks. Recorded normal-use acceptance establishes the workflow and outcomes observed. Agree focused test work separately when a specific failure warrants automation. [Test Contract Discipline](Test_Contract_Discipline.md)

## Choose The Evidence

Name the changed boundary, plausible failure, exact check and material effects/cost. Use the smallest evidence that answers that question, and stop when sufficient. Repeat for a relevant change, failure or unresolved risk. A documentation-only edit may need only source/link review.

| Changed boundary | Current evidence |
| --- | --- |
| Repository Markdown | Read-through and relevant path/anchor/identity checks; whitespace where warranted |
| Python/JavaScript source | Focused lint, syntax/import/module diagnostics as relevant, plus bounded source review |
| Represented public runtime/configuration | The projection and deploy-root sequence below |
| Generated output | Inspect the owning operation's selected output when its contract changed; avoid another generation merely for idempotence |
| Interaction, presentation or normal-use completion | Manual acceptance naming the route/workflow and observed outcome |

Lint, compilation, imports and code review establish different things. They do not substitute for live Save/Publish, failure-path acceptance or visual fit. Keep those omissions visible.

## Source Lint

Use explicit paths for new or materially changed source:

```bash
bin/lint-python <path> [path ...]
bin/lint-js <path> [path ...]
```

Use `bin/lint --scope <scope-id>` only for a complete adopted boundary. `tooling/lint/targets.json` owns membership; that package owns pinned Ruff/ESLint rules. Explicit commands fail without eligible targets. Report the actual paths/roots; generated, vendor, dependency, cache, canonical data, retired and Processing source remain outside this Python/JavaScript claim. [Tool installation](Runtime_Dependencies.md)

Python compilation or existing read-only import/JSON diagnostics can resolve a specific syntax or wiring concern. Use the project interpreter. Compilation can update ignored bytecode. `git diff --check` diagnoses changed-text whitespace.

## Docs Viewer Site Code Projection

Shared/public runtime is canonical under `docs-viewer/`; `site-tools/config/site-code-update.json` owns its tracked public projection. After a represented source changes:

```bash
bin/site-code-update
git diff -- site/docs-viewer site/shared
bin/site-code-update --check
bin/site-validate
```

Inspect the exact inventory-owned delta, including any represented file outside those directories. Commit canonical and projected files together when committing is authorised. Adding/removing a file or changing its public status needs an explicit manifest change; mixed source directories do not grant public adoption.

Projection writes tracked public code/configuration; `--check` and site validation inspect repository output without a Docs workspace or network. Content Build/Publish and the manual Pages release have their own owners. [Publish and deploy](../guide/Publish_And_Deploy.md)

## Review And Manual Acceptance

Each material code/config delivery retains a distinct review step, including the [Redundancy And Defensive Behavior Review](Development_Checklist.md#redundancy-and-defensive-behavior-review). Record actual findings/resolutions, changed-owner checks and important omissions. A passing static diagnostic does not establish that added behaviour is needed.

Use the owning local app for local operations and `bin/site-preview` for the tracked public artifact. Leave visual/tactile review to the user unless specifically requested. Keep completed persistence/generation separate from fresh-display failures and report completed effects. Reuse existing acceptance without claiming cases that were never observed.
