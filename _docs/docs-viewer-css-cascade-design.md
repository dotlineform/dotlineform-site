---
doc_id: docs-viewer-css-cascade-design
title: Docs Viewer CSS Cascade Design
added_date: 2026-05-11
last_updated: "2026-05-13 20:20"
parent_id: docs-viewer
sort_order: 12000
hidden: false
---
# Docs Viewer CSS Cascade Design

## Summary

Docs Viewer should be portable without becoming visually isolated from the site that hosts it.
The host project should provide the page layout, base typography, prose defaults, and theme tokens.
Docs Viewer should provide its own shell, navigation, search, result, bookmark, status, and management component styles.

## Target Stylesheet Order

The intended cascade is:

1. host layout stylesheet, currently `assets/css/main.css`
2. Docs Viewer public stylesheet, `assets/docs-viewer/css/docs-viewer.css`
3. Docs Viewer management stylesheet, `assets/docs-viewer/css/docs-viewer-management.css`, only when management mode is enabled

The host stylesheet is not loaded by Docs Viewer at runtime.
It is part of the consuming Jekyll layout.
The Docs Viewer include adds only Docs Viewer-owned stylesheets.

## Host Stylesheet Responsibilities

The host stylesheet owns site-wide presentation:

- font family and baseline type scale
- theme tokens such as text, panel, border, muted, and link colors
- page layout containers
- global utility classes such as `muted`, `small`, and `visually-hidden`
- prose/document rules through `.content`
- generated document media defaults, including responsive images

Generated docs HTML is rendered inside:

```html
<div class="docsViewer__content content" id="docsViewerContent"></div>
```

The `content` class is intentional.
It lets generated markdown output inherit the host project's document typography and media behavior instead of requiring Docs Viewer to recreate every prose rule.

## Docs Viewer Public Stylesheet Responsibilities

`assets/docs-viewer/css/docs-viewer.css` should own reusable viewer UI:

- `.docsViewer` grid and responsive shell
- sidebar/index layout
- nav rows, toggles, active states, and collapsed index state
- scope selector and search controls
- action button baseline used by public viewer controls
- status text
- bookmark row and bookmark controls
- metadata row, path, updated date, and summary display
- UI status pills
- search and recently-added results
- viewer-specific content constraints such as measure width

It should not define broad site typography or unrelated public-site layout.

## Docs Viewer Management Stylesheet Responsibilities

`assets/docs-viewer/css/docs-viewer-management.css` should only load when `allow_management=true`.
It should own management-only surfaces:

- management toolbar row
- hidden/viewable toggle controls
- drag/drop index states
- undo move button
- context menu
- metadata modal
- import modal frame
- management notes and unavailable/error states
- transitional Docs Import form/control styles copied from Studio CSS

Management mode should not depend on `assets/studio/css/studio.css`.
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

## What Should Move In Slice 5

Move out of `assets/css/main.css`:

- all `.docsViewer*` shell and component rules that are part of the viewer
- viewer-specific search, bookmark, status, and result styles
- viewer-specific responsive layout rules

Keep in `assets/css/main.css`:

- site chrome
- general layout/container styles
- theme tokens
- `.content` document typography
- generic responsive image rules
- unrelated Studio, Catalogue, and public-site UI

Move or copy into `assets/docs-viewer/css/docs-viewer-management.css`:

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
- confirm public routes do not load `assets/studio/css/studio.css`
- confirm generated docs content still uses host prose and responsive image styling

## Related Docs

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
