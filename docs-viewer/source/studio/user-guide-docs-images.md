---
doc_id: user-guide-docs-images
title: Docs Images And Assets
added_date: 2026-04-23
last_updated: 2026-07-13
parent_id: docs-viewer
viewable: true
---
# Docs Images And Assets

Use this guide when you need to show an image or visual example inside a docs page.

There are three supported options.

## 1. Repo-Local Docs Asset

Use this for:

- screenshots checked into the repo
- annotated reference images
- stable local technical/design references that should remain with the docs source

Save the file under:

- `docs-viewer/source/<scope>/media/img/<filename>`
- `docs-viewer/source/<scope>/media/files/<filename>`

Examples:

- `docs-viewer/source/studio/media/img/workspaces-example-doc.png`
- `docs-viewer/source/studio/media/img/ui-audits-example-state.png`

Use it in Markdown:

```md
![Docs Viewer example](/docs/media/studio/img/workspaces-example-doc.png)
```

Use it in raw HTML:

```html
<img src="/docs/media/studio/img/workspaces-example-doc.png" alt="Docs Viewer example">
```

Recommended rule:

- keep docs-facing images small and optimized
- prefix filenames with the topic when that makes the flat class folder easier to scan
- use clear names such as `default.png`, `example-docs-viewer.png`, or `state-disabled.png`

The local Docs Viewer service serves only the configured repo media root through `/docs/media/<scope>/...` with containment checks.
Do not put local design documents or working references in `site/`; that tree is the public deploy artifact.

## 2. Remote Docs Media

Use this for:

- images/files owned by public Library, Analysis, or Moments scopes
- larger docs media that should use the shared media origin
- public docs that should not hardcode the full media origin

Important:

- <code>&#91;&#91;media:...&#93;&#93;</code> is a real literal token that you type directly into the Markdown or HTML source

Markdown example:

<pre><code>![Library example](&#91;&#91;media:docs/library/img/example.jpg&#93;&#93;)</code></pre>

Markdown image tokens can include optional dimensions:

<pre><code>![Library example](&#91;&#91;media:docs/library/img/example.jpg width=800 height=600&#93;&#93;)</code></pre>

Raw HTML example:

<pre><code>&lt;img src="&#91;&#91;media:docs/library/img/example.jpg&#93;&#93;" alt="Library example"&gt;</code></pre>

What you type:

- <code>&#91;&#91;media:docs/library/img/example.jpg&#93;&#93;</code>

What the docs builder resolves it to before render:

- `<media_base>/docs/library/img/example.jpg`

Docs Import publishes record-owned public media automatically before it commits this token.
For a manually authored asset already placed in the shared import-staging drop-zone, use the exact-scope dry-run-first CLI described in [Publish Media To R2](/docs/?scope=studio&doc=scripts-publish-media-to-r2).
Use a new filename when one replacement must be visible immediately; Docs media cache versioning is not part of the current uploader.

## 3. Inline Raw HTML/CSS/SVG

Use this for:

- small diagrams
- custom callouts or layouts
- self-contained SVG examples that belong directly in the doc body

Example:

```html
<svg viewBox="0 0 120 40" width="240" role="img" aria-label="Simple example">
  <rect x="1" y="1" width="118" height="38" rx="6" fill="none" stroke="currentColor" />
  <text x="60" y="25" text-anchor="middle" font-size="14">Example</text>
</svg>
```

Use this when the visual is part of the explanation itself and does not need to exist as a separate image file.

## Which Option Should I Use?

- use `/docs/media/<scope>/...` for repo-backed or external-local scope assets
- use <code>&#91;&#91;media:docs/&lt;scope&gt;/...&#93;&#93;</code> for public R2 media
- use inline HTML/CSS/SVG for small self-contained visuals

If the doc is public, use its R2 media token. If it is local technical/design documentation, keep the asset beside the docs source.

## Related References

- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling)
