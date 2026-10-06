---
draft: false
doc_id: d-20261006-210809-a7436e
title: Summary Token Delivery
added_date: "2026-10-06 21:08:09"
last_updated: "2026-10-06 21:18:11"
parent_id: d-20260428-000000-f5ff18
---
# Summary Token Delivery

## Current And Next State

Status: implementation complete; focused static checks and bounded code review passed, including the user-requested final Directives **Summary** item with `summary.svg`. The shared document builder expands standalone `[[summary]]` blocks into escaped Summary text with dedicated grey-panel styling; Search omits active directives from body terms. The canonical stylesheet has its tracked public projection; menu insertion and its supplied icon stay management-only. Next: reload Docs Viewer for user manual menu/insertion and rendering/presentation review; retain this delivery until later manual archive. No document source or generated document data was changed; no tests, browser automation, Docs/Search build, Publish, commit or push was performed. This delivery is parented to [Planned Features](../Planned_Features.md); [Builder](../Builder.md#summary-block) owns expansion and [Source Editor Scripts](../Source_Editor_Scripts.md#directives) owns insertion.

## Requirements And Deliverables

- Expand each exact standalone `[[summary]]` occurrence from the current document's normalized front-matter Summary during ordinary/collection document builds and publication preparation, retaining authored source.
- Render escaped plain text in one standard grey panel, borrowing quote spacing/background without its left border. Omit empty summaries; preserve literal code, escaped/inline occurrences and HTML contexts. No token options are added.
- Offer **Summary** as the final Directives menu item with the supplied `summary.svg` icon, inserting a standalone block through the existing guarded Source adapter while retaining selected text and supplying blank-line separation. No modal, front-matter update or automatic Save is added.
- Keep Summary's existing Search metadata ownership and omit active directives from body terms. Do not rebuild Search as implementation follow-through.
- Project the canonical shared stylesheet through the tracked public runtime inventory. Do not edit document content, generated document data or existing Summary assignments.

## Process

Choose **Directives → Summary** in Source to insert `[[summary]]` with block spacing, maintain `summary` in front matter, and Save. Direct typing on its own line with blank lines around surrounding prose also works. The watcher builds expanded document content. Reload styles to see the panel/menu icon; Publish is the separately authorized public-data operation.

## Delivery Steps

- [x] **SUM-0 — Readiness:** confirmed existing normalized Summary metadata, shared ordinary/collection payload ownership and parser extension points. No dependency blocks this bounded addition; avoid a template system, new endpoint or automatic document placement.
- [x] **SUM-1 — Implementation:** added the parser-owned Summary block, exact document metadata handoff, Search-source omission and dedicated shared styling; durable behavior is documented in Builder.
- [x] **SUM-2 — Focused verification:** `bin/lint-python` and explicit Python `-m py_compile` passed for `summary_directive.py`, `inline_icons.py`, `payloads.py` and `build_search.py`. `bin/site-code-update` changed only the shared stylesheet projection; its `--check` and `bin/site-validate` passed. Scoped tracked/new-file whitespace diagnostics emitted no errors; the focused sanitization scan found only expected token names and identifiers. These inexpensive local diagnostics address source mistakes and public projection drift, writing only normal caches plus the explicit stylesheet projection. No test code, tests, browser automation, document source changes or Docs/Search build was included; behavioral and visual review remain manual.
- [x] **SUM-3 — Code review:** reviewed document-local metadata handoff, literal text escaping, omission of empty blocks, parser code/HTML boundaries, exact Search-source omission, independent styling and the sole public stylesheet delta. Removed paragraph interruption after identifying that multiline inline code can contain a token-only line; Summary uses a separate Markdown block with blank lines around surrounding prose. Repeated lint/syntax for the changed directive module passed. No blocking finding remains; no renderer execution, Search build or Export behavior was exercised.
- [x] **SUM-4 — Implementation closeout:** Builder owns the lasting grammar, build/Search behavior and evidence limits. Implementation is complete; manual rendering/presentation acceptance remains pending. Retain this delivery and its Planned Features link for review and recent-work lookup until manual archive after acceptance; no separate concept, architecture or verification document was created.
- [x] **SUM-5 — Menu follow-through:** added user-approved final **Summary** item, mapped the supplied `summary.svg` in management CSS and advanced the shell stylesheet version. The existing captured adapter/range insertion preserves selected text and adds missing blank-line separation for Summary, with existing directive spacing retained. `bin/lint-js` for `directive-actions.js` passed; scoped whitespace diagnostics emitted no errors. Subsequent code review covered last-item ordering, current/busy guards, caret offsets, start/end insertion, spacing and the local mask path; no blocking finding remains. These static diagnostics took seconds, exercised no browser or source writes and needed no additional public projection because all follow-through assets are management-only; manual icon/menu/insertion review remains pending.

Gate: implementation completion requires selected static checks and code review. Manual rendering/presentation acceptance remains with the user. No tests or fixtures are created, changed or run under this delivery; [Test Contract Discipline](../Test_Contract_Discipline.md) owns any separately agreed test work. Docs/Search build, Publish, commit and push are separate actions.
