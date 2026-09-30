---
doc_id: d-20260910-223116-9a1011
title: Shared Icons
added_date: "2026-09-10 22:31:16"
last_updated: "2026-09-30 21:39:26"
summary: Reuse a consistent SVG icon collection across buttons, reports, document content and the Swift app while preserving simple Markdown authoring.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
draft: false
---
# Shared Icons

## Outcome  

Provide one maintained icon collection and consistent meanings across interface buttons, reports and sub-scopes, with optional reuse in authored documents and the native Mac/iPad app. SVG assets give the application control over appearance, scale and reuse. Ordinary emoji remain available in prose because they are convenient text characters that survive copy/paste without an asset dependency.

Lucide is the preferred family for general interface and document-type icons. The selected Catalogue Series and Work artwork now uses saved SVG assets. Lucide is expected to cover most remaining meanings; confirm coverage when choosing the individual icons. The [Toolbar Mapping](Toolbar_Icon_Mapping.md) records the implemented toolbar replacements, state variants and remaining visual review. Viewer and report toolbars use the current 20px artwork trial inside 32px buttons, with smaller search-clear controls. Selected report-list Subject/Draft icons and index Draft/status cues use independent 16px saved artwork. Manual [Icon Tokens](Icon_Tokens.md) are implemented; their [delivery](Icon_Tokens_Delivery.md) awaits user visual acceptance. The selected collection config and Index markers are implemented in [Collection Icons Delivery](Collection_Icons_Delivery.md), with visual review pending. Related-links generation, other unselected report/index artwork and App integration remain open.

The maintained [Toolbar Icons](Toolbar_Icons.md) reference explains the implemented shared CSS tokens, button/mask classes, rendering helper and artwork ownership. It is parented under Runtime and remains the implementation reference independently of this feature's delivery planning.

The [Studio Works Editor Mapping](Works_Editor_Icon_Mapping.md) records the adopted Works editor replacements, retained text controls and validation evidence. Studio serves the existing SVG files from their canonical folder and supplies its own small CSS-mask styling layer. The user accepted the visual result on 24 September 2026.

## Shared Ownership

