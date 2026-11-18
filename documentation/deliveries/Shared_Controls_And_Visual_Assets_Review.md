---
draft: false
doc_id: d-20261118-230010-e2b71f
title: Shared Controls And Visual Assets Review
added_date: "2026-11-18"
last_updated: "2026-11-18"
parent_id: d-20261118-151521-a0f9c3
---
# Shared Controls And Visual Assets Review

This documentation batch consolidated twenty-two Studio pages into current component/control/style/shell references, separate design reasoning and initially four Working icon records. All four have since been retired as recorded below, and the [shared Lucide licence notice](../../docs-viewer/static/icons/LICENSE.lucide) is retained beside the canonical icons. The [tracker](Rationalise_Documentation.md) and [triage inventory](Site_Workflow_Guide_Triage.md) own the dispositions. Original migration tables and paragraphs remain in Git at `c76f6608ef` under `documentation/studio/`; they are historical evidence rather than current runtime inventories.

## Icon Migration Evidence

The 19 September toolbar/report migrations reported focused JS lint, projection consistency, site validation and whitespace checks. The viewer slice added thirteen SVGs and projected nine shared modules plus CSS; the report slice projected the shared collection module and report CSS while reusing existing arrow/clear assets. The recorded visual review remained pending. Stage, panel-collapse, Info/Links and retired-report rows subsequently ceased to describe current controls.

The 20 September list/status work reported JS lint for thirteen canonical modules, Python lint for three source/collection owners, XML parsing of seven SVGs and projection/site checks. It separated ordinary free-text `ui_status` from boolean readiness, retaining only planned/report artwork and omitting collection status. The original source inspection found no `ui_status` in 2,484 collection documents. Docs-only complete builds changed five management manifests, with zero warnings and no document/reader/relationship changes. Those historical collection names, counts and commands do not define current configuration or authorize repeating the builds.

Studio's Work-editor conversion was user-accepted on 24 September 2026. Focused lint covered six JS modules and the Studio HTTP owner; source review removed a text refresh that would have restored picker emoji. The conversion reused existing SVGs through a small Studio mask layer, retained text confirmation/identity controls, and introduced no Catalogue data or publication change. No separate interaction-test run was recorded.

The 30 September manual-token implementation delivered extensionless `[[icon:name]]`, Source insertion with stem selection and portable sanitized SVG-mask markup. The record reports explicit Python/JavaScript lint, compilation, whitespace, public-projection consistency and the builder's read-only help/import diagnostic. Code review tightened confinement/diagnostics and checked literal preservation, operation-scoped caching and export portability. It did not build authored content, exercise export or run tests/browser checks.

The collection-marker implementation configured Catalogue, Concepts, Context and Moments stems and exact Index report-host matching. Its record reports lint/compilation, production config loading, reader-config writing, projection of four SVGs and two shared modules, projection consistency, site validation and whitespace. Review covered exact filenames, path/symlink confinement, loaded host mapping and local/public SVG URLs. These checks did not establish browser appearance or document Publish/deployment; user completion is recorded below.

## Toolbar Acceptance Closeout

On 18 November 2026 the user confirmed that Toolbar Icon Mapping was done and its Working record was no longer needed. The remaining toolbar visual-review checklist was closed and retired after redirecting references and checking its document identity. This records the user's completion decision; individual theme, state and artwork cases were not separately itemised, and this retirement ran no browser review. Current artwork and placement remain with [Toolbar Icons](../reference/Toolbar_Icons.md) and [control surfaces](../reference/Panel_Hosts_And_Control_Surfaces.md). Manual-token and collection-marker completion follows below.

## Token And Collection Acceptance Closeout

On 18 November 2026 the user confirmed that Icon Tokens Delivery and Collection Icons Delivery were done and requested their retirement. This closes their remaining manual acceptance gates for token insertion/selection/rendering and the four selected collection markers. Individual cases were not separately itemised, and this retirement ran no new browser checks. Their useful implementation/verification evidence is preserved above; current behaviour belongs to [Icon Tokens](../reference/Icon_Tokens.md) and [Collection Icons](../reference/Source_Organisation.md#collection-icons). References and document identities were checked before retiring both Working files. The broader icon proposal's final disposition follows below.

## Shared Icons Closeout

The user subsequently requested retirement of Shared Icons, retaining only the canonical artwork origin/version/notice record as a follow-on. Additional artwork, native reuse, an icon picker and a combined image modal are no longer tracked as pending outcomes of this proposal. Current interface, token, collection-marker and Related Links behaviour remains with its Reference owners.

The [repository README](../../README.md#external-libraries-and-resources) credits Lucide as the source of several SVG icons and names key document/media libraries. At the user's request, the full upstream [Lucide licence](../../docs-viewer/static/icons/LICENSE.lucide), including its ISC and Feather-derived MIT notices, was retained in the canonical icons folder and linked from the README. This completes the notice-retention follow-up without an icon-by-icon inventory or historical version reconstruction. No artwork or public assets changed.

## Shared Interaction And Style Evidence

The 20 October Search List free-entry change reported targeted JS lint/source review; Medium typing and suggestion commit reused the caller's draft handlers. Keyboard/pointer/blur behaviour remained manual acceptance. The 22 October File Picker initial-focus fix reported focused lint/whitespace and reused close cancellation to prevent late suggestions reopening over a seeded folder, with no extra read/timer or workflow change.

The 24 October neutral-result-colour change reported projection consistency, site validation, whitespace and source/redundancy review across palette inputs, selector precedence and host inheritance. It changed presentation without requests, state or generation. Manual light/dark review remained pending in that record.

## Public Root And Supersession

The 15 October public-root move replaced the homepage redirect with the reader at `/`, removed `/analysis/` without an alias and aligned route/workspace bases and 404 recovery. Source review corrected the installed asset-version token. Lint/compilation, projection/site checks and read-only configuration/URL diagnostics passed; browser interaction/deployment were not established by that record.

Current references now describe five control surfaces, Search/Recent in Index, direct Home/theme composition, pinned Related Links Info, Source's present controls and canonical source paths. They remove watcher, stage-selector, Graph, metadata-picker and old Index-toolbar claims. The retained ready-state audit still omits installed public/Review shells; the unused Selectable List and stale backlinks/status tests are tracker follow-ups.

## Evidence Limit

This batch inspected current browser components/controllers, style/shell files, icon rendering and the explicit public inventory, and checked documentation paths, headings and identities. It ran no live UI, build, import, publication or deployment operation and supplies no new visual acceptance. Subsequent user completion decisions, retirement of the four Working icon records and retention of the shared licence notice are recorded above; no icon follow-on remains open.
