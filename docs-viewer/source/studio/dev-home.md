---
doc_id: dev-home
title: Dev Home
added_date: 2026-04-19
last_updated: 2026-07-14
summary: This section contains technical reference documents that apply to the repo as a whole.
parent_id: ""
viewable: true
---
# Dev Home

This section contains technical design guidance for the repo, which is the source for the dotlineform website and deployed via GitHub Pages. The site is served on the domain [dotlineform.com](https://www.dotlineform.com).

The repo also contains locally run web apps:

- **[Studio](/docs/?scope=studio&doc=studio)**, which manages the data for the site.
- **[Analytics](/docs/?scope=studio&doc=analytics)**, which adds a semantic tagging layer to catalogue data.
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** is a shared module used to publish source markdown documents. Documents are imported and organised using manage mode, which is served by the standalone Docs Viewer service.
- **[Admin](/docs/?scope=studio&doc=admin)**, which includes audit, risks and activity reporting.

The repo also contains `processing/` alongside `site/`. It is currently a separate Java/Processing project rather than a website module, and it is not part of the GitHub Pages artifact deployed from `site/`. It has its own [Processing Docs Viewer scope](/docs/?scope=processing) and is expected to acquire its own build, test, and development lifecycle. Sharing a Git repository does not imply shared runtime or toolchain assumptions; any integration between Processing and the website should be treated as an explicit cross-project change.

## How The Site Works

`site/` is the checked-in static site root and the GitHub Pages artifact.
The public site is published directly by the GitHub Actions workflow after validation; there is no deploy-time build, copy, or shell-rendering step.
Public route HTML, public CSS, public JavaScript, browser-safe config, and published data payloads are source files under `site/`.

The local apps exist to maintain and inspect that site.
They may share browser-safe config, CSS, and runtime modules with the public site when that is the real owner of the behavior.
Docs Viewer is the clearest example: public routes such as `/library/`, `/analysis/`, and `/moments/` load site-owned Docs Viewer CSS, public/shared runtime JavaScript, and the site-owned public route registry.
The local `/docs/` manage route uses the standalone Docs Viewer service, and that service maps shared public URLs such as `/docs-viewer/static/css/docs-viewer.css`, `/docs-viewer/runtime/js/shared/...`, and `/docs-viewer/config/routes/docs-viewer-public-routes.json` back to their `site/` files.
Local-only management, import, report, and write behavior stays in `docs-viewer/` and behind local service routes.

Note on document structure:

- document metadata saved in front-matter YML.
- `parent_id` is used to create a hierarchical structure to group related documents. Parent documents are often referred to as 'folders' or 'sections', because this is how they appear in the Docs Viewer index-tree. The source Markdown files are saved in a flat folder `docs-viewer/source/studio/...`

## Key Documents

- **[UI](/docs/?scope=studio&doc=ui)**
  site-wide UI framework and maintenance
- **[Change Requests](/docs/?scope=studio&doc=change-requests)**
  proposed and in-progress request docs, including UI request specs and task breakdowns.
- **[Development Workflow](/docs/?scope=studio&doc=development-workflow)**
  repo implementation lifecycle guide for scoping, verification, documentation, and closeout.
- **[Development Checklist](/docs/?scope=studio&doc=development-checklist)**
  detailed implementation rules for local Studio route migration, public/local URL boundaries, route builders, and UI Catalogue demo visibility.
- **[Architecture](/docs/?scope=studio&doc=architecture)**
  route/runtime building blocks, shared shell behavior, and generated-artifact flow into the live site.
- **[Scripts](/docs/?scope=studio&doc=scripts)**
  repo scripts, their flags, outputs, and operational responsibilities.
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)**
  the shared docs module used by `/docs/` and other installed scopes (e.g. `/library/`).
- **[Search](/docs/?scope=studio&doc=search)**
  dedicated catalogue and docs search engines.
