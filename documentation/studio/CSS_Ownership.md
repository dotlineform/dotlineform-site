---
draft: false
doc_id: d-20260511-200845-2a03a0
title: CSS Ownership
added_date: "2026-05-11 20:08:45"
last_updated: "2026-10-18"
parent_id: d-20260424-000000-50b63f

---
# Docs Viewer CSS Ownership

Docs Viewer owns the active site's reader presentation across Public, Manage and Review. The public root loads the same canonical viewer styles through their tracked projection; there is no active site-wide `main.css`. The frozen archive owns independent stylesheet copies and is outside this boundary.

## Owners

- **shared palette** at `docs-viewer/static/css/docs-viewer-theme.css` owns light/dark colour roles for Public, Manage, Review and the public 404 page.
- **shared viewer CSS** at `docs-viewer/static/css/docs-viewer.css` owns reader typography and tokens, prose, the page shell, navigation, panels, search, status and shared controls. Its tracked public copy is `site/docs-viewer/static/css/docs-viewer.css`.
- **feature CSS** under `docs-viewer/static/css/` owns shared reports and focused management, Source, Import and Review surfaces. Only explicitly public files are projected under `site/`.
- **404 CSS** at `site/assets/css/error.css` owns that standalone page's minimal layout, typography and theme-button appearance. It consumes the shared palette and loads no viewer runtime or report styles.

Rendered documents use `docsViewer__content`; the former generic `content` host-style hook is removed. The public root and route template use `docs-viewer-shell` and `docsViewerShell__container`, while local routes use their service shell. Shared shell rules supply page background, body defaults and wrapper spacing without a host stylesheet. The main pane has the same top inset as the Index panel's padding and border, so ordinary headings and reports share one content offset. An opening collection report inside its document mount omits its own top margin to avoid doubling that inset.

The shared viewer stylesheet owns document body font/line height, paragraph and list spacing, inline/fenced code presentation, horizontal-rule spacing, generic captions, H1–H4 typography, table layout/cells, links, blockquotes, images, Related Links and Info presentation. Standard prose rules are scoped to document content; low-specificity list defaults allow report and gallery owners to retain their own spacing. Specialised presentation retains its more specific rules: Moments uses shared H1 typography with compact title/date spacing and its poetry layout; modern figure captions, expanded tables and Catalogue records retain their established presentation.

For heading-size edits, change the four `--docs-viewer-font-heading-*` values near the top of [docs-viewer.css](../../docs-viewer/static/css/docs-viewer.css). Viewer typography and spacing use their own tokens rather than generic host-token fallbacks. Reload the local viewer to use saved CSS; public preview/deployment uses the tracked projection maintained by `bin/site-code-update`. These style edits require no document generation, Search rebuild or Publish. [Heading Typography](deliveries/Docs_Viewer_Heading_Typography.md) and [Retire Main CSS](deliveries/Retire_Main_CSS.md) record the changes and evidence limits.

Document H2 headings have a bottom divider with the same 1px strong-border role as a normal horizontal rule, separated from the heading text by the smallest shared spacing token. Both use `--docs-viewer-border-strong` for a more visible thin line. This section cue does not change the heading font scale.

## Load Boundary

The public root and maintained public-route template load the shared palette, viewer stylesheet and public report styles. They do not load management CSS. The 404 page loads the palette, its dedicated stylesheet and its existing theme-toggle script. Active routes no longer load `main.css`; archive routes keep their frozen copies.

The local Manage shell loads the palette, viewer stylesheet, shared report styles and focused management styles. Review loads the palette, viewer stylesheet and its own stylesheet. Neither depends on public-site or Studio CSS.

Management checkbox rows use the shared checkbox-field layout, with a sibling label for consistent spacing. The management stylesheet gives disabled checkboxes' labels the existing disabled-text colour directly from the input's disabled state; Add/Edit image uses this for Preserve original resolution and Create thumb without separate JavaScript styling state.

Local apps serve canonical reader styles under `docs-viewer/`; public preview and GitHub Pages serve their tracked projection under `site/docs-viewer/`. `bin/site-code-update` maintains that projection, so public and Manage do not maintain separate reader styles.

## Extension Method

- shared colour role: palette stylesheet
- reader prose, layout or shared control: shared viewer stylesheet
- report or local workflow control: its owning feature stylesheet
- 404-only presentation: public `error.css`

Keep a rule with the presentation it owns. Do not copy legacy site components into the reader stylesheet without a current reader responsibility.

Components consume Docs Viewer custom properties. Exact variables and selectors live in CSS; do not mirror their inventory here. The archive's stylesheet copies are frozen site assets and are never updated by active runtime projection.

## Weak Spots

- raw HTML documents can introduce local presentation that bypasses the normal Markdown shape
- stylesheet order is part of the contract but is expressed in route shells rather than a central manifest
- visual changes to prose defaults need manual checks of reports, Moments and detailed content alongside ordinary Markdown

Verify representative public and manage routes after moving ownership between layers. Use visual/manual checks for cascade and layout; use public-boundary checks to confirm management assets do not leak into public shells.
