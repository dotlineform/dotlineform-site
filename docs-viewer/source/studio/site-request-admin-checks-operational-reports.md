---
doc_id: site-request-admin-checks-operational-reports
title: Admin Checks Operational Reports
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: change-requests
---
# Admin Checks Operational Reports

Status: planned separate request

## Summary

This request captures Admin Checks reports that answer operational, runtime, payload, performance, or generated-artifact questions.

It is intentionally separate from [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports), which is scoped to responsibility and ownership evidence.

Operational reports may still use the Admin Checks runner, report registry, artifacts, and UI, but they should not broaden the responsibility-focused request.

## Scope

This request can contain reports that answer questions such as:

```text
Question                                      Evidence report
--------------------------------------------  ------------------
Which generated payloads are large or broad?  generated-payloads
Which targets have runtime evidence gaps?     runtime-checks
Which route profiles are stale or failing?    runtime-checks
Which payloads or routes need perf review?    future request
```

These reports should remain narrow evidence reports.
They should not become a catch-all test dashboard, and they should not declare responsibility risk unless a later dependency report explicitly joins them with ownership evidence.

## Boundary

Operational report requests belong here when their primary question is about:

- generated payload size, shape, or validity
- runtime profile freshness or status
- performance measurements
- route smoke results
- build or generated-artifact health

Responsibility report requests belong under [Admin Checks Reports](/docs/?scope=studio&doc=site-request-admin-checks-reports) when their primary question is about:

- file size as maintainability evidence
- configured ownership and target boundaries
- imports across target boundaries
- public or top-level code surface
- churn around selected source files
- discovered test links around selected source files
- configured responsibility or ownership tokens

## Non-Goals

- no catch-all dashboard scope
- no browser-defined commands, search roots, or profiles
- no replacement for focused report requests
- no broad risk score from operational metrics alone
