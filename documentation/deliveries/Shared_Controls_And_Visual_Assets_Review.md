---
draft: false
doc_id: d-20261118-230010-e2b71f
title: Shared Controls And Visual Assets Review
added_date: "2026-11-18"
last_updated: "2026-11-18"
parent_id: d-20261118-151521-a0f9c3
---
# Shared Controls And Visual Assets Review

This documentation batch consolidates twenty-two Studio pages into current component/control/style/shell references, separate design reasoning and four Working icon records. The [tracker](Rationalise_Documentation.md) and [triage inventory](Site_Workflow_Guide_Triage.md) own its disposition. Original migration tables and paragraphs remain in Git at `c76f6608ef` under `documentation/studio/`; they are historical evidence rather than current runtime inventories.

## Icon Migration Evidence

The 19 September toolbar/report migrations reported focused JS lint, projection consistency, site validation and whitespace checks. The viewer slice added thirteen SVGs and projected nine shared modules plus CSS; the report slice projected the shared collection module and report CSS while reusing existing arrow/clear assets. The recorded visual review remained pending. Stage, panel-collapse, Info/Links and retired-report rows subsequently ceased to describe current controls.

The 20 September list/status work reported JS lint for thirteen canonical modules, Python lint for three source/collection owners, XML parsing of seven SVGs and projection/site checks. It separated ordinary free-text `ui_status` from boolean readiness, retaining only planned/report artwork and omitting collection status. The original source inspection found no `ui_status` in 2,484 collection documents. Docs-only complete builds changed five management manifests, with zero warnings and no document/reader/relationship changes. Those historical collection names, counts and commands do not define current configuration or authorize repeating the builds.

Studio's Work-editor conversion was user-accepted on 24 September 2026. Focused lint covered six JS modules and the Studio HTTP owner; source review removed a text refresh that would have restored picker emoji. The conversion reused existing SVGs through a small Studio mask layer, retained text confirmation/identity controls, and introduced no Catalogue data or publication change. No separate interaction-test run was recorded.

The 30 September manual-token and collection-marker implementations reported static/code review and their separate build/config evidence. Tokens embedded sanitized masks; collection configuration reused the exact filename owner and projected four assets. Neither record established browser acceptance. Their remaining gates are preserved in [Icon Tokens Delivery](../_working/Icon_Tokens_Delivery.md) and [Collection Icons Delivery](../_working/Collection_Icons_Delivery.md), alongside [toolbar acceptance](../_working/Toolbar_Icon_Mapping.md).

## Shared Interaction And Style Evidence

The 20 October Search List free-entry change reported targeted JS lint/source review; Medium typing and suggestion commit reused the caller's draft handlers. Keyboard/pointer/blur behaviour remained manual acceptance. The 22 October File Picker initial-focus fix reported focused lint/whitespace and reused close cancellation to prevent late suggestions reopening over a seeded folder, with no extra read/timer or workflow change.

The 24 October neutral-result-colour change reported projection consistency, site validation, whitespace and source/redundancy review across palette inputs, selector precedence and host inheritance. It changed presentation without requests, state or generation. Manual light/dark review remained pending in that record.

## Public Root And Supersession

The 15 October public-root move replaced the homepage redirect with the reader at `/`, removed `/analysis/` without an alias and aligned route/workspace bases and 404 recovery. Source review corrected the installed asset-version token. Lint/compilation, projection/site checks and read-only configuration/URL diagnostics passed; browser interaction/deployment were not established by that record.

Current references now describe five control surfaces, Search/Recent in Index, direct Home/theme composition, pinned Related Links Info, Source's present controls and canonical source paths. They remove watcher, stage-selector, Graph, metadata-picker and old Index-toolbar claims. The retained ready-state audit still omits installed public/Review shells; the unused Selectable List and stale backlinks/status tests are tracker follow-ups.

## Evidence Limit

This batch inspected current browser components/controllers, style/shell files, icon rendering and the explicit public inventory, and checked documentation paths, headings and identities. It ran no live UI, build, import, publication or deployment operation and supplies no new visual acceptance. Proposed native reuse and further artwork remain in [Working](../_working/Shared_Icons.md).
