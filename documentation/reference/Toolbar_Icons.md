---
doc_id: d-20260919-102340-25979d
title: Toolbar Icons
added_date: "2026-09-19 10:23:40"
last_updated: "2026-11-18"
summary: Maintained Docs Viewer toolbar and list icon sizing, shared mask styles, rendering helpers, artwork ownership and extension method.
parent_id: d-20260331-000000-c313fd
draft: false
---
# Toolbar Icons

Interface icons have separate owners for action meaning, button interaction, artwork geometry and size. Canonical SVGs live in [docs-viewer/static/icons](../../docs-viewer/static/icons/); Docs Viewer and Studio use small CSS-mask adapters around those same saved files. Authored [Icon Tokens](Icon_Tokens.md) use prepared embedded markup instead.

## Pieces And Owners

| Piece | Owner |
| --- | --- |
| Action, target, label, tooltip, enabled/pressed/expanded/busy state | Focused control/report owner and [surface host](Panel_Hosts_And_Control_Surfaces.md) |
| Button hit area, rest/hover/focus/disabled/hidden/active appearance | `.docsViewer__toolbarIconButton` in [reader CSS](../../docs-viewer/static/css/docs-viewer.css) |
| Artwork box | `--docs-viewer-toolbar-icon-size`, currently 20px |
| Button dimensions | Layout-supplied `--docs-viewer-control-height`, normally 2rem; report scopes supply their own control height |
| Monochrome mask, alignment and tint | `.docsViewer__toolbarIcon`, using `currentColor` |
| Exact saved drawing | Maintained artwork class supplying only its SVG URL |
| Decorative span creation | [createDocsViewerToolbarIcon](../../docs-viewer/runtime/js/shared/docs-viewer-toolbar-icon.js) |
| Independent list/type cue | `.docsViewer__listIcon`, 1rem artwork without button interaction |

The helper receives an exact CSS class and creates an `aria-hidden` span. It does not infer meaning from a label, construct a filename, register controls or attach listeners. The existing button/link supplies its accessible name. An artwork change preserves the control/action id and workflow state.

## Size, Colour And State

Changing the artwork token resizes its consumers without changing their hit areas. The Info close and search-clear controls use smaller local artwork; the home mask uses twice the general artwork size inside its existing row. Layout scopes must supply the button-height token before adopting the shared button class. Menu icons retain their accompanying text.

Masks tint the painted silhouette, including outline strokes; tinting does not fill an outline's hollow centre. Multicolour artwork such as the ordinary `report` status uses a background image. Theme and disabled roles remain palette-owned. Enabled hover uses the panel/text neutral mix; explicit active styling keeps its own priority. `aria-pressed` does not universally select a background.

The state owner selects artwork when needed: theme shows the current light/dark state, Draft/Ready shows readiness, and Star reflects membership. These are separate from publication state. Subject cues describe Folder/Work/Series/Detail declarations; collection markers describe collection ownership. Ordinary `ui_status` remains free text with only `planned` and `report` mapped to artwork by [code config](../../docs-viewer/runtime/js/shared/docs-viewer-code-config.js). Collection metadata has no such status mapping. [Source Organisation](Source_Organisation.md#collection-icons) owns configured collection stems and exact host matching.

## Changing Or Adding Artwork

Reuse a saved SVG, or preserve origin/version/notices when adopting new artwork. Put a URL-only artwork class in the stylesheet actually loaded by its consumers: shared reader, local Manage, Review or Studio. CSS resolves URLs relative to that stylesheet. Review's VS Code class is deliberately declared in Review CSS as well as Manage CSS; both reference one saved `file-code-corner.svg`.

Keep the focused renderer and state owner, give icon-only controls an accessible name and tooltip, and hide redundant decoration. Studio's [icon helper](../../studio/app/frontend/js/studio-icon.js) and [stylesheet](../../studio/app/assets/css/studio.css) adapt saved artwork to Studio's theme without importing the Docs runtime. Its record-list adapter supplies File/Link type labels and action classes.

Only selected reader SVGs enter the [public inventory](../../site-tools/config/site-code-update.json). A public artwork choice needs both a loaded class and projected file; a downloaded SVG alone activates nothing. Follow [projection maintenance](Public_Docs_Route_Shell.md#maintenance) for public changes. A runtime/style-only change needs no Docs/Search build. Rebuilding authored icon markup is separately [build-owned](Icon_Tokens.md#portability-and-exports).

## Adoption And Remaining Work

The detailed migration tables are historical choices rather than runtime configuration. [Design](../design/Shared_Controls_And_Visual_Assets.md) retains their reusable rationale; [delivery evidence](../deliveries/Shared_Controls_And_Visual_Assets_Review.md) records Studio acceptance and static-check limits. The remaining [toolbar visual review](../_working/Toolbar_Icon_Mapping.md), [manual token acceptance](../_working/Icon_Tokens_Delivery.md) and [collection marker acceptance](../_working/Collection_Icons_Delivery.md) remain open in Working. Broader [native/unselected icon work](../_working/Shared_Icons.md) remains proposed.
