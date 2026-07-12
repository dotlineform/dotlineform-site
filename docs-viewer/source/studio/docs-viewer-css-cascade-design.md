---
doc_id: docs-viewer-css-cascade-design
title: CSS Cascade Design
added_date: 2026-05-11
last_updated: 2026-07-12
parent_id: docs-viewer
viewable: true
---
# Docs Viewer CSS Cascade Design

## Summary

- Docs Viewer should be portable without becoming visually isolated from the site that hosts it.
- Public host routes should provide page layout, prose defaults, and public-site chrome.
- Docs Viewer should provide its own portable base contract plus shell, navigation, search, result, bookmark, status, report, and management component styles.
- Public read-only routes intentionally inherit the public host stylesheet so `/library/` and `/analysis/` continue to belong to the public site.
- Scope-owned presentation stays outside the basic stylesheet and selects the active scope rather than a particular route shell.
- Docs Viewer does not require the public host stylesheet to function.
- The Docs Viewer include adds only Docs Viewer-owned stylesheets.

## Target Stylesheet Order

The intended cascade for public routes is:

1. host layout stylesheet, currently `site/assets/css/main.css`
2. Docs Viewer basic/public stylesheet, served at `/docs-viewer/static/css/docs-viewer.css` from `site/docs-viewer/static/css/docs-viewer.css`
3. an installed scope stylesheet when needed; `/moments/` loads `/docs-viewer/static/css/docs-viewer-moments.css`

The intended cascade for local or standalone management routes is:

1. explicit local shell stylesheet when the host has one, currently `studio/app/assets/css/studio.css` for Local Studio's temporary manage shell
2. Docs Viewer basic/public stylesheet, served at `/docs-viewer/static/css/docs-viewer.css` from `site/docs-viewer/static/css/docs-viewer.css`
3. Docs Viewer shared report stylesheet, `site/docs-viewer/static/css/docs-viewer-reports.css`
4. scope-owned stylesheets available to the management scope selector, currently `site/docs-viewer/static/css/docs-viewer-moments.css`
5. Docs Viewer management shell stylesheet, `docs-viewer/static/css/docs-viewer-manage.css`
6. source editor and semantic picker stylesheet, `docs-viewer/static/css/docs-viewer-source-editor.css`
7. Docs Import stylesheet, `docs-viewer/static/css/docs-viewer-import.css`

## Host Stylesheet Responsibilities

The host stylesheet owns site-wide presentation:

- font family and baseline type scale
- theme tokens such as text, panel, border, muted, and link colors
- page layout containers
- prose/document rules through `.content`
- generated document media defaults, including responsive images

Generated docs HTML is rendered inside:

```html
<div class="docsViewer__content content" id="docsViewerContent"></div>
```

The `content` class is intentional. It lets generated markdown output inherit the host project's document typography and media behavior instead of requiring Docs Viewer to recreate every prose rule.

## Docs Viewer Basic Stylesheet Responsibilities

`site/docs-viewer/static/css/docs-viewer.css` owns the basic/public viewer contract.
The public static site serves it directly from the `site/` deploy root, and the local Docs Viewer service maps the same `/docs-viewer/static/css/docs-viewer.css` URL to that file so public and manage mode share one CSS owner.

- Docs Viewer-prefixed font, type scale, spacing, color, radius, and container tokens with host-token fallbacks
- `.docsViewer`-scoped utilities such as `visually-hidden`, `muted`, `small`, and hidden-state handling
- minimal monospace inheritance for code blocks rendered inside the viewer shell
- opt-in standalone shell body/container defaults for Docs Viewer-owned service pages
- `.docsViewer` grid and responsive shell
- sidebar/index layout
- nav rows, toggles, active states, and collapsed index state
- search controls
- action button baseline used by public viewer controls
- status text
- bookmark row and bookmark controls
- main-view toolbar, breadcrumb path, info toggle, and document action controls
- search and recently-added results
- viewer-specific content constraints such as measure width
- rendered Markdown content should not force mid-word wrapping by default
- rendered Markdown code blocks should preserve code whitespace and use horizontal overflow when needed
- tables may still scroll horizontally when needed

It should not restyle public host page chrome, override public `site/assets/css/main.css` tokens on `/library/` and `/analysis/`, or define report, import, source-editor, scope-owned presentation, scope-lifecycle, settings, management-shell, or status mutation/menu selectors.

## Moments Scope Stylesheet Responsibilities

`site/docs-viewer/static/css/docs-viewer-moments.css` owns presentation that is meaningful only for the `moments` scope:

- the compact Moments document measure
- Moments title and date spacing
- inherited prose typography for `pre.moment-text`
- the opt-in `moment-text--axis` word-axis composition and its narrow-screen flowing-text fallback

Its selectors use `.docsViewer[data-viewer-scope="moments"]`, not the public route id. The runtime projects the active scope onto that attribute, so the same rules apply on `/moments/` and `/docs/?scope=moments` while remaining inactive for other management scopes.

