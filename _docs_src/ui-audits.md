---
doc_id: ui-audits
title: "UI Audits"
added_date: 2026-04-21
last_updated: 2026-04-21
parent_id: ""
sort_order: 210
---
# UI Audits

This section stores page-level UI audit outputs.

Use it for:

- Studio UI conformance reviews
- page-specific audit findings that compare a live route against shared UI standards
- follow-up audit passes where the result, cleanup path, or coverage status changed meaningfully

Do not use it for:

- rolling change history
- design standards themselves
- one-off implementation requests or feature specs

Those belong in:

- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Design](/docs/?scope=studio&doc=design)
- [UI Requests](/docs/?scope=studio&doc=ui-requests)

## Naming Convention

Create one doc per meaningful page audit using:

- `doc_id: ui-audit-<page-key>-<yyyymmdd>`
- source file: `_docs_src/ui-audit-<page-key>-<yyyymmdd>.md`

Examples:

- `ui-audit-catalogue-new-work-20260421`
- `ui-audit-bulk-add-work-20260421`
- `ui-audit-catalogue-work-20260421`

Use a short route-based `page-key`.

Good examples:

- `catalogue-new-work`
- `bulk-add-work`
- `catalogue-work-detail`

Avoid:

- vague labels such as `page-1`
- very broad labels such as `studio-forms`
- file-path punctuation that does not fit cleanly into a doc id

## When To Create A New Audit Doc

Create a new doc when:

- a page receives its first formal conformance review
- a later pass materially changes the result
- the audit exposes new standards gaps or cleanup work that should stay historically visible

Update the existing same-day audit doc when:

- you are only refining wording
- you are adding a small follow-up note from the same review pass
- the outcome and required cleanup have not materially changed

## Expected Contents

Audit docs should follow the output structure defined in [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance):

- coverage summary
- findings
- cleanup opportunities
- remediation status
- open decisions
- verification

Working rule:

- keep post-audit remediation progress in the audit doc itself
- keep unresolved page or shared-design decisions visible in the audit doc until they are either resolved or promoted into a real shared request/spec task
- do not use [Site Change Log](/docs/?scope=studio&doc=site-change-log) as the open-audit tracker

## Reading Order

When reviewing or creating a page audit:

1. [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
2. [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
3. this section
4. the relevant audit doc
