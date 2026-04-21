---
doc_id: studio-ui-conformance
title: "Studio UI Conformance Spec"
last_updated: 2026-04-21
parent_id: design
sort_order: 22
---
# Studio UI Conformance Spec

This document defines the current conformance test for Studio UI pages.

Use it when the task is:

- check whether page X conforms to Studio UI standards
- identify non-conforming UI on a Studio page
- decide whether a deviation is fixable, intentional, or still outside current shared coverage
- identify redundant route-local markup or CSS and the cleanup needed after a fix

This is the audit contract, not the primitive reference itself.

Use the published primitive pages and shared framework docs as the source rules. Use this document to define how those rules should be audited and reported.

Related references:

- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [UI Audits](/docs/?scope=studio&doc=ui-audits)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## Goal

Make the following test valid and repeatable:

> check whether page X conforms to the full Studio design standards currently defined in the repo

The key constraint is `currently defined`.

If a page uses a pattern that has not yet been standardized enough to audit, the correct result is not a false pass or false fail. The correct result is a coverage gap.

## What Counts As Authoritative

Use these sources in this order:

1. Published primitive pages under `/studio/ui-catalogue/`
2. [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
3. [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
4. Relevant page/runtime docs if they define route-specific behavior that does not conflict with the shared Studio contract

Do not treat live page behavior by itself as authoritative if it conflicts with a published primitive or permanent shared rule.

## Coverage Model

Every audited UI element must be classified into one of these coverage states before judging conformance:

- `authoritative`
  The pattern has a published primitive page or a clear shared framework rule.
- `framework-only`
  The pattern has a shared framework rule but no published primitive page yet.
- `partial`
  The pattern is named or implied in docs, but the contract is still incomplete.
- `uncovered`
  The pattern is not standardized enough yet to run a reliable conformance judgment.

Current expected coverage:

- `authoritative`
  - button
  - input
  - panel
- `framework-only`
  - toolbar/import block
  - list shell
  - modal form internals
  - message/result pattern
- `partial`
  - list shell as a published primitive
  - toolbar as a published primitive
  - modal shell as a published primitive
- `uncovered`
  - any page pattern that is not yet mapped into the shared `tagStudio*` layer or recorded as a permanent shared rule

Implication:

- a page can be audited fully only to the extent that its UI is covered by `authoritative` or `framework-only` rules
- uncovered or partial areas must be flagged as coverage gaps, not hidden inside a generic pass/fail judgment

## Audit Inputs

Use these sources while auditing:

- the page route itself in a browser
- the page template and relevant runtime JS
- the shared Studio CSS
- the published primitive pages
- the shared framework and rules docs

Expected verification modes:

- desktop browser check
- mobile browser check
- local code inspection for shared-class usage, route-local compensation, and redundant styling

## Audit Workflow

Run the audit in this order:

1. Identify the page’s UI inventory.
2. Map each element to a shared primitive, shared composition, route-local pattern, or uncovered pattern.
3. Classify each element by coverage state.
4. For covered elements, compare the page to the authoritative rule.
5. For deviations, classify whether they are:
   - non-conformance
   - intentional exception
   - coverage gap
6. For each non-conformance, decide whether it is:
   - fixable now in shared code
   - fixable now only locally
   - blocked pending clearer shared coverage
7. Check whether the page contains redundant CSS, redundant markup, or obsolete route-local compensation after the fix.
8. Record the findings in the standard output format below.

## Required Audit Output

Every page-level conformance review should produce these sections:

### 1. Page Outcome

Start with one compact line:

- `/studio/example/ : non-conforming`

### 2. Remediation Status

Use the audit doc as the ongoing record of post-audit remediation for that page until the page is settled.

Record:

- which findings are still `open`
- which findings are `in-progress`
- which findings are `resolved`
- which findings are `deferred`
- what cleanup has actually been completed
- what cleanup is still pending

Do not use [Site Change Log](/docs/?scope=studio&doc=site-change-log) as the open remediation tracker.

The site change log should record implemented outcomes only.

### 3. Open Decisions

Record unresolved decisions that should not be buried inside findings or cleanup notes.

Use this section for:

- page-level decisions that still affect the remediation path
- shared-composition or shared-design questions exposed by the audit
- unresolved decisions about whether a pattern should stay local or move into shared coverage

Escalation rule:

- keep the decision in the audit doc while it remains part of that page’s remediation path
- move it into [UI Requests](/docs/?scope=studio&doc=ui-requests) only when it has become a real shared design/spec task rather than a normal page fix

### 4. Coverage Summary

List the page’s major UI areas and their coverage state.

Minimum categories:

- actions/buttons
- fields/inputs
- panels/surfaces
- summaries/messages
- list or result shells
- route-specific compositions

### 5. Findings

Each finding should include:

- `status`
  - `non-conforming`
  - `coverage-gap`
  - `intentional-exception`
  - `conforming-with-cleanup`
- `severity`
  - `high`
  - `medium`
  - `low`
- `ui area`
- `source rule`
  - primitive page, framework section, or permanent rule
- `evidence`
  - route plus file/line references when useful
- `why it matters`
- `fixability`
  - `shared-now`
- `local-now`
- `blocked`

### 6. Cleanup Opportunities

If the audit identifies redundant implementation after a fix, record:

- redundant route-local CSS
- redundant route-local markup wrappers
- shared CSS or JS that can now replace local behavior
- follow-up steps needed to complete the cleanup

This section is required even when the page mostly conforms.

### 7. Verification

Record:

- routes checked
- desktop checks run
- mobile checks run
- any code inspection used
- any blocked verification path

## Where Audit Output Lives

Save page-level audit outputs in [UI Audits](/docs/?scope=studio&doc=ui-audits), using:

- `doc_id: ui-audit-<page-key>-<yyyymmdd>`
- source file: `_docs_src/ui-audit-<page-key>-<yyyymmdd>.md`

This keeps page audit records separate from:

- [Site Change Log](/docs/?scope=studio&doc=site-change-log), which records implementation history
- [Design](/docs/?scope=studio&doc=design), which defines standards
- [UI Requests](/docs/?scope=studio&doc=ui-requests), which records task/request specs

Working rule:

- keep post-audit remediation, cleanup progress, and unresolved decisions in the audit doc itself
- use [Site Change Log](/docs/?scope=studio&doc=site-change-log) only when a change has actually been implemented
- use [UI Requests](/docs/?scope=studio&doc=ui-requests) only when the audit exposes a real shared design task that needs its own spec or request doc

## What Should Be Flagged

The audit must flag:

- where non-conformance exists
- whether the issue can be fixed now
- whether the fix belongs in shared code or only locally
- where the page depends on redundant compensation or stale styling
- which cleanup steps would be needed after the behavioral/visual fix lands

The audit must also flag:

- when the standards themselves are not yet defined enough to judge the page reliably

## Cleanup Test

After identifying a fix, the reviewer should ask:

1. Is the page compensating for a weak shared primitive?
2. If the shared primitive is fixed, what local code becomes redundant?
3. Does the page still carry old CSS, wrapper markup, or typography overrides that no longer serve a purpose?
4. Can the route move closer to the shared `tagStudio*` layer after the fix?

If yes, the audit should record the exact cleanup path rather than stopping at the first visible fix.

## Pass / Fail Rule

A page can only be declared `conforming to full Studio UI standards` if:

- every major UI area on the page is covered by `authoritative` or `framework-only` rules
- no unresolved non-conformance remains in those covered areas
- no uncovered area is being silently treated as if it were standardized

Otherwise use one of these outcomes:

- `conforming within current covered scope`
- `non-conforming`
- `blocked by coverage gaps`

Outcome precedence:

- if a page has any real non-conformance in a covered area, the overall outcome is `non-conforming`
- report coverage gaps separately, but do not let them soften or replace a real covered-area failure
- use `blocked by coverage gaps` only when the unresolved issues are coverage-only and there is no separate covered-area non-conformance

## Signposting Rule

If a user or future Codex session asks to check whether page X conforms to Studio UI standards, the expected reading order is:

1. [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
2. this document
3. [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
4. [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
5. [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
6. [UI Audits](/docs/?scope=studio&doc=ui-audits)
7. the page-specific audit doc if one exists

## Recommended Output Template

```text
Page outcome:
- /studio/example/ : conforming within current covered scope | non-conforming | blocked by coverage gaps

Remediation status:
- finding 1:
- finding 2:
- cleanup completed:
- cleanup pending:

Open decisions:
- decision:
- current owner/home:

Coverage summary:
- buttons: authoritative
- inputs: authoritative
- summary panel: framework-only
- route-specific composition: partial

Findings:
1. [severity] [status] ui area
   source rule:
   evidence:
   why it matters:
   fixability:

Cleanup opportunities:
- redundant local CSS:
- redundant local markup:
- follow-up steps:

Verification:
- desktop:
- mobile:
- code inspection:
- blocked checks:
```

## Current Limitation

This audit spec is ahead of the current primitive catalogue coverage.

That is deliberate.

The spec makes it possible to say:

- what can already be audited confidently
- what is only partially covered
- what additional primitive or framework work is needed before a page can pass a fuller design-conformance test

That is better than treating every page review as either a vague style opinion or a false full pass.