The public Moments shell and the management shell both load the stylesheet. Keeping it available in the local management shell is preferred to adding a dynamic stylesheet loader; only the matching scope activates its rules.

## Rendered Table Defaults

Markdown tables do not expose column-width controls.
Docs Viewer should keep normal Markdown tables readable by default:

- do not force mid-word wrapping in rendered docs content, inline code, links, or table cells
- keep ordinary Markdown tables horizontally scrollable when the document measure is too narrow
- use a wrapper class for problem tables that need intrinsic column widths or a minimum width for a specific column

For a table whose first column contains package names, ids, paths, or similar technical labels, wrap the Markdown table in trusted raw HTML:

```md
<div class="docsViewerTable docsViewerTable--firstColumnMin docsViewerTable--nowrapFirstColumn" style="--docs-viewer-table-first-column: 14ch;">

| Package | Notes |
| - | - |
| `beautifulsoup4` | Parser |

</div>
```

The renderer allows raw HTML in source docs, and Markdown tables inside a raw wrapper are rendered as tables.
Use the wrapper only where a table needs local width behavior; do not replace ordinary Markdown tables with raw HTML tables unless the table needs markup that Markdown cannot express.

## Docs Viewer Management Stylesheet Responsibilities

`docs-viewer/static/css/docs-viewer-manage.css` should only load in the local `/docs/` service shell when management markup is enabled.
It owns the shared management shell surfaces:

- management toolbar row
- scope selector controls
- selected-document status mutation/menu controls
- non-viewable/viewable toggle controls
- drag/drop index states
- undo move button
- context menu
- metadata modal
- management notes and unavailable/error states

Feature-owned management styles are separate:

- `docs-viewer/static/css/docs-viewer-source-editor.css` owns Markdown source editor and semantic-target picker selectors
- `docs-viewer/static/css/docs-viewer-import.css` owns Docs Import controls, collection decisions, result/warning states, and import-modal layout

Management mode should not depend on Studio CSS for Docs Viewer controls, modals, or import surfaces.
Feature selectors should stay in their owning stylesheet instead of accumulating in the shared management shell file.

## Custom Property Contract

Docs Viewer CSS should consume host tokens when present and provide fallbacks for portable installs.
Prefer a two-level token pattern:

```css
.docsViewer{
  --docs-viewer-text: var(--docs-viewer-theme-text, var(--text, #1f1f1f));
  --docs-viewer-muted: var(--docs-viewer-theme-muted, var(--muted, #666));
  --docs-viewer-panel: var(--docs-viewer-theme-panel, var(--panel, #fff));
  --docs-viewer-panel-2: var(--docs-viewer-theme-panel-2, var(--panel-2, #f6f6f6));
  --docs-viewer-border: var(--docs-viewer-theme-border, var(--border, #d8d8d8));
  --docs-viewer-border-strong: var(--docs-viewer-theme-border-strong, var(--border-strong, #777));
}
```

Component rules should prefer Docs Viewer tokens:

```css
.docsViewer__sidebarInner{
  background: var(--docs-viewer-panel);
  border-color: var(--docs-viewer-border);
  color: var(--docs-viewer-text);
}
```

This keeps three override levels:

- host defaults such as `--text`, `--panel`, and `--border`
- Docs Viewer portable fallbacks
- explicit Docs Viewer theme overrides such as `--docs-viewer-theme-panel`

## Applied Extraction State

The reusable Docs Viewer browser CSS now lives under `docs-viewer/static/css/`.
The public stylesheet extraction moved out of `site/assets/css/main.css`:

- all `.docsViewer*` shell and component rules that are part of the viewer
- viewer-specific search, bookmark, status, and result styles
- viewer-specific responsive layout rules

The public site stylesheet still owns:

- site chrome
- general layout/container styles
- theme tokens
- `.content` document typography
- generic responsive image rules
- unrelated Studio, Catalogue, and public-site UI

Management-only styles are split by owner:

- `docs-viewer/static/css/docs-viewer-manage.css`: shared management shell, navigation mutation, menus, modals, scope selector, and actions
- `docs-viewer/static/css/docs-viewer-source-editor.css`: source editor and semantic picker
- `docs-viewer/static/css/docs-viewer-import.css`: Docs Import and reviewed-collection workflow

Scope-owned public styles are also split from the basic viewer:

- `site/docs-viewer/static/css/docs-viewer-moments.css`: Moments measure, typography, and opt-in composed-text treatments shared by the public and management views of that scope

## Verification

After changing the cascade:

- build the site
- smoke `/docs/?scope=studio`
- smoke `/docs/?scope=library`
- smoke `/docs/?scope=moments`
- smoke `/library/`
- smoke `/analysis/`
- smoke `/moments/`
- open `/docs/?scope=studio&import=1` and verify the import modal still has usable form controls
- confirm public routes do not load Studio CSS
- confirm generated docs content still uses host prose and responsive image styling

## Related Docs

- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
