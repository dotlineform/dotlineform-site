---
draft: false
doc_id: d-20261017-165926-8d4c73
title: Table Detail Titles
added_date: "2026-10-17 16:59:26"
last_updated: "2026-10-17"
---
# Table Detail Titles

Parent: [Planned Features](../Planned_Features.md). Durable behaviour: [Source Editor Scripts](../Source_Editor_Scripts.md#directives).

Status: implemented and reviewed on 2026-10-17; awaiting manual normal-use acceptance. The user approved optional editable table titles, `Table` as the default, removal of numbering and no required-title validation. Restart Docs Viewer and reload Manage to adopt the renderer and Source insertion changes; normal Save or exact document Rebuild projects an authored title. No commit, Publish or deployment was performed.

## Agreed Scope And Ownership

The existing one-line directive accepts an optional double-quoted `title` immediately before its associated Markdown table. Source inserts `<!-- dotlineform:table-detail title="Table" -->` with the value selected. An empty or omitted title displays `Table`. Titles are plain text, preserve capitalisation and label the expanded view and its Open control. Internal identifiers remain independent of titles.

The frontend owns authoring selection and display. The existing Python Markdown renderer parses the optional title during generation and projects an escaped text attribute; ordinary Source Save owns persistence and exact generation. No endpoint, title-validation pass, migration or complete document/Search rebuild is added. Public runtime code uses the existing tracked projection.

## Completion Gates

- [x] Readiness: existing directive/rendered-table/presentation flow supports the change without a new workflow or schema owner; scope is limited to title authoring, projection and presentation.
- [x] Implement optional title projection, Source value selection and unnumbered browser labels.
- [x] Run focused source checks and update the public projection.
- [x] Review the final source and projection, including redundancy and defensive behaviour.

## Evidence And Review

Selected evidence is changed-path Python/JavaScript lint, Python compilation, whitespace checks, exact public projection inspection, projection consistency and site validation. These address syntax, module wiring and deploy-artifact consistency, take seconds locally and may update ignored lint/bytecode caches. They do not exercise live Source Save, generated title output or browser interaction. No test creation, changes or execution are included; manual interaction remains with the user.

Python lint and compilation passed for the shared Markdown renderer; JavaScript lint passed for the shared table adapter and Source directive actions. The public projection changed only the shared table adapter; projection consistency and site validation passed. The bounded source/diff review covered empty and omitted title handling, entity decoding and escaped attributes, text-only heading/label rendering, selected-placeholder offsets and independent table identities.

### Code Review: Redundancy And Defensive Behaviour

The title is parsed in the existing Markdown token pass and carried through one table attribute into the already-mounted browser record. The `Table` display default has one owner in the browser. Source reuses its existing captured-range insertion and placeholder selection; no endpoint, request, source read, title completeness check, normalization, audit, compatibility alias or recovery path was added. The no-title form is part of the optional-title grammar. Display numbering and its unused occurrence field were removed, while internal table IDs remain for exact target selection and cloned-ID remapping.

Retained safeguards are the directive's single-line grammar and immediate-table association, existing escaped HTML attribute serialization, DOM text/attribute assignment and existing exact mounted-target lifecycle. They prevent a directive affecting unrelated content, preserve title text safely and keep presentation tied to its table; they add no filesystem or network work. No blocking findings remain. Live Save/generation, public browser presentation and interaction remain unexercised; retain this delivery link until normal-use acceptance is recorded.

## Icon Styling Follow-Up

Implemented and reviewed on 2026-10-17 following the user's request. Enabled grey toolbar icons, including Recent and Manage collection sort, use the normal theme foreground on hover; the grey search-clear button follows the same colour rule. Table Detail now uses the shared toolbar button: grey at rest, transparent, borderless and without a persistent shadow, with the shared icon size and a circular background tint on hover. Light mode uses the existing near-black foreground; dark mode uses its corresponding light foreground. [Runtime](../Docs_Viewer_Runtime.md#three-surfaces) owns the durable presentation contract.

JavaScript lint passed for the changed shared table adapter; the shared JavaScript and CSS public projections were updated and inspected. Projection consistency, site validation and whitespace checks passed. No tests, browser actions, document generation, Publish or deployment ran; visual acceptance remains manual after reloading Docs Viewer.

Bounded code review confirmed that the common hover selector overrides the resting grey colours, including the later-loaded Manage sort rule, while existing active/disabled/focus styles retain their ownership. The table opener supplies the shared control-height token within its content row and reuses the common button instead of retaining separate border, shadow, hover and focus rules. These are frontend styling changes with no new handlers, validation, service work or compatibility layer. No blocking findings remain.
