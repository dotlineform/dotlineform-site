---
doc_id: docs-viewer-moments-migration-plan
title: Docs Viewer Moments Migration Plan
added_date: 2026-06-17
last_updated: 2026-06-18
ui_status: draft
parent_id: docs-viewer-public-scopes
viewable: true
---
# Docs Viewer Moments Migration Plan

This note records the intended migration shape for moving public moments from the catalogue moments route into a public Docs Viewer scope.

The goal is to preserve moment presentation with source Markdown, generated Docs Viewer JSON, and narrow scope-specific CSS. Avoid a moments-specific Docs Viewer runtime fork.

## Route Migration

Retire the existing static route shell before creating the Docs Viewer public scope:

- archive `site/moments/index.html` so `/moments/` is available for the scope lifecycle tool
- keep existing moment source data, generated moment payloads, and media assets in place during migration
- create a public Docs Viewer scope with `scope_id: moments` and `public_route_path: /moments/`
- generate source Markdown under `docs-viewer/source/moments/`
- build the new docs and search payloads after source migration
- after migration, remove moments from catalogue, works, and studio surfaces so Docs Viewer is the only long-term owner

The archived route shell now lives at `studio/retired/site-routes/moments/index.html`. It is rollback material only and should not remain active once the Docs Viewer route owns `/moments/`.

## Markdown Shape

Each migrated moment source file should carry moment metadata in front matter and render the public-facing title/date/image/body in Markdown.

Example:

```md
---
doc_id: a-doll-story
title: a doll story
date: 2025-06-14
date_display: 14 Jun 2025
added_date: 2025-06-14
parent_id: ""
viewable: true
---
# a doll story

<p class="momentDate">14 Jun 2025</p>

<img src="[[media:docs/moments/img/a-doll-story-primary-800.webp]]" alt="a doll story" width="800" height="800">

<pre class="moment-text">
doll was created many years before she came into my care
but we don't know why or by whom
</pre>
```

`title`, `date`, and `date_display` should remain in front matter for generated metadata and search behavior. The `#` heading and `.momentDate` paragraph are the rendered public document content.

## Date Presentation

Use a raw HTML paragraph for the rendered date so it can be styled without introducing a Docs Viewer runtime feature.

Suggested CSS:

```css
.docsViewer[data-route-id="moments"] .docsViewer__content > h1:first-child{
  margin: 0 0 0.375rem;
  font-size: var(--docs-viewer-font-heading-2);
  line-height: 1.25;
}

.docsViewer[data-route-id="moments"] .momentDate{
  margin: 0 0 1.5rem;
  color: var(--docs-viewer-muted);
  font-size: var(--docs-viewer-font-small);
  line-height: var(--docs-viewer-line-snug);
}
```

Prefer `data-route-id="moments"` for the public route because it exists in the static route shell before runtime state resolves. `data-viewer-scope="moments"` is available after config load and is better suited to manage-mode or scope-switching concerns.

## Primary Image

Render the optional primary image as a Docs Viewer media token in the migrated Markdown.

The migration should emit the 800px primary variant:

```md
<img src="[[media:docs/moments/img/a-doll-story-primary-800.webp]]" alt="a doll story" width="800" height="800">
```

Use the path shape:

```text
docs/moments/img/<moment_id>-primary-800.webp
```

Keep `width` and `height` as local `<img>` attributes rather than front-matter fields. This keeps dimensions attached to the exact image and remains unambiguous if a document later contains multiple images.

The migration should treat dimensions as optional:

- if both `width` and `height` are present and valid positive integers, emit them as `<img>` attributes;
- if either value is missing or invalid, omit both dimension attributes and render the image as a normal media token.

Do not rebuild moment-specific image rendering JavaScript inside Docs Viewer. The image should be ordinary document content.

## Moment Text

Keep the existing `<pre class="moment-text">` wrapper during the migration.

The current moments route uses this wrapper to preserve line breaks, blank lines, indentation, and poem-like spacing while resetting the browser's default code-block appearance. Converting the body to ordinary Markdown paragraphs would collapse single newlines unless the migration inserted hard breaks or paragraph boundaries throughout the text.

Docs Viewer already preserves line breaks in generic `pre` blocks, but its default `pre` styling is code-like. Add a narrow CSS reset instead:

```css
.docsViewer[data-route-id="moments"] pre.moment-text{
  font-family: inherit;
  white-space: pre-wrap;
  background: transparent;
  border: 0;
  padding: 0;
  margin: 0 0 1.5rem;
}
```

Removing `<pre class="moment-text">` should be a later editorial cleanup, not part of the first migration.

## CSS Boundary

Scope-specific CSS is acceptable here because it preserves migrated content semantics without forking Docs Viewer runtime code.

Keep the CSS narrow:

- target `.docsViewer[data-route-id="moments"]`
- style only migrated content classes such as `.momentDate`, `.momentPrimaryImage`, and `pre.moment-text`
- do not change shared Docs Viewer layout, routing, document loading, or hosted-view behavior for moments

If a later migration needs behavior that cannot be expressed as Markdown, media tokens, generated metadata, or scoped CSS, treat that as a separate Docs Viewer feature decision rather than a hidden moments-route fork.
