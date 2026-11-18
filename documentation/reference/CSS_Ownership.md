---
draft: false
doc_id: d-20260511-200845-2a03a0
title: CSS Ownership
added_date: "2026-05-11 20:08:45"
last_updated: "2026-11-18"
parent_id: d-20260424-000000-50b63f

---
# CSS Ownership

Docs Viewer owns reader presentation across Public, Manage and Review. Local routes serve canonical styles; the public reader serves their tracked projection. Studio supplies its own shell, theme and adapter styles around shared primitives.

## Owners

| Change | Maintained owner |
| --- | --- |
| Docs light/dark colour roles | [docs-viewer-theme.css](../../docs-viewer/static/css/docs-viewer-theme.css) |
| Reader shell, typography, panels, prose, shared controls and artwork classes | [docs-viewer.css](../../docs-viewer/static/css/docs-viewer.css) |
| Public-safe report presentation | [docs-viewer-reports.css](../../docs-viewer/static/css/docs-viewer-reports.css) |
| Manage/reports/Source/Import/Review-only presentation | Focused styles under [Docs CSS](../../docs-viewer/static/css/) loaded by that route shell |
| Reusable field/list/picker interaction presentation | [shared/frontend/css](../../shared/frontend/css/) |
| Studio shell and adapter presentation | [studio.css](../../studio/app/assets/css/studio.css) |
| Standalone public 404 | [error.css](../../site/assets/css/error.css), consuming the Docs palette |

Public and Manage load palette, reader and public report styles. Manage adds its local workflow styles; Review loads palette, reader and Review styles. Review does not inherit Manage's artwork declarations. The 404 uses its own layout and theme-toggle script. Active shells have no site-wide `main.css`; the frozen `site/archive/` styles remain independent.

## Layout And Prose

Rendered content uses `.docsViewer__content`. The public shell uses `docs-viewer-shell`/`docsViewerShell__container`; local service shells supply their own framing. Reader CSS owns the common top inset, document width and toolbar alignment. An opening collection report omits its own extra top margin. Standard prose rules stay scoped to content, with low-specificity list defaults so reports retain their spacing. Moments poetry, modern figure captions, Catalogue content and expanded detail retain their specialised owners.

Heading sizes use the four `--docs-viewer-font-heading-*` tokens. H2 dividers and horizontal rules consume `--docs-viewer-border-strong`. Reader typography has its own font/spacing tokens. Change the owner rather than adding host-token fallbacks. Raw authored HTML can still supply local presentation; inspect the actual content when a prose rule appears ineffective.

Public and Manage use an 18px top inset and ordinary 2rem reader controls. Above 820px their controls stick at the top; the shell observes their border-box height and supplies the offset for sticky Index/Info panels and document anchors. Lists scroll in the remaining height. Narrow layout remains a separate public/manual review concern.

Moments documents use a centred maximum 50ch width keyed to the resolved collection on each document mount. A retained hidden Moments mount cannot narrow another collection or list. Content Detail and Source keep their own width owners. Authored `pre.moment-text` separately selects poetry typography, compact title spacing and the 47% word axis.

## Themes And Shared Fields

Shell heads apply the locally stored `theme` before styles load, defaulting to light. [The reader theme controller](../../docs-viewer/runtime/js/shared/docs-viewer-theme.js) changes the document's `data-theme`, stores the choice and updates its current-theme artwork and next-action name. Studio has its own [theme adapter](../../studio/app/frontend/js/studio-theme.js); 404 keeps its standalone script. SVG masks inherit surrounding text colour.

Both apps supply `--shared-search-*` values to [Search Field](Shared_UI.md#search-field). Root-relative SVG URLs survive the shared stylesheet's different serving locations. Ordinary form fields and Review's package select retain dedicated presentation.

## Search Result Highlight

Docs Viewer maps `--shared-search-result-bg` to its toolbar hover role; Studio supplies the same 92% panel/8% text neutral mix. Shared autocomplete, pickers, record-list selection and reader results consume this supplied role. Record-list selected-background hooks map to it. Focus rings, checked selections and active-query semantics keep their own owners; a grey result highlight does not add or change selection state. Collection rows retain their rounded leading extension.

Disabled checkbox labels derive their colour directly from the sibling input's disabled state. Shared icon buttons retain focus, disabled, hidden and explicit active presentation. [Toolbar Icons](Toolbar_Icons.md) owns artwork dimensions independently of button hit areas.

## Focus And Feedback

The [focus-mode controller](../../docs-viewer/runtime/js/shared/docs-viewer-focus-mode.js) records keyboard navigation on the viewer root. Tab, Arrow, Home/End and Page Up/Down enable indicators; pointer input clears them and typing alone does not enable them. This changes visible indicators without taking over actual focus, modal trapping or Back restoration. Selection, borders and drag/drop remain independent.

Busy/readiness state comes from the operation owner and drives disabled controls, cursors and accessibility. A progress message is not an availability flag. [Route readiness](Route_Ready_State.md) owns the root contract; [Runtime](Docs_Viewer_Runtime.md#three-surfaces) records the current quiet-progress feedback policy. Errors and completion/empty states retain their visible feedback.

## Maintenance

Edit canonical styles, reload the owning local app and inspect representative prose, report, Moments and detail content in both themes. A CSS-only change requires no document generation, Search rebuild or Publish. Changes to represented public CSS follow [code projection and site validation](Public_Docs_Route_Shell.md#maintenance); local-only styles stay outside that inventory.

Stylesheet order is expressed in the route shells. Check which shell actually loads an artwork or feature stylesheet before adding a duplicate rule. Interactive fit and light/dark appearance remain manual review under [Testing](../development/Verification.md). [Design](../design/Shared_Controls_And_Visual_Assets.md) records the ownership choices.
