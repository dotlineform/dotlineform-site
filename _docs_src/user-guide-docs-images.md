---
doc_id: user-guide-docs-images
title: "Docs Images And Assets"
last_updated: 2026-04-23
parent_id: user-guide
sort_order: 10
---
# Docs Images And Assets

Use this guide when you need to show an image or visual example inside a docs page.

There are three supported options.

## 1. Repo-Local Docs Asset

Use this for:

- screenshots checked into the repo
- annotated reference images
- stable docs-only images that should ship with the site

Save the file under:

- `assets/docs/<topic>/...`

Examples:

- `assets/docs/ui-catalogue/panel/default.png`
- `assets/docs/docs-viewer/example-doc.png`

Use it in Markdown:

```md
![Panel example](/assets/docs/ui-catalogue/panel/default.png)
```

Use it in raw HTML:

```html
<img src="/assets/docs/ui-catalogue/panel/default.png" alt="Panel example">
```

Recommended rule:

- keep docs-facing images small and optimized
- group them by topic under `assets/docs/`
- use clear names such as `default.png`, `example-docs-viewer.png`, or `state-disabled.png`

Do not save docs images under `_docs_src/`. The docs source root is for Markdown source docs, not published image assets.

## 2. Remote Docs Media

Use this for:

- images hosted outside the repo
- larger docs media that should follow `_config.yml` `media_base`
- docs that should not hardcode the full media origin in every page

Important:

- <code>&#91;&#91;media:...&#93;&#93;</code> is a real literal token that you type directly into the Markdown or HTML source

Markdown example:

<pre><code>![Library example](&#91;&#91;media:library/example.jpg&#93;&#93;)</code></pre>

Raw HTML example:

<pre><code>&lt;img src="&#91;&#91;media:library/example.jpg&#93;&#93;" alt="Library example"&gt;</code></pre>

What you type:

- <code>&#91;&#91;media:library/example.jpg&#93;&#93;</code>

What the docs builder resolves it to before render:

- `<media_base>/library/example.jpg`

Use this when you want the docs page to point at remote media without repeating the full base URL in the doc body.

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

- use `/assets/docs/...` for normal repo-owned screenshots and reference images
- use <code>&#91;&#91;media:...&#93;&#93;</code> for remotely hosted docs media
- use inline HTML/CSS/SVG for small self-contained visuals

If you are unsure, start with `/assets/docs/...`. It is the simplest option for most documentation images.

## Related References

- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
