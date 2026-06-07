---
doc_id: docs-viewer-css-cascade-design
title: CSS Cascade Design
added_date: 2026-05-11
last_updated: 2026-06-02
parent_id: docs-viewer
viewable: true
---
# Docs Viewer CSS Cascade Design

## Summary

- Docs Viewer should be portable without becoming visually isolated from the site that hosts it.
- Public host routes should provide page layout, prose defaults, and public-site chrome.
- Docs Viewer should provide its own portable base contract plus shell, navigation, search, result, bookmark, status, report, and management component styles.
- Public read-only routes intentionally inherit the public host stylesheet so `/library/` and `/analysis/` continue to belong to the public site.
- Docs Viewer does not require the public host stylesheet to function.
- The Docs Viewer include adds only Docs Viewer-owned stylesheets.

## Target Stylesheet Order

The intended cascade for public Jekyll routes is:

1. host layout stylesheet, currently `assets/css/main.css`
2. Docs Viewer basic/public stylesheet, `docs-viewer/static/css/docs-viewer.css`

The intended cascade for local or standalone management routes is:

1. explicit local shell stylesheet when the host has one, currently `studio/app/assets/css/studio.css` for Local Studio's temporary manage shell
2. Docs Viewer basic/public stylesheet, `docs-viewer/static/css/docs-viewer.css`
3. Docs Viewer report stylesheet, `docs-viewer/static/css/docs-viewer-reports.css`
4. Docs Viewer management stylesheet, `docs-viewer/static/css/docs-viewer-manage.css`

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

`docs-viewer/static/css/docs-viewer.css` owns the basic/public viewer contract:

- Docs Viewer-prefixed font, type scale, spacing, color, radius, and container tokens with host-token fallbacks
- `.docsViewer`-scoped utilities such as `visually-hidden`, `muted`, `small`, and hidden-state handling
- minimal monospace inheritance for code blocks rendered inside the viewer shell
- opt-in standalone shell body/container defaults for Docs Viewer-owned service pages
- `.docsViewer` grid and responsive shell
- sidebar/index layout
- nav rows, toggles, active states, and collapsed index state
- scope selector and search controls
- action button baseline used by public viewer controls
- status text
- bookmark row and bookmark controls
- metadata row, path, updated date, and status/bookmark display
- search and recently-added results
- viewer-specific content constraints such as measure width
- rendered Markdown content should not force mid-word wrapping by default
- rendered Markdown code blocks should preserve code whitespace and use horizontal overflow when needed
- tables may still scroll horizontally when needed

It should not restyle public host page chrome, override public `assets/css/main.css` tokens on `/library/` and `/analysis/`, or define report, import, source-editor, scope-lifecycle, settings, management-shell, or status mutation/menu selectors.

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

`docs-viewer/static/css/docs-viewer-manage.css` should only load when `allow_management=true`.
It should own management-only surfaces:

- management toolbar row
- selected-document status mutation/menu controls
- non-viewable/viewable toggle controls
- drag/drop index states
- undo move button
- context menu
- metadata modal
- import modal frame
- management notes and unavailable/error states
- transitional Docs Import form/control styles copied from Studio CSS

Management mode should not depend on Studio CSS for Docs Viewer controls, modals, or import surfaces.
If Docs Import still uses `tagStudio*` class names, copy only the narrow required rules into Docs Viewer management CSS as a transitional compatibility layer.
Rename or refactor those classes later after the dependency is contained.

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
The public stylesheet extraction moved out of `assets/css/main.css`:

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

Management-only styles live in `docs-viewer/static/css/docs-viewer-manage.css`:

- management-only `.docsViewer*` rules
- only the `tagStudio*` form/control rules required by the Docs Import modal

## Verification

After changing the cascade:

- build the site
- smoke `/docs/?scope=studio`
- smoke `/docs/?scope=library&mode=manage`
- smoke `/library/`
- smoke `/analysis/`
- open `/docs/?scope=studio&mode=manage&import=1` and verify the import modal still has usable form controls
- confirm public routes do not load Studio CSS
- confirm generated docs content still uses host prose and responsive image styling

## Related Docs

- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
