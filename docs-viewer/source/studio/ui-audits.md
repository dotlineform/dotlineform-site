---
doc_id: ui-audits
title: UI Audits
added_date: 2026-04-21
last_updated: 2026-06-10
parent_id: ui
viewable: true
---
# UI Audits

This section describes live-route UI audit outputs.

Use it for:

- UI conformance reviews for Studio, Docs Viewer, Admin app, Analytics, and public-site routes
- page-specific audit findings that compare a live route against shared UI standards and app-specific contracts
- follow-up audit passes where the result, cleanup path, or coverage status changed meaningfully
- live-route checks that map UI Catalogue demo patterns into production namespaces

## Naming Convention

Create one child doc per meaningful page audit using:

- `doc_id: ui-audit-<page-key>-<yyyymmdd>`
- source file: `docs-viewer/source/studio/ui-audit-<page-key>-<yyyymmdd>.md`

Examples:

- `ui-audit-catalogue-new-work-20260421`
- `ui-audit-bulk-add-work-20260421`
- `ui-audit-catalogue-work-20260421`

## When To Create A New Audit Doc

Create a new doc when:

- a page receives a formal conformance review
- the audit exposes new standards gaps or cleanup work that should stay historically visible

Update the existing same-day audit doc when repeating an audit following changes to the page.

## Expected Contents

Audit docs should follow the output structure defined in [UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance):

- coverage summary
- modal composition, when the audited route opens modals
- findings
- cleanup opportunities
- remediation status
- open decisions
- verification

## UI Catalogue Demo Alignment

UI Audit owns live implementation checks. The UI Catalogue owns isolated demos.

When auditing a page that implements a catalogue primitive or pattern:

- reference the relevant demo route under `/admin/ui-catalogue/demos/`
- identify the demo namespace classes, for example `uiCatalogueDemoButton` or `uiCatalogueDemoModal`
- identify the live implementation classes that the page maps the pattern into, for example `docsViewer__actionButton`, `studioHomeLinks`, an Admin route namespace, an Analytics route namespace, or another route-owned namespace
- verify the live route imports production CSS/JS only, not `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css` or demo scripts
- check the live route with its production ready-state attributes, such as `data-studio-ready` only for Studio routes
- do not treat UI Catalogue demo pages as proof that live CSS is correct

If a live page drifts from the demo pattern, record whether the issue belongs to the live route implementation, the production shared primitive, or the catalogue demo itself.

## Coverage Gaps

Many live routes use UI that has not been fully standardised.

When an audit encounters an uncovered or partial pattern:

- record it as a coverage gap
- say whether the route can still be fixed locally without inventing a new shared rule
- say whether a focused primitive or pattern definition is needed before broader cleanup
- do not mark the route as fully conforming if important UI areas cannot be judged

Legacy `tagStudio*` usage should be treated as a migration signal. It can be accepted as existing implementation evidence on older Studio pages, but it should not be recommended for new work without an explicit migration decision.

When the pattern is a modal shell, open representative modal states in the live route and record the checks required by the [UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance). The modal shell demo proves the isolated pattern only; it does not prove the route's focus behavior, close behavior, validation placement, action ownership, or responsive fit.

Working rule:

- keep post-audit remediation progress in the audit doc itself
- keep unresolved page or shared-design decisions visible in the audit doc until they are either resolved or promoted into a real shared request/spec task