Keep one canonical collection of SVG artwork. Interface/report meanings select artwork through maintained mappings; manual document tokens deliberately use the exact extensionless SVG filename instead of a second naming registry. [Source Organisation](Source_Organisation.md#collection-icons) owns the implemented extensionless collection `icon` configuration and Index-panel host mapping. [Related Links](Related_Links.md#selected-icons-and-collection-configuration) records its planned reuse in generated link lists. Collection icons identify collection ownership; Subject artwork remains separate. Preserve document identity and title sorting independently of icon presentation.

Downloaded general SVG artwork lives in `docs-viewer/static/icons/`, and the Edit document control consumes `pen.svg` there. The VS Code controls now use `file-code-corner.svg`; the former branded asset and its dedicated attribution file have been removed. Public resources have an explicit tracked site projection; App resources would be packaged from the same canonical artwork. Keep those outputs replaceable and avoid independently maintained drawings in each consumer. Any runtime meaning-to-asset mapping can be settled in a bounded delivery; the editable toolbar selection document is not runtime configuration, and this feature does not require a general asset framework.

Retain each adopted asset's origin, upstream version, licence and required notices. Brand artwork keeps its own proportions, colours and usage conditions. A brand asset is not a template for drawing unrelated application icons.

## Recommended Drawing Guidelines

These proposed defaults follow Lucide's outline family. Review a small representative set alongside the existing Catalogue designs at actual display sizes before adopting them. Preserve approved Catalogue geometry and brand artwork; fit assets into the same presentation box without distorting their proportions.

| Property | Recommended starting point |
| --- | --- |
| Drawing area | A square `viewBox="0 0 24 24"`. These are design units; they do not force a 24-pixel display size. |
| Internal margin | Keep most stroke centre lines within coordinates 2–22. A 2-unit stroke then leaves at least 1 unit between painted artwork and the canvas edge. Maintain comparable optical margins for filled shapes. |
| Stroke | 2 units at the 24-unit design size, with round line caps and joins. Keep one visual weight across the outline family. |
| Detail | Prefer clear silhouettes and roughly 2-unit internal gaps. Remove details that disappear at small sizes. |
| Alignment | Centre visually, allowing small optical corrections for asymmetric shapes. Related icons should feel equally prominent. |
| Display sizes | The current toolbar trial uses 20px artwork inside 32px buttons, following the initial 24px pilot. One shared CSS token selects the general artwork size; explicitly recorded smaller controls use local overrides. Document-text and native sizes remain separate choices; the enclosing button owns its hit area. |
| Colour | Use monochrome artwork for ordinary actions and document types as the initial proposal. Let the renderer apply theme colour; reserve fixed colours for deliberately chosen colour artwork and brands. |
| SVG content | Prefer paths and basic shapes with a complete viewBox. Avoid scripts, external resources, embedded fonts, text glyph dependencies and raster images. Treat filters or other complex effects as exceptions requiring web/native review. |

The 24-unit canvas and 2-unit rounded strokes follow [Lucide's design specification](https://lucide.dev/contribute/icons/specification). Report-list and index cues retain 16px artwork; toolbar artwork remains 20px unless explicitly recorded otherwise. Use the selected saved Catalogue drawings as supplied. Do not redraw an adopted icon merely to change its native viewBox; preserve its aspect ratio and inspect its optical fit.

The renderer owns sizing, alignment and accessibility. Give icon-only actions an accessible name and a visible tooltip. Hide redundant decoration from assistive technology; expose a type meaning when it is otherwise absent from the document title. Keep meaningful state understandable without colour alone. Web tinting and native template rendering need their own small adapters; SVG artwork alone does not make browser CSS apply to SwiftUI.

## Artwork Sources And Existing Catalogue Icons

Use selected [Lucide SVG assets](https://lucide.dev/license) for the shared family, retaining their ISC and applicable inherited MIT notices. Choose by the meaning of each control or document type; an existing emoji is a cue to that meaning and does not require an exact pictorial replacement. Draw a new icon only when the adopted family and existing Catalogue artwork leave a confirmed gap.

`docs-viewer/runtime/js/reports/project-subject-icons.js` maps Series, Work and Folder to `dlf-series.svg`, `dlf-work.svg` and `folder.svg` under `docs-viewer/static/icons/`. The helper now creates one decorative mask span per Subject instead of inline SVG or emoji. The selected saved drawings own their geometry; shared list CSS owns 16px sizing, theme tint and alignment. The supplied Work asset is a deliberate replacement for its previous inline design.

Ordinary emoji remain supported in authored prose. If colour emoji artwork is later needed as an asset, choose an explicitly licensed SVG source. A Unicode character and a platform's drawing are separate: Unicode directs permission enquiries for vendor imagery to the relevant vendor. [Unicode emoji guidance](https://www.unicode.org/faq/emoji_dingbats.html).

## Markdown Authoring And Export

Authors can include an exact saved icon with `[[icon:refresh-cw]]`, selecting `refresh-cw.svg` from the canonical icon folder. **Directives → Insert icon** inserts that token inline and selects the stem for editing. [Icon Tokens](Icon_Tokens.md) owns the supported syntax, renderer, failure behaviour and export contract.

Ordinary Markdown can also reference an SVG using an image link, but the reference still needs a reachable asset and suitable inline sizing. [Markdown image syntax](https://spec.commonmark.org/spec/#images), [SVG image support](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image).

Leave authored emoji unchanged. Do not globally replace matching characters in prose, code, titles or copied text. Manual icon references resolve exact canonical filenames; missing files fail the document build. Normal rendering must not turn small icons into diagram-detail targets.

Generated HTML embeds the sanitized SVG mask and inline presentation, so HTML exports carry their own artwork. Markdown and plain-text conversion retain the readable token; source packages require the matching canonical icon when rebuilt. No machine-local or website-root-only asset path is embedded in the portable icon identity.

## Swift App Reuse

The app already has a `WKWebView` host for bundled web content. When Docs Viewer content is integrated, the same SVG files can be packaged as web resources with URLs that resolve inside the permitted bundle directory. Native SwiftUI controls can consume SVG artwork through Xcode image asset sets and named images; Xcode supports SVG image assets. [Apple SVG asset support](https://developer.apple.com/documentation/xcode-release-notes/xcode-12-release-notes).

Keep one artwork source while allowing separate web-resource and native asset-catalogue packaging. Native image assets are prepared at build time; this does not establish a general runtime loader for arbitrary SVG files. Theme tint, layout and accessibility remain with their respective interfaces. Before adopting a family, inspect representative assets in WebKit and native Mac/iPad views, including small-size and light/dark appearance. This feature does not bring forward the wider Docs Viewer App integration.

## Decisions Before Delivery

- Choose the initial Lucide icons and confirm any remaining coverage gaps, including document collection/Subject precedence and whether any prefixes combine more than one meaning.
- Confirm the canonical asset location, attribution record and how web/public/App packages consume it.
- Review representative Lucide actions/document types alongside the existing Catalogue designs and VS Code brand asset at the recommended sizes; decide whether the Catalogue stroke weight needs adjustment.
- Define the next complete delivery for collection prefixes or App reuse independently of the implemented manual token.

The [Links report](/docs/?doc=d-20260910-214604-f9e841) already separates title text from a future prefix. Its shipped aggregation and navigation remain unchanged. This feature owns the shared icon decisions deferred by [Unified Analysis And Catalogue Presentation](Analysis_And_Catalogue_Presentation.md); an eventual delivery should name the consumers it migrates and provide a complete reviewable result.
