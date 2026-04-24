---
doc_id: css-primitives
title: "CSS Primitives"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: design
sort_order: 40
---
# CSS Primitives

This document defines the current shared CSS contract for the site and Studio.

The goal is not to freeze all visual design. The goal is to make repeated patterns explicit so future CSS work extends the existing system instead of adding new one-off selectors, sizes, or colors.

## Rules

- Fit UI to the shared token set in `assets/css/main.css`.
- Do not add raw `font-size` or color literals to `assets/css/main.css` or `assets/studio/css/studio.css`.
- Prefer extending an existing primitive before creating a new page-specific pattern.
- If a new token is required, add it in the shared token layer, not inside a page block.
- If two pages need the same visual shell, promote it to a shared primitive.

## Shared Token Sources

### Site tokens

Defined in `assets/css/main.css`:

- typography:
  - `--text-xs`
  - `--text-sm`
  - `--text-md`
  - `--text-lg`
  - `--text-xl`
  - `--text-2xl`
  - `--font-body`
  - `--font-small`
  - `--font-caption`
  - `--font-heading-1` through `--font-heading-4`
- color:
  - `--text`
  - `--muted`
  - `--bg`
  - `--panel`
  - `--panel-2`
  - `--border`
  - `--border-strong`
  - `--link`
  - `--link-hover`
  - `--link-visited`
  - `--shadow-pop`
  - `--debug-outline-link`
  - `--debug-outline-image`
- spacing/layout:
  - `--space-1` through `--space-7`
  - `--radius`
  - `--container`
  - `--content-measure`

### Shared list tokens

Defined in `assets/css/main.css`:

- `--list-thumb-size`
- `--list-column-gap`
- `--list-row-padding`
- `--list-row-padding-compact`
- `--list-row-gap-tight`
- `--list-section-gap`
- `--list-caption-color`

### Studio shell tokens

Defined in `assets/studio/css/studio.css`:

- `--studio-radius-sm`
- `--studio-radius-md`
- `--studio-radius-lg`
- `--studio-surface-padding-sm`
- `--studio-surface-padding-md`
- `--studio-surface-padding-lg`
- `--studio-control-height`
- `--studio-shell-gap-sm`
- `--studio-shell-gap-md`

Studio also defines its own palette/state tokens there for tag colors, surfaces, lines, focus, status, and RAG indicators.

## Approved Shared Primitives

### Site content shells

Defined in `assets/css/main.css`:

- `.box`
  shared bordered content box
- `.prompt`
  shared inset prompt/callout block
- `.container`
  shared page-width wrapper

### Site metadata pattern

Defined in `assets/css/main.css`:

- `.page__caption.page__metaList`
  unboxed metadata list used for work/work-detail style metadata blocks

This is the approved metadata baseline when listing work or series metadata:

- `--font-small`
- no container border or background
- no row borders
- bold title row via `.work__titleMain`
- only `cat.` as an explicit field label when needed

### Site list patterns

Defined in `assets/css/main.css`:

- `.index__*`
  generic index list shell
- `.workIndexItem`, `.seriesIndexItem`
  thumbnail-plus-text compact card/list rows
- `.worksList__*`
  denser works/studio data list shell

These are the approved shared list families for the main site today.

Use them like this:

- use `.index__*` for simple title/date/id index rows
- use `.workIndexItem` / `.seriesIndexItem` for thumbnail list rows
- use `.worksList__*` for multi-column data lists with sort headers

Do not create another list shell unless the existing three cannot express the layout without awkward overrides.

### Shared site link behavior

Defined in `assets/css/main.css`:

- `.index__link`
- `.workIndexItem`
- `.seriesIndexItem`
- `.worksList__title`
- `.worksList__cat`
- `.worksList__series`

These patterns already share the same focus and hover intent:

- link color from shared link tokens
- underline on hover/focus-visible
- focus ring from `--border-strong`

New list-link patterns should match this behavior.

### Studio surfaces and controls

Defined in `assets/studio/css/studio.css`:

- `.tagStudio__panel`
- `.tagStudio__input`
- `.tagStudio__button`
- `.tagStudio__button--primary`
- `.tagStudio__popupInner`
- `.tagStudio__keyInfoPopup`
- `.tagStudioModal__dialog`

These are the approved shared Studio surface/control shells.

### Studio list and form patterns

Defined in `assets/studio/css/studio.css`:

- `.tagStudioFilters__*`
- `.tagStudioToolbar__*`
- `.tagStudioList__*`
- `.tagStudioForm__*`

These are the approved shared Studio structural patterns for:

- filter/search rows
- action/import toolbars
- list shells
- modal form internals

For Studio lists, `tagStudioList__*` now carries the baseline for:

- `--font-small` row and header type
- shared head/row spacing
- shared row vertical alignment
- shared border/line treatment

Page-specific list classes should usually only define column grids and cell internals.

### Studio plain-button/reset controls

Defined in `assets/studio/css/studio.css`:

- `.tagStudio__chipRemove`
- `.tagStudio__selectedWorkBtn`
- `.tagRegistry__sortBtn`
- `.tagRegistry__tagInlineBtn`
- `.tagRegistry__demoteBtn`
- `.tagAliases__aliasBtn`

These share the same “unstyled interactive control” reset. New inline Studio controls should follow that reset rather than redefining it.

## Extension Rules

When changing CSS:

1. Start from tokens.
2. Then check whether an approved primitive already matches the pattern.
3. If the pattern repeats across pages, extend the primitive.
4. If the pattern is truly page-specific, keep it in the page namespace.
5. Re-run `python3 scripts/css_token_audit.py` after each cleanup pass.

## Current Direction

The token cleanup is structurally complete for typography and color in the shared CSS files.

The next cleanup work should focus on:

- reducing repeated page-level layout declarations that can now sit on the approved primitives
- documenting any additional shared list or shell pattern only after it exists in code
- keeping Studio page namespaces for row internals and feature-specific layouts
